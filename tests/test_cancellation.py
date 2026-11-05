"""Tests for Job Cancellation, Temp File Tracking, and Responsiveness in Scriber M12."""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from scriber.exceptions import JobCancelledException
from scriber.diarizer import AcousticDiarizer
from scriber.pipeline import ScriberPipeline
from scriber.transcription_engine import TranscriptionEngine
from scriber.voice_clone import VoiceCloner
from scriber.web.server import (
    CancellationManager,
    ScriberHTTPRequestHandler,
    _CANCEL_MGR,
)


class TestCancellationMechanism(unittest.TestCase):

    def setUp(self):
        _CANCEL_MGR.reset()

    def tearDown(self):
        _CANCEL_MGR.reset()

    def test_cancellation_manager_lifecycle(self):
        """Verifies cancellation flag lifecycle: set, check, and reset."""
        mgr = CancellationManager()
        self.assertFalse(mgr.is_cancelled())
        mgr.request_cancel()
        self.assertTrue(mgr.is_cancelled())
        mgr.reset()
        self.assertFalse(mgr.is_cancelled())

    def test_temp_file_registration_and_purge(self):
        """Verifies temporary files registered during processing are cleanly purged on cancellation."""
        mgr = CancellationManager()
        fd1, path1 = tempfile.mkstemp(suffix=".mp3")
        os.close(fd1)
        fd2, path2 = tempfile.mkstemp(suffix=".wav")
        os.close(fd2)

        self.assertTrue(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))

        mgr.register_temp_file(path1)
        mgr.register_temp_file(path2)

        mgr.request_cancel()

        self.assertFalse(os.path.exists(path1), "Temp file 1 should have been purged")
        self.assertFalse(os.path.exists(path2), "Temp file 2 should have been purged")

    def test_temp_file_unregistration(self):
        """Verifies unregister_temp_file prevents purge of kept files."""
        mgr = CancellationManager()
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            mgr.register_temp_file(path)
            mgr.unregister_temp_file(path)
            mgr.purge_temp_files()
            self.assertTrue(os.path.exists(path), "Unregistered file should not be purged")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_transcription_engine_cancellation(self):
        """Verifies TranscriptionEngine halts and raises JobCancelledException when cancel_checker fires."""
        engine = TranscriptionEngine()
        cancel_called = False

        def cancel_check():
            nonlocal cancel_called
            cancel_called = True
            return True

        with self.assertRaises(JobCancelledException):
            engine.transcribe(
                pcm16_data=b"\x00" * 32000,
                duration=1.0,
                cancel_checker=cancel_check,
            )

        self.assertTrue(cancel_called)

    def test_diarizer_cancellation(self):
        """Verifies AcousticDiarizer checks cancel_checker and raises JobCancelledException."""
        diarizer = AcousticDiarizer()
        with self.assertRaises(JobCancelledException):
            diarizer.diarize_segments(
                segments=[],
                pcm16_data=b"",
                sample_rate=16000,
                cancel_checker=lambda: True,
            )

    def test_voice_cloner_cancellation(self):
        """Verifies VoiceCloner checks cancel_checker and raises JobCancelledException."""
        cloner = VoiceCloner()
        with self.assertRaises(JobCancelledException):
            cloner.clone_voice(
                text="Test cancellation",
                cancel_checker=lambda: True,
            )

    def test_pipeline_cancellation(self):
        """Verifies ScriberPipeline immediately raises JobCancelledException when cancel_checker is True."""
        pipeline = ScriberPipeline()
        with self.assertRaises(JobCancelledException):
            pipeline.process_file(
                "dummy_file.mp3",
                cancel_checker=lambda: True,
            )

    def test_api_cancel_post_endpoint(self):
        """Verifies POST /api/cancel endpoint sets cancellation event and returns status cancelled."""
        handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        handler.wfile = io.BytesIO()
        handler.rfile = io.BytesIO()
        handler.headers = {}
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.path = "/api/cancel"

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(output.get("status"), "cancelled")
        self.assertTrue(output.get("cancelled"))
        self.assertTrue(_CANCEL_MGR.is_cancelled())

    def test_api_edit_audio_cancellation(self):
        """Verifies /api/edit-audio handles cancellation cleanly with status cancelled."""
        handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        handler.wfile = io.BytesIO()
        body = json.dumps({"volume": 1.5, "filename": "test.mp3"}).encode("utf-8")
        handler.rfile = io.BytesIO(body)
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.path = "/api/edit-audio"

        _CANCEL_MGR.request_cancel()
        handler.do_POST()

        handler.send_response.assert_called_with(200)
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(output.get("status"), "cancelled")
        self.assertTrue(output.get("cancelled"))

    def test_api_clone_voice_cancellation(self):
        """Verifies /api/clone-voice catches JobCancelledException, purges temp files, and returns status cancelled."""
        handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        handler.wfile = io.BytesIO()
        body = json.dumps({"text": "Hello world", "speaker": "Speaker 1"}).encode("utf-8")
        handler.rfile = io.BytesIO(body)
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.path = "/api/clone-voice"
        handler.pipeline = MagicMock()
        handler.pipeline.clone_voice.side_effect = JobCancelledException("Voice synthesis cancelled")

        fd, temp_audio = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        _CANCEL_MGR.register_temp_file(temp_audio)
        self.assertTrue(os.path.exists(temp_audio))

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(output.get("status"), "cancelled")
        self.assertTrue(output.get("cancelled"))
        self.assertFalse(os.path.exists(temp_audio), "Temp file must be purged upon cancellation")

    def test_api_process_cancellation(self):
        """Verifies /api/process handles JobCancelledException and purges temporary files."""
        handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        handler.wfile = io.BytesIO()
        body = json.dumps({"file_path": "tests/test_cancellation.py"}).encode("utf-8")
        handler.rfile = io.BytesIO(body)
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.path = "/api/process"
        handler.pipeline = MagicMock()
        handler.pipeline.process_file.side_effect = JobCancelledException("Job cancelled by user")

        fd, temp_file = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        _CANCEL_MGR.register_temp_file(temp_file)
        self.assertTrue(os.path.exists(temp_file))

        handler.do_POST()

        handler.send_response.assert_called_with(200)
        output = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(output.get("status"), "cancelled")
        self.assertTrue(output.get("cancelled"))
        self.assertFalse(os.path.exists(temp_file), "Temp file must be purged on cancel")

    def test_cancellation_manager_concurrency(self):
        """Verifies thread-safe registration and purging across concurrent threads."""
        import threading
        mgr = CancellationManager()
        created_files = []
        lock = threading.Lock()

        def worker():
            for _ in range(5):
                fd, path = tempfile.mkstemp(suffix=".tmp")
                os.close(fd)
                with lock:
                    created_files.append(path)
                mgr.register_temp_file(path)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(created_files), 20)
        for f in created_files:
            self.assertTrue(os.path.exists(f))

        mgr.request_cancel()
        for f in created_files:
            self.assertFalse(os.path.exists(f), f"Temp file {f} was not purged")


if __name__ == "__main__":
    unittest.main()

