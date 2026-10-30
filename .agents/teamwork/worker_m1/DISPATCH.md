# Task Assignment: Worker M1 — Hardware & GPU Capability Assessment

- Role: Milestone 1 Implementation Worker
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m1\
- Authoritative Request: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
- Scope Document: c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
- Explorer Findings: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_1\handoff.md

## Scope & File Ownership
You exclusively own:
- `scriber/hardware.py` (new module)
- Additions to `scriber/models.py` (`HardwareCapabilities` dataclass)
- Additions to `scriber/web/server.py` (`/api/hardware` REST endpoint)
- `tests/test_hardware.py` (comprehensive unit tests)

## Requirements
1. Implement `scriber/hardware.py`:
   - Inspect NVIDIA GPU via in-process `nvml.dll` using `ctypes` (`nvmlInit`, `nvmlDeviceGetHandleByIndex`, `nvmlDeviceGetName`, `nvmlDeviceGetMemoryInfo`, `nvmlDeviceGetCudaComputeCapability`, `nvmlSystemGetDriverVersion`, `nvmlShutdown`).
   - Inspect DirectX 12 support via `d3d12.dll` using `ctypes.windll.d3d12.D3D12CreateDevice` across feature levels `0xc000` (12_0), `0xc100` (12_1), and `0xc200` (12_2).
   - Inspect CTranslate2 CUDA support via `ctranslate2.get_cuda_device_count()`.
   - Provide graceful fallback if running on non-NVIDIA/CPU-only environments or non-Windows OS.
   - Implement `get_hardware_capabilities() -> HardwareCapabilities`:
     - Fields: `gpu_name: Optional[str]`, `vram_total_mb: float`, `vram_free_mb: float`, `compute_capability: Tuple[int, int]`, `cuda_available: bool`, `cuda_version: str`, `directx_12_supported: bool`, `directx_feature_level: str`, `recommended_device: str` (`"cuda"` or `"cpu"`), `recommended_compute_type: str` (`"float16"` or `"int8"`), `supports_local_speech_llm: bool` (True if NVIDIA GPU with $\ge 3500$ MB free VRAM).
   - Implement `get_transcription_device_config() -> Tuple[str, str]` returning `(device, compute_type)`.
2. Update `scriber/models.py`:
   - Define dataclass `HardwareCapabilities`.
3. Update `scriber/web/server.py`:
   - Add `GET /api/hardware` route returning JSON serialization of `HardwareCapabilities`.
4. Create `tests/test_hardware.py`:
   - Test live hardware query on host machine (verifying RTX 5050 detection, VRAM > 0, DirectX 12.2).
   - Test simulated/mocked environments (e.g. CPU-only, low VRAM, NVML missing, D3D12 missing) to verify routing and fallback paths.
5. Run the tests using `.venv\Scripts\python.exe -m unittest tests/test_hardware.py` and run full test suite `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"` to ensure zero regressions.
6. Record build/test results in `.agents/teamwork/worker_m1/handoff.md`.

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.


## 2026-10-30T17:07:36Z
[Message] timestamp=2026-10-30T17:07:36Z sender=c60e3390-79cc-45bf-a4ac-11c2f4785ada priority=MESSAGE_PRIORITY_HIGH content=You are Worker M1 for Milestone 1 (Hardware & GPU Capability Assessment).
Read your dispatch instructions in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m1\DISPATCH.md
and the authoritative request in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
and project specification in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
and Explorer 1 findings in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_1\handoff.md

Your role is to implement:
1. scriber/hardware.py (NVML, D3D12, CUDA, VRAM detection, device routing)
2. scriber/models.py (HardwareCapabilities dataclass)
3. scriber/web/server.py (/api/hardware endpoint)
4. tests/test_hardware.py (comprehensive unit tests)
5. Run tests with .venv\Scripts\python.exe -m unittest tests/test_hardware.py and full suite.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliver your complete handoff report to:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m1\handoff.md
Notify the orchestrator when complete.
