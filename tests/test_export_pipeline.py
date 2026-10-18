"""E2E Verification for Clean Transcript Export in Scriber Server."""

import json
import urllib.request
import unittest


class TestExportPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scriber.web.server import ScriberBackgroundServer
        cls.server = ScriberBackgroundServer(host="127.0.0.1", port=0)
        cls.server.start()
        cls.BASE_URL = cls.server.url

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server") and cls.server:
            cls.server.stop()

    def test_ui_contains_clean_export_logic(self):
        req = urllib.request.Request(self.BASE_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")

        # Verify inline word token
        self.assertIn(".word-token {\n    display: inline;", html)

        # Verify new format options
        self.assertIn("Clean Text (No Headers)", html)
        self.assertIn(".MD", html)
        self.assertIn(".TXT", html)
        self.assertIn(".SRT", html)
        self.assertIn(".VTT", html)

        # Verify export cleaning functions exist in client script
        self.assertIn("function cleanExportText", html)
        self.assertIn("function getCleanSegmentText", html)
        self.assertIn("function formatSrtExport", html)
        self.assertIn("function formatVttExport", html)

    def test_demo_endpoint_returns_clean_exports(self):
        req = urllib.request.Request(f"{self.BASE_URL}/api/process-demo", method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, data=b"{}", timeout=15) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))

        self.assertIn("exports", data)
        exports = data["exports"]
        self.assertIn("txt", exports)
        self.assertIn("markdown", exports)
        self.assertIn("srt", exports)
        self.assertIn("vtt", exports)

        txt_content = exports["txt"]
        self.assertIn("SCRIBER TRANSCRIPT", txt_content)
        # Ensure spaces between words exist
        self.assertIn("Welcome to the Scriber", txt_content)
        self.assertNotIn("WelcometotheScriber", txt_content)


if __name__ == "__main__":
    unittest.main()
