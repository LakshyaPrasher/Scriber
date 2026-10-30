# BRIEFING — 2026-10-30T17:05:00Z

## Mission
Investigate Whisper Turbo model caching/fallback behavior and acoustic speaker diarization pipeline to plan upgrades to true Large-v3-Turbo and deep ONNX neural speaker embeddings (CAM++ / 3D-Speaker).

## 🔒 My Identity
- Archetype: explorer
- Roles: speech transcription & acoustic diarization pipeline investigator
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_2
- Original parent: c60e3390-79cc-45bf-a4ac-11c2f4785ada
- Milestone: survey & architecture analysis

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Produce 5-component handoff.md report
- Maintain progress.md heartbeat

## Current Parent
- Conversation ID: c60e3390-79cc-45bf-a4ac-11c2f4785ada
- Updated: 2026-10-30T17:05:00Z

## Investigation State
- **Explored paths**:
  - `scriber/transcription_engine.py`: Whisper model registry, fallback logic, Faster-Whisper integration
  - `C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2`: Incomplete snapshot analysis
  - `scriber/diarizer.py`: `SpeakerMemory`, `AcousticDiarizer`, AHC distance computation, continuity heuristics
  - `scriber/voice_clone.py`: `VoiceProfiler`, 16-d heuristic voice vector computation
  - `scriber/pipeline.py`: Pipeline orchestration of VAD, transcription, diarization, council
  - `welcomyou/campplus-3dspeaker-200k-onnx` and `csukuangfj/speaker-embedding-models`: CAM++ and 3D-Speaker ONNX models (28.2 MB, 192-d embeddings)
  - `onnxruntime` (1.31.0 installed in `.venv`) and `sherpa-onnx` (prebuilt Windows wheels on PyPI)
  - `tests/test_transcription_engine.py`, `tests/test_diarizer_accuracy.py`, `tests/suite_20_evaluator.py`: Verified test suites and requirements
- **Key findings**:
  - Whisper Turbo fallback root cause: `model.bin` (1.61 GB) in `C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2` is incomplete (truncated at 268 MB). `local_files_only=True` triggers `IncompleteSnapshotError`, caught by `except Exception:`, causing silent fallback to cached `base` model.
  - Acoustic Diarization: Currently relies on handcrafted 16-d DSP features (autocorrelation F0, spectral centroid, ZCR, sub-band energies) in `scriber/diarizer.py` and `scriber/voice_clone.py`. Upgrading to CAM++ (`campplus_cn_en_common_200k.onnx`, 28.2 MB, 192-d embeddings) via `onnxruntime` or `sherpa-onnx` provides deep neural speaker embeddings with VoxCeleb SOTA accuracy.
- **Unexplored areas**: None for this survey milestone.

## Key Decisions Made
- Confirmed dual execution route for neural diarization: Direct `onnxruntime` (already in `.venv`) with 80-bin Mel Fbank, with optional `sherpa-onnx` support and graceful DSP fallback.
- Confirmed single-step cache completion for Whisper Turbo via HuggingFace Hub snapshot download.

## Artifact Index
- DISPATCH.md — Task instructions
- BRIEFING.md — Situational awareness
- progress.md — Liveness heartbeat
- handoff.md — Complete 5-component survey report
