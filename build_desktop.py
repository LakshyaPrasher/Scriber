"""Build and packaging script for Scriber Desktop Application.
Packages Scriber into a standalone native Windows executable bundle.

Usage:
    py build_desktop.py              # Build portable onedir executable in dist/Scriber/
    py build_desktop.py --onefile    # Build single-file executable in dist/Scriber.exe
    py build_desktop.py --clean      # Clean previous build artifacts before building
    py build_desktop.py --console    # Build with console visible for debugging
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def ensure_brand_assets(root_dir: Path) -> Path:
    """Ensures icon assets exist in scriber/assets, generating them if absent."""
    assets_dir = root_dir / "scriber" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    icon_ico = assets_dir / "icon.ico"
    icon_png = assets_dir / "icon.png"

    if icon_ico.exists() and icon_png.exists():
        return icon_ico

    print("[*] Generating brand icons (Tangerine & Antique Gold dark luxury)...")
    try:
        from PIL import Image, ImageDraw

        size = 256
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded dark obsidian background
        rect_color = (13, 15, 22, 255)
        border_color = (255, 94, 0, 90)
        draw.rounded_rectangle([12, 12, 244, 244], radius=52, fill=rect_color, outline=border_color, width=3)

        # Radial glow / core circle
        center = (128, 128)
        for r in range(70, 0, -2):
            alpha = int(140 * (1.0 - r / 70.0))
            draw.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], fill=(255, 94, 0, alpha))

        # Waveform points forming dynamic S harmonic
        points = [
            (54, 148), (74, 98), (94, 138), (114, 68), (128, 48), (142, 192), (162, 98), (182, 152), (202, 128)
        ]
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=(255, 168, 38, 255), width=7)
            draw.line([points[i], points[i+1]], fill=(255, 230, 180, 255), width=3)

        # Center acoustic core
        draw.ellipse([center[0] - 12, center[1] - 12, center[0] + 12, center[1] + 12], fill=(255, 228, 181, 255))

        img.save(str(icon_png), format="PNG")
        img.save(
            str(icon_ico),
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        print(f"[+] Brand icons saved to {assets_dir}")
    except Exception as e:
        print(f"[-] Warning: Failed generating icons automatically ({e})")

    return icon_ico


def clean_build_artifacts(root_dir: Path):
    """Removes previous build and dist directories."""
    for d in [root_dir / "build", root_dir / "dist"]:
        if d.exists():
            print(f"[*] Removing existing {d.name}/ directory...")
            shutil.rmtree(d, ignore_errors=True)


def build_executable(onefile: bool = False, console: bool = False, clean: bool = False) -> int:
    """Builds Scriber standalone desktop executable."""
    root_dir = Path(__file__).resolve().parent

    print("\n=======================================================")
    print("  [*] Scriber Desktop Application Packaging Pipeline")
    print("=======================================================")
    print(f"Target OS:     Windows ({sys.platform})")
    print(f"Package Mode:  {'Single File (.exe)' if onefile else 'Portable Directory (onedir)'}")
    print(f"Window Type:   {'Console Visible (Debug)' if console else 'Windowed Native (No Console)'}")
    print(f"Workspace:     {root_dir}")
    print("-------------------------------------------------------")

    icon_ico = ensure_brand_assets(root_dir)

    if clean:
        clean_build_artifacts(root_dir)

    # Check PyInstaller availability
    try:
        import PyInstaller
        print(f"[+] PyInstaller {PyInstaller.__version__} detected.")
    except ImportError:
        print("[-] PyInstaller not found. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])

    spec_file = root_dir / "scriber.spec"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
    ]

    build_env = os.environ.copy()
    if console:
        build_env["SCRIBER_BUILD_CONSOLE"] = "1"
    else:
        build_env["SCRIBER_BUILD_CONSOLE"] = "0"

    if onefile:
        # Onefile build
        assets_src = str(root_dir / "scriber" / "assets")
        add_data = f"{assets_src}{os.pathsep}scriber/assets"
        cmd.extend([
            str(root_dir / "run_desktop.py"),
            "--name=Scriber",
            "--onefile",
            f"--add-data={add_data}",
            "--collect-submodules=scriber",
            "--collect-submodules=clr_loader",
            "--collect-submodules=pythonnet",
            "--collect-submodules=webview",
            "--collect-submodules=faster_whisper",
            "--collect-submodules=ctranslate2",
            "--collect-submodules=onnxruntime",
            "--collect-data=faster_whisper",
            "--collect-data=ctranslate2",
            "--collect-data=onnxruntime",
            "--collect-data=tokenizers",
            "--hidden-import=scriber",
            "--hidden-import=scriber.desktop",
            "--hidden-import=scriber.web",
            "--hidden-import=scriber.web.server",
            "--hidden-import=scriber.web.ui",
            "--hidden-import=scriber.assets",
            "--hidden-import=scriber.cli",
            "--hidden-import=scriber.models",
            "--hidden-import=scriber.pipeline",
            "--hidden-import=scriber.audio_extractor",
            "--hidden-import=scriber.audio_editor",
            "--hidden-import=scriber.voice_clone",
            "--hidden-import=scriber.diarizer",
            "--hidden-import=scriber.council",
            "--hidden-import=scriber.quality",
            "--hidden-import=scriber.validator",
            "--hidden-import=scriber.transcription_engine",
            "--hidden-import=scriber.exporters",
            "--hidden-import=webview",
            "--hidden-import=webview.platforms.winforms",
            "--hidden-import=clr_loader",
            "--hidden-import=pythonnet",
            "--noconfirm",
        ])
        if icon_ico.exists():
            cmd.append(f"--icon={icon_ico}")
        if not console:
            cmd.append("--noconsole")
        else:
            cmd.append("--console")
        if clean:
            cmd.append("--clean")
    else:
        # Use tuned scriber.spec
        cmd.extend([
            str(spec_file),
            "--noconfirm",
        ])
        if clean:
            cmd.append("--clean")

    print(f"[*] Executing build command: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(root_dir), env=build_env)

    if result.returncode != 0:
        print(f"\n[-] Packaging failed with exit code {result.returncode}", file=sys.stderr)
        return result.returncode

    # Verify build artifact
    if onefile:
        dist_exe = root_dir / "dist" / "Scriber.exe"
    else:
        dist_exe = root_dir / "dist" / "Scriber" / "Scriber.exe"

    if dist_exe.exists():
        size_mb = dist_exe.stat().st_size / (1024 * 1024)
        print("\n=======================================================")
        print("  [+] BUILD SUCCEEDED -- SCRIBER DESKTOP EXECUTABLE READY")
        print("=======================================================")
        print(f"Executable:   {dist_exe}")
        print(f"Binary Size:  {size_mb:.2f} MB")
        print(f"Mode:         {'Standalone Single-File' if onefile else 'Localized Portable Bundle'}")
        print(f"Launch with:  {dist_exe}")
        print("-------------------------------------------------------\n")

        # Smoke-test executable help output
        try:
            test_run = subprocess.run([str(dist_exe), "--help"], capture_output=True, timeout=8)
            print(f"[+] Executable smoke-test: exit code {test_run.returncode}")
        except Exception as e:
            print(f"[-] Note: Smoke-test skipped ({e})")

        return 0
    else:
        print(f"[-] Error: Expected executable not found at {dist_exe}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="Package Scriber into a native Windows executable")
    parser.add_argument("--onefile", action="store_true", help="Package into a single standalone .exe")
    parser.add_argument("--console", action="store_true", help="Keep console window visible for debugging")
    parser.add_argument("--clean", action="store_true", help="Clean build directories before packaging")
    parser.add_argument("--verify-only", action="store_true", help="Verify assets and configuration without building")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent
    if args.verify_only:
        ico = ensure_brand_assets(root_dir)
        print(f"[+] Verification complete. Icon at: {ico}")
        return 0

    return build_executable(onefile=args.onefile, console=args.console, clean=args.clean)


if __name__ == "__main__":
    sys.exit(main())
