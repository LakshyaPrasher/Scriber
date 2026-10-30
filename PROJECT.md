# Project: Scriber Native Desktop Application Perfection

## Architecture
- **Framework**: Hybrid native desktop studio combining a standard library Python HTTP backend server (`http.server.SimpleHTTPRequestHandler` / `ThreadingTCPServer`), Microsoft Edge WebView2 GUI window manager (`pywebview` with Per-Monitor High-DPI V2 and custom Python-JS bridge), and an embedded dark luxury frontend (`Dark Obsidian #08090C`, `Tangerine #FF5E00`, `Antique Gold #FFA826`).
- **Hardware Routing Engine**: In-process NVML (`nvml.dll`), Direct3D 12 (`d3d12.dll`), and CTranslate2 CUDA probes detecting NVIDIA GPU, total/free VRAM, CUDA compute capability, and DirectX feature levels; intelligently routes between local GPU execution and cloud API bridges.
- **Speech Transcription Pipeline**: Faster-Whisper / CTranslate2 INT8 transformer engine executing Whisper Large-v3-Turbo (`deepdml/faster-whisper-large-v3-turbo-ct2`) with dynamic GPU CUDA/CPU device selection and snapshot validation.
- **Speaker Diarization Engine**: Deep ONNX neural speaker embeddings (CAM++ `campplus_cn_en_common_200k.onnx`, 192-d unit-normalized vectors) via `onnxruntime` with 80-bin Mel-filterbank, cosine distance agglomerative hierarchical clustering, and conversational continuity priors; resilient fallback to 16-d acoustic DSP features.
- **Voice Cloning & Synthesis Subsystem**:
  - *Tier 1 (Local GPU)*: Out-of-process companion microservice (`scriber.services.voice_microservice` on loopback `127.0.0.1:18840`) executing zero-shot flow-matching / speech LLM (F5-TTS DiT + 48kHz Vocos vocoder) on dedicated NVIDIA GPU (RTX 5050 8GB).
  - *Tier 2 (Cloud Studio)*: Direct REST connectors for Voicemaker.in (`AudioSampleRate: 48000`, `Engine: "neural"`) and ElevenLabs (`output_format: pcm_48000`, Instant Voice Clone with audio hash caching).
  - *Tier 3 (Edge-TTS)*: Microsoft Edge Neural TTS with Mel-filterbank timbre transfer and 48kHz polyphase sinc upsampling.
  - *Tier 4 (Offline Fallback)*: Parametric 2nd-order biquad IIR formant vocoder with Rosenberg glottal pulse excitation.
  - *Dual-Rate Audio*: 16kHz for Whisper transcription and acoustic profiling; 48kHz for synthesis, visualizer, playback, and MP3 export.
- **Packaging & Desktop Distribution**: PyInstaller standalone portable directory bundle (`dist/Scriber/`) with Subsystem 2 (GUI, no console window) enforcement, multi-resolution `.ico` generation, and Windows desktop/Start Menu shortcut automation (`make_shortcut.py` & `scripts/install_windows_shortcuts.ps1`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Hardware & GPU Probe | In-process detection of NVIDIA GPU, total/free VRAM, compute capability, CUDA driver version, and DirectX 12 feature level | M1 | Survey (Explorer 1) / R1 |
| F2 | Hardware API Endpoint | HTTP endpoint `/api/hardware` exposing real-time GPU/CPU capabilities, VRAM, and recommended engine routes | M1 | Survey (Explorer 1) / R1 |
| F3 | Dynamic Device Routing | Route CTranslate2 transcription engine between `cuda` (when dedicated GPU with $\ge 4$GB VRAM present) and `cpu` | M1 | Survey (Explorer 1) / R1 |
| F4 | Whisper Turbo Model Cache Repair | Download and verify complete `model.bin` (1.61 GB) in HuggingFace hub cache for `deepdml/faster-whisper-large-v3-turbo-ct2` | M2 | Survey (Explorer 2) / R4 |
| F5 | Whisper Turbo Execution & Validation | Ensure `WhisperModel` executes Large-v3-Turbo without raising `IncompleteSnapshotError` or falling back to Base | M2 | Survey (Explorer 2) / R4 |
| F6 | CAM++ ONNX Neural Model Asset | Place 28.2 MB CAM++ model asset (`campplus_cn_en_common_200k.onnx`) in `scriber/assets/models/` | M3 | Survey (Explorer 2) / R3 |
| F7 | Neural Speaker Embedding Extractor | 80-bin Mel Fbank extractor + ONNX Runtime inference producing 192-d unit-normalized speaker vectors | M3 | Survey (Explorer 2) / R3 |
| F8 | Deep Embedding Diarizer Clustering | Cosine distance AHC clustering with conversational continuity discount in `AcousticDiarizer` and `SpeakerMemory` | M3 | Survey (Explorer 2) / R3 |
| F9 | Diarization Heuristic Fallback | Graceful fallback to 16-d DSP voice vector when ONNX model is unavailable | M3 | Survey (Explorer 2) / R3 |
| F10 | Local Flow-Matching Companion Microservice | Lightweight out-of-process daemon on `127.0.0.1:18840` for zero-shot neural synthesis on dedicated NVIDIA GPU | M4 | Survey (Explorer 3) / R2 |
| F11 | Voicemaker.in Cloud Connector | Direct REST client for Voicemaker.in neural engine supporting 48,000 Hz synthesis | M4 | Survey (Explorer 3) / R2 |
| F12 | ElevenLabs Cloud Connector | Direct REST client for ElevenLabs TTS and Instant Voice Clone with 48,000 Hz PCM streaming | M4 | Survey (Explorer 3) / R2 |
| F13 | 4-Tier Voice Synthesis Fallback Matrix | Resilient fallback chain: Local GPU $\rightarrow$ Cloud Studio $\rightarrow$ Edge-TTS $\rightarrow$ Offline Vocoder | M4 | Survey (Explorer 3) / R2 |
| F14 | 48kHz Dual-Rate Audio Pipeline | Dual-rate management (16kHz analysis, 48kHz synthesis) with miniaudio/PyAV resampling and MP3 export | M4 | Survey (Explorer 3) / R2 |
| F15 | Voice API & UI Studio Integration | Server endpoints `/api/clone-voice` & credentials handling, plus frontend model selection in UI | M4 | Survey (Explorer 3) / R2 |
| F16 | Empty Profile Similarity Calibration | Fix baseline similarity calculation in `calculate_similarity` to prevent false unit test failures on non-reference prompts | M4 | Survey (Explorer 3) / R2 |
| F17 | Comprehensive Test Suite Pass | Verify all unit and integration tests (existing 128 tests + new test suites) pass with zero errors | M5 | Survey (Explorer 1) / R5 |
| F18 | Standalone Desktop Executable Packaging | Run PyInstaller `build_desktop.py` to compile Subsystem 2 GUI bundle into `dist/Scriber/` | M5 | Survey (Explorer 1) / R5 |
| F19 | Windows Desktop Shortcut Automation | Run `make_shortcut.py` and `scripts/install_windows_shortcuts.ps1` to refresh desktop and Start Menu shortcuts | M5 | Survey (Explorer 1) / R5 |
| F20 | Remote Git Repository Synchronization | Commit all verified changes and push directly to `origin/main` on remote GitHub repository | M5 | Survey (Explorer 1) / R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Hardware & GPU Capability Assessment | Implement `scriber/hardware.py`, NVML/D3D12/CUDA probes, `/api/hardware` endpoint, and dynamic device selection in transcription engine | none | DONE |
| M2 | Whisper Turbo Model Cache Repair | Download complete `model.bin` for `deepdml/faster-whisper-large-v3-turbo-ct2`, add snapshot verification in `transcription_engine.py`, eliminate Base fallback | none | DONE |
| M3 | Acoustic Diarization ONNX Neural Upgrade | Place CAM++ ONNX model asset, implement 80-bin Mel Fbank extractor + ONNX session in `scriber/diarizer.py`, upgrade `SpeakerMemory` and AHC clustering to 192-d cosine distance | none | DONE |
| M4 | Voice Cloning Overhaul & Cloud Connectors | Implement local GPU companion microservice, Voicemaker.in & ElevenLabs 48kHz connectors, 4-tier fallback matrix, dual-rate audio processing, UI/server integration | M1 | DONE |
| M5 | Verification, Executable Packaging & GitHub Push | Run automated test suite, rebuild desktop executable bundle (`dist/Scriber`), update desktop shortcuts, commit and push to remote origin | M1, M2, M3, M4 | PLANNED |

## Interface Contracts

### Hardware Module (`scriber.hardware`) ↔ Transcription & Voice Subsystems
- **Functions**:
  - `get_hardware_capabilities() -> HardwareCapabilities`
    - Returns dataclass: `gpu_name: Optional[str]`, `vram_total_mb: float`, `vram_free_mb: float`, `compute_capability: Tuple[int, int]`, `cuda_available: bool`, `cuda_version: str`, `directx_12_supported: bool`, `directx_feature_level: str`, `recommended_device: str` (`"cuda"` or `"cpu"`), `recommended_compute_type: str` (`"float16"`, `"int8_float16"`, or `"int8"`), `supports_local_speech_llm: bool` (True if NVIDIA GPU with VRAM free $\ge 3500$ MB).
  - `get_transcription_device_config() -> Tuple[str, str]`
    - Returns `(device, compute_type)` e.g. `("cuda", "float16")` or `("cpu", "int8")`.

### Diarization Subsystem (`scriber.diarizer`) ↔ Pipeline & Transcription
- **Classes & Functions**:
  - `NeuralSpeakerExtractor.extract_embedding(pcm16_bytes: bytes, sample_rate: int = 16000) -> np.ndarray`
    - Input: 16-bit mono PCM bytes, $\ge 0.25$ seconds.
    - Output: 1D `np.ndarray` of shape `(192,)`, $L_2$-normalized ($||\mathbf{v}||_2 = 1.0$).
    - Fallback: If ONNX model missing, returns 16-d normalized DSP voice vector.
  - `compute_acoustic_distance(p1: VoiceProfile, p2: VoiceProfile) -> float`
    - Cosine distance: $1.0 - \max(0.0, \mathbf{v}_1 \cdot \mathbf{v}_2)$ when 192-d embeddings are present.
  - `AcousticDiarizer.diarize_segments(...) -> List[TranscriptionSegment]`
    - Emits segments with updated `speaker` identifiers using neural clustering.

### Voice Subsystem (`scriber.voice_clone`) ↔ Web Server & Desktop Bridge
- **Classes & Functions**:
  - `VoiceCloner.clone_voice(text: str, profile: Optional[VoiceProfile] = None, reference_audio_pcm: Optional[bytes] = None, backend: str = "auto", sample_rate: int = 48000, **kwargs) -> VoiceCloneResult`
    - Returns `VoiceCloneResult`: `audio_pcm16: bytes`, `sample_rate_hz: int = 48000`, `similarity_score: float`, `synthesis_backend: str`, `provider: str`, `fallback_chain: List[str]`, `audio_base64: str`, `duration: float`.
  - Connectors:
    - `VoicemakerConnector.synthesize(text: str, voice_id: str = "ai3-Jony", api_key: Optional[str] = None) -> Tuple[bytes, int]`
    - `ElevenLabsConnector.synthesize(text: str, voice_id: Optional[str] = None, ref_audio_pcm: Optional[bytes] = None, api_key: Optional[str] = None) -> Tuple[bytes, int]`
    - `VoiceMicroserviceManager.synthesize(text: str, ref_audio_pcm: bytes, ref_text: str = "") -> Tuple[bytes, int, float]`

## Code Layout
```
scriber/
├── __init__.py
├── __main__.py
├── audio_editor.py          # Miniaudio & PyAV processing, 16k <-> 48k resampling
├── desktop.py               # WebView2 window manager, High-DPI V2, AppUserModelID
├── diarizer.py              # CAM++ ONNX neural speaker embeddings & AHC clustering
├── hardware.py             # NVML, D3D12, CUDA, VRAM detection & device routing
├── models.py                # Dataclasses (HardwareCapabilities, VoiceProfile, etc.)
├── pipeline.py              # End-to-end multimedia orchestration pipeline
├── transcription_engine.py  # Faster-Whisper Large-v3-Turbo cache validation & CUDA execution
├── voice_clone.py           # Multi-tier voice cloning (Microservice, Cloud, Edge-TTS, Vocoder)
├── assets/
│   ├── icon.ico
│   ├── icon.png
│   └── models/
│       └── campplus_cn_en_common_200k.onnx  # 28.2 MB CAM++ neural speaker model
├── services/
│   ├── __init__.py
│   └── voice_microservice.py  # Local zero-shot flow-matching companion daemon
└── web/
    ├── server.py            # Pure standard library HTTP REST server & API endpoints
    └── ui.py                # Embedded Dark Obsidian & Tangerine studio UI
```
