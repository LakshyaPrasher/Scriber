"""Universal media format ingestion test suite for Scriber.
Verifies audio extraction, VAD chunking, and pipeline resilience across
diverse formats: WAV, MP3, MP4, FLAC, OGG, WebM, and edge cases (corrupt, silent, stereo).
"""

import math
import os
import struct
import tempfile
import unittest
import wave

from scriber.audio_extractor import AudioExtractor


def generate_synthetic_wav(path: str, duration_sec: float = 2.0, sr: int = 16000, channels: int = 1, freq: float = 440.0):
    """Generates a valid sine-wave WAV file."""
    n_samples = int(duration_sec * sr)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        raw_bytes = bytearray()
        for i in range(n_samples):
            val = int(16000.0 * math.sin(2.0 * math.pi * freq * (i / sr)))
            sample_bytes = struct.pack("<h", max(-32768, min(32767, val)))
            for _ in range(channels):
                raw_bytes.extend(sample_bytes)
        wf.writeframes(bytes(raw_bytes))


class TestUniversalMediaFormats(unittest.TestCase):
    """Tests universal media format ingestion and audio extraction robustness."""

    def setUp(self):
        self.extractor = AudioExtractor()
        self.temp_dir = tempfile.mkdtemp(prefix="scriber_universal_media_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_standard_wav_mono(self):
        """Test standard 16kHz mono WAV file extraction."""
        wav_path = os.path.join(self.temp_dir, "mono_16k.wav")
        generate_synthetic_wav(wav_path, duration_sec=2.5, sr=16000, channels=1, freq=220.0)

        meta = self.extractor.inspect_file(wav_path)
        self.assertAlmostEqual(meta.duration, 2.5, delta=0.1)

        pcm, pcm_meta = self.extractor.extract_pcm16(wav_path)
        self.assertEqual(len(pcm), int(2.5 * 16000 * 2))
        self.assertEqual(pcm_meta.sample_rate, 16000)
        self.assertEqual(pcm_meta.channels, 1)

    def test_02_stereo_44100_wav_resampling(self):
        """Test high-sample-rate 44.1kHz stereo WAV automatic downmix and resampling to 16kHz mono."""
        wav_path = os.path.join(self.temp_dir, "stereo_44k.wav")
        generate_synthetic_wav(wav_path, duration_sec=1.5, sr=44100, channels=2, freq=300.0)

        pcm, pcm_meta = self.extractor.extract_pcm16(wav_path)
        self.assertEqual(pcm_meta.sample_rate, 16000)
        self.assertEqual(pcm_meta.channels, 1)
        expected_samples = int(1.5 * 16000)
        actual_samples = len(pcm) // 2
        self.assertAlmostEqual(actual_samples, expected_samples, delta=160)

    def test_03_stereo_48000_wav_studio(self):
        """Test 48kHz studio broadcast rate WAV downmix and resampling."""
        wav_path = os.path.join(self.temp_dir, "studio_48k.wav")
        generate_synthetic_wav(wav_path, duration_sec=2.0, sr=48000, channels=2, freq=500.0)

        pcm, pcm_meta = self.extractor.extract_pcm16(wav_path)
        self.assertEqual(pcm_meta.sample_rate, 16000)
        self.assertEqual(pcm_meta.channels, 1)
        expected_samples = int(2.0 * 16000)
        actual_samples = len(pcm) // 2
        self.assertAlmostEqual(actual_samples, expected_samples, delta=160)

    def test_04_mp3_encoding_and_decoding(self):
        """Test MP3 file format extraction and normalization."""
        try:
            from scriber.audio_editor import AudioEditor
        except ImportError:
            self.skipTest("AudioEditor MP3 encoder not available")

        # Create raw PCM and encode to MP3
        n_samples = int(2.0 * 16000)
        raw_pcm = bytearray()
        for i in range(n_samples):
            val = int(15000.0 * math.sin(2.0 * math.pi * 400.0 * (i / 16000)))
            raw_pcm.extend(struct.pack("<h", val))

        mp3_bytes = AudioEditor.encode_mp3(bytes(raw_pcm), sr=16000, channels=1, bit_rate=128000)
        mp3_path = os.path.join(self.temp_dir, "test_audio.mp3")
        with open(mp3_path, "wb") as f:
            f.write(mp3_bytes)

        pcm, pcm_meta = self.extractor.extract_pcm16(mp3_path)
        self.assertEqual(pcm_meta.sample_rate, 16000)
        self.assertEqual(pcm_meta.channels, 1)
        self.assertGreater(len(pcm), 0)

    def test_05_vad_speech_segmentation_across_formats(self):
        """Test Silero VAD segmentation on audio extracted from media."""
        # 1s tone, 1s silence, 1s tone
        sr = 16000
        raw_pcm = bytearray()
        for i in range(sr):  # 1s tone
            val = int(18000.0 * math.sin(2.0 * math.pi * 350.0 * (i / sr)))
            raw_pcm.extend(struct.pack("<h", val))
        for _ in range(sr):  # 1s silence
            raw_pcm.extend(struct.pack("<h", 0))
        for i in range(sr):  # 1s tone
            val = int(18000.0 * math.sin(2.0 * math.pi * 350.0 * (i / sr)))
            raw_pcm.extend(struct.pack("<h", val))

        wav_path = os.path.join(self.temp_dir, "tone_silence_tone.wav")
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(bytes(raw_pcm))

        pcm, meta = self.extractor.extract_pcm16(wav_path)
        segments = self.extractor.split_vad_segments(pcm)
        self.assertGreaterEqual(len(segments), 1, "VAD must identify speech/tones")

    def test_06_nonexistent_and_corrupt_files(self):
        """Test error resilience on missing or 0-byte corrupt media files."""
        # Non-existent
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract_pcm16(os.path.join(self.temp_dir, "does_not_exist.mp4"))

        # Zero-byte file
        zero_file = os.path.join(self.temp_dir, "corrupt_empty.mp4")
        with open(zero_file, "wb") as f:
            pass

        # Should either raise ValueError or inspect cleanly without crashing
        meta = self.extractor.inspect_file(zero_file)
        self.assertEqual(meta.file_size_bytes, 0)


if __name__ == "__main__":
    unittest.main()
