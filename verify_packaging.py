"""Standalone Build & Packaging Empirical Verification Script for Milestone M12."""

import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


def verify():
    root = Path(__file__).resolve().parent
    exe_path = root / "dist" / "Scriber" / "Scriber.exe"

    print(f"=== Standalone Packaging Verification ===")
    print(f"Checking executable path: {exe_path}")
    assert exe_path.exists(), f"Executable not found at {exe_path}"
    
    stat = exe_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    print(f"[PASS] Executable exists: {exe_path}")
    print(f"[PASS] File size: {stat.st_size} bytes ({size_mb:.2f} MB)")
    print(f"[PASS] Last modified: {stat.st_mtime}")

    # 1. Verify PE Subsystem
    with open(exe_path, "rb") as f:
        data = f.read(1024)
    assert data[:2] == b"MZ", "Not a valid DOS/MZ header"
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[pe_offset:pe_offset+4] == b"PE\0\0", "Invalid PE signature"
    subsystem = struct.unpack_from("<H", data, pe_offset + 24 + 68)[0]
    print(f"[PASS] PE Subsystem: {subsystem} (Expected 2: IMAGE_SUBSYSTEM_WINDOWS_GUI)")
    assert subsystem == 2, f"Subsystem mismatch: expected 2, got {subsystem}"

    # 2. Verify Desktop Shortcut
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut_path = desktop / "Scriber.lnk"
    print(f"Checking desktop shortcut: {shortcut_path}")
    assert shortcut_path.exists(), f"Shortcut not found at {shortcut_path}"

    vbs = f"""Set oWS = CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{shortcut_path}")
WScript.Echo "SHORTCUT_TARGET=" & oLink.TargetPath
WScript.Echo "SHORTCUT_WORKDIR=" & oLink.WorkingDirectory
WScript.Echo "SHORTCUT_ICON=" & oLink.IconLocation
"""
    with tempfile.NamedTemporaryFile("w", suffix=".vbs", delete=False) as tf:
        tf.write(vbs)
        vbs_name = tf.name

    try:
        out = subprocess.check_output(["cscript", "//nologo", vbs_name], text=True)
        print(out.strip())
        lines = dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
        target = lines.get("SHORTCUT_TARGET", "")
        print(f"[PASS] Shortcut Target: {target}")
        assert Path(target).resolve() == exe_path.resolve(), f"Shortcut target mismatch: {target} != {exe_path}"
    finally:
        if os.path.exists(vbs_name):
            os.remove(vbs_name)

    print("\n[ALL PACKAGING CHECKS PASSED EMPIRICALLY]")


if __name__ == "__main__":
    verify()
