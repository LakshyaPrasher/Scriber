# Original User Request

## Initial Request — 2026-10-30T16:52:39Z

Perfect the Scriber native desktop application by assessing hardware and GPU availability, overhauling voice cloning with local neural models or cloud API bridges, upgrading acoustic speaker diarization, repairing the Whisper Turbo model cache, and deploying the resulting changes locally and to GitHub.

Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber
Integrity mode: development

## Requirements

### R1. GPU & Hardware Capability Assessment
Inspect the host Windows system to gauge GPU availability (evaluating VRAM, compute capability, CUDA, and DirectX) and determine the operational effectiveness of running local neural models versus cloud API bridges.

### R2. Voice Cloning Overhaul
Implement voice cloning at the level of Voicemaker.in:
- When a dedicated NVIDIA GPU is present, implement a local zero-shot flow-matching / speech LLM architecture (such as F5-TTS or ChatterBox) via a companion microservice.
- For all systems and instant studio parity, provide direct cloud voice cloning connectors supporting both Voicemaker.in and ElevenLabs with 48kHz neural synthesis and clean local fallback.

### R3. Speaker Segregation & Diarization
Upgrade acoustic diarization to use deep ONNX neural speaker embeddings (CAM++ / 3D-Speaker via sherpa-onnx/onnxruntime) to eliminate over-grouping and over-segregating of speakers.

### R4. Transcription Model Cache
Complete and repair the Whisper Turbo model cache so it executes true Large-v3-Turbo without falling back to Base.

### R5. Verification, Build & Deployment
Verify changes with automated tests using local or synthetic test audio, rebuild the desktop executable bundle, update the desktop shortcut, and push all commits directly to the current checked-out branch on the remote origin repository.

## Acceptance Criteria

### Hardware Assessment
- [ ] Hardware capability detection accurately identifies GPU availability, VRAM, and compute capability, and routes appropriately between local execution and cloud fallbacks.

### Voice Cloning
- [ ] Local zero-shot voice cloning microservice functions when supported GPU hardware is available.
- [ ] Cloud connectors for Voicemaker.in and ElevenLabs are implemented with 48kHz neural synthesis and automatic fallback handling.

### Speaker Diarization
- [ ] Acoustic diarization pipeline runs with deep ONNX neural speaker embeddings (CAM++ / 3D-Speaker) without falling back to basic centroid/continuity heuristics alone.

### Transcription
- [ ] Whisper Large-v3-Turbo executes directly from the repaired model cache and does not fall back to the Base model.

### Build & Repository
- [ ] Automated test suite runs and passes.
- [ ] Standalone desktop executable bundle is built and the desktop shortcut is updated.
- [ ] All code changes are committed and pushed to the current branch on the remote GitHub origin repository.
