"""Empirical Adversarial Stress Test Suite for Milestone M6.

Stress-tests:
1. Concurrency stress: 10 concurrent threads invoking transcribe() on warm and cold cache.
2. Cache lifecycle: clear_model_cache, clean reload, VRAM model sharing across multiple TranscriptionEngine instances.
3. Cloud isolation: hostile fake API keys + outbound network socket blocker.
"""

from __future__ import annotations

import concurrent.futures
import os
import socket
import threading
import time
import unittest
from unittest import mock

from scriber.audio_extractor import AudioExtractor
from scriber.transcription_engine import TranscriptionEngine, resolve_transcription_device

TEST_VIDEO = r"C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4"


class TestM6AdversarialChallenge(unittest.TestCase):
    """Adversarial stress-testing suite for Milestone M6."""

    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_VIDEO):
            cls.pcm_data, cls.meta = AudioExtractor().extract_pcm16(TEST_VIDEO)
        else:
            cls.pcm_data = b"\x00" * (16000 * 2 * 3)  # 3 seconds silence
            cls.meta = mock.Mock(duration=3.0)

    def setUp(self):
        # Reset cache before tests where needed
        TranscriptionEngine.clear_model_cache()

    def tearDown(self):
        TranscriptionEngine.clear_model_cache()

    # -------------------------------------------------------------------------
    # 1. Concurrency Stress Tests
    # -------------------------------------------------------------------------
    def test_concurrency_warm_cache_10_threads(self):
        """Stress test: 10 concurrent threads executing transcribe() simultaneously on warm cache."""
        # Warm up the cache
        engine_warm = TranscriptionEngine()
        res_warm = engine_warm.transcribe(self.pcm_data, self.meta.duration, language="en", model="turbo")
        expected_text = res_warm.text
        self.assertTrue(len(expected_text) > 0, "Warm-up transcription returned empty text")

        # Barrier to synchronize start of all 10 threads
        barrier = threading.Barrier(10)
        results = [None] * 10
        errors = [None] * 10
        latencies = [0.0] * 10

        def worker_task(idx: int):
            try:
                # Each thread uses its own TranscriptionEngine instance
                engine = TranscriptionEngine()
                barrier.wait(timeout=10.0)  # synchronize burst
                t0 = time.perf_counter()
                res = engine.transcribe(self.pcm_data, self.meta.duration, language="en", model="turbo")
                latencies[idx] = time.perf_counter() - t0
                results[idx] = res
            except Exception as e:
                errors[idx] = e

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        # Check for any exceptions or deadlocks
        for i, err in enumerate(errors):
            self.assertIsNone(err, f"Thread {i} encountered error: {err}")

        for i, res in enumerate(results):
            self.assertIsNotNone(res, f"Thread {i} timed out or produced None")
            self.assertEqual(
                res.text,
                expected_text,
                f"Thread {i} produced inconsistent output: '{res.text}' vs '{expected_text}'",
            )
            self.assertEqual(res.model_name, "whisper-turbo")
            self.assertIn("faster-whisper", res.backend_used.lower())

        print(f"\n[Warm Concurrency 10 Threads] Average latency: {sum(latencies)/len(latencies):.3f}s, Max: {max(latencies):.3f}s")

    def test_concurrency_cold_cache_10_threads(self):
        """Stress test: 10 concurrent threads hitting transcribe() simultaneously with COLD cache."""
        TranscriptionEngine.clear_model_cache()
        self.assertEqual(len(TranscriptionEngine._MODEL_CACHE), 0)

        barrier = threading.Barrier(10)
        results = [None] * 10
        errors = [None] * 10
        latencies = [0.0] * 10

        def worker_task(idx: int):
            try:
                engine = TranscriptionEngine()
                barrier.wait(timeout=10.0)  # All 10 threads hit cold cache simultaneously
                t0 = time.perf_counter()
                res = engine.transcribe(self.pcm_data, self.meta.duration, language="en", model="turbo")
                latencies[idx] = time.perf_counter() - t0
                results[idx] = res
            except Exception as e:
                errors[idx] = e

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60.0)

        for i, err in enumerate(errors):
            self.assertIsNone(err, f"Thread {i} encountered error on cold cache: {err}")

        reference_text = None
        for i, res in enumerate(results):
            self.assertIsNotNone(res, f"Thread {i} produced None on cold cache")
            if reference_text is None:
                reference_text = res.text
            self.assertEqual(
                res.text,
                reference_text,
                f"Thread {i} produced mismatched text on cold cache: {res.text}",
            )

        print(f"\n[Cold Concurrency 10 Threads] All 10 threads resolved safely. Average latency: {sum(latencies)/len(latencies):.3f}s")

    # -------------------------------------------------------------------------
    # 2. Cache Lifecycle Tests
    # -------------------------------------------------------------------------
    def test_cache_lifecycle_sharing_across_instances(self):
        """Verify model object identity is shared across distinct TranscriptionEngine instances in VRAM."""
        # Ensure fresh start
        TranscriptionEngine.clear_model_cache()
        self.assertIsNone(
            TranscriptionEngine.get_cached_model(
                "deepdml/faster-whisper-large-v3-turbo-ct2", "cuda", "float16"
            )
        )

        engine1 = TranscriptionEngine()
        res1 = engine1.transcribe(self.pcm_data[:32000], 1.0, language="en", model="turbo")
        self.assertIsNotNone(res1)

        cached_model = TranscriptionEngine.get_cached_model(
            "deepdml/faster-whisper-large-v3-turbo-ct2", "cuda", "float16"
        )
        self.assertIsNotNone(cached_model)
        cached_model_id = id(cached_model)

        # Create multiple subsequent TranscriptionEngine instances
        for i in range(5):
            engine_n = TranscriptionEngine()
            # Perform transcription
            res_n = engine_n.transcribe(self.pcm_data[:32000], 1.0, language="en", model="turbo")
            self.assertIsNotNone(res_n)
            # Check model instance identity
            active_cached = TranscriptionEngine.get_cached_model(
                "deepdml/faster-whisper-large-v3-turbo-ct2", "cuda", "float16"
            )
            self.assertEqual(
                id(active_cached),
                cached_model_id,
                f"Instance {i} did not share the cached WhisperModel object (VRAM duplicate detected!)",
            )

    def test_cache_lifecycle_clear_and_clean_reload(self):
        """Verify clear_model_cache completely empties cache, and next invocation performs clean reload."""
        engine = TranscriptionEngine()
        engine.transcribe(self.pcm_data[:32000], 1.0, language="en", model="turbo")
        self.assertGreater(len(TranscriptionEngine._MODEL_CACHE), 0)

        # Clear cache
        TranscriptionEngine.clear_model_cache()
        self.assertEqual(len(TranscriptionEngine._MODEL_CACHE), 0)
        self.assertIsNone(
            TranscriptionEngine.get_cached_model(
                "deepdml/faster-whisper-large-v3-turbo-ct2", "cuda", "float16"
            )
        )

        # Next invocation must cleanly reload
        engine2 = TranscriptionEngine()
        res2 = engine2.transcribe(self.pcm_data[:32000], 1.0, language="en", model="turbo")
        self.assertIsNotNone(res2)
        self.assertGreater(len(TranscriptionEngine._MODEL_CACHE), 0)
        reloaded = TranscriptionEngine.get_cached_model(
            "deepdml/faster-whisper-large-v3-turbo-ct2", "cuda", "float16"
        )
        self.assertIsNotNone(reloaded)

    # -------------------------------------------------------------------------
    # 3. Cloud Isolation Test
    # -------------------------------------------------------------------------
    def test_cloud_isolation_with_hostile_keys_and_network_block(self):
        """Empirically test zero external network calls and refusal of cloud fallbacks.
        
        Injects fake OpenAI/Gemini keys and intercepts all socket connections.
        """
        # Intercept socket.connect to catch any outbound network attempt
        original_connect = socket.socket.connect
        network_calls = []

        def guarded_connect(sock_self, address):
            # Record attempted destination
            network_calls.append(address)
            raise ConnectionRefusedError(f"Cloud tap blocked: attempted outbound connection to {address}")

        hostile_env = {
            "OPENAI_API_KEY": "sk-fake-openai-challenge-key-1234567890",
            "GEMINI_API_KEY": "fake-gemini-adversarial-api-key-9876543210",
            "VOICEMAKER_API_KEY": "fake-voicemaker-key",
            "ELEVENLABS_API_KEY": "fake-elevenlabs-key",
        }

        with mock.patch.dict(os.environ, hostile_env):
            with mock.patch.object(socket.socket, "connect", side_effect=guarded_connect):
                engine = TranscriptionEngine()
                # Verify backend is strictly local
                self.assertNotEqual(engine.active_backend, "cloud-api")
                self.assertFalse(hasattr(engine, "_transcribe_cloud_api"))

                # Perform transcription
                res = engine.transcribe(self.pcm_data, self.meta.duration, language="en", model="turbo")

                self.assertIsNotNone(res)
                self.assertTrue(len(res.text) > 0)
                self.assertNotIn("cloud", res.backend_used.lower())
                self.assertEqual(res.model_name, "whisper-turbo")

        # Verify zero network connections were attempted
        self.assertEqual(
            network_calls,
            [],
            f"Violated cloud isolation: attempted outbound network calls: {network_calls}",
        )
        print(f"\n[Cloud Isolation] 0 network calls attempted. Engine transcribed locally on GPU.")


if __name__ == "__main__":
    unittest.main()
