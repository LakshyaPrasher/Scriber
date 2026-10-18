"""Diarization accuracy and universal media ingestion unit tests."""

import os
import unittest
import numpy as np

from scriber.pipeline import ScriberPipeline
from scriber.models import AudioSegment
from scriber.voice_clone import VoiceProfiler
from scriber.diarizer import AcousticDiarizer, SpeakerMemory
from scriber.audio_extractor import AudioExtractor


class TestDiarizerAccuracy(unittest.TestCase):

    def setUp(self):
        self.pipeline = ScriberPipeline(diarization_threshold=0.48)
        self.extractor = AudioExtractor()

    def test_single_speaker_unification(self):
        """Verifies that single-speaker monologue audio is not split into phantom speakers."""
        rc44_path = os.path.expanduser(r"~\Downloads\R&C 44.mp3")
        if not os.path.exists(rc44_path):
            self.skipTest(f"Sample file {rc44_path} not found in Downloads")

        output = self.pipeline.process_file(rc44_path)
        segments = output.transcription.segments
        self.assertGreater(len(segments), 0)

        # All segments should be unified under Speaker_1
        speakers = {s.speaker for s in segments}
        self.assertEqual(len(speakers), 1, f"Expected 1 speaker, but got: {speakers}")
        self.assertIn("Speaker_1", speakers)

    def test_multi_speaker_segregation(self):
        """Verifies that audio segments with clearly different acoustic pitches segregate into different speakers."""
        sr = 16000
        # Speaker A: 120 Hz pitch (male register)
        t = np.linspace(0, 3.0, int(3.0 * sr), endpoint=False)
        audio_a = (0.5 * np.sin(2 * np.pi * 120 * t) + 0.2 * np.sin(2 * np.pi * 240 * t)).astype(np.float32)
        pcm_a = (audio_a * 32767).astype(np.int16).tobytes()

        # Speaker B: 240 Hz pitch (female register)
        t_b = np.linspace(0, 3.0, int(3.0 * sr), endpoint=False)
        audio_b = (0.5 * np.sin(2 * np.pi * 240 * t_b) + 0.2 * np.sin(2 * np.pi * 480 * t_b)).astype(np.float32)
        pcm_b = (audio_b * 32767).astype(np.int16).tobytes()

        full_pcm = pcm_a + pcm_b
        seg1 = AudioSegment(id=0, seek=0, start=0.0, end=3.0, text="First statement from speaker one.", speaker=None)
        seg2 = AudioSegment(id=1, seek=3, start=3.0, end=6.0, text="Second statement from a different speaker.", speaker=None)

        diarizer = AcousticDiarizer(similarity_threshold=0.48)
        diarized = diarizer.diarize_segments([seg1, seg2], full_pcm, sample_rate=sr)

        speakers = {s.speaker for s in diarized}
        self.assertGreaterEqual(len(speakers), 2, "Expected 2 distinct speakers for separate acoustic pitch profiles")

    def test_universal_media_ingestion(self):
        """Verifies that AudioExtractor handles multiple media container formats."""
        downloads = os.path.expanduser(r"~\Downloads")
        test_candidates = [
            os.path.join(downloads, "R&C 44.mp3"),
            os.path.join(downloads, "BNP Paribas.m4a"),
            os.path.join(downloads, "BNP Paribas.mp4"),
        ]

        tested_count = 0
        for f in test_candidates:
            if os.path.exists(f):
                pcm, meta = self.extractor.extract_pcm16(f)
                self.assertGreater(len(pcm), 1000)
                self.assertGreater(meta.duration, 0.5)
                self.assertEqual(meta.sample_rate, 16000)
                tested_count += 1

        self.assertGreater(tested_count, 0, "At least one media file must be tested")


if __name__ == "__main__":
    unittest.main()
