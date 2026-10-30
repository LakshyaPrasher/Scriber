# Challenger 1 Handoff Report: Milestone 1 Verification

**Agent**: Challenger 1 (`challenger_m1_1`)  
**Target Milestone**: Milestone 1 (Hardware & GPU Capability Assessment)  
**Date**: 2026-10-30T17:43:00Z  
**Verdict**: **APPROVE**

---

## 1. Observation

1. **Baseline Implementation Inspection**:
   - `scriber/hardware.py`:
     - Dynamic loading of NVML DLL (`_load_nvml_library`) checking Windows system and ProgramFiles candidate paths (lines 43-64).
     - Querying GPU metrics with lifecycle-managed `try...finally: shutdown_fn()` (lines 66-171).
     - Direct3D 12 feature levels query checking `12_2`, `12_1`, `12_0`, `11_1`, `11_0` with `D3D12CreateDevice` checking `hr in (0, 1)` (lines 173-220).
     - `get_hardware_capabilities` protected by `_HARDWARE_LOCK = threading.Lock()` with cache memoization (lines 231-289).
     - Routing logic: `recommended_device = "cuda"` and `recommended_compute_type = "float16"` if `cuda_avail and vram_total_mb >= 4000.0`, else `"cpu"` and `"int8"` (lines 262-267).
     - Speech LLM gating: `supports_local_speech_llm = bool(cuda_avail and vram_free_mb >= 3500.0)` (line 271).
   - `scriber/models.py:72-101`: `HardwareCapabilities` dataclass with `to_dict()` converting compute capability tuple to list and rounding floats.
   - `scriber/web/server.py:64-67`: Exposes `GET /api/hardware` returning 200 with `caps.to_dict()`.

2. **Baseline Unit & Integration Tests**:
   - Command: `.\.venv\Scripts\python.exe -m unittest -v tests/test_hardware.py`
     - Verbatim result: `Ran 13 tests in 2.684s: OK`
   - Command: `.\.venv\Scripts\python.exe -m unittest tests.e2e_suite.test_tier1_features.TestTier1F1HardwareProbe tests.e2e_suite.test_tier1_features.TestTier1F2HardwareAPIEndpoint tests.e2e_suite.test_tier1_features.TestTier1F3DynamicDeviceRouting`
     - Verbatim result: `Ran 15 tests in 9.711s: OK`

3. **Empirical Stress-Test Suite (`tests/test_hardware_stress.py`)**:
   - Authored and executed a 21-test challenge harness targeting:
     - Boundary conditions around the 3500.0 MB free VRAM speech LLM threshold:
       - `3499.0 MB` free VRAM -> `supports_local_speech_llm = False` (verified)
       - `3499.9 MB` free VRAM -> `supports_local_speech_llm = False` (verified)
       - `3500.0 MB` free VRAM -> `supports_local_speech_llm = True` (verified)
       - `3500.1 MB` free VRAM -> `supports_local_speech_llm = True` (verified)
       - `0.0 MB` and `-100.0 MB` free VRAM -> `supports_local_speech_llm = False` (verified)
       - `12000.0 MB` free VRAM with `cuda_available = False` -> `supports_local_speech_llm = False` (verified)
     - Boundary conditions around the 4000.0 MB total VRAM device routing threshold:
       - `3999.0 MB` total VRAM -> `recommended_device = "cpu"`, `recommended_compute_type = "int8"` (verified)
       - `3999.9 MB` total VRAM -> `recommended_device = "cpu"`, `recommended_compute_type = "int8"` (verified)
       - `4000.0 MB` total VRAM -> `recommended_device = "cuda"`, `recommended_compute_type = "float16"` (verified)
       - `4000.1 MB` total VRAM -> `recommended_device = "cuda"`, `recommended_compute_type = "float16"` (verified)
       - `0.0 MB` total VRAM -> `recommended_device = "cpu"`, `recommended_compute_type = "int8"` (verified)
       - `8192.0 MB` total VRAM without CUDA capability -> `recommended_device = "cpu"`, `recommended_compute_type = "int8"` (verified)
     - Thread-safety & Concurrency:
       - 64 concurrent threads pounding `get_hardware_capabilities` with alternating `force_refresh=True` and `force_refresh=False`: zero exceptions, zero deadlocks, zero partial structures.
       - 32 concurrent cached readers verified to receive identical singleton object (`self.assertIs(inst, primary)`).
     - Direct3D 12 Feature Level Fallbacks:
       - Feature Level 12_2 supported -> `(True, "12_2")` (verified)
       - Feature Level downgrade (12_2/12_1 rejected, 12_0 accepted) -> `(True, "12_0")` (verified)
       - Feature Level below 12_0 (12_x rejected, 11_1 accepted) -> `(False, "11_1")` (verified)
       - All feature levels rejected (-2005270524 / DXGI_ERROR_UNSUPPORTED) -> `(False, "")` (verified)
       - `d3d12.dll` load failure / `OSError` -> `(False, "")` (verified)
     - NVML Error Code Handling:
       - `NVML_ERROR_NO_PERMISSION` (code 4) during init -> returns `None`, `nvmlShutdown` not called (verified)
       - `NVML_ERROR_GPU_IS_LOST` (code 15) during init -> returns `None`, `nvmlShutdown` not called (verified)
       - `NVML_ERROR_NOT_FOUND` (code 6) on device get count -> returns `None`, `nvmlShutdown` called once (verified)
       - Device count 0 -> returns `None`, `nvmlShutdown` called once (verified)
       - Multi-GPU with GPU 0 lost and GPU 1 healthy -> recovers cleanly and picks GPU 1 with 8192 MB VRAM (verified)
       - Memory query failure (`NVML_ERROR_UNKNOWN` 999) -> sets 0.0 VRAM without throwing exception (verified)
       - Exception raised inside `nvmlShutdown` -> caught gracefully without crashing caller (verified)
     - Live Host Invariants:
       - Live RTX 5050 Laptop GPU verified with 8151.0 MB total VRAM, ~5.4 GB free VRAM, Direct3D 12.2, compute capability (12, 0).
       - `get_transcription_device_config()` verified matching `HardwareCapabilities` attributes.
       - `format_hardware_summary()` verified producing a clean 11+ line ASCII table.
   - Command: `.\.venv\Scripts\python.exe -m unittest -v tests/test_hardware.py tests/test_hardware_stress.py`
     - Verbatim result: `Ran 34 tests in 28.514s: OK`

---

## 2. Logic Chain

1. **Threshold Precision & Contract Compliance**:
   - `PROJECT.md` specifies that transcription routing requires $\ge 4000$ MB total VRAM and CUDA support, while speech LLM gating requires $\ge 3500$ MB free VRAM and CUDA support.
   - Observation 3 confirmed that boundary values strictly at 3499.9 MB vs 3500.0 MB and 3999.9 MB vs 4000.0 MB partition the behavior as specified by contract.
   - Edge cases such as non-CUDA GPUs with high VRAM or negative values are properly routed to CPU/int8 and speech LLM is disabled, avoiding OOMs or crashes.

2. **Concurrency Invariants**:
   - Because `_HARDWARE_LOCK` serializes access during probe execution and assigns `_CACHED_HARDWARE` atomically at the end of initialization, multi-threaded readers never observe half-populated instances or race on driver calls.
   - Observation 3 confirmed 64 parallel threads under mixed refresh modes completed with zero exceptions or race conditions.

3. **Driver Failure Isolation**:
   - Dynamic probing via `ctypes` can introduce instability if driver calls raise SEH exceptions or fail to release contexts.
   - As observed in Observation 3, `_load_nvml_library` and `_query_nvml_gpu` encapsulate initialization and shutdown within standard `try...finally` blocks, properly maintaining the invariant that `shutdown` is only invoked when `init` succeeded.
   - All examined NVML error codes (4, 6, 15, 999) degrade to safe CPU fallbacks rather than crashing the application or HTTP server.

4. **Direct3D 12 Feature Levels Hierarchy**:
   - Probing iterates descending feature levels from 12_2 down to 11_0.
   - Tests empirically verified that feature levels $\ge 12\_0$ set `directx_12_supported = True`, whereas feature levels below $12\_0$ (e.g. 11_1) set `directx_12_supported = False` while correctly recording the highest supported feature level string.

---

## 3. Caveats

1. **Driver Context Concurrency in External Processes**: While in-process NVML calls in `hardware.py` are thread-safe within Python via `_HARDWARE_LOCK`, launching external multi-process workloads that independently access the GPU (e.g., PyTorch CUDA allocations alongside CTranslate2) will compete for physical VRAM. `get_hardware_capabilities(force_refresh=True)` provides the mechanism to re-check free VRAM before spawning heavy workloads.
2. **Platform Constraints**: Direct3D 12 probing is Windows-specific (`sys.platform == "win32"`). On non-Windows platforms, tests confirmed `_query_d3d12()` returns `(False, "")` gracefully.

---

## 4. Conclusion

**Verdict: APPROVE**

Milestone 1 satisfies all requirements set forth in `ORIGINAL_REQUEST.md`, `PROJECT.md`, and the dispatch instructions:
- `scriber/hardware.py` provides accurate, in-process hardware assessment without external CLI dependencies.
- Device routing (`cuda` / `float16` vs `cpu` / `int8`) and speech LLM gating (`supports_local_speech_llm`) operate strictly at specified thresholds (4000 MB total and 3500 MB free VRAM).
- Robust thread safety under high concurrency and complete fault tolerance against NVML error codes and D3D12 fallback states have been empirically validated.
- All 34 tests across unit and stress test suites pass with 100% success.

---

## 5. Verification Method

To independently reproduce the empirical verification:

```powershell
# Run the complete hardware unit and empirical stress test suite:
.\.venv\Scripts\python.exe -m unittest -v tests/test_hardware.py tests/test_hardware_stress.py
```
*Expected Result: 34 tests ran, all OK.*

```powershell
# Run Tier 1 Feature Contract verification:
.\.venv\Scripts\python.exe -m unittest tests.e2e_suite.test_tier1_features.TestTier1F1HardwareProbe tests.e2e_suite.test_tier1_features.TestTier1F2HardwareAPIEndpoint tests.e2e_suite.test_tier1_features.TestTier1F3DynamicDeviceRouting
```
*Expected Result: 15 tests ran, all OK.*
