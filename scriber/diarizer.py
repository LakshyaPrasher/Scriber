"""Acoustic Speaker Diarization & Timbre Memory Engine.

Performs genuine voice-based speaker recognition:
1. Slices 16kHz PCM audio for each transcription segment.
2. Extracts acoustic voice embeddings (F0 pitch, spectral centroid, ZCR, dynamic timbre).
3. Maintains persistent SpeakerMemory across the entire recording:
   - Compares incoming speech to known speaker acoustic centroids using cosine similarity & pitch compatibility.
   - Only assigns a new speaker when an authentic voice change is detected (similarity < threshold).
   - Re-identifies previous speakers when they talk again later in the audio (acoustic voice memory).
4. Groups consecutive same-speaker turns into cohesive, beautifully formatted English dialogue blocks.
5. Polishes English grammar, capitalization, technical acronyms, and punctuation.
"""

from __future__ import annotations

import math
import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from scriber.exceptions import JobCancelledException
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
                # Diarization issues many short, sequential inference calls per
                # recording. ONNX Runtime's default intra-op spin-wait keeps worker
                # threads hot between those calls, which burns CPU during the
                # NumPy phases and makes later calls progressively slower
                # (measured 3-4x across a single diarization pass). Sleeping the
                # pool between calls is scheduling-only and numerically identical.
                session_options = ort.SessionOptions()
                try:
                    session_options.add_session_config_entry("session.intra_op.allow_spinning", "0")
                except Exception:
                    pass
                self.session = ort.InferenceSession(self.model_path, sess_options=session_options, providers=providers)
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

    _FILTERS: Optional[np.ndarray] = None
    _WINDOW: Optional[np.ndarray] = None

    @classmethod
    def _get_filterbank_and_window(cls, sample_rate: int = 16000, n_fft: int = 512, num_bins: int = 80, frame_len: int = 400) -> Tuple[np.ndarray, np.ndarray]:
        if cls._FILTERS is not None and cls._WINDOW is not None:
            return cls._FILTERS, cls._WINDOW

        low_freq = 20.0
        high_freq = sample_rate / 2.0

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

        window = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(frame_len) / (frame_len - 1))) ** 0.85
        cls._FILTERS = filters
        cls._WINDOW = window.astype(np.float32)
        return cls._FILTERS, cls._WINDOW

    # Frames per vectorized block: bounds peak memory (~25 MB) for very long
    # segments while keeping the common 1-30 s turn in a single FFT batch.
    _FBANK_BLOCK_FRAMES = 8192

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

        if len(samples) < frame_len:
            samples = np.pad(samples, (0, frame_len - len(samples)), mode="constant")
        num_frames = max(1, (len(samples) - frame_len) // frame_shift + 1)

        filters, window = cls._get_filterbank_and_window(sample_rate, n_fft=n_fft, frame_len=frame_len)

        # Vectorized framing: one strided view over the signal, copied block by
        # block so pre-emphasis/windowing can run in place without touching the
        # source samples. Same frame length/shift/FFT as the scalar version.
        framed = np.lib.stride_tricks.sliding_window_view(samples, frame_len)[::frame_shift]
        block = cls._FBANK_BLOCK_FRAMES
        pre_emphasis = np.float32(1.0 - 0.97)
        log_mel_blocks: List[np.ndarray] = []

        for start in range(0, num_frames, block):
            frames = np.array(framed[start:start + block], dtype=np.float32)
            # Pre-emphasis (0.97) and mean removal
            frames[:, 1:] -= 0.97 * frames[:, :-1]
            frames[:, 0] *= pre_emphasis
            frames -= frames.mean(axis=1, keepdims=True)
            frames *= window

            spec = np.fft.rfft(frames, n=n_fft, axis=1)
            power_spec = np.abs(spec) ** 2
            mel_energies = np.maximum(np.dot(power_spec, filters.T), 1e-10)
            log_mel_blocks.append(np.log(mel_energies))

        log_mel = log_mel_blocks[0] if len(log_mel_blocks) == 1 else np.concatenate(log_mel_blocks, axis=0)

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
        """Computes continuous probabilistic match score between new audio chunk and this speaker."""
        # 192-d Deep ONNX Neural Embedding branch
        if len(vector) == 192 and len(self.centroid_vector) == 192:
            n_vec = np.linalg.norm(vector)
            n_cent = np.linalg.norm(self.centroid_vector)
            u = (vector / n_vec) if n_vec > 1e-6 else vector
            v = (self.centroid_vector / n_cent) if n_cent > 1e-6 else self.centroid_vector
            cos_sim = float(np.dot(u, v))
            cos_dist = max(0.0, 1.0 - max(0.0, min(1.0, cos_sim)))

            f0_curr = max(60.0, profile.fundamental_frequency_hz)
            f0_base = max(60.0, self.mean_f0)
            semitone_diff = abs(12.0 * math.log2(f0_curr / f0_base))

            # Pitch tolerance: allow natural intra-speaker vocal variation up to 5.0 semitones
            pitch_pen = 0.0
            if cos_sim < 0.65 and semitone_diff > 5.0:
                pitch_pen = min(0.30, (semitone_diff - 5.0) / 8.0)

            # Robust gender penalty: only penalize if pitch difference is large (> 7 semitones)
            gender_penalty = 0.0
            if (
                profile.gender_estimate != "androgynous"
                and self.gender != "androgynous"
                and profile.gender_estimate != self.gender
                and semitone_diff > 7.0
            ):
                gender_penalty = 0.40

            dist = cos_dist + gender_penalty + pitch_pen
            if is_active_speaker and pause_sec <= 3.5 and gender_penalty == 0.0:
                if cos_sim >= 0.60 or (semitone_diff <= 3.0 and cos_sim >= 0.45):
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
        max_speakers: int = 10,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_speakers = max(1, int(max_speakers))
        self.extractor = extractor if extractor is not None else NeuralSpeakerExtractor()

    def diarize_segments(
        self,
        segments: List[AudioSegment],
        pcm16_data: bytes,
        sample_rate: int = 16000,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> List[AudioSegment]:
        """Analyzes acoustic voice characteristics of each segment and assigns speakers based on real vocal timbre."""
        if cancel_checker and cancel_checker():
            raise JobCancelledException("Diarization cancelled before starting")

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

        # Pre-segmentation pass: Split into distinct conversational turns based on word timestamps,
        # pause duration, sentence boundaries, and question transitions.
        refined_segments: List[AudioSegment] = []
        QUESTION_WORDS = {
            "how", "what", "why", "who", "where", "when", "did", "do", "does",
            "are", "is", "can", "could", "would", "will", "so", "tell", "alright"
        }

        for seg in segments:
            if not seg.words or len(seg.words) < 2:
                refined_segments.append(seg)
                continue
            turn_words: List[WordTimestamp] = []
            turn_start = seg.words[0].start
            for idx, w in enumerate(seg.words):
                turn_words.append(w)
                if idx < len(seg.words) - 1:
                    next_w = seg.words[idx + 1]
                    gap = next_w.start - w.end
                    w_text = w.word.strip()
                    next_w_text = next_w.word.strip()
                    ends_question = w_text.endswith("?")
                    ends_sentence = w_text.endswith((".", "!"))
                    next_is_q_starter = (
                        next_w_text.lower().rstrip("?,.!") in QUESTION_WORDS
                        and len(next_w_text) > 0
                        and next_w_text[0].isupper()
                    )

                    should_split = False
                    if ends_question and gap >= 0.05:
                        should_split = True
                    elif ends_sentence and next_is_q_starter and gap >= 0.05:
                        should_split = True
                    elif ends_sentence and gap >= 0.25:
                        should_split = True
                    elif gap >= 0.45:
                        should_split = True
                    elif (w.end - turn_start) >= 20.0 and ends_sentence and gap >= 0.10:
                        should_split = True

                    if should_split:
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
                        turn_start = next_w.start

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
        segments = [s for s in refined_segments if s.end > s.start and s.text.strip()]

        bytes_per_sec = sample_rate * 2
        total_pcm_len = len(pcm16_data)
        min_bytes = int(0.25 * bytes_per_sec)

        # First pass: Extract profiles and normalized acoustic/neural vectors for all segments
        extracted_info = []
        total_segs = len(segments)

        for idx_seg, seg in enumerate(segments):
            if cancel_checker and cancel_checker():
                raise JobCancelledException("Diarization aborted by cancellation signal")
            seg_dur = max(0.05, seg.end - seg.start)
            start_byte = max(0, int(seg.start * bytes_per_sec))
            start_byte -= (start_byte % 2)
            end_byte = min(total_pcm_len, int(seg.end * bytes_per_sec))
            end_byte -= (end_byte % 2)

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

            p = VoiceProfiler.profile_fast(seg_pcm, speaker_id="temp", sample_rate=sample_rate)

            # Extract 192-d deep ONNX neural embedding
            neural_vec = self.extractor.extract_embedding(seg_pcm, sample_rate=sample_rate)
            if neural_vec is not None:
                vec = np.asarray(neural_vec, dtype=np.float32)
                setattr(p, "_neural_embedding", vec)
            else:
                # Clean zero-dependency fallback to 16-d DSP voice vector
                dsp_vec = np.array(p.voice_vector, dtype=np.float32)
                v_norm = np.linalg.norm(dsp_vec)
                normed_dsp = (dsp_vec / v_norm) if v_norm > 1e-6 else dsp_vec
                if self.extractor.is_available:
                    vec = np.pad(normed_dsp, (0, 192 - len(normed_dsp)), mode="constant")
                else:
                    vec = normed_dsp

            extracted_info.append((seg, p, vec))

            if progress_callback and (idx_seg % 15 == 0 or idx_seg == total_segs - 1):
                frac = (idx_seg + 1) / max(1, total_segs)
                pct = 80 + int(frac * 16)
                progress_callback({
                    "percent": pct,
                    "stage": "diarization",
                    "phase": f"Step 4 of 4 · Labelling speakers ({pct}%)",
                    "title": "Identifying speakers",
                    "subtitle": f"Reviewing speech segment {idx_seg + 1} of {total_segs}...",
                    "current_time_sec": round(seg.end, 2),
                    "total_duration_sec": round(segments[-1].end if segments else 0.0, 2),
                    "speed_factor": 1.0,
                    "elapsed_sec": 0.0,
                    "eta_sec": max(0.5, round((total_segs - idx_seg) * 0.01, 1)),
                })

        # Adaptive Agglomerative Hierarchical Clustering (AHC)
        n = len(extracted_info)
        if n <= 1:
            for s in segments:
                s.speaker = "Speaker_1"
                s.text = self.polish_english(s.text)
            return self.group_consecutive_speaker_segments(segments)

        # Calibrate distance threshold: neural cosine distance vs DSP composite.
        # A STRICT cut keeps distinct voices apart and prevents the cast from collapsing
        # into one or two voices (the previously reported bug). Same-voice turns that AHC
        # splits are deliberately reunited by the conservative re-merge step below, which
        # requires both high centroid cosine AND close pitch, so it cannot mistake a
        # different speaker for a returning one.
        is_neural = (len(extracted_info[0][2]) == 192)
        base_threshold = 0.14 if is_neural else 0.78
        distance_threshold = base_threshold * (0.48 / max(0.1, self.similarity_threshold))

        # Vectorized pairwise distance computation
        if is_neural:
            embs = np.array([x[2] for x in extracted_info], dtype=np.float32)
            norms = np.linalg.norm(embs, axis=1, keepdims=True)
            embs_norm = np.where(norms > 1e-6, embs / norms, embs)
            cos_sim = np.clip(np.dot(embs_norm, embs_norm.T), -1.0, 1.0)
            cos_dist = np.maximum(0.0, 1.0 - np.maximum(0.0, cos_sim))

            f0s = np.array([max(60.0, x[1].fundamental_frequency_hz) for x in extracted_info], dtype=np.float32)
            semitone_diff = np.abs(12.0 * np.log2(f0s[:, None] / f0s[None, :]))

            genders = np.array([x[1].gender_estimate for x in extracted_info])
            gen_diff = (genders[:, None] != genders[None, :]) & (genders[:, None] != "androgynous") & (genders[None, :] != "androgynous") & (semitone_diff > 6.0)
            gender_penalty = np.where(gen_diff, 0.45, 0.0).astype(np.float32)
            pitch_penalty = np.where(semitone_diff > 5.5, np.minimum(0.35, (semitone_diff - 5.5) / 8.0), 0.0).astype(np.float32)

            dist_mat = (cos_dist + gender_penalty + pitch_penalty).astype(np.float32)

            # Adjacent-turn continuity is intentionally NOT applied as a distance
            # discount here. Discounting adjacent turns was the prior failure mode:
            # distinct speakers trading short interjections got force-merged into one
            # voice. Same-speaker continuity is instead restored by the conservative
            # centroid re-merge (cosine + pitch + gender) below.
        else:
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

        # Fast Lance-Williams Agglomerative Hierarchical Clustering (average linkage)
        clusters = [[i] for i in range(n)]
        cluster_sizes = np.ones(n, dtype=np.int32)
        dist_copy = dist_mat.copy()
        np.fill_diagonal(dist_copy, np.inf)

        mins = np.min(dist_copy, axis=1)
        min_indices = np.argmin(dist_copy, axis=1)

        merges = 0
        while merges < n - 1:
            best_a = int(np.argmin(mins))
            min_d = float(mins[best_a])
            if min_d >= distance_threshold:
                break
            best_b = int(min_indices[best_a])
            if best_a > best_b:
                best_a, best_b = best_b, best_a

            sa = cluster_sizes[best_a]
            sb = cluster_sizes[best_b]
            new_s = sa + sb

            d_ak = dist_copy[best_a]
            d_bk = dist_copy[best_b]
            new_d = (sa * d_ak + sb * d_bk) / new_s
            dist_copy[best_a] = new_d
            dist_copy[:, best_a] = new_d
            dist_copy[best_a, best_a] = np.inf

            dist_copy[best_b] = np.inf
            dist_copy[:, best_b] = np.inf
            mins[best_b] = np.inf
            cluster_sizes[best_a] = new_s

            mins[best_a] = np.min(dist_copy[best_a])
            min_indices[best_a] = np.argmin(dist_copy[best_a])

            mask = (min_indices == best_a) | (min_indices == best_b)
            mask[best_b] = False
            if np.any(mask):
                affected = np.where(mask)[0]
                mins[affected] = np.min(dist_copy[affected], axis=1)
                min_indices[affected] = np.argmin(dist_copy[affected], axis=1)

            clusters[best_a].extend(clusters[best_b])
            clusters[best_b] = []
            merges += 1

        clusters = [c for c in clusters if c]

        # Single-pass consolidation of near-duplicate clusters.
        # Similarities are measured on the ORIGINAL cluster centroids and never
        # re-merged iteratively, so a group of similar voices cannot "drift" into
        # one giant cluster (the previous failure mode).
        if len(clusters) > 1:

            def _cluster_centroid(members):
                mean_vec = np.mean([extracted_info[i][2] for i in members], axis=0)
                nrm = np.linalg.norm(mean_vec)
                return (mean_vec / nrm) if nrm > 1e-6 else mean_vec

            def _cluster_f0(members):
                vals = [
                    extracted_info[i][1].fundamental_frequency_hz
                    for i in members
                    if extracted_info[i][1].fundamental_frequency_hz > 0
                ]
                return float(np.median(vals)) if vals else 0.0

            def _cluster_gender(members):
                gens = [
                    extracted_info[i][1].gender_estimate
                    for i in members
                    if extracted_info[i][1].gender_estimate not in ("androgynous", "unmeasured")
                ]
                return max(set(gens), key=gens.count) if gens else "androgynous"

            orig_centroids = [_cluster_centroid(c) for c in clusters]
            orig_f0 = [_cluster_f0(c) for c in clusters]
            orig_gender = [_cluster_gender(c) for c in clusters]

            parent = list(range(len(clusters)))

            def _find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            merge_sim = 0.85 if is_neural else 0.92
            candidates = []
            for a in range(len(clusters)):
                for b in range(a + 1, len(clusters)):
                    ga, gb = orig_gender[a], orig_gender[b]
                    if ga != gb and ga != "androgynous" and gb != "androgynous":
                        continue
                    fa, fb = orig_f0[a], orig_f0[b]
                    if fa > 0 and fb > 0:
                        s_diff = abs(12.0 * math.log2(fa / fb))
                    else:
                        s_diff = 0.0
                    # Only reunite clusters that are genuinely the same voice: high
                    # centroid cosine AND close pitch. A 4-semitone limit tolerates
                    # natural intra-speaker inflection while still blocking confusable
                    # distinct voices (e.g. two male TTS voices ~4 semitones apart).
                    if s_diff > 4.0:
                        continue
                    sim = float(np.dot(orig_centroids[a], orig_centroids[b]))
                    if sim >= merge_sim:
                        candidates.append((sim, a, b))

            candidates.sort(key=lambda t: t[0], reverse=True)
            for _, a, b in candidates:
                ra, rb = _find(a), _find(b)
                if ra != rb:
                    parent[rb] = ra

            if any(parent[i] != i for i in range(len(parent))):
                grouped: Dict[int, List[int]] = {}
                for i in range(len(clusters)):
                    grouped.setdefault(_find(i), []).extend(clusters[i])
                clusters = list(grouped.values())

        # Keep up to max_speakers voices that actually carry the recording, and
        # fold short micro-clusters into the most compatible voice using pitch and
        # timbre. The duration floor is deliberately low so short-but-distinct
        # speakers are kept as their own voice instead of being folded away.
        if len(clusters) > 1:
            total_dur = float(sum(max(0.0, s.end - s.start) for s in segments))

            def _cluster_duration(members):
                return float(
                    sum(max(0.0, extracted_info[i][0].end - extracted_info[i][0].start) for i in members)
                )

            ranked = sorted(clusters, key=_cluster_duration, reverse=True)
            min_track = max(0.5, 0.002 * total_dur)
            primary = [c for c in ranked if _cluster_duration(c) >= min_track][: self.max_speakers]
            if not primary:
                primary = ranked[: self.max_speakers]
            primary_ids = {id(c) for c in primary}
            tail = [c for c in ranked if id(c) not in primary_ids]

            if tail:
                p_centroids = [_cluster_centroid(c) for c in primary]
                p_f0 = [_cluster_f0(c) for c in primary]
                p_gender = [_cluster_gender(c) for c in primary]

                for oc in tail:
                    o_vec = _cluster_centroid(oc)
                    o_f0 = _cluster_f0(oc)
                    o_gender = _cluster_gender(oc)
                    best_idx = 0
                    best_cost = float("inf")
                    for pi in range(len(primary)):
                        cost = 1.0 - float(np.dot(o_vec, p_centroids[pi]))
                        pf = p_f0[pi]
                        if o_f0 > 0 and pf > 0:
                            semis = abs(12.0 * math.log2(o_f0 / pf))
                            if semis > 4.0:
                                cost += min(0.40, (semis - 4.0) / 10.0)
                        pg = p_gender[pi]
                        if o_gender != pg and o_gender != "androgynous" and pg != "androgynous":
                            cost += 0.45
                        if cost < best_cost:
                            best_cost = cost
                            best_idx = pi
                    # Conservative tail assignment: only fold a short cluster into an
                    # existing voice when it is genuinely similar (centroid cosine >=
                    # ~0.72). Otherwise keep it as a distinct speaker if there is room.
                    # Once the cap is reached, fold into the closest voice so no turn
                    # is left unlabelled (which would otherwise default to Speaker_1).
                    if best_cost <= 0.28 or len(primary) >= self.max_speakers:
                        primary[best_idx].extend(oc)
                    else:
                        primary.append(oc)

            # Dominant-speaker unification: when one voice carries the clear majority
            # of the audio, absorb short matching fragments into it. This reunites a
            # single continuous speaker (e.g. a monologue) that the strict AHC cut split
            # into fragments, without merging two genuine alternating speakers, because
            # in a dialogue neither speaker dominates enough to qualify.
            if len(primary) > 1:
                total_dur = float(sum(_cluster_duration(c) for c in primary))
                dom_idx = max(range(len(primary)), key=lambda pi: _cluster_duration(primary[pi]))
                dominant = primary[dom_idx]
                d_dur = _cluster_duration(dominant)
                if total_dur > 0 and d_dur / total_dur > 0.50:
                    d_vec = _cluster_centroid(dominant)
                    d_f0 = _cluster_f0(dominant)
                    d_gender = _cluster_gender(dominant)
                    absorb = []
                    for pi in range(len(primary)):
                        if pi == dom_idx:
                            continue
                        c = primary[pi]
                        c_dur = _cluster_duration(c)
                        if c_dur >= 3.0:
                            continue
                        if d_dur <= 3.0 * c_dur:
                            continue
                        c_vec = _cluster_centroid(c)
                        c_f0 = _cluster_f0(c)
                        c_gender = _cluster_gender(c)
                        sim = float(np.dot(d_vec, c_vec))
                        semis = (
                            abs(12.0 * math.log2(d_f0 / c_f0))
                            if (d_f0 > 0 and c_f0 > 0) else 0.0
                        )
                        same_gender = (
                            d_gender == c_gender
                            or d_gender == "androgynous"
                            or c_gender == "androgynous"
                        )
                        if sim >= 0.55 and semis <= 4.0 and same_gender:
                            dominant.extend(c)
                            absorb.append(pi)
                    if absorb:
                        primary = [c for pi, c in enumerate(primary) if pi not in absorb]

            clusters = primary

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

        # Cross-Turn Speaker Memory Re-Identification Pass:
        # Re-evaluates clusters against earlier established SpeakerMemory profiles to re-identify
        # returning speakers (e.g. Speaker 1 talking again after Speaker 2) rather than creating a new Speaker 3.
        if len(speaker_registry) > 1:
            merged_into: Dict[str, str] = {}
            id_to_mem = {mem.speaker_id: mem for mem in speaker_registry}

            for i in range(len(speaker_registry)):
                id_i = speaker_registry[i].speaker_id
                target_spk = id_i
                while target_spk in merged_into:
                    target_spk = merged_into[target_spk]

                if target_spk != id_i:
                    continue

                mem_i = id_to_mem[target_spk]

                for j in range(i + 1, len(speaker_registry)):
                    id_j = speaker_registry[j].speaker_id
                    cand_spk = id_j
                    while cand_spk in merged_into:
                        cand_spk = merged_into[cand_spk]

                    if target_spk == cand_spk:
                        continue

                    mem_j = id_to_mem[cand_spk]

                    norm_i = float(np.linalg.norm(mem_i.centroid_vector))
                    norm_j = float(np.linalg.norm(mem_j.centroid_vector))
                    u_i = (mem_i.centroid_vector / norm_i) if norm_i > 1e-6 else mem_i.centroid_vector
                    u_j = (mem_j.centroid_vector / norm_j) if norm_j > 1e-6 else mem_j.centroid_vector
                    c_cos = float(np.dot(u_i, u_j))

                    f0_i = max(60.0, mem_i.mean_f0)
                    f0_j = max(60.0, mem_j.mean_f0)
                    s_diff = abs(12.0 * math.log2(f0_i / f0_j))

                    gen_i = mem_i.gender
                    gen_j = mem_j.gender
                    cross_gender = (gen_i != "androgynous" and gen_j != "androgynous" and gen_i != gen_j and s_diff > 6.0)

                    reidentify = False
                    if not cross_gender:
                        if is_neural:
                            # Only fold near-identical voices back together; a returning
                            # speaker keeps their ID without erasing distinct characters.
                            # High cosine + close pitch required so a different speaker
                            # is never mistaken for a returning one.
                            if c_cos >= 0.88 and s_diff <= 4.0:
                                reidentify = True
                        else:
                            sc_rel = abs(mem_i.mean_centroid - mem_j.mean_centroid) / max(mem_i.mean_centroid, mem_j.mean_centroid, 100.0)
                            if c_cos >= 0.94 and s_diff <= 4.0 and sc_rel <= 0.15:
                                reidentify = True
                            elif c_cos >= 0.96 and s_diff <= 5.0:
                                reidentify = True

                    if reidentify:
                        merged_into[cand_spk] = target_spk
                        for p, v in zip(mem_j.profiles, mem_j.vectors):
                            mem_i.update(p, v)

            if merged_into:
                for idx in cluster_map:
                    cur = cluster_map[idx]
                    while cur in merged_into:
                        cur = merged_into[cur]
                    cluster_map[idx] = cur

                # Renumber remaining distinct speakers chronologically
                seen_order: List[str] = []
                for idx in range(len(segments)):
                    s_id = cluster_map.get(idx, "Speaker_1")
                    if s_id not in seen_order:
                        seen_order.append(s_id)
                reorder_map = {old: f"Speaker_{new_i + 1}" for new_i, old in enumerate(seen_order)}
                for idx in cluster_map:
                    cluster_map[idx] = reorder_map.get(cluster_map[idx], cluster_map[idx])

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
        max_pause_sec: float = 2.0,
        max_chars: int = 350,
    ) -> List[AudioSegment]:
        """Merges consecutive sentences by the same speaker into cohesive natural paragraphs."""
        if not segments:
            return []

        grouped: List[AudioSegment] = []
        current: Optional[AudioSegment] = None

        for seg in segments:
            if seg.end <= seg.start or not seg.text.strip():
                continue

            if current is None:
                current = AudioSegment(
                    id=seg.id,
                    seek=seg.seek,
                    start=seg.start,
                    end=seg.end,
                    text=self.polish_english(seg.text),
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
                ends_question = current.text.rstrip().endswith("?")
                is_too_long = (len(current.text) + len(seg.text) > max_chars)

                if is_same_speaker and pause_dur <= max_pause_sec and not ends_question and not is_too_long:
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
                    if current.confidence is not None and seg.confidence is not None:
                        current.confidence = round((current.confidence + seg.confidence) / 2.0, 3)
                    elif seg.confidence is not None:
                        current.confidence = seg.confidence
                else:
                    # Finalize current speaker block and begin new one
                    grouped.append(current)
                    current = AudioSegment(
                        id=seg.id,
                        seek=seg.seek,
                        start=seg.start,
                        end=seg.end,
                        text=self.polish_english(seg.text),
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
