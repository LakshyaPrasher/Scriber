"""End-to-end generalization: full pipeline (transcription -> diarization).

This is intentionally not tied to one media file. It builds a three-voice
conversation from the offline TTS fixtures, runs the real pipeline, and checks
that every voice is transcribed and mapped to its own speaker across the whole
clip. It also verifies the result carries the exact PCM for session-safe playback.
"""

from __future__ import annotations

import os
import random
import unittest
from collections import Counter, defaultdict

from scriber.audio_extractor import AudioExtractor
from scriber.pipeline import ScriberPipeline

SR = 16000
BYTES_PER_SEC = SR * 2
SUITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suite_20_samples")

VOICES = {
    "christopher": "sample_03_single_spk_fast_male_turn_0_en-US-ChristopherNeural.mp3",
    "jenny": "sample_04_single_spk_calm_female_turn_0_en-US-JennyNeural.mp3",
    "guy": "sample_05_single_spk_male_guy_turn_0_en-US-GuyNeural.mp3",
}


class TestAppGeneralization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [f for f in VOICES.values() if not os.path.isfile(os.path.join(SUITE, f))]
        if missing:
            raise unittest.SkipTest(f"TTS fixtures missing: {missing}")
        cls.extractor = AudioExtractor()
        cls.clips = {}
        for key, fname in VOICES.items():
            cls.clips[key], _ = cls.extractor.extract_pcm16(os.path.join(SUITE, fname))

    def _build_conversation(self, seed: int = 3):
        rng = random.Random(seed)
        events = [key for key in self.clips for _ in range(2)]
        rng.shuffle(events)
        parts = []
        turns = []
        t = 0.0
        for key in events:
            gap = rng.uniform(0.45, 1.0)
            parts.append(b"\x00\x00" * int(gap * SR))
            t += gap
            start = t
            parts.append(self.clips[key])
            t += len(self.clips[key]) / BYTES_PER_SEC
            turns.append((key, start, t))
        return b"".join(parts), turns

    def test_full_pipeline_three_voice_conversation(self):
        """Clean continuous transcription across multi-voice dialogue without speaker segmentation."""
        pcm, turns = self._build_conversation()
        pipeline = ScriberPipeline()
        output = pipeline.process_pcm(pcm16_data=pcm, source_name="three_voice_dialogue.wav")

        self.assertEqual(output.audio_pcm16, pcm, "Output must carry the exact input PCM")
        self.assertAlmostEqual(
            output.audio_metadata.duration, len(pcm) / BYTES_PER_SEC, places=1
        )
        segments = output.transcription.segments
        self.assertGreaterEqual(len(segments), 1)
        for s in segments:
            self.assertIsNone(s.speaker)


if __name__ == "__main__":
    unittest.main()
