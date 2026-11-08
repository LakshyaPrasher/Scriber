"""Unit and behavioral tests for GPU DLL registration, in-memory model caching, and pure-local transcription."""

import os
import unittest
from unittest import mock

import faster_whisper
from scriber.hardware import register_cuda_dll_directories, get_hardware_capabilities
from scriber.transcription_engine import (
    TranscriptionEngine,
    resolve_transcription_device,
)


class TestGpuCacheLocal(unittest.TestCase):
    """Verifies Milestone M6 requirements."""

    def setUp(self):
        TranscriptionEngine.clear_model_cache()

    def test_cuda_dll_registration(self):
        """Verifies that register_cuda_dll_directories runs without error and registers directories."""
        register_cuda_dll_directories()
        caps = get_hardware_capabilities(force_refresh=True)
        # On host with NVIDIA RTX 5050, CUDA must be detected
        self.assertTrue(caps.cuda_available)
        self.assertIn("NVIDIA", caps.gpu_name)

    def test_resolve_transcription_device_resolves_cuda_float16(self):
        """Verifies resolve_transcription_device resolves to ('cuda', 'float16') on host GPU."""
        device, compute_type = resolve_transcription_device()
        self.assertEqual(device, "cuda")
        self.assertEqual(compute_type, "float16")

    def test_in_memory_model_cache_lifecycle(self):
        """Verifies get_cached_model, set_cached_model, and clear_model_cache lifecycle."""
        self.assertIsNone(TranscriptionEngine.get_cached_model("test-model", "cuda", "float16"))
        mock_obj = object()
        TranscriptionEngine.set_cached_model("test-model", "cuda", "float16", mock_obj)
        self.assertIs(TranscriptionEngine.get_cached_model("test-model", "cuda", "float16"), mock_obj)
        TranscriptionEngine.clear_model_cache()
        self.assertIsNone(TranscriptionEngine.get_cached_model("test-model", "cuda", "float16"))

    def test_zero_cloud_api_dependencies(self):
        """Verifies that setting OPENAI_API_KEY and GEMINI_API_KEY does NOT activate cloud-api backend."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake-openai", "GEMINI_API_KEY": "fake-gemini"}):
            engine = TranscriptionEngine()
            self.assertNotEqual(engine.active_backend, "cloud-api")
            self.assertIn(engine.active_backend, ["faster-whisper", "openai-whisper", "whisper-flow-reference"])
            self.assertFalse(hasattr(engine, "_transcribe_cloud_api"))

    def test_model_caching_eliminates_disk_reload(self):
        """Verifies that transcribing with the same model reuses the cached WhisperModel."""
        pcm = b"\x00" * (16000 * 2)  # 1 second silence
        engine = TranscriptionEngine()

        # First transcribe call loads model
        res1 = engine.transcribe(pcm, 1.0, language="en", model="turbo")
        self.assertIsNotNone(res1)
        cached = TranscriptionEngine.get_cached_model(
            "deepdml/faster-whisper-large-v3-turbo-ct2",
            "cuda",
            "float16",
        )
        self.assertIsNotNone(cached)

        # Second transcribe call should reuse cached model without calling faster_whisper.WhisperModel
        with mock.patch("faster_whisper.WhisperModel", side_effect=AssertionError("Should use cached model!")):
            res2 = engine.transcribe(pcm, 1.0, language="en", model="turbo")
            self.assertIsNotNone(res2)


if __name__ == "__main__":
    unittest.main()
