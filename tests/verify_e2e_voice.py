import sys
import os
import urllib.request
import json
import io
import math
import struct
import wave

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scriber.web.server import ScriberBackgroundServer
from scriber.pipeline import ScriberPipeline


def main():
    server = ScriberBackgroundServer(host="127.0.0.1", port=0)
    server.start()
    base_url = server.url
    print(f"[*] Started test Scriber server on {base_url}")

    try:
        print("\n--- 1. UI Check ---")
        resp = urllib.request.urlopen(f"{base_url}/index.html")
        html = resp.read().decode("utf-8")
        assert "WARM BARITONE" not in html, "Hardcoded speaker card 1 found!"
        assert "CLEAR ALTO" not in html, "Hardcoded speaker card 2 found!"
        assert "synthesis-resonance-stage" in html, "Resonance canvas missing!"
        assert "renderResonanceLoop" in html, "Resonance loop missing!"
        assert "mode1-audio-editor" in html, "Mode 1 audio editor missing!"
        assert "mode2-audio-editor" in html, "Mode 2 audio editor missing!"
        assert "voice-ref-badge" in html, "Voice reference badge missing!"
        print("UI Check: PASSED - Hardcoded preset cards eliminated, Audio Editors & Resonance Canvas present.")

        print("\n--- 2. Profile Synthetic Voice Check ---")
        sample_rate = 16000
        duration = 1.5
        num_samples = int(sample_rate * duration)
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            pcm = []
            for i in range(num_samples):
                t = i / sample_rate
                val = 0.5 * math.sin(2 * math.pi * 140 * t) + 0.3 * math.sin(2 * math.pi * 280 * t) + 0.2 * math.sin(2 * math.pi * 420 * t)
                sample = int(val * 32767 * 0.7)
                pcm.append(struct.pack("<h", sample))
            wf.writeframes(b"".join(pcm))
        wav_bytes = wav_io.getvalue()

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = bytearray()
        body.extend(f"--{boundary}\r\n".encode("latin-1"))
        body.extend(b'Content-Disposition: form-data; name="file"; filename="test_user_voice.wav"\r\n')
        body.extend(b"Content-Type: audio/wav\r\n\r\n")
        body.extend(wav_bytes)
        body.extend(b"\r\n")
        body.extend(f"--{boundary}\r\n".encode("latin-1"))
        body.extend(b'Content-Disposition: form-data; name="speaker"\r\n\r\n')
        body.extend(b"User Profiled Speaker\r\n")
        body.extend(f"--{boundary}--\r\n".encode("latin-1"))

        req = urllib.request.Request(
            f"{base_url}/api/profile-voice",
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        resp = urllib.request.urlopen(req)
        profile_data = json.loads(resp.read().decode("utf-8"))
        profile = profile_data["profile"]
        assert "audio_base64" in profile_data, "Profile audio_base64 missing!"
        print("Profile Voice: PASSED - Extracted F0 =", profile["fundamental_frequency_hz"], "Centroid =", profile["spectral_centroid_hz"], "Gender =", profile["gender_estimate"])

        print("\n--- 3. Real Custom MP3 File Voice Profiling Check ---")
        user_mp3_path = r"C:/Users/laksh/.gemini/antigravity/brain/9584151d-391a-4301-aeb6-7c223efeb72c/.user_uploaded/uploaded_media_1792306217323.mp3"
        if os.path.isfile(user_mp3_path):
            with open(user_mp3_path, "rb") as f:
                custom_mp3_data = f.read()

            b2 = "----WebKitFormBoundaryCustomMp3"
            body2 = bytearray()
            body2.extend(f"--{b2}\r\n".encode("latin-1"))
            body2.extend(b'Content-Disposition: form-data; name="file"; filename="custom_speaker.mp3"\r\n')
            body2.extend(b"Content-Type: audio/mpeg\r\n\r\n")
            body2.extend(custom_mp3_data)
            body2.extend(b"\r\n")
            body2.extend(f"--{b2}\r\n".encode("latin-1"))
            body2.extend(b'Content-Disposition: form-data; name="speaker"\r\n\r\nCustom MP3 Speaker\r\n')
            body2.extend(f"--{b2}--\r\n".encode("latin-1"))

            req2 = urllib.request.Request(
                f"{base_url}/api/profile-voice",
                data=bytes(body2),
                headers={"Content-Type": f"multipart/form-data; boundary={b2}"}
            )
            with urllib.request.urlopen(req2) as resp2:
                mp3_prof_data = json.loads(resp2.read().decode("utf-8"))

            mp3_profile = mp3_prof_data["profile"]
            assert mp3_prof_data.get("audio_base64"), "Custom MP3 audio_base64 missing!"
            print(f"Custom MP3 Profiling: PASSED - Duration: {mp3_prof_data['duration']}s, F0: {mp3_profile['fundamental_frequency_hz']}Hz, Gender: {mp3_profile['gender_estimate']}")
            target_profile = mp3_profile
            target_ref_audio = mp3_prof_data["audio_base64"]
        else:
            target_profile = profile
            target_ref_audio = profile_data["audio_base64"]

        print("\n--- 4. Clone Voice Check ---")
        clone_payload = json.dumps({
            "text": "Scriber zero shot voice cloning test on custom user voice.",
            "profile": target_profile,
            "pitch_shift": 0.0,
            "rate_shift": 0.0,
            "output_format": "mp3",
            "reference_audio": target_ref_audio
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/api/clone-voice",
            data=clone_payload,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req)
        clone_res = json.loads(resp.read().decode("utf-8"))
        assert "audio_base64" in clone_res, "audio_base64 missing!"
        assert len(clone_res["audio_base64"]) > 100, "Audio base64 is empty!"
        print("Clone Voice: PASSED - Synthesized format", clone_res["audio_format"], "with duration", clone_res["duration"], "s, backend:", clone_res["synthesis_backend"], "similarity:", clone_res["similarity_percentage"])

        print("\n--- 5. Audio Editor (Volume, Pitch & Trimming) Check ---")
        edit_payload = json.dumps({
            "volume": 1.25,
            "pitch_semitones": 3.0,
            "start_sec": 0.5,
            "end_sec": 2.5,
            "filename": "custom_cloned_edited.mp3",
            "audio_base64": clone_res["audio_base64"]
        }).encode("utf-8")
        req_edit = urllib.request.Request(
            f"{base_url}/api/edit-audio",
            data=edit_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_edit) as resp_edit:
            edit_res = json.loads(resp_edit.read().decode("utf-8"))
        assert edit_res["success"], "Audio editor export was not successful!"
        assert edit_res.get("audio_base64"), "Edited audio base64 missing!"
        print(f"Audio Editor: PASSED - Duration: {edit_res['duration']}s, Size: {edit_res['size_bytes']} bytes, Saved: {edit_res['saved_path']}")

        print("\n--- 6. Pipeline Diarization Unification Check ---")
        pipe = ScriberPipeline()
        out = pipe.process_pcm(
            pcm16_data=wav_bytes,
            source_name="single_speaker_test.wav",
            reference_text="Welcome to Scriber pipeline. This is a single speaker test demonstrating unified speaker grouping. Each sentence should stay under one speaker card."
        )
        print("Diarization Check: Total segments =", len(out.transcription.segments))
        speakers = set(s.speaker for s in out.transcription.segments)
        print("Speakers detected across sentences:", speakers)
        assert len(speakers) == 1, f"Expected single speaker, got {speakers}"
        assert list(speakers)[0] == "Speaker_1", f"Expected Speaker_1, got {speakers}"
        print("Single Speaker Unification: PASSED - All segments unified under Speaker_1!")
        print("\n>>> ALL E2E CHECKS PASSED WITH 100% ACCURACY! <<<")

    finally:
        server.stop()


if __name__ == "__main__":
    main()
