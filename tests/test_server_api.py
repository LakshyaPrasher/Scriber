"""Tests for Scriber Web Server, REST API, and Multipart upload parser."""

import io
import json
import unittest
from unittest.mock import MagicMock

from scriber.audio_extractor import AudioExtractor
from scriber.web.server import (
    ScriberHTTPRequestHandler,
    get_embedded_html,
    ScriberServer,
    ScriberBackgroundServer,
)


class TestServerAPI(unittest.TestCase):

    def setUp(self):
        self.handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        self.handler.wfile = io.BytesIO()
        self.handler.rfile = io.BytesIO()
        self.handler.headers = {}
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def test_embedded_ui_contains_key_components(self):
        """Verifies embedded HTML contains modern UI elements, file dropzone, and voice cloning."""
        html = get_embedded_html()
        self.assertIn("Scriber", html)
        self.assertIn("Voice Cloning Studio", html)
        self.assertIn("dropzone", html)
        self.assertIn("audio-player", html)
        self.assertIn("interactive", html.lower())

    def test_do_options_cors(self):
        """Verifies CORS preflight OPTIONS request returns 200."""
        self.handler.do_OPTIONS()
        self.handler.send_response.assert_called_with(200)

    def test_do_get_info(self):
        """Verifies GET /api/info returns top 10 repos."""
        self.handler.path = "/api/info"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(written["name"], "Scriber")
        self.assertGreaterEqual(len(written["repos"]), 10)

    def test_do_get_benchmark(self):
        """Verifies GET /api/benchmark returns benchmark suite results."""
        self.handler.path = "/api/benchmark"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        written = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(written["all_passed_99_percent"])

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
        self.assertGreaterEqual(written["similarity_score"], 0.990)

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
        self.assertIn("hello world", transcription_text, "Spanish 'hola mundo' should be translated to 'hello world'")
        self.assertIn("meeting will start now", transcription_text)

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
        self.assertIn("hello world", transcription_text)
        self.assertIn("the meeting will start now", transcription_text)
        self.assertIn("how are you", transcription_text)
        self.assertIn("thank you very much", transcription_text)
        self.assertNotIn("[translated from", transcription_text)

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

    def test_four_speaker_intelligent_diarization(self):
        """Verifies speaker diarization cycles intelligently across Speaker 1, 2, 3, 4."""
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
            b'Content-Disposition: form-data; name="reference_text"\r\n\r\n',
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
        speakers = [s["speaker"].replace(" ", "_") for s in written["transcription"]["segments"]]
        self.assertIn("Speaker_1", speakers)
        self.assertIn("Speaker_2", speakers)
        self.assertIn("Speaker_3", speakers)
        self.assertIn("Speaker_4", speakers)

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
            self.assertGreater(written["similarity_score"], 0.85)


if __name__ == "__main__":
    unittest.main()
