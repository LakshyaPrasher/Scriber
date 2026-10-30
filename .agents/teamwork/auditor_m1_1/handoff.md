# Forensic Audit Report: Milestone 1 (Hardware & GPU Capability Assessment)

**Auditor**: Forensic Auditor (`auditor_m1_1`)  
**Working Directory**: `c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\auditor_m1_1\`  
**Target Milestone**: Milestone 1 (Hardware & GPU Capability Assessment)  
**Profile**: General Project  
**Integrity Mode**: Development (per `ORIGINAL_REQUEST.md` line 8)  
**Verdict**: **CLEAN**

---

## Forensic Audit Summary

| Check | Scope | Result | Details |
|---|---|:---:|---|
| **Phase 1.1: Hardcoded Output Detection** | `scriber/hardware.py`, `scriber/models.py`, `tests/test_hardware.py` | **PASS** | No hardcoded GPU model strings, VRAM constants, or fixed return shortcuts found in source code. |
| **Phase 1.2: Facade & Dummy Logic Detection** | `scriber/hardware.py`, `scriber/web/server.py` | **PASS** | Genuine dynamic ctypes bindings to `nvml.dll` and `d3d12.dll`, querying OS driver interfaces. |
| **Phase 1.3: Pre-populated Artifact Scan** | Full repository workspace | **PASS** | No pre-existing fake test logs, mock outputs, or fabricated benchmark results predating test runs. |
| **Phase 2.1: DLL Invocation & Address Verification** | `nvml.dll`, `d3d12.dll` via Windows CTypes | **PASS** | Empirical dynamic probe confirmed live module handles, active function pointers, and fluctuating VRAM metrics. |
| **Phase 2.2: Unit & Feature Test Execution** | `tests/test_hardware.py`, `tests/e2e_suite/test_tier1_features.py` | **PASS** | 13/13 unit tests passed (2.72s); 15/15 Tier 1 E2E feature contract tests passed (8.45s). |
| **Phase 2.3: Adversarial Stress & Concurrency Test** | Multi-threaded invocation & repeated queries | **PASS** | 30 concurrent threads and 10 sequential NVML queries completed with 0 errors and no handle leaks. |

---

## 1. Observation

### 1.1 Direct Windows Dynamic Library Probing
Direct dynamic Python execution of ctypes bindings to host libraries confirmed:
- `ctypes.CDLL('nvml.dll')` successfully loaded at memory address `0x7ff9de360000`.
- Function pointers resolved dynamically:
  - `nvmlInit`: `<_FuncPtr object at 0x000001CA8075E680>`, returned `0` (`NVML_SUCCESS`).
  - `nvmlDeviceGetCount`: returned `0`, count = `1`.
  - `nvmlDeviceGetHandleByIndex(0)`: returned `0`, handle = `0x7ff902219768`.
  - `nvmlDeviceGetName`: returned `0`, verbatim name = `"NVIDIA GeForce RTX 5050 Laptop GPU"`.
  - `nvmlDeviceGetMemoryInfo`: returned `0`, total = `8,546,942,976` bytes (`8151.0 MB`), free = `6,798,647,296` bytes (`6483.7 MB`). Subsequent probe showed free = `6,410.3 MB`, demonstrating live dynamic memory polling from OS driver registers rather than static constants.
  - `nvmlDeviceGetCudaComputeCapability`: returned `0`, compute capability = `(12, 0)`.
  - `nvmlShutdown`: returned `0`.
- Direct3D 12 probe via `ctypes.windll.d3d12`:
  - `d3d12.dll` loaded at memory handle `0x7ff9c2920000`.
  - `D3D12CreateDevice`: `<_FuncPtr object at 0x000001CA8075F2B0>`.
  - Calls across feature levels returned:
    - `D3D12CreateDevice(None, 0xc200, None, None)` (DirectX 12.2): returned `1` (`S_FALSE`), confirming hardware support for Feature Level 12_2.
    - `D3D12CreateDevice(None, 0xc100, None, None)` (DirectX 12.1): returned `1`.
    - `D3D12CreateDevice(None, 0xc000, None, None)` (DirectX 12.0): returned `1`.

### 1.2 Source Code Analysis
- `scriber/hardware.py`:
  - Lines 43-64: `_load_nvml_library()` safely queries candidate paths (`nvml.dll`, `C:\Windows\System32\nvml.dll`, `C:\Program Files\NVIDIA Corporation\NVSMI\nvml.dll`, and Linux `.so`).
  - Lines 66-171: `_query_nvml_gpu()` implements complete struct `_nvmlMemory_t`, allocates `c_char` buffers for device names, inspects all GPUs by index, selects GPU with maximum VRAM, and guarantees shutdown cleanup in `finally: shutdown_fn()`.
  - Lines 173-220: `_query_d3d12()` iterates through `[0xc200, 0xc100, 0xc000, 0xb100, 0xb000]` and detects highest supported level.
  - Lines 231-289: `get_hardware_capabilities()` applies thread-safe caching (`_HARDWARE_LOCK = threading.Lock()`), enforces `>= 4000.0 MB` VRAM for `"cuda"` / `"float16"` routing, and gates `supports_local_speech_llm` at `vram_free_mb >= 3500.0`.
- `scriber/models.py:73-101`:
  - Defines `HardwareCapabilities` dataclass with all required attributes and JSON-serializable `to_dict()`.
- `scriber/web/server.py:64-67`:
  - Directly binds `GET /api/hardware` to `get_hardware_capabilities().to_dict()` with status 200.
- `scriber/transcription_engine.py:264-318`:
  - `resolve_transcription_device()` prioritizes `WHISPER_DEVICE` environment variables before delegating to `scriber.hardware.get_transcription_device_config()`.

### 1.3 Static Grep Scans for Hardcoded Values
- Searched `scriber/` for `"5050"` -> 0 matches.
- Searched `scriber/` for `"8151"` -> 0 matches.
- Searched `scriber/` for `"GeForce"` -> 0 matches.

### 1.4 Test Suite & Adversarial Stress Execution Results
- `tests/test_hardware.py`:
  ```
  Ran 13 tests in 2.722s
  OK
  ```
- Tier 1 Contract Tests (`TestTier1F1HardwareProbe`, `TestTier1F2HardwareAPIEndpoint`, `TestTier1F3DynamicDeviceRouting`):
  ```
  Ran 15 tests in 8.451s
  OK
  ```
- Concurrency & Leak Stress Test (30 simultaneous threads + 10 sequential NVML calls):
  ```
  10 sequential NVML queries succeeded without handle leaks.
  30 concurrent threads completed with 0 errors.
  DirectX 12 supported: True, feature level: 12_2
  All adversarial stress tests PASSED successfully!
  ```

---

## 2. Logic Chain

1. **Empirical Verification of Real Hardware Integration**:
   - The worker claimed in `worker_m1/handoff.md` that NVML and Direct3D 12 detect an NVIDIA RTX 5050 GPU with 8151 MB VRAM and DirectX 12.2.
   - Independent dynamic inspection confirmed real DLL handles (`0x7ff9de360000`, `0x7ff9c2920000`), genuine C library function pointers, and live OS register reads.
   - The free VRAM reading varied across runs (`6483.7 MB` then `6410.3 MB`), proving that the values are dynamically queried from GPU driver memory, not hardcoded.

2. **Absence of Facade or Evasion**:
   - Static analysis of `scriber/hardware.py` reveals complete, genuine implementations of C API structures, buffer allocations, error code verifications, and resource cleanup (`try...finally: nvmlShutdown()`).
   - Grep searches confirm zero hardcoded test outputs or dummy return strings.
   - Unit tests test both the genuine live environment (`TestHardwareLive`) and boundary/fallback conditions via targeted mocks (`TestHardwareSimulated`).

3. **Requirement & Contract Compliance**:
   - Meets Requirement R1 of `ORIGINAL_REQUEST.md`: GPU availability, VRAM, compute capability, CUDA, and DirectX are accurately inspected.
   - Meets Feature contracts F1, F2, F3 of `PROJECT.md`: Dataclass conforms to specified schema, `/api/hardware` serves real-time metrics over HTTP, and transcription engine dynamically routes between CUDA and CPU based on hardware thresholds.
   - Adversarial review verified thread safety under high concurrency (30 concurrent threads) without race conditions or memory corruption.

---

## 3. Caveats

- **Host cuBLAS Dependency**: While NVML and CTranslate2 detect the NVIDIA GPU, CTranslate2's CUDA execution provider requires `cublas64_12.dll` on Windows to perform tensor gemm operations. `scriber/transcription_engine.py` handles this with multi-tiered fallback.
- **Dynamic VRAM Fluctuations**: Available free VRAM is dependent on operating system and background desktop load. The thread-safe `get_hardware_capabilities(force_refresh=True)` interface allows callers to query up-to-date capacity before initializing large neural models.

---

## 4. Conclusion

The work products for Milestone 1 (`scriber/hardware.py`, `scriber/models.py`, `scriber/web/server.py`, `scriber/transcription_engine.py`, `tests/test_hardware.py`) are **CLEAN**.

All checks passed:
- No hardcoded test outputs or dummy facades.
- Genuine, un-mocked dynamic DLL calls to `nvml.dll` and `d3d12.dll`.
- Zero pre-populated falsified artifacts.
- 100% pass rate across 28 independent tests and adversarial concurrency stress tests.

**Verdict**: **CLEAN** — Approved for Milestone 1 completion.

---

## 5. Verification Method

To independently reproduce the forensic verification:

1. **Verify Live DLL Handles & Function Pointers**:
   ```powershell
   .\.venv\Scripts\python.exe -c "
   import ctypes
   nvml = ctypes.CDLL('nvml.dll')
   print('NVML handle:', hex(nvml._handle))
   d3d = ctypes.windll.d3d12
   print('D3D12 handle:', hex(d3d._handle))
   "
   ```

2. **Verify Live Hardware Summary CLI**:
   ```powershell
   .\.venv\Scripts\python.exe -m scriber.hardware
   ```

3. **Run Unit Test Suite**:
   ```powershell
   .\.venv\Scripts\python.exe -m unittest -v tests/test_hardware.py
   ```

4. **Run Tier 1 Contract Test Suite**:
   ```powershell
   .\.venv\Scripts\python.exe -m unittest -v tests.e2e_suite.test_tier1_features.TestTier1F1HardwareProbe tests.e2e_suite.test_tier1_features.TestTier1F2HardwareAPIEndpoint tests.e2e_suite.test_tier1_features.TestTier1F3DynamicDeviceRouting
   ```

5. **Run Multi-threaded Concurrency Stress Test**:
   ```powershell
   .\.venv\Scripts\python.exe -c "
   import threading
   from scriber.hardware import get_hardware_capabilities
   def check(i):
       c = get_hardware_capabilities(force_refresh=(i%2==0))
       assert c.cuda_available is True
   threads = [threading.Thread(target=check, args=(i,)) for i in range(30)]
   for t in threads: t.start()
   for t in threads: t.join()
   print('30 threads successfully completed!')
   "
   ```
