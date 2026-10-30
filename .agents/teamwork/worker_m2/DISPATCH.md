# Task Assignment: Worker M2 — Whisper Turbo Model Cache Repair & Execution

- Role: Milestone 2 Implementation Worker
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m2\
- Authoritative Request: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
- Scope Document: c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
- Explorer Findings: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_2\handoff.md

## Scope & File Ownership
You exclusively own:
- Hugging Face cache completion for `deepdml/faster-whisper-large-v3-turbo-ct2` (`C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2`)
- `scriber/transcription_engine.py` (cache verification, model resolution, device selection, elimination of Base fallback)
- `tests/test_whisper_turbo_cache.py` (unit & integration tests for Turbo cache and execution)

## Requirements
1. Repair the Whisper Turbo cache:
   - In `C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2`, `model.bin` was interrupted at 268 MB (`.incomplete` blob).
   - Use `huggingface_hub.snapshot_download("deepdml/faster-whisper-large-v3-turbo-ct2", local_files_only=False)` (or direct download) to download and verify the complete 1.61 GB `model.bin` into the snapshot directory.
   - Verify with `os.path.exists` and file size (~1.61 GB) that `model.bin` is present and snapshot is complete.
2. Update `scriber/transcription_engine.py`:
   - Enhance model loading logic in `_transcribe_faster_whisper`:
     - Inspect whether `target_model` snapshot is valid.
     - Eliminate silent fallback to Base when Turbo is requested.
     - Integrate device selection: dynamically query `scriber.hardware.get_transcription_device_config()` (or check `ctranslate2.get_cuda_device_count()`) to choose `("cuda", "float16")` when available, falling back to `("cpu", "int8")` safely.
     - Ensure `active_model_id` and `backend_used` reflect true `turbo` execution without any fallback tag.
3. Write `tests/test_whisper_turbo_cache.py`:
   - Test that `faster_whisper.WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", local_files_only=True)` loads without `IncompleteSnapshotError`.
   - Test that `TranscriptionEngine().transcribe(pcm, duration=2.0, model="turbo")` runs successfully, returns `backend_used="SYSTRAN/faster-whisper (turbo)"`, and does NOT fall back to Base.
4. Run tests:
   - `.venv\Scripts\python.exe -m unittest tests/test_whisper_turbo_cache.py`
   - Run full test suite `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"` to ensure zero regressions.
5. Record build and test results in `.agents/teamwork/worker_m2/handoff.md`.

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.


## 2026-10-30T17:07:55Z
You are Worker M2 for Milestone 2 (Whisper Turbo Model Cache Repair & Execution).
Read your dispatch instructions in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m2\DISPATCH.md
and the authoritative request in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
and project specification in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
and Explorer 2 findings in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_2\handoff.md

Your role is to:
1. Complete download of model.bin (1.61 GB) for deepdml/faster-whisper-large-v3-turbo-ct2 into the local HuggingFace cache.
2. Update scriber/transcription_engine.py to validate snapshot, dynamically select CUDA/CPU device, and execute true Large-v3-Turbo without falling back to Base.
3. Write and run tests/test_whisper_turbo_cache.py and full test suite.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliver your complete handoff report to:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m2\handoff.md
Notify the orchestrator when complete.
