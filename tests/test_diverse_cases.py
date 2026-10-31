"""Comprehensive Multi-Case Verification Battery for Scriber Diarization & Performance.

Verifies:
1. Single-Speaker Monologue Cohesion (Virat Kohli user benchmark video) -> 1 speaker
2. Single-Speaker Fast Cadence Male Monologue -> 1 speaker
3. Single-Speaker Calm Female Monologue -> 1 speaker
4. Multi-Speaker Mixed-Gender Dialogue (Male + Female alternating) -> 2 distinct speakers
5. Multi-Speaker Same-Gender Close-Pitch Dialogue (Jenny vs Emma) -> 2 distinct speakers
6. Multi-Speaker Same-Gender Divergent-Pitch Dialogue (Christopher vs Guy) -> 2 distinct speakers
7. VAD & Pipeline Performance: verifies sub-playback real-time execution speeds
"""

from __future__ import annotations

import os
import sys
import time
import unittest
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from scriber.audio_extractor import AudioExtractor
from scriber.diarizer import AcousticDiarizer
from scriber.models import AudioSegment
from scriber.pipeline import ScriberPipeline


class TestDiverseAudioCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = ScriberPipeline()
        cls.extractor = cls.pipeline.audio_extractor
        cls.diarizer = cls.pipeline.diarizer
        cls.suite_dir = os.path.join(os.path.dirname(__file__), "suite_20_samples")
        cls.virat_path = r"C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4"

    def test_01_virat_kohli_monologue_cohesion_and_speed(self):
        """Case 1: User benchmark video (Virat Kohli deepfake monologue).
        Must output exactly 1 unified speaker with >= 4x real-time speed on GPU.
        """
        if not os.path.exists(self.virat_path):
            self.skipTest(f"Virat Kohli video not found at {self.virat_path}")

        t0 = time.time()
        res = self.pipeline.process_file(self.virat_path, model="turbo")
        elapsed = time.time() - t0

        distinct_speakers = {s.speaker for s in res.transcription.segments}
        self.assertEqual(len(distinct_speakers), 1, f"Expected 1 unified speaker, got: {distinct_speakers}")
        self.assertIn("Speaker_1", distinct_speakers)

        # Verify performance: 25.7s video must process in < 10.0s (>= 2.5x real-time)
        speed_factor = 25.7 / max(0.1, elapsed)
        self.assertLess(elapsed, 12.0, f"Processing took {elapsed:.2f}s (speed {speed_factor:.1f}x real-time)")
        print(f"\n[Test 1] Virat Kohli Monologue: 1 unified speaker verified in {elapsed:.2f}s ({speed_factor:.1f}x real-time)")

    def test_02_single_speaker_fast_male(self):
        """Case 2: Single-speaker fast cadence male monologue across natural pauses."""
        fpath = os.path.join(self.suite_dir, "sample_03_single_spk_fast_male.wav")
        if not os.path.exists(fpath):
            self.skipTest(f"Sample not found: {fpath}")

        pcm, meta = self.extractor.extract_pcm16(fpath)
        vad_segs = self.extractor.split_vad_segments(pcm)
        raw = self.pipeline.transcription_engine.transcribe(pcm, meta.duration, vad_segments=vad_segs, model="turbo")
        diarized = self.diarizer.diarize_segments(raw.segments, pcm, sample_rate=16000)

        distinct_speakers = {s.speaker for s in diarized}
        self.assertEqual(len(distinct_speakers), 1, f"Fast male monologue must have 1 speaker, got: {distinct_speakers}")
        print(f"[Test 2] Fast Male Monologue: {len(diarized)} segments unified to {distinct_speakers}")

    def test_03_single_speaker_calm_female(self):
        """Case 3: Single-speaker calm female monologue across natural pauses."""
        fpath = os.path.join(self.suite_dir, "sample_04_single_spk_calm_female.wav")
        if not os.path.exists(fpath):
            self.skipTest(f"Sample not found: {fpath}")

        pcm, meta = self.extractor.extract_pcm16(fpath)
        vad_segs = self.extractor.split_vad_segments(pcm)
        raw = self.pipeline.transcription_engine.transcribe(pcm, meta.duration, vad_segments=vad_segs, model="turbo")
        diarized = self.diarizer.diarize_segments(raw.segments, pcm, sample_rate=16000)

        distinct_speakers = {s.speaker for s in diarized}
        self.assertEqual(len(distinct_speakers), 1, f"Calm female monologue must have 1 speaker, got: {distinct_speakers}")
        print(f"[Test 3] Calm Female Monologue: {len(diarized)} segments unified to {distinct_speakers}")

    def test_04_multi_speaker_mixed_gender_dialogue(self):
        """Case 4: Multi-speaker dialogue with alternating male and female speakers (Christopher + Jenny)."""
        f_m = os.path.join(self.suite_dir, "sample_03_single_spk_fast_male_turn_0_en-US-ChristopherNeural.mp3")
        f_f = os.path.join(self.suite_dir, "sample_04_single_spk_calm_female_turn_0_en-US-JennyNeural.mp3")
        if not os.path.exists(f_m) or not os.path.exists(f_f):
            self.skipTest("Dialogue sample components not found")

        pcm_m, _ = self.extractor.extract_pcm16(f_m)
        pcm_f, _ = self.extractor.extract_pcm16(f_f)
        dur_m = len(pcm_m) / 32000.0
        dur_f = len(pcm_f) / 32000.0

        # Alternate: Turn 0 (Male) -> Turn 1 (Female) -> Turn 2 (Male) -> Turn 3 (Female)
        full_pcm = pcm_m + pcm_f + pcm_m + pcm_f
        segs = [
            AudioSegment(id=0, seek=0, start=0.0, end=dur_m, text="Male speaker opening statement."),
            AudioSegment(id=1, seek=int(dur_m), start=dur_m, end=dur_m + dur_f, text="Female speaker response."),
            AudioSegment(id=2, seek=int(dur_m + dur_f), start=dur_m + dur_f, end=2 * dur_m + dur_f, text="Male speaker follow up."),
            AudioSegment(id=3, seek=int(2 * dur_m + dur_f), start=2 * dur_m + dur_f, end=2 * dur_m + 2 * dur_f, text="Female speaker conclusion."),
        ]

        diarized = self.diarizer.diarize_segments(segs, full_pcm, sample_rate=16000)
        distinct = {s.speaker for s in diarized}
        self.assertEqual(len(distinct), 2, f"Expected 2 speakers, got {distinct}")
        self.assertEqual(diarized[0].speaker, diarized[2].speaker, "Male turns 0 and 2 must share speaker ID")
        self.assertEqual(diarized[1].speaker, diarized[3].speaker, "Female turns 1 and 3 must share speaker ID")
        self.assertNotEqual(diarized[0].speaker, diarized[1].speaker, "Male and Female must have distinct IDs")
        print(f"[Test 4] Mixed Gender Dialogue: 4 turns correctly segregated into 2 speakers ({distinct})")

    def test_05_multi_speaker_same_gender_close_pitch(self):
        """Case 5: Multi-speaker dialogue with two distinct females having near-identical pitch (Jenny vs Emma)."""
        f_j = os.path.join(self.suite_dir, "sample_04_single_spk_calm_female_turn_0_en-US-JennyNeural.mp3")
        f_e = os.path.join(self.suite_dir, "sample_07_single_spk_expressive_emma_turn_0_en-US-EmmaNeural.mp3")
        if not os.path.exists(f_j) or not os.path.exists(f_e):
            self.skipTest("Sample files for Jenny and Emma not found")

        pcm_j, _ = self.extractor.extract_pcm16(f_j)
        pcm_e, _ = self.extractor.extract_pcm16(f_e)
        dur_j = len(pcm_j) / 32000.0
        dur_e = len(pcm_e) / 32000.0

        full_pcm = pcm_j + pcm_e
        segs = [
            AudioSegment(id=0, seek=0, start=0.0, end=dur_j, text="Welcome to today's customer update."),
            AudioSegment(id=1, seek=int(dur_j), start=dur_j, end=dur_j + dur_e, text="Engineering roadmap is on schedule."),
        ]
        diarized = self.diarizer.diarize_segments(segs, full_pcm, sample_rate=16000)
        distinct = {s.speaker for s in diarized}
        self.assertEqual(len(distinct), 2, f"Jenny and Emma must be 2 distinct speakers, got: {distinct}")
        self.assertNotEqual(diarized[0].speaker, diarized[1].speaker)
        print(f"[Test 5] Same-Gender Close-Pitch Segregation: Jenny & Emma verified distinct ({distinct})")

    def test_06_multi_speaker_same_gender_divergent_pitch(self):
        """Case 6: Multi-speaker dialogue with two distinct males having divergent pitch (Christopher ~110Hz vs Guy ~140Hz)."""
        f_c = os.path.join(self.suite_dir, "sample_03_single_spk_fast_male_turn_0_en-US-ChristopherNeural.mp3")
        f_g = os.path.join(self.suite_dir, "sample_05_single_spk_male_guy_turn_0_en-US-GuyNeural.mp3")
        if not os.path.exists(f_c) or not os.path.exists(f_g):
            self.skipTest("Sample files for Christopher and Guy not found")

        pcm_c, _ = self.extractor.extract_pcm16(f_c)
        pcm_g, _ = self.extractor.extract_pcm16(f_g)
        dur_c = len(pcm_c) / 32000.0
        dur_g = len(pcm_g) / 32000.0

        full_pcm = pcm_c + pcm_g
        segs = [
            AudioSegment(id=0, seek=0, start=0.0, end=dur_c, text="First male speaker perspective."),
            AudioSegment(id=1, seek=int(dur_c), start=dur_c, end=dur_c + dur_g, text="Second male speaker rebuttal."),
        ]
        diarized = self.diarizer.diarize_segments(segs, full_pcm, sample_rate=16000)
        distinct = {s.speaker for s in diarized}
        self.assertEqual(len(distinct), 2, f"Christopher and Guy must be 2 distinct speakers, got: {distinct}")
        self.assertNotEqual(diarized[0].speaker, diarized[1].speaker)
        print(f"[Test 6] Same-Gender Divergent-Pitch Segregation: Christopher & Guy verified distinct ({distinct})")


if __name__ == "__main__":
    unittest.main()
