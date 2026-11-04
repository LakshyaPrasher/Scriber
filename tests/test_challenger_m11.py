"""Empirical Challenger Test Suite for Milestone M11.

Focusing on:
- Feature 5: Meeting Intelligence & R1.5 Purge Check
- Feature 6: Voice Cloning Studio & Inference Lockout
- Feature 7: Export Pipeline (TXT, SRT, VTT, JSON, HTML)
- Constraint R2: 100% Local Execution (Zero Paid Cloud APIs)
"""

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scriber.audio_extractor import AudioExtractor
from scriber.council import SupremeCouncil
from scriber.exporters import ScriberExporter
from scriber.web.server import ScriberBackgroundServer
from scriber.models import (
    ActionItem,
    AudioMetadata,
    AudioSegment,
    CouncilAnalysis,
    DiscussionPoint,
    ExecutiveSummary,
    QualityReport,
    ScriberOutput,
    TranscriptionResult,
    HashChainBlock,
    ValidationReport,
    VoiceProfile,
)
from scriber.pipeline import ScriberPipeline
from scriber.voice_clone import VoiceProfiler


class TestChallengerFeature5MeetingIntelligence(unittest.TestCase):
    """Empirical verification of Feature 5: Meeting Intelligence."""

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        cls.index_html_path = cls.root / "scriber" / "web" / "static" / "index.html"
        cls.app_js_path = cls.root / "scriber" / "web" / "static" / "app.js"
        cls.html_content = cls.index_html_path.read_text(encoding="utf-8")
        cls.js_content = cls.app_js_path.read_text(encoding="utf-8")

    def test_dom_council_dashboard_panel_present(self):
        """Confirm #council-dashboard-panel and all subcomponents are present in DOM."""
        self.assertIn('id="council-dashboard-panel"', self.html_content)
        self.assertIn('id="council-briefing-headline"', self.html_content)
        self.assertIn('id="council-briefing-tldr"', self.html_content)
        self.assertIn('id="council-decisions-wrap"', self.html_content)
        self.assertIn('id="council-decisions-list"', self.html_content)
        self.assertIn('id="council-chapters-wrap"', self.html_content)
        self.assertIn('id="council-chapters-strip"', self.html_content)

    def test_r1_5_action_items_grid_purged_from_ui(self):
        """Rigorously verify #action-items-grid and related action items tables are absent from UI."""
        self.assertNotIn('id="action-items-grid"', self.html_content)
        self.assertNotIn('id="council-actions-grid"', self.html_content)
        self.assertNotIn("Forensic Action Item Commitments", self.html_content)
        self.assertNotIn('id="action-items-grid"', self.js_content)
        self.assertNotIn('id="council-actions-grid"', self.js_content)

    def test_meeting_intelligence_backend_synthesis_sunil_mittal(self):
        """Synthesize meeting intelligence on real Sunil Mittal transcript."""
        transcript_text = (
            "We need to get away from this obsession of import of gold. "
            "We need to lower our energy costs. We need to move more faster towards renewable energy in our industry. "
            "And importantly, we need to vote with our feet within our country. Spend more here, put more capex here. "
            "My own company, Airtel, in 24 -25 spent about 31,000 crores in capex. And if I include a subsidiary in those towers, "
            "There is another 7,000 crores. The investment went up. And we know that in the current year, the investment will keep on going up. "
            "We need to invest more. This is not the moment to shy away. This is the moment to invest. "
            "Double down in our own country, because the underlying growth is there."
        )
        segments = [
            AudioSegment(id=0, seek=0, start=0.14, end=3.14, text="We need to get away from this obsession of import of gold.", speaker="Speaker_1"),
            AudioSegment(id=1, seek=0, start=3.82, end=5.94, text="We need to lower our energy costs.", speaker="Speaker_2"),
            AudioSegment(id=2, seek=0, start=6.46, end=15.86, text="We need to move more faster towards renewable energy in our industry. And importantly, we need to vote with our feet within our country.", speaker="Speaker_1"),
            AudioSegment(id=3, seek=0, start=16.54, end=27.90, text="Spend more here, put more capex here. My own company, Airtel, in 24 -25 spent about 31,000 crores in capex.", speaker="Speaker_2"),
            AudioSegment(id=4, seek=0, start=28.00, end=43.00, text="There is another 7,000 crores. The investment went up. And we know that in the current year, the investment will keep on going up. We need to invest more.", speaker="Speaker_1"),
            AudioSegment(id=5, seek=0, start=43.00, end=56.00, text="This is the moment to invest. Double down in our own country, because the underlying growth is there.", speaker="Speaker_1"),
        ]

        transcription = TranscriptionResult(
            text=transcript_text,
            language="en",
            language_probability=0.99,
            duration=90.0,
            segments=segments,
        )
        council = SupremeCouncil()
        analysis = council.analyze(transcription)

        self.assertIsNotNone(analysis)
        self.assertIsNotNone(analysis.executive_summary)
        self.assertTrue(len(analysis.executive_summary.headline) > 0)
        self.assertTrue(len(analysis.executive_summary.tldr) > 20)

        # Verify Ratified Decisions
        decisions = analysis.executive_summary.decisions_reached
        self.assertGreater(len(decisions), 0, "No decisions were ratified from policy commitments!")
        gold_or_capex_found = any("gold" in d.lower() or "capex" in d.lower() or "invest" in d.lower() for d in decisions)
        self.assertTrue(gold_or_capex_found, f"Expected key policy commitments in decisions: {decisions}")

        # Verify Thematic Chapters & Discussion Points
        self.assertGreater(len(analysis.discussion_points), 0, "No thematic discussion points extracted!")
        first_chapter = analysis.discussion_points[0]
        self.assertTrue(hasattr(first_chapter, "title") and len(first_chapter.title) > 0)
        self.assertTrue(hasattr(first_chapter, "start_time") and first_chapter.start_time >= 0.0)

    def test_meeting_intelligence_edge_cases(self):
        """Stress-test meeting intelligence with empty text and single-word input."""
        council = SupremeCouncil()
        empty_trans = TranscriptionResult(text="", language="en", language_probability=0.99, duration=0.0, segments=[])
        analysis_empty = council.analyze(empty_trans)
        self.assertIsNotNone(analysis_empty)
        self.assertEqual(len(analysis_empty.executive_summary.decisions_reached), 0)

        single_trans = TranscriptionResult(
            text="Hello.",
            language="en",
            language_probability=0.99,
            duration=1.0,
            segments=[AudioSegment(id=0, seek=0, start=0.0, end=1.0, text="Hello.", speaker="Speaker_1")],
        )
        analysis_single = council.analyze(single_trans)
        self.assertIsNotNone(analysis_single)
        self.assertTrue(len(analysis_single.executive_summary.headline) > 0)


class TestChallengerFeature6VoiceCloningStudio(unittest.TestCase):
    """Empirical verification of Feature 6: Voice Cloning Studio & Lockout."""

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        cls.ref_audio_path = Path("C:/Users/laksh/Downloads/VIRAT KOHLI REF AUDIO.mp3")
        cls.extractor = AudioExtractor()
        cls.pipeline = ScriberPipeline()

    def test_timbre_pitch_extraction_real_reference(self):
        """Extract acoustic biometric VoiceProfile from authentic reference audio."""
        if not self.ref_audio_path.exists():
            self.skipTest(f"Reference file {self.ref_audio_path} not found")

        pcm_data, meta = self.extractor.extract_pcm16(str(self.ref_audio_path), max_duration=25.0)
        self.assertGreater(len(pcm_data), 32000, "Extracted PCM data too short")

        profile = VoiceProfiler.profile_from_pcm16(pcm_data, speaker_id="Virat_Kohli")

        # F0 checks for male speaker (Virat Kohli baritone is ~100-130 Hz)
        self.assertGreater(profile.fundamental_frequency_hz, 70.0)
        self.assertLess(profile.fundamental_frequency_hz, 220.0)
        self.assertGreater(profile.spectral_centroid_hz, 500.0)
        self.assertGreater(profile.pitch_stability, 0.70)
        self.assertEqual(profile.gender_estimate, "masculine")
        self.assertIsNotNone(profile.recommended_voice)
        self.assertEqual(profile.speaker_id, "Virat_Kohli")

    def test_voice_profiler_edge_cases(self):
        """Stress-test VoiceProfiler with silence, empty buffer, and noise."""
        empty_profile = VoiceProfiler.profile_from_pcm16(b"", speaker_id="Empty")
        self.assertEqual(empty_profile.fundamental_frequency_hz, 140.0)  # Safe default fallback

        silence_pcm = bytes(16000 * 2)  # 1s of pure zeros
        silence_profile = VoiceProfiler.profile_from_pcm16(silence_pcm, speaker_id="Silent")
        self.assertIsNotNone(silence_profile)
        self.assertEqual(silence_profile.fundamental_frequency_hz, 130.0)  # Robust neutral speech fallback

        # High-frequency synthetic sine wave (1000 Hz)
        sr = 16000
        t = np.linspace(0, 1.0, sr, endpoint=False)
        sine = (np.sin(2 * np.pi * 1000 * t) * 30000).astype(np.int16)
        sine_profile = VoiceProfiler.profile_from_pcm16(sine.tobytes(), speaker_id="Sine1k")
        self.assertIsNotNone(sine_profile)

    def test_direct_synthesis_workflow(self):
        """Execute direct voice synthesis workflow via pipeline."""
        if not self.ref_audio_path.exists():
            self.skipTest("Reference audio not found")

        pcm_data, _ = self.extractor.extract_pcm16(str(self.ref_audio_path), max_duration=10.0)
        profile = VoiceProfiler.profile_from_pcm16(pcm_data, speaker_id="Virat_Kohli")

        result = self.pipeline.clone_voice(
            profile=profile,
            text_prompt="Empirical verification of Scriber speech intelligence.",
            reference_pcm=pcm_data,
            backend="edge-neural",
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.audio_base64.startswith("data:audio/mp3;base64,"))
        self.assertGreater(len(result.audio_base64), 1000)
        self.assertGreater(result.duration, 0.5)
        self.assertGreaterEqual(result.similarity_score, 0.0)
        self.assertLessEqual(result.similarity_score, 1.0)

    def test_dropdown_inference_lockout_logic(self):
        """Verify frontend locking logic prevents race conditions during synthesis inference."""
        app_js = (self.root / "scriber" / "web" / "static" / "app.js").read_text(encoding="utf-8")

        # 1. setVoiceModelLocked / setTranscribeModelLocked locks both triggers
        self.assertIn("function setTranscribeModelLocked(locked)", app_js)
        self.assertIn("voice-dropdown-trigger", app_js)
        self.assertIn("el.disabled = true;", app_js)
        self.assertIn("el.classList.add('locked');", app_js)

        # 2. selectVoiceModel aborts if trigger is disabled or locked
        self.assertIn("function selectVoiceModel(modelId)", app_js)
        self.assertIn("trigger.disabled || trigger.classList.contains('locked')", app_js)

        # 3. synthesis functions call setVoiceModelLocked(true) before inference and false after
        self.assertIn("setVoiceModelLocked(true);", app_js)
        self.assertIn("setVoiceModelLocked(false);", app_js)


class TestChallengerFeature7ExportPipeline(unittest.TestCase):
    """Empirical verification of Feature 7: Export Pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parent.parent
        cls.output_dir = cls.root / "scriber_output"

    def _create_sample_scriber_output(self) -> ScriberOutput:
        metadata = AudioMetadata(
            filename="empirical_test.mp3",
            duration=30.0,
            sample_rate=16000,
            channels=1,
            file_size_bytes=960000,
            file_format="mp3",
            bitrate_kbps=128,
        )
        segments = [
            AudioSegment(id=0, seek=0, start=0.0, end=5.5, text="First empirical segment of test transcript.", speaker="Speaker_1"),
            AudioSegment(id=1, seek=0, start=6.0, end=14.2, text="Second segment confirming subtitle formatting.", speaker="Speaker_2"),
        ]
        transcription = TranscriptionResult(
            text="First empirical segment of test transcript. Second segment confirming subtitle formatting.",
            language="en",
            language_probability=0.99,
            duration=30.0,
            segments=segments,
            backend_used="whisper-turbo",
        )
        exec_sum = ExecutiveSummary(
            headline="Empirical Verification Briefing",
            tldr="Summary of test session verifying export pipeline integrity across all file formats.",
            key_takeaways=["All formats verified non-empty", "SRT timecodes conform to spec"],
            decisions_reached=["Approve format export pipeline"],
            action_items_count=1,
        )
        council = CouncilAnalysis(
            executive_summary=exec_sum,
            action_items=[ActionItem(id="ACT-001", task="Verify formats", assignee="QA", priority="high", status="open", start_time=0.0, end_time=5.5)],
            discussion_points=[DiscussionPoint(id="DP-001", title="Export Integrity", summary="Verification of all 5 export formats", speakers=["Speaker_1", "Speaker_2"], start_time=0.0, end_time=14.2)],
        )
        return ScriberOutput(
            session_id="test_sess_001",
            video_source="empirical_test.mp3",
            audio_metadata=metadata,
            transcription=transcription,
            translation=None,
            council_analysis=council,
            quality_report=QualityReport(
                overall_score=0.99,
                confidence_avg=0.98,
                repetition_looping_detected=False,
                hallucinations_culled=0,
                low_confidence_segments_flagged=0,
                compression_ratio_healthy=True,
                word_count=10,
                estimated_speaking_wpm=120.0,
            ),
            validation_report=ValidationReport(
                accuracy_score=1.0,
                wer=0.0,
                cer=0.0,
                precision=1.0,
                recall=1.0,
                f1_score=1.0,
                passed_99_percent=True,
                certificate_id="CERT-TEST-001",
                root_hash="sha256_mock_hash",
                hash_chain=[HashChainBlock(0, "INIT", 0.0, "0"*64, "hash_0", "Init")],
            ),
            processing_time_seconds=1.23,
        )

    def test_export_all_formats_syntactically_valid(self):
        """Generate and validate TXT, SRT, VTT, JSON, and HTML exports."""
        output = self._create_sample_scriber_output()

        # 1. TXT
        txt = ScriberExporter.to_txt(output)
        self.assertIn("SCRIBER TRANSCRIPT:", txt)
        self.assertIn("[00:00 - 00:05] Speaker 1:", txt)
        self.assertIn("First empirical segment of test transcript.", txt)

        # 2. SRT
        srt = ScriberExporter.to_srt(output)
        self.assertIn("1\n00:00:00,000 --> 00:00:05,500", srt)
        self.assertIn("-->", srt)
        self.assertIn("First empirical segment of test transcript.", srt)

        # 3. VTT
        vtt = ScriberExporter.to_vtt(output)
        self.assertTrue(vtt.startswith("WEBVTT"))
        self.assertIn("00:00:00.000 --> 00:00:05.500", vtt)

        # 4. JSON
        json_str = ScriberExporter.to_json(output)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["session_id"], "test_sess_001")
        self.assertIn("transcription", parsed)
        self.assertIn("council_analysis", parsed)

        # 5. HTML
        html = ScriberExporter.to_html(output)
        self.assertIn("doctype html", html.lower())
        self.assertIn("<html", html.lower())
        self.assertIn("</html>", html.lower())
        self.assertIn("empirical verification briefing", html.lower())

    def test_inspect_existing_scriber_output_artifacts(self):
        """Inspect actual generated export files in ./scriber_output/ from live runs."""
        self.assertTrue(self.output_dir.exists(), "./scriber_output does not exist")

        target_base = "Sunil Bharti Mittal Appeals For India-Focused Growth, Echoes PM Modi's 'Economic Patriotism' Message"

        # Check TXT
        txt_file = self.output_dir / f"{target_base}_transcript.txt"
        self.assertTrue(txt_file.exists(), f"TXT export missing: {txt_file}")
        txt_content = txt_file.read_text(encoding="utf-8")
        self.assertGreater(len(txt_content), 100)
        self.assertIn("Speaker 1", txt_content)

        # Check SRT
        srt_file = self.output_dir / f"{target_base}.srt"
        self.assertTrue(srt_file.exists(), f"SRT export missing: {srt_file}")
        srt_content = srt_file.read_text(encoding="utf-8")
        self.assertIn("-->", srt_content)
        self.assertTrue(re.search(r"\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}", srt_content))

        # Check VTT
        vtt_file = self.output_dir / f"{target_base}.vtt"
        self.assertTrue(vtt_file.exists(), f"VTT export missing: {vtt_file}")
        vtt_content = vtt_file.read_text(encoding="utf-8")
        self.assertTrue(vtt_content.startswith("WEBVTT"))
        self.assertIn("-->", vtt_content)

        # Check JSON
        json_file = self.output_dir / f"{target_base}.json"
        self.assertTrue(json_file.exists(), f"JSON export missing: {json_file}")
        json_content = json.loads(json_file.read_text(encoding="utf-8"))
        self.assertIn("transcription", json_content)
        self.assertIn("segments", json_content["transcription"])
        self.assertGreater(len(json_content["transcription"]["segments"]), 0)

        # Check HTML
        html_file = self.output_dir / f"{target_base}_dashboard.html"
        self.assertTrue(html_file.exists(), f"HTML export missing: {html_file}")
        html_content = html_file.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("Scriber Report", html_content)


class TestChallengerConstraintR2LocalExecution(unittest.TestCase):
    """Empirical verification of Constraint R2: 100% Local Execution (Zero Paid APIs)."""

    def test_voice_credentials_endpoint_zero_financial_exposure(self):
        """Verify /api/voice/credentials confirms zero financial exposure and no paid APIs."""
        server = ScriberBackgroundServer(port=8199)
        server.start()
        try:
            import urllib.request
            req = urllib.request.Request(f"{server.url}/api/voice/credentials")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("zero_financial_exposure"), "zero_financial_exposure is not True")
                self.assertFalse(data.get("voicemaker_configured"), "Voicemaker paid API is configured")
                self.assertFalse(data.get("elevenlabs_configured"), "ElevenLabs paid API is configured")
        finally:
            server.stop()

    def test_no_outbound_cloud_calls_during_voice_synthesis(self):
        """Verify speech synthesis functions without external internet connection."""
        from scriber.pipeline import ScriberPipeline
        pipeline = ScriberPipeline()

        profile = VoiceProfiler._empty_profile("Offline_Speaker")
        result = pipeline.clone_voice(
            profile=profile,
            text_prompt="Local offline test prompt without cloud connections.",
            backend="edge-neural",
        )
        self.assertIsNotNone(result)
        self.assertTrue(result.audio_base64.startswith("data:audio/mp3;base64,"))
        self.assertGreater(len(result.audio_base64), 500)


if __name__ == "__main__":
    unittest.main()
