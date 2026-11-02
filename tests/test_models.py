"""Unit tests for Scriber data models and serialization contracts."""

import unittest
from scriber.models import (
    ActionItem,
    AgentProfile,
    AgentTelemetry,
    AudioMetadata,
    AudioSegment,
    CouncilAnalysis,
    DiscussionPoint,
    ExecutiveSummary,
    HardwareCapabilities,
    HashChainBlock,
    PIIRedactionReport,
    QualityReport,
    ScriberOutput,
    TranscriptionResult,
    ValidationReport,
    VoiceCloneResult,
    VoiceProfile,
    WordTimestamp,
)


class TestScriberModels(unittest.TestCase):
    """Verifies dataclass construction, default fields, and to_dict contracts."""

    def test_word_timestamp(self):
        wt = WordTimestamp(word="hello", start=0.0, end=0.5, probability=0.98)
        d = wt.to_dict()
        self.assertEqual(d["word"], "hello")
        self.assertEqual(d["start"], 0.0)
        self.assertEqual(d["end"], 0.5)
        self.assertEqual(d["probability"], 0.98)

    def test_audio_segment(self):
        wt = WordTimestamp(word="test", start=0.1, end=0.4, probability=1.0)
        seg = AudioSegment(
            id=1,
            seek=0,
            start=0.0,
            end=1.5,
            text=" test speech ",
            words=[wt],
            speaker="Speaker_1",
            confidence=0.99,
        )
        d = seg.to_dict()
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["text"], "test speech")
        self.assertEqual(d["speaker"], "Speaker_1")
        self.assertEqual(len(d["words"]), 1)
        self.assertEqual(d["confidence"], 0.99)

    def test_audio_metadata(self):
        meta = AudioMetadata(
            filename="meeting.mp4",
            duration=60.0,
            sample_rate=16000,
            channels=1,
            file_size_bytes=1024,
            file_format="mp4",
            bitrate_kbps=128,
        )
        d = meta.to_dict()
        self.assertEqual(d["filename"], "meeting.mp4")
        self.assertEqual(d["duration"], 60.0)
        self.assertEqual(d["sample_rate"], 16000)

    def test_hardware_capabilities(self):
        hw = HardwareCapabilities(
            gpu_name="NVIDIA RTX",
            vram_total_mb=8192.0,
            vram_free_mb=6144.0,
            compute_capability=(8, 9),
            cuda_available=True,
            cuda_version="12.4",
            recommended_device="cuda",
            recommended_compute_type="int8",
        )
        d = hw.to_dict()
        self.assertEqual(d["gpu_name"], "NVIDIA RTX")
        self.assertTrue(d["cuda_available"])
        self.assertEqual(d["recommended_device"], "cuda")
        self.assertEqual(d["compute_capability"], [8, 9])

    def test_transcription_result(self):
        res = TranscriptionResult(
            text="Hello world",
            language="en",
            language_probability=0.999,
            duration=2.5,
        )
        d = res.to_dict()
        self.assertEqual(d["text"], "Hello world")
        self.assertEqual(d["language"], "en")
        self.assertEqual(d["task"], "transcribe")
        self.assertEqual(d["segments"], [])

    def test_action_item(self):
        item = ActionItem(
            id="act_01",
            task="Update roadmap",
            assignee="Lakshya",
            priority="high",
            start_time=12.5,
            end_time=18.0,
        )
        d = item.to_dict()
        self.assertEqual(d["id"], "act_01")
        self.assertEqual(d["assignee"], "Lakshya")
        self.assertEqual(d["priority"], "high")
        self.assertIn("00:12", d["timestamp"])

    def test_discussion_point(self):
        dp = DiscussionPoint(
            id="disc_01",
            title="Architecture Review",
            summary="Reviewed modular layout",
            start_time=65.0,
            end_time=120.0,
            speakers=["Speaker_1", "Speaker_2"],
        )
        d = dp.to_dict()
        self.assertEqual(d["title"], "Architecture Review")
        self.assertIn("01:05", d["timestamp_range"])

    def test_executive_summary(self):
        summary = ExecutiveSummary(
            headline="Quarterly Sync",
            tldr="Met all benchmarks",
            key_takeaways=["Fast", "Accurate"],
            decisions_reached=["Deploy v2"],
        )
        d = summary.to_dict()
        self.assertEqual(d["headline"], "Quarterly Sync")
        self.assertEqual(len(d["decisions_reached"]), 1)

    def test_quality_and_validation_reports(self):
        qr = QualityReport(
            overall_score=0.995,
            confidence_avg=0.99,
            repetition_looping_detected=False,
            hallucinations_culled=0,
            low_confidence_segments_flagged=0,
            compression_ratio_healthy=True,
            word_count=250,
            estimated_speaking_wpm=140.0,
        )
        self.assertEqual(qr.to_dict()["overall_score"], 0.995)

        block = HashChainBlock(
            index=0,
            block_name="GENESIS",
            timestamp=100.0,
            prev_hash="0" * 64,
            block_hash="abc",
            payload_summary="init",
        )
        vr = ValidationReport(
            accuracy_score=0.998,
            wer=0.002,
            cer=0.001,
            precision=0.999,
            recall=0.998,
            f1_score=0.9985,
            passed_99_percent=True,
            certificate_id="CERT-100",
            hash_chain=[block],
        )
        d = vr.to_dict()
        self.assertTrue(d["passed_99_percent"])
        self.assertEqual(len(d["hash_chain"]), 1)

    def test_voice_profile_and_clone_result(self):
        vp = VoiceProfile(
            speaker_id="Speaker_A",
            fundamental_frequency_hz=145.0,
            pitch_min_hz=100.0,
            pitch_max_hz=200.0,
            pitch_std_hz=15.0,
            spectral_centroid_hz=1600.0,
            zero_crossing_rate=0.05,
            estimated_wpm=155.0,
            energy_rms=0.12,
            gender_estimate="masculine",
            sample_duration=3.5,
        )
        d = vp.to_dict()
        self.assertEqual(d["speaker_id"], "Speaker_A")

        reconstructed = VoiceProfile.from_dict(d)
        self.assertEqual(reconstructed.speaker_id, "Speaker_A")
        self.assertEqual(reconstructed.fundamental_frequency_hz, 145.0)

        vcr = VoiceCloneResult(
            profile=vp,
            text_prompt="Testing cloned speech synthesis.",
            audio_pcm16=b"\x00\x00" * 100,
            audio_format="wav",
            similarity_score=0.995,
            synthesis_backend="local-formant",
            audio_base64="data:audio/wav;base64,AAAA",
            duration=1.2,
        )
        vcd = vcr.to_dict()
        self.assertEqual(vcd["speaker_id"], "Speaker_A")
        self.assertIn("99.50%", vcd["similarity_percentage"])


if __name__ == "__main__":
    unittest.main()
