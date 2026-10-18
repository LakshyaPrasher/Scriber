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

# Windows GUI guard: ensure stdout/stderr/stdin exist and record errors when running under Subsystem 2 (GUI / pythonw.exe)
if sys.stdout is None or sys.stderr is None:
    try:
        log_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
            "Scriber",
            "Logs",
        )
        os.makedirs(log_dir, exist_ok=True)
        log_file = open(os.path.join(log_dir, "desktop.log"), "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = log_file
        if sys.stderr is None:
            sys.stderr = log_file
    except Exception:
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")

if sys.stdin is None:
    try:
        sys.stdin = open(os.devnull, "r", encoding="utf-8")
    except Exception:
        pass

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scriber import __version__
from scriber.assets import get_icon_path
from scriber.web.server import ScriberBackgroundServer, find_available_port

logger = logging.getLogger("scriber.desktop")


def apply_windows_dpi_and_app_id():
    """Sets Windows High-DPI awareness (Per-Monitor V2) before any COM/Shell initialization,
    then assigns explicit AppUserModelID for taskbar branding."""
    if sys.platform != "win32":
        return

    # 1. Set Per-Monitor High-DPI Awareness (V2) FIRST, before COM or Shell32 initialization
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4 (Win10 Creators Update 1703+)
        if hasattr(ctypes.windll.user32, "SetProcessDpiAwarenessContext"):
            ctypes.windll.user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
            ctypes.windll.user32.SetProcessDpiAwarenessContext.restype = ctypes.c_bool
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        elif hasattr(ctypes.windll.shcore, "SetProcessDpiAwareness"):
            # PROCESS_PER_MONITOR_DPI_AWARE = 2 (Win 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness.argtypes = [ctypes.c_int]
            ctypes.windll.shcore.SetProcessDpiAwareness.restype = ctypes.c_long
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        else:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        logger.debug("DPI awareness initialization skipped: %s", e)

    # 2. Set explicit AppUserModelID with explicit LPCWSTR Unicode type
    try:
        from ctypes import wintypes
        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [wintypes.LPCWSTR]
        set_app_id.restype = ctypes.c_long
        set_app_id("Scriber.Studio.Desktop.1.0")
    except Exception as e:
        logger.debug("Failed setting AppUserModelID: %s", e)


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

    _serializable = False

    def __init__(self, app: ScriberDesktopApp):
        # NOTE: Attribute MUST start with an underscore so pywebview's recursive
        # get_functions() reflection does NOT traverse into ScriberDesktopApp -> Window ->
        # native WinForms BrowserForm / CLR controls, which causes an infinite reflection loop
        # and COM apartment deadlocks that freeze the UI thread into 'Not Responding'.
        self._app = app
        self._app._serializable = False

    def get_desktop_info(self) -> Dict[str, Any]:
        """Returns desktop runtime metadata to the web interface."""
        return {
            "name": "Scriber Studio Desktop",
            "app_name": "Scriber Studio Desktop",
            "version": __version__,
            "platform": sys.platform,
            "engine": self._app.active_engine,
            "port": self._app.server.port if self._app.server else 8080,
            "url": self._app.server.url if self._app.server else "",
            "is_desktop": True,
            "desktop_mode": True,
            "is_frozen": getattr(sys, "frozen", False),
        }

    def open_file_dialog(self, file_types: Optional[List[str]] = None) -> Optional[str]:
        """Opens native file picker dialog and returns selected path."""
        if not self._app.window:
            return None
        import webview
        dialog_types = file_types or [
            "Media Files (*.mp4;*.mp3;*.wav;*.m4a;*.aac;*.ogg;*.flac;*.webm;*.mov;*.mkv;*.avi;*.flv;*.wmv;*.opus;*.wma;*.3gp;*.ts;*.m4v)",
            "Video Files (*.mp4;*.mov;*.mkv;*.webm;*.avi;*.flv;*.wmv;*.3gp;*.ts;*.m4v)",
            "Audio Files (*.mp3;*.wav;*.m4a;*.aac;*.ogg;*.flac;*.opus;*.wma)",
            "All Files (*.*)",
        ]
        try:
            result = self._app.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=dialog_types,
            )
            if result and len(result) > 0:
                return result[0]
        except Exception as e:
            logger.warning("Native open file dialog error: %s", e)
        return None

    def save_file_dialog(self, filename: str = "transcript.txt") -> Optional[str]:
        """Opens native save file dialog and returns target path."""
        if not self._app.window:
            return None
        import webview
        try:
            result = self._app.window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=filename,
            )
            return result if isinstance(result, str) else (result[0] if result else None)
        except Exception as e:
            logger.warning("Native save file dialog error: %s", e)
        return None

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
        if self._app.window:
            self._app.window.minimize()

    def maximize_window(self):
        """Toggles maximize state for the native desktop window."""
        if self._app.window:
            self._app.window.toggle_fullscreen()

    def close_window(self):
        """Closes the desktop application window."""
        if self._app.window:
            self._app.window.destroy()

    def log(self, message: str):
        """Logs a message from the web UI to the desktop console."""
        print(f"[Scriber UI] {message}")


def cleanup_stale_webview_processes(storage_path: Optional[str] = None):
    """Detects and terminates any orphaned msedgewebview2.exe processes associated with
    Scriber from previous ungraceful shutdowns, freeing locked files and pipes."""
    if sys.platform != "win32":
        return
    try:
        current_pid = os.getpid()
        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"""
            Get-CimInstance Win32_Process -Filter "Name = 'msedgewebview2.exe'" | Where-Object {{
                ($_.CommandLine -like '*Scriber*') -and ($_.ParentProcessId -ne {current_pid})
            }} | ForEach-Object {{
                try {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }} catch {{}}
            }}
            """,
        ]
        subprocess.run(cmd, timeout=3.0, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.debug("Orphaned webview process cleanup skipped: %s", e)


def cleanup_webview_storage_locks(storage_path: str) -> str:
    """Removes stale Chromium / WebView2 lock files. If the directory cannot be cleaned
    due to an active file lock, returns an isolated clean directory path."""
    if not storage_path:
        return storage_path

    try:
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)
            return storage_path

        lock_names = {"SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile", "LOCK"}
        has_unremovable_lock = False

        for root, _, files in os.walk(storage_path):
            for f in files:
                if f.endswith(".lock") or f in lock_names:
                    p = os.path.join(root, f)
                    try:
                        os.remove(p)
                    except Exception:
                        has_unremovable_lock = True

        if has_unremovable_lock:
            fallback_path = os.path.join(
                os.path.dirname(storage_path),
                f"WebView2_p{os.getpid()}_{int(time.time())}",
            )
            os.makedirs(fallback_path, exist_ok=True)
            logger.warning(
                "Primary WebView2 storage locked by prior instance. Using isolated fallback: %s",
                fallback_path,
            )
            return fallback_path
    except Exception as e:
        logger.debug("Storage lock cleanup error: %s", e)

    return storage_path


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

        # Configure pywebview settings
        webview.settings["ALLOW_FILE_URLS"] = True
        webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False

        # Configure WebView2 browser resilience flags:
        # Prevents GPU context-loss black screen, background throttling, and renderer freezing
        existing_args = os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "")
        resilience_args = (
            "--disable-gpu-process-crash-limit "
            "--disable-background-timer-throttling "
            "--disable-backgrounding-occluded-windows "
            "--disable-renderer-backgrounding "
            "--disable-features=ElasticOverscroll"
        )
        if "--disable-gpu-process-crash-limit" not in existing_args:
            os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = f"{existing_args} {resilience_args}".strip()

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
        primary_storage = os.path.join(
            os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
            "Scriber",
            "WebView2",
        )
        cleanup_stale_webview_processes(primary_storage)
        storage_path = cleanup_webview_storage_locks(primary_storage)

        # Track page load status and arm watchdog timer
        loaded_event = threading.Event()

        def on_loaded():
            loaded_event.set()
            logger.info("WebView2 window loaded successfully.")

        self.window.events.loaded += on_loaded

        # Watchdog: if WebView2 freezes on startup and fails to load within 6.0s,
        # close the hung window and fall back to Edge standalone app mode
        def webview_watchdog():
            if not loaded_event.wait(timeout=6.0):
                if not self._shutdown_event.is_set():
                    logger.warning(
                        "WebView2 window did not signal loaded within 6s (possible GPU/STA freeze). "
                        "Triggering fallback to Edge standalone app mode..."
                    )
                    try:
                        if self.window:
                            self.window.destroy()
                    except Exception:
                        pass

        watchdog_thread = threading.Thread(target=webview_watchdog, daemon=True, name="ScriberWebviewWatchdog")
        watchdog_thread.start()

        try:
            webview.start(
                gui="edgechromium",
                debug=self.debug,
                icon=icon_path,
                storage_path=storage_path,
                private_mode=False,
            )

            # If webview.start returned but page was never loaded and not user shutdown, fallback to edge
            if not loaded_event.is_set() and not self._shutdown_event.is_set():
                logger.warning("WebView2 exited without loading page. Launching Edge standalone app mode.")
                return self._run_edge(url)

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

        # Clean stale locks
        try:
            for root, _, files in os.walk(user_data_dir):
                for f in files:
                    if f.endswith(".lock") or f in ("SingletonLock", "lockfile", "LOCK"):
                        try:
                            os.remove(os.path.join(root, f))
                        except Exception:
                            pass
        except Exception:
            pass

        args = [
            edge_bin,
            f"--app={url}",
            f"--user-data-dir={user_data_dir}",
            f"--window-size={self.width},{self.height}",
            "--window-position=100,80",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate,ElasticOverscroll",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--class=ScriberStudioApp",
            "--app-id=ScriberStudioApp",
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
