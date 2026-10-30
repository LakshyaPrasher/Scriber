# Orchestration Plan — Scriber Native Desktop Application Perfection

## Objectives
1. **GPU & Hardware Capability Assessment**: System inspection (VRAM, compute capability, CUDA, DirectX), automatic routing between local microservice and cloud bridges.
2. **Voice Cloning Overhaul**: Local zero-shot flow-matching/speech LLM (F5-TTS/ChatterBox) via companion microservice when dedicated NVIDIA GPU is present; cloud connectors for Voicemaker.in and ElevenLabs with 48kHz neural synthesis and clean fallback.
3. **Speaker Segregation & Diarization**: Deep ONNX neural speaker embeddings (CAM++ / 3D-Speaker via sherpa-onnx / onnxruntime) replacing basic centroid heuristics.
4. **Transcription Model Cache**: Complete and repair Whisper Large-v3-Turbo model cache so it executes without falling back to Base.
5. **Verification, Build & Deployment**: Automated test suite, standalone executable rebuild, desktop shortcut update, and git push to remote origin.

## Phases
- **Phase 0: Survey (Parallel Exploration)**
  - Explorer 1: Codebase structure, entry points, current hardware detection, and packaging/desktop shortcut setup.
  - Explorer 2: Audio engine, diarization pipeline (CAM++/3D-Speaker ONNX), Whisper model cache / loader logic.
  - Explorer 3: Voice cloning architecture, Voicemaker.in & ElevenLabs integration, local companion microservice design.
- **Phase 1: Project & Test Specification**
  - Merge findings into `PROJECT.md` (Feature Inventory, Architecture, Milestones, Interface Contracts, Code Layout).
  - Spawn E2E Testing Orchestrator / Test suite framework.
- **Phase 2: Milestone Execution (Iterative / Sub-orchestrators)**
  - M1: Hardware & GPU Detection & Routing
  - M2: Whisper Turbo Model Cache Repair
  - M3: Speaker Segregation & Diarization (CAM++ / 3D-Speaker ONNX)
  - M4: Voice Cloning Overhaul (Local Microservice + Cloud APIs)
- **Phase 3: Integration, E2E Verification & Adversarial Hardening**
  - Complete test suite pass (Tiers 1-4)
  - Adversarial hardening (Tier 5)
- **Phase 4: Build, Packaging & Remote Deployment**
  - Standalone desktop executable rebuild
  - Desktop shortcut update
  - Git commit and push to remote origin
  - Final human report
