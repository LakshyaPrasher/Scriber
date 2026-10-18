"""Main entrypoint for Scriber module execution (py -m scriber)."""

from __future__ import annotations

import sys
from scriber.cli import main


if __name__ == "__main__":
    # If run with no arguments, launch native desktop application directly
    if len(sys.argv) == 1:
        from scriber.desktop import launch_desktop
        sys.exit(launch_desktop())
    else:
        main()
