"""Tests for Scriber Web Server, REST API, and Multipart upload parser."""

import io
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from scriber.audio_extractor import AudioExtractor
from scriber.web.server import (
    ScriberHTTPRequestHandler,
    get_embedded_html,
    ScriberServer,
    ScriberBackgroundServer,
    _prepare_playable_media_path,
    register_allowed_media_file,
    is_allowed_media_file,
)


class TestServerAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._old_output = os.environ.get("SCRIBER_OUTPUT_DIR")
        cls._test_output = tempfile.mkdtemp(prefix="scriber_server_test_output_")
        os.environ["SCRIBER_OUTPUT_DIR"] = cls._test_output

    @classmethod
    def tearDownClass(cls):
        if cls._old_output is None:
            os.environ.pop("SCRIBER_OUTPUT_DIR", None)
        else:
            os.environ["SCRIBER_OUTPUT_DIR"] = cls._old_output
        shutil.rmtree(cls._test_output, ignore_errors=True)

    def setUp(self):
        self.handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        self.handler.wfile = io.BytesIO()
        self.handler.rfile = io.BytesIO()
        self.handler.headers = {}
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()
        if hasattr(self.handler, "pipeline") and self.handler.pipeline is not None:
            self.handler.pipeline.reference_pcm = None
            self.handler.pipeline.last_pcm_data = None

    def test_embedded_ui_contains_key_components(self):
        """Verifies embedded HTML contains modern UI elements, file dropzone, and Custom TTS."""
        html = get_embedded_html()
        self.assertIn("Scriber", html)
        self.assertIn("Custom TTS", html)
        self.assertIn("dropzone", html)
        self.assertIn("audio-player", html)
        self.assertIn("interactive", html.lower())

    def test_do_options_cors(self):
        """Verifies CORS preflight OPTIONS request returns 204."""
        self.handler.do_OPTIONS()
        self.handler.send_response.assert_called_with(204)

    def test_do_options_cors_echoes_only_loopback_origin(self):
        """Verifies CORS never echoes a wildcard and validates the loopback Origin."""
        self.handler.headers = {"Origin": "http://127.0.0.1:8080"}
        self.handler.do_OPTIONS()
        self.handler.send_response.assert_called_with(204)
        sent = [call.args for call in self.handler.send_header.call_args_list]
        self.assertIn(("Access-Control-Allow-Origin", "http://127.0.0.1:8080"), sent)
        self.assertNotIn(("Access-Control-Allow-Origin", "*"), sent)

    def test_rejects_oversized_upload(self):
        """Verifies a Content-Length above the 1 GB ceiling returns HTTP 413 before reading."""
        from scriber.web.server import MAX_UPLOAD_SIZE

        class _ExplodingReader:
            def read(self, *args, **kwargs):
                raise AssertionError("Request body must not be read when over the upload limit")

        self.handler.path = "/api/process"
        self.handler.headers = {"Content-Length": str(MAX_UPLOAD_SIZE + 1)}
        self.handler.rfile = _ExplodingReader()
        self.handler.do_POST()
        self.handler.send_response.assert_called_with(413)

    def test_do_get_info(self):
        """Verifies GET /api/info returns top repos."""
        self.handler.path = "/api/info"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(written["name"], "Scriber")
        self.assertGreaterEqual(len(written["repos"]), 8)

    def test_do_get_benchmark(self):
        """Verifies GET /api/benchmark returns benchmark suite results."""
        self.handler.path = "/api/benchmark"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(written["all_passed_99_percent"])

    def test_do_get_voices(self):
        """Verifies GET /api/voices returns curated studio voices suite."""
        self.handler.path = "/api/voices"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("voices", written)
        self.assertGreaterEqual(len(written["voices"]), 20)
        first_voice = written["voices"][0]
        self.assertIn("id", first_voice)
        self.assertIn("name", first_voice)
        self.assertIn("locale", first_voice)
        self.assertIn("gender", first_voice)

    def test_do_get_performance(self):
        """Verifies GET /api/performance returns RAM, CPU, and GPU stats."""
        self.handler.path = "/api/performance"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("ram", written)
        self.assertIn("cpu", written)
        self.assertIn("gpu", written)
        self.assertIn("working_set_mb", written["ram"])
        self.assertIn("percent", written["cpu"])
        self.assertIn("name", written["gpu"])

    def test_do_get_progress(self):
        """Verifies GET /api/progress returns real-time progress state with speed factor and ETA."""
        self.handler.path = "/api/progress"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("percent", written)
        self.assertIn("stage", written)
        self.assertIn("phase", written)
        self.assertIn("speed_factor", written)
        self.assertIn("eta_sec", written)
        self.assertIn("elapsed_sec", written)

    def test_do_post_demo(self):
        """Verifies POST /api/process-demo executes demo meeting."""
        self.handler.path = "/api/process-demo"
        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("transcription", written)
        self.assertIn("council_analysis", written)
        self.assertIn("voice_profiles", written)

    def test_do_post_clone_voice(self):
        """Verifies POST /api/clone-voice synthesizes audio."""
        req_body = json.dumps({
            "text": "Action item status confirmed by council.",
            "pitch_shift": 5.0,
            "rate_shift": 0.0,
        }).encode("utf-8")

        self.handler.path = "/api/clone-voice"
        self.handler.headers = {"Content-Length": str(len(req_body))}
        self.handler.rfile = io.BytesIO(req_body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("audio_base64", written)
        self.assertIsNone(written["similarity_score"])

    def test_multipart_media_upload_parsing(self):
        """Verifies multipart/form-data upload parsing without cgi dependency."""
        sample_wav = AudioExtractor.create_synthetic_wav("Upload test", duration_sec=1.0)
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

        # Construct multipart payload
        parts = [
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="task"\r\n\r\ntranscribe\r\n',
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="file"; filename="test_audio.wav"\r\n',
            b'Content-Type: audio/wav\r\n\r\n',
            sample_wav,
            b"\r\n",
            f"--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)

        self.handler.path = "/api/process"
        self.handler.headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        self.handler.rfile = io.BytesIO(body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(written["video_source"], "test_audio.wav")
        self.assertIn("validation_report", written)

    def test_multipart_media_upload_automatic_english_translation(self):
        """Verifies default upload automatically translates non-English speech directly to English."""
        spanish_speech = "hola mundo la reunion comenzara ahora"
        sample_wav = AudioExtractor.create_synthetic_wav(spanish_speech, duration_sec=2.0)
        boundary = "----WebKitFormBoundaryXYZ9876543210"

        parts = [
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="reference_text"\r\n\r\n',
            spanish_speech.encode("utf-8"),
            b"\r\n",
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="file"; filename="meeting_spanish.mp4"\r\n',
            b'Content-Type: video/mp4\r\n\r\n',
            sample_wav,
            b"\r\n",
            f"--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/process"
        self.handler.headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        self.handler.rfile = io.BytesIO(body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        transcription_text = written["transcription"]["text"].lower()
        self.assertEqual(transcription_text, "no distinct speech detected in audio.")

    def test_multipart_media_upload_accented_spanish_speech(self):
        """Verifies Spanish speech with accents and question/exclamation marks translates cleanly into English."""
        accented_speech = "¡Hola mundo! La reunión comenzará ahora. ¿Cómo estás? Muchas gracias."
        sample_wav = AudioExtractor.create_synthetic_wav(accented_speech, duration_sec=2.0)
        boundary = "----WebKitFormBoundaryAccents12345"

        parts = [
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="reference_text"\r\n\r\n',
            accented_speech.encode("utf-8"),
            b"\r\n",
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="file"; filename="accented_spanish.mp4"\r\n',
            b'Content-Type: video/mp4\r\n\r\n',
            sample_wav,
            b"\r\n",
            f"--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/process"
        self.handler.headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        self.handler.rfile = io.BytesIO(body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        transcription_text = written["transcription"]["text"].lower()
        self.assertEqual(transcription_text, "no distinct speech detected in audio.")
        self.assertNotIn("hello world", transcription_text)

    def test_multipart_media_upload_mp4_binary_container(self):
        """Verifies binary MP4 upload succeeds gracefully and does not raise RuntimeError when FFmpeg is not installed."""
        mp4_binary = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08free" + b"\x00" * 2000
        boundary = "----WebKitFormBoundaryMP4Test99"

        parts = [
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="file"; filename="sample_meeting.mp4"\r\n',
            b'Content-Type: video/mp4\r\n\r\n',
            mp4_binary,
            b"\r\n",
            f"--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/process"
        self.handler.headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        self.handler.rfile = io.BytesIO(body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(written["video_source"], "sample_meeting.mp4")
        self.assertIn("transcription", written)
        self.assertGreater(len(written["transcription"]["segments"]), 0)

    def test_do_post_profile_voice(self):
        """Verifies POST /api/profile-voice accepts reference audio and returns extracted VoiceProfile."""
        sample_wav = AudioExtractor.create_synthetic_wav("Reference speaker audio", duration_sec=1.5)
        boundary = "----WebKitFormBoundaryVoiceRef"

        parts = [
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="speaker"\r\n\r\nCustomSpeaker\r\n',
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="file"; filename="ref_voice.wav"\r\n',
            b'Content-Type: audio/wav\r\n\r\n',
            sample_wav,
            b"\r\n",
            f"--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/profile-voice"
        self.handler.headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        self.handler.rfile = io.BytesIO(body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("profile", written)
        profile = written["profile"]
        self.assertEqual(profile["speaker_id"], "CustomSpeaker")
        self.assertGreater(profile["fundamental_frequency_hz"], 0)
        self.assertGreater(profile["spectral_centroid_hz"], 0)

    def test_transcription_clean_segments_without_artificial_speakers(self):
        """Verifies transcription generates clean segments without artificial speaker segmentation."""
        multi_speaker_text = (
            "Speaker one discusses roadmap. "
            "Speaker two details architecture. "
            "Speaker three verifies metrics. "
            "Speaker four ratifies delivery."
        )
        sample_wav = AudioExtractor.create_synthetic_wav(multi_speaker_text, duration_sec=4.0)
        boundary = "----WebKitFormBoundaryDiarization"

        parts = [
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="ground_truth_hint"\r\n\r\n',
            multi_speaker_text.encode("utf-8"),
            b"\r\n",
            f"--{boundary}\r\n".encode("latin-1"),
            b'Content-Disposition: form-data; name="file"; filename="multi_speaker.wav"\r\n',
            b'Content-Type: audio/wav\r\n\r\n',
            sample_wav,
            b"\r\n",
            f"--{boundary}--\r\n".encode("latin-1"),
        ]
        body = b"".join(parts)

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/process"
        self.handler.headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        }
        self.handler.rfile = io.BytesIO(body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        segments = written["transcription"]["segments"]
        self.assertGreater(len(segments), 0)
        for s in segments:
            self.assertIsNone(s.get("speaker"))

    def test_do_post_clone_voice_with_reference_audio(self):
        """Verifies POST /api/clone-voice accepts reference_audio base64 and transfers vocal timbre."""
        import base64
        ref_wav = AudioExtractor.create_synthetic_wav("Custom voice reference audio", duration_sec=1.5)
        ref_b64 = "data:audio/wav;base64," + base64.b64encode(ref_wav).decode("ascii")

        req_body = json.dumps({
            "text": "Testing voice cloning with direct reference audio payload.",
            "pitch_shift": 0.0,
            "rate_shift": 0.0,
            "output_format": "mp3",
            "reference_audio": ref_b64,
            "profile": {
                "speaker_id": "CustomVoiceRef",
                "fundamental_frequency_hz": 155.0,
                "gender_estimate": "masculine",
            },
        }).encode("utf-8")

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/clone-voice"
        self.handler.headers = {"Content-Length": str(len(req_body))}
        self.handler.rfile = io.BytesIO(req_body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("audio_base64", written)
        self.assertEqual(written["audio_format"], "mp3")
        self.assertGreater(len(written["audio_base64"]), 100)

    def test_do_post_edit_audio_json(self):
        """Verifies POST /api/edit-audio applies volume, pitch, and trimming to cached or base64 audio."""
        import base64
        sample_wav = AudioExtractor.create_synthetic_wav("Audio editor testing session", duration_sec=3.0)
        sample_b64 = "data:audio/wav;base64," + base64.b64encode(sample_wav).decode("ascii")

        req_body = json.dumps({
            "volume": 1.4,
            "pitch_semitones": 3.0,
            "start_sec": 0.5,
            "end_sec": 2.5,
            "filename": "test_edited.mp3",
            "audio_base64": sample_b64,
        }).encode("utf-8")

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/edit-audio"
        self.handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(req_body)),
        }
        self.handler.rfile = io.BytesIO(req_body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(written["success"])
        self.assertEqual(written["filename"], "test_edited.mp3")
        self.assertIn("audio_base64", written)
        self.assertAlmostEqual(written["duration"], 2.0, delta=0.2)

    def test_do_post_edit_audio_from_registered_file_path(self):
        """Mode 1 must edit the session's playable media path, not a shared last-audio buffer."""
        import os
        import tempfile
        import wave

        pcm = b"\x00\x00" * 16000  # 1 second 16kHz mono
        with tempfile.TemporaryDirectory() as td:
            wav_path = os.path.join(td, "session_media.wav")
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm)
            register_allowed_media_file(wav_path)

            req_body = json.dumps({
                "volume": 1.0,
                "pitch_semitones": 0.0,
                "start_sec": 0.0,
                "end_sec": None,
                "filename": "session_edited.mp3",
                "file_path": wav_path,
            }).encode("utf-8")

            self.handler.wfile = io.BytesIO()
            self.handler.path = "/api/edit-audio"
            self.handler.headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(req_body)),
            }
            self.handler.rfile = io.BytesIO(req_body)

            self.handler.do_POST()
            self.handler.send_response.assert_called_with(200)
            written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
            self.assertTrue(written["success"])
            self.assertIn("audio_base64", written)
            self.assertAlmostEqual(written["duration"], 1.0, delta=0.15)

    def test_do_get_models(self):
        """Verifies GET /api/models returns models for both transcription and cloning."""
        self.handler.path = "/api/models"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("transcribe_models", written)
        self.assertIn("voice_models", written)
        self.assertEqual(len(written["transcribe_models"]), 4)
        self.assertEqual(len(written["voice_models"]), 4)

        transcribe_ids = [m["id"] for m in written["transcribe_models"]]
        self.assertIn("turbo", transcribe_ids)
        self.assertIn("distil-large-v3", transcribe_ids)
        self.assertIn("base", transcribe_ids)
        self.assertIn("whisperx", transcribe_ids)

        voice_ids = [m["id"] for m in written["voice_models"]]
        self.assertIn("local-gpu", voice_ids)
        self.assertIn("edge-neural", voice_ids)
        self.assertIn("whisperspeech", voice_ids)
        self.assertIn("gpt-sovits", voice_ids)
        self.assertNotIn("voicemaker", voice_ids)
        self.assertNotIn("elevenlabs", voice_ids)

    def test_do_post_clone_voice_all_backends(self):
        """Verifies POST /api/clone-voice functions stably across all 3 top models."""
        for backend in ["edge-neural", "whisperspeech", "gpt-sovits"]:
            if hasattr(self.handler, "pipeline") and self.handler.pipeline is not None:
                self.handler.pipeline.reference_pcm = None
                self.handler.pipeline.last_pcm_data = None
            req_body = json.dumps({
                "text": f"Testing synthesis with {backend} model.",
                "pitch_shift": 2.0,
                "rate_shift": 0.0,
                "output_format": "mp3",
                "backend": backend,
                "profile": {
                    "speaker_id": "Speaker_Test",
                    "fundamental_frequency_hz": 150.0,
                    "gender_estimate": "masculine",
                },
            }).encode("utf-8")

            self.handler.wfile = io.BytesIO()
            self.handler.path = "/api/clone-voice"
            self.handler.headers = {"Content-Length": str(len(req_body))}
            self.handler.rfile = io.BytesIO(req_body)

            self.handler.do_POST()
            self.handler.send_response.assert_called_with(200)
            written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
            self.assertIn("audio_base64", written)
            self.assertIsNone(written["similarity_score"])

    def test_do_post_profile_voice_json_file_path(self):
        """Verifies POST /api/profile-voice accepts direct JSON file_path."""
        import tempfile, os
        sample_wav = AudioExtractor.create_synthetic_wav("Local file path profiling test", duration_sec=1.5)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(sample_wav)
            tmp_path = tmp.name

        try:
            req_body = json.dumps({
                "file_path": tmp_path,
                "speaker": "DirectPathSpeaker",
            }).encode("utf-8")

            self.handler.wfile = io.BytesIO()
            self.handler.path = "/api/profile-voice"
            self.handler.headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(req_body)),
            }
            self.handler.rfile = io.BytesIO(req_body)

            self.handler.do_POST()
            self.handler.send_response.assert_called_with(200)
            written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
            self.assertIn("profile", written)
            self.assertEqual(written["profile"]["speaker_id"], "DirectPathSpeaker")
            self.assertIn("audio_base64", written)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_do_post_clone_voice_file_path(self):
        """Verifies POST /api/clone-voice directly extracts timbre from file_path without base64 overhead."""
        import tempfile, os
        sample_wav = AudioExtractor.create_synthetic_wav("Local file path cloning test", duration_sec=1.5)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(sample_wav)
            tmp_path = tmp.name

        try:
            req_body = json.dumps({
                "text": "Direct path cloning synthesis test.",
                "file_path": tmp_path,
                "profile": {
                    "speaker_id": "PathSpeaker",
                    "fundamental_frequency_hz": 135.0,
                    "gender_estimate": "masculine",
                },
            }).encode("utf-8")

            self.handler.wfile = io.BytesIO()
            self.handler.path = "/api/clone-voice"
            self.handler.headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(req_body)),
            }
            self.handler.rfile = io.BytesIO(req_body)

            self.handler.do_POST()
            self.handler.send_response.assert_called_with(200)
            written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
            self.assertIn("audio_base64", written)
            self.assertGreater(written["similarity_score"], 0.60)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_do_post_clone_voice_with_voice_id_and_volume(self):
        """Verifies POST /api/clone-voice parses and forwards voice_id and volume."""
        req_body = json.dumps({
            "text": "Testing studio voice synthesis with voice_id and volume.",
            "voice_id": "en-US-JennyNeural",
            "volume": 1.25,
            "output_format": "mp3",
            "profile": {
                "speaker_id": "en-US-JennyNeural",
                "fundamental_frequency_hz": 180.0,
                "gender_estimate": "feminine",
            },
        }).encode("utf-8")

        self.handler.wfile = io.BytesIO()
        self.handler.path = "/api/clone-voice"
        self.handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(req_body)),
        }
        self.handler.rfile = io.BytesIO(req_body)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("audio_base64", written)
        self.assertEqual(written["audio_format"], "mp3")
        self.assertIsNone(written["similarity_score"])

    def test_do_get_media_full_content(self):
        """Verifies GET /api/media serves audio file with 200, Accept-Ranges, and CORS."""
        import tempfile, os, urllib.parse
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32)
            tmp_path = tmp.name
        try:
            register_allowed_media_file(tmp_path)
            self.handler.wfile = io.BytesIO()
            self.handler.headers = {"Host": "127.0.0.1"}
            self.handler.path = f"/api/media?path={urllib.parse.quote(tmp_path)}"
            self.handler.do_GET()
            self.handler.send_response.assert_called_with(200)
            headers_sent = dict(self.handler.send_header.call_args_list)
            self.assertEqual(self.handler.wfile.getvalue(), b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_do_get_media_range_seeking(self):
        """Verifies GET /api/media handles byte range seeking (206 Partial Content)."""
        import tempfile, os, urllib.parse
        payload = b"0123456789" * 100  # 1000 bytes
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            register_allowed_media_file(tmp_path)
            self.handler.wfile = io.BytesIO()
            self.handler.headers = {"Host": "127.0.0.1", "Range": "bytes=100-199"}
            self.handler.path = f"/api/media?path={urllib.parse.quote(tmp_path)}"
            self.handler.do_GET()
            self.handler.send_response.assert_called_with(206)
            self.assertEqual(len(self.handler.wfile.getvalue()), 100)
            self.assertEqual(self.handler.wfile.getvalue(), payload[100:200])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_do_get_media_suffix_range(self):
        """Verifies GET /api/media handles suffix range requests (e.g. bytes=-50)."""
        import tempfile, os, urllib.parse
        payload = b"ABCDEFGHIJ" * 20  # 200 bytes
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            register_allowed_media_file(tmp_path)
            self.handler.wfile = io.BytesIO()
            self.handler.headers = {"Host": "127.0.0.1", "Range": "bytes=-50"}
            self.handler.path = f"/api/media?path={urllib.parse.quote(tmp_path)}"
            self.handler.do_GET()
            self.handler.send_response.assert_called_with(206)
            self.assertEqual(len(self.handler.wfile.getvalue()), 50)
            self.assertEqual(self.handler.wfile.getvalue(), payload[-50:])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_do_head_media(self):
        """Verifies HEAD /api/media returns headers without streaming file body."""
        import tempfile, os, urllib.parse
        payload = b"RIFF" + b"\x00" * 96
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            register_allowed_media_file(tmp_path)
            self.handler.wfile = io.BytesIO()
            self.handler.headers = {"Host": "127.0.0.1"}
            self.handler.path = f"/api/media?path={urllib.parse.quote(tmp_path)}"
            self.handler.do_HEAD()
            self.handler.send_response.assert_called_with(200)
            self.assertEqual(self.handler.wfile.getvalue(), b"")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_prepare_playable_media_path_mkv_conversion(self):
        """Verifies non-standard MKV container is converted to 16kHz mono WAV speech track."""
        import tempfile, os
        dummy_pcm = b"\x00\x00" * 16000  # 1 second 16kHz 16-bit mono
        with tempfile.TemporaryDirectory() as out_dir:
            mkv_path = os.path.join(out_dir, "test_video.mkv")
            with open(mkv_path, "wb") as f:
                f.write(b"dummy_mkv_bytes")
            wav_path = _prepare_playable_media_path(
                mkv_path,
                session_id="sess_test123",
                pcm_data=dummy_pcm,
                output_dir=out_dir
            )
            self.assertTrue(wav_path.endswith("_speech.wav"))
            self.assertTrue(os.path.isfile(wav_path))
            self.assertTrue(is_allowed_media_file(wav_path))

    def test_prepare_playable_media_path_rewrites_stale_truncated_wav(self):
        """A stale/partial WAV from an earlier run must be replaced, never reused."""
        import tempfile, os, wave
        dummy_pcm = b"\x00\x00" * 16000
        with tempfile.TemporaryDirectory() as out_dir:
            mkv_path = os.path.join(out_dir, "episode.mkv")
            with open(mkv_path, "wb") as f:
                f.write(b"dummy")
            stale = os.path.join(out_dir, "sess_stale_episode_speech.wav")
            with wave.open(stale, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00\x00" * 16)  # 10 ms of accidental audio
            wav_path = _prepare_playable_media_path(
                mkv_path, session_id="sess_stale", pcm_data=dummy_pcm, output_dir=out_dir
            )
            self.assertEqual(os.path.getsize(wav_path), 44 + len(dummy_pcm))
            with wave.open(wav_path, "rb") as wf:
                self.assertEqual(wf.getnframes(), 16000)
            self.assertFalse(os.path.exists(wav_path + ".part"))

    def test_compute_waveform_peaks_reflects_audio_energy(self):
        """Waveform bars must follow real PCM energy, not an invented shape."""
        from scriber.web.server import _compute_waveform_peaks
        import struct
        quiet = struct.pack("<h", 200) * 16000       # 1 s very quiet
        loud = struct.pack("<h", 20000) * 16000      # 1 s loud
        peaks = _compute_waveform_peaks(quiet + loud, 64)
        self.assertEqual(len(peaks), 64)
        self.assertGreater(sum(peaks[32:]), sum(peaks[:32]) * 3)
        flat = _compute_waveform_peaks(b"\x00\x00" * 16000, 64)
        self.assertEqual(len(flat), 64)
        self.assertLessEqual(max(flat), 0.05)

    def test_prepare_playable_media_path_browser_containers_pass_through(self):
        """Browser-playable containers (.mp3, .wav, .mp4, .webm, .aac, .m4a, .ogg) pass through directly."""
        import tempfile, os
        from scriber.web.server import BROWSER_PLAYABLE_CONTAINERS
        with tempfile.TemporaryDirectory() as out_dir:
            for ext in BROWSER_PLAYABLE_CONTAINERS:
                sample_file = os.path.join(out_dir, f"sample{ext}")
                with open(sample_file, "wb") as f:
                    f.write(b"container_bytes_1234567890")
                result_path = _prepare_playable_media_path(
                    sample_file,
                    session_id="sess_playable",
                    pcm_data=b"\x00\x00" * 16000,
                    output_dir=out_dir,
                )
                self.assertEqual(result_path, sample_file, f"Format {ext} should pass through as original")
                self.assertTrue(is_allowed_media_file(result_path))

    def test_prepare_playable_media_path_non_browser_transcodes_speech_wav(self):
        """Non-browser containers (.mkv, .avi, .wmv) transcode to speech WAV track."""
        import tempfile, os
        with tempfile.TemporaryDirectory() as out_dir:
            for ext in [".mkv", ".avi", ".wmv"]:
                sample_file = os.path.join(out_dir, f"video{ext}")
                with open(sample_file, "wb") as f:
                    f.write(b"non_browser_video_bytes")
                dummy_pcm = b"\x00\x00" * 32000  # 2s 16kHz mono
                result_path = _prepare_playable_media_path(
                    sample_file,
                    session_id="sess_transcode",
                    pcm_data=dummy_pcm,
                    output_dir=out_dir,
                )
                self.assertTrue(result_path.endswith("_speech.wav"), f"Format {ext} should transcode to speech WAV")
                self.assertEqual(os.path.getsize(result_path), 44 + len(dummy_pcm))
                self.assertTrue(is_allowed_media_file(result_path))

    def test_attach_playback_payload_serves_pristine_mp4_url(self):
        """_attach_playback_payload on MP4 serves original container directly with media_url."""
        import tempfile, os
        from scriber.web.server import _attach_playback_payload
        with tempfile.TemporaryDirectory() as out_dir:
            mp4_path = os.path.join(out_dir, "meeting.mp4")
            with open(mp4_path, "wb") as f:
                f.write(b"mp4_video_payload")
            resp = {}
            dummy_pcm = b"\x00\x00" * 16000
            class MockOutput:
                session_id = "sess_mp4"
                audio_pcm16 = dummy_pcm
            _attach_playback_payload(resp, MockOutput(), mp4_path, output_dir=out_dir)
            self.assertIn("media_url", resp)
            self.assertIn("meeting.mp4", resp["media_url"])
            self.assertNotIn("_speech.wav", resp["media_url"])
            self.assertIn("waveform_peaks", resp)
            self.assertEqual(len(resp["waveform_peaks"]), 64)

    def test_do_get_media_mp4_range_streaming(self):
        """Verifies GET /api/media handles byte range seeking for MP4 container with video/mp4 MIME."""
        import tempfile, os, urllib.parse
        payload = b"\x00\x00\x00\x20ftypmp42" + b"A" * 500
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            register_allowed_media_file(tmp_path)
            self.handler.wfile = io.BytesIO()
            self.handler.headers = {"Host": "127.0.0.1", "Range": "bytes=0-99"}
            self.handler.path = f"/api/media?path={urllib.parse.quote(tmp_path)}"
            self.handler.do_GET()
            self.handler.send_response.assert_called_with(206)
            self.assertEqual(len(self.handler.wfile.getvalue()), 100)
            self.assertEqual(self.handler.wfile.getvalue(), payload[:100])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_do_get_media_unsatisfiable_range_returns_416(self):
        """RFC 7233: Range beyond file size must return 416 Range Not Satisfiable."""
        import tempfile, os, urllib.parse
        payload = b"short_audio_payload"
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            register_allowed_media_file(tmp_path)
            self.handler.wfile = io.BytesIO()
            self.handler.headers = {"Host": "127.0.0.1", "Range": "bytes=500-600"}
            self.handler.path = f"/api/media?path={urllib.parse.quote(tmp_path)}"
            self.handler.do_GET()
            self.handler.send_response.assert_called_with(416)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
