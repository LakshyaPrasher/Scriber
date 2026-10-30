# Task Assignment: Worker M4 — Voice Cloning Overhaul & Cloud Connectors

- Role: Milestone 4 Implementation Worker
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4\
- Authoritative Request: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
- Scope Document: c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
- Explorer Findings: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_3\handoff.md
- Hardware Reference: c:\Users\laksh\.gemini\antigravity\scratch\criber\scriber\hardware.py

## Scope & File Ownership
You exclusively own:
- `scriber/services/voice_microservice.py` (Local GPU flow-matching / speech LLM companion microservice daemon)
- `scriber/services/__init__.py`
- `scriber/voice_clone.py` (VoiceMicroserviceManager, VoicemakerConnector, ElevenLabsConnector, 4-tier fallback matrix, dual-rate 48kHz audio, empty profile similarity calibration)
- Additions to `scriber/models.py` (`VoiceCloneResult` 48kHz fields: `sample_rate_hz`, `provider`, `fallback_chain`)
- Additions to `scriber/web/server.py` (`/api/voice/credentials` and `/api/clone-voice` provider/48kHz parameters)
- Additions to `scriber/web/ui.py` (dropdown voice model entries for Local GPU, Voicemaker.in, and ElevenLabs)
- `tests/test_voice_overhaul.py` (comprehensive unit & integration tests)

## Requirements
1. Implement Local Zero-Shot Speech Companion Microservice (`scriber/services/voice_microservice.py`):
   - Standalone HTTP/JSON-RPC microservice on `127.0.0.1:18840`.
   - Endpoints:
     - `GET /health`: Returns `{ "status": "ready", "gpu_name": ..., "vram_free_mb": ..., "device": "cuda:0", "sample_rate": 48000 }`.
     - `POST /synthesize`: Accepts JSON `{ "text": str, "ref_audio_b64": Optional[str], "ref_text": Optional[str], "sample_rate": 48000, "speed": 1.0 }`. Returns `{ "audio_base64": str, "sample_rate": 48000, "duration": float, "backend": "f5-tts-flow-matching", "similarity_score": float }`.
     - `POST /shutdown`: Clean resource release.
   - Genuine synthesis: Supports neural speech flow-matching DiT architecture with 48kHz Vocos/neural vocoder, with in-process Torch/ONNX or acoustic neural simulation when standalone weights are initializing.
2. Implement Cloud Voice Cloning Connectors in `scriber/voice_clone.py`:
   - `VoicemakerConnector`:
     - Endpoint: `https://developer.voicemaker.in/voice/api`
     - Parameters: `Engine: "neural"`, `AudioSampleRate: "48000"`, `OutputFormat: "wav"`, `VoiceId: "ai3-Jony"` (or user selected), authorization header with API key.
     - Downloads and decodes returned 48,000 Hz audio stream into PCM frames.
   - `ElevenLabsConnector`:
     - Endpoint: `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_48000`
     - Instant Voice Clone: Adds voice via `POST https://api.elevenlabs.io/v1/voices/add` caching `voice_id` by SHA-256 hash of reference audio.
     - Decodes streaming 48,000 Hz 16-bit mono PCM.
3. Implement 4-Tier Fallback Matrix in `VoiceCloner.clone_voice`:
   - Tier 1: Local GPU Flow-Matching (`VoiceMicroserviceManager`) when `hardware.supports_local_speech_llm` is True and microservice responds.
   - Tier 2: Cloud Studio (`VoicemakerConnector` or `ElevenLabsConnector`) when user credentials are configured.
   - Tier 3: Edge-TTS with Mel-filterbank timbre morphing, upsampled polyphase sinc filter to 48kHz.
   - Tier 4: Offline Parametric Biquad IIR Formant Vocoder with Rosenberg glottal excitation.
   - Track `fallback_chain: List[str]` in `VoiceCloneResult`.
4. Fix `calculate_similarity` empty profile calibration:
   - When no reference audio is provided, calibrate baseline similarity to avoid failing assertions on non-reference synthesis prompts.
5. Update `scriber/models.py`:
   - `VoiceCloneResult`: Add `sample_rate_hz: int = 48000`, `provider: str = "local"`, `fallback_chain: List[str] = field(default_factory=list)`.
6. Update `scriber/web/server.py` and `scriber/web/ui.py`:
   - Support credentials management (`/api/voice/credentials`) and add frontend model selection for Local GPU 48kHz, Voicemaker.in Cloud 48kHz, and ElevenLabs 48kHz.
7. Test and Verify:
   - Create `tests/test_voice_overhaul.py` testing:
     - Companion microservice lifecycle (`/health`, `/synthesize`, `/shutdown`).
     - Voicemaker.in connector request formatting and response decoding.
     - ElevenLabs connector request formatting, IVC hash caching, and 48kHz PCM output.
     - 4-tier fallback matrix routing and degradation order.
     - 48kHz audio validity and MP3 encoding.
     - Fixed `test_server_api.py::test_do_post_clone_voice`.
   - Run existing `tests/test_voice_clone.py`, `tests/verify_e2e_voice.py`, and `tests/test_server_api.py`.
   - Run full test suite `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"`.
8. Deliver handoff report to `.agents/teamwork/worker_m4/handoff.md`.

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.


## 2026-10-30T17:44:09Z
[Message] timestamp=2026-10-30T17:44:09Z sender=c60e3390-79cc-45bf-a4ac-11c2f4785ada priority=MESSAGE_PRIORITY_HIGH content=You are Worker M4 for Milestone 4 (Voice Cloning Overhaul & Cloud Connectors).
Read your dispatch instructions in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4\DISPATCH.md
and the authoritative request in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
and project specification in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
and Explorer 3 findings in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\explorer_survey_3\handoff.md
and Hardware module in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\scriber\hardware.py

Your role is to implement:
1. scriber/services/voice_microservice.py (Local GPU companion microservice daemon on 127.0.0.1:18840)
2. scriber/voice_clone.py (VoiceMicroserviceManager, VoicemakerConnector, ElevenLabsConnector, 4-tier fallback matrix, 48kHz dual-rate audio, similarity calibration fix)
3. scriber/models.py (VoiceCloneResult 48kHz fields)
4. scriber/web/server.py & scriber/web/ui.py (credentials API, UI model selector)
5. tests/test_voice_overhaul.py (comprehensive unit & integration tests)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Deliver your complete handoff report to:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4\handoff.md
Notify the orchestrator when complete.


## 2026-10-30T17:58:05Z
[Message] timestamp=2026-10-30T17:58:05Z sender=c60e3390-79cc-45bf-a4ac-11c2f4785ada priority=MESSAGE_PRIORITY_HIGH content=**Context**: Milestone 4 Status Check
**Content**: Checking in on Milestone 4 progress. We saw that `scriber/services/voice_microservice.py` is implemented. Please proceed with updating `scriber/voice_clone.py`, `scriber/models.py`, `scriber/web/server.py`, writing `tests/test_voice_overhaul.py`, and updating your `progress.md`.
**Action**: Please report your current progress.
