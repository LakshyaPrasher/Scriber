"""Test Desktop Stability and Process Forensics for Scriber on Windows."""

import concurrent.futures
import inspect
import json
import os
import socket
import sys
import time
import unittest
import urllib.request

from scriber.desktop import (
    ScriberDesktopApp,
    ScriberDesktopBridge,
    apply_windows_dpi_and_app_id,
)
from scriber.web.server import ScriberBackgroundServer


class TestDesktopStability(unittest.TestCase):
    """Verifies prevention of UI thread freezes, COM apartment locks, and server deadlocks."""

    def test_dpi_awareness_safe_initialization(self):
        """Verifies apply_windows_dpi_and_app_id succeeds without raising access violations."""
        try:
            apply_windows_dpi_and_app_id()
        except Exception as e:
            self.fail(f"apply_windows_dpi_and_app_id raised unexpected exception: {e}")

    def test_bridge_reflection_safety_and_no_recursion(self):
        """Verifies pywebview's get_functions reflection does not recurse into DesktopApp or WinForms."""
        app = ScriberDesktopApp()
        bridge = ScriberDesktopBridge(app)

        # Replicate pywebview's exact reflection logic from webview.platforms.edgechromium.inject_pywebview
        exposed_objects = []

        def get_functions(obj, base_name="", functions=None):
            obj_id = id(obj)
            if obj_id in exposed_objects:
                return functions
            exposed_objects.append(obj_id)
            if functions is None:
                functions = {}
            for name in dir(obj):
                try:
                    full_name = f"{base_name}.{name}" if base_name else name
                    if name.startswith("_"):
                        continue
                    attr = getattr(obj, name)
                    if not getattr(attr, "_serializable", True):
                        continue
                    if inspect.ismethod(attr) or inspect.isfunction(attr):
                        functions[full_name] = [
                            a
                            for a in inspect.getfullargspec(attr).args
                            if a != "self"
                        ]
                    elif inspect.isclass(attr) or (
                        isinstance(attr, object)
                        and not callable(attr)
                        and hasattr(attr, "__module__")
                    ):
                        get_functions(attr, full_name, functions)
                except Exception as e:
                    pass
            return functions

        t0 = time.time()
        funcs = get_functions(bridge)
        elapsed = time.time() - t0

        # Must execute in under 0.05 seconds (previously took minutes / hung indefinitely)
        self.assertLess(
            elapsed,
            0.05,
            f"Bridge reflection took too long ({elapsed:.3f}s), indicating recursive object leak",
        )

        expected_bridge_methods = {
            "get_desktop_info",
            "open_file_dialog",
            "save_file_dialog",
            "reveal_in_explorer",
            "minimize_window",
            "maximize_window",
            "close_window",
            "log",
        }
        for method in expected_bridge_methods:
            self.assertIn(method, funcs, f"Expected bridge method {method} not found in reflection")

        # Ensure NO private or internal DesktopApp or Window properties leaked into JS API
        leaked = [k for k in funcs.keys() if "." in k or k.startswith("server") or k.startswith("window")]
        self.assertEqual(
            leaked,
            [],
            f"Leaked internal DesktopApp / WinForms objects into JS reflection: {leaked}",
        )

    def test_multithreaded_server_concurrency_and_no_deadlock(self):
        """Verifies multi-threaded server handles simultaneous requests without deadlock or socket starvation."""
        server = ScriberBackgroundServer(host="127.0.0.1", port=0)
        server.start(timeout=5.0)
        self.assertTrue(server._is_running)

        def make_request(path):
            url = f"{server.url}{path}"
            t0 = time.time()
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "ScriberTestClient", "Connection": "close"},
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    data = resp.read()
                    return (resp.status, len(data), time.time() - t0)
            except Exception as e:
                return (0, str(e), time.time() - t0)

        # Fire 12 concurrent requests across various endpoints
        endpoints = [
            "/",
            "/api/health",
            "/api/desktop/info",
            "/favicon.ico",
        ] * 3

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(make_request, endpoints))

        for status, data_len, duration in results:
            self.assertEqual(status, 200, f"Request failed: {data_len} in {duration:.3f}s")
            self.assertLess(duration, 2.0, f"Request took too long: {duration:.3f}s")

        server.stop()
        self.assertFalse(server._is_running)


if __name__ == "__main__":
    unittest.main()
