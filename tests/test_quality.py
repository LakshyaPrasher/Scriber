"""Tests for QualityChecker (Sub-Agent 3: Hallucination Guard & Repetition Penalties)."""

import unittest

from scriber.models import AudioSegment, TranscriptionResult
from scriber.quality import QualityChecker


class TestQualityChecker(unittest.TestCase):

    def setUp(self):
        self.checker = QualityChecker()

    def test_cull_silence_hallucinations(self):
        """Verifies high no-speech probability silence segments are culled."""
        segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=3.0,
                text="This is genuine spoken audio.",
                no_speech_prob=0.01,
                avg_logprob=-0.1,
            ),
            AudioSegment(
                id=1,
                seek=300,
                start=3.0,
                end=6.0,
                text="Thank you for watching.",
                no_speech_prob=0.95,
                avg_logprob=-1.5,  # Hallucinated Whisper artifact on silence
            ),
        ]
        transcription = TranscriptionResult(
            text="This is genuine spoken audio. Thank you for watching.",
            language="en",
            language_probability=0.99,
            duration=6.0,
            segments=segments,
        )

        cleaned, report = self.checker.audit_and_clean(transcription)

        self.assertEqual(len(cleaned.segments), 1)
        self.assertEqual(cleaned.segments[0].text, "This is genuine spoken audio.")
        self.assertEqual(report.hallucinations_culled, 1)

    def test_repetition_looping_detection(self):
        """Verifies repetition explosion across multiple segments is penalized and cleaned."""
        segments = [
            AudioSegment(id=0, seek=0, start=0.0, end=2.0, text="Thank you for watching."),
            AudioSegment(id=1, seek=200, start=2.0, end=4.0, text="Thank you for watching."),
            AudioSegment(id=2, seek=400, start=4.0, end=6.0, text="Thank you for watching."),
            AudioSegment(id=3, seek=600, start=6.0, end=8.0, text="Thank you for watching."),
            AudioSegment(id=4, seek=800, start=8.0, end=10.0, text="Thank you for watching."),
        ]
        transcription = TranscriptionResult(
            text="Thank you for watching. Thank you for watching. Thank you for watching. Thank you for watching.",
            language="en",
            language_probability=0.99,
            duration=10.0,
            segments=segments,
        )

        cleaned, report = self.checker.audit_and_clean(transcription)

        self.assertTrue(report.repetition_looping_detected)
        self.assertLess(len(cleaned.segments), len(segments))

    def test_inverted_timestamps_correction(self):
        """Verifies inverted timestamps (end < start) are auto-corrected."""
        segments = [
            AudioSegment(id=0, seek=0, start=5.0, end=2.0, text="Valid words."),
        ]
        transcription = TranscriptionResult(
            text="Valid words.",
            language="en",
            language_probability=0.99,
            duration=6.0,
            segments=segments,
        )

        cleaned, _ = self.checker.audit_and_clean(transcription)
        self.assertGreater(cleaned.segments[0].end, cleaned.segments[0].start)


if __name__ == "__main__":
    unittest.main()
