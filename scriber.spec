# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for Scriber Studio Desktop Application.
Packages Scriber into a standalone native Windows executable bundle.
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

project_root = os.path.abspath(SPECPATH)
assets_src = os.path.join(project_root, "scriber", "assets")

datas = [
    (assets_src, os.path.join("scriber", "assets")),
]
datas.extend(collect_data_files("faster_whisper"))
datas.extend(collect_data_files("ctranslate2"))
datas.extend(collect_data_files("onnxruntime"))
datas.extend(collect_data_files("tokenizers"))

hidden_imports = [
    "scriber",
    "scriber.desktop",
    "scriber.single_instance",
    "scriber.web",
    "scriber.web.server",
    "scriber.web.ui",
    "scriber.assets",
    "scriber.models",
    "scriber.pipeline",
    "scriber.audio_extractor",
    "scriber.audio_editor",
    "scriber.voice_clone",
    "scriber.diarizer",
    "scriber.council",
    "scriber.quality",
    "scriber.validator",
    "scriber.transcription_engine",
    "scriber.exporters",
    "scriber.cli",
    "webview",
    "webview.platforms.winforms",
    "clr_loader",
    "pythonnet",
    "email",
    "email.message",
    "http.server",
    "socketserver",
    "urllib.parse",
    "wave",
    "json",
    "ctypes",
]

hidden_imports.extend(collect_submodules("scriber"))
hidden_imports.extend(collect_submodules("clr_loader"))
hidden_imports.extend(collect_submodules("pythonnet"))
hidden_imports.extend(collect_submodules("webview"))
hidden_imports.extend(collect_submodules("faster_whisper"))
hidden_imports.extend(collect_submodules("ctranslate2"))
hidden_imports.extend(collect_submodules("onnxruntime"))

binaries = []

# Collect NVIDIA CUDA/cuBLAS/cuDNN runtime DLLs from site-packages
for pfx in [sys.prefix, os.path.join(project_root, ".venv")]:
    sp = os.path.join(pfx, "Lib", "site-packages")
    nv = os.path.join(sp, "nvidia")
    if os.path.isdir(nv):
        for root, dirs, files in os.walk(nv):
            for file in files:
                if file.lower().endswith(".dll"):
                    rel_dest = os.path.relpath(root, sp)
                    binaries.append((os.path.join(root, file), rel_dest))
        break

excludes = [
    "tkinter",
    "matplotlib.tests",
    "numpy.tests",
    "scipy",
    "pandas",
    "IPython",
    "jupyter",
    "torch",
]

icon_path = os.path.join(assets_src, "icon.ico")
if not os.path.exists(icon_path):
    icon_path = None

# Standalone Native Desktop Build: Windows GUI Subsystem (Subsystem 2: IMAGE_SUBSYSTEM_WINDOWS_GUI).
# Subsystem 3 (Console) causes Windows to spawn an unwanted black terminal window on startup.
# console=False is strictly enforced as the default to guarantee the compiled binary is Subsystem 2.
# Accidental environment variables are disregarded.
force_debug_console = os.environ.get("SCRIBER_FORCE_CONSOLE_DEBUG", "0").lower() in ("1", "true")
build_console = force_debug_console

a = Analysis(
    [os.path.join(project_root, "run_desktop.py")],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Scriber",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=build_console,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Scriber",
)
