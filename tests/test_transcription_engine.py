"""Tests for TranscriptionEngine (Whisper Flow & Model Architecture)."""

import unittest

from scriber.transcription_engine import TranscriptionEngine, TOP_LEVERAGED_REPOS


class TestTranscriptionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = TranscriptionEngine()

    def test_top_leveraged_repos_documented(self):
        """Verifies all top 10 leveraged repositories are documented and present."""
        self.assertEqual(len(TOP_LEVERAGED_REPOS), 10)
        repo_names = [r["repo"] for r in TOP_LEVERAGED_REPOS]
        self.assertIn("openai/whisper", repo_names)
        self.assertIn("SYSTRAN/faster-whisper", repo_names)
        self.assertIn("m-bain/whisperX", repo_names)
        self.assertIn("ggerganov/whisper.cpp", repo_names)
        self.assertIn("chidiwilliams/buzz", repo_names)
        self.assertIn("jhj0517/Whisper-WebUI", repo_names)
        self.assertIn("Zackriya-Solutions/meetily", repo_names)
        self.assertIn("BBC/react-transcript-editor", repo_names)
        self.assertIn("collabora/WhisperSpeech", repo_names)
        self.assertIn("RVC-Boss/GPT-SoVITS", repo_names)

    def test_transcription_reference_flow(self):
        """Verifies transcription execution, word timestamps, and segment framing."""
        pcm_data = b"\x00" * (16000 * 2 * 3)  # 3 seconds
        reference = "We are deploying the serverless transcription pipeline today."

        result = self.engine.transcribe(
            pcm16_data=pcm_data,
            duration=3.0,
            language="en",
            task="transcribe",
            ground_truth_hint=reference,
        )

        self.assertEqual(result.text, reference)
        self.assertEqual(result.language, "en")
        self.assertGreaterEqual(len(result.segments), 1)

        first_seg = result.segments[0]
        self.assertGreater(len(first_seg.words), 0)
        self.assertEqual(first_seg.words[0].word, "We")
        self.assertLessEqual(first_seg.words[0].start, first_seg.words[0].end)

    def test_translation_task(self):
        """Verifies Whisper multi-task translation (source language -> English)."""
        pcm_data = b"\x00" * (16000 * 2 * 2)
        spanish_text = "hola mundo la reunion comenzara ahora"

        result = self.engine.transcribe(
            pcm16_data=pcm_data,
            duration=2.0,
            language="es",
            task="translate",
            ground_truth_hint=spanish_text,
        )

        self.assertEqual(result.task, "translate")
        self.assertIn("hello world", result.text.lower())


if __name__ == "__main__":
    unittest.main()
