# Scriber — Logical, Security & Visual/UX Audit

**Audit date:** 2026-11-07  
**Repository:** `LakshyaPrasher/Scriber`  
**HEAD at audit start:** `51c70bf1fffb456395ed386877822bd8c889deb4` (`main`)  
**Working tree at audit start:** clean  
**Baseline test run:** `532 passed, 8 skipped` in 501.05 s (`python -m pytest -q`)

> **Bottom line:** Scriber has a large, well-organized codebase and a green test suite, but the suite is green partly because several tests assert fabricated output. The most serious problems are (1) an unauthenticated local HTTP API that can read and write arbitrary files, (2) a plaintext GitHub token in `.git/config`, (3) a transcription fallback that invents dialogue when ASR fails, and (4) marketing/UI claims (“100% offline”, “F5-TTS”, “WhisperSpeech”, “GPT-SoVITS”, “99.4% biometric match”, “Certified 99%+ accuracy”) that the implementation does not support. These are fixable without redesigning the product, but they must be fixed before the app is presented as production-ready.

---

## 0. Severity summary

| Severity | Area | Count | Examples |
|---|---|---:|---|
| **P0** | Security / data safety | 8 | plaintext PAT, arbitrary file read/write, CORS `*`, unauthenticated `/shutdown`, stored XSS |
| **P1** | Crash bugs / silent corruption | 8 | undefined `shutil`, `logger`, `file_size`, `out`; double-escaped regexes; synthetic-tone fallback |
| **P1** | Product honesty | 10 | invented transcripts, fake model labels, rigged similarity, fake GPU telemetry, “99% certified” |
| **P2** | API / contract defects | 5 | PII request/response mismatch, plugin response mismatch, `reference_text` circularity |
| **P2** | Logic / correctness | 8 | Luhn check absent, action metrics default to 1.0, non-exact “Levenshtein”, version mismatch |
| **P2** | Visual / UX / accessibility | 8 | low contrast, 10–11 px text, missing focus rings, duplicated editor markup, external fonts |
| **P3** | Naming / cleanup / docs | 5 | 428 stale `criber` path references, stale duplicate folder, desktop shortcut, README claims |

---

## 1. What is genuinely solid

This is not a “rewrite it” audit. Several parts are well done:

- **Clear package layout**: `scriber/` modules are purpose-named, with lazy exports in `scriber/__init__.py`.
- **Dataclass-based contracts**: `scriber/models.py` is readable and consistently serialized with `to_dict()`.
- **Real DSP foundations**: `audio_editor.py`, `audio_extractor.py`, and the diarizer contain real signal-processing code (resampling, biquad/formant synthesis, VAD, spectral features), not just stubs.
- **Graceful degradation is attempted**: ASR → CPU fallback, Edge-TTS → SAPI → formant synthesis, local/remote model selection.
- **Good baseline test coverage**: 532 tests pass, including API, exporters, pipeline, validator, PII, and UI contract tests.
- **Accessibility is not ignored**: there are `aria-label`s, `role="status"`, `aria-live`, and a `prefers-reduced-motion` block.
- **Localhost binding**: the main server defaults to `127.0.0.1` (`server.py:1316`, `1340`), which is the right default.
- **Packaging is deliberate**: PyInstaller spec, PE subsystem verification, and a build script exist.

The problems below are mostly about **trust boundaries, truthfulness, and edge-case correctness**, not architecture.

---

## 2. P0 — Security and data-safety defects

### 2.1 Plaintext GitHub PAT in `.git/config` (critical)

**Verified:** `remote.origin.url` contains an embedded credential for `github.com/LakshyaPrasher/Scriber.git`.

**Risk:** Anyone with read access to the folder (backup, zip, screen share, cloud sync, malware) gets a working GitHub token. If the token has `repo` scope, it can read/write private repositories.

**Fix (do this before anything else):**
1. Revoke/rotate the token in GitHub → Settings → Developer settings → Personal access tokens.
2. Remove it from the remote:
   ```powershell
   git remote set-url origin https://github.com/LakshyaPrasher/Scriber.git
   ```
3. Use Git Credential Manager (`git config --global credential.helper manager`) or SSH.
4. Check for leaks in shell history, `.env`, logs, and the packaged `dist/` folder.
5. Do **not** print the token in reports, chat, or commits.

> The token is in `.git/config`, not in tracked history, so rotating and rewriting the remote is sufficient. If the token was ever committed, rotate it and purge history separately.

### 2.2 Arbitrary file read via `/api/media?path=`

**Location:** `scriber/web/server.py:190-196`.

```python
media_path = query.get("path", [""])[0]
if media_path and os.path.isfile(media_path):
    self._serve_static_file(media_path)
```

Combined with `Access-Control-Allow-Origin: *` (`server.py:363`, `1246`), any website the user visits can:

```js
fetch('http://127.0.0.1:8080/api/media?path=C:/Users/me/Documents/secret.pdf')
  .then(r => r.text())
```

and read the response. This is a full local-file disclosure primitive. It also bypasses the intended “serve exported media” use case.

**Fix:**
- Resolve the requested path and require it to be inside an allow-listed root:
  ```python
  from pathlib import Path
  OUTPUT_ROOT = (Path.cwd() / "scriber_output").resolve()
  TEMP_ROOT = Path(tempfile.gettempdir()).resolve()
  candidate = Path(media_path).resolve()
  if not any(candidate.is_relative_to(root) for root in (OUTPUT_ROOT, TEMP_ROOT)):
      return 404
  ```
- Reject symlinks/junctions that escape the root (`candidate.resolve()` handles most, but check `is_symlink()`).
- Remove the CORS wildcard (see 2.5).
- Consider a signed, short-lived media token instead of a raw path.

### 2.3 Arbitrary file write via `/api/desktop/save-file`

**Location:** `scriber/web/server.py:1216-1236`.

The client supplies both `filename` and `dir`; the server does `os.makedirs(out_dir)` and writes `os.path.join(out_dir, os.path.basename(filename))`. Any website can POST to this endpoint and write files anywhere the user can write, including startup folders, `.ssh`, or project source.

**Fix:**
- Ignore client-supplied `dir`; always write under `./scriber_output`.
- Sanitize the filename to a conservative allow-list (`[A-Za-z0-9._- ]`), strip leading dots, reject reserved Windows names (`CON`, `PRN`, `AUX`, `NUL`, `COM1`…).
- Resolve the final path and verify `is_relative_to(OUTPUT_ROOT)`.
- Limit content size (e.g. 50 MB) and reject `..`.
- If a user-chosen directory is a real product requirement, use a native save dialog (desktop app) rather than accepting a path over HTTP.

### 2.4 Arbitrary path open/execute via `/api/desktop/reveal`

**Location:** `scriber/web/server.py:1178-1214`.

`target` can be any path. On Windows, `os.startfile(abs_path)` will launch an executable or document; `explorer.exe /select,<path>` also accepts arbitrary paths. A malicious site can trigger this through CORS.

**Fix:**
- Restrict `target` to the output root (and optionally the last processed media file).
- Do not call `os.startfile` on user-supplied paths.
- If the path is a file, only reveal it in Explorer (`/select,`), never execute it.

### 2.5 CORS `*` plus no authentication

**Locations:** `server.py:152-161`, `363`, `1246`, `1297`; `services/voice_microservice.py:242`, `250`.

The server exposes powerful endpoints with `Access-Control-Allow-Origin: *` and no session token:
- `/api/process` (reads arbitrary `file_path`, returns transcript)
- `/api/process-demo`
- `/api/clone-voice`
- `/api/profile-voice`
- `/api/edit-audio`
- `/api/desktop/save-file`
- `/api/desktop/reveal`
- `/api/plugin/install`
- `/api/voice/credentials`
- `/api/cancel`

CORS is not a substitute for authentication, and a wildcard makes browser-based cross-origin attacks trivial. Binding to `127.0.0.1` does not protect against a malicious page in the user’s browser.

**Fix:**
- The UI is served same-origin, so **remove CORS headers entirely** for the main app. If a separate origin is needed, echo only `http://127.0.0.1:<port>` / `http://localhost:<port>` after checking `Origin`.
- Add a per-launch random token (`secrets.token_urlsafe(32)`) that the UI receives in the HTML and sends as `X-Scriber-Token`; reject requests without it. This also mitigates DNS rebinding.
- Validate the `Host` header (`127.0.0.1`/`localhost` + expected port) and reject others.
- Add `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and a restrictive `Content-Security-Policy` (after removing inline scripts/styles or adding nonces).
- Add `SameSite=Strict` if cookies are introduced; currently there are none.

### 2.6 Unauthenticated microservice `/shutdown`

**Location:** `services/voice_microservice.py:266`.

Any local process or web page (with the CORS wildcard) can kill the voice service.

**Fix:** remove `/shutdown` or require the same per-launch token. Bind to `127.0.0.1` explicitly. Do not expose `Access-Control-Allow-Origin: *`.

### 2.7 Stored XSS in the generated HTML report

**Location:** `scriber/exporters.py:179-305`; `web/static/app.js:2936`.

`to_html` interpolates these values without escaping:
- `output.video_source` (filename)
- `summary.headline`, `summary.tldr`
- `a.task`, `a.assignee`, `a.due_date`
- `s.text`, `s.speaker`
- `ch.summary` in the UI chapter card (`app.js:2936`) is also inserted raw.

A crafted filename or transcript can execute JavaScript when the exported HTML is opened, or in the app’s own DOM.

**Fix:**
- Python: `import html` and wrap every interpolated value with `html.escape(str(value), quote=True)`; use a small `_e()` helper.
- JavaScript: use `escapeHtml(ch.summary || '')`; audit every `innerHTML` template for raw values.
- Prefer `textContent`/DOM construction for user-controlled text.
- Add a test that exports a transcript containing `<img src=x onerror=alert(1)>` and asserts the output contains `&lt;img`.

### 2.8 PII redaction is not reliable

**Location:** `scriber/pii_security.py:34-110`, `146-155`.

Issues:
- Credit-card “validation” only checks `len(digits) == 16` (`pii_security.py:70-74`); it does not run Luhn. Random 16-digit IDs are redacted; invalid cards may be missed if the regex shape differs.
- `str.replace(val, replacement)` replaces **every** occurrence of the matched substring, including occurrences that were not matched as PII in context. This can over-redact and inflate counts.
- `is_shielded=True` is set even when `redacted_count == 0` (`pii_security.py:154`), so the UI can claim protection when nothing was found.
- The regex bank is a good start, but phone/email/SSN patterns need tests for false positives and international formats.

**Fix:**
- Implement Luhn:
  ```python
  def _luhn_ok(digits: str) -> bool:
      total = 0
      for i, ch in enumerate(reversed(digits)):
          n = int(ch)
          if i % 2 == 1:
              n *= 2
              if n > 9: n -= 9
          total += n
      return total % 10 == 0
  ```
- Redact by rebuilding the string from regex spans (or `re.sub` with a callback), not global `replace`.
- Set `is_shielded = total_redacted > 0`; add `pii_found: bool` and `clean: bool` if the model can be extended.
- Add tests for Luhn-valid/invalid cards, repeated values, overlapping patterns, and empty input.

---

## 3. P1 — Crash bugs and silent corruption

### 3.1 `shutil` is used but not imported

**Location:** `scriber/web/server.py:784`.

```python
shutil.copy2(tmp_path, persistent_path)
```

`shutil` is imported locally inside `_handle_plugin_install` (`server.py:496`), not at module scope. The `except Exception: pass` at 786 swallows the `NameError`, so `media_url` silently disappears and the UI cannot play the uploaded file.

**Fix:** add `import shutil` at the top of `server.py`; remove the local import; log the exception instead of swallowing it.

### 3.2 Undefined `logger`

**Locations:** `server.py:871`, `1378`.

`logger.debug(...)` / `logger.warning(...)` are called but no module-level `logger` exists. These paths only run on errors, so the app can crash while handling another error.

**Fix:**
```python
import logging
logger = logging.getLogger(__name__)
```

### 3.3 Undefined `file_size` in audio extraction strategy 5

**Location:** `scriber/audio_extractor.py:284`.

```python
duration = meta.duration if meta.duration > 0 else max(2.5, min(120.0, file_size / 32000.0))
```

`file_size` is only defined inside `inspect_file` (`audio_extractor.py:58`), not in `extract_pcm16`. Any file that reaches strategy 5 raises `NameError` (or would, before the synthetic fallback).

**Fix:** use `meta.file_size_bytes` or `os.path.getsize(file_path)`.

### 3.4 Unreachable code and undefined `out` in `process_pcm`

**Location:** `scriber/pipeline.py:350-364`.

`return ScriberOutput(...)` at 350 exits the function; `gc.collect()` and `return out` at 363-364 are unreachable, and `out` is undefined. This is dead code, but it signals a copy/paste merge and confuses static analysis.

**Fix:** remove lines 363-364 (keep the `gc.collect()` in a `finally` if desired).

### 3.5 Double-escaped regular expressions in `app.js`

**Locations:** `app.js:707`, `728`, `1832`, `2216`.

Examples:
```js
.replace(/\\s+/g, ' ')          // matches a literal backslash + "s"
.replace(/([,.:;?!])\\./g, '$1') // matches literal backslash + any char
.replace(/\\.[^/.]+$/, "")       // matches literal backslash + any char
```

These should be `/\s+/g`, `/([,.:;?!])\./g`, and `/\.[^/.]+$/`. As written:
- Unified transcript text keeps literal `\s` artifacts instead of collapsing whitespace.
- Filename extension stripping fails.
- Voice profile download names keep `.mp3` or produce odd names.

**Fix:** correct all four regex literals and add a unit test for the helpers.

### 3.6 `bool("false")` enables PII redaction

**Location:** `server.py:536`.

```python
redact_pii_val = bool(data.get("redact_pii", False))
```

`bool("false")` is `True`, so a JSON client sending `"redact_pii": "false"` gets redaction. The multipart paths correctly parse strings (`server.py:637`, `677`).

**Fix:** central helper:
```python
def _as_bool(value, default=False):
    if isinstance(value, bool): return value
    if isinstance(value, (int, float)): return value != 0
    if isinstance(value, str): return value.strip().lower() in ("1","true","yes","on")
    return default
```

### 3.7 `copyFullTranscript` disagrees with the rendered transcript

**Location:** `app.js:846-872` versus `renderTranscription` (`app.js:668-711`).

The renderer merges consecutive same-speaker segments into `window.renderedSegments`, and the DOM has one `seg-text-<idx>` per merged card. `copyFullTranscript` iterates the **original** `data.transcription.segments` and calls `getCleanSegmentText(s, idx)`, reading `seg-text-0`, `seg-text-1`, … which are merged cards. Result: duplicated text, wrong timestamps, and repeated speaker labels.

**Fix:** iterate `window.renderedSegments` (already stored) in `copyFullTranscript`, or have the renderer keep a stable mapping from original segments to merged cards. Add a test that merges two segments and asserts the copied text contains each sentence once.

### 3.8 Synthetic tone masks decode failures

**Location:** `scriber/audio_extractor.py:272-293`.

If FFmpeg/other decoders fail, strategy 5 returns a **synthetic tone** (`create_synthetic_wav`) and claims success. The pipeline then transcribes the tone, producing empty or invented output. This is worse than a clear failure because the user believes their file was processed.

**Fix:** raise a clear `RuntimeError` explaining that FFmpeg is required for this container, and surface it in the UI. Keep synthetic audio only for the explicit demo endpoint, and label it as demo audio.

---

## 4. P1 — Product honesty: claimed capabilities vs implementation

This is the most important non-security section. The UI and README describe an AI product that the code does not implement. Some of this may be intentional marketing, but several claims are falsifiable from the source.

### 4.1 Invented transcript when ASR fails

**Location:** `scriber/transcription_engine.py:541-680`.

`_transcribe_reference_flow` has two paths:
- If `ground_truth_hint` is provided, it uses that text as the transcript and fabricates token IDs, logprobs, and `confidence=0.995` (`lines 567-600`).
- If no hint is provided, it returns a five-turn fabricated conversation about “Scriber studio review”, “biometric timbre matching”, and “release sign-off” (`lines 602-609`), with `confidence=0.995`.

The method is called whenever faster-whisper fails or is unavailable (`lines 477-536`). On a machine without the model, a user can upload a real recording and receive a plausible but completely fake transcript.

**Fix:**
- Rename to `_synthetic_demo_flow` and require an explicit `demo_mode=True`.
- In normal mode, raise a clear `TranscriptionUnavailableError` with install instructions.
- Never set `confidence=0.995` on fabricated segments; set `confidence=0.0` and `is_synthetic=True` if demo data must be shown.
- Add a visible “DEMO — synthetic transcript” banner in the demo UI.

### 4.2 `reference_text` bypasses ASR and guarantees 100% accuracy

**Locations:** `pipeline.py:144`, `315`; `server.py:546`, `688`, `747`.

`process_file` passes `reference_text` into `ground_truth_hint`, which makes the transcriber return the reference text verbatim. Then the validator compares the transcript to the same reference and reports 100% accuracy. Any API client can supply `reference_text` and receive a “perfect” transcript without any speech recognition.

**Fix:**
- Separate the concepts:
  - `reference_text`: used **only** for validation, never passed to ASR.
  - `ground_truth_hint`: explicit test/demo injection, not exposed in the normal API (or gated behind a `demo` flag).
- Update `process_file`/`process_pcm` signatures accordingly.
- Update tests to use `ground_truth_hint` explicitly.
- Add a test asserting that `reference_text` does not change `transcription.text`.

### 4.3 Model labels do not match implementations

**Location:** `scriber/transcription_engine.py:183-304`, `voice_clone.py:1051-1080`.

| UI / docs label | Actual implementation |
|---|---|
| **WhisperX** | Alias for the `base` CT2 model; no WhisperX package, no wav2vec2 phoneme alignment (`transcription_engine.py:213-218`) |
| **F5-TTS Flow-Matching 48kHz** | Optional external microservice; `torch` is excluded from `scriber.spec` and not in `pyproject.toml`; default path is Edge-TTS/SAPI/formant |
| **WhisperSpeech** | Edge-TTS with `backend_used = "whisperspeech-inversion"` (`voice_clone.py:1540`) |
| **GPT-SoVITS** | Edge-TTS with `backend_used = "gpt-sovits-timbre"` (`voice_clone.py:1540`) |
| **Distil-Whisper / Turbo / Large-v3** | Real faster-whisper model IDs, but the evaluation matrix values are hardcoded, not measured locally |

**Fix (minimum honest version):**
- Rename the `whisperx` entry to “Whisper Base + Silero VAD” unless WhisperX is actually bundled.
- Rename `local-gpu` to “Local GPU Companion (requires separate install)”.
- Rename `whisperspeech` / `gpt-sovits` entries to “WhisperSpeech (not bundled)” / “GPT-SoVITS (not bundled)” or remove them from the selectable list.
- Add `available: bool` to each model descriptor and disable unavailable options in the UI.
- In `MODEL_EVALUATION_MATRIX`, add `"measured_locally": False` and `"source": "vendor-published"`; relabel the UI “Published specs” rather than “Empirical”.
- If the product genuinely needs these models, add `torch`/`f5-tts` dependencies and a real model loader, then test it. Do not ship the label without the implementation.

### 4.4 “Voice cloning” is mostly TTS + DSP, and similarity is inflated

**Location:** `scriber/voice_clone.py:1460-1600`, `1937-2016`.

- Default `auto` path tries the microservice, then Edge-TTS (network), then Windows SAPI, then a formant vocoder. None of these performs neural zero-shot voice cloning.
- `calculate_similarity` returns **0.9950** for empty/default profiles (`voice_clone.py:2006-2007`).
- The logistic calibration maps a raw score of ~0.68 to ≥0.990 (`voice_clone.py:2009-2016`), so ordinary TTS output is presented as a 99% biometric match.
- The UI hardcodes “99.4% Biometric Timbre Match” (`app.js:2613`, `index.html:785`) regardless of the actual result.

**Fix:**
- Return the raw acoustic similarity (e.g. `raw_fidelity`) and label it “acoustic similarity heuristic — not biometric verification”.
- Return `0.0` or `None` when profiles are empty; never return 0.995 for missing data.
- Add `measured: bool` / `similarity_basis` to `VoiceCloneResult`.
- Display the actual value from the API, or “Not measured” if absent.
- Rename “Biometric Timbre Match” to “Acoustic Timbre Similarity”.

### 4.5 Fake GPU telemetry in the microservice

**Location:** `services/voice_microservice.py:28-55`.

On failure, `/health` returns:
```python
"gpu_name": caps.gpu_name or "NVIDIA GeForce RTX 5050 Laptop GPU"
"vram_total_mb": 8151.0
```
and synthesis reports hardcoded `0.996` / `0.992` similarity (`lines 216`).

**Fix:**
- Report `gpu_name: None`, `available: false`, `error: "..."` when detection fails.
- Never invent hardware.
- Return `similarity_score: None` when no measurement was performed.
- Add a test that mocks `get_hardware_capabilities()` failure and asserts no fake GPU string appears.

### 4.6 “Autonomous agent swarm” is a set of regex/heuristic wrappers

**Location:** `scriber/agent_swarm.py`.

The agents have hardcoded confidences (`0.992`, `0.985`, `0.990`, `0.988`, `0.999`, `0.995`) and summaries like “Verified acoustic continuity…”. They do not call an LLM in the default path. `council.py` may optionally use an LLM, but the “swarm” telemetry is cosmetic.

**Fix:**
- Either wire the agents to a real model and record actual token/latency/verification data, or
- Rename them “heuristic analyzers” and set `confidence` to a computed heuristic score with `confidence_basis: "heuristic"`.
- Do not show “0.999” confidence for a regex check.

### 4.7 Translation is a small phrase dictionary

**Location:** `transcription_engine.py:687-760`.

`_mock_translate` maps a handful of Spanish/French/German phrases to English and leaves everything else unchanged. It is used in the reference/demo flow. Real translation should come from Whisper’s `task="translate"` for supported models, or a real translation backend.

**Fix:** remove `_mock_translate` from user-facing paths; rely on Whisper translate or mark the fallback as “no translation available”. Add a visible warning when the mock is used.

### 4.8 “Certified 99%+ accuracy” is self-comparison

**Locations:** `pipeline.py:218-234`, `validator.py:46-90`, `exporters.py:305`, `app.js:2962`.

When no reference is supplied, the pipeline compares the transcript to itself:
```python
reference_text=cleaned_transcription.text
```
The validator then reports `accuracy_score=1.0`, `passed_99_percent=True`, and “STATUS: PASSED 99%+ ACCURACY AUDIT.” The HTML exporter prints “Certified 99%+ Accuracy” unconditionally.

**Fix:**
- Add `reference_available: bool` and `evaluation_mode: "reference" | "self_consistency"` to `ValidationReport`.
- In self-consistency mode, set `passed_99_percent=False` and label the result “Self-consistency check (no reference)”.
- In exporters/UI, show “Accuracy vs reference” only when `reference_available`; otherwise show “Self-consistency only”.
- Remove the word “Certified” unless a real external benchmark was run.

### 4.9 “100% offline” contradicts the implementation

**Locations:** `README.md:22-24`, `181`; `pyproject.toml:29`; `index.html:15-17`.

- `edge-tts` is a required dependency and performs network requests to Microsoft’s service (`voice_clone.py:1520-1544`).
- The UI loads Google Fonts from `fonts.googleapis.com` (`index.html:15-17`).
- The default voice path prefers Edge-TTS before offline SAPI/formant.
- `/api/process` accepts arbitrary local file paths and can download? (No URL downloader found in the audited path; verify before claiming.)
- The README says “zero external API calls” and “100% offline”; both are false in the default configuration.

**Fix:**
- Change the README to “offline-capable with optional online neural voices” and list the network dependencies.
- Remove external font links; self-host fonts or use system fonts.
- Add an explicit “Offline mode” toggle that disables Edge-TTS and forces SAPI/formant.
- Add a startup network check and display the active mode.

### 4.10 Version mismatch

- `scriber/__init__.py`: `__version__ = "2.0.0"`
- `pyproject.toml:7`: `2.0.0`
- UI badge: `v2.0` (`index.html:70`)
- Markdown export: “Generated by Scriber v1.0.0” (`exporters.py:47`)

**Fix:** import `__version__` in the exporter and use it everywhere; add a test that asserts the exported Markdown contains `__version__`.

---

## 5. P2 — API contract mismatches

### 5.1 PII redaction request/response mismatch

**Frontend** (`app.js:2990-3012`):
```js
body: JSON.stringify({ segments: [...] })
// expects:
resData.sanitized_segments
resData.report.redactions_count
```

**Backend** (`server.py:471-491`):
```python
text = req_data.get("text", "")
redacted_text, counts, audit_log = officer.redact_text(text, ...)
return {"original_text": ..., "redacted_text": ..., "entities_found": ..., "redacted_count": ...}
```

The frontend sends no `text`, so the backend redacts an empty string and returns no `sanitized_segments`. The shield appears active but does nothing.

**Fix:** support both shapes:
```python
segments = req_data.get("segments")
if segments:
    sanitized, report = officer.sanitize_segments([AudioSegment.from_dict(s) for s in segments], mask_mode)
    return {"sanitized_segments": [s.to_dict() for s in sanitized], "report": report.to_dict()}
# else legacy text path
```
Add `AudioSegment.from_dict` if it does not exist. Update the frontend to request/consume the new shape and handle errors.

### 5.2 Plugin install response mismatch

**Frontend** (`app.js:3071-3074`) expects `data.success` and `data.target_dir`.

**Backend** (`server.py:508-512`) returns `{status, message, path}`.

Result: a successful install is reported as a failure.

**Fix:** return both:
```python
{"success": True, "status": "success", "message": ..., "path": str(dest_dir), "target_dir": str(dest_dir)}
```
and make the frontend tolerant of either field.

### 5.3 `redact_pii` boolean parsing

See 3.6.

### 5.4 `/api/process` JSON `file_path` has no boundary

The endpoint accepts any server-side path (`server.py:529-535`) and processes it. With CORS `*`, a website can ask the app to transcribe any readable media file and return the text. Fix by requiring the per-launch token and restricting paths to files the user explicitly selected (e.g. a one-time upload token or native dialog).

### 5.5 `/api/desktop/save-file` `dir` contract

The frontend sends `dir: './scriber_output'`, but the backend trusts it. Fix per 2.3; the client should not send a directory at all.

---

## 6. P2 — Logic and correctness defects

### 6.1 Action metrics default to 1.0

**Location:** `validator.py:403-412`.

```python
if not reference_actions:
    return 1.0, 1.0, 1.0
```

No reference actions means the metric is **not evaluable**, not perfect. This inflates reports.

**Fix:** return `(0.0, 0.0, 0.0)` plus a `reference_available` flag, or make the fields `Optional[float]` and serialize `null`. Update the UI to show “N/A” rather than 100%.

### 6.2 `_fast_sequence_distance` is not Levenshtein-equivalent

**Location:** `validator.py:316-330`.

`difflib.SequenceMatcher` produces a valid but not necessarily minimal edit script. The method claims “accurate Levenshtein-equivalent” in its docstring. For large inputs it is used as a fallback (`validator.py:379-381`), so WER can be overestimated.

**Fix:**
- Either use `rapidfuzz.distance.Levenshtein.distance` (fast, exact) as the large-input path, or
- Keep the DP for all sizes with a memory cap, and document the approximation if you keep `difflib`.
- Rename the method to `_sequence_matcher_distance` if you keep it.

### 6.3 Speaker-boundary capitalization can corrupt names

**Location:** `diarizer.py:1053-1129`, called at `334`, `341`, `507`, `845`, `986`, `1019`, `1033`.

`polish_english` is a heuristic that:
- Collapses duplicate words (`\b([A-Za-z]+)\s+\1\b`), including intentional repetition (“very very”, “had had”).
- Replaces acronym-like tokens globally (`api` → `API`, `ml` → `ML`, `ai` → `AI`, `whisper` → `Whisper`, `scriber` → `Scriber`), which can corrupt units, names, or quoted speech.
- Forces capitalization after every `.`, `?`, `!`, even in abbreviations or decimal numbers.
- Adds terminal punctuation.

It is applied to every English segment automatically, not just display text.

**Fix:**
- Make polishing opt-in (`polish_transcript: bool = False`) and log a diff when enabled.
- Never alter verbatim transcripts by default; offer a separate “Clean up” action.
- Restrict the acronym map to unambiguous casing (or remove it) and preserve original punctuation.
- Add regression tests with proper nouns, decimals, URLs, and repeated words.

### 6.4 `inspect_file` caps estimated duration at 300 s

**Location:** `audio_extractor.py:164`.

```python
estimated_dur = max(2.0, min(300.0, file_size / 32000.0))
```

For large files without metadata, the duration is capped at 5 minutes, which can truncate UI timelines, trim ranges, and progress calculations.

**Fix:** derive duration from the container header or stream; if unknown, report `duration=None`/`unknown` instead of a false cap. Do not use file size as a duration heuristic without a clear label.

### 6.5 PII over-redaction and false negatives

See 2.8.

### 6.6 Version mismatch

See 4.10.

### 6.7 `audio_extractor` synthetic fallback

See 3.8.

### 6.8 `pipeline.process_pcm` validation

See 4.8 and 3.4.

---

## 7. Visual / UX / accessibility audit

### 7.1 Contrast

Measured against the dark background `#08090C`:

| Token / usage | Value | Approx. contrast | Verdict |
|---|---|---:|---|
| `--text-muted` | `#64748B` | **4.19:1** | Fails WCAG AA for normal text (4.5:1); used at 10–11 px |
| White text on `--tangerine` / primary buttons | `#FFFFFF` on `#FF5E00` | **3.06:1** | Fails AA for normal text; passes only for large text (≥18.66 px bold / 24 px) |
| `--text-secondary` | likely `#94A3B8` | ~7.4:1 | Good |
| Body text | `#E2E8F0` on `#08090C` | ~15:1 | Good |

**Fix:**
- Raise `--text-muted` to `#94A3B8` or `#A3B0C2` (≥7:1), and never use it for essential 10 px labels.
- For primary buttons, either:
  - use dark text (`#0B0C0E`) on `#FF5E00` (contrast ~6.8:1), or
  - darken the button to `#C2410C` with white text (~5.9:1).
- Add a contrast regression test or a documented token table.

### 7.2 Tiny text

There are **48+** declarations at `10px`, `10.5px`, or `11px` in `styles.css` and inline styles in `index.html` (e.g. `styles.css:488, 568, 604, 785, 815, 909, 922, 1004, 1216, 1234, 1269, 1360, 1401, 1541, 1671, 1792, 1822, 1878, 1949, 2044, 2096, 2157, 2232, 2311, 2317, 2356, 2618, 2689, 2767, 2788, 2796, 2821, 2879`; `index.html:193, 194, 210, 547, 551, 1009, 1014`).

At 100% zoom these are hard to read; on high-DPI screens they are worse.

**Fix:**
- Set a 12 px minimum for metadata and 14 px for body text.
- Use `clamp()` for responsive typography.
- Reserve 10–11 px only for non-essential decorative labels, and pair with high contrast.
- Add a “Compact / Comfortable” density toggle if space is tight.

### 7.3 Focus visibility

Only two `:focus-visible` rules exist (`styles.css:276`, `430`), while `outline: none` appears at `styles.css:868, 889, 1422, 1727, 1811, 1975, 2074` and inline `outline:none` at `index.html:792`.

Keyboard users cannot see focus on many controls.

**Fix:**
```css
:where(a, button, input, select, textarea, [tabindex]):focus-visible {
  outline: 2px solid var(--tangerine);
  outline-offset: 2px;
}
:where(a, button, input, select, textarea, [tabindex]):focus:not(:focus-visible) {
  outline: none;
}
```
Remove blanket `outline: none` declarations.

### 7.4 Duplicated audio-editor markup

`index.html` contains two near-identical editor blocks:
- Mode 1: `#mode1-audio-editor` (`index.html:447-573`)
- Mode 2: `#mode2-audio-editor` (`index.html:914-1044`)

They duplicate sliders, pills, trim inputs, preview buttons, and export buttons, with `m1`/`m2` prefixes. `app.js` then duplicates logic by mode. This is ~250 lines of markup and repeated CSS/JS. It is a maintenance and accessibility-drift risk.

**Fix:** extract a single `audio-editor` template/component and instantiate it twice with a `mode` parameter. Or render it from a small JS function. Keep IDs unique but derive them from the mode.

### 7.5 External Google Fonts contradict offline mode

`index.html:15-17`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono...&family=Plus+Jakarta+Sans...">
```

This leaks the user’s IP to Google, fails on air-gapped machines, and contradicts the “100% offline” claim.

**Fix:**
- Self-host the WOFF2 files in `scriber/assets/fonts/` (both families are OFL-licensed), or
- Use a system stack: `ui-sans-serif, system-ui, "Segoe UI", Roboto, ...` and `ui-monospace, "Cascadia Code", Consolas, ...`.
- Remove the `preconnect` and stylesheet links.

### 7.6 Inline styles and magic colors

`index.html` uses dozens of inline `style="..."` attributes (e.g. lines 70, 193-194, 210, 542-551, 588, 687, 792, 1009-1018). This makes theming, dark/light mode, and CSP difficult.

**Fix:** move styles into `styles.css` classes; use CSS variables for colors/spacing; add a nonce or hash if a CSP is added.

### 7.7 ARIA and feedback

Good:
- `role="status" aria-live="polite"` on the processing card (`index.html:220`).
- `role="listbox"`/`aria-label` on dropdowns (`index.html:127`, `841`).
- `aria-expanded` on the export trigger (`app.js:1177`).

Gaps:
- `#toast-container` has no `role="status"`/`aria-live`; screen readers may miss success/error toasts (`index.html:1136`).
- `contenteditable` transcript cards (`app.js:760`) have no `aria-label`, no keyboard instructions, and edits are lost when `renderTranscription` re-renders.
- Icon-only buttons rely on `title` or no label; add `aria-label` (e.g. copy block, seek, close).
- The chapter cards use `onclick` on a `<div>` without `tabindex`/`role="button"` (`app.js:2938`), so they are not keyboard reachable.
- Progress updates may be too frequent for `aria-live`; throttle or use `aria-atomic`.

**Fix:** add `role="status" aria-live="polite"` to the toast container, labels to icon buttons, `role="button" tabindex="0"` + key handler to clickable cards, and a “Your edits may be reset” note (or persist edits to `currentResult`).

### 7.8 Responsive / motion

- Breakpoints exist at 768, 820, 600, 860, 640 px, and `prefers-reduced-motion` is handled (`styles.css:3042`). Good.
- At narrow widths, the duplicated editor and 10 px labels are likely cramped. Test at 360×640 and 200% zoom.
- Ensure tap targets are ≥44×44 px; current 10–11 px pill buttons may be smaller.

**Fix:** add a 360 px layout pass, increase touch targets, and test with browser zoom at 200%.

---

## 8. Branding, packaging, and naming cleanup

### 8.1 Stale duplicate folder

`C:\Users\laksh\.gemini\antigravity\scratch\scriber` is a stale duplicate of `...\scratch\criber`:
- 815 files compared
- 0 content differences
- same HEAD `51c70bf`
- clean status

It can be removed before renaming the main folder to `scriber`. (Verified during the audit.)

### 8.2 Literal `criber` path references

428 bare `criber` matches remain, almost entirely under `.agents/teamwork/**`, plus `VERIFICATION_REPORT.md`. The Python package is already consistently named `scriber`. Replace path segments only (`\criber\` → `\scriber\`, `/criber/` → `/scriber/`, bare `criber` → `scriber` with a negative lookbehind for `s` to avoid corrupting `scriber`).

### 8.3 Desktop shortcuts

Existing shortcuts point to the old path:
- `C:\Users\laksh\Desktop\Scriber.lnk` → `...\criber\dist\Scriber\Scriber.exe`
- `C:\Users\laksh\OneDrive\Desktop\Scriber.lnk`
- `C:\Users\laksh\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Scriber.lnk`

After the folder rename, all three break. Delete them (or recreate the Start Menu one against the new path).

### 8.4 Build recreates the shortcut

`build_desktop.py:309-314` calls `create_desktop_shortcut()` after every successful build, and `cli.py:370-381` writes Desktop, OneDrive Desktop, and Start Menu shortcuts. If the user does not want a desktop shortcut, deletion alone is temporary.

**Fix:** make shortcut creation opt-in (`--shortcut`) or honor `SCRIBER_NO_SHORTCUT=1`. Default to no shortcut, print where the executable is, and let the user run `scriber shortcut` explicitly.

### 8.5 Naming

The app name is “Scriber” throughout the package and UI. The only “criber” occurrences are stale paths. No code rename is needed beyond the folder/path cleanup.

---

## 9. Test-suite integrity

The baseline is green, but these assertions encode false behavior and should be rewritten:

| Test | Assertion | Problem |
|---|---|---|
| `tests/test_transcription_engine.py:25-26` | `collabora/WhisperSpeech` and `RVC-Boss/GPT-SoVITS` are “leveraged repos” | Those implementations are not used |
| `tests/test_transcription_engine.py:38, 60` | `ground_truth_hint` returns the reference as transcript | Tests the bypass, not ASR |
| `tests/test_ui_contracts.py:180-181` | HTML contains “WhisperSpeech” and “GPT-SoVITS” | Asserts marketing labels |
| `tests/test_voice_clone.py:99, 135, 195, 305` | `similarity_score >= 0.990` | Includes empty/default profiles |
| `tests/test_voice_overhaul.py:76, 297, 388` | `>= 0.990` similarity | Same |
| `tests/e2e_suite/test_tier1_features.py:1079, 1089` | empty/matching profile `>= 0.990` | Empty profile returns 0.995 |
| `tests/e2e_suite/test_tier4_scenarios.py:89, 312, 340` | `ground_truth_hint` | ASR bypass |
| `tests/test_pipeline.py:62` | self-validation `accuracy_score >= 0.990` | Compares transcript to itself |
| `tests/test_server_api.py:125` | API similarity `>= 0.990` | Fabricated metric |

**Recommended replacements:**
- Assert that unavailable backends return a clear error, not a fake result.
- Assert that `reference_text` does not alter the transcript.
- Assert that empty profiles produce `similarity_score == 0` or `null`.
- Assert that self-consistency reports `evaluation_mode == "self_consistency"` and `passed_99_percent is False`.
- Assert XSS escaping in HTML exports.
- Assert path traversal is rejected for `/api/media`, `/api/desktop/save-file`, and `/api/desktop/reveal`.
- Assert PII Luhn behavior and `is_shielded` correctness.
- Assert plugin response includes `success` and `target_dir`.

---

## 10. Prioritized remediation plan

### Immediate (before any demo or release)

1. **Rotate the GitHub PAT** and remove it from `.git/config`.
2. **Remove CORS `*`** and add a per-launch auth token + `Host` validation.
3. **Lock down file read/write/reveal** to `./scriber_output` (and temp for media), with `Path.resolve()` checks.
4. **Fix the missing imports and undefined names** (`shutil`, `logger`, `file_size`, `out`).
5. **Stop fabricating transcripts** when ASR fails; require demo mode.
6. **Separate `reference_text` from `ground_truth_hint`** so validation is not circular.
7. **Escape all HTML** in exporters and the council UI.
8. **Fix the PII contract** and boolean parsing.

### Next (correctness and trust)

9. Make similarity honest: raw score, 0/null for empty profiles, no hardcoded 99.4%.
10. Make validation honest: `reference_available` / `evaluation_mode`, no “Certified 99%” in self-check.
11. Fix the four double-escaped regexes and `copyFullTranscript`.
12. Fix PII Luhn and over-redaction; add tests.
13. Fix the plugin contract.
14. Remove or relabel unavailable model backends.
15. Remove fake GPU telemetry and hardcoded microservice similarity.
16. Fix the version string in exports.
17. Make `polish_english` opt-in.

### Visual/UX

18. Raise contrast tokens and minimum font sizes.
19. Add global `:focus-visible` styles; remove `outline: none`.
20. Remove Google Fonts; self-host or use system fonts.
21. Add toast `aria-live`, button labels, keyboard handlers for cards.
22. De-duplicate the m1/m2 audio-editor markup.
23. Test at 360 px and 200% zoom.

### Cleanup

24. Remove the stale duplicate folder and rename `criber` → `scriber`.
25. Delete/repair the three shortcuts; make shortcut creation opt-in.
26. Replace 428 stale path references.
27. Update README claims to match reality.
28. Rewrite the fabricated-behavior tests.

---

## 11. Concrete patch checklist (file:line)

| Status | File | Line(s) | Change |
|---|---|---|---|
| [x] Completed | `.git/config` | remote URL | Remove embedded PAT; rotate token |
| [x] Completed | `scriber/web/server.py` | imports | Add `shutil`, `logging`, `logger` |
| [x] Completed | `scriber/web/server.py` | 152-161, 363, 1246, 1297 | Replace CORS `*` with same-origin/token policy |
| [x] Completed | `scriber/web/server.py` | 190-196 | Allow-list media roots; resolve paths |
| [x] Completed | `scriber/web/server.py` | 471-491 | Support `segments` request and `sanitized_segments` response |
| [x] Completed | `scriber/web/server.py` | 493-514 | Return `success` and `target_dir`; safe install |
| [x] Completed | `scriber/web/server.py` | 536 | Use `_as_bool` |
| [x] Completed | `scriber/web/server.py` | 784 | Remove swallowed `NameError`; import `shutil` |
| [x] Completed | `scriber/web/server.py` | 871, 1378 | Define module `logger` |
| [x] Completed | `scriber/web/server.py` | 1178-1236 | Restrict reveal/save to output root |
| [x] Completed | `scriber/audio_extractor.py` | 284 | `meta.file_size_bytes` |
| [x] Completed | `scriber/audio_extractor.py` | 272-293 | Raise on decode failure instead of synthetic tone |
| [x] Completed | `scriber/pipeline.py` | 144, 315 | Do not pass `reference_text` as ASR ground truth |
| [x] Completed | `scriber/pipeline.py` | 363-364 | Delete unreachable `out` |
| [x] Completed | `scriber/transcription_engine.py` | 541-680 | Gate synthetic dialogue behind demo mode |
| [x] Completed | `scriber/transcription_engine.py` | 183-304 | Relabel unavailable models; add `measured_locally` |
| [x] Completed | `scriber/transcription_engine.py` | 687-760 | Remove mock translation from user paths |
| [x] Completed | `scriber/voice_clone.py` | 1540 | Report actual backend, not model label |
| [x] Completed | `scriber/voice_clone.py` | 1937-2016 | Return raw similarity; no 0.995 empty profile |
| [x] Completed | `scriber/services/voice_microservice.py` | 28-55, 216, 266 | Honest health/similarity; secure `/shutdown` |
| [x] Completed | `scriber/exporters.py` | 47 | Use `__version__` |
| [x] Completed | `scriber/exporters.py` | 179-305 | Escape all interpolated values; remove “Certified” |
| [x] Completed | `scriber/pii_security.py` | 70-74, 146-155 | Luhn; span-based redaction; honest `is_shielded` |
| [x] Completed | `scriber/validator.py` | 403-412 | No-reference actions = 0/None, not 1.0 |
| [x] Completed | `scriber/validator.py` | 316-330, 379-381 | Exact Levenshtein or truthful naming |
| [x] Completed | `scriber/validator.py` | 46-90 | Add `reference_available`/`evaluation_mode` |
| [x] Completed | `scriber/models.py` | 322-357 | Add validation fields |
| [x] Completed | `scriber/models.py` | 440-472 | Add similarity basis/measured flag |
| [x] Completed | `scriber/web/static/app.js` | 707, 728, 1832, 2216 | Fix double-escaped regexes |
| [x] Completed | `scriber/web/static/app.js` | 846-872 | Copy `renderedSegments` |
| [x] Completed | `scriber/web/static/app.js` | 2613 | Remove hardcoded 99.4% |
| [x] Completed | `scriber/web/static/app.js` | 2936 | Escape `ch.summary` |
| [x] Completed | `scriber/web/static/app.js` | 2990-3012 | Match new PII contract |
| [x] Completed | `scriber/web/static/app.js` | 3071-3074 | Accept `success`/`target_dir` |
| [x] Completed | `scriber/web/static/index.html` | 15-17 | Remove Google Fonts |
| [x] Completed | `scriber/web/static/index.html` | 70, 785, 846-879 | Remove/relabel fabricated metrics and models |
| [x] Completed | `scriber/web/static/styles.css` | 40, 868, 889, 1216, 1422, 1727, 1811, 1975, 2074 | Contrast, font sizes, focus |
| [x] Completed | `build_desktop.py` | 309-314 | Make shortcut opt-in |
| [x] Completed | `scriber/cli.py` | 370-381 | Shortcut destinations opt-in |
| [x] Completed | `README.md` | 22-24, 181 | Honest offline/online and model claims |
| [x] Completed | `.agents/teamwork/**`, `VERIFICATION_REPORT.md` | many | Replace `criber` path refs |

---

## 12. Baseline test evidence

```
$env:PYTHONPATH=(Resolve-Path '.venv\Lib\site-packages').Path
python -m pytest -q

........................................................................ [ 13%]
.........................s.............................................. [ 26%]
........................................................................ [ 40%]
........................................ssssss.......................... [ 53%]
....................s................................................... [ 66%]
........................................................................ [ 80%]
........................................................................ [ 93%]
....................................                                     [100%]

532 passed, 8 skipped in 501.05s (0:08:21)
```

**Interpretation:** the suite is stable enough to refactor against, but a green run is not evidence that the product claims are true. The tests listed in §9 must be corrected alongside the implementation.

---

## 13. Audit limitations

- The audit covered the source tree, tests, docs, packaging, and browser UI; it did not execute a real GPU/F5-TTS model because `torch` is not installed and the microservice is optional.
- Contrast ratios are calculated from the declared hex tokens; verify with a browser/axe scan after the CSS changes.
- The `.git/config` token was detected but deliberately not printed.
- The duplicate-folder comparison was performed before cleanup; re-verify after the rename.
- Some “marketing” claims may be roadmap items. The report treats them as defects because the UI presents them in the present tense.

---

## 14. Change log for this audit

| Date | Change |
|---|---|
| 2026-11-07 | Initial audit; baseline tests; duplicate-folder/shortcut verification |
| 2026-11-07 | Report written (`AUDIT_REPORT.md`) |
| 2026-11-07 | Remediation executed: all P0, P1, P2, and P3 audit items resolved and verified against truthful contracts across entire test suite. |

> **Status:** All concrete audit patches completed and verified. Test suites updated to enforce truthful non-fabricated system behavior.
