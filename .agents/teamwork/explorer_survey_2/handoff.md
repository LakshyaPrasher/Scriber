# Survey Explorer 2 Handoff Report: Whisper Turbo Cache & Acoustic Speaker Diarization

## 1. Observation

### A. Whisper / Whisper Turbo Model Cache & Execution Pipeline
1. **Model Registry & Resolution**:
   - In `scriber/transcription_engine.py` (lines 119-126):
     ```python
     "turbo": {
         "id": "turbo",
         "name": "Whisper Turbo (large-v3-turbo)",
         "ct2_name": "deepdml/faster-whisper-large-v3-turbo-ct2",
         "params": "809M INT8",
         "description": "OpenAI SOTA transformer architecture with 4 decoder layers, offering 8x speedup over large-v3 while retaining near-identical WER.",
     },
     ```
   - In `faster_whisper.utils._MODELS` (verified in `.venv` faster-whisper 1.2.1):
     `'large-v3-turbo': 'mobiuslabsgmbh/faster-whisper-large-v3-turbo'`
     `'turbo': 'mobiuslabsgmbh/faster-whisper-large-v3-turbo'`
2. **Fallback Execution Loop**:
   - In `scriber/transcription_engine.py` (lines 643-670):
     ```python
     target_model = os.environ.get("WHISPER_MODEL")
     if not target_model:
         model_info = SUPPORTED_TRANSCRIBE_MODELS.get(model_name.lower())
         target_model = model_info["ct2_name"] if model_info else model_name

     is_whisperx = (model_name.lower() == "whisperx")

     model = None
     active_model_id = target_model
     fallback_occurred = False
     candidates = [target_model]
     if target_model != "base":
         candidates.append("base")
     if "tiny" not in candidates:
         candidates.append("tiny")

     for candidate in candidates:
         try:
             model = faster_whisper.WhisperModel(candidate, device="cpu", compute_type="int8", local_files_only=True)
             active_model_id = candidate
             if candidate != target_model:
                 fallback_occurred = True
             break
         except Exception:
             continue
     ```
   - Note that `local_files_only=True` is hardcoded for the candidate list.
3. **Physical Cache Directory Inspection**:
   - Hugging Face cache root: `C:\Users\laksh\.cache\huggingface\hub`
   - Target directory: `C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2`
   - Snapshot directory: `snapshots\4df90f75321148c3a29a9e2351b7ddf8f5b115a8\`
     - `config.json` (2,263 bytes) — present
     - `preprocessor_config.json` (340 bytes) — present
     - `tokenizer.json` (2,710,337 bytes) — present
     - `vocabulary.json` (1,068,114 bytes) — present
     - `model.bin` — **MISSING**
   - Blob directory: `blobs\`
     - `e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da.8a7c7054.incomplete` (268,283,012 bytes)
   - Remote repository check (`https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2/resolve/main/model.bin`):
     - Remote file size: `1,617,884,929 bytes` (~1.61 GB)
4. **Verbatim Exception on Direct Execution**:
   Running `faster_whisper.WhisperModel('deepdml/faster-whisper-large-v3-turbo-ct2', device='cpu', compute_type='int8', local_files_only=True)` produces:
   ```
   huggingface_hub.errors.IncompleteSnapshotError: The cached snapshot for 'deepdml/faster-whisper-large-v3-turbo-ct2' (revision 'main', commit 4df90f75321148c3a29a9e2351b7ddf8f5b115a8) is incomplete: 1 file(s) are missing (model.bin). Outgoing traffic is disabled ('local_files_only=True'). Re-run the download with network access to complete the snapshot.
   ```
   Because `except Exception:` catches this error without logging or raising, candidate 1 fails and candidate 2 (`"base"`) is selected. `models--Systran--faster-whisper-base` contains complete files (`model.bin` 145,217,532 bytes), so `WhisperModel("base", ...)` succeeds and returns `backend_used="SYSTRAN/faster-whisper (base [offline fallback from turbo])"`.

---

### B. Acoustic Speaker Diarization Subsystem
1. **Existing Diarization Engine**:
   - In `scriber/diarizer.py`:
     - `SpeakerMemory` (lines 26-117): Keeps track of running `centroid_vector` (16-d), duration-weighted `mean_f0`, `mean_centroid`, `gender`, and formants. Computes `match_score` using a composite distance:
       ```python
       dist = (0.25 * pitch_dist) + (0.30 * sc_dist) + (0.35 * cos_dist) + (0.10 * formant_dist) + gender_penalty
       ```
       with conversational continuity discount (`dist *= 0.60`) if active speaker and pause $\le 2.5$s.
     - `AcousticDiarizer.diarize_segments` (lines 125-292):
       Slices PCM audio per segment, extracts `p = VoiceProfiler.profile_from_pcm16(seg_pcm)`, normalizes the 16-d `p.voice_vector`, builds pairwise distance matrix via `compute_acoustic_distance(p1, p2)`, and executes Agglomerative Hierarchical Clustering (AHC) using average linkage with distance threshold:
       ```python
       distance_threshold = 0.78 * (0.48 / max(0.1, self.similarity_threshold))
       ```
       followed by inter-cluster centroid consolidation.
2. **Existing 16-d Handcrafted Feature Extractor**:
   - In `scriber/voice_clone.py` (lines 33-136, `VoiceProfiler.profile_from_pcm16`):
     - Computes F0 pitch contour via octave-aware normalized autocorrelation (60-380 Hz).
     - Computes spectral centroid (center of mass of FFT power spectrum).
     - Computes zero crossing rate (ZCR), RMS energy, cadence WPM, gender estimate.
     - Computes formants F1-F3 via LPC autocorrelation.
     - Computes 9 sub-band spectral energy ratios (0-250Hz, 250-500Hz, 500-1000Hz, 1000-2000Hz, 2000-3000Hz, 3000-4000Hz, 4000-6000Hz, 6000-8000Hz, >8000Hz).
     - Combines them into a 16-element float vector.
3. **Hardware & Environment Dependencies**:
   - `onnxruntime==1.31.0` is already installed in `.venv`.
   - `ctranslate2==4.8.3` and `faster-whisper==1.2.1` are already installed in `.venv`.
   - `dist/Scriber/_internal/onnxruntime` and `faster_whisper` are already packaged in PyInstaller build.
   - `sherpa-onnx` version 2.0.1 is available on PyPI with official Windows x64 Python 3.12 pre-built wheels (`sherpa_onnx-2.0.1-cp312-cp312-win_amd64.whl`).
4. **Target Neural ONNX Models**:
   - **CAM++ (`welcomyou/campplus-3dspeaker-200k-onnx` / `csukuangfj/speaker-embedding-models: 3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx`)**:
     - Model file size: `28,281,164 bytes` (~28.28 MB).
     - Architecture: DenseNet / Context-Aware Masking backbone trained on 200k+ speakers across multi-lingual datasets (VoxCeleb + 3D-Speaker).
     - Input shape: `[1, T, 80]` (80-bin log mel-filterbank features with CMVN at 16kHz).
     - Output shape: `[1, 192]` (192-dimensional unit-normalized speaker embedding vector).
     - Distance metric: Cosine distance $1.0 - \mathbf{u} \cdot \mathbf{v}$. Equal Error Rate (EER) on VoxCeleb1 $< 0.7\%$.

---

## 2. Logic Chain

1. **Root Cause of Whisper Turbo Fallback**:
   - Observation A.3 shows that in `C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2\blobs\`, the model weight file `model.bin` exists only as an incomplete download blob (`e76620...incomplete`, 268 MB out of 1.61 GB).
   - Observation A.2 shows that `transcription_engine.py` attempts to instantiate `faster_whisper.WhisperModel(candidate, local_files_only=True)`.
   - Observation A.4 confirms that `huggingface_hub` raises `IncompleteSnapshotError` because `model.bin` is missing from the snapshot directory.
   - The loop in `transcription_engine.py` catches `Exception` and advances to candidate `"base"`, which exists and loads.
   - **Therefore**: The fallback to Base is not caused by missing code or unsupported model architecture; it is caused specifically by an interrupted download of `model.bin` in the local HuggingFace cache combined with `local_files_only=True`.

2. **Remediation for Whisper Turbo**:
   - Since network connectivity to `https://huggingface.co/` is functional (verified via HTTP HEAD in Observation A.3), downloading the complete `model.bin` (or invoking `huggingface_hub.snapshot_download("deepdml/faster-whisper-large-v3-turbo-ct2", local_files_only=False)` once) will place the complete 1.61 GB file in the snapshot directory.
   - Once `model.bin` is complete, `WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8", local_files_only=True)` loads without error, eliminating fallback to Base.
   - Furthermore, adding model repair/recovery logic in `transcription_engine.py` (checking if snapshot is incomplete and triggering an interactive or background download before falling back) prevents this failure mode permanently.

3. **Weaknesses of Current Diarization**:
   - Observation B.1 and B.2 reveal that speaker clustering relies entirely on heuristic thresholds: pitch difference (semitones), spectral centroid shift (%), ZCR, and 9 sub-band energy ratios.
   - Distinct speakers of the same gender frequently share overlapping pitch ranges (120-140 Hz for men, 180-220 Hz for women).
   - Natural expressive inflection in a single speaker (e.g. asking an enthusiastic question vs calm statement) creates 3-4 semitone pitch swings, risking false fragmentation.
   - While the handcrafted heuristics were tuned to pass `suite_20_evaluator.py`, they lack deep acoustic timbre invariance across varied real-world microphones, acoustics, and accents.

4. **Neural Diarization Integration Strategy**:
   - Observation B.3 confirms that `onnxruntime` 1.31.0 is already present in `.venv` and packaged in `dist/Scriber/`.
   - Observation B.4 shows that CAM++ is an ultra-compact (28.2 MB) ONNX model that maps 16kHz speech to a 192-dimensional embedding space where cosine distance directly measures speaker identity.
   - Two viable implementation paths exist:
     - **Path 1 (Pure onnxruntime + numpy 80-bin Mel Fbank)**: Requires zero new pip dependencies. Uses existing `onnxruntime` to run `campplus_cn_en_common.onnx`. Computes 80-bin triangular mel filterbank in pure numpy.
     - **Path 2 (`sherpa-onnx`)**: Adds `sherpa-onnx` (pre-built Windows wheel on PyPI), which contains native C++ Kaldi Fbank extraction and offline speaker embedding extraction in a high-level API.
   - Recommended robust architecture: Implement a `NeuralSpeakerExtractor` class that attempts `sherpa_onnx.SpeakerEmbeddingExtractor` first; if absent, executes via direct `onnxruntime.InferenceSession` with numpy Mel-Fbank; and if the ONNX model is missing, falls back cleanly to the existing 16-d `VoiceProfiler` DSP heuristic.
   - In `AcousticDiarizer.compute_acoustic_distance`, replace the handcrafted sum with cosine distance: $D = 1.0 - \max(0.0, \mathbf{e}_1 \cdot \mathbf{e}_2)$, applying the continuity discount for adjacent turns. In `SpeakerMemory`, maintain the 192-d normalized centroid vector.

---

## 3. Caveats

1. **Whisper Turbo VRAM / RAM Footprint**:
   - Large-v3-Turbo requires ~1.25 GB of RAM when running INT8 on CPU, compared to ~180 MB for Base. On machines with very low available memory, CPU inference will take longer (~2.0-3.5s per 10s audio chunk vs ~0.5s for Base).
2. **Audio Chunk Length for Neural Embeddings**:
   - Deep neural embeddings (CAM++ / 3D-Speaker) perform best on speech segments $\ge 0.5$ seconds. For very short segments (< 0.25s, e.g. single-syllable interjections like "yeah", "uh-huh"), the extractor should either pad the segment or rely on the conversational continuity prior to retain the active speaker.
3. **Synthetic Sine Wave Unit Tests**:
   - `tests/test_diarizer_accuracy.py` contains `test_multi_speaker_segregation`, which generates pure synthetic sine waves (120 Hz and 240 Hz). While CAM++ produces different activations for different harmonic frequencies, retaining a fallback or hybrid blend with acoustic pitch features guarantees that artificial sine-wave unit tests and authentic human speech both pass seamlessly.
4. **PyInstaller Distribution Size**:
   - Bundling the 28.2 MB CAM++ ONNX model into `scriber/assets/models/` will slightly increase the `dist/Scriber/` directory size from ~650 MB to ~678 MB, which is completely acceptable for a native desktop application. Whisper Turbo (1.61 GB) should remain in the user cache directory (`%USERPROFILE%\.cache\huggingface\hub` or `%LOCALAPPDATA%\Scriber\models`) rather than embedded directly into the PyInstaller binary.

---

## 4. Conclusion

1. **Whisper Turbo**:
   - **Root Cause**: The model cache in `C:\Users\laksh\.cache\huggingface\hub\models--deepdml--faster-whisper-large-v3-turbo-ct2` has an incomplete download blob (`e766...incomplete` at 268 MB) and lacks `model.bin` in the snapshot directory. `faster_whisper` raises `IncompleteSnapshotError` under `local_files_only=True`, prompting silent fallback to `"base"`.
   - **Remedy**:
     - Complete the download of `model.bin` (1.61 GB) into the Hugging Face cache using `huggingface_hub.snapshot_download("deepdml/faster-whisper-large-v3-turbo-ct2", local_files_only=False)`.
     - Update `transcription_engine.py` to handle cache validation gracefully, enabling automated download/repair when internet connectivity is detected.
2. **Acoustic Diarization**:
   - **Root Cause**: The current pipeline uses handcrafted 16-d acoustic vectors (pitch, spectral centroid, ZCR, formants) that are vulnerable to pitch inflection and cannot separate similar-pitched speakers reliably.
   - **Remedy**:
     - Acquire CAM++ ONNX model (`campplus_cn_en_common_200k.onnx`, 28.2 MB) and store in `scriber/assets/models/`.
     - Integrate deep neural embedding extraction via `onnxruntime` (already available) or `sherpa-onnx`.
     - Update `AcousticDiarizer` and `SpeakerMemory` to cluster on 192-d L2-normalized embeddings using cosine distance ($1.0 - \mathbf{u} \cdot \mathbf{v}$) with continuity priors.
     - Keep the existing 16-d DSP heuristic as a zero-dependency fallback.

---

## 5. Verification Method

### 1. Whisper Turbo Execution Verification
Run the following PowerShell command in the project root:
```powershell
& .\.venv\Scripts\python.exe -c "
import faster_whisper
model = faster_whisper.WhisperModel('deepdml/faster-whisper-large-v3-turbo-ct2', device='cpu', compute_type='int8', local_files_only=True)
print('Successfully loaded model:', model)
"
```
- **Pass condition**: Successfully prints the `WhisperModel` object with zero exceptions.
- **Invalidation condition**: Raises `IncompleteSnapshotError` or `LocalEntryNotFoundError`.

Test via Scriber `TranscriptionEngine`:
```powershell
& .\.venv\Scripts\python.exe -c "
from scriber.transcription_engine import TranscriptionEngine
engine = TranscriptionEngine()
pcm = b'\x00' * (16000 * 2 * 2)
res = engine.transcribe(pcm, duration=2.0, model='turbo')
print('Backend used:', res.backend_used)
print('Model name:', res.model_name)
assert 'fallback' not in res.backend_used.lower(), 'Failed: Model fell back to base!'
"
```
- **Pass condition**: `Backend used: SYSTRAN/faster-whisper (turbo)` and `fallback` is absent.

### 2. Deep ONNX Diarizer Verification
Verify ONNX model inference with `onnxruntime`:
```powershell
& .\.venv\Scripts\python.exe -c "
import onnxruntime as ort
import numpy as np
session = ort.InferenceSession('scriber/assets/models/campplus_cn_en_common_200k.onnx', providers=['CPUExecutionProvider'])
dummy_fbank = np.random.randn(1, 200, 80).astype(np.float32)
out = session.run(None, {session.get_inputs()[0].name: dummy_fbank})[0]
print('Embedding shape:', out.shape)
assert out.shape == (1, 192), f'Unexpected embedding shape {out.shape}'
print('ONNX CAM++ inference test passed.')
"
```
- **Pass condition**: Prints `Embedding shape: (1, 192)`.

### 3. Diarizer Accuracy & Suite Verification
Execute both the standard diarization test and the comprehensive 20-sample benchmark:
```powershell
& .\.venv\Scripts\python.exe -m unittest tests/test_diarizer_accuracy.py
$env:PYTHONPATH="."
& .\.venv\Scripts\python.exe tests/suite_20_evaluator.py
```
- **Pass condition**: `test_diarizer_accuracy.py` passes all tests; `suite_20_evaluator.py` achieves 20/20 PASS (100.0%) with 0.0% single-speaker false fragmentation rate and 100.0% multi-speaker segregation accuracy.
