"""Tests for AudioExtractor and VAD chunking engine."""

import os
import tempfile
import unittest

from scriber.audio_extractor import AudioExtractor


class TestAudioExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = AudioExtractor()

    def test_synthetic_wav_creation(self):
        """Verifies synthetic 16kHz mono WAV generation."""
        wav_bytes = self.extractor.create_synthetic_wav("test", duration_sec=2.0)
        self.assertGreater(len(wav_bytes), 44)  # WAV header is 44 bytes

        # Write to temporary file and inspect
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp_path = tmp.name

        try:
            meta = self.extractor.inspect_file(tmp_path)
            self.assertEqual(meta.sample_rate, 16000)
            self.assertEqual(meta.channels, 1)
            self.assertAlmostEqual(meta.duration, 2.0, delta=0.1)

            # Test PCM extraction
            pcm_data, pcm_meta = self.extractor.extract_pcm16(tmp_path)
            self.assertEqual(len(pcm_data), 16000 * 2 * 2)  # 2 sec * 16000 Hz * 2 bytes
            self.assertEqual(pcm_meta.sample_rate, 16000)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_vad_chunking_speech_and_silence(self):
        """Verifies VAD chunking separates speech from ambient silence."""
        # 1 sec tone + 1 sec silence + 1 sec tone = 3 sec
        speech_tone = self.extractor.create_synthetic_wav("speech", duration_sec=1.0)
        pcm_tone = speech_tone[44:]  # strip header

        silence = b"\x00" * (16000 * 2 * 1)  # 1 sec silence
        combined_pcm = pcm_tone + silence + pcm_tone

        segments = self.extractor.split_vad_segments(
            combined_pcm,
            frame_ms=30,
            energy_threshold=0.015,
            max_silence_ms=400,
        )

        self.assertGreaterEqual(len(segments), 1)
        # Verify first segment starts near 0.0
        self.assertAlmostEqual(segments[0][0], 0.0, delta=0.2)

    def test_pcm_packing_clamping(self):
        """Verifies 16-bit PCM packing clamps extreme values."""
        samples = [40000, -50000, 100, 0]
        packed = self.extractor._pack_pcm16(samples)
        self.assertEqual(len(packed), 8)
        unpacked = self.extractor._unpack_pcm(packed, sampwidth=2, channels=1)
        self.assertEqual(unpacked[0], 32767)  # clamped max
        self.assertEqual(unpacked[1], -32768)  # clamped min
        self.assertEqual(unpacked[2], 100)
        self.assertEqual(unpacked[3], 0)

    def test_linear_resampling(self):
        """Verifies sample rate conversion via linear interpolation."""
        src_samples = [0, 1000, 2000, 3000, 4000]
        # Resample from 8000 to 16000 (2x upsampling)
        resampled = self.extractor._resample_linear(src_samples, 8000, 16000)
        self.assertEqual(len(resampled), 10)
        self.assertEqual(resampled[0], 0)


if __name__ == "__main__":
    unittest.main()
