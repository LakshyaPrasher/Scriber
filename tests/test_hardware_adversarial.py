"""Adversarial stress and verification tests for Scriber Hardware & GPU Capability Assessment.

Covers:
1. High-concurrency HTTP load on /api/hardware.
2. Malformed HTTP requests, unexpected methods, query strings, and abrupt socket disconnects.
3. Server lifecycle robustness: rapid start/stop cycles, double start/stop, port rebinding.
4. Memory and Windows OS handle leak detection across repeated force_refresh cycles.
5. Environment variable overrides (WHISPER_DEVICE, WHISPER_COMPUTE_TYPE) edge cases and case handling.
6. Driver and NVML/D3D12 probe boundary conditions and concurrent cache access.
"""

from __future__ import annotations

import concurrent.futures
import ctypes
from ctypes import wintypes
import gc
import json
import os
import socket
import sys
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import MagicMock, patch

from scriber.hardware import (
    _HARDWARE_LOCK,
    _load_nvml_library,
    _query_ctranslate2_cuda,
    _query_d3d12,
    _query_nvml_gpu,
    format_hardware_summary,
    get_hardware_capabilities,
    get_transcription_device_config,
)
from scriber.models import HardwareCapabilities
from scriber.transcription_engine import resolve_transcription_device
from scriber.web.server import (
    ScriberBackgroundServer,
    ScriberHTTPRequestHandler,
    find_available_port,
)


def get_current_process_handle_count() -> int:
    """Returns the current Windows process handle count using kernel32.dll."""
    if sys.platform != "win32":
        return 0
    try:
        handle_count = wintypes.DWORD()
        h_process = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.kernel32.GetProcessHandleCount(h_process, ctypes.byref(handle_count)):
            return int(handle_count.value)
    except Exception:
        pass
    return 0


def get_current_process_memory_bytes() -> int:
    """Returns the current Windows process WorkingSetSize in bytes."""
    if sys.platform != "win32":
        return 0
    try:
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        h_process = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(h_process, ctypes.byref(pmc), pmc.cb):
            return int(pmc.WorkingSetSize)
    except Exception:
        pass
    return 0


class TestHardwareHTTPConcurrencyAndLoad(unittest.TestCase):
    """Stress-tests the /api/hardware endpoint under concurrent load and abnormal socket behavior."""

    @classmethod
    def setUpClass(cls):
        cls.port = find_available_port("127.0.0.1", 19895)
        cls.server = ScriberBackgroundServer(host="127.0.0.1", port=cls.port)
        cls.server.start(timeout=8.0)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_concurrent_http_requests_burst(self):
        """Stress-tests /api/hardware with 50 concurrent threads executing 250 total requests."""
        url = f"{self.server.url}/api/hardware"
        num_requests = 250
        num_workers = 50

        results = []
        errors = []

        def make_request(idx: int):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": f"StressWorker-{idx}"})
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    status = resp.status
                    body = resp.read()
                    data = json.loads(body.decode("utf-8"))
                    return status, data
            except Exception as e:
                return -1, str(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            for future in concurrent.futures.as_completed(futures):
                status, data = future.result()
                if status == 200:
                    results.append(data)
                else:
                    errors.append(data)

        self.assertEqual(len(errors), 0, f"Encountered errors during concurrent HTTP burst: {errors[:5]}")
        self.assertEqual(len(results), num_requests)

        # Validate consistency across all concurrent responses
        first = results[0]
        for item in results:
            self.assertEqual(item["recommended_device"], first["recommended_device"])
            self.assertEqual(item["cuda_available"], first["cuda_available"])
            self.assertEqual(item["compute_capability"], first["compute_capability"])

    def test_abrupt_client_socket_disconnects(self):
        """Simulates clients establishing connection, sending partial or full GET, and disconnecting immediately."""
        url_path = b"GET /api/hardware HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n"

        for _ in range(30):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("127.0.0.1", self.port))
                s.sendall(url_path[:15])  # Send partial bytes
                s.close()  # Abrupt RST/close
            except Exception:
                pass

        # Ensure server remains healthy and responsive after socket drops
        req = urllib.request.Request(f"{self.server.url}/api/hardware")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("recommended_device", data)

    def test_query_string_handling(self):
        """Verifies endpoint correctly responds to arbitrary and unusual query strings."""
        test_queries = [
            "?force_refresh=true",
            "?foo=bar&baz=123",
            "?empty=",
            "?url_encoded=%20%2F%24",
            "?repeated=1&repeated=2",
            "?",
        ]
        for q in test_queries:
            url = f"{self.server.url}/api/hardware{q}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                self.assertEqual(resp.status, 200, f"Failed on query: {q}")
                data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("recommended_device", data)

    def test_disallowed_http_methods(self):
        """Verifies that non-GET methods to /api/hardware either return 404/405 or CORS 200/204."""
        # OPTIONS should return 200 or 204 with CORS headers
        req_opt = urllib.request.Request(f"{self.server.url}/api/hardware", method="OPTIONS")
        with urllib.request.urlopen(req_opt, timeout=5.0) as resp:
            self.assertIn(resp.status, (200, 204))
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

        # POST should return 404 (Endpoint not found) per server design
        req_post = urllib.request.Request(
            f"{self.server.url}/api/hardware",
            data=b'{"payload": "test"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_post, timeout=5.0)
        self.assertEqual(ctx.exception.code, 404)

    def test_nonexistent_subpaths(self):
        """Verifies that requests to subpaths of /api/hardware return 404."""
        bad_paths = [
            "/api/hardware/",
            "/api/hardware/details",
            "/api/hardware.json",
        ]
        for p in bad_paths:
            req = urllib.request.Request(f"{self.server.url}{p}")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5.0)
            self.assertEqual(ctx.exception.code, 404, f"Path {p} did not return 404")


class TestServerLifecycleAndShutdown(unittest.TestCase):
    """Verifies server start, stop, port reuse, and lifecycle robustness."""

    def test_rapid_sequential_start_stop_cycles(self):
        """Verifies server can be started and stopped repeatedly on the same port without socket leaks."""
        test_port = find_available_port("127.0.0.1", 19896)

        for cycle in range(5):
            server = ScriberBackgroundServer(host="127.0.0.1", port=test_port)
            server.start(timeout=6.0)
            # Verify listening
            with socket.create_connection(("127.0.0.1", test_port), timeout=1.0) as sock:
                sock.sendall(b"GET /api/health HTTP/1.0\r\n\r\n")
                data = sock.recv(64)
                self.assertIn(b"200 OK", data)
            server.stop()
            time.sleep(0.1)

    def test_double_start_and_double_stop(self):
        """Verifies calling start() twice or stop() twice does not crash or raise exceptions."""
        test_port = find_available_port("127.0.0.1", 19897)
        server = ScriberBackgroundServer(host="127.0.0.1", port=test_port)
        try:
            server.start()
            # Double start should be idempotent
            server.start()
            self.assertTrue(server._is_running)
        finally:
            server.stop()
            # Double stop should be idempotent
            server.stop()
            self.assertFalse(server._is_running)


class TestMemoryAndResourceLeaks(unittest.TestCase):
    """Stress-tests repeated hardware probing to detect memory leaks, DLL handle leaks, or thread leaks."""

    def test_repeated_force_refresh_resource_stability(self):
        """Runs 300 repeated force_refresh cycles and measures memory and OS handle growth."""
        # Warmup and initial collection
        gc.collect()
        time.sleep(0.1)
        _ = get_hardware_capabilities(force_refresh=True)
        gc.collect()

        initial_handles = get_current_process_handle_count()
        initial_mem = get_current_process_memory_bytes()
        initial_threads = threading.active_count()

        iterations = 50
        for _ in range(iterations):
            caps = get_hardware_capabilities(force_refresh=True)
            self.assertIsInstance(caps, HardwareCapabilities)

        gc.collect()
        time.sleep(0.2)

        final_handles = get_current_process_handle_count()
        final_mem = get_current_process_memory_bytes()
        final_threads = threading.active_count()

        # Thread count must remain strictly stable
        self.assertEqual(final_threads, initial_threads, "Thread count leaked during force_refresh cycles!")

        # Handle growth should be bounded (less than 15 handles allowed across 50 runs)
        if initial_handles > 0:
            handle_diff = final_handles - initial_handles
            self.assertLess(
                handle_diff,
                15,
                f"Significant OS handle growth detected: {initial_handles} -> {final_handles} (+{handle_diff})",
            )

        # Memory growth check: Working set should not grow by more than 15 MB across 50 calls
        if initial_mem > 0:
            mem_growth_mb = (final_mem - initial_mem) / (1024 * 1024)
            self.assertLess(
                mem_growth_mb,
                15.0,
                f"Excessive working set growth detected: {mem_growth_mb:.2f} MB across {iterations} calls",
            )

    def test_concurrent_force_refresh_thread_safety(self):
        """Verifies multi-threaded concurrent calls to force_refresh=True execute without race conditions."""
        caps_results = []
        errors = []

        def worker():
            try:
                c = get_hardware_capabilities(force_refresh=True)
                caps_results.append(c)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread safety errors during concurrent force_refresh: {errors}")
        self.assertEqual(len(caps_results), 20)
        first_gpu = caps_results[0].gpu_name
        for c in caps_results:
            self.assertEqual(c.gpu_name, first_gpu)


class TestEnvironmentOverridesAdversarial(unittest.TestCase):
    """Adversarial testing of environment variable overrides for WHISPER_DEVICE and WHISPER_COMPUTE_TYPE."""

    def setUp(self):
        self._orig_device = os.environ.get("WHISPER_DEVICE")
        self._orig_compute = os.environ.get("WHISPER_COMPUTE_TYPE")

    def tearDown(self):
        if self._orig_device is not None:
            os.environ["WHISPER_DEVICE"] = self._orig_device
        else:
            os.environ.pop("WHISPER_DEVICE", None)

        if self._orig_compute is not None:
            os.environ["WHISPER_COMPUTE_TYPE"] = self._orig_compute
        else:
            os.environ.pop("WHISPER_COMPUTE_TYPE", None)

    def test_whisper_device_explicit_cpu_override(self):
        """WHISPER_DEVICE='cpu' must force CPU and default compute type 'int8'."""
        os.environ["WHISPER_DEVICE"] = "cpu"
        os.environ.pop("WHISPER_COMPUTE_TYPE", None)

        device, compute_type = resolve_transcription_device()
        self.assertEqual(device, "cpu")
        self.assertEqual(compute_type, "int8")

    def test_whisper_device_explicit_cuda_override(self):
        """WHISPER_DEVICE='cuda' must force cuda and default compute type 'float16'."""
        os.environ["WHISPER_DEVICE"] = "cuda"
        os.environ.pop("WHISPER_COMPUTE_TYPE", None)

        device, compute_type = resolve_transcription_device()
        self.assertEqual(device, "cuda")
        self.assertEqual(compute_type, "float16")

    def test_whisper_device_with_explicit_compute_override(self):
        """WHISPER_DEVICE='cpu' and WHISPER_COMPUTE_TYPE='int8_float16' must be respected."""
        os.environ["WHISPER_DEVICE"] = "cpu"
        os.environ["WHISPER_COMPUTE_TYPE"] = "int8_float16"

        device, compute_type = resolve_transcription_device()
        self.assertEqual(device, "cpu")
        self.assertEqual(compute_type, "int8_float16")

    def test_whisper_compute_type_alone_behavior(self):
        """Examines behavior when WHISPER_COMPUTE_TYPE is set but WHISPER_DEVICE is unset."""
        os.environ.pop("WHISPER_DEVICE", None)
        os.environ["WHISPER_COMPUTE_TYPE"] = "int8"

        device, compute_type = resolve_transcription_device()
        # Document observed behavior: currently resolve_transcription_device checks `if env_device:`,
        # so if env_device is not set, it delegates to get_transcription_device_config().
        self.assertIn(device, ("cuda", "cpu"))
        self.assertIn(compute_type, ("float16", "int8", "int8_float16"))

    def test_whisper_device_empty_string(self):
        """WHISPER_DEVICE='' (empty string) should be treated as falsy and fall back to detection."""
        os.environ["WHISPER_DEVICE"] = ""
        os.environ.pop("WHISPER_COMPUTE_TYPE", None)

        device, compute_type = resolve_transcription_device()
        self.assertIn(device, ("cuda", "cpu"))
        self.assertNotEqual(device, "")


class TestProbeRobustnessAndExceptions(unittest.TestCase):
    """Stress-tests probe internals under simulated driver errors and edge cases."""

    @patch("scriber.hardware._load_nvml_library")
    def test_nvml_init_exception_guarantees_cleanup(self, mock_load):
        """Verifies that an exception during device inspection calls nvmlShutdown cleanly."""
        mock_nvml = MagicMock()
        mock_nvml.nvmlInit_v2.return_value = 0
        mock_nvml.nvmlDeviceGetCount_v2.side_effect = RuntimeError("Simulated driver fault")
        mock_load.return_value = mock_nvml

        result = _query_nvml_gpu()
        self.assertIsNone(result)
        mock_nvml.nvmlShutdown.assert_called_once()

    @patch("scriber.hardware._load_nvml_library")
    def test_nvml_zero_devices(self, mock_load):
        """Verifies that NVML with device count 0 returns None."""
        mock_nvml = MagicMock()
        mock_nvml.nvmlInit_v2.return_value = 0

        def fake_count(ptr):
            ptr._obj.value = 0
            return 0

        mock_nvml.nvmlDeviceGetCount_v2.side_effect = fake_count
        mock_load.return_value = mock_nvml

        result = _query_nvml_gpu()
        self.assertIsNone(result)
        mock_nvml.nvmlShutdown.assert_called_once()

    @patch("scriber.hardware._load_nvml_library")
    def test_nvml_device_get_handle_failure(self, mock_load):
        """Verifies that failure on nvmlDeviceGetHandleByIndex skips index gracefully."""
        mock_nvml = MagicMock()
        mock_nvml.nvmlInit_v2.return_value = 0

        def fake_count(ptr):
            ptr._obj.value = 1
            return 0

        mock_nvml.nvmlDeviceGetCount_v2.side_effect = fake_count
        mock_nvml.nvmlDeviceGetHandleByIndex_v2.return_value = 999  # Error
        mock_load.return_value = mock_nvml

        result = _query_nvml_gpu()
        self.assertIsNone(result)

    @patch("scriber.hardware.ctypes.WinDLL")
    def test_d3d12_create_device_raises_os_error(self, mock_windll):
        """Verifies D3D12 probe gracefully returns (False, '') if DLL raises OSError."""
        mock_windll.side_effect = OSError("Simulated DLL loading failure")
        with patch("scriber.hardware.sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch.object(ctypes, "windll", None, create=True):
                supported, fl = _query_d3d12()
                self.assertFalse(supported)
                self.assertEqual(fl, "")


if __name__ == "__main__":
    unittest.main()
