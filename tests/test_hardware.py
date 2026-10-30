"""Unit and integration tests for Scriber Hardware & GPU Capability Assessment.

Covers:
- In-process NVML GPU probing (name, total/free VRAM, CUDA compute capability).
- Direct3D 12 feature level detection via d3d12.dll across 12_0, 12_1, and 12_2.
- CTranslate2 CUDA accelerator availability detection.
- Dynamic device & compute type routing ("cuda"/"float16" vs "cpu"/"int8").
- Local speech LLM / companion microservice threshold gating (>= 3500 MB free VRAM).
- Graceful fallbacks for CPU-only, low-VRAM, missing NVML, and non-Windows environments.
- REST API endpoint GET /api/hardware.
"""

from __future__ import annotations

import io
import json
import socket
import socketserver
import sys
import threading
import time
import unittest
import urllib.request
from unittest.mock import MagicMock, patch

from scriber.hardware import (
    _load_nvml_library,
    _query_ctranslate2_cuda,
    _query_d3d12,
    _query_nvml_gpu,
    format_hardware_summary,
    get_hardware_capabilities,
    get_transcription_device_config,
)
from scriber.models import HardwareCapabilities
from scriber.web.server import ScriberHTTPRequestHandler


class TestHardwareLive(unittest.TestCase):
    """Verifies live hardware detection on the host system."""

    def test_live_hardware_capabilities(self):
        """Verifies real host GPU detection (NVIDIA RTX 5050 Laptop GPU, VRAM, DirectX 12.2)."""
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertIsInstance(caps, HardwareCapabilities)

        # On the host Windows machine with NVIDIA RTX 5050
        if sys.platform == "win32" and caps.gpu_name:
            self.assertIn("NVIDIA", caps.gpu_name)
            self.assertGreater(caps.vram_total_mb, 4000.0)
            self.assertGreater(caps.vram_free_mb, 0.0)
            self.assertEqual(caps.compute_capability, (12, 0))
            self.assertTrue(caps.cuda_available)
            self.assertTrue(caps.directx_12_supported)
            self.assertEqual(caps.directx_feature_level, "12_2")
            self.assertEqual(caps.recommended_device, "cuda")
            self.assertEqual(caps.recommended_compute_type, "float16")
            self.assertTrue(caps.supports_local_speech_llm)

    def test_live_transcription_device_config(self):
        """Verifies get_transcription_device_config returns valid accelerator tuple."""
        device, compute_type = get_transcription_device_config()
        self.assertIn(device, ("cuda", "cpu"))
        self.assertIn(compute_type, ("float16", "int8", "int8_float16"))
        if device == "cuda":
            self.assertEqual(compute_type, "float16")

    def test_format_hardware_summary(self):
        """Verifies format_hardware_summary generates a well-structured report."""
        summary = format_hardware_summary()
        self.assertIn("Scriber Hardware & GPU Acceleration Capability", summary)
        self.assertIn("GPU Name:", summary)
        self.assertIn("Total VRAM:", summary)
        self.assertIn("Recommended Device:", summary)

    def test_hardware_dataclass_serialization(self):
        """Verifies to_dict produces valid, JSON-serializable output with all required keys."""
        caps = get_hardware_capabilities()
        d = caps.to_dict()

        expected_keys = {
            "gpu_name",
            "vram_total_mb",
            "vram_free_mb",
            "compute_capability",
            "cuda_available",
            "cuda_version",
            "directx_12_supported",
            "directx_feature_level",
            "recommended_device",
            "recommended_compute_type",
            "supports_local_speech_llm",
        }
        self.assertTrue(expected_keys.issubset(d.keys()))

        # Check JSON round-trip
        serialized = json.dumps(d)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["recommended_device"], caps.recommended_device)
        self.assertEqual(deserialized["compute_capability"], list(caps.compute_capability))


class TestHardwareSimulated(unittest.TestCase):
    """Verifies simulated environments, fallbacks, and boundary conditions."""

    @patch("scriber.hardware._query_nvml_gpu")
    @patch("scriber.hardware._query_ctranslate2_cuda")
    @patch("scriber.hardware._query_d3d12")
    def test_cpu_only_fallback(self, mock_d3d12, mock_ct2, mock_nvml):
        """Verifies clean fallback to CPU / int8 when no GPU or CUDA is present."""
        mock_nvml.return_value = None
        mock_ct2.return_value = 0
        mock_d3d12.return_value = (False, "")

        caps = get_hardware_capabilities(force_refresh=True)

        self.assertIsNone(caps.gpu_name)
        self.assertEqual(caps.vram_total_mb, 0.0)
        self.assertEqual(caps.vram_free_mb, 0.0)
        self.assertEqual(caps.compute_capability, (0, 0))
        self.assertFalse(caps.cuda_available)
        self.assertFalse(caps.directx_12_supported)
        self.assertEqual(caps.directx_feature_level, "")
        self.assertEqual(caps.recommended_device, "cpu")
        self.assertEqual(caps.recommended_compute_type, "int8")
        self.assertFalse(caps.supports_local_speech_llm)

        device, compute_type = get_transcription_device_config()
        self.assertEqual(device, "cpu")
        self.assertEqual(compute_type, "int8")

    @patch("scriber.hardware._query_nvml_gpu")
    @patch("scriber.hardware._query_ctranslate2_cuda")
    @patch("scriber.hardware._query_d3d12")
    def test_low_vram_routing(self, mock_d3d12, mock_ct2, mock_nvml):
        """Verifies that an NVIDIA GPU with < 4GB VRAM routes to CPU / int8."""
        mock_nvml.return_value = {
            "gpu_name": "NVIDIA GeForce GTX 1050",
            "vram_total_mb": 2048.0,
            "vram_free_mb": 1200.0,
            "compute_capability": (6, 1),
            "driver_version": "512.15",
            "cuda_version": "11.6",
        }
        mock_ct2.return_value = 1
        mock_d3d12.return_value = (True, "12_0")

        caps = get_hardware_capabilities(force_refresh=True)

        self.assertEqual(caps.gpu_name, "NVIDIA GeForce GTX 1050")
        self.assertTrue(caps.cuda_available)
        # Total VRAM 2048 MB < 4000 MB -> CPU route
        self.assertEqual(caps.recommended_device, "cpu")
        self.assertEqual(caps.recommended_compute_type, "int8")
        self.assertFalse(caps.supports_local_speech_llm)

    @patch("scriber.hardware._query_nvml_gpu")
    @patch("scriber.hardware._query_ctranslate2_cuda")
    @patch("scriber.hardware._query_d3d12")
    def test_speech_llm_vram_threshold_boundary(self, mock_d3d12, mock_ct2, mock_nvml):
        """Verifies local speech LLM gating at the 3500 MB free VRAM threshold."""
        mock_ct2.return_value = 1
        mock_d3d12.return_value = (True, "12_1")

        # Case 1: 3499.0 MB free VRAM -> False
        mock_nvml.return_value = {
            "gpu_name": "NVIDIA GeForce RTX 4060",
            "vram_total_mb": 8192.0,
            "vram_free_mb": 3499.0,
            "compute_capability": (8, 9),
            "driver_version": "550.00",
            "cuda_version": "12.4",
        }
        caps1 = get_hardware_capabilities(force_refresh=True)
        self.assertEqual(caps1.recommended_device, "cuda")
        self.assertEqual(caps1.recommended_compute_type, "float16")
        self.assertFalse(caps1.supports_local_speech_llm)

        # Case 2: 3500.0 MB free VRAM -> True
        mock_nvml.return_value["vram_free_mb"] = 3500.0
        caps2 = get_hardware_capabilities(force_refresh=True)
        self.assertTrue(caps2.supports_local_speech_llm)

        # Case 3: 6000.0 MB free VRAM -> True
        mock_nvml.return_value["vram_free_mb"] = 6000.0
        caps3 = get_hardware_capabilities(force_refresh=True)
        self.assertTrue(caps3.supports_local_speech_llm)

    @patch("scriber.hardware.sys")
    def test_d3d12_non_windows_platform(self, mock_sys):
        """Verifies Direct3D 12 probe cleanly returns (False, '') on non-Windows OS."""
        mock_sys.platform = "linux"
        supported, fl = _query_d3d12()
        self.assertFalse(supported)
        self.assertEqual(fl, "")

    @patch("scriber.hardware._load_nvml_library")
    def test_nvml_library_missing(self, mock_load):
        """Verifies _query_nvml_gpu gracefully returns None when NVML DLL is missing."""
        mock_load.return_value = None
        result = _query_nvml_gpu()
        self.assertIsNone(result)

    @patch("scriber.hardware._load_nvml_library")
    def test_nvml_init_nonzero_return(self, mock_load):
        """Verifies _query_nvml_gpu returns None when nvmlInit returns an error code."""
        mock_nvml = MagicMock()
        mock_nvml.nvmlInit_v2.return_value = 999  # Error code
        mock_load.return_value = mock_nvml

        result = _query_nvml_gpu()
        self.assertIsNone(result)

    def test_clean_up_after_tests(self):
        """Ensures cache is refreshed to genuine live hardware state after mocks."""
        caps = get_hardware_capabilities(force_refresh=True)
        self.assertIsInstance(caps, HardwareCapabilities)


class TestHardwareEndpoint(unittest.TestCase):
    """Verifies the /api/hardware REST API endpoint on ScriberHTTPRequestHandler."""

    def setUp(self):
        self.handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        self.handler.wfile = io.BytesIO()
        self.handler.rfile = io.BytesIO()
        self.handler.headers = {}
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def test_get_hardware_endpoint_in_memory(self):
        """Verifies GET /api/hardware returns 200 with full hardware JSON."""
        self.handler.path = "/api/hardware"
        self.handler.do_GET()

        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))

        self.assertIn("recommended_device", written)
        self.assertIn("recommended_compute_type", written)
        self.assertIn("cuda_available", written)
        self.assertIn("directx_12_supported", written)
        self.assertIn("supports_local_speech_llm", written)
        self.assertIn("vram_total_mb", written)
        self.assertIn("vram_free_mb", written)

    def test_get_hardware_endpoint_live_socket(self):
        """Verifies live HTTP request to /api/hardware over loopback socket."""
        # Find a free ephemeral port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        class _EphemeralServer(socketserver.TCPServer):
            allow_reuse_address = True

        server = _EphemeralServer(("127.0.0.1", port), ScriberHTTPRequestHandler)
        srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
        srv_thread.start()
        time.sleep(0.3)

        try:
            req_url = f"http://127.0.0.1:{port}/api/hardware"
            with urllib.request.urlopen(req_url, timeout=5) as response:
                self.assertEqual(response.status, 200)
                body = response.read().decode("utf-8")
                data = json.loads(body)
                self.assertIn("recommended_device", data)
                self.assertIn(data["recommended_device"], ("cuda", "cpu"))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
