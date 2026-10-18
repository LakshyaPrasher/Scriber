"""Scriber Native Desktop Application Entry Point.

Launch standalone desktop studio:
    Scriber.exe
    py run_desktop.py

CLI Subcommands & Desktop Flags:
    py run_desktop.py --mode [webview|edge|browser]
    py run_desktop.py --port 8080 --fullscreen --debug
    py run_desktop.py process <media_file> [options]
    py run_desktop.py benchmark
    py run_desktop.py info
"""

from __future__ import annotations

import argparse
import multiprocessing
import os
import sys

# Windows GUI guard: ensure stdout/stderr exist and record errors when running under pythonw.exe
if sys.stdout is None or sys.stderr is None:
    try:
        import tempfile
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

from scriber.desktop import launch_desktop


def parse_and_run() -> int:
    """Parses command-line arguments and dispatches to desktop window or CLI subcommands."""
    # If no arguments provided, launch desktop studio window directly
    if len(sys.argv) <= 1:
        return launch_desktop()

    first_arg = sys.argv[1].lower()

    # If first argument is a known CLI subcommand, dispatch to CLI
    cli_commands = {"process", "benchmark", "info", "clone-voice", "serve", "app"}
    if first_arg in cli_commands:
        import scriber.cli
        scriber.cli.main()
        return 0

    # Otherwise, handle top-level desktop flags and help
    parser = argparse.ArgumentParser(
        prog="Scriber",
        description="Scriber Native Desktop Application & Autonomous Studio",
    )
    parser.add_argument("--port", type=int, default=None, help="Port to bind server (default: auto)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "webview", "edge", "browser"],
        help="Desktop window engine (default: auto)",
    )
    parser.add_argument("--fullscreen", action="store_true", help="Launch in fullscreen mode")
    parser.add_argument("--debug", action="store_true", help="Enable developer tools and debug logging")

    args = parser.parse_args()

    return launch_desktop(
        host=args.host,
        port=args.port,
        mode=args.mode,
        fullscreen=args.fullscreen,
        debug=args.debug,
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        sys.exit(parse_and_run())
    except Exception as exc:
        import traceback
        err_text = traceback.format_exc()
        try:
            import tempfile
            log_dir = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "Scriber", "Logs")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "desktop_crash.log"), "a", encoding="utf-8") as f:
                f.write(err_text + "\n")
        except Exception:
            pass
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, f"Scriber encountered an error during launch:\n\n{exc}", "Scriber Desktop Error", 0x10)
            except Exception:
                pass
        sys.exit(1)
