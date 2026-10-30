# Task Assignment: Replacement Worker M3 — Acoustic Diarization ONNX Neural Upgrade Completion

- Role: Milestone 3 Completion Worker
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3_2\
- Authoritative Request: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
- Scope Document: c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
- Predecessor Progress: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3\progress.md

## Interruption Point & Completed Work
Predecessor `worker_m3` successfully completed:
1. Downloaded and verified CAM++ ONNX model asset (`scriber/assets/models/campplus_cn_en_common_200k.onnx`, 28.28 MB).
2. Implemented `NeuralSpeakerExtractor` with 80-bin Mel Fbank + frame CMVN in `scriber/diarizer.py`.
3. Upgraded `compute_acoustic_distance` with cosine distance and 0.60x continuity prior.
4. Upgraded `SpeakerMemory` for 192-d centroid unit vector updates.
5. Upgraded `AcousticDiarizer.diarize_segments` with silence gap pre-splitting and calibrated AHC clustering.
6. Created `tests/test_diarizer_onnx.py`.

## Remaining Tasks for Replacement Worker
1. Run and verify tests:
   - `.\.venv\Scripts\python.exe -m unittest tests/test_diarizer_onnx.py`
   - `.\.venv\Scripts\python.exe -m unittest tests/test_diarizer_accuracy.py`
   - `.\.venv\Scripts\python.exe -m unittest tests.e2e_suite.test_tier1_features.TestTier1F6CAMPlusONNXModel tests.e2e_suite.test_tier1_features.TestTier1F7NeuralSpeakerDiarization tests.e2e_suite.test_tier1_features.TestTier1F8CosineAgglomerativeClustering`
2. Ensure all diarization tests pass cleanly with 0 errors.
3. Write your complete 5-section handoff report to `c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3_2\handoff.md`.
4. Send a message to the orchestrator when finished.

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## 2026-10-30T20:48:21Z
[Message] sender=c60e3390-79cc-45bf-a4ac-11c2f4785ada priority=MESSAGE_PRIORITY_HIGH
You are replacement Worker M3 (Acoustic Diarization ONNX Neural Upgrade Completion).
Read your dispatch instructions in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3_2\DISPATCH.md
and the authoritative request in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
and project specification in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md

Your role is to verify the CAM++ ONNX neural diarization implementation:
1. Run and verify tests: tests/test_diarizer_onnx.py, tests/test_diarizer_accuracy.py, and E2E diarization tests.
2. Deliver your complete handoff report to:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3_2\handoff.md
Notify the orchestrator when complete.
