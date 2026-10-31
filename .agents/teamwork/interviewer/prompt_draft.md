Fix Scriber for daily production use by profiling and resolving excessive processing delays in VAD segmentation to achieve real-time or faster performance, correcting speaker diarization so single-speaker monologues do not shatter across natural pauses, and eliminating all paid API links and bridges so all features run 100% locally and free on the host RTX 5050 GPU with zero financial exposure, rebuilding the desktop application and deploying to GitHub.

Working directory: c:\Users\laksh\.gemini\antigravity\scratch\criber
Integrity mode: development

## Requirements

### R1. VAD Segmentation Performance & Speed
Debug and profile the VAD segmentation pipeline directly against `C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4` on the host RTX 5050 GPU. Optimize Phase 2/4 VAD Segmentation ("Voice Activity Detection & Filtering - Isolating human speech boundaries · Culling ambient silence") so processing achieves real-time or faster execution (total segmentation processing time less than media playback duration).

### R2. Speaker Diarization Accuracy & Monologue Cohesion
Fix the speaker segmentation failure where a single speaker is shattered into multiple speakers across natural sentence pauses. Using `C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4` as the benchmark, ensure all speech segments from the monologue are correctly grouped and assigned to a single speaker rather than three separate speakers.

### R3. Elimination of Paid APIs & 100% Local / Free Operation
Remove all paid API links, dependencies, bridges, and references across both UI and backend (including Voicemaker.in Cloud Studio and API bridge). Ensure zero financial exposure and zero open taps: all application features (transcription, diarization, voice cloning) must execute 100% locally and free using the host RTX 5050 GPU and offline/unmetered engines.

### R4. Verification, Build, Desktop Shortcut & Git Push
Verify changes against the target test video and the existing test suite, synthesizing additional audio test cases as needed. Rebuild the standalone desktop executable bundle, update the Windows desktop shortcut to launch the rebuilt application, and commit and push all changes to the remote origin repository on GitHub.

## Verification Resources
- Test video: `C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4`
- Existing repository test suites
- Team-synthesized test cases for VAD and diarization as needed

## Acceptance Criteria

### VAD Performance
- [ ] Phase 2/4 VAD segmentation executes in real-time or faster (processing time < media duration) on `C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4` using local hardware.

### Speaker Diarization
- [ ] Profiling and running diarization on `C:\Users\laksh\Downloads\VIRAT KOHLI DEEPFAKE NO CAPTIONS.mp4` outputs a single unified speaker for the entire monologue, with no shattering across pauses into Speaker 1, 2, or 3.

### Local & Free Execution
- [ ] All paid API endpoints, references, and bridges (including Voicemaker.in Cloud Studio) are removed from the UI and backend.
- [ ] Voice cloning, transcription, and diarization run fully offline and locally without making outbound network calls to paid API services or incurring financial costs.

### Build & Deployment
- [ ] Automated tests pass.
- [ ] Desktop executable bundle is rebuilt and verified to launch.
- [ ] Desktop shortcut is updated to point to the rebuilt application.
- [ ] All commits are pushed to the current branch on the remote origin repository on GitHub.
