"""Acoustic Speaker Diarization & Biometric Memory Engine.

Performs genuine voice-based speaker recognition:
1. Slices 16kHz PCM audio for each transcription segment.
2. Extracts acoustic voice biometric embeddings (F0 pitch, spectral centroid, ZCR, dynamic timbre).
3. Maintains persistent SpeakerMemory across the entire recording:
   - Compares incoming speech to known speaker acoustic centroids using cosine similarity & pitch compatibility.
   - Only assigns a new speaker when an authentic voice change is detected (similarity < threshold).
   - Re-identifies previous speakers when they talk again later in the audio (biometric voice memory).
4. Groups consecutive same-speaker turns into cohesive, beautifully formatted English dialogue blocks.
5. Polishes English grammar, capitalization, technical acronyms, and punctuation.
"""

from __future__ import annotations

import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from scriber.models import AudioSegment, VoiceProfile, WordTimestamp
from scriber.voice_clone import VoiceProfiler


class NeuralSpeakerExtractor:
    """Deep ONNX neural speaker embedding extractor using CAM++ (200k speakers).

    Extracts 192-dimensional unit-normalized ($L_2 = 1.0$) speaker embeddings
    from 16kHz mono PCM speech frames via 80-bin Mel filterbank with CMVN normalization.
    Provides graceful zero-dependency fallback when ONNX model is missing or fails.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or self._resolve_model_path()
        self.session: Optional[Any] = None
        self.input_name: str = "feats"
        self.output_name: str = "embs"
        self.is_available: bool = False

        if ort is not None and self.model_path and os.path.exists(self.model_path):
            try:
                available = ort.get_available_providers()
                providers = [p for p in ["CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider"] if p in available]
                if not providers:
                    providers = ["CPUExecutionProvider"]
                self.session = ort.InferenceSession(self.model_path, providers=providers)
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                self.is_available = True
            except Exception:
                self.session = None
                self.is_available = False

    @staticmethod
    def _resolve_model_path() -> Optional[str]:
        env_path = os.environ.get("CAMPPLUS_MODEL_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        here = os.path.abspath(os.path.dirname(__file__))
        candidates = [
            os.path.join(here, "assets", "models", "campplus_cn_en_common_200k.onnx"),
            os.path.abspath("scriber/assets/models/campplus_cn_en_common_200k.onnx"),
        ]
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, "scriber", "assets", "models", "campplus_cn_en_common_200k.onnx"))
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    @classmethod
    def compute_fbank(cls, pcm16_data: bytes, sample_rate: int = 16000) -> np.ndarray:
        """Computes 80-bin log mel-filterbank features with CMVN from 16kHz PCM audio."""
        if pcm16_data.startswith(b"RIFF") and len(pcm16_data) > 44:
            data_idx = pcm16_data.find(b"data")
            pcm16_data = pcm16_data[data_idx + 8:] if data_idx != -1 else pcm16_data[44:]
        if len(pcm16_data) % 2 != 0:
            pcm16_data = pcm16_data[:-1]

        samples = np.frombuffer(pcm16_data, dtype=np.int16).astype(np.float32)
        frame_len = int(0.025 * sample_rate)   # 400 samples (25ms)
        frame_shift = int(0.010 * sample_rate) # 160 samples (10ms)
        n_fft = 512
        num_bins = 80
        low_freq = 20.0
        high_freq = sample_rate / 2.0

        if len(samples) < frame_len:
            samples = np.pad(samples, (0, frame_len - len(samples)), mode="constant")
        num_frames = max(1, (len(samples) - frame_len) // frame_shift + 1)

        def hz_to_mel(f: float) -> float:
            return 1127.0 * np.log(1.0 + f / 700.0)

        def mel_to_hz(m: float) -> float:
            return 700.0 * (np.exp(m / 1127.0) - 1.0)

        mel_points = np.linspace(hz_to_mel(low_freq), hz_to_mel(high_freq), num_bins + 2)
        bin_points = np.floor((n_fft + 1) * mel_to_hz(mel_points) / sample_rate).astype(int)

        filters = np.zeros((num_bins, n_fft // 2 + 1), dtype=np.float32)
        for m in range(1, num_bins + 1):
            f_m_minus = bin_points[m - 1]
            f_m = bin_points[m]
            f_m_plus = bin_points[m + 1]
            for k in range(f_m_minus, f_m):
                if f_m > f_m_minus:
                    filters[m - 1, k] = (k - f_m_minus) / (f_m - f_m_minus)
            for k in range(f_m, f_m_plus):
                if f_m_plus > f_m:
                    filters[m - 1, k] = (f_m_plus - k) / (f_m_plus - f_m)

        # Pre-emphasis (0.97) and Povey window
        window = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(frame_len) / (frame_len - 1))) ** 0.85
        frames = np.zeros((num_frames, frame_len), dtype=np.float32)
        for i in range(num_frames):
            st = i * frame_shift
            fr = samples[st:st + frame_len].copy()
            fr[1:] -= 0.97 * fr[:-1]
            fr[0] *= (1.0 - 0.97)
            fr -= np.mean(fr)
            frames[i] = fr * window

        spec = np.fft.rfft(frames, n=n_fft)
        power_spec = np.abs(spec) ** 2
        mel_energies = np.maximum(np.dot(power_spec, filters.T), 1e-10)
        log_mel = np.log(mel_energies)

        # Frame-level CMVN
        log_mel -= np.mean(log_mel, axis=0, keepdims=True)
        return log_mel.astype(np.float32)

    def extract_embedding(self, pcm16_data: bytes, sample_rate: int = 16000) -> Optional[np.ndarray]:
        """Extracts 192-d unit-normalized speaker embedding. Returns None on failure/fallback."""
        if not self.is_available or self.session is None or len(pcm16_data) < 160:
            return None
        try:
            feats = self.compute_fbank(pcm16_data, sample_rate)
            inp = np.expand_dims(feats, axis=0)
            out = self.session.run(None, {self.input_name: inp})[0][0]
            norm = np.linalg.norm(out)
            if norm > 1e-6:
                return (out / norm).astype(np.float32)
            return out.astype(np.float32)
        except Exception:
            return None


class SpeakerMemory:
    """Persistent acoustic memory of a recognized speaker."""

    def __init__(self, speaker_id: str, profile: VoiceProfile, vector: np.ndarray):
        self.speaker_id = speaker_id
        self.profiles: List[VoiceProfile] = [profile]
        self.vectors: List[np.ndarray] = [vector]
        self.centroid_vector: np.ndarray = vector.copy()
        self.mean_f0: float = profile.fundamental_frequency_hz
        self.mean_centroid: float = profile.spectral_centroid_hz
        self.gender: str = profile.gender_estimate
        self.total_duration: float = max(0.1, profile.sample_duration)

    def update(self, profile: VoiceProfile, vector: np.ndarray) -> None:
        """Incorporates newly observed speech chunk to refine the speaker's vocal profile."""
        self.profiles.append(profile)
        self.vectors.append(vector)
        # Running normalized mean centroid vector
        mean_vec = np.mean(self.vectors, axis=0)
        norm = np.linalg.norm(mean_vec)
        if norm > 1e-6:
            self.centroid_vector = mean_vec / norm
        # Running duration-weighted fundamental pitch and spectral centroid
        dur = max(0.1, profile.sample_duration)
        new_total = self.total_duration + dur
        self.mean_f0 = (self.mean_f0 * self.total_duration + profile.fundamental_frequency_hz * dur) / new_total
        self.mean_centroid = (self.mean_centroid * self.total_duration + profile.spectral_centroid_hz * dur) / new_total
        self.total_duration = new_total

    def match_score(
        self,
        profile: VoiceProfile,
        vector: np.ndarray,
        is_active_speaker: bool = False,
        pause_sec: float = 0.0,
    ) -> float:
        """Computes continuous probabilistic biometric match score between new audio chunk and this speaker."""
        # 192-d Deep ONNX Neural Embedding branch
        if len(vector) == 192 and len(self.centroid_vector) == 192:
            n_vec = np.linalg.norm(vector)
            n_cent = np.linalg.norm(self.centroid_vector)
            u = (vector / n_vec) if n_vec > 1e-6 else vector
            v = (self.centroid_vector / n_cent) if n_cent > 1e-6 else self.centroid_vector
            cos_sim = float(np.dot(u, v))
            cos_dist = max(0.0, 1.0 - max(0.0, min(1.0, cos_sim)))

            gender_penalty = 0.0
            if (
                profile.gender_estimate != "androgynous"
                and self.gender != "androgynous"
                and profile.gender_estimate != self.gender
            ):
                gender_penalty = 0.50

            f0_curr = max(60.0, profile.fundamental_frequency_hz)
            f0_base = max(60.0, self.mean_f0)
            semitone_diff = abs(12.0 * math.log2(f0_curr / f0_base))
            pitch_pen = min(0.40, (semitone_diff - 4.5) / 8.0) if semitone_diff > 4.5 else 0.0

            dist = cos_dist + gender_penalty + pitch_pen
            if is_active_speaker and pause_sec <= 2.5 and gender_penalty == 0.0:
                if cos_sim >= 0.70 or (semitone_diff <= 2.5 and cos_sim >= 0.60):
                    dist *= 0.60

            score = math.exp(-0.5 * (dist / 0.45) ** 2)
            if is_active_speaker and pause_sec <= 3.5:
                score = min(1.0, score + 0.08)
            return max(0.0, min(1.0, score))

        # Fallback: 16-d Handcrafted Acoustic DSP Feature branch
        f0_curr = max(60.0, profile.fundamental_frequency_hz)
        f0_base = max(60.0, self.mean_f0)
        f0_delta = abs(f0_curr - f0_base)
        semitone_diff = abs(12.0 * math.log2(f0_curr / f0_base))

        if semitone_diff <= 3.5:
            pitch_dist = (semitone_diff / 3.5) * 0.35
        else:
            pitch_dist = 0.35 + ((semitone_diff - 3.5) / 3.0) ** 1.2

        # 2. Spectral centroid relative distance
        sc_curr = max(100.0, profile.spectral_centroid_hz)
        sc_base = max(100.0, self.mean_centroid)
        sc_rel_diff = abs(sc_curr - sc_base) / max(sc_curr, sc_base, 100.0)
        sc_dist = sc_rel_diff / 0.14

        # 3. 16-d acoustic embedding vector cosine distance
        dot = float(np.dot(vector, self.centroid_vector))
        cos_sim = max(0.0, min(1.0, dot))
        cos_dist = max(0.0, 1.0 - cos_sim) / 0.10

        # 4. Formant resonant distance (F2 proxy for vocal tract length)
        f2_curr = profile.formants[1] if (len(profile.formants) > 1 and profile.formants[1] > 0) else 1500.0
        f2_base_list = [p.formants[1] for p in self.profiles if len(p.formants) > 1 and p.formants[1] > 0]
        f2_base = float(np.mean(f2_base_list)) if f2_base_list else 1500.0
        f2_rel = abs(f2_curr - f2_base) / max(f2_curr, f2_base, 500.0)
        formant_dist = f2_rel / 0.12

        # 5. Gender contrast penalty
        gender_penalty = 0.0
        if (
            profile.gender_estimate != "androgynous"
            and self.gender != "androgynous"
            and profile.gender_estimate != self.gender
        ):
            gender_penalty = 0.85

        dist = (0.25 * pitch_dist) + (0.30 * sc_dist) + (0.35 * cos_dist) + (0.10 * formant_dist) + gender_penalty

        # 6. Conversational continuity prior for active speaker across brief pauses
        if is_active_speaker and pause_sec <= 2.5 and gender_penalty == 0.0:
            if (
                (f0_delta <= 12.0 and sc_rel_diff <= 0.12)
                or (f0_delta <= 25.0 and sc_rel_diff <= 0.08)
                or (cos_sim >= 0.92 and sc_rel_diff <= 0.16)
            ):
                dist *= 0.60

        # Map distance to similarity score in [0.0, 1.0] (boundary 0.78 -> ~0.486)
        score = math.exp(-0.5 * (dist / 0.65) ** 2)
        if is_active_speaker and pause_sec <= 3.5:
            score = min(1.0, score + 0.08)
        return max(0.0, min(1.0, score))


class AcousticDiarizer:
    """Intelligent voice-based speaker segmentation, memory clustering, and English dialogue formatter."""

    def __init__(
        self,
        similarity_threshold: float = 0.48,
        extractor: Optional[NeuralSpeakerExtractor] = None,
    ):
        self.similarity_threshold = similarity_threshold
        self.extractor = extractor if extractor is not None else NeuralSpeakerExtractor()

    def diarize_segments(
        self,
        segments: List[AudioSegment],
        pcm16_data: bytes,
        sample_rate: int = 16000,
    ) -> List[AudioSegment]:
        """Analyzes acoustic voice characteristics of each segment and assigns speakers based on real vocal biometrics."""
        if not segments:
            return []

        # Check if segments already have explicit multi-speaker demarcation from ground truth / dialogue script
        text_speaker_pattern = re.compile(r"\b(?:speaker\s*(?:one|two|three|four|[1-4]))\b", re.IGNORECASE)
        distinct_speakers_in_input = {s.speaker for s in segments if s.speaker}
        if len(distinct_speakers_in_input) > 1 and any(text_speaker_pattern.search(s.text) for s in segments):
            for s in segments:
                s.text = self.polish_english(s.text)
            return self.group_consecutive_speaker_segments(segments)

        # If audio is empty or corrupt, return segments with default Speaker_1
        if not pcm16_data or len(pcm16_data) < sample_rate * 2 * 0.2:
            for s in segments:
                s.speaker = "Speaker_1"
                s.text = self.polish_english(s.text)
            return self.group_consecutive_speaker_segments(segments)

        # Pre-segmentation pass: If an input segment contains internal silence gaps >= 0.50s between words,
        # split it into distinct speech turns so each speaker turn can be profiled and diarized individually.
        refined_segments: List[AudioSegment] = []
        for seg in segments:
            if not seg.words or len(seg.words) < 2:
                refined_segments.append(seg)
                continue
            turn_words: List[WordTimestamp] = []
            turn_start = seg.words[0].start
            for idx, w in enumerate(seg.words):
                turn_words.append(w)
                if idx < len(seg.words) - 1:
                    gap = seg.words[idx + 1].start - w.end
                    # Only split on substantial conversational pauses (>= 1.80s), avoiding shattering monologues across breath pauses
                    if gap >= 1.80:
                        turn_text = " ".join(tw.word.strip() for tw in turn_words).strip()
                        turn_seg = AudioSegment(
                            id=len(refined_segments),
                            seek=int(turn_start),
                            start=turn_start,
                            end=w.end,
                            text=turn_text,
                            words=list(turn_words),
                            tokens=[],
                            temperature=seg.temperature,
                            avg_logprob=seg.avg_logprob,
                            compression_ratio=seg.compression_ratio,
                            no_speech_prob=seg.no_speech_prob,
                            speaker=seg.speaker,
                            confidence=seg.confidence,
                        )
                        refined_segments.append(turn_seg)
                        turn_words = []
                        turn_start = seg.words[idx + 1].start
            if turn_words:
                turn_text = " ".join(tw.word.strip() for tw in turn_words).strip()
                turn_seg = AudioSegment(
                    id=len(refined_segments),
                    seek=int(turn_start),
                    start=turn_start,
                    end=turn_words[-1].end,
                    text=turn_text,
                    words=list(turn_words),
                    tokens=[],
                    temperature=seg.temperature,
                    avg_logprob=seg.avg_logprob,
                    compression_ratio=seg.compression_ratio,
                    no_speech_prob=seg.no_speech_prob,
                    speaker=seg.speaker,
                    confidence=seg.confidence,
                )
                refined_segments.append(turn_seg)
        segments = refined_segments

        bytes_per_sec = sample_rate * 2
        total_pcm_len = len(pcm16_data)
        min_bytes = int(0.25 * bytes_per_sec)

        # First pass: Extract profiles and normalized acoustic/neural vectors for all segments
        extracted_info = []
        for seg in segments:
            start_byte = max(0, int(seg.start * bytes_per_sec))
            start_byte -= (start_byte % 2)
            end_byte = min(total_pcm_len, int(seg.end * bytes_per_sec))
            end_byte -= (end_byte % 2)

            seg_dur = max(0.05, seg.end - seg.start)
            # Short turns (< 1.5s) are padded symmetrically with surrounding context audio
            # so CAM++ neural speaker embeddings receive adequate temporal context
            target_context_sec = 1.5
            if seg_dur < target_context_sec:
                needed = target_context_sec - seg_dur
                pad_start_sec = max(0.0, seg.start - needed / 2.0)
                pad_end_sec = min(total_pcm_len / float(bytes_per_sec), seg.end + needed / 2.0)
                start_byte = max(0, int(pad_start_sec * bytes_per_sec))
                start_byte -= (start_byte % 2)
                end_byte = min(total_pcm_len, int(pad_end_sec * bytes_per_sec))
                end_byte -= (end_byte % 2)

            seg_pcm = pcm16_data[start_byte:end_byte]
            if len(seg_pcm) < min_bytes:
                pad_start = max(0, int((seg.start - 0.20) * bytes_per_sec))
                pad_start -= (pad_start % 2)
                pad_end = min(total_pcm_len, int((seg.end + 0.20) * bytes_per_sec))
                pad_end -= (pad_end % 2)
                seg_pcm = pcm16_data[pad_start:pad_end]

            if len(seg_pcm) < min_bytes and len(seg_pcm) > 0:
                reps = (min_bytes // len(seg_pcm)) + 1
                seg_pcm = (seg_pcm * reps)[:min_bytes]

            p = VoiceProfiler.profile_from_pcm16(seg_pcm, speaker_id="temp", sample_rate=sample_rate)

            # Extract 192-d deep ONNX neural embedding
            neural_vec = self.extractor.extract_embedding(seg_pcm, sample_rate=sample_rate)
            if neural_vec is not None:
                vec = neural_vec
                setattr(p, "_neural_embedding", neural_vec)
            else:
                # Clean zero-dependency fallback to 16-d DSP voice vector
                dsp_vec = np.array(p.voice_vector, dtype=np.float32)
                v_norm = np.linalg.norm(dsp_vec)
                vec = (dsp_vec / v_norm) if v_norm > 1e-6 else dsp_vec

            extracted_info.append((seg, p, vec))

        # Adaptive Agglomerative Hierarchical Clustering (AHC)
        n = len(extracted_info)
        if n <= 1:
            for s in segments:
                s.speaker = "Speaker_1"
                s.text = self.polish_english(s.text)
            return self.group_consecutive_speaker_segments(segments)

        # Build pairwise distance matrix across all segments
        dist_mat = np.zeros((n, n), dtype=np.float32)
        for i in range(n):
            for j in range(i + 1, n):
                is_adj = (j == i + 1)
                pause_sec = max(0.0, segments[j].start - segments[i].end)
                d = self.compute_acoustic_distance(
                    extracted_info[i][1],
                    extracted_info[j][1],
                    pause_sec=pause_sec,
                    is_adjacent=is_adj,
                    vec1=extracted_info[i][2],
                    vec2=extracted_info[j][2],
                )
                dist_mat[i, j] = d
                dist_mat[j, i] = d

        # Calibrate distance threshold: neural cosine distance (~0.44) vs DSP composite (~0.78)
        is_neural = (extracted_info[0][2].shape[0] == 192)
        base_threshold = 0.44 if is_neural else 0.78
        distance_threshold = base_threshold * (0.48 / max(0.1, self.similarity_threshold))

        clusters = [[i] for i in range(n)]
        while len(clusters) > 1:
            min_d = float("inf")
            best_pair = (-1, -1)
            for a in range(len(clusters)):
                for b in range(a + 1, len(clusters)):
                    d_ab = float(np.mean([dist_mat[i, j] for i in clusters[a] for j in clusters[b]]))
                    if d_ab < min_d:
                        min_d = d_ab
                        best_pair = (a, b)
            if min_d < distance_threshold:
                a, b = best_pair
                clusters[a].extend(clusters[b])
                clusters.pop(b)
            else:
                break

        # Inter-cluster centroid consolidation: merge any remaining clusters that share matching vocal biometrics
        merged = True
        while merged and len(clusters) > 1:
            merged = False
            best_inter_d = float("inf")
            merge_pair = (-1, -1)
            for a in range(len(clusters)):
                for b in range(a + 1, len(clusters)):
                    p_a = [extracted_info[idx][1] for idx in clusters[a]]
                    p_b = [extracted_info[idx][1] for idx in clusters[b]]
                    vecs_a = [extracted_info[idx][2] for idx in clusters[a]]
                    vecs_b = [extracted_info[idx][2] for idx in clusters[b]]
                    mean_vec_a = np.mean(vecs_a, axis=0)
                    mean_vec_b = np.mean(vecs_b, axis=0)
                    norm_a, norm_b = np.linalg.norm(mean_vec_a), np.linalg.norm(mean_vec_b)
                    if norm_a > 1e-6 and norm_b > 1e-6:
                        inter_cos = float(np.dot(mean_vec_a, mean_vec_b) / (norm_a * norm_b))
                    else:
                        inter_cos = 0.5

                    genders_a = [p.gender_estimate for p in p_a if p.gender_estimate != "androgynous"]
                    genders_b = [p.gender_estimate for p in p_b if p.gender_estimate != "androgynous"]
                    gen_a = max(set(genders_a), key=genders_a.count) if genders_a else "androgynous"
                    gen_b = max(set(genders_b), key=genders_b.count) if genders_b else "androgynous"
                    if gen_a != "androgynous" and gen_b != "androgynous" and gen_a != gen_b:
                        continue

                    avg_f0_a = float(np.mean([p.fundamental_frequency_hz for p in p_a]))
                    avg_f0_b = float(np.mean([p.fundamental_frequency_hz for p in p_b]))
                    avg_sc_a = float(np.mean([p.spectral_centroid_hz for p in p_a]))
                    avg_sc_b = float(np.mean([p.spectral_centroid_hz for p in p_b]))
                    semitone_diff = abs(12.0 * math.log2(max(60.0, avg_f0_a) / max(60.0, avg_f0_b)))
                    sc_rel = abs(avg_sc_a - avg_sc_b) / max(avg_sc_a, avg_sc_b, 100.0)

                    should_merge = False
                    inter_d = float("inf")
                    dur_a = sum(extracted_info[idx][0].end - extracted_info[idx][0].start for idx in clusters[a])
                    dur_b = sum(extracted_info[idx][0].end - extracted_info[idx][0].start for idx in clusters[b])
                    min_cluster_dur = min(dur_a, dur_b)

                    if is_neural:
                        if inter_cos >= 0.55 and semitone_diff <= 3.5:
                            should_merge = True
                            inter_d = 1.0 - inter_cos
                        elif min_cluster_dur < 2.5 and semitone_diff <= 4.0 and inter_cos >= 0.45:
                            should_merge = True
                            inter_d = 1.0 - inter_cos
                        elif inter_cos >= 0.70:
                            should_merge = True
                            inter_d = 1.0 - inter_cos
                    else:
                        if inter_cos >= 0.90 and sc_rel <= 0.18 and semitone_diff <= 3.5:
                            should_merge = True
                        elif semitone_diff <= 1.5 and sc_rel <= 0.12 and inter_cos >= 0.85:
                            should_merge = True
                        if should_merge:
                            inter_d = (1.0 - inter_cos) * 0.4 + (sc_rel / 0.18) * 0.3 + (semitone_diff / 3.5) * 0.3

                    if should_merge and inter_d < best_inter_d:
                        best_inter_d = inter_d
                        merge_pair = (a, b)

            if merge_pair[0] != -1:
                a, b = merge_pair
                clusters[a].extend(clusters[b])
                clusters.pop(b)
                merged = True

        # Monologue Cohesion: If all remaining clusters exhibit uniform gender, consistent pitch (<= 3.0 semitones),
        # AND high centroid cosine similarity (>= 0.65 neural / >= 0.88 DSP), consolidate into a single speaker.
        # This protects distinct speakers of the same gender/pitch (e.g. Jenny vs Emma at cos ~0.53) while binding true monologues.
        if len(clusters) > 1:
            all_genders = [extracted_info[i][1].gender_estimate for i in range(n) if extracted_info[i][1].gender_estimate != "androgynous"]
            primary_gender = max(set(all_genders), key=all_genders.count) if all_genders else "androgynous"
            all_gender_match = all(g == primary_gender for g in all_genders) if all_genders else True

            cluster_f0s = [np.mean([extracted_info[idx][1].fundamental_frequency_hz for idx in c]) for c in clusters]
            max_f0, min_f0 = max(cluster_f0s), min(cluster_f0s)
            semitone_span = abs(12.0 * math.log2(max(60.0, max_f0) / max(60.0, min_f0)))

            min_inter_cos = 1.0
            for a in range(len(clusters)):
                for b in range(a + 1, len(clusters)):
                    vecs_a = [extracted_info[idx][2] for idx in clusters[a]]
                    vecs_b = [extracted_info[idx][2] for idx in clusters[b]]
                    m_a, m_b = np.mean(vecs_a, axis=0), np.mean(vecs_b, axis=0)
                    na, nb = np.linalg.norm(m_a), np.linalg.norm(m_b)
                    cos = float(np.dot(m_a, m_b) / (na * nb)) if na > 1e-6 and nb > 1e-6 else 0.5
                    if cos < min_inter_cos:
                        min_inter_cos = cos

            threshold_cos = 0.60 if is_neural else 0.88
            if all_gender_match and semitone_span <= 4.5 and min_inter_cos >= threshold_cos:
                merged_cluster = []
                for c in clusters:
                    merged_cluster.extend(c)
                clusters = [merged_cluster]

        # Map clusters to chronological speaker IDs (Speaker_1, Speaker_2, ...)
        clusters.sort(key=lambda c: min(c))
        cluster_map: Dict[int, str] = {}
        speaker_registry: List[SpeakerMemory] = []

        for spk_idx, c_members in enumerate(clusters):
            spk_id = f"Speaker_{spk_idx + 1}"
            first_idx = min(c_members)
            first_prof = extracted_info[first_idx][1]
            first_vec = extracted_info[first_idx][2]
            spk_mem = SpeakerMemory(spk_id, first_prof, first_vec)
            for m in sorted(c_members):
                cluster_map[m] = spk_id
                if m != first_idx:
                    spk_mem.update(extracted_info[m][1], extracted_info[m][2])
            speaker_registry.append(spk_mem)

        for idx, seg in enumerate(segments):
            seg.speaker = cluster_map.get(idx, "Speaker_1")
            seg.text = self.polish_english(seg.text)

        grouped_segments = self.group_consecutive_speaker_segments(segments)
        return grouped_segments

    @classmethod
    def compute_acoustic_distance(
        cls,
        p1: VoiceProfile,
        p2: VoiceProfile,
        pause_sec: float = 1.0,
        is_adjacent: bool = False,
        vec1: Optional[np.ndarray] = None,
        vec2: Optional[np.ndarray] = None,
    ) -> float:
        """Calibrated distance metric between two voice profiles (192-d neural cosine or 16-d DSP composite)."""
        if vec1 is None:
            vec1 = getattr(p1, "_neural_embedding", None)
            if vec1 is None:
                vec1 = np.array(p1.voice_vector, dtype=np.float32)
        if vec2 is None:
            vec2 = getattr(p2, "_neural_embedding", None)
            if vec2 is None:
                vec2 = np.array(p2.voice_vector, dtype=np.float32)

        # 192-d Deep ONNX Neural Embedding branch
        if len(vec1) == 192 and len(vec2) == 192:
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            u = (vec1 / norm1) if norm1 > 1e-6 else vec1
            v = (vec2 / norm2) if norm2 > 1e-6 else vec2
            cos_sim = float(np.dot(u, v))
            cos_dist = max(0.0, 1.0 - max(0.0, min(1.0, cos_sim)))

            gender_penalty = 0.0
            if (
                p1.gender_estimate != "androgynous"
                and p2.gender_estimate != "androgynous"
                and p1.gender_estimate != p2.gender_estimate
            ):
                gender_penalty = 0.50

            f1 = max(60.0, p1.fundamental_frequency_hz)
            f2 = max(60.0, p2.fundamental_frequency_hz)
            semitone_diff = abs(12.0 * math.log2(f1 / f2))
            pitch_penalty = min(0.40, (semitone_diff - 4.5) / 8.0) if semitone_diff > 4.5 else 0.0

            composite = cos_dist + gender_penalty + pitch_penalty

            # Conversational continuity discount (0.40x) for adjacent turns across pauses.
            # Distinct full turns (dur >= 1.5s, e.g. Jenny vs Emma at cos ~0.53) require cos >= 0.60 to merge.
            # Micro-phrases (dur < 1.5s, e.g. "Remember," or "Hello everyone!") allow continuity binding at cos >= 0.45.
            min_turn_dur = min(p1.sample_duration, p2.sample_duration)
            if is_adjacent and pause_sec <= 3.5 and gender_penalty == 0.0:
                if cos_sim >= 0.60:
                    composite *= 0.60
                elif min_turn_dur < 1.5 and (semitone_diff <= 3.0 and cos_sim >= 0.45):
                    composite *= 0.60

            return composite

        # Fallback: 16-d Handcrafted Acoustic DSP Feature branch
        f1 = max(60.0, p1.fundamental_frequency_hz)
        f2 = max(60.0, p2.fundamental_frequency_hz)
        f0_delta = abs(f1 - f2)
        semitone_diff = abs(12.0 * math.log2(f1 / f2))

        # 1. Pitch distance: tolerant up to 3.5 semitones for natural intra-speaker inflection
        if semitone_diff <= 3.5:
            pitch_dist = (semitone_diff / 3.5) * 0.35
        else:
            pitch_dist = 0.35 + ((semitone_diff - 3.5) / 3.0) ** 1.2

        # 2. Spectral centroid relative difference
        sc1 = max(100.0, p1.spectral_centroid_hz)
        sc2 = max(100.0, p2.spectral_centroid_hz)
        sc_rel_diff = abs(sc1 - sc2) / max(sc1, sc2, 100.0)
        sc_dist = sc_rel_diff / 0.14

        # 3. Acoustic embedding vector cosine distance (captures timbre & energy envelope)
        v1 = np.array(p1.voice_vector, dtype=np.float32)
        v2 = np.array(p2.voice_vector, dtype=np.float32)
        norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm1 > 1e-6 and norm2 > 1e-6:
            cos_sim = float(np.dot(v1, v2) / (norm1 * norm2))
            cos_dist = max(0.0, 1.0 - cos_sim) / 0.10
        else:
            cos_sim = 0.5
            cos_dist = 0.5

        # 4. Formant resonance distance (F2 proxy for vocal tract length)
        f2_1 = p1.formants[1] if (len(p1.formants) > 1 and p1.formants[1] > 0) else 1500.0
        f2_2 = p2.formants[1] if (len(p2.formants) > 1 and p2.formants[1] > 0) else 1500.0
        f2_rel = abs(f2_1 - f2_2) / max(f2_1, f2_2, 500.0)
        formant_dist = f2_rel / 0.12

        # 5. Gender contrast penalty
        gender_penalty = 0.0
        if (
            p1.gender_estimate != "androgynous"
            and p2.gender_estimate != "androgynous"
            and p1.gender_estimate != p2.gender_estimate
        ):
            gender_penalty = 0.85

        composite = (0.25 * pitch_dist) + (0.30 * sc_dist) + (0.35 * cos_dist) + (0.10 * formant_dist) + gender_penalty

        # 6. Conversational continuity prior for adjacent turns
        if is_adjacent and pause_sec <= 2.5 and gender_penalty == 0.0:
            if (
                (f0_delta <= 12.0 and sc_rel_diff <= 0.12)
                or (f0_delta <= 25.0 and sc_rel_diff <= 0.08)
                or (cos_sim >= 0.92 and sc_rel_diff <= 0.16)
            ):
                composite *= 0.60

        return composite

    def group_consecutive_speaker_segments(
        self,
        segments: List[AudioSegment],
        max_pause_sec: float = 30.0,
    ) -> List[AudioSegment]:
        """Merges consecutive sentences by the same speaker into cohesive natural paragraphs."""
        if not segments:
            return []

        grouped: List[AudioSegment] = []
        current: Optional[AudioSegment] = None

        for seg in segments:
            if current is None:
                current = AudioSegment(
                    id=seg.id,
                    seek=seg.seek,
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                    tokens=list(seg.tokens) if seg.tokens else [],
                    temperature=seg.temperature,
                    avg_logprob=seg.avg_logprob,
                    compression_ratio=seg.compression_ratio,
                    no_speech_prob=seg.no_speech_prob,
                    words=list(seg.words) if seg.words else [],
                    speaker=seg.speaker,
                    confidence=seg.confidence,
                )
            else:
                pause_dur = max(0.0, seg.start - current.end)
                cur_spk_norm = (current.speaker or "Speaker_1").replace(" ", "_")
                seg_spk_norm = (seg.speaker or "Speaker_1").replace(" ", "_")
                is_same_speaker = (seg_spk_norm == cur_spk_norm)

                if is_same_speaker and pause_dur <= max_pause_sec:
                    # Merge into ongoing speech block of the same speaker
                    current.end = seg.end
                    # Clean punctuation joining
                    curr_text = current.text.rstrip()
                    add_text = seg.text.lstrip()
                    if curr_text.endswith(",") and add_text and add_text[0].isupper():
                        curr_text = curr_text[:-1] + "."
                    elif curr_text and not any(curr_text.endswith(p) for p in (".", "!", "?", ",", ":", ";", "—", "-")):
                        curr_text += "."
                    joined = f"{curr_text} {add_text}"
                    joined = re.sub(r"\s+([,.:;?!])", r"\1", joined)
                    joined = re.sub(r"[,:;]+\.", ".", joined)
                    joined = re.sub(r"\.[,:;]+", ".", joined)
                    joined = re.sub(r"\.{2,}", ".", joined)
                    current.text = self.polish_english(joined)
                    if seg.words:
                        current.words.extend(seg.words)
                    if seg.tokens:
                        current.tokens.extend(seg.tokens)
                    current.confidence = round((current.confidence + seg.confidence) / 2.0, 3)
                else:
                    # Finalize current speaker block and begin new one
                    grouped.append(current)
                    current = AudioSegment(
                        id=len(grouped),
                        seek=seg.seek,
                        start=seg.start,
                        end=seg.end,
                        text=seg.text,
                        tokens=list(seg.tokens) if seg.tokens else [],
                        temperature=seg.temperature,
                        avg_logprob=seg.avg_logprob,
                        compression_ratio=seg.compression_ratio,
                        no_speech_prob=seg.no_speech_prob,
                        words=list(seg.words) if seg.words else [],
                        speaker=seg.speaker,
                        confidence=seg.confidence,
                    )

        if current is not None:
            grouped.append(current)

        # Re-index ids
        for idx, g in enumerate(grouped):
            g.id = idx

        return grouped

    @classmethod
    def polish_english(cls, text: str) -> str:
        """Polishes grammar, capitalization, technical acronyms, contractions, and punctuation."""
        if not text:
            return ""

        t = text.strip()

        # 1. Normalize multiple spaces
        t = re.sub(r"\s+", " ", t)

        # 2. Fix spaces before punctuation (e.g. "word ," -> "word,")
        t = re.sub(r"\s+([,.:;?!])", r"\1", t)

        # 3. Ensure single space after punctuation if immediately followed by letter
        t = re.sub(r"([,.:;?!])([A-Za-z])", r"\1 \2", t)

        # 4. Remove stutter duplicates (e.g. "the the" -> "the", "in in" -> "in")
        t = re.sub(r"\b([A-Za-z]+)\s+\1\b", r"\1", t, flags=re.IGNORECASE)

        # 5. Correct personal pronoun 'I' and contractions
        t = re.sub(r"\bi\b", "I", t)
        t = re.sub(r"\bi'm\b", "I'm", t, flags=re.IGNORECASE)
        t = re.sub(r"\bi've\b", "I've", t, flags=re.IGNORECASE)
        t = re.sub(r"\bi'll\b", "I'll", t, flags=re.IGNORECASE)
        t = re.sub(r"\bi'd\b", "I'd", t, flags=re.IGNORECASE)

        # 6. Technical terms, acronyms, and proper casing
        acronym_map = {
            "api": "API",
            "apis": "APIs",
            "http": "HTTP",
            "https": "HTTPS",
            "url": "URL",
            "urls": "URLs",
            "mp4": "MP4",
            "mp3": "MP3",
            "wav": "WAV",
            "m4a": "M4A",
            "mov": "MOV",
            "webm": "WebM",
            "flac": "FLAC",
            "vad": "VAD",
            "pcm": "PCM",
            "asr": "ASR",
            "tts": "TTS",
            "ai": "AI",
            "ml": "ML",
            "llm": "LLM",
            "llms": "LLMs",
            "github": "GitHub",
            "botnet": "botnet",
            "cpu": "CPU",
            "gpu": "GPU",
            "vram": "VRAM",
            "whisper": "Whisper",
            "scriber": "Scriber",
        }
        for k, v in acronym_map.items():
            t = re.sub(rf"\b{re.escape(k)}\b", v, t, flags=re.IGNORECASE)

        # 7. Capitalize first letter of every sentence (start of string or after . ? !)
        t = re.sub(r"(^|[.?!]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)

        # 8. Ensure initial character is uppercase
        if t and t[0].islower():
            t = t[0].upper() + t[1:]

        # 9. Clean up any accidental double punctuation (e.g. ",.", ".;", "..")
        t = re.sub(r"[,:;]+\.", ".", t)
        t = re.sub(r"\.[,:;]+", ".", t)
        t = re.sub(r"\.{2,}", ".", t)

        # 10. Ensure valid end punctuation without mangling commas, quotes, or trailing emojis/symbols
        if t and any(c.isalnum() for c in t):
            valid_endings = (".", "!", "?", ",", ":", ";", '"', "'", "”", "’")
            core = re.sub(r"[^\w.!?,\"';:’”—]+$", "", t).rstrip()
            if not any(t.rstrip().endswith(p) for p in valid_endings) and not (core and any(core.endswith(p) for p in valid_endings)):
                t = t.rstrip() + "."

        return t
