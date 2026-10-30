"""Empirical stress-testing and adversarial challenge suite for scriber.hardware.

Authored by Challenger 1 for Milestone 1 verification.
Stress-tests:
1. Boundary conditions around the 3500 MB free VRAM speech LLM threshold:
   - 3499.0 MB, 3499.9 MB, 3500.0 MB, 3500.1 MB, 0.0 MB, negative VRAM, high VRAM with cuda_available=False.
2. Boundary conditions around the 4000 MB total VRAM device routing threshold:
   - 3999.0 MB, 3999.9 MB, 4000.0 MB, 4000.1 MB, 0.0 MB, high VRAM with cuda_available=False.
3. Multi-threaded race conditions and thread-safety under heavy concurrent execution:
   - 64 concurrent threads pounding get_hardware_capabilities with mixed force_refresh flags.
4. Direct3D 12 feature levels fallback matrix:
   - FL 12_2, 12_1, 12_0, 11_1, 11_0, full rejection, unexpected HRESULT codes, OSError on load.
5. NVML error code matrix:
   - NVML_ERROR_NO_PERMISSION (4), NVML_ERROR_GPU_IS_LOST (15), NVML_ERROR_NOT_FOUND (6),
   - NVML_ERROR_UNKNOWN (999), mid-probe failure on memory query, mid-probe failure on device handle.
   - Verifies nvmlShutdown lifecycle invariants (called iff initialized).
6. Live hardware detection invariants on host system.
"""

from __future__ import annotations

import concurrent.futures
import ctypes
from ctypes import c_char, c_int, c_uint, c_ulonglong, pointer
import json
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, call, patch

import scriber.hardware as hw
from scriber.hardware import (
    D3D_FEATURE_LEVEL_11_0,
    D3D_FEATURE_LEVEL_11_1,
    D3D_FEATURE_LEVEL_12_0,
    D3D_FEATURE_LEVEL_12_1,
    D3D_FEATURE_LEVEL_12_2,
    _load_nvml_library,
    _nvmlMemory_t,
    _query_ctranslate2_cuda,
    _query_d3d12,
    _query_nvml_gpu,
    format_hardware_summary,
    get_hardware_capabilities,
    get_transcription_device_config,
)
from scriber.models import HardwareCapabilities


class TestBoundaryThresholds(unittest.TestCase):
    """Adversarial testing of strict threshold boundaries for VRAM routing."""

    def tearDown(self):
        # Restore genuine cache after mocked tests
        get_hardware_capabilities(force_refresh=True)

    @patch("scriber.hardware._query_ctranslate2_cuda", return_value=1)
    @patch("scriber.hardware._query_d3d12", return_value=(True, "12_2"))
    @patch("scriber.hardware._query_nvml_gpu")
    def test_speech_llm_free_vram_exact_boundaries(self, mock_nvml, mock_d3d, mock_ct2):
        """Stress-tests the exact 3500.0 MB free VRAM threshold for supports_local_speech_llm."""
        base_gpu = {
            "gpu_name": "NVIDIA GeForce RTX 5050 Laptop GPU",
            "vram_total_mb": 8192.0,
            "vram_free_mb": 3500.0,
            "compute_capability": (12, 0),
            "driver_version": "610.74",
            "cuda_version": "13.3",
        }

        # Sub-test 1: 3499.0 MB -> False
        base_gpu["vram_free_mb"] = 3499.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertFalse(caps.supports_local_speech_llm, "3499.0 MB free VRAM must not support speech LLM")

        # Sub-test 2: 3499.9 MB -> False
        base_gpu["vram_free_mb"] = 3499.9
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertFalse(caps.supports_local_speech_llm, "3499.9 MB free VRAM must not support speech LLM")

        # Sub-test 3: Exactly 3500.0 MB -> True
        base_gpu["vram_free_mb"] = 3500.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertTrue(caps.supports_local_speech_llm, "Exactly 3500.0 MB free VRAM must support speech LLM")

        # Sub-test 4: 3500.1 MB -> True
        base_gpu["vram_free_mb"] = 3500.1
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertTrue(caps.supports_local_speech_llm, "3500.1 MB free VRAM must support speech LLM")

        # Sub-test 5: 0.0 MB -> False
        base_gpu["vram_free_mb"] = 0.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertFalse(caps.supports_local_speech_llm, "0.0 MB free VRAM must not support speech LLM")

        # Sub-test 6: Negative free VRAM -> False
        base_gpu["vram_free_mb"] = -100.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertFalse(caps.supports_local_speech_llm, "Negative free VRAM must not support speech LLM")

    @patch("scriber.hardware._query_ctranslate2_cuda", return_value=0)
    @patch("scriber.hardware._query_d3d12", return_value=(False, ""))
    @patch("scriber.hardware._query_nvml_gpu")
    def test_speech_llm_without_cuda_available(self, mock_nvml, mock_d3d, mock_ct2):
        """Even with massive free VRAM, speech LLM must be False if CUDA is unavailable."""
        mock_nvml.return_value = {
            "gpu_name": "Generic GPU",
            "vram_total_mb": 16384.0,
            "vram_free_mb": 12000.0,
            "compute_capability": (0, 0),  # No compute capability
            "driver_version": "1.0",
            "cuda_version": "",
        }
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertFalse(caps.cuda_available)
        self.assertFalse(caps.supports_local_speech_llm, "Speech LLM must be False if cuda_available is False")

    @patch("scriber.hardware._query_ctranslate2_cuda", return_value=1)
    @patch("scriber.hardware._query_d3d12", return_value=(True, "12_2"))
    @patch("scriber.hardware._query_nvml_gpu")
    def test_total_vram_routing_exact_boundaries(self, mock_nvml, mock_d3d, mock_ct2):
        """Stress-tests the exact 4000.0 MB total VRAM threshold for recommended_device routing."""
        base_gpu = {
            "gpu_name": "NVIDIA GeForce RTX 5050",
            "vram_total_mb": 4000.0,
            "vram_free_mb": 2000.0,
            "compute_capability": (12, 0),
            "driver_version": "610.74",
            "cuda_version": "13.3",
        }

        # Sub-test 1: 3999.0 MB total -> cpu, int8
        base_gpu["vram_total_mb"] = 3999.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertEqual(caps.recommended_device, "cpu")
        self.assertEqual(caps.recommended_compute_type, "int8")

        # Sub-test 2: 3999.9 MB total -> cpu, int8
        base_gpu["vram_total_mb"] = 3999.9
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertEqual(caps.recommended_device, "cpu")
        self.assertEqual(caps.recommended_compute_type, "int8")

        # Sub-test 3: Exactly 4000.0 MB total -> cuda, float16
        base_gpu["vram_total_mb"] = 4000.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertEqual(caps.recommended_device, "cuda")
        self.assertEqual(caps.recommended_compute_type, "float16")

        # Sub-test 4: 4000.1 MB total -> cuda, float16
        base_gpu["vram_total_mb"] = 4000.1
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertEqual(caps.recommended_device, "cuda")
        self.assertEqual(caps.recommended_compute_type, "float16")

        # Sub-test 5: 0.0 MB total -> cpu, int8
        base_gpu["vram_total_mb"] = 0.0
        mock_nvml.return_value = dict(base_gpu)
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertEqual(caps.recommended_device, "cpu")
        self.assertEqual(caps.recommended_compute_type, "int8")

    @patch("scriber.hardware._query_ctranslate2_cuda", return_value=0)
    @patch("scriber.hardware._query_d3d12", return_value=(True, "12_0"))
    @patch("scriber.hardware._query_nvml_gpu")
    def test_total_vram_high_without_cuda(self, mock_nvml, mock_d3d, mock_ct2):
        """Even with 8192 MB VRAM, without CUDA capability, device must route to CPU int8."""
        mock_nvml.return_value = {
            "gpu_name": "AMD Radeon RX 7600",
            "vram_total_mb": 8192.0,
            "vram_free_mb": 7000.0,
            "compute_capability": (0, 0),
            "driver_version": "23.10.1",
            "cuda_version": "",
        }
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertFalse(caps.cuda_available)
        self.assertEqual(caps.recommended_device, "cpu")
        self.assertEqual(caps.recommended_compute_type, "int8")
        self.assertFalse(caps.supports_local_speech_llm)


class TestDirect3D12Fallbacks(unittest.TestCase):
    """Adversarial stress-testing of Direct3D 12 feature levels and failure modes."""

    def test_d3d12_feature_level_hierarchy_12_2(self):
        """Device creation accepts 12_2 -> returns (True, '12_2')."""
        with patch("ctypes.WinDLL") as mock_windll, patch.object(hw, "sys") as mock_sys:
            mock_sys.platform = "win32"
            mock_d3d12 = MagicMock()
            # D3D12CreateDevice returns 0 (S_OK) or 1 (S_FALSE)
            mock_d3d12.D3D12CreateDevice.return_value = 1
            mock_windll.return_value = mock_d3d12

            # Force windll fallback in _query_d3d12
            with patch("ctypes.windll", create=True) as mock_ctypes_windll:
                del mock_ctypes_windll.d3d12
                is_supported, fl = _query_d3d12()
                self.assertTrue(is_supported)
                self.assertEqual(fl, "12_2")

    def test_d3d12_feature_level_downgrade_to_12_0(self):
        """Device creation fails for 12_2 and 12_1, succeeds for 12_0."""
        with patch("ctypes.WinDLL") as mock_windll, patch.object(hw, "sys") as mock_sys:
            mock_sys.platform = "win32"
            mock_d3d12 = MagicMock()

            def mock_create_device(adapter, feature_level, riid, ppDevice):
                if feature_level in (D3D_FEATURE_LEVEL_12_2, D3D_FEATURE_LEVEL_12_1):
                    return -2005270524  # DXGI_ERROR_UNSUPPORTED
                return 0  # S_OK for 12_0 and below

            mock_d3d12.D3D12CreateDevice.side_effect = mock_create_device
            mock_windll.return_value = mock_d3d12

            with patch("ctypes.windll", create=True) as mock_ctypes_windll:
                del mock_ctypes_windll.d3d12
                is_supported, fl = _query_d3d12()
                self.assertTrue(is_supported)
                self.assertEqual(fl, "12_0")

    def test_d3d12_feature_level_below_12_0_fails_d3d12_support(self):
        """Device creation fails for all 12_x, succeeds only for 11_1 -> directx_12_supported is False."""
        with patch("ctypes.WinDLL") as mock_windll, patch.object(hw, "sys") as mock_sys:
            mock_sys.platform = "win32"
            mock_d3d12 = MagicMock()

            def mock_create_device(adapter, feature_level, riid, ppDevice):
                if feature_level in (D3D_FEATURE_LEVEL_12_2, D3D_FEATURE_LEVEL_12_1, D3D_FEATURE_LEVEL_12_0):
                    return -2005270524  # DXGI_ERROR_UNSUPPORTED
                return 1  # S_FALSE for 11_1 and 11_0

            mock_d3d12.D3D12CreateDevice.side_effect = mock_create_device
            mock_windll.return_value = mock_d3d12

            with patch("ctypes.windll", create=True) as mock_ctypes_windll:
                del mock_ctypes_windll.d3d12
                is_supported, fl = _query_d3d12()
                self.assertFalse(is_supported, "DirectX 12 supported must be False if highest FL is 11_1")
                self.assertEqual(fl, "11_1")

    def test_d3d12_complete_rejection_all_feature_levels(self):
        """Device creation fails across all feature levels -> (False, '')."""
        with patch("ctypes.WinDLL") as mock_windll, patch.object(hw, "sys") as mock_sys:
            mock_sys.platform = "win32"
            mock_d3d12 = MagicMock()
            mock_d3d12.D3D12CreateDevice.return_value = -2005270524  # DXGI_ERROR_UNSUPPORTED
            mock_windll.return_value = mock_d3d12

            with patch("ctypes.windll", create=True) as mock_ctypes_windll:
                del mock_ctypes_windll.d3d12
                is_supported, fl = _query_d3d12()
                self.assertFalse(is_supported)
                self.assertEqual(fl, "")

    def test_d3d12_dll_load_failure(self):
        """Simulate d3d12.dll missing or failing to load (OSError)."""
        with patch("ctypes.WinDLL", side_effect=OSError("d3d12.dll not found")), patch.object(hw, "sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch("ctypes.windll", create=True) as mock_ctypes_windll:
                del mock_ctypes_windll.d3d12
                is_supported, fl = _query_d3d12()
                self.assertFalse(is_supported)
                self.assertEqual(fl, "")


class TestNVMLErrorHandling(unittest.TestCase):
    """Stress-testing NVML error codes and device inspection failure modes."""

    def test_nvml_init_error_no_permission(self):
        """NVML init returns NVML_ERROR_NO_PERMISSION (4) -> returns None, shutdown not called."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 4  # NVML_ERROR_NO_PERMISSION
        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNone(result)
            # nvmlShutdown must NOT be called if nvmlInit failed
            mock_lib.nvmlShutdown.assert_not_called()

    def test_nvml_init_error_gpu_is_lost(self):
        """NVML init returns NVML_ERROR_GPU_IS_LOST (15) -> returns None, shutdown not called."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 15  # NVML_ERROR_GPU_IS_LOST
        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNone(result)
            mock_lib.nvmlShutdown.assert_not_called()

    def test_nvml_device_get_count_error(self):
        """NVML init succeeds but get_count returns error code 6 (NVML_ERROR_NOT_FOUND) -> calls shutdown."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 0  # Success
        mock_lib.nvmlDeviceGetCount_v2.return_value = 6  # NVML_ERROR_NOT_FOUND
        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNone(result)
            mock_lib.nvmlShutdown.assert_called_once()

    def test_nvml_device_count_zero(self):
        """NVML reports 0 devices -> returns None and cleanly shuts down."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 0

        def mock_get_count(p_count):
            p_count._obj.value = 0
            return 0

        mock_lib.nvmlDeviceGetCount_v2.side_effect = mock_get_count
        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNone(result)
            mock_lib.nvmlShutdown.assert_called_once()

    def test_nvml_device_handle_error_on_first_gpu_success_on_second(self):
        """GPU 0 fails with NVML_ERROR_GPU_IS_LOST (15), GPU 1 succeeds with 8GB VRAM."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 0

        def mock_get_count(p_count):
            p_count._obj.value = 2
            return 0
        mock_lib.nvmlDeviceGetCount_v2.side_effect = mock_get_count

        def mock_get_handle(idx, p_handle):
            if idx == 0:
                return 15  # NVML_ERROR_GPU_IS_LOST
            p_handle._obj.value = 0x12345
            return 0
        mock_lib.nvmlDeviceGetHandleByIndex_v2.side_effect = mock_get_handle

        def mock_get_name(handle, buf, size):
            buf.value = b"NVIDIA GeForce RTX 5050"
            return 0
        mock_lib.nvmlDeviceGetName.side_effect = mock_get_name

        def mock_get_mem(handle, p_mem):
            p_mem._obj.total = 8192 * 1024 * 1024
            p_mem._obj.free = 5000 * 1024 * 1024
            p_mem._obj.used = 3192 * 1024 * 1024
            return 0
        mock_lib.nvmlDeviceGetMemoryInfo.side_effect = mock_get_mem

        def mock_get_cc(handle, p_maj, p_min):
            p_maj._obj.value = 12
            p_min._obj.value = 0
            return 0
        mock_lib.nvmlDeviceGetCudaComputeCapability.side_effect = mock_get_cc

        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNotNone(result)
            self.assertEqual(result["gpu_name"], "NVIDIA GeForce RTX 5050")
            self.assertEqual(result["vram_total_mb"], 8192.0)
            mock_lib.nvmlShutdown.assert_called_once()

    def test_nvml_memory_query_error_returns_zero_vram(self):
        """When nvmlDeviceGetMemoryInfo fails, vram defaults to 0.0 without crash."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 0

        def mock_get_count(p_count):
            p_count._obj.value = 1
            return 0
        mock_lib.nvmlDeviceGetCount_v2.side_effect = mock_get_count
        mock_lib.nvmlDeviceGetHandleByIndex_v2.return_value = 0
        mock_lib.nvmlDeviceGetName.return_value = 0
        # Return error on memory query
        mock_lib.nvmlDeviceGetMemoryInfo.return_value = 999  # NVML_ERROR_UNKNOWN

        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNotNone(result)
            self.assertEqual(result["vram_total_mb"], 0.0)
            self.assertEqual(result["vram_free_mb"], 0.0)
            mock_lib.nvmlShutdown.assert_called_once()

    def test_nvml_shutdown_exception_is_handled(self):
        """Even if nvmlShutdown raises an exception, _query_nvml_gpu handles it gracefully."""
        mock_lib = MagicMock()
        mock_lib.nvmlInit_v2.return_value = 0
        mock_lib.nvmlShutdown.side_effect = RuntimeError("Driver crash during shutdown")
        mock_lib.nvmlDeviceGetCount_v2.return_value = 0  # Trigger shutdown

        with patch("scriber.hardware._load_nvml_library", return_value=mock_lib):
            result = _query_nvml_gpu()
            self.assertIsNone(result)


class TestConcurrencyStress(unittest.TestCase):
    """Stress-testing thread-safety, locking, and concurrency under load."""

    def tearDown(self):
        get_hardware_capabilities(force_refresh=True)

    def test_concurrent_multithreaded_queries(self):
        """Spawns 64 concurrent threads reading get_hardware_capabilities with mixed force_refresh.
        
        Verifies:
        - No race conditions or deadlocks.
        - Every thread returns a valid HardwareCapabilities dataclass.
        - Every dataclass serialized via to_dict has complete schema and valid types.
        """
        num_threads = 64
        results: list[HardwareCapabilities] = [None] * num_threads
        exceptions: list[Exception] = []

        def worker(thread_idx: int):
            try:
                # Half threads do force_refresh=True, half do force_refresh=False
                refresh = (thread_idx % 2 == 0)
                caps = get_hardware_capabilities(force_refresh=refresh)
                d = caps.to_dict()
                # Verify required dictionary keys and value types
                assert isinstance(d["recommended_device"], str)
                assert isinstance(d["supports_local_speech_llm"], bool)
                assert isinstance(d["vram_total_mb"], (float, int))
                results[thread_idx] = caps
            except Exception as e:
                exceptions.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
            self.assertFalse(t.is_alive(), f"Thread timed out / deadlocked")

        self.assertEqual(len(exceptions), 0, f"Exceptions occurred during concurrency: {exceptions}")
        self.assertEqual(len(results), num_threads)
        for i, res in enumerate(results):
            self.assertIsInstance(res, HardwareCapabilities, f"Thread {i} did not return HardwareCapabilities")
            self.assertIn(res.recommended_device, ("cuda", "cpu"))

    def test_simultaneous_cached_reads_return_same_instance(self):
        """When force_refresh=False, concurrent threads must all receive the exact same singleton instance."""
        # Prime cache
        primary = get_hardware_capabilities(force_refresh=True)

        instances = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [executor.submit(get_hardware_capabilities, False) for _ in range(32)]
            for f in concurrent.futures.as_completed(futures):
                instances.append(f.result())

        for inst in instances:
            self.assertIs(inst, primary, "All concurrent cached reads must return the exact same instance")


class TestLiveHardwareInvariants(unittest.TestCase):
    """Verifies live invariants on the actual host machine."""

    def test_live_rtx_5050_invariants(self):
        """Host environment must report NVIDIA GPU with >= 8GB total VRAM and Direct3D 12.2."""
        caps = get_hardware_capabilities(force_refresh=True)
        if sys.platform == "win32" and caps.gpu_name:
            self.assertIn("RTX 5050", caps.gpu_name)
            self.assertGreaterEqual(caps.vram_total_mb, 8000.0)
            self.assertGreaterEqual(caps.vram_free_mb, 4000.0)
            self.assertEqual(caps.compute_capability, (12, 0))
            self.assertTrue(caps.cuda_available)
            self.assertTrue(caps.directx_12_supported)
            self.assertEqual(caps.directx_feature_level, "12_2")
            self.assertEqual(caps.recommended_device, "cuda")
            self.assertEqual(caps.recommended_compute_type, "float16")
            self.assertTrue(caps.supports_local_speech_llm)

    def test_transcription_device_config_consistency(self):
        """get_transcription_device_config must match caps.recommended_device and compute_type."""
        caps = get_hardware_capabilities()
        device, compute_type = get_transcription_device_config()
        self.assertEqual(device, caps.recommended_device)
        self.assertEqual(compute_type, caps.recommended_compute_type)

    def test_format_hardware_summary_structure(self):
        """format_hardware_summary must output a clean, parsable multiline ASCII table."""
        summary = format_hardware_summary()
        self.assertTrue(summary.startswith("=== Scriber Hardware & GPU Acceleration Capability ==="))
        self.assertTrue(summary.endswith("======================================================="))
        lines = summary.strip().split("\n")
        self.assertGreaterEqual(len(lines), 11)


if __name__ == "__main__":
    unittest.main()
