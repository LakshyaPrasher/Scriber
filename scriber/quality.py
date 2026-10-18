"""Quality Check Sub-Agent: Audits transcription quality and prevents Whisper hallucinations.

Checks:
1. Hallucination looping detection (repetition penalties)
2. Compression ratio health (gzip/zlib ratio < 2.4)
3. Silence & no-speech threshold filtering (no_speech_prob > 0.6)
4. Word rate sanity (WPM within human threshold: 80 - 260 WPM)
5. Timestamp monotonicity and overlap resolution
6. Confidence scoring and automated segment cleanup
"""

from __future__ import annotations

import collections
import re
import zlib
from typing import List, Tuple

from scriber.models import AudioSegment, QualityReport, TranscriptionResult


class QualityChecker:
    """Sub-agent enforcing quality standards and filtering Whisper artifacts."""

    MAX_COMPRESSION_RATIO = 2.40
    MAX_NO_SPEECH_PROB = 0.60
    MIN_AVG_LOGPROB = -1.00
    MAX_REPETITION_COUNT = 3

    def audit_and_clean(self, transcription: TranscriptionResult) -> Tuple[TranscriptionResult, QualityReport]:
        """Performs comprehensive quality audit on transcription result and fixes anomalies."""
        cleaned_segments: List[AudioSegment] = []
        hallucinations_culled = 0
        low_confidence_flagged = 0
        repetition_looping_detected = False
        warnings: List[str] = []
        recommendations: List[str] = []

        seen_phrases = collections.Counter()

        for seg in transcription.segments:
            seg_text = seg.text.strip()

            # 1. Check for pure silence hallucination
            if seg.no_speech_prob > self.MAX_NO_SPEECH_PROB and seg.avg_logprob < self.MIN_AVG_LOGPROB:
                hallucinations_culled += 1
                warnings.append(
                    f"Segment {seg.id} ({seg.start:.1f}s-{seg.end:.1f}s) culled: high no-speech probability ({seg.no_speech_prob:.2f})."
                )
                continue

            # 2. Check for compression ratio failure (repetition explosion)
            comp_ratio = self._calculate_compression_ratio(seg_text)
            seg.compression_ratio = comp_ratio
            if comp_ratio > self.MAX_COMPRESSION_RATIO:
                repetition_looping_detected = True
                warnings.append(
                    f"Segment {seg.id} flagged: high compression ratio ({comp_ratio:.2f} > {self.MAX_COMPRESSION_RATIO})."
                )
                # Deduplicate repeated n-grams in text
                seg_text = self._deduplicate_phrase(seg_text)
                seg.text = seg_text

            # 3. Check for phrase repetition looping across segments
            norm_phrase = seg_text.lower().strip()
            seen_phrases[norm_phrase] += 1
            if seen_phrases[norm_phrase] > self.MAX_REPETITION_COUNT and len(norm_phrase) > 10:
                repetition_looping_detected = True
                hallucinations_culled += 1
                warnings.append(
                    f"Segment {seg.id} culled: repeated phrase detected {seen_phrases[norm_phrase]} times ('{norm_phrase[:30]}...')."
                )
                continue

            # 4. Check confidence
            if seg.confidence < 0.80 or seg.avg_logprob < -0.8:
                low_confidence_flagged += 1

            # 5. Ensure timestamp monotonicity
            if seg.end < seg.start:
                seg.end = seg.start + 0.5
                warnings.append(f"Segment {seg.id}: fixed inverted timestamp.")

            cleaned_segments.append(seg)

        # Re-assemble cleaned text
        cleaned_text = " ".join(s.text.strip() for s in cleaned_segments if not s.text.startswith("[silence]")).strip()

        # Calculate word count & speaking rate
        words = cleaned_text.split()
        word_count = len(words)
        duration_minutes = max(0.01, transcription.duration / 60.0)
        wpm = word_count / duration_minutes

        if wpm > 260:
            warnings.append(f"Unusually high speaking rate detected: {wpm:.1f} WPM (typical speech: 120-180 WPM).")
            recommendations.append("Verify whether audio speed is accelerated or contains overlapping dialogue.")
        elif wpm < 50 and word_count > 10:
            recommendations.append("Audio contains extensive pauses or ambient silence between speech turns.")

        # Compute overall quality score
        conf_scores = [s.confidence for s in cleaned_segments] if cleaned_segments else [0.0]
        avg_confidence = sum(conf_scores) / float(len(conf_scores)) if conf_scores else 0.0

        penalty = 0.0
        if repetition_looping_detected:
            penalty += 0.02
        if hallucinations_culled > 0:
            penalty += min(0.05, hallucinations_culled * 0.01)
        if low_confidence_flagged > 0:
            penalty += min(0.05, low_confidence_flagged * 0.01)

        overall_score = max(0.0, min(1.0, avg_confidence - penalty))

        if overall_score >= 0.95:
            recommendations.append("Audio clarity is exceptional; transcription verified with high confidence.")
        elif overall_score >= 0.90:
            recommendations.append("Good transcription quality; minor acoustic artifacts resolved.")
        else:
            recommendations.append("Moderate quality; manual review recommended for flagged low-confidence passages.")

        quality_report = QualityReport(
            overall_score=overall_score,
            confidence_avg=avg_confidence,
            repetition_looping_detected=repetition_looping_detected,
            hallucinations_culled=hallucinations_culled,
            low_confidence_segments_flagged=low_confidence_flagged,
            compression_ratio_healthy=not repetition_looping_detected,
            word_count=word_count,
            estimated_speaking_wpm=wpm,
            warnings=warnings,
            recommendations=recommendations,
        )

        cleaned_result = TranscriptionResult(
            text=cleaned_text,
            language=transcription.language,
            language_probability=transcription.language_probability,
            duration=transcription.duration,
            segments=cleaned_segments,
            task=transcription.task,
            backend_used=transcription.backend_used,
            model_name=transcription.model_name,
        )

        return cleaned_result, quality_report

    @staticmethod
    def _calculate_compression_ratio(text: str) -> float:
        """Measures zlib compression ratio matching OpenAI Whisper's compression test."""
        raw_bytes = text.encode("utf-8")
        if not raw_bytes:
            return 1.0
        compressed = zlib.compress(raw_bytes)
        return len(raw_bytes) / float(len(compressed))

    @staticmethod
    def _deduplicate_phrase(text: str) -> str:
        """Removes adjacent repeating sentences or phrases."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        deduped = []
        last_s = ""
        for s in sentences:
            s_clean = s.strip()
            if s_clean.lower() != last_s.lower():
                deduped.append(s_clean)
                last_s = s_clean
        return " ".join(deduped)
