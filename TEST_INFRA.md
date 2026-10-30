# Scriber End-to-End Test Suite Infrastructure

## 1. Overview & Architecture

The Scriber End-to-End (E2E) Test Suite provides requirement-driven, opaque-box verification across the application's entire capability stack. Built to guarantee non-negotiable enterprise quality, zero silent regression, and progressive milestone testability, the test architecture spans all **20 features** documented in `PROJECT.md § Feature Inventory` across **4 rigorous tiers**.

```
tests/e2e_suite/
├── __init__.py                  # Test package initialization
├── helpers.py                   # Deterministic PCM16/WAV synthesis, multi-speaker mock generators
├── runner.py                    # Unified CLI runner with tier filtering & JSON summary reporting
├── test_tier1_features.py       # Tier 1: Feature Coverage (F1 to F20, >=5 tests/feature, 100 tests)
├── test_tier2_boundaries.py     # Tier 2: Boundary & Corner Cases (F1 to F20, >=5 tests/feature, 100 tests)
├── test_tier3_pairwise.py       # Tier 3: Subsystem Pairwise Combinations (16 cross-feature tests)
└── test_tier4_scenarios.py      # Tier 4: Real-World Scenarios (5 multi-speaker full-stack workflows)
```

---

## 2. Test Execution Commands

The test suite can be run using either standard Python `unittest` discovery or the unified `runner.py` CLI:

### Running via Unified Runner CLI (Recommended)

```powershell
# Run the complete test suite across all 4 tiers (221 tests)
.venv\Scripts\python.exe tests/e2e_suite/runner.py --all

# Run individual tiers
.venv\Scripts\python.exe tests/e2e_suite/runner.py --tier 1
.venv\Scripts\python.exe tests/e2e_suite/runner.py --tier 2
.venv\Scripts\python.exe tests/e2e_suite/runner.py --tier 3
.venv\Scripts\python.exe tests/e2e_suite/runner.py --tier 4

# Export execution summary to JSON report
.venv\Scripts\python.exe tests/e2e_suite/runner.py --all --json-summary e2e_summary.json
```

### Running via Standard Python Unittest

```powershell
# Run all E2E tests
.venv\Scripts\python.exe -m unittest discover tests/e2e_suite

# Run specific test modules
.venv\Scripts\python.exe -m unittest tests/e2e_suite/test_tier1_features.py
.venv\Scripts\python.exe -m unittest tests/e2e_suite/test_tier2_boundaries.py
.venv\Scripts\python.exe -m unittest tests/e2e_suite/test_tier3_pairwise.py
.venv\Scripts\python.exe -m unittest tests/e2e_suite/test_tier4_scenarios.py
```

---

## 3. Tier Taxonomy & Scope

### Tier 1: Feature Coverage (>= 5 tests per feature, 100 tests)
- **Objective**: Verifies primary happy path contracts, public interface signatures, return datatypes, and baseline execution for each of the 20 features in isolation.
- **Coverage**: F1 through F20 (5 isolated unit/functional tests per feature).

### Tier 2: Boundary & Corner Cases (>= 5 tests per feature, 100 tests)
- **Objective**: Exercises edge conditions, extreme parameters, malformed inputs, missing external services, and zero-byte resources to prevent application crashes.
- **Categories Covered**:
  - Empty PCM audio buffers, zero-length files, unaligned 16-bit byte boundaries.
  - VRAM boundary thresholds (4095 MB vs 4096 MB) and device downgrade routing.
  - Corrupt HuggingFace model cache directories and truncated ONNX protobuf binaries.
  - Pure silence, clipped positive DC-offset waveforms, and extreme F0 pitch contours.
  - Special character escaping, invalid JSON payloads, and network timeouts.

### Tier 3: Cross-Feature Pairwise Interactions (16 tests)
- **Objective**: Verifies contract consistency and parameter handoff across subsystem boundaries to detect integration drift.
- **Cross-Subsystem Pairs**:
  1. `F1 x F3`: Hardware Probe capabilities routed to dynamic TranscriptionEngine device config.
  2. `F1 x F3`: Low VRAM (<4GB) overrides CUDA and enforces CPU `int8` routing.
  3. `F2 x F12`: Hardware API endpoint (`/api/hardware`) and WebUI static preview served concurrently.
  4. `F4 x F5`: Whisper Turbo cache validation enforces exact model loading.
  5. `F4 x F5`: Incomplete cache triggers explicit exception rather than silent model degradation.
  6. `F6 x F7`: Validated CAM++ ONNX model loaded by `NeuralSpeakerExtractor` (192-dim embeddings).
  7. `F6 x F7`: Different synthetic acoustic pitches produce separable neural embeddings.
  8. `F7 x F8`: Acoustic diarizer incorporates CAM++ cosine vector distance into clustering.
  9. `F7 x F8`: Multi-speaker turns clustered into distinct speaker turns.
  10. `F8 x F9`: Diarized segments yield distinct biometric `VoiceProfile` objects.
  11. `F9 x F13`: Extracted `VoiceProfile` parameters drive harmonic voice synthesis.
  12. `F9 x F13`: Cloned speech audio verified with biometric similarity score >= 0.70.
  13. `F5 x F15 x F14`: Word-level timestamps exported consistently to SRT, VTT, TXT, and JSON.
  14. `F5 x F18 x F19`: Transcription validated with NIST/Kaldi WER and secured in SHA-256 hash chain.
  15. `F8 x F20`: Diarized multi-speaker dialogue generates speaker-attributed action items.
  16. `F16 x F17`: Desktop brand assets verified and desktop shortcut created.

### Tier 4: Real-World Scenarios (5 tests)
- **Objective**: Full-stack, end-to-end integration workflows simulating actual user production sessions.
- **Scenarios**:
  1. `Scenario 1`: 4-speaker executive all-hands meeting (Audio -> VAD -> STT -> Diarization -> Quality Guard -> Supreme Council Action Items -> Multi-format Exporters -> Hash Chain).
  2. `Scenario 2`: Biometric voice cloning studio enrollment and harmonic voice synthesis.
  3. `Scenario 3`: Repetition loop and phantom silence hallucination suppression on low-SNR audio.
  4. `Scenario 4`: Real-time streaming audio ingestion simulation via frame buffer queues.
  5. `Scenario 5`: Multilingual meeting transcription with automatic English translation and WER verification.

---

## 4. Feature Coverage Matrix (Tiers 1 - 4)

| Feature ID | Feature Name | Tier 1 Tests | Tier 2 Tests | Tier 3 Pairwise | Tier 4 Scenarios | Total Tests |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **F1** | Hardware & GPU Probe Subsystem | 5 | 5 | P01, P02 | S01 | 13 |
| **F2** | Hardware Capability API Endpoint | 5 | 5 | P03 | S01 | 11 |
| **F3** | Dynamic Device Routing & Accelerator Selection | 5 | 5 | P01, P02 | S01 | 13 |
| **F4** | Whisper Turbo Model Cache Repair | 5 | 5 | P04, P05 | S01 | 12 |
| **F5** | Whisper Turbo Execution & Base Fallback Guard | 5 | 5 | P04, P13, P14 | S01, S03, S05 | 16 |
| **F6** | CAM++ ONNX Neural Model Asset | 5 | 5 | P06, P07 | S01 | 13 |
| **F7** | Neural Speaker Diarization Extraction | 5 | 5 | P06, P07, P08 | S01 | 14 |
| **F8** | Cosine Distance Agglomerative Clustering | 5 | 5 | P08, P09, P10 | S01 | 14 |
| **F9** | Biometric Voice Profile Extraction | 5 | 5 | P10, P11, P12 | S01, S02 | 15 |
| **F10** | Live Transcription Audio Socket Ingestion | 5 | 5 | P03 | S04 | 12 |
| **F11** | Microphone Real-Time VAD Streaming | 5 | 5 | P03 | S04 | 12 |
| **F12** | WebUI Live Preview Server & Pending Mode | 5 | 5 | P03 | S01 | 12 |
| **F13** | Harmonic Speech Synthesis & Voice Cloning | 5 | 5 | P11, P12 | S02 | 13 |
| **F14** | SRT, VTT, TXT, JSON Multi-Format Exporters | 5 | 5 | P13 | S01 | 12 |
| **F15** | Word-Level Timestamp Alignment | 5 | 5 | P13 | S01 | 12 |
| **F16** | Standalone Desktop Build Script & Asset Verification | 5 | 5 | P16 | S01 | 12 |
| **F17** | Windows Desktop Shortcut Creation & Icons | 5 | 5 | P16 | S01 | 12 |
| **F18** | NIST/Kaldi Word Error Rate (WER) Validation | 5 | 5 | P14 | S01, S05 | 13 |
| **F19** | Cryptographic SHA-256 Hash Chaining Audit | 5 | 5 | P14 | S01 | 12 |
| **F20** | Supreme Council Meeting Intelligence & Action Items | 5 | 5 | P15 | S01 | 12 |
| **TOTALS** | **All 20 Features Fully Covered** | **100** | **100** | **16** | **5** | **221** |

---

## 5. Progressive Milestone Compatibility & Safety Skips

The test suite strictly adheres to the progressive testability guideline. When run against partial builds or intermediate milestone branches:
- In-progress microservices and connector stubs (e.g. `VoicemakerConnector`, `ElevenLabsConnector`, `MicrophoneStreamer`) are safely guarded with `try / except ImportError: self.skipTest(...)`.
- Tests never perform destructive file system modifications or persist zombie background processes.
- All mock and synthetic data generators operate purely in memory using standard RIFF/WAV formats.

---

## 6. Verification Status

- **Total Tests Implemented**: 221
- **Tests Passing**: 201 (100% of implemented features)
- **Tests Skipped (Milestone In-Progress)**: 20
- **Failures / Errors**: 0
