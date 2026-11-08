"""Comprehensive Unit Tests for Deep ONNX Neural Speaker Diarization.

Verifies:
1. CAM++ ONNX model asset presence and session initialization.
2. 80-bin Mel filterbank computation and frame-level CMVN.
3. 192-dimensional unit-normalized (L2 = 1.0) speaker embeddings.
4. Cosine distance metric and conversational continuity prior discount (0.60x).
5. SpeakerMemory centroid maintenance and probabilistic match scoring.
6. AHC clustering with calibrated neural threshold.
7. Graceful zero-dependency fallback when ONNX model is missing or disabled.
"""

from __future__ import annotations

import os
import unittest
import numpy as np

from scriber.diarizer import AcousticDiarizer, NeuralSpeakerExtractor, SpeakerMemory
from scriber.models import AudioSegment, VoiceProfile
from scriber.voice_clone import VoiceProfiler


class TestNeuralSpeakerDiarizer(unittest.TestCase):
    """Test suite for CAM++ deep ONNX neural speaker embeddings and diarization."""

    @classmethod
    def setUpClass(cls):
        cls.sr = 16000
        cls.model_path = os.path.abspath("scriber/assets/models/campplus_cn_en_common_200k.onnx")
        cls.extractor = NeuralSpeakerExtractor(model_path=cls.model_path)

    def test_01_model_asset_exists_and_loads(self):
        """Verifies CAM++ ONNX model asset exists (~28.2 MB) and loads into ONNX Runtime session."""
        self.assertTrue(os.path.exists(self.model_path), f"Model file not found at {self.model_path}")
        size_bytes = os.path.getsize(self.model_path)
        self.assertGreater(size_bytes, 25 * 1024 * 1024, f"Model size {size_bytes} is smaller than expected 25MB")
        self.assertTrue(self.extractor.is_available, "NeuralSpeakerExtractor failed to initialize ONNX session")
        self.assertIsNotNone(self.extractor.session, "InferenceSession must not be None")

    def test_02_mel_fbank_cmvn_features(self):
        """Verifies 80-bin log mel-filterbank feature extraction and frame-level CMVN normalization."""
        # Generate 1.0s synthetic audio
        t = np.linspace(0, 1.0, self.sr, endpoint=False)
        tone = (0.5 * np.sin(2 * np.pi * 200 * t) * 32767).astype(np.int16).tobytes()

        feats = self.extractor.compute_fbank(tone, sample_rate=self.sr)
        self.assertEqual(feats.ndim, 2, "Mel Fbank features must be a 2D matrix (frames, 80)")
        self.assertEqual(feats.shape[1], 80, "Mel Fbank features must contain exactly 80 mel frequency bins")
        self.assertGreater(feats.shape[0], 50, "1.0s audio must yield at least 50 frames with 10ms shift")

        # Verify CMVN: Mean across frames (axis 0) should be near zero (< 1e-4)
        frame_mean = np.mean(feats, axis=0)
        np.testing.assert_allclose(frame_mean, np.zeros(80), atol=1e-4, err_msg="CMVN failed: frame mean not normalized to zero")

    def test_03_neural_embedding_shape_and_l2_normalization(self):
        """Verifies CAM++ extracts exactly 192-d unit-normalized (L2 = 1.0) embedding vectors."""
        t = np.linspace(0, 1.5, int(1.5 * self.sr), endpoint=False)
        audio = (0.4 * np.sin(2 * np.pi * 150 * t) + 0.2 * np.sin(2 * np.pi * 300 * t)) * 32767
        pcm = audio.astype(np.int16).tobytes()

        emb = self.extractor.extract_embedding(pcm, sample_rate=self.sr)
        self.assertIsNotNone(emb, "Embedding extraction returned None")
        self.assertEqual(emb.shape, (192,), f"Expected shape (192,), got {emb.shape}")
        self.assertEqual(emb.dtype, np.float32, "Embedding dtype must be float32")

        l2_norm = float(np.linalg.norm(emb))
        self.assertAlmostEqual(l2_norm, 1.0, places=5, msg=f"Embedding not unit-normalized: norm = {l2_norm}")

    def test_04_cosine_distance_and_continuity_prior(self):
        """Verifies pairwise neural cosine distance computation and conversational continuity discount."""
        # Two random unit vectors representing different speakers
        rng = np.random.RandomState(42)
        v1 = rng.randn(192).astype(np.float32)
        v1 /= np.linalg.norm(v1)
        v2 = rng.randn(192).astype(np.float32)
        v2 /= np.linalg.norm(v2)

        p1 = VoiceProfile(speaker_id="temp1", fundamental_frequency_hz=140.0, pitch_min_hz=100.0, pitch_max_hz=180.0,
                          pitch_std_hz=10.0, spectral_centroid_hz=1500.0, zero_crossing_rate=0.05, estimated_wpm=150.0,
                          energy_rms=0.1, gender_estimate="masculine", sample_duration=1.0)
        p2 = VoiceProfile(speaker_id="temp2", fundamental_frequency_hz=142.0, pitch_min_hz=100.0, pitch_max_hz=180.0,
                          pitch_std_hz=10.0, spectral_centroid_hz=1520.0, zero_crossing_rate=0.05, estimated_wpm=150.0,
                          energy_rms=0.1, gender_estimate="masculine", sample_duration=1.0)

        # Distance to self should be near 0
        self_dist = AcousticDiarizer.compute_acoustic_distance(p1, p1, vec1=v1, vec2=v1)
        self.assertAlmostEqual(self_dist, 0.0, places=4, msg="Distance between identical embeddings must be 0")

        # Distance between distinct vectors
        diff_dist = AcousticDiarizer.compute_acoustic_distance(p1, p2, vec1=v1, vec2=v2)
        expected_cos_dist = 1.0 - max(0.0, min(1.0, float(np.dot(v1, v2))))
        self.assertAlmostEqual(diff_dist, expected_cos_dist, places=4)

        # Test continuity discount (0.60x) on adjacent segments of same speaker (cos_sim >= 0.70)
        v_orth = rng.randn(192).astype(np.float32)
        v_orth -= float(np.dot(v1, v_orth)) * v1
        v_orth /= np.linalg.norm(v_orth)
        v_same = (0.85 * v1 + np.sqrt(1.0 - 0.85**2) * v_orth).astype(np.float32)

        dist_non_adjacent = AcousticDiarizer.compute_acoustic_distance(p1, p2, pause_sec=1.0, is_adjacent=False, vec1=v1, vec2=v_same)
        dist_adjacent = AcousticDiarizer.compute_acoustic_distance(p1, p2, pause_sec=1.0, is_adjacent=True, vec1=v1, vec2=v_same)

        self.assertAlmostEqual(dist_adjacent, dist_non_adjacent * 0.60, places=4, msg="Adjacent continuity discount (0.60x) not applied")

    def test_05_speaker_memory_centroid_tracking(self):
        """Verifies SpeakerMemory maintains 192-d normalized centroid and updates running profile."""
        v0 = np.ones(192, dtype=np.float32) / np.sqrt(192)
        p0 = VoiceProfile(speaker_id="Speaker_1", fundamental_frequency_hz=130.0, pitch_min_hz=100.0, pitch_max_hz=160.0,
                          pitch_std_hz=8.0, spectral_centroid_hz=1400.0, zero_crossing_rate=0.05, estimated_wpm=140.0,
                          energy_rms=0.1, gender_estimate="masculine", sample_duration=2.0)

        mem = SpeakerMemory("Speaker_1", p0, v0)
        self.assertEqual(mem.centroid_vector.shape, (192,))
        self.assertAlmostEqual(float(np.linalg.norm(mem.centroid_vector)), 1.0, places=5)

        # Update with second chunk
        v1 = np.zeros(192, dtype=np.float32)
        v1[0] = 1.0
        p1 = VoiceProfile(speaker_id="Speaker_1", fundamental_frequency_hz=140.0, pitch_min_hz=110.0, pitch_max_hz=170.0,
                          pitch_std_hz=9.0, spectral_centroid_hz=1500.0, zero_crossing_rate=0.06, estimated_wpm=150.0,
                          energy_rms=0.12, gender_estimate="masculine", sample_duration=3.0)

        mem.update(p1, v1)
        self.assertEqual(len(mem.vectors), 2)
        self.assertAlmostEqual(float(np.linalg.norm(mem.centroid_vector)), 1.0, places=5)
        # Total duration = 2.0 + 3.0 = 5.0
        self.assertAlmostEqual(mem.total_duration, 5.0, places=3)
        # Weighted mean F0 = (130 * 2 + 140 * 3) / 5 = 136.0
        self.assertAlmostEqual(mem.mean_f0, 136.0, places=2)

    def test_06_graceful_fallback_when_model_missing(self):
        """Verifies graceful fallback to 16-d DSP voice vector when model path does not exist."""
        dummy_extractor = NeuralSpeakerExtractor(model_path="nonexistent_campplus_model.onnx")
        self.assertFalse(dummy_extractor.is_available)
        self.assertIsNone(dummy_extractor.session)

        # extract_embedding returns None
        t = np.linspace(0, 1.0, self.sr, endpoint=False)
        pcm = ((0.5 * np.sin(2 * np.pi * 150 * t)) * 32767).astype(np.int16).tobytes()
        res = dummy_extractor.extract_embedding(pcm, sample_rate=self.sr)
        self.assertIsNone(res, "Missing model must cleanly return None without raising exceptions")

        # AcousticDiarizer with dummy extractor falls back cleanly
        diarizer = AcousticDiarizer(similarity_threshold=0.48, extractor=dummy_extractor)
        seg1 = AudioSegment(id=0, seek=0, start=0.0, end=0.5, text="First utterance.")
        seg2 = AudioSegment(id=1, seek=1, start=0.5, end=1.0, text="Second utterance.")
        diarized = diarizer.diarize_segments([seg1, seg2], pcm, sample_rate=self.sr)

        self.assertEqual(len(diarized), 1)
        self.assertEqual(diarized[0].speaker, "Speaker_1")

    def test_07_ahc_clustering_multi_speaker_neural(self):
        """Verifies neural embedding clustering cleanly segregates distinct voices."""
        # Speaker A (120 Hz) vs Speaker B (240 Hz)
        t = np.linspace(0, 2.0, int(2.0 * self.sr), endpoint=False)
        pcm_a = ((0.5 * np.sin(2 * np.pi * 120 * t) + 0.2 * np.sin(2 * np.pi * 240 * t)) * 32767).astype(np.int16).tobytes()
        pcm_b = ((0.5 * np.sin(2 * np.pi * 240 * t) + 0.2 * np.sin(2 * np.pi * 480 * t)) * 32767).astype(np.int16).tobytes()

        full_pcm = pcm_a + pcm_b
        seg1 = AudioSegment(id=0, seek=0, start=0.0, end=2.0, text="Turn from first speaker.")
        seg2 = AudioSegment(id=1, seek=2, start=2.0, end=4.0, text="Turn from second speaker.")

        diarizer = AcousticDiarizer(similarity_threshold=0.48, extractor=self.extractor)
        diarized = diarizer.diarize_segments([seg1, seg2], full_pcm, sample_rate=self.sr)

        speakers = {s.speaker for s in diarized}
        self.assertEqual(len(speakers), 2, f"Expected 2 distinct speakers, got {speakers}")


if __name__ == "__main__":
    unittest.main()
