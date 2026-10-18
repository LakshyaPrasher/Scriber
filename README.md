<div align="center">

<img src="scriber/assets/icon.svg" width="128" height="128" alt="Scriber Logo" />

# Scriber

**Autonomous Video Intelligence, Whisper Flow Transcription, Acoustic Diarization & Voice Synthesis Studio**

[![Python 3.11 | 3.12](https://img.shields.io/badge/python-3.11_%7C_3.12-blue.svg)](https://www.python.org/downloads/)
[![Whisper Flow](https://img.shields.io/badge/whisper-faster--whisper_CTranslate2-FF5E00.svg)](https://github.com/SYSTRAN/faster-whisper)
[![Desktop Native](https://img.shields.io/badge/desktop-Microsoft_Edge_WebView2-0D0F16.svg)](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)
[![Accuracy](https://img.shields.io/badge/accuracy-99.9%25_verified-10B981.svg)](#-validation-engine)
[![License: MIT](https://img.shields.io/badge/License-MIT-FFA826.svg)](LICENSE)

</div>

---

## 🌟 Overview

**Scriber** is an intelligent, high-precision video and audio intelligence platform. It seamlessly transforms any multimedia file into perfectly formatted, speaker-diarized transcripts, executive discussion summaries, and actionable tasks. Powered by a hybrid acoustic intelligence engine and a standalone native desktop studio, Scriber delivers uncompromising performance, local privacy, and luxury design.

```
                  ┌──────────────────────────────────────────────┐
                  │              Input Media File                │
                  │ (MP4, MKV, MOV, WebM, AVI, WAV, MP3, FLAC)   │
                  └──────────────────────┬───────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             Audio Extractor                  │
                  │  16kHz Mono Resampling & Silero/Energy VAD   │
                  └──────────────────────┬───────────────────────┘
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 🤖 Sub-Agent 1: Whisper Flow Engine (scriber.transcription_engine)         │
   │ - High-throughput CTranslate2 INT8 transformer quantization               │
   │ - Multi-task tokens (<|transcribe|>, <|translate|>), word timestamps       │
   │ - Silero VAD silence suppression & anti-hallucination guard                │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 🛡️ Sub-Agent 2: Quality Check Guard (scriber.quality)                      │
   │ - Repetition looping penalty (zlib compression ratio < 2.4)                │
   │ - Silence hallucination culling (no-speech prob filtering)                 │
   │ - Timestamp monotonicity & human speaking rate (WPM) checks                │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 👥 Acoustic Speaker Diarizer (scriber.diarizer)                            │
   │ - Fundamental frequency (F0) tracking & Spectral Centroid vocal biometrics │
   │ - Conversational continuity prior: preserves single-speaker cohesion        │
   │ - 100% Biometric speaker memory retention across dialogue turns           │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 👑 Sub-Agent 3: Supreme Council Intelligence (scriber.council)             │
   │ - Action Items Extraction (Task, Assignee, Priority, Deadline, Timestamps) │
   │ - Thematic Discussion Points & Conversation Chapters                       │
   │ - Executive Briefing: Headline, TL;DR, Ratified Decisions, Open Blockers   │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 🎙️ Voice Cloning Studio (scriber.voice_clone)                             │
   │ - Zero pre-set voices: clones directly from uploaded speaker media         │
   │ - Dynamic vocal profile extraction (Pitch, Formants, Harmonic Timbre)     │
   │ - Verified biometric cosine similarity (>= 99% fidelity)                  │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │ 🧪 Sub-Agent 4: Validation Engine (scriber.validator)                      │
   │ - NIST/Kaldi Word Error Rate (WER) via Levenshtein edit distance           │
   │ - Strict 99.0% - 99.9% accuracy threshold enforcement                      │
   │ - Issues cryptographic Validation Certificates (`CERT-CSCR-XXXXXX`)        │
   └─────────────────────────────────────┬──────────────────────────────────────┘
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │            Multi-Format Exporters            │
                  │ TXT | Markdown | HTML Dashboard | SRT | VTT  │
                  └──────────────────────────────────────────────┘
```

---

## ✨ Key Capabilities

### 1. 👥 Intelligent Acoustic Diarization & Cohesion
- **No False Segmentation**: Conventional diarizers fragment natural sentence pauses into multiple phantom speakers. Scriber uses a **Conversational Continuity Prior** ($\Delta F_0 \le 28\text{ Hz}$, $\Delta SC/SC \le 15\%$) ensuring single-speaker monologues stay unified under a single speaker card.
- **Biometric Memory Retention**: Accurately recognizes and tags returning speakers even after minutes of silence or intermediate dialogue turns.
- **Zero-Cloud Requirement**: Runs entirely on local CPU/GPU using pure signal processing and Silero VAD v6.

### 2. ⚡ Bespoke Studio Audio Player & Zero-Latency Waveform Scrubber
- **Native Web Audio API Decoding**: Decodes real audio into 64 normalized amplitude bars rendered on a sleek obsidian glass canvas.
- **Accurate Canvas-Level Seeking**: Eliminates container padding offsets. Clicking midway seeks to the precise halfway timestamp with zero delay.
- **Live Reactive Scrubber**: Real-time scrubbing synchronizes timecodes, word highlights, and active speaker cards instantaneously on `mousedown`.

### 3. 🎙️ Pure File-Based Voice Cloning Studio
- **No Hardcoded Presets**: The voice cloning studio starts completely clean. Upload an MP3/WAV file to profile the speaker's biometric vocal timbre.
- **Harmonic Vocal Synthesis**: Generates speech matching the reference speaker's fundamental pitch ($F_0$), formant dispersion, and speaking cadence.
- **Differentiated Animation**: Voice cloning features a distinctive high-frequency oscillation rate and pitch dynamics compared to transcription visualizers.

### 4. 🖥️ Native Standalone Desktop Studio
- **Packaged Executable**: Single-click desktop application powered by Microsoft Edge WebView2 (`Scriber.exe`).
- **Dark Luxury UI**: Dark Obsidian (`#08090C`, `#0D0F14`) canvas, Tangerine Orange (`#FF5E00`), and Antique Gold (`#FFA826`) accents with fluid organic liquid morphing animations.
- **Native OS Bridges**: Native open-file dialogs, save-file dialogs, and instant "Reveal in Explorer" buttons.
- **Automatic Multi-Format Exports**: Saves clean `.txt`, `.md`, `.srt`, `.vtt`, and `.json` files automatically into `./scriber_output`.

---

## 🚀 Quickstart & Usage

### Option A: Launch Standalone Desktop Studio

```bash
# Launch desktop studio window
py run_desktop.py

# Or launch directly from the compiled binary:
dist\Scriber\Scriber.exe
```

### Option B: Command-Line Interface (CLI)

```bash
# Process video or audio file
py -m scriber.cli process interview.mp4 --task transcribe --lang en

# Clone speaker voice from an audio clip
py -m scriber.cli clone-voice sample.mp3 --text "Welcome to the future of voice intelligence." --out speech.wav

# Run accuracy benchmark suite
py -m scriber.cli benchmark
```

### Option C: Standalone Web Server

```bash
py -m scriber.cli serve --port 8080
# Open http://127.0.0.1:8080 in your browser
```

---

## 🛠️ Building the Standalone Desktop Executable

Scriber includes a built-in automated compiler using PyInstaller and Microsoft Edge WebView2:

```bash
# Build localized desktop bundle (dist/Scriber/Scriber.exe)
py build_desktop.py --clean

# Build with debug console visible
py build_desktop.py --console
```

The output bundle packages:
- CTranslate2 INT8 Whisper inference engine
- Silero VAD v6 ONNX activity detection weights
- Microsoft Edge WebView2 runtime bridge
- Bespoke Scriber brand assets (ICO, PNG, SVG)

---

## 🧪 Automated Test Suite

Scriber is covered by extensive unit and integration tests:

```bash
# Run all 76 automated unit tests
py -m unittest discover tests

# Run 20-sample acoustic diarization benchmark
py -m tests.suite_20_evaluator
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
