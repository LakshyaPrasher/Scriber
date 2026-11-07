# Scriber — Project Handoff Report for the Next LLM

**Purpose:** Give a successor LLM (or agent) everything it needs to continue work on Scriber without re-auditing from scratch.

> **Re-audit update (2026-11-07, HEAD `f19b4fe`):** A fresh independent audit was performed after this report was written. See **`RE_AUDIT_REPORT.md`** for the current findings. Two claims below are overstated:
> - “Arbitrary file read/write/reveal endpoints locked down” is incomplete: `/api/media` still serves any file under `Path.home()` (`scriber/web/server.py:43`).
> - “Hardcoded confidences replaced” is false: `scriber/agent_swarm.py:267` and `scriber/models.py:37,143` still contain hardcoded `0.985`/`0.99` values.

---

## 1. Project identity

| Field | Value |
|---|---|
| Project | **Scriber Studio** (local-first speech intelligence & voice synthesis) |
| App name | **Scriber** — never "criber" |
| Repo root | `C:\Users\laksh\.gemini\antigravity\scratch\scriber` |
| Python package | `scriber/` |
| Git branch | `main` |
| HEAD commit | `f19b4fe` "docs: add LLM handoff report; commit pending cli.py shortcut-destination reorder" (prior remediation: `e35c9a9`) |
| Prior HEAD | `51c70bf` (baseline, clean) |
| Working tree | Clean (nothing uncommitted) |
| Remote | `origin` → `https://github.com/LakshyaPrasher/Scriber.git` (in sync; 0 ahead/behind) |
| `.git/config` | Clean — no embedded PAT or credentials |
| Baseline tests | `532 passed, 8 skipped` in ~8 min (pre-remediation) |
| Post-remediation tests | `533 passed, 8 skipped, 0 failed` in `tests/` (6:24–20:53 depending on machine load; see `RE_AUDIT_REPORT.md` P3-7) |

---

## 2. What was fixed (all committed in `e35c9a9`)

### Security (P0)
- Removed plaintext GitHub PAT from `.git/config`; remote URL is now clean.
- Removed CORS `*` wildcard; Host/Origin checks added; save and reveal restricted to `./scriber_output` with `Path.resolve()` allow-list. `/api/media` is restricted to output root + temp + the user's home directory (broader than intended; see `RE_AUDIT_REPORT.md` P1-1).
- PII span-based redaction with Luhn credit-card validation; honest `is_shielded`.
- Arbitrary file write/reveal endpoints locked down; `/api/media` read scope is still broader than intended (see `RE_AUDIT_REPORT.md` P1-1).
- Microservice: honest GPU health fields, no fake telemetry, `similarity_score` null when unmeasured, CORS removed, token-protected `/shutdown` and `/synthesize`.
- Microservice manager generates a per-launch token and passes it via `--token` / `X-Scriber-Token`.

### Honesty / contracts (P1)
- `reference_text` is validation-only; `ground_truth_hint` is explicit demo/test injection — no longer passed to ASR.
- Transcription fallback no longer invents dialogue; non-availability raises `TranscriptionUnavailableError` (HTTP 503).
- Synthetic dialogue gated behind `demo_mode`; confidence 0.0 and `is_synthetic=True`.
- Removed fabricated Whisper token IDs; removed WhisperSpeech/GPT-SoVITS/F5-TTS from `TOP_LEVERAGED_REPOS`; model labels are truthful ("not bundled / fallback").
- `calculate_similarity` returns raw acoustic heuristic; 0.0 for empty profiles; no logistic inflation; no hardcoded 99.4%.
- Voice backend labels honest (Edge-TTS / SAPI / formant-companion).
- Agent swarm telemetry uses computed heuristic scores + `confidence_basis` labels; however, per-item `ActionItem.confidence` is still hardcoded `0.985` (see `RE_AUDIT_REPORT.md` P1-2).
- Version uses `__version__` everywhere; removed "Certified 99%+ Accuracy".

### Validation semantics (P1)
- `ValidationReport` has `reference_available`, `evaluation_mode` ("reference" / "self_consistency").
- No-reference mode: `passed_99_percent=False`, `evaluation_mode="self_consistency"`, accuracy/WER/CER serialize as `null`.
- Missing reference actions return `None` metrics (not 1.0).

### Frontend (P2)
- Fixed double-escaped regexes (`\\s+` → `\s+`) at the four locations.
- `copyFullTranscript` iterates `window.renderedSegments` (merged speaker cards).
- `escapeHtml(ch.summary)` applied in chapter cards; chapter cards keyboard-reachable (`tabindex="0"`, Enter/Space).
- Removed hardcoded `99.4% Biometric Timbre Match`; acoustic similarity displays truthful raw heuristic or "not measured".
- Removed Google Fonts links (system font stack).
- Added visible "DEMO — synthetic transcript"/synthetic-audio warnings based on `is_synthetic`.
- `--text-muted` contrast raised; all sub-12px font sizes → ≥12px; global `:focus-visible`; blanket `outline: none` removed.

### Packaging / naming (P3)
- `build_desktop.py`: shortcut creation opt-in via `--shortcut` or `SCRIBER_NO_SHORTCUT=1`; default is no shortcut.
- `scriber/cli.py`: shortcut install honors `SCRIBER_NO_SHORTCUT`.
- README updated: honest offline/online claims, voice-backend disclosures, accuracy language, shortcut opt-in.
- Deleted stale shortcuts; renamed duplicate folder; removed 428 stale `criber` path references.

### Tests
- Updated `test_pipeline.py`, `test_transcription_engine.py`, `test_voice_clone.py`, `test_voice_overhaul.py`, `test_server_api.py`, `test_ui_contracts.py`, `test_validator.py`, `e2e_suite/*` to assert truthful behavior (null metrics, no fabricated 99%, no WhisperSpeech/GPT-SoVITS presence, similarity is heuristic).

---

## 3. What was NOT fixed (remaining risks)

These were **out of scope** or intentionally deferred. A successor LLM should treat them as known issues:

| Area | Status | Note |
|---|---|---|
| Per-launch auth token for the **main** HTTP server | Not done | Microservice has token auth; main server (`scriber/web/server.py`) still serves the UI same-origin with no request token. Consider adding one if the app is exposed beyond localhost. |
| m1/m2 audio-editor markup duplication | Not done | ~250 lines of duplicated editor markup in `index.html`. Candidate for a reusable template/component. |
| Toast `aria-live` / screen-reader polish | Partially done | Focus rings and contrast fixed; toast container still lacks `role="status" aria-live="polite"`. |
| Responsive 360px layout pass | Not done | Breakpoints exist; narrow-width and 200% zoom not thoroughly tested. |
| Real GPU/F5-TTS model execution | Not done | `torch` not installed; microservice optional. Claims about GPU acceleration are conditional on separate install. |
| History purge if PAT was ever committed | Not done | PAT was only in `.git/config` (untracked), not in commit history. If it ever was committed, purge with BFG/filter-repo. |
| `/api/media` home-directory read scope | Open (P1) | `_media_roots()` includes `Path.home()`, so `/api/media?path=` can serve any file under home. See `RE_AUDIT_REPORT.md` P1-1. |
| Hardcoded confidence values | Open (P1) | `agent_swarm.py:267` uses `0.985`; `models.py:37,143` default to `0.99`; OpenAI-Whisper fallback inherits `0.99`. See P1-2. |
| “Biometric” labels in CLI/progress/agents | Open (P2) | Frontend fixed, but `cli.py`, `pipeline.py`, `diarizer.py`, `agent_swarm.py`, `voice_clone.py` still use biometric language. See P2-1. |
| Synthetic placeholder audio → ASR | Open (P2) | No decoder → synthetic tone is still transcribed; UI warns about audio but transcript is not marked synthetic. See P2-2. |
| Full suite runtime | Open (P3) | Hardware stress test alone ~2 min; full suite can exceed 15 min. See P3-7. |

---

## 4. How to run tests

From the repo root (PowerShell):

```powershell
# Full suite (allow 30 minutes; the hardware stress test alone takes ~2 minutes
# and the suite can exceed 15 minutes on a busy machine)
.\.venv\Scripts\python.exe -m pytest -q

# Targeted UI / API contracts (fast iteration)
.\.venv\Scripts\python.exe -m pytest tests/test_ui_contracts.py tests/test_server_api.py -q

# Pipeline / validator / transcription / voice clone
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py tests/test_validator.py tests/test_transcription_engine.py tests/test_voice_clone.py -q

# E2E (may need optional deps)
.\.venv\Scripts\python.exe -m pytest tests/e2e_suite/ -q
```

**Expected:** `533 passed, 8 skipped, 0 failed`. If a number drops, a regression was introduced — investigate before committing.

---

## 5. Key files and their roles

| File | Role |
|---|---|
| `scriber/__init__.py` | Package entry, `__version__` |
| `scriber/models.py` | Dataclass contracts (`ValidationReport`, `VoiceCloneResult`, `ScriberOutput`, etc.) + `to_dict()` |
| `scriber/pipeline.py` | `process_file`/`process_pcm`; ground-truth/demo separation |
| `scriber/transcription_engine.py` | ASR backends; demo gating; honest errors; `TOP_LEVERAGED_REPOS` |
| `scriber/validator.py` | WER/CER/accuracy; `reference_available`/`evaluation_mode`; null metrics |
| `scriber/voice_clone.py` | Synthesis backends; raw acoustic similarity; `TOP_VOICE_MODELS` |
| `scriber/services/voice_microservice.py` | Optional local GPU companion service |
| `scriber/pii_security.py` | Span-based PII redaction; Luhn; `is_shielded` |
| `scriber/exceptions.py` | `TranscriptionUnavailableError` |
| `scriber/exporters.py` | HTML/MD/SRT/VTT export; HTML escaping via `_e()` |
| `scriber/web/server.py` | Local HTTP API; security headers; path allow-lists |
| `scriber/web/server.py` microservice manager | Per-launch token generation + `--token` / `X-Scriber-Token` |
| `scriber/agent_swarm.py` | Heuristic council agents with `confidence_basis` |
| `scriber/cli.py` | CLI entry; shortcut install (`SCRIBER_NO_SHORTCUT`) |
| `build_desktop.py` | PyInstaller packaging; `--shortcut` opt-in |
| `scriber/web/static/app.js` | Frontend app logic |
| `scriber/web/static/index.html` | Frontend markup |
| `scriber/web/static/styles.css` | Design tokens, contrast, focus, fonts |
| `README.md` | User-facing claims (now honest) |
| `AUDIT_REPORT.md` | Full original audit findings + patch checklist (889 lines) |

---

## 6. Truthfulness rules to preserve (do not regress)

If the successor LLM changes any of these, the audit's honesty guarantees break:

1. **Never fabricate a transcript.** If ASR is unavailable, raise `TranscriptionUnavailableError`; synthetic output only behind `demo_mode` with `is_synthetic=True` and confidence `0.0`.
2. **Never pass `reference_text` to ASR.** `reference_text` is validation-only. `ground_truth_hint` is explicit demo/test injection.
3. **Never claim 99%+ accuracy without a reference.** Self-consistency mode must report `evaluation_mode="self_consistency"`, `passed_99_percent=False`, and `null` accuracy/WER/CER.
4. **Never label acoustic similarity as biometric verification.** It is a heuristic; empty/unmeasured profiles return `0.0`/`null`; UI must say "Acoustic Similarity (heuristic)".
5. **Never hardcode "99.4% Biometric Timbre Match" or similar.** Display the actual value from `VoiceCloneResult`, or "Not measured".
6. **Never claim "100% offline" or "F5-TTS bundled" unless true.** Edge-TTS is network; F5-TTS/WhisperSpeech/GPT-SoVITS are optional/not bundled.
7. **Escape all HTML** in exporters and the council UI (`_e()` / `escapeHtml`).
8. **Keep shortcuts opt-in.** `build_desktop.py --shortcut` or `SCRIBER_NO_SHORTCUT=1`; never auto-create `.lnk` files.

---

## 7. Files the successor LLM should read first

- `scriber/models.py` — understand the data contracts before changing anything.
- `scriber/pipeline.py` + `scriber/validator.py` — validation flow and demo gating.
- `scriber/web/static/app.js` — frontend behavior and contract consumption.
- `AUDIT_REPORT.md` — the full original audit with line-level patch checklist (reference for why things were changed).
- `HANDOFF_REPORT.md` — this file.

---

## 8. Quick context for the next session

- Git is clean; everything is committed on `main` and pushed to origin.
- No uncommitted work, no stashed changes.
- The test suite is green; use it as a regression net.
- If you need to re-verify the `.git/config` PAT: it is clean (URL only, no credentials).
- If you need to re-run the full audit: `AUDIT_REPORT.md` contains the complete severity summary, findings, and patch checklist.

---

**End of handoff.** The next LLM can start by reading `AUDIT_REPORT.md` for full findings, then proceed with feature work while preserving the truthfulness rules in section 6.