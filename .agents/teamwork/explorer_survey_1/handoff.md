# Survey Explorer 1 Handoff Report: Architecture, Packaging & Hardware Capability Survey

**Author**: Survey Explorer 1 (`explorer_survey_1`)  
**Working Directory**: `c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_1\`  
**Date**: 2026-10-30T17:05:00Z  
**Target Milestone**: Survey & Codebase Architecture Investigation

---

## 1. Observation

### A. Codebase Architecture & Application Framework
1. **Desktop Architecture**:
   - **Framework**: Hybrid native desktop studio.
   - **Backend Server** (`scriber/web/server.py:29-133`, `360-366`): Pure standard library HTTP server (`http.server.SimpleHTTPRequestHandler` & `socketserver.ThreadingTCPServer`) implementing REST API endpoints (`/api/process`, `/api/clone-voice`, `/api/profile-voice`, `/api/desktop/info`, `/api/benchmark`, `/api/models`, etc.). No FastAPI, Flask, or external web server dependency.
   - **Frontend UI** (`scriber/web/ui.py:1-4000+`): Embedded dark luxury UI (Dark Obsidian `#08090C`, Tangerine `#FF5E00`, Antique Gold `#FFA826`) served directly via `get_embedded_html()`.
   - **Desktop Window Manager** (`scriber/desktop.py:300-580`):
     - Primary engine: Microsoft Edge WebView2 via `pywebview` with custom Python-JS bridge `ScriberDesktopBridge` (exposed as `window.pywebview.api`).
     - Includes WebView2 resilience flags (`--disable-gpu-process-crash-limit`, `--disable-background-timer-throttling`, `--disable-renderer-backgrounding`).
     - Fallback engines: Edge standalone application mode (`msedge.exe --app=http://127.0.0.1:...`) and default web browser (`webbrowser.open`).
     - Window initialization applies Per-Monitor High-DPI V2 awareness (`SetProcessDpiAwarenessContext(-4)`) and sets taskbar `AppUserModelID` (`Scriber.Studio.Desktop.1.0`) in `scriber/desktop.py:71-103`.
   - **Entry Points**:
     - Standalone Desktop launch: `run_desktop.py` (includes `multiprocessing.freeze_support()`, GUI stdout/stderr redirection to `%LOCALAPPDATA%\Scriber\Logs\desktop.log`, and dispatches to `launch_desktop()`).
     - Module launch: `scriber/__main__.py:9-15` (runs desktop if no CLI args, else dispatches to `scriber.cli.main()`).
     - Batch/VBS: `Scriber.bat` and `Scriber.vbs`.

### B. Build, Packaging & Desktop Shortcuts
1. **PyInstaller Packaging**:
   - Spec file: `scriber.spec:1-136`. Collects submodules and data files for `scriber`, `faster_whisper`, `ctranslate2`, `onnxruntime`, `tokenizers`, `webview`, `clr_loader`, `pythonnet`.
   - Build script: `build_desktop.py:1-325`:
     - Default output: Portable directory bundle in `dist/Scriber/` (`Scriber.exe` + `_internal/`).
     - Alternative: Single-file executable `--onefile` (`dist/Scriber.exe`).
     - Subsystem Enforcement: `verify_pe_subsystem()` inspects the PE header at offset 0x3C and verifies `Subsystem == 2` (`IMAGE_SUBSYSTEM_WINDOWS_GUI`), guaranteeing no black console window spawns.
     - Brand Icon Generation: `ensure_brand_assets()` dynamically generates `scriber/assets/icon.ico` (multi-resolution 16x16 to 256x256) and `icon.png` using Pillow.
2. **Desktop Shortcut Mechanisms**:
   - `make_shortcut.py:5-30`: Python script that writes a temporary `.vbs` script and executes `cscript //nologo` to create `Scriber.lnk` on the user's desktop targeting `dist/Scriber/Scriber.exe`. Invoked automatically on build completion (`build_desktop.py:287-290`).
   - `scripts/install_windows_shortcuts.ps1:1-77`: PowerShell script creating/updating shortcuts across Desktop, OneDrive Desktop, and Start Menu (`APPDATA\Microsoft\Windows\Start Menu\Programs\Scriber.lnk`), then notifying the shell via `SHChangeNotify(0x08000000, 0, 0, 0)`.
   - `scripts/update_shortcuts.ps1:1-5`: Shortcut update wrapper.

### C. Host Hardware & GPU Capability Inspection
Direct inspection commands executed on the host Windows machine:
1. **WMI Video Controllers**:
   ```powershell
   Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, Status
   ```
   Result:
   - `Intel(R) UHD Graphics` (Driver: 32.0.101.7088, AdapterRAM: 2,147,479,552 bytes)
   - `NVIDIA GeForce RTX 5050 Laptop GPU` (Driver: 32.0.16.1074, AdapterRAM: 4,293,918,720 bytes)
2. **NVIDIA System Management Interface (`nvidia-smi`)**:
   ```cmd
   nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version,compute_cap --format=csv,noheader,nounits
   ```
   Result:
   ```text
   NVIDIA GeForce RTX 5050 Laptop GPU, 8151, 5381, 610.74, 12.0
   ```
   - GPU: NVIDIA GeForce RTX 5050 Laptop GPU (Blackwell generation architecture)
   - Total VRAM: 8,151 MiB (~8.0 GB)
   - Free VRAM: 5,381 MiB (~5.4 GB free)
   - Driver Version: 610.74 (supports CUDA 13.3)
   - Compute Capability: **12.0**
3. **In-Process NVML Query via Python `ctypes`**:
   - `ctypes.CDLL('nvml.dll')` loads cleanly.
   - `nvmlDeviceGetMemoryInfo` confirms 8,151.0 MB total VRAM and 5,381.0 MB free VRAM.
   - `nvmlDeviceGetCudaComputeCapability` confirms compute capability 12.0.
4. **DirectX / Direct3D 12 Query via `d3d12.dll`**:
   - `ctypes.windll.d3d12.D3D12CreateDevice(None, FeatureLevel, None, None)` returns `0x1` (`S_FALSE`, meaning capability supported without creating device):
     - `0xc000` (`D3D_FEATURE_LEVEL_12_0`): Supported = True
     - `0xc100` (`D3D_FEATURE_LEVEL_12_1`): Supported = True
     - `0xc200` (`D3D_FEATURE_LEVEL_12_2` / DirectX 12 Ultimate): Supported = True
5. **Existing Codebase Hardware Detection**:
   - Grep search for `cuda`, `directx`, `vram`, `hardware` across `scriber/` confirmed **ZERO** hardware capability detection exists in the existing codebase.
   - `scriber/transcription_engine.py:664`:
     ```python
     model = faster_whisper.WhisperModel(candidate, device="cpu", compute_type="int8", local_files_only=True)
     ```
     `device="cpu"` and `compute_type="int8"` are hardcoded, ignoring available CUDA GPU hardware.
   - However, in `.venv`, `ctranslate2.get_cuda_device_count()` returns `1`, and `ctranslate2.StorageView` on CUDA allocator `cuda_malloc_async` succeeded without error.

### D. Whisper Turbo Model Cache Failure (R4)
1. In `~/.cache/huggingface/hub/models--deepdml--faster-whisper-large-v3-turbo-ct2/snapshots/4df90f75321148c3a29a9e2351b7ddf8f5b115a8/`:
   - Present: `config.json` (2,263 bytes), `preprocessor_config.json` (340 bytes), `tokenizer.json` (2.7 MB), `vocabulary.json` (1.0 MB).
   - Missing: `model.bin` is completely missing.
2. Direct execution test:
   ```python
   faster_whisper.WhisperModel('deepdml/faster-whisper-large-v3-turbo-ct2', device='cpu', compute_type='int8', local_files_only=True)
   ```
   Verbatim error:
   ```text
   IncompleteSnapshotError: The cached snapshot for 'deepdml/faster-whisper-large-v3-turbo-ct2' (revision 'main', commit 4df90f75321148c3a29a9e2351b7ddf8f5b115a8) is incomplete: 1 file(s) are missing (model.bin). Outgoing traffic is disabled ('local_files_only=True'). Re-run the download with network access to complete the snapshot.
   ```
   Because `local_files_only=True` fails on the incomplete snapshot, `transcription_engine.py:656-680` falls back to `base` (which has `model.bin` 145 MB present).

### E. Git Status & Remote Repository
- Checked-out branch: `main`
- Status: Clean working directory except untracked `.agents/`
- Remote origin: `https://github.com/LakshyaPrasher/Scriber.git`
- Tracking branch: `origin/main` (up to date)
- Test suite: `python -m unittest discover -s tests -p "test_*.py"` ran **128 tests in 32.5s: ALL PASSED (0 failures, 1 skipped)**.

---

## 2. Logic Chain

1. **Host Capabilities**:
   - The host system possesses a dedicated NVIDIA GeForce RTX 5050 Laptop GPU with 8,151 MiB total VRAM (~5.4 GB free), Compute Capability 12.0, CUDA 13.3 support, and DirectX 12 Ultimate (`D3D_FEATURE_LEVEL_12_2`) support.
   - The Python environment already has `ctranslate2` built with CUDA support, and CUDA tensor allocations succeed.
2. **Current Codebase Deficit**:
   - Despite having an 8GB RTX GPU, the current application hardcodes `device="cpu"` in `transcription_engine.py:664`.
   - The application has zero hardware assessment logic to evaluate whether to run local neural models or fallback to cloud API bridges.
   - The application lacks cloud voice cloning connectors (Voicemaker.in, ElevenLabs) and lacks a local zero-shot flow-matching / speech LLM companion microservice (F5-TTS/ChatterBox).
   - Diarization relies purely on heuristic F0/centroid pitch tracking without deep ONNX neural speaker embeddings.
   - Whisper Turbo fails to load and falls back to Base solely because `model.bin` is missing from the local HuggingFace cache snapshot of `deepdml/faster-whisper-large-v3-turbo-ct2`.
3. **Packaging & Shortcuts Readiness**:
   - PyInstaller packaging script `build_desktop.py` and spec `scriber.spec` are functional and enforce Subsystem 2 GUI mode.
   - Desktop shortcut scripts (`make_shortcut.py` and `scripts/install_windows_shortcuts.ps1`) exist and function. When the build runs, `make_shortcut.py` refreshes `Scriber.lnk` on the Desktop.

---

## 3. Caveats

1. **VRAM Concurrency**: Free VRAM is currently ~5.4 GB (out of 8.1 GB total) due to background host processes (display server, webview, games, apps). A local voice cloning model plus Whisper Turbo running simultaneously on GPU must stay within ~4.5 GB peak VRAM.
2. **PyInstaller Bundle Size**: Packaging ONNX neural speaker models and PyTorch/CUDA binaries into the PyInstaller bundle can expand binary size; modular microservice architecture or dynamic local loading prevents executable bloat.
3. **DirectX DirectML vs. CUDA**: While CUDA is supported via `ctranslate2` and `nvml`, `onnxruntime` in `.venv` is currently CPU-only (`AzureExecutionProvider`, `CPUExecutionProvider`). To leverage GPU for ONNX models (e.g. CAM++ / 3D-Speaker), `onnxruntime-directml` or `onnxruntime-gpu` could be leveraged, or CPU INT8 ONNX execution can be used for embeddings (< 15ms latency per segment).

---

## 4. Conclusion & Recommendations

### Summary Table

| Category | Observed Current State | Target Requirement | Recommendation for Implementation |
|---|---|---|---|
| **GPU / Hardware Detection** | None. Hardcoded CPU in `transcription_engine.py:664`. | R1: Detect GPU, VRAM, compute capability, CUDA, DirectX; route local vs. cloud. | Create `scriber/hardware.py` using in-process `nvml.dll`, `d3d12.dll`, and `ctranslate2.get_cuda_device_count()`. Expose `/api/hardware` endpoint and auto-select `device="cuda"` when VRAM >= 4GB. |
| **Whisper Turbo Cache** | `deepdml/faster-whisper-large-v3-turbo-ct2` missing `model.bin`. | R4: Complete/repair cache to execute true Large-v3-Turbo. | Download/populate `model.bin` into the snapshot directory or point to a complete local/HF cache for `large-v3-turbo`. |
| **Voice Cloning** | Only `edge-tts` + synthetic harmonic oscillator. | R2: Local flow-matching/speech LLM microservice on GPU; Voicemaker & ElevenLabs cloud bridges with 48kHz synthesis. | Implement cloud connectors in `scriber/voice_clone.py` for Voicemaker.in & ElevenLabs; add companion microservice runner when NVIDIA GPU is present. |
| **Speaker Diarization** | Heuristic F0 autocorrelation & spectral centroid. | R3: Deep ONNX neural embeddings (CAM++ / 3D-Speaker) via onnxruntime. | Add deep ONNX embedding extractor (e.g., CAM++ / 3D-Speaker) into `scriber/diarizer.py`. |
| **Packaging & Shortcut** | Functional `build_desktop.py` and `make_shortcut.py`. | R5: Rebuild executable bundle, update desktop shortcut, push to GitHub. | Run `python build_desktop.py` after fixes; invoke `scripts/install_windows_shortcuts.ps1`; commit and push to `origin/main`. |

---

## 5. Verification Method

To independently verify these survey findings:
1. **GPU & CUDA Verification**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import ctranslate2; print('CUDA devices:', ctranslate2.get_cuda_device_count())"
   nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version,compute_cap --format=csv
   ```
2. **DirectX Verification**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import ctypes; d3d12=ctypes.windll.d3d12; print('D3D12 FL 12_2:', d3d12.D3D12CreateDevice(None, 0xc200, None, None) in (0, 1))"
   ```
3. **Whisper Turbo Cache Failure Reproduction**:
   ```powershell
   .\.venv\Scripts\python.exe -c "import faster_whisper; faster_whisper.WhisperModel('deepdml/faster-whisper-large-v3-turbo-ct2', local_files_only=True)"
   ```
   (Fails with `IncompleteSnapshotError: 1 file(s) are missing (model.bin)`).
4. **Automated Test Suite**:
   ```powershell
   .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
   ```
   (Confirms all 128 tests pass).
5. **Git Status & Remote Verification**:
   ```powershell
   git status; git remote -v
   ```
   (Confirms clean on `main`, remote `https://github.com/LakshyaPrasher/Scriber.git`).
