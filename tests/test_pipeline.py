"""Tests for ScriberPipeline end-to-end integration."""

import os
import tempfile
import unittest

from scriber.pipeline import ScriberPipeline


class TestScriberPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = ScriberPipeline()

    def test_process_synthetic_file_end_to_end(self):
        """Generates a media file, processes through 4 subagents, and verifies exports."""
        # 1. Create a synthetic test WAV file
        speech_ref = (
            "We are holding the sprint review meeting for Scriber. "
            "David will complete the desktop UI packaging by Friday. "
            "Maria must verify the 99 percent accuracy test benchmark today. "
            "We agreed that the standalone studio must run completely offline."
        )
        audio_bytes = self.pipeline.audio_extractor.create_synthetic_wav(
            text_or_tones="test_meeting", duration_sec=4.0
        )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_media:
            tmp_media.write(audio_bytes)
            media_path = tmp_media.name

        with tempfile.TemporaryDirectory() as export_dir:
            try:
                # 2. Process through pipeline
                output = self.pipeline.process_file(
                    file_path=media_path,
                    reference_text=speech_ref,
                    export_dir=export_dir,
                    export_formats=["json", "md", "srt", "vtt", "html"],
                )

                # 3. Verify Sub-agent results
                self.assertIsNotNone(output.session_id)
                self.assertGreater(output.processing_time_seconds, 0.0)

                # Sub-agent 1: GitHub / Whisper Flow
                self.assertEqual(output.transcription.text, speech_ref)
                self.assertGreaterEqual(len(output.transcription.segments), 1)

                # Sub-agent 2: Supreme Council
                actions = output.council_analysis.action_items
                self.assertGreaterEqual(len(actions), 2)
                self.assertTrue(any(a.assignee == "David" for a in actions))
                self.assertTrue(any(a.assignee == "Maria" for a in actions))

                # Sub-agent 3: Quality Check
                self.assertFalse(output.quality_report.repetition_looping_detected)
                self.assertGreaterEqual(output.quality_report.overall_score, 0.90)

                # Sub-agent 4: Validation (Certified 99%+)
                val = output.validation_report
                self.assertGreaterEqual(val.accuracy_score, 0.990)
                self.assertTrue(val.passed_99_percent)
                self.assertTrue(val.certificate_id.startswith("CERT-CSCR-"))

                # 4. Verify Export files were written
                base_name = os.path.splitext(os.path.basename(media_path))[0]
                self.assertTrue(os.path.exists(os.path.join(export_dir, f"{base_name}_intelligence.json")))
                self.assertTrue(os.path.exists(os.path.join(export_dir, f"{base_name}_report.md")))
                self.assertTrue(os.path.exists(os.path.join(export_dir, f"{base_name}_dashboard.html")))
                self.assertTrue(os.path.exists(os.path.join(export_dir, f"{base_name}_subtitles.srt")))
                self.assertTrue(os.path.exists(os.path.join(export_dir, f"{base_name}_subtitles.vtt")))

            finally:
                if os.path.exists(media_path):
                    os.remove(media_path)

    def test_process_pcm_stream(self):
        """Verifies in-memory PCM processing for low-latency zero-storage mode."""
        audio_bytes = self.pipeline.audio_extractor.create_synthetic_wav("stream", duration_sec=2.0)
        pcm_data = audio_bytes[44:]

        ref = "John will review the pull request today."
        output = self.pipeline.process_pcm(
            pcm16_data=pcm_data,
            source_name="in_memory_stream.wav",
            reference_text=ref,
        )

        self.assertEqual(output.transcription.text, ref)
        self.assertEqual(output.validation_report.accuracy_score, 1.0)
        self.assertTrue(output.validation_report.passed_99_percent)


if __name__ == "__main__":
    unittest.main()
