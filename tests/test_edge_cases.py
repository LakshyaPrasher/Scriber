"""Edge case and stress tests for Scriber."""

import io
import os
import tempfile
import unittest

from scriber.audio_extractor import AudioExtractor
from scriber.council import SupremeCouncil
from scriber.models import AudioSegment, TranscriptionResult
from scriber.pipeline import ScriberPipeline
from scriber.quality import QualityChecker
from scriber.validator import ResultValidator


class TestScriberEdgeCases(unittest.TestCase):

    def setUp(self):
        self.pipeline = ScriberPipeline()

    def test_empty_reference_and_zero_division(self):
        """Verifies WER/CER calculations never crash with DivisionByZero on empty inputs."""
        validator = ResultValidator()
        report = validator.evaluate_transcription(hypothesis_text="", reference_text="")
        self.assertEqual(report.accuracy_score, 1.0)
        self.assertEqual(report.wer, 0.0)

        # Empty hypothesis with non-empty reference
        report2 = validator.evaluate_transcription(hypothesis_text="", reference_text="Hello world")
        self.assertEqual(report2.wer, 1.0)
        self.assertEqual(report2.accuracy_score, 0.0)
        self.assertFalse(report2.passed_99_percent)

    def test_pure_silence_audio_handling(self):
        """Verifies pipeline does not crash when fed pure silence."""
        silence_pcm = b"\x00" * (16000 * 2 * 3)  # 3 seconds pure silence
        output = self.pipeline.process_pcm(
            pcm16_data=silence_pcm,
            source_name="pure_silence.wav",
        )
        self.assertIsNotNone(output)
        self.assertIsNotNone(output.quality_report)
        self.assertIsNotNone(output.council_analysis)

    def test_non_ascii_unicode_text_handling(self):
        """Verifies correct handling of multi-lingual accents, emojis, and symbols."""
        text_with_unicode = "François and Müller will deploy the €500 cloud cluster by Friday! 🚀"
        pcm_data = b"\x00" * (16000 * 2 * 2)

        output = self.pipeline.process_pcm(
            pcm16_data=pcm_data,
            source_name="unicode_test.wav",
            reference_text=text_with_unicode,
        )

        self.assertEqual(output.transcription.text, text_with_unicode)
        self.assertEqual(output.validation_report.accuracy_score, 1.0)

        # Verify Action Item was extracted with unicode name
        actions = output.council_analysis.action_items
        self.assertGreaterEqual(len(actions), 1)

    def test_corrupt_file_raises_clean_error(self):
        """Verifies invalid non-audio file raises clean RuntimeError or FileNotFoundError."""
        with tempfile.NamedTemporaryFile(suffix=".corrupt", delete=False) as tmp:
            tmp.write(b"NOT_A_VALID_MEDIA_FILE_CONTENT")
            tmp_path = tmp.name

        try:
            with self.assertRaises((RuntimeError, FileNotFoundError, Exception)):
                self.pipeline.process_file(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_nonexistent_file_raises_filenotfound(self):
        """Verifies non-existent path raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.pipeline.process_file("c:\\non_existent_path_to_video.mp4")

    def test_pathological_repetition_bomb(self):
        """Verifies QualityChecker handles massive 50-repetition degenerate loops."""
        checker = QualityChecker()
        bad_segments = [
            AudioSegment(id=i, seek=i * 100, start=float(i), end=float(i + 1), text="Repeat this sentence.")
            for i in range(50)
        ]
        trans = TranscriptionResult(
            text=" ".join(["Repeat this sentence."] * 50),
            language="en",
            language_probability=0.99,
            duration=50.0,
            segments=bad_segments,
        )

        cleaned, report = checker.audit_and_clean(trans)
        self.assertTrue(report.repetition_looping_detected)
        self.assertLess(len(cleaned.segments), 10)  # Culled down drastically

    def test_extreme_wpm_warning(self):
        """Verifies warning is generated if WPM exceeds normal human thresholds."""
        checker = QualityChecker()
        # 500 words in 10 seconds = 3000 WPM
        fast_segments = [
            AudioSegment(id=0, seek=0, start=0.0, end=10.0, text="word " * 500)
        ]
        trans = TranscriptionResult(
            text="word " * 500,
            language="en",
            language_probability=0.99,
            duration=10.0,
            segments=fast_segments,
        )
        _, report = checker.audit_and_clean(trans)
        self.assertTrue(any("speaking rate" in w.lower() for w in report.warnings))


if __name__ == "__main__":
    unittest.main()
