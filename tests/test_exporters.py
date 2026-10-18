"""Tests for ScriberExporter (JSON, Markdown, HTML, SRT, VTT)."""

import json
import unittest

from scriber.exporters import ScriberExporter
from scriber.models import (
    ActionItem,
    AudioMetadata,
    AudioSegment,
    CouncilAnalysis,
    ScriberOutput,
    DiscussionPoint,
    ExecutiveSummary,
    QualityReport,
    TranscriptionResult,
    ValidationReport,
)


class TestScriberExporter(unittest.TestCase):

    def setUp(self):
        seg = AudioSegment(id=0, seek=0, start=1.5, end=4.2, text="Deploying Scriber Studio locally.")
        trans = TranscriptionResult(
            text="Deploying Scriber Studio locally.",
            language="en",
            language_probability=0.99,
            duration=5.0,
            segments=[seg],
        )
        action = ActionItem(id="ACT-001", task="Deploy Scriber", assignee="Alex", priority="high")
        disc = DiscussionPoint(
            id="DISC-001", title="Studio Deployment", summary="Discussion on Scriber.", start_time=1.0, end_time=4.0
        )
        summary = ExecutiveSummary(
            headline="Studio Deployment Session",
            tldr="Summary of deployment meeting.",
            key_takeaways=["Local privacy and zero latency."],
            decisions_reached=["Use EdgeChromium WebView2."],
            unresolved_questions=[],
        )
        council = CouncilAnalysis(
            executive_summary=summary,
            action_items=[action],
            discussion_points=[disc],
            topics=["Studio"],
        )
        qual = QualityReport(
            overall_score=0.99,
            confidence_avg=0.99,
            repetition_looping_detected=False,
            hallucinations_culled=0,
            low_confidence_segments_flagged=0,
            compression_ratio_healthy=True,
            word_count=5,
            estimated_speaking_wpm=60.0,
        )
        val = ValidationReport(
            accuracy_score=1.0,
            wer=0.0,
            cer=0.0,
            precision=1.0,
            recall=1.0,
            f1_score=1.0,
            passed_99_percent=True,
            certificate_id="CERT-TEST-1234",
        )
        meta = AudioMetadata(
            filename="meeting.mp4",
            duration=5.0,
            sample_rate=16000,
            channels=1,
            file_size_bytes=100000,
            file_format="mp4",
        )

        self.output = ScriberOutput(
            session_id="sess_123",
            video_source="meeting.mp4",
            audio_metadata=meta,
            transcription=trans,
            translation=None,
            council_analysis=council,
            quality_report=qual,
            validation_report=val,
            processing_time_seconds=0.45,
            repos_leveraged=["openai/whisper", "faster-whisper"],
        )

    def test_json_export(self):
        json_str = ScriberExporter.to_json(self.output)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["session_id"], "sess_123")
        self.assertEqual(parsed["validation_report"]["certificate_id"], "CERT-TEST-1234")

    def test_markdown_export(self):
        md = ScriberExporter.to_markdown(self.output)
        self.assertIn("# 🎬 Scriber Intelligence Report", md)
        self.assertIn("Studio Deployment Session", md)
        self.assertIn("ACT-001", md)
        self.assertIn("CERT-TEST-1234", md)

    def test_srt_export(self):
        srt = ScriberExporter.to_srt(self.output)
        self.assertIn("00:00:01,500 --> 00:00:04,200", srt)
        self.assertIn("Deploying Scriber Studio locally.", srt)

    def test_vtt_export(self):
        vtt = ScriberExporter.to_vtt(self.output)
        self.assertTrue(vtt.startswith("WEBVTT"))
        self.assertIn("00:00:01.500 --> 00:00:04.200", vtt)

    def test_txt_export(self):
        txt = ScriberExporter.to_txt(self.output)
        self.assertIn("SCRIBER TRANSCRIPT", txt)
        self.assertIn("meeting.mp4", txt)
        self.assertIn("[00:01 - 00:04] Speaker:", txt)
        self.assertIn("Deploying Scriber Studio locally.", txt)

    def test_html_export(self):
        html = ScriberExporter.to_html(self.output)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Deploy Scriber", html)
        self.assertIn("Scriber", html)



if __name__ == "__main__":
    unittest.main()
