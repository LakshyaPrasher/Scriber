"""Scriber Native Desktop Application Window.
Embeds the Scriber Studio luxury UI inside a localized desktop window using
Microsoft Edge WebView2 (pywebview) or dedicated Edge standalone app-mode.
Eliminates the requirement for external Chrome browser tabs.
"""

from __future__ import annotations

import atexit
import ctypes
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scriber import __version__
from scriber.assets import get_icon_path
from scriber.web.server import ScriberBackgroundServer, find_available_port

logger = logging.getLogger("scriber.desktop")


def apply_windows_dpi_and_app_id():
    """Sets Windows AppUserModelID for taskbar grouping and activates Per-Monitor High-DPI awareness."""
    if sys.platform != "win32":
        return

    # 1. Set explicit AppUserModelID so taskbar groups properly with Scriber brand icon
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Scriber.Studio.Desktop.1.0")
    except Exception as e:
        logger.debug("Failed setting AppUserModelID: %s", e)

    # 2. Set Per-Monitor High-DPI Awareness (V2) or fallback to system DPI aware
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e:
            logger.debug("Failed setting DPI awareness: %s", e)


def find_edge_binary() -> Optional[str]:
    """Locates the Microsoft Edge executable on Windows."""
    # Check PATH first
    which_edge = shutil.which("msedge")
    if which_edge and os.path.exists(which_edge):
        return which_edge

    # Common Windows installation directories
    candidate_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in candidate_paths:
        if os.path.isfile(p):
            return p
    return None


class ScriberDesktopBridge:
    """JavaScript API bridge exposed to the webview DOM window via window.pywebview.api."""

    def __init__(self, app: ScriberDesktopApp):
        self.app = app

    def get_desktop_info(self) -> Dict[str, Any]:
        """Returns desktop runtime metadata to the web interface."""
        return {
            "name": "Scriber Studio Desktop",
            "app_name": "Scriber Studio Desktop",
            "version": __version__,
            "platform": sys.platform,
            "engine": self.app.active_engine,
            "port": self.app.server.port if self.app.server else 8080,
            "url": self.app.server.url if self.app.server else "",
            "is_desktop": True,
            "desktop_mode": True,
            "is_frozen": getattr(sys, "frozen", False),
        }

    def open_file_dialog(self, file_types: Optional[List[str]] = None) -> Optional[str]:
        """Opens native file picker dialog and returns selected path."""
        if not self.app.window:
            return None
        import webview
        dialog_types = file_types or [
            "Media Files (*.mp4;*.mp3;*.wav;*.m4a;*.aac;*.ogg;*.flac;*.webm;*.mov;*.mkv)",
            "All Files (*.*)",
        ]
        result = self.app.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=dialog_types,
        )
        if result and len(result) > 0:
            return result[0]
        return None

    def save_file_dialog(self, filename: str = "transcript.txt") -> Optional[str]:
        """Opens native save file dialog and returns target path."""
        if not self.app.window:
            return None
        import webview
        result = self.app.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename,
        )
        return result if isinstance(result, str) else (result[0] if result else None)

    def reveal_in_explorer(self, target_path: Optional[str] = None) -> bool:
        """Opens the specified file or folder in native Windows Explorer."""
        path = os.path.abspath(target_path or "./scriber_output")
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        try:
            if sys.platform == "win32":
                if os.path.isfile(path):
                    subprocess.Popen(["explorer.exe", f"/select,{path}"])
                else:
                    os.startfile(path)
                return True
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
                return True
            else:
                subprocess.Popen(["xdg-open", path])
                return True
        except Exception as e:
            logger.error("Failed revealing path in explorer: %s", e)
            return False

    def minimize_window(self):
        """Minimizes the native desktop window."""
        if self.app.window:
            self.app.window.minimize()

    def maximize_window(self):
        """Toggles maximize state for the native desktop window."""
        if self.app.window:
            self.app.window.toggle_fullscreen()

    def close_window(self):
        """Closes the desktop application window."""
        if self.app.window:
            self.app.window.destroy()

    def log(self, message: str):
        """Logs a message from the web UI to the desktop console."""
        print(f"[Scriber UI] {message}")


class ScriberDesktopApp:
    """Manages the lifecycle of Scriber native desktop application."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        mode: str = "auto",
        fullscreen: bool = False,
        debug: bool = False,
        width: int = 1280,
        height: int = 860,
        min_width: int = 980,
        min_height: int = 640,
    ):
        self.host = host
        self.port = port
        self.mode = mode.lower()
        self.fullscreen = fullscreen
        self.debug = debug
        self.width = width
        self.height = height
        self.min_width = min_width
        self.min_height = min_height

        self.server: Optional[ScriberBackgroundServer] = None
        self.window = None
        self.bridge = ScriberDesktopBridge(self)
        self.active_engine = "unknown"
        self._shutdown_event = threading.Event()

    def detect_available_engines(self) -> List[str]:
        """Detects available desktop runtime engines in order of preference."""
        engines = []
        try:
            import webview
            engines.append("webview")
        except ImportError:
            pass

        if find_edge_binary():
            engines.append("edge")

        engines.append("browser")
        return engines

    def resolve_engine(self) -> str:
        """Resolves target engine based on requested mode and available runtimes."""
        available = self.detect_available_engines()
        if self.mode == "auto":
            return available[0] if available else "browser"
        if self.mode in available:
            return self.mode
        # If requested mode not found, fall back gracefully
        logger.warning(
            "Requested engine '%s' not available. Falling back to '%s'.",
            self.mode,
            available[0],
        )
        return available[0]

    def start_background_server(self, timeout: float = 6.0) -> str:
        """Starts the local Scriber server and waits for readiness."""
        self.server = ScriberBackgroundServer(host=self.host, port=self.port)
        self.server.start(timeout=timeout)
        logger.info("Scriber background server listening at %s", self.server.url)
        return self.server.url

    def stop(self):
        """Stops the desktop application and shuts down the background server."""
        self._shutdown_event.set()
        if self.server:
            try:
                self.server.stop()
            except Exception as e:
                logger.debug("Error stopping server: %s", e)
            self.server = None

    def run(self) -> int:
        """Launches the desktop application window with native system integration."""
        apply_windows_dpi_and_app_id()

        # Register cleanup handlers
        atexit.register(self.stop)

        try:
            url = self.start_background_server()
        except Exception as e:
            print(f"Error starting Scriber server: {e}", file=sys.stderr)
            return 1

        self.active_engine = self.resolve_engine()

        print(f"\n=======================================================")
        print(f"  [*] Scriber Studio Desktop Application v{__version__}")
        print(f"=======================================================")
        print(f"  Engine:   {self.active_engine.upper()} (Microsoft Edge WebView2)")
        print(f"  Endpoint: {url}")
        print(f"  Aesthetic: Dark Obsidian (#08090C) & Vibrant Tangerine")
        print(f"-------------------------------------------------------\n")

        try:
            if self.active_engine == "webview":
                return self._run_webview(url)
            elif self.active_engine == "edge":
                return self._run_edge(url)
            else:
                return self._run_browser(url)
        except KeyboardInterrupt:
            print("\nScriber desktop application terminated by user.")
            return 0
        finally:
            self.stop()

    def _run_webview(self, url: str) -> int:
        """Runs the native window using pywebview backed by Microsoft Edge WebView2."""
        import webview

        icon_path = str(get_icon_path().resolve()) if get_icon_path().exists() else None

        self.window = webview.create_window(
            title="Scriber — Studio Intelligence & Voice Synthesis",
            url=url,
            width=self.width,
            height=self.height,
            min_size=(self.min_width, self.min_height),
            resizable=True,
            fullscreen=self.fullscreen,
            background_color="#08090C",
            js_api=self.bridge,
            text_select=True,
        )

        # On closing window, signal shutdown
        def on_closed():
            self.stop()

        self.window.events.closed += on_closed

        # Persistent user data directory for WebView2 to prevent tempdir locking issues
        storage_path = os.path.join(
            os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
            "Scriber",
            "WebView2",
        )
        try:
            os.makedirs(storage_path, exist_ok=True)
        except Exception:
            storage_path = None

        try:
            # gui='edgechromium' ensures Microsoft Edge WebView2 on Windows
            webview.start(
                gui="edgechromium",
                debug=self.debug,
                icon=icon_path,
                storage_path=storage_path,
            )
            return 0
        except Exception as e:
            logger.warning("pywebview edgechromium failed (%s). Falling back to Edge standalone app.", e)
            return self._run_edge(url)

    def _run_edge(self, url: str) -> int:
        """Runs Microsoft Edge in borderless standalone application mode."""
        edge_bin = find_edge_binary()
        if not edge_bin:
            logger.warning("Microsoft Edge not found. Falling back to default browser.")
            return self._run_browser(url)

        # Create isolated temporary user data dir so app runs independently from main Edge browsing
        user_data_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
            "ScriberDesktop",
            "EdgeProfile",
        )
        os.makedirs(user_data_dir, exist_ok=True)

        args = [
            edge_bin,
            f"--app={url}",
            f"--user-data-dir={user_data_dir}",
            f"--window-size={self.width},{self.height}",
            "--window-position=100,80",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate",
            "--class=ScriberStudioApp",
        ]
        if self.fullscreen:
            args.append("--start-fullscreen")

        print("[*] Launching Scriber in standalone desktop application window...")
        proc = subprocess.Popen(args)

        try:
            proc.wait()
            return proc.returncode or 0
        except KeyboardInterrupt:
            try:
                proc.terminate()
            except Exception:
                pass
            return 0

    def _run_browser(self, url: str) -> int:
        """Launches system default web browser fallback."""
        print(f"[*] Opening Scriber in default browser: {url}")
        webbrowser.open(url)
        print("[*] Scriber is running in browser mode. Press Ctrl+C to terminate.")
        try:
            while not self._shutdown_event.is_set():
                time.sleep(0.5)
            return 0
        except KeyboardInterrupt:
            return 0


def launch_desktop(
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    mode: str = "auto",
    fullscreen: bool = False,
    debug: bool = False,
) -> int:
    """Convenience entry point for launching Scriber desktop window."""
    app = ScriberDesktopApp(
        host=host,
        port=port,
        mode=mode,
        fullscreen=fullscreen,
        debug=debug,
    )
    return app.run()




if __name__ == "__main__":
    sys.exit(launch_desktop())
