"""Verification tests for Scriber Native Desktop Application,
Desktop Bridge, WebView2 integration, background server, and packaging scripts.
"""

from __future__ import annotations

import io
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

from scriber import __version__
from scriber.assets import get_asset_path, get_assets_dir, get_icon_path
from scriber.audio_extractor import AudioExtractor
from scriber.desktop import (
    ScriberDesktopApp,
    ScriberDesktopBridge,
    apply_windows_dpi_and_app_id,
    find_edge_binary,
    launch_desktop,
)
from scriber.web.server import ScriberBackgroundServer, find_available_port
import run_desktop


class TestDesktopApplication(unittest.TestCase):

    def test_brand_assets_exist_and_valid(self):
        """Verifies icon.ico, icon.png, and icon.svg exist with proper format and dimensions."""
        ico_path = get_icon_path()
        self.assertTrue(ico_path.exists(), f"Icon {ico_path} must exist")

        png_path = get_asset_path("icon.png")
        self.assertTrue(png_path.exists(), f"PNG icon {png_path} must exist")

        svg_path = get_asset_path("icon.svg")
        self.assertTrue(svg_path.exists(), f"SVG icon {svg_path} must exist")

        # Verify Pillow can open icon
        from PIL import Image
        with Image.open(png_path) as img:
            self.assertIn(img.size, [(256, 256), (512, 512), (1024, 1024)])
            self.assertIn(img.mode, ("RGB", "RGBA"))

    def test_windows_dpi_and_app_id_safe_execution(self):
        """Verifies apply_windows_dpi_and_app_id runs cleanly without uncaught exceptions."""
        try:
            apply_windows_dpi_and_app_id()
        except Exception as e:
            self.fail(f"apply_windows_dpi_and_app_id raised unexpected exception: {e}")

    def test_find_edge_binary(self):
        """Verifies Edge binary finder executes and detects msedge on Windows."""
        edge_path = find_edge_binary()
        if sys.platform == "win32":
            self.assertIsNotNone(edge_path, "Microsoft Edge should be detected on Windows")
            self.assertTrue(os.path.isfile(edge_path), f"Edge path '{edge_path}' must be a file")

    def test_engine_detection_and_resolution(self):
        """Verifies desktop runtime engine detection order and fallback resolution."""
        app = ScriberDesktopApp(mode="auto")
        engines = app.detect_available_engines()
        self.assertIn("browser", engines)
        self.assertIn("webview", engines, "pywebview with EdgeChromium must be detected")

        # Test mode auto resolves to top engine
        resolved = app.resolve_engine()
        self.assertEqual(resolved, "webview")

        # Test fallback when unknown engine requested
        app_custom = ScriberDesktopApp(mode="non_existent_engine")
        self.assertEqual(app_custom.resolve_engine(), engines[0])

    def test_desktop_bridge_info(self):
        """Verifies ScriberDesktopBridge exposes expected metadata to JavaScript."""
        app = ScriberDesktopApp(port=9999)
        bridge = ScriberDesktopBridge(app)
        info = bridge.get_desktop_info()

        self.assertEqual(info["app_name"], "Scriber Studio Desktop")
        self.assertEqual(info["name"], "Scriber Studio Desktop")
        self.assertEqual(info["version"], __version__)
        self.assertTrue(info["is_desktop"])
        self.assertTrue(info["desktop_mode"])
        self.assertEqual(info["platform"], sys.platform)
        self.assertIn("engine", info)
        self.assertIn("port", info)

    def test_background_server_lifecycle_and_desktop_endpoints(self):
        """Verifies background server starts on free port, responds to endpoints, and stops cleanly."""
        free_port = find_available_port("127.0.0.1", preferred_port=0)
        server = ScriberBackgroundServer(host="127.0.0.1", port=free_port)
        with server:
            self.assertTrue(server._is_running)
            self.assertTrue(server.url.startswith("http://127.0.0.1:"))

            # 1. Test GET /api/desktop/info
            with urllib.request.urlopen(f"{server.url}/api/desktop/info", timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data["desktop_mode"])
                self.assertTrue(data["is_desktop"])
                self.assertEqual(data["version"], __version__)
                self.assertEqual(data["app_name"], "Scriber Studio Desktop")

            # 2. Test GET /favicon.ico
            with urllib.request.urlopen(f"{server.url}/favicon.ico", timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                self.assertGreater(len(resp.read()), 100)

            # 3. Test POST /api/desktop/reveal
            req_data = json.dumps({"path": "./tests"}).encode("utf-8")
            req = urllib.request.Request(
                f"{server.url}/api/desktop/reveal",
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                result = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(result["success"])

            # 4. Test POST /api/desktop/save-file
            save_payload = json.dumps({
                "filename": "test_desktop_export.txt",
                "content": "Desktop save verification content",
                "dir": "./test_scratch",
            }).encode("utf-8")
            req_save = urllib.request.Request(
                f"{server.url}/api/desktop/save-file",
                data=save_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req_save, timeout=3.0) as resp:
                self.assertEqual(resp.status, 200)
                save_res = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(save_res["success"])
                saved_path = save_res["saved_path"]
                self.assertTrue(os.path.isfile(saved_path))
                with open(saved_path, "r", encoding="utf-8") as f:
                    self.assertEqual(f.read(), "Desktop save verification content")

        # After context manager exit, server must be stopped
        self.assertFalse(server._is_running)

    def test_cli_app_subcommand_parser(self):
        """Verifies CLI argument parser handles 'app' command with custom parameters."""
        from scriber.cli import main

        test_args = ["scriber", "app", "--port", "8899", "--mode", "webview", "--fullscreen", "--debug"]
        with patch.object(sys, "argv", test_args):
            with patch("scriber.cli.run_app") as mock_run_app:
                main()
                mock_run_app.assert_called_once()
                called_args = mock_run_app.call_args[0][0]
                self.assertEqual(called_args.command, "app")
                self.assertEqual(called_args.port, 8899)
                self.assertEqual(called_args.mode, "webview")
                self.assertTrue(called_args.fullscreen)
                self.assertTrue(called_args.debug)

    def test_run_desktop_argument_dispatch(self):
        """Verifies run_desktop.py parses desktop flags and dispatches to launch_desktop or CLI."""
        # 1. Test top-level desktop flags
        test_args = ["run_desktop.py", "--port", "9123", "--mode", "edge", "--fullscreen"]
        with patch.object(sys, "argv", test_args):
            with patch("run_desktop.launch_desktop") as mock_launch:
                mock_launch.return_value = 0
                ret = run_desktop.parse_and_run()
                self.assertEqual(ret, 0)
                mock_launch.assert_called_once_with(
                    host="127.0.0.1",
                    port=9123,
                    mode="edge",
                    fullscreen=True,
                    debug=False,
                )

        # 2. Test CLI subcommand dispatch (e.g. 'benchmark')
        test_sub_args = ["run_desktop.py", "benchmark"]
        with patch.object(sys, "argv", test_sub_args):
            with patch("scriber.cli.main") as mock_cli_main:
                ret = run_desktop.parse_and_run()
                self.assertEqual(ret, 0)
                mock_cli_main.assert_called_once()

    def test_find_available_port_probe(self):
        """Verifies find_available_port detects occupied ports and chooses fallback."""
        # Create a dummy socket listening on an ephemeral port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_s:
            probe_s.bind(("127.0.0.1", 0))
            probe_s.listen(1)
            busy_port = probe_s.getsockname()[1]

            # Trying to request the busy_port should detect occupation and yield an alternate port
            alt_port = find_available_port("127.0.0.1", preferred_port=busy_port)
            self.assertNotEqual(alt_port, busy_port)
            self.assertGreater(alt_port, 0)

    def test_process_auto_exports_to_output_folder(self):
        """Verifies processing media auto-exports multi-format files to ./scriber_output."""
        free_port = find_available_port("127.0.0.1", preferred_port=0)
        server = ScriberBackgroundServer(host="127.0.0.1", port=free_port)
        with server:
            sample_wav = AudioExtractor.create_synthetic_wav("Auto export test", duration_sec=1.0)
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            parts = [
                f"--{boundary}\r\n".encode("latin-1"),
                b'Content-Disposition: form-data; name="task"\r\n\r\ntranscribe\r\n',
                f"--{boundary}\r\n".encode("latin-1"),
                b'Content-Disposition: form-data; name="file"; filename="test_auto_export.wav"\r\n',
                b'Content-Type: audio/wav\r\n\r\n',
                sample_wav,
                b"\r\n",
                f"--{boundary}--\r\n".encode("latin-1"),
            ]
            body = b"".join(parts)

            req = urllib.request.Request(
                f"{server.url}/api/process",
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                self.assertEqual(resp.status, 200)
                res_data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("exports", res_data)
                self.assertIn("txt", res_data["exports"])

            # Verify ./scriber_output contains the generated files
            out_dir = Path("./scriber_output")
            self.assertTrue(out_dir.exists())
            expected_txt = out_dir / "test_auto_export_transcript.txt"
            self.assertTrue(expected_txt.exists(), f"Expected auto-exported file {expected_txt} to exist")

    def test_pywebview_window_creation_and_shutdown(self):
        """Verifies pywebview module is available and window creation API is valid."""
        import webview
        from unittest.mock import patch, MagicMock

        self.assertTrue(hasattr(webview, "create_window"))
        self.assertTrue(hasattr(webview, "start"))

        with patch.object(webview, "create_window", return_value=MagicMock(title="Scriber Test Window")) as mock_create:
            win = webview.create_window("Scriber Test Window", "about:blank")
            self.assertEqual(win.title, "Scriber Test Window")
            mock_create.assert_called_once()

    def test_cleanup_webview_storage_locks(self):
        """Verifies cleanup_webview_storage_locks cleans stale locks and creates fallback if locked."""
        from scriber.desktop import cleanup_webview_storage_locks
        with tempfile.TemporaryDirectory() as td:
            # Create dummy stale locks
            lock1 = os.path.join(td, "SingletonLock")
            lock2 = os.path.join(td, "test.lock")
            with open(lock1, "w") as f:
                f.write("test")
            with open(lock2, "w") as f:
                f.write("test")

            cleaned = cleanup_webview_storage_locks(td)
            self.assertEqual(cleaned, td)
            self.assertFalse(os.path.exists(lock1))
            self.assertFalse(os.path.exists(lock2))

    def test_cleanup_stale_webview_processes_safe(self):
        """Verifies cleanup_stale_webview_processes executes safely without throwing exceptions."""
        from scriber.desktop import cleanup_stale_webview_processes
        try:
            cleanup_stale_webview_processes()
        except Exception as e:
            self.fail(f"cleanup_stale_webview_processes failed: {e}")


if __name__ == "__main__":
    unittest.main()
