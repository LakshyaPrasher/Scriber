"""Unit and Integration Tests for Whisper Large-v3-Turbo Cache Repair & Execution.

Validates:
1. Complete download and integrity of model.bin (~1.61 GB) in HuggingFace cache.
2. Absence of IncompleteSnapshotError under local_files_only=True.
3. TranscriptionEngine genuine execution of Large-v3-Turbo without falling back to Base.
4. Dynamic device configuration and strict non-fallback guarantees.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest import mock

import faster_whisper
from scriber.transcription_engine import (
    SUPPORTED_TRANSCRIBE_MODELS,
    TranscriptionEngine,
    is_model_snapshot_valid,
    resolve_transcription_device,
)


class TestWhisperTurboCache(unittest.TestCase):
    """Test suite for Whisper Turbo HuggingFace cache and model execution."""

    @classmethod
    def setUpClass(cls):
        cls.hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface/hub"))
        cls.repo_cache_dir = os.path.join(
            cls.hf_home,
            "models--deepdml--faster-whisper-large-v3-turbo-ct2",
        )
        cls.snapshot_dir = os.path.join(
            cls.repo_cache_dir,
            "snapshots",
            "4df90f75321148c3a29a9e2351b7ddf8f5b115a8",
        )
        cls.model_bin_path = os.path.join(cls.snapshot_dir, "model.bin")

    def test_turbo_cache_directory_and_model_bin_size(self):
        """Verifies model.bin exists in the HuggingFace cache snapshot and is >= 1.5 GB."""
        self.assertTrue(
            os.path.isdir(self.snapshot_dir),
            f"Snapshot directory missing: {self.snapshot_dir}",
        )
        self.assertTrue(
            os.path.isfile(self.model_bin_path),
            f"model.bin weight file missing from snapshot: {self.model_bin_path}",
        )
        model_size_bytes = os.path.getsize(self.model_bin_path)
        min_expected_bytes = int(1.5 * 1024 * 1024 * 1024)  # 1.5 GB
        self.assertGreaterEqual(
            model_size_bytes,
            min_expected_bytes,
            f"model.bin size {model_size_bytes} is less than minimum expected 1.5 GB (~1.61 GB expected)",
        )

    def test_turbo_cache_required_metadata_files(self):
        """Verifies all required configuration, tokenizer, and vocabulary files are present."""
        required_files = [
            "config.json",
            "preprocessor_config.json",
            "tokenizer.json",
            "vocabulary.json",
            "model.bin",
        ]
        for fname in required_files:
            fpath = os.path.join(self.snapshot_dir, fname)
            self.assertTrue(os.path.isfile(fpath), f"Required asset '{fname}' missing from snapshot")
            self.assertGreater(os.path.getsize(fpath), 0, f"Asset '{fname}' is empty")

    def test_no_incomplete_blobs_in_cache(self):
        """Verifies no interrupted .incomplete download blobs remain in the repo cache."""
        blobs_dir = os.path.join(self.repo_cache_dir, "blobs")
        if os.path.isdir(blobs_dir):
            incomplete = [
                f for f in os.listdir(blobs_dir) if f.endswith(".incomplete")
            ]
            self.assertEqual(
                incomplete,
                [],
                f"Found unfinished download blobs in cache: {incomplete}",
            )

    def test_config_json_declares_turbo_architecture(self):
        """Verifies config.json reflects the OpenAI Large-v3-Turbo 4-decoder-layer architecture."""
        config_path = os.path.join(self.snapshot_dir, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertTrue(
            "alignment_heads" in cfg or "decoder_layers" in cfg,
            "config.json does not contain architectural layer specifications",
        )
        if "alignment_heads" in cfg:
            max_head_layer = max(h[0] for h in cfg["alignment_heads"])
            self.assertLessEqual(
                max_head_layer,
                3,
                f"Expected 4-layer decoder (indices 0..3) for Large-v3-Turbo, found max layer index {max_head_layer}",
            )

    def test_whisper_model_direct_load_local_files_only(self):
        """Verifies faster_whisper.WhisperModel loads with local_files_only=True without IncompleteSnapshotError."""
        model = faster_whisper.WhisperModel(
            "deepdml/faster-whisper-large-v3-turbo-ct2",
            device="cpu",
            compute_type="int8",
            local_files_only=True,
        )
        self.assertIsNotNone(model)

    def test_is_model_snapshot_valid_helper(self):
        """Verifies is_model_snapshot_valid helper returns True for complete models and False for invalid."""
        self.assertTrue(is_model_snapshot_valid("deepdml/faster-whisper-large-v3-turbo-ct2"))
        self.assertTrue(is_model_snapshot_valid("turbo"))
        self.assertTrue(is_model_snapshot_valid("base"))
        self.assertFalse(is_model_snapshot_valid("nonexistent/invalid-model-name"))

    def test_resolve_transcription_device(self):
        """Verifies resolve_transcription_device dynamically produces valid (device, compute_type)."""
        device, compute_type = resolve_transcription_device()
        self.assertIn(device, ["cuda", "cpu"])
        self.assertIn(compute_type, ["float16", "int8_float16", "int8", "float32"])

    def test_transcription_engine_turbo_execution_no_fallback(self):
        """Verifies TranscriptionEngine.transcribe with model='turbo' executes without falling back to Base."""
        engine = TranscriptionEngine()
        pcm = b"\x00" * (16000 * 2 * 2)  # 2 seconds of silence at 16kHz mono 16-bit
        result = engine.transcribe(pcm, duration=2.0, model="turbo")

        self.assertIsNotNone(result)
        self.assertEqual(
            result.backend_used,
            "SYSTRAN/faster-whisper (turbo)",
            f"Expected true Turbo backend, got: '{result.backend_used}'",
        )
        self.assertNotIn(
            "fallback",
            result.backend_used.lower(),
            f"Model execution fell back: {result.backend_used}",
        )
        self.assertNotIn(
            "base",
            result.backend_used.lower(),
            f"Model executed Base instead of Turbo: {result.backend_used}",
        )
        self.assertEqual(result.model_name, "whisper-turbo")
        self.assertGreaterEqual(result.duration, 0.0)

    def test_transcription_engine_turbo_eliminates_silent_base_fallback(self):
        """Verifies that if Whisper Turbo fails to load, it raises rather than silently falling back to Base."""
        engine = TranscriptionEngine()
        pcm = b"\x00" * (16000 * 2)

        with mock.patch("faster_whisper.WhisperModel", side_effect=RuntimeError("Corrupt weight file")):
            with self.assertRaises(RuntimeError) as ctx:
                engine._transcribe_faster_whisper(pcm, 1.0, "en", "transcribe", model_name="turbo")
            self.assertIn("Fallback to Base is strictly disabled for Turbo", str(ctx.exception))

    def test_device_fallback_from_cuda_to_cpu_preserves_turbo_model(self):
        """Verifies that if CUDA device execution fails, it safely falls back to CPU for the SAME model (Turbo)."""
        engine = TranscriptionEngine()
        pcm = b"\x00" * (16000 * 2)

        real_model_cls = faster_whisper.WhisperModel
        call_count = {"cuda_attempts": 0, "cpu_attempts": 0}

        def mock_whisper_model(model_name, device, compute_type, local_files_only=True):
            if device == "cuda":
                call_count["cuda_attempts"] += 1
                raise RuntimeError("Library cublas64_12.dll is not found")
            call_count["cpu_attempts"] += 1
            return real_model_cls(
                model_name,
                device="cpu",
                compute_type="int8",
                local_files_only=True,
            )

        with mock.patch("scriber.transcription_engine.resolve_transcription_device", return_value=("cuda", "float16")):
            with mock.patch("faster_whisper.WhisperModel", side_effect=mock_whisper_model):
                res = engine._transcribe_faster_whisper(pcm, 1.0, "en", "transcribe", model_name="turbo")

        self.assertGreaterEqual(call_count["cuda_attempts"], 1)
        self.assertGreaterEqual(call_count["cpu_attempts"], 1)
        self.assertEqual(res.backend_used, "SYSTRAN/faster-whisper (turbo)")
        self.assertNotIn("base", res.backend_used.lower())


if __name__ == "__main__":
    unittest.main()
