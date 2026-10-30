# Task Assignment: Replacement Worker M4 — Voice Cloning Overhaul & Cloud Connectors Completion

- Role: Milestone 4 Completion Worker
- Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4_2\
- Authoritative Request: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
- Scope Document: c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
- Predecessor Progress: c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4\progress.md
- Microservice Implementation: c:\Users\laksh\.gemini\antigravity\scratch\criber\scriber\services\voice_microservice.py

## Interruption Point & Completed Work
Predecessor `worker_m4` completed:
1. Implemented `scriber/services/voice_microservice.py` (Local GPU companion microservice on loopback `127.0.0.1:18840` for F5-TTS flow-matching with `/health`, `/synthesize`, `/shutdown`).
2. Updated `scriber/models.py` (`VoiceCloneResult` 48kHz fields: `sample_rate_hz`, `provider`, `fallback_chain`).
3. Implemented `resample_pcm` in `scriber/audio_editor.py`.
4. Fixed empty profile similarity calibration.

## Remaining Tasks for Replacement Worker
1. In `scriber/voice_clone.py`:
   - Implement `VoiceMicroserviceManager` (spawns daemon, probes `/health`, posts `/synthesize`, handles shutdown).
   - Implement `VoicemakerConnector` (`https://developer.voicemaker.in/voice/api`, `AudioSampleRate: "48000"`, `Engine: "neural"`, audio decoding).
   - Implement `ElevenLabsConnector` (`https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_48000`, Instant Voice Clone with SHA-256 hash caching).
   - Wire the 4-tier fallback matrix in `VoiceCloner.clone_voice`:
     - Tier 1: Local GPU Microservice (`VoiceMicroserviceManager`) if `supports_local_speech_llm` and microservice available.
     - Tier 2: Cloud Studio (`VoicemakerConnector` / `ElevenLabsConnector`) if API keys configured.
     - Tier 3: Edge-TTS with Mel-filterbank morphing and 48kHz resampling.
     - Tier 4: Offline Parametric Formant Biquad IIR Vocoder.
2. In `scriber/web/server.py` and `scriber/web/ui.py`:
   - Expose `/api/voice/credentials` for API keys and update `/api/clone-voice` parameters.
   - Add frontend UI model selector options: "Local GPU (F5-TTS Flow-Matching 48kHz)", "Voicemaker.in Cloud Studio (48kHz)", "ElevenLabs Studio (48kHz)".
3. In `tests/test_voice_overhaul.py`:
   - Implement tests covering microservice lifecycle, Voicemaker connector, ElevenLabs connector, 4-tier fallback, 48kHz audio validity, and fixed `test_do_post_clone_voice`.
4. Run tests:
   - `.\.venv\Scripts\python.exe -m unittest tests/test_voice_overhaul.py`
   - `.\.venv\Scripts\python.exe -m unittest tests/test_server_api.py`
   - `.\.venv\Scripts\python.exe -m unittest tests/test_voice_clone.py`
   - `.\.venv\Scripts\python.exe tests/e2e_suite/runner.py --tier 1`
5. Deliver handoff report to `c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m3_2\handoff.md`.
6. Send completion message to orchestrator.

## Mandatory Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## 2026-10-30T20:48:26Z
[Message] timestamp=2026-10-30T20:48:26Z sender=c60e3390-79cc-45bf-a4ac-11c2f4785ada priority=MESSAGE_PRIORITY_HIGH
content=You are replacement Worker M4 (Voice Cloning Overhaul & Cloud Connectors Completion).
Read your dispatch instructions in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4_2\DISPATCH.md
and the authoritative request in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\ORIGINAL_REQUEST.md
and project specification in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\PROJECT.md
and existing microservice in:
c:\Users\laksh\.gemini\antigravity\scratch\criber\scriber\services\voice_microservice.py

Your role is to complete the voice cloning overhaul:
1. In scriber/voice_clone.py: implement VoiceMicroserviceManager, VoicemakerConnector, ElevenLabsConnector, and the 4-tier fallback matrix.
2. In scriber/web/server.py & scriber/web/ui.py: add credentials handling and UI model selection for 48kHz engines.
3. In tests/test_voice_overhaul.py: implement and run comprehensive tests for connectors, fallback matrix, and 48kHz audio.
4. Deliver your complete handoff report to:
c:\Users\laksh\.gemini\antigravity\scratch\criber\.agents\teamwork\worker_m4_2\handoff.md
Notify the orchestrator when complete.
