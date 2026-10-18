"""Scriber Asset Resolution Helpers.
Supports source execution and frozen PyInstaller standalone executables.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    """Returns the root directory of the application bundle.
    When frozen with PyInstaller, returns sys._MEIPASS.
    Otherwise, returns the repository/package root directory.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # scriber/assets/__init__.py -> scriber -> root
    return Path(__file__).resolve().parent.parent.parent


def get_assets_dir() -> Path:
    """Returns the absolute path to the assets directory."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "scriber" / "assets"
        if bundled.exists():
            return bundled
        return Path(sys._MEIPASS) / "assets"
    return Path(__file__).resolve().parent


def get_asset_path(filename: str) -> Path:
    """Resolves an asset file by name."""
    return get_assets_dir() / filename


def get_icon_path() -> Path:
    """Returns the primary application icon path (ICO on Windows, fallback PNG)."""
    ico = get_asset_path("icon.ico")
    if ico.exists():
        return ico
    png = get_asset_path("icon.png")
    if png.exists():
        return png
    return ico

