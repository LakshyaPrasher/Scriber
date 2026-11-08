"""Empirical Adversarial Stress Test Suite for Scriber Cancellation System (Milestone M12).

Adversarially tests:
1. Rapid successive cancellations under high-concurrency multi-threading.
2. Repeated cancellations while idle (idempotence).
3. Mid-flight abortion during audio/pipeline simulation with guaranteed temp file eradication.
4. Clean recovery and resumption of subsequent processing jobs after cancellation.
5. Live HTTP hammering of /api/cancel on an active ScriberBackgroundServer instance.
6. Edge case handling (None, empty, duplicate, deleted-before-purge paths).
"""

import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
import urllib.request
from unittest.mock import MagicMock

from scriber.exceptions import JobCancelledException
from scriber.pipeline import ScriberPipeline
from scriber.web.server import (
    CancellationManager,
    ScriberBackgroundServer,
    ScriberHTTPRequestHandler,
    _CANCEL_MGR,
    _ACTIVE_PROGRESS,
    _PROGRESS_LOCK,
    reset_progress_state,
)


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestAdversarialCancellation(unittest.TestCase):

    def setUp(self):
        _CANCEL_MGR.reset()
        reset_progress_state()

    def tearDown(self):
        _CANCEL_MGR.reset()
        reset_progress_state()

    def test_rapid_successive_cancellations_concurrency(self):
        """Stress test: 10 threads hammering request_cancel and register_temp_file simultaneously."""
        mgr = CancellationManager()
        all_created_files = []
        lock = threading.Lock()
        errors = []

        def worker_register(thread_idx):
            try:
                for i in range(25):
                    fd, path = tempfile.mkstemp(prefix=f"adv_temp_{thread_idx}_{i}_", suffix=".tmp")
                    os.close(fd)
                    with lock:
                        all_created_files.append(path)
                    mgr.register_temp_file(path)
                    time.sleep(0.001)
            except Exception as e:
                with lock:
                    errors.append(e)

        def worker_cancel():
            try:
                for _ in range(30):
                    mgr.request_cancel()
                    time.sleep(0.001)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=worker_register, args=(i,)))
        for _ in range(5):
            threads.append(threading.Thread(target=worker_cancel))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors during high concurrency: {errors}")
        self.assertTrue(mgr.is_cancelled())

        # Purge any remaining files registered after final cancel
        mgr.purge_temp_files()

        # Verify all created files were eradicated from disk
        surviving = [p for p in all_created_files if os.path.exists(p)]
        self.assertEqual(len(surviving), 0, f"Leaked files detected on disk: {surviving}")

    def test_cancellation_when_idle_repeated(self):
        """Stress test: Repeated cancellations when system is idle must be idempotent and safe."""
        mgr = CancellationManager()
        for i in range(100):
            mgr.request_cancel()
            self.assertTrue(mgr.is_cancelled())
        
        # Reset and repeat
        mgr.reset()
        self.assertFalse(mgr.is_cancelled())
        for i in range(50):
            mgr.request_cancel()
            self.assertTrue(mgr.is_cancelled())

    def test_midflight_pipeline_abort_and_cleanup(self):
        """Stress test: Mid-flight pipeline job abortion guarantees temp file deletion and clean state."""
        fd1, raw_audio = tempfile.mkstemp(prefix="raw_input_", suffix=".wav")
        os.close(fd1)
        fd2, intermediate_slice = tempfile.mkstemp(prefix="slice_", suffix=".wav")
        os.close(fd2)
        fd3, partial_model_output = tempfile.mkstemp(prefix="model_out_", suffix=".bin")
        os.close(fd3)

        tracked_files = [raw_audio, intermediate_slice, partial_model_output]
        for f in tracked_files:
            self.assertTrue(os.path.exists(f))
            _CANCEL_MGR.register_temp_file(f)

        cancelled_caught = False
        try:
            # Simulate a multi-step worker that checks cancel between steps
            for step in range(10):
                if step == 3:
                    _CANCEL_MGR.request_cancel()
                if _CANCEL_MGR.is_cancelled():
                    raise JobCancelledException(f"Aborted at step {step}")
                time.sleep(0.01)
        except JobCancelledException:
            cancelled_caught = True
            _CANCEL_MGR.purge_temp_files()

        self.assertTrue(cancelled_caught, "JobCancelledException was not raised")
        for f in tracked_files:
            self.assertFalse(os.path.exists(f), f"File {f} leaked after mid-flight cancellation")

    def test_post_cancellation_recovery(self):
        """Verify that after cancellation, a new job can reset the manager and execute to completion."""
        # Job 1 gets cancelled
        _CANCEL_MGR.request_cancel()
        self.assertTrue(_CANCEL_MGR.is_cancelled())

        # Reset before starting Job 2
        _CANCEL_MGR.reset()
        self.assertFalse(_CANCEL_MGR.is_cancelled())

        fd, job2_file = tempfile.mkstemp(prefix="job2_", suffix=".wav")
        os.close(fd)
        _CANCEL_MGR.register_temp_file(job2_file)

        # Job 2 runs without cancellation
        job2_completed = False
        for step in range(5):
            if _CANCEL_MGR.is_cancelled():
                raise JobCancelledException("Unexpected cancellation in Job 2")
            time.sleep(0.005)
        job2_completed = True

        self.assertTrue(job2_completed)
        self.assertFalse(_CANCEL_MGR.is_cancelled())
        # Unregister and keep job2 result
        _CANCEL_MGR.unregister_temp_file(job2_file)
        _CANCEL_MGR.purge_temp_files()
        self.assertTrue(os.path.exists(job2_file))
        os.remove(job2_file)

    def test_file_registration_edge_cases(self):
        """Verify edge cases: None, empty string, non-existent paths, pre-deleted paths."""
        mgr = CancellationManager()
        # Should not crash on falsy values
        mgr.register_temp_file("")
        mgr.register_temp_file(None)
        mgr.unregister_temp_file("")
        mgr.unregister_temp_file(None)

        # Non-existent file
        fake_path = os.path.abspath("non_existent_file_12345.tmp")
        mgr.register_temp_file(fake_path)

        # File created then deleted before purge
        fd, early_deleted = tempfile.mkstemp(suffix=".tmp")
        os.close(fd)
        mgr.register_temp_file(early_deleted)
        os.remove(early_deleted)

        # Real file that should be purged
        fd2, real_file = tempfile.mkstemp(suffix=".tmp")
        os.close(fd2)
        mgr.register_temp_file(real_file)

        # Purge must succeed without raising FileNotFoundError
        mgr.purge_temp_files()
        self.assertFalse(os.path.exists(real_file))

    def test_live_server_http_cancellation_hammering(self):
        """Live HTTP Stress Test: Spin up real ScriberBackgroundServer and hammer /api/cancel with 50 requests."""
        port = get_free_port()
        server = ScriberBackgroundServer(host="127.0.0.1", port=port)
        server.start()

        try:
            base_url = f"http://127.0.0.1:{port}"
            # Verify server is responding
            req = urllib.request.Request(f"{base_url}/api/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)

            # Hammer /api/cancel from 5 concurrent worker threads (10 requests each)
            cancel_errors = []
            status_codes = []
            lock = threading.Lock()

            def hammer_worker():
                for _ in range(10):
                    try:
                        c_req = urllib.request.Request(f"{base_url}/api/cancel", data=b"", method="POST")
                        with urllib.request.urlopen(c_req, timeout=5) as c_resp:
                            with lock:
                                status_codes.append(c_resp.status)
                    except Exception as ex:
                        with lock:
                            cancel_errors.append(ex)

            threads = [threading.Thread(target=hammer_worker) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(len(cancel_errors), 0, f"HTTP cancellation errors: {cancel_errors}")
            self.assertEqual(len(status_codes), 50)
            self.assertTrue(all(code == 200 for code in status_codes))

            # Verify global progress state reports cancelled
            with _PROGRESS_LOCK:
                progress = dict(_ACTIVE_PROGRESS)
            self.assertFalse(progress.get("active"))
            self.assertEqual(progress.get("stage"), "cancelled")

            # Verify server remains responsive after the barrage
            req_after = urllib.request.Request(f"{base_url}/api/health")
            with urllib.request.urlopen(req_after, timeout=5) as resp_after:
                self.assertEqual(resp_after.status, 200)
                data = json.loads(resp_after.read().decode("utf-8"))
                self.assertEqual(data.get("status"), "ok")

        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
