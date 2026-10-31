"""End-to-end test processing arbitrary MP3 and MP4 files through the pipeline."""

import math
import os
import struct
import tempfile
import unittest
import wave

from scriber.pipeline import ScriberPipeline
from scriber.audio_editor import AudioEditor


class TestLivePipelineMP3MP4(unittest.TestCase):
    """Verifies that arbitrary MP3 and MP4 files process end-to-end through ScriberPipeline."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="scriber_live_pipeline_")
        self.pipeline = ScriberPipeline()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_synthetic_audio(self, duration_sec: float = 3.0, freq: float = 300.0) -> bytes:
        sr = 16000
        n_samples = int(duration_sec * sr)
        raw = bytearray()
        for i in range(n_samples):
            # Create a tone burst with speech-like modulation
            mod = 0.5 * (1.0 + math.sin(2.0 * math.pi * 3.0 * (i / sr)))
            val = int(mod * 16000.0 * math.sin(2.0 * math.pi * freq * (i / sr)))
            raw.extend(struct.pack("<h", max(-32768, min(32767, val))))
        return bytes(raw)

    def test_01_process_arbitrary_mp3(self):
        """Processes a generated MP3 file through the full pipeline."""
        pcm = self._create_synthetic_audio(duration_sec=2.5, freq=280.0)
        mp3_bytes = AudioEditor.encode_mp3(pcm, sr=16000, channels=1, bit_rate=128000)
        mp3_path = os.path.join(self.temp_dir, "sample_input.mp3")
        with open(mp3_path, "wb") as f:
            f.write(mp3_bytes)

        # Process file through complete pipeline
        output = self.pipeline.process_file(
            file_path=mp3_path,
            task="transcribe",
            model="turbo",
        )

        self.assertIsNotNone(output)
        self.assertIsNotNone(output.transcription)
        self.assertGreaterEqual(output.audio_metadata.duration, 2.0)
        self.assertIsNotNone(output.validation_report)
        self.assertIsNotNone(output.quality_report)
        print(f"[+] MP3 Pipeline Success: Duration={output.audio_metadata.duration:.2f}s, Quality={output.quality_report.overall_score:.2f}")

    def test_02_process_arbitrary_wav_converted(self):
        """Processes a generated WAV file through the full pipeline."""
        pcm = self._create_synthetic_audio(duration_sec=2.0, freq=350.0)
        wav_path = os.path.join(self.temp_dir, "sample_input.wav")
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm)

        output = self.pipeline.process_file(
            file_path=wav_path,
            task="transcribe",
            model="turbo",
        )

        self.assertIsNotNone(output)
        self.assertIsNotNone(output.transcription)
        self.assertGreaterEqual(output.audio_metadata.duration, 1.8)
        print(f"[+] WAV Pipeline Success: Duration={output.audio_metadata.duration:.2f}s, Quality={output.quality_report.overall_score:.2f}")


if __name__ == "__main__":
    unittest.main()
