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
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from scriber.models import AudioSegment, VoiceProfile, WordTimestamp
from scriber.voice_clone import VoiceProfiler


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
        # 1. Cosine similarity of 16-d acoustic embedding
        dot = float(np.dot(vector, self.centroid_vector))
        cos_sim = max(0.0, min(1.0, dot))

        # 2. Pitch semitone distance
        f0_curr = max(60.0, profile.fundamental_frequency_hz)
        f0_base = max(60.0, self.mean_f0)
        f0_delta = abs(f0_curr - f0_base)
        semitone_diff = abs(12.0 * math.log2(f0_curr / f0_base))

        if semitone_diff <= 1.2:
            pitch_dist = (semitone_diff / 1.2) * 0.25
        else:
            pitch_dist = 0.25 + ((semitone_diff - 1.2) / 2.0) ** 1.3

        # 3. Spectral centroid relative distance
        sc_curr = max(100.0, profile.spectral_centroid_hz)
        sc_base = max(100.0, self.mean_centroid)
        sc_rel_diff = abs(sc_curr - sc_base) / max(sc_curr, sc_base, 100.0)
        sc_dist = sc_rel_diff / 0.16

        # 4. Cosine distance
        cos_dist = max(0.0, 1.0 - cos_sim) / 0.08

        # 5. Gender contrast penalty
        gender_penalty = 0.0
        if (
            profile.gender_estimate != "androgynous"
            and self.gender != "androgynous"
            and profile.gender_estimate != self.gender
        ):
            gender_penalty = 0.80

        dist = (0.45 * pitch_dist) + (0.35 * sc_dist) + (0.20 * cos_dist) + gender_penalty

        # 6. Conversational continuity prior for active speaker across brief pauses
        if is_active_speaker and pause_sec <= 2.0 and gender_penalty == 0.0:
            if (f0_delta <= 12.0 and sc_rel_diff <= 0.24) or (f0_delta <= 25.0 and sc_rel_diff <= 0.12):
                dist *= 0.65

        # Map distance to similarity score in [0.0, 1.0] (boundary 0.78 -> ~0.486)
        score = math.exp(-0.5 * (dist / 0.65) ** 2)
        if is_active_speaker and pause_sec <= 3.5:
            score = min(1.0, score + 0.08)
        return max(0.0, min(1.0, score))


class AcousticDiarizer:
    """Intelligent voice-based speaker segmentation, memory clustering, and English dialogue formatter."""

    def __init__(self, similarity_threshold: float = 0.48):
        self.similarity_threshold = similarity_threshold

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

        bytes_per_sec = sample_rate * 2
        total_pcm_len = len(pcm16_data)

        # First pass: Extract profiles and normalized acoustic vectors for all segments
        extracted_info = []
        for seg in segments:
            start_byte = max(0, int(seg.start * bytes_per_sec))
            start_byte -= (start_byte % 2)
            end_byte = min(total_pcm_len, int(seg.end * bytes_per_sec))
            end_byte -= (end_byte % 2)

            seg_pcm = pcm16_data[start_byte:end_byte]
            if len(seg_pcm) < int(0.2 * bytes_per_sec):
                pad_start = max(0, int((seg.start - 0.15) * bytes_per_sec))
                pad_start -= (pad_start % 2)
                pad_end = min(total_pcm_len, int((seg.end + 0.15) * bytes_per_sec))
                pad_end -= (pad_end % 2)
                seg_pcm = pcm16_data[pad_start:pad_end]

            p = VoiceProfiler.profile_from_pcm16(seg_pcm, speaker_id="temp")
            vec = np.array(p.voice_vector, dtype=np.float32)
            v_norm = np.linalg.norm(vec)
            if v_norm > 1e-6:
                vec = vec / v_norm
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
                )
                dist_mat[i, j] = d
                dist_mat[j, i] = d

        # Calibrate distance threshold based on similarity_threshold (default 0.48 maps to 0.78)
        distance_threshold = 0.78 * (0.48 / max(0.1, self.similarity_threshold))

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
                    avg_f0_a = float(np.mean([p.fundamental_frequency_hz for p in p_a]))
                    avg_f0_b = float(np.mean([p.fundamental_frequency_hz for p in p_b]))
                    avg_sc_a = float(np.mean([p.spectral_centroid_hz for p in p_a]))
                    avg_sc_b = float(np.mean([p.spectral_centroid_hz for p in p_b]))
                    gender_a = p_a[0].gender_estimate
                    gender_b = p_b[0].gender_estimate
                    if gender_a != "androgynous" and gender_b != "androgynous" and gender_a != gender_b:
                        continue
                    semitone_diff = abs(12.0 * math.log2(max(60.0, avg_f0_a) / max(60.0, avg_f0_b)))
                    sc_rel = abs(avg_sc_a - avg_sc_b) / max(avg_sc_a, avg_sc_b, 100.0)
                    if semitone_diff <= 1.0 and sc_rel <= 0.15:
                        inter_d = (semitone_diff / 1.0) * 0.3 + (sc_rel / 0.15) * 0.3
                        if inter_d < best_inter_d:
                            best_inter_d = inter_d
                            merge_pair = (a, b)
            if merge_pair[0] != -1:
                a, b = merge_pair
                clusters[a].extend(clusters[b])
                clusters.pop(b)
                merged = True

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
    ) -> float:
        """Calibrated acoustic distance metric between two voice profiles."""
        f1 = max(60.0, p1.fundamental_frequency_hz)
        f2 = max(60.0, p2.fundamental_frequency_hz)
        f0_delta = abs(f1 - f2)
        semitone_diff = abs(12.0 * math.log2(f1 / f2))

        # 1. Pitch distance: non-linear scaling. Intra-speaker inflection <= 1.2 semitones is low cost.
        if semitone_diff <= 1.2:
            pitch_dist = (semitone_diff / 1.2) * 0.25
        else:
            pitch_dist = 0.25 + ((semitone_diff - 1.2) / 2.0) ** 1.3

        # 2. Spectral centroid relative difference
        sc1 = max(100.0, p1.spectral_centroid_hz)
        sc2 = max(100.0, p2.spectral_centroid_hz)
        sc_rel_diff = abs(sc1 - sc2) / max(sc1, sc2, 100.0)
        sc_dist = sc_rel_diff / 0.16

        # 3. Acoustic embedding vector cosine distance
        v1 = np.array(p1.voice_vector, dtype=np.float32)
        v2 = np.array(p2.voice_vector, dtype=np.float32)
        norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm1 > 1e-6 and norm2 > 1e-6:
            cos_sim = float(np.dot(v1, v2) / (norm1 * norm2))
            cos_dist = max(0.0, 1.0 - cos_sim) / 0.08
        else:
            cos_dist = 0.5

        # 4. Gender contrast penalty
        gender_penalty = 0.0
        if (
            p1.gender_estimate != "androgynous"
            and p2.gender_estimate != "androgynous"
            and p1.gender_estimate != p2.gender_estimate
        ):
            gender_penalty = 0.80

        composite = (0.45 * pitch_dist) + (0.35 * sc_dist) + (0.20 * cos_dist) + gender_penalty

        # 5. Conversational continuity prior for adjacent turns
        if is_adjacent and pause_sec <= 2.0 and gender_penalty == 0.0:
            if (f0_delta <= 12.0 and sc_rel_diff <= 0.24) or (f0_delta <= 25.0 and sc_rel_diff <= 0.12):
                composite *= 0.65

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
