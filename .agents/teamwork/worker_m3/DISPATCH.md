# Task Assignment: Worker M3 — Acoustic Diarization ONNX Neural Upgrade

- Role: Milestone 3 Implementation Worker
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3\
- Authoritative Request: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
- Scope Document: c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
- Explorer Findings: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_2\handoff.md

## Scope & File Ownership
You exclusively own:
- `scriber/assets/models/campplus_cn_en_common_200k.onnx` (CAM++ ONNX model asset)
- `scriber/diarizer.py` (neural speaker embedding extractor, ONNX inference, cosine distance clustering, continuity discount, heuristic fallback)
- `tests/test_diarizer_onnx.py` (ONNX inference and neural clustering unit tests)

## Requirements
1. Acquire the CAM++ ONNX model asset:
   - Target model: `campplus_cn_en_common_200k.onnx` (~28.2 MB). Download from reliable repository (e.g. `csukuangfj/speaker-embedding-models` on Hugging Face / ModelScope / GitHub releases) and place in `scriber/assets/models/campplus_cn_en_common_200k.onnx`.
   - Verify file exists, size is ~28.2 MB, and loads into `onnxruntime.InferenceSession` with input shape `[1, T, 80]` and output shape `[1, 192]`.
2. Implement Deep ONNX Neural Speaker Embeddings in `scriber/diarizer.py`:
   - Create `NeuralSpeakerExtractor`:
     - Computes 80-bin log mel-filterbank features with CMVN from 16kHz mono audio PCM frames.
     - Runs `onnxruntime.InferenceSession` (using `CPUExecutionProvider` or DirectML/CUDA if available) to extract 192-dimensional unit-normalized ($L_2 = 1.0$) speaker embeddings.
     - Optional acceleration via `sherpa-onnx` if installed, with primary in-process execution via `onnxruntime` (which is already installed in `.venv` 1.31.0).
     - Graceful fallback: If ONNX model is missing or fails, falls back cleanly to the existing 16-d DSP voice vector from `VoiceProfiler`.
   - Upgrade `compute_acoustic_distance(p1, p2)`:
     - For 192-d neural embeddings, compute cosine distance: $1.0 - \max(0.0, \mathbf{u} \cdot \mathbf{v})$.
     - Preserve conversational continuity discount ($0.60 \times$) for consecutive speaker segments.
   - Upgrade `SpeakerMemory`:
     - Maintain 192-d normalized centroid vector.
   - Upgrade `AcousticDiarizer.diarize_segments`:
     - Extract neural embeddings for all speech segments $\ge 0.25$s.
     - Run Agglomerative Hierarchical Clustering (AHC) using neural cosine distance matrix with calibrated threshold (e.g. ~0.45 - 0.55).
3. Test and Verify:
   - Create `tests/test_diarizer_onnx.py` testing ONNX model loading, 192-d shape, cosine distance, and clustering.
   - Run `tests/test_diarizer_accuracy.py` and `tests/suite_20_evaluator.py`.
   - Ensure all 20 benchmark samples pass (20/20 PASS, 100.0%) with 0.0% false fragmentation.
   - Run full test suite `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"` to guarantee zero regressions.
4. Record build and test results in `.agents/teamwork/worker_m3/handoff.md`.

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.


## 2026-10-30T17:08:17Z
You are Worker M3 for Milestone 3 (Acoustic Diarization ONNX Neural Upgrade).
Read your dispatch instructions in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3\DISPATCH.md
and the authoritative request in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
and project specification in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
and Explorer 2 findings in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_2\handoff.md

Your role is to:
1. Download CAM++ ONNX model asset (28.2 MB) into scriber/assets/models/campplus_cn_en_common_200k.onnx.
2. Implement 80-bin Mel Fbank extractor + ONNX session in scriber/diarizer.py for 192-d speaker embeddings.
3. Upgrade SpeakerMemory, compute_acoustic_distance (cosine distance), and AcousticDiarizer AHC clustering to use neural embeddings with continuity priors and heuristic fallback.
4. Verify with tests/test_diarizer_onnx.py, tests/suite_20_evaluator.py (20/20 PASS), and full test suite.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliver your complete handoff report to:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3\handoff.md
Notify the orchestrator when complete.


## 2026-10-30T17:40:03Z
**Context**: Milestone 3 Status Check
**Content**: Checking in on Milestone 3 progress. We noticed `NeuralSpeakerExtractor` and `tests/test_diarizer_onnx.py` are in place. Please complete the benchmark evaluations and write your handoff report to `.agents/teamwork/worker_m3/handoff.md`.
**Action**: Send your completion report when finished.

## 2026-10-30T17:59:00Z
Context: Milestone 3 Status Query
Content: We are checking in on worker_m3. The 20-sample benchmark report was partially generated earlier. Please complete the benchmark evaluation, run unit tests, and provide your handoff report to .agents/teamwork/worker_m3/handoff.md.
Action: Please report status or deliver handoff.
