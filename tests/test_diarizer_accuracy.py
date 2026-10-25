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

    def test_alternating_dialogue_reidentification(self):
        """Verifies multi-turn conversation (A -> B -> A -> B) re-identifies speakers instead of creating new ones."""
        sr = 16000
        t_turn = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
        # Speaker A: 125 Hz
        pcm_a1 = ((0.5 * np.sin(2 * np.pi * 125 * t_turn) + 0.2 * np.sin(2 * np.pi * 250 * t_turn)) * 32767).astype(np.int16).tobytes()
        # Speaker B: 220 Hz
        pcm_b1 = ((0.5 * np.sin(2 * np.pi * 220 * t_turn) + 0.2 * np.sin(2 * np.pi * 440 * t_turn)) * 32767).astype(np.int16).tobytes()
        # Speaker A turn 2: 128 Hz (slight natural variation)
        pcm_a2 = ((0.5 * np.sin(2 * np.pi * 128 * t_turn) + 0.2 * np.sin(2 * np.pi * 256 * t_turn)) * 32767).astype(np.int16).tobytes()
        # Speaker B turn 2: 218 Hz
        pcm_b2 = ((0.5 * np.sin(2 * np.pi * 218 * t_turn) + 0.2 * np.sin(2 * np.pi * 436 * t_turn)) * 32767).astype(np.int16).tobytes()

        full_pcm = pcm_a1 + pcm_b1 + pcm_a2 + pcm_b2
        segs = [
            AudioSegment(id=0, seek=0, start=0.0, end=2.0, text="Good morning, let's review the updates."),
            AudioSegment(id=1, seek=2, start=2.0, end=4.0, text="Yes, all backend metrics look stable."),
            AudioSegment(id=2, seek=4, start=4.0, end=6.0, text="Excellent, and what about voice cloning?"),
            AudioSegment(id=3, seek=6, start=6.0, end=8.0, text="Deep analysis is completely integrated."),
        ]
        diarizer = AcousticDiarizer(similarity_threshold=0.48)
        diarized = diarizer.diarize_segments(segs, full_pcm, sample_rate=sr)
        distinct_speakers = {s.speaker for s in diarized}
        self.assertEqual(len(distinct_speakers), 2, f"Expected exactly 2 speakers across 4 alternating turns, got {distinct_speakers}")
        self.assertEqual(diarized[0].speaker, diarized[2].speaker, "Turn 1 and Turn 3 should be recognized as the same speaker (Speaker A)")
        self.assertEqual(diarized[1].speaker, diarized[3].speaker, "Turn 2 and Turn 4 should be recognized as the same speaker (Speaker B)")

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

    def test_natural_pitch_inflection_reidentification(self):
        """Verifies that natural pitch inflections across non-adjacent turns do not split into phantom speakers."""
        sr = 16000
        t_turn = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
        # Speaker A turn 1: 120 Hz
        pcm_a1 = ((0.5 * np.sin(2 * np.pi * 120 * t_turn) + 0.2 * np.sin(2 * np.pi * 240 * t_turn)) * 32767).astype(np.int16).tobytes()
        # Speaker B turn 1: 220 Hz
        pcm_b1 = ((0.5 * np.sin(2 * np.pi * 220 * t_turn) + 0.2 * np.sin(2 * np.pi * 440 * t_turn)) * 32767).astype(np.int16).tobytes()
        # Speaker A turn 2: 145 Hz (natural pitch swing of ~3.2 semitones between statement and question)
        pcm_a2 = ((0.5 * np.sin(2 * np.pi * 145 * t_turn) + 0.2 * np.sin(2 * np.pi * 290 * t_turn)) * 32767).astype(np.int16).tobytes()
        # Speaker B turn 2: 222 Hz
        pcm_b2 = ((0.5 * np.sin(2 * np.pi * 222 * t_turn) + 0.2 * np.sin(2 * np.pi * 444 * t_turn)) * 32767).astype(np.int16).tobytes()

        full_pcm = pcm_a1 + pcm_b1 + pcm_a2 + pcm_b2
        segs = [
            AudioSegment(id=0, seek=0, start=0.0, end=2.0, text="First statement from speaker A."),
            AudioSegment(id=1, seek=2, start=2.0, end=4.0, text="Response from speaker B."),
            AudioSegment(id=2, seek=4, start=4.0, end=6.0, text="Did speaker A ask an enthusiastic question?"),
            AudioSegment(id=3, seek=6, start=6.0, end=8.0, text="Closing remark from speaker B."),
        ]
        diarizer = AcousticDiarizer(similarity_threshold=0.48)
        diarized = diarizer.diarize_segments(segs, full_pcm, sample_rate=sr)
        distinct_speakers = {s.speaker for s in diarized}
        self.assertEqual(len(distinct_speakers), 2, f"Expected 2 speakers, but got {distinct_speakers}")
        self.assertEqual(diarized[0].speaker, diarized[2].speaker, "Turn 1 and Turn 3 must match Speaker A")
        self.assertEqual(diarized[1].speaker, diarized[3].speaker, "Turn 2 and Turn 4 must match Speaker B")

    def test_same_pitch_distinct_speakers_segregation(self):
        """Verifies that two distinct speakers of the same gender with near-identical pitch (Jenny vs Emma) are segregated."""
        suite_dir = os.path.join(os.path.dirname(__file__), "suite_20_samples")
        f_jenny = os.path.join(suite_dir, "sample_04_single_spk_calm_female_turn_0_en-US-JennyNeural.mp3")
        f_emma = os.path.join(suite_dir, "sample_07_single_spk_expressive_emma_turn_0_en-US-EmmaNeural.mp3")

        if not os.path.exists(f_jenny) or not os.path.exists(f_emma):
            self.skipTest("Sample files for Jenny and Emma not found")

        pcm_j, _ = self.extractor.extract_pcm16(f_jenny)
        pcm_e, _ = self.extractor.extract_pcm16(f_emma)
        full_pcm = pcm_j + pcm_e
        dur_j = len(pcm_j) / (16000.0 * 2.0)
        dur_e = len(pcm_e) / (16000.0 * 2.0)

        segs = [
            AudioSegment(id=0, seek=0, start=0.0, end=dur_j, text="Welcome to today's customer experience update."),
            AudioSegment(id=1, seek=int(dur_j), start=dur_j, end=dur_j + dur_e, text="Our engineering roadmap is progressing on schedule."),
        ]
        diarizer = AcousticDiarizer(similarity_threshold=0.48)
        diarized = diarizer.diarize_segments(segs, full_pcm, sample_rate=16000)
        distinct_speakers = {s.speaker for s in diarized}
        self.assertEqual(len(distinct_speakers), 2, f"Jenny and Emma must be segregated into 2 distinct speakers, got: {distinct_speakers}")
        self.assertNotEqual(diarized[0].speaker, diarized[1].speaker, "Jenny and Emma must receive different speaker IDs")


if __name__ == "__main__":
    unittest.main()
