"""Scriber Web UI Module.
Decoupled static asset loader providing backward-compatible embedded HTML
for standalone server and desktop webview rendering.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_static_dir() -> Path:
    """Returns the absolute path to the static web assets directory.
    Supports both source execution and frozen PyInstaller executables.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / "scriber" / "web" / "static"
        if bundled.exists():
            return bundled
        return Path(sys._MEIPASS) / "static"
    return Path(__file__).resolve().parent / "static"


def get_embedded_html() -> str:
    """Returns the clean, modern production single-page UI for Scriber.
    Inlines CSS and JS assets from scriber/web/static for standalone single-page delivery,
    preserving all existing DOM, CSS, and JS API contracts.
    """
    static_dir = get_static_dir()
    index_path = static_dir / "index.html"
    css_path = static_dir / "styles.css"
    js_path = static_dir / "app.js"

    html = index_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")

    # Inline CSS
    if '<link rel="stylesheet" href="/static/styles.css">' in html:
        html = html.replace(
            '<link rel="stylesheet" href="/static/styles.css">',
            f"<style>\n{css}\n</style>",
        )
    elif "</head>" in html:
        html = html.replace("</head>", f"<style>\n{css}\n</style>\n</head>")

    # Inline JS
    if '<script src="/static/app.js"></script>' in html:
        html = html.replace(
            '<script src="/static/app.js"></script>',
            f"<script>\n{js}\n</script>",
        )
    elif "</body>" in html:
        html = html.replace("</body>", f"<script>\n{js}\n</script>\n</body>")

    return html
