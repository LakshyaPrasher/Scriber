"""Tests for AudioEditor module and /api/edit-audio endpoint.
Validates volume scaling, pitch shifting, trimming, and MP3 generation.
"""

import json
import unittest
import numpy as np

from scriber.audio_editor import AudioEditor
from scriber.pipeline import ScriberPipeline


class TestAudioEditor(unittest.TestCase):
    """Unit tests for AudioEditor."""

    def setUp(self):
        self.sr = 16000
        t = np.linspace(0, 2.0, self.sr * 2, endpoint=False)
        self.raw_pcm = (np.sin(2 * np.pi * 440 * t) * 20000).astype(np.int16).tobytes()

    def test_trimming(self):
        """Verifies start and end trimming accurately reduces duration."""
        edited, dur = AudioEditor.edit_pcm16(
            pcm_bytes=self.raw_pcm,
            sr=self.sr,
            volume=1.0,
            pitch_semitones=0.0,
            start_sec=0.5,
            end_sec=1.5,
        )
        self.assertAlmostEqual(dur, 1.0, places=2)
        self.assertEqual(len(edited), int(1.0 * self.sr * 2))

    def test_volume_scaling(self):
        """Verifies volume scaling modifies amplitude within valid ranges."""
        edited_half, _ = AudioEditor.edit_pcm16(self.raw_pcm, sr=self.sr, volume=0.5)
        arr_half = np.frombuffer(edited_half, dtype=np.int16)
        arr_orig = np.frombuffer(self.raw_pcm, dtype=np.int16)
        self.assertAlmostEqual(np.max(np.abs(arr_half)) / np.max(np.abs(arr_orig)), 0.5, delta=0.05)

    def test_pitch_shift(self):
        """Verifies pitch shift retains duration while transforming waveform."""
        shifted, dur = AudioEditor.edit_pcm16(self.raw_pcm, sr=self.sr, pitch_semitones=3.0)
        self.assertAlmostEqual(dur, 2.0, places=2)
        self.assertEqual(len(shifted), len(self.raw_pcm))

    def test_mp3_encoding(self):
        """Verifies MP3 encoding returns valid binary bytes."""
        mp3_data = AudioEditor.encode_mp3(self.raw_pcm, sr=self.sr, channels=1, bit_rate=192000)
        self.assertTrue(len(mp3_data) > 1000)
        self.assertTrue(isinstance(mp3_data, bytes))

    def test_pipeline_edit_audio(self):
        """Verifies pipeline.edit_audio processes audio and produces structured output."""
        pipeline = ScriberPipeline()
        res = pipeline.edit_audio(
            pcm_data=self.raw_pcm,
            volume=1.2,
            pitch_semitones=-2.0,
            start_sec=0.2,
            end_sec=1.2,
            filename="test_pipeline_edit.mp3",
        )
        self.assertTrue(res["success"])
        self.assertAlmostEqual(res["duration"], 1.0, places=1)
        self.assertTrue(res["audio_base64"].startswith("data:audio/mp3;base64,"))


if __name__ == "__main__":
    unittest.main()
