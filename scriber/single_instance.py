"""Single instance application guard for Scriber Studio Desktop.
Prevents duplicate instances from launching simultaneously on Windows.
When a second instance is launched, it restores and focuses the existing window
and exits cleanly.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import sys

logger = logging.getLogger("scriber.single_instance")

# Global handle reference so Python GC does not close the handle
_MUTEX_HANDLE = None
MUTEX_NAME = "Local\\ScriberStudioDesktopSingleInstanceMutex"


def focus_existing_window() -> bool:
    """Finds an existing Scriber Studio desktop window and brings it to the foreground."""
    if sys.platform != "win32":
        return False

    try:
        user32 = ctypes.windll.user32
        found_hwnd = None

        def enum_windows_callback(hwnd, _):
            nonlocal found_hwnd
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value
                    is_candidate = (
                        ("Scriber — Studio" in title)
                        or ("Scriber" in title and "Studio" in title)
                        or (title.strip() == "Scriber")
                    )
                    is_excluded = any(
                        x in title
                        for x in [
                            "Visual Studio",
                            "Code",
                            "File Explorer",
                            "Notepad",
                            ".txt",
                            ".py",
                            ".md",
                            "Chrome",
                            "Edge",
                            "Firefox",
                        ]
                    )
                    if is_candidate and not is_excluded:
                        found_hwnd = hwnd
                        return False  # Stop enumeration
            return True

        enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_windows_callback)
        user32.EnumWindows(enum_proc, 0)

        if found_hwnd:
            # SW_RESTORE = 9, SW_SHOW = 5
            # Only un-minimize if iconic to preserve user's maximized state
            if user32.IsIconic(found_hwnd):
                user32.ShowWindow(found_hwnd, 9)
            else:
                user32.ShowWindow(found_hwnd, 5)
            user32.SetForegroundWindow(found_hwnd)
            return True
    except Exception as e:
        logger.debug("Could not focus existing window: %s", e)

    return False


def ensure_single_instance() -> bool:
    """Ensures only a single instance of Scriber Studio runs at any time.

    Returns:
        bool: True if this is the primary instance (execution should continue).
              False if another instance is already running (execution should terminate).
    """
    global _MUTEX_HANDLE

    if sys.platform != "win32":
        return True

    try:
        kernel32 = ctypes.windll.kernel32
        # ERROR_ALREADY_EXISTS = 183
        _MUTEX_HANDLE = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = kernel32.GetLastError()

        if last_error == 183:
            logger.info("Another instance of Scriber Studio is already running.")
            focus_existing_window()
            return False

        return True
    except Exception as e:
        logger.warning("Single instance mutex initialization skipped: %s", e)
        return True


def release_single_instance():
    """Explicitly releases the mutex handle upon application termination."""
    global _MUTEX_HANDLE
    if sys.platform == "win32" and _MUTEX_HANDLE:
        try:
            ctypes.windll.kernel32.CloseHandle(_MUTEX_HANDLE)
        except Exception:
            pass
        _MUTEX_HANDLE = None
