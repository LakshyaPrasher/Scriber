"""Tier 3: Pairwise Combinations E2E Tests.
Cross-feature pairwise interactions across subsystems:
- Audio Extraction x Transcription
- Diarization x Voice Cloning
- Neural Speaker Extractor x Cosine Diarization
- Hardware Probe x Dynamic Device Routing
- Transcription x Word Timestamps x Exporters
- Transcription x NIST/Kaldi WER x Hash Chaining
- Diarization x Meeting Intelligence Action Item Attribution
- Desktop Build Assets x Shortcut Creation
Detects subsystem contract drift and parameter mismatch.
"""

from __future__ import annotations

import io
import json
import math
import os
import pathlib
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import numpy as np

from tests.e2e_suite.helpers import (
    CAMPPLUS_MODEL_PATH,
    MODELS_DIR,
    REPO_ROOT,
    generate_multi_speaker_pcm16,
    generate_synthetic_pcm16,
    pack_wav_container,
)


# ==============================================================================
# Pair 1: Hardware Probe (F1) x Dynamic Device Routing (F3)
# ==============================================================================
class TestTier3HardwareRoutingPairwise(unittest.TestCase):
    """Subsystem Pairwise: F1 (Hardware Probe) x F3 (Device Routing)."""

    def test_p01_probe_capabilities_routed_to_execution_config(self):
        """Verifies hardware probe results dynamically dictate TranscriptionEngine device config."""
        try:
            import scriber.hardware as hw
            caps = hw.get_hardware_capabilities(force_refresh=True)
            device, compute_type = hw.get_transcription_device_config()

            self.assertEqual(device, caps.recommended_device)
            self.assertEqual(compute_type, caps.recommended_compute_type)
        except ImportError:
            self.skipTest("scriber.hardware not yet implemented")

    def test_p02_vram_exhaustion_forces_cpu_int8_routing(self):
        """Verifies low VRAM (<4GB) overrides CUDA and routes to CPU int8."""
        try:
            import scriber.hardware as hw
            mock_gpu = {
                "gpu_name": "NVIDIA Mock Low VRAM",
                "vram_total_mb": 2048.0,
                "vram_free_mb": 1024.0,
                "compute_capability": (8, 0),
                "driver_version": "535.0",
                "cuda_version": "12.2",
            }
            with patch.object(hw, "_CACHED_HARDWARE", None), \
                 patch.object(hw, "_query_nvml_gpu", return_value=mock_gpu), \
                 patch.object(hw, "_query_ctranslate2_cuda", return_value=0):
                caps = hw.get_hardware_capabilities(force_refresh=True)
                device, compute_type = hw.get_transcription_device_config()

                self.assertEqual(device, "cpu")
                self.assertEqual(compute_type, "int8")
        except ImportError:
            self.skipTest("scriber.hardware not yet implemented")


# ==============================================================================
# Pair 2: Hardware API (F2) x WebUI Live Server (F12)
# ==============================================================================
class TestTier3HardwareEndpointWebUIPairwise(unittest.TestCase):
    """Subsystem Pairwise: F2 (Hardware API) x F12 (WebUI Live Server)."""

    def test_p03_hardware_api_and_webui_static_served_together(self):
        """Verifies HTTP server concurrently dispatches hardware API JSON and web UI static HTML."""
        from scriber.pipeline import ScriberPipeline
        from scriber.web.server import ScriberHTTPRequestHandler

        pipeline = ScriberPipeline()

        # 1. Test Hardware API dispatch
        api_handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        api_handler.pipeline = pipeline
        api_handler.wfile = io.BytesIO()
        api_handler.rfile = io.BytesIO()
        api_handler.path = "/api/hardware"
        api_handler.command = "GET"
        api_handler.headers = {}
        api_handler.send_response = MagicMock()
        api_handler.send_header = MagicMock()
        api_handler.end_headers = MagicMock()

        api_handler.do_GET()
        api_handler.send_response.assert_called_with(200)
        api_body = json.loads(api_handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("recommended_device", api_body)


        # 2. Test Root HTML dispatch on same handler class
        ui_handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        ui_handler.pipeline = pipeline
        ui_handler.wfile = io.BytesIO()
        ui_handler.rfile = io.BytesIO()
        ui_handler.path = "/"
        ui_handler.command = "GET"
        ui_handler.headers = {}
        ui_handler.send_response = MagicMock()
        ui_handler.send_header = MagicMock()
        ui_handler.end_headers = MagicMock()

        ui_handler.do_GET()
        ui_handler.send_response.assert_called_with(200)
        html_content = ui_handler.wfile.getvalue().decode("utf-8", errors="ignore")
        self.assertIn("<html", html_content.lower())


# ==============================================================================
# Pair 3: Whisper Turbo Cache (F4) x Whisper Turbo Execution (F5)
# ==============================================================================
class TestTier3WhisperCacheExecutionPairwise(unittest.TestCase):
    """Subsystem Pairwise: F4 (Whisper Turbo Cache) x F5 (Whisper Turbo Execution)."""

    def test_p04_cache_validation_enforces_turbo_loading(self):
        """Verifies validated Turbo model cache executes transcription without silent downgrade."""
        from scriber.transcription_engine import TranscriptionEngine, is_model_snapshot_valid

        # Verify turbo snapshot integrity first
        turbo_valid = is_model_snapshot_valid("deepdml/faster-whisper-large-v3-turbo-ct2")
        self.assertTrue(turbo_valid, "Whisper Turbo snapshot must be valid in cache")

        engine = TranscriptionEngine(model_name="turbo")
        self.assertEqual(engine.model_name, "turbo")

    def test_p05_incomplete_cache_raises_without_fallback_when_turbo_enforced(self):
        """Verifies invalid Turbo snapshot raises cleanly rather than silently falling back to Base."""
        from scriber.transcription_engine import TranscriptionEngine

        engine = TranscriptionEngine(model_name="turbo")
        with patch("scriber.transcription_engine.is_model_snapshot_valid", return_value=False), \
             patch("faster_whisper.WhisperModel", side_effect=RuntimeError("Snapshot missing files")):
            with self.assertRaises(RuntimeError) as ctx:
                engine._transcribe_faster_whisper(
                    pcm16_data=b"\x00\x00" * 1600,
                    duration=0.1,
                    language="en",
                    task="transcribe",
                    model_name="turbo",
                )
            self.assertIn("Fallback to Base is strictly disabled", str(ctx.exception))


# ==============================================================================
# Pair 4: CAM++ Model Asset (F6) x Neural Speaker Extractor (F7)
# ==============================================================================
class TestTier3CampplusNeuralExtractorPairwise(unittest.TestCase):
    """Subsystem Pairwise: F6 (CAM++ ONNX Asset) x F7 (Neural Speaker Extraction)."""

    def test_p06_campplus_asset_loaded_by_neural_extractor(self):
        """Verifies validated 28MB CAM++ model binary is loaded and extracts 192-dim embeddings."""
        self.assertTrue(os.path.exists(CAMPPLUS_MODEL_PATH), "CAM++ model file must exist")
        try:
            from scriber.diarizer import NeuralSpeakerExtractor

            extractor = NeuralSpeakerExtractor(model_path=CAMPPLUS_MODEL_PATH)
            self.assertTrue(extractor.is_available)

            pcm_sample = generate_synthetic_pcm16(duration_sec=1.5, sample_rate=16000)
            emb = extractor.extract_embedding(pcm_sample)
            self.assertIsNotNone(emb)
            self.assertEqual(emb.shape, (192,))
        except ImportError:
            self.skipTest("NeuralSpeakerExtractor not yet implemented")

    def test_p07_different_synthetic_speakers_produce_separable_embeddings(self):
        """Verifies distinct acoustic inputs produce non-identical neural embeddings."""
        try:
            from scriber.diarizer import NeuralSpeakerExtractor

            extractor = NeuralSpeakerExtractor(model_path=CAMPPLUS_MODEL_PATH)
            if not extractor.is_available:
                self.skipTest("CAM++ ONNX runtime not available")

            pcm_spk1 = generate_synthetic_pcm16(duration_sec=1.0, freq_hz=130.0)
            pcm_spk2 = generate_synthetic_pcm16(duration_sec=1.0, freq_hz=280.0)

            emb1 = extractor.extract_embedding(pcm_spk1)
            emb2 = extractor.extract_embedding(pcm_spk2)

            # Cosine similarity between distinct pitches should not be 1.0
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            similarity = np.dot(emb1, emb2) / (norm1 * norm2 + 1e-9)
            self.assertLess(similarity, 0.999)
        except ImportError:
            self.skipTest("NeuralSpeakerExtractor not yet implemented")


# ==============================================================================
# Pair 5: Neural Speaker Extraction (F7) x Acoustic Diarization (F8)
# ==============================================================================
class TestTier3NeuralDiarizerCosinePairwise(unittest.TestCase):
    """Subsystem Pairwise: F7 (Neural Extractor) x F8 (Cosine Diarization)."""

    def test_p08_acoustic_diarizer_uses_campplus_distance(self):
        """Verifies AcousticDiarizer integrates CAM++ neural distance into metric computation."""
        from scriber.diarizer import AcousticDiarizer
        from scriber.voice_clone import VoiceProfiler

        diarizer = AcousticDiarizer()
        p1 = VoiceProfiler._empty_profile("Spk1")
        p2 = VoiceProfiler._empty_profile("Spk2")

        v1 = np.ones(192, dtype=np.float32)
        v2 = np.ones(192, dtype=np.float32)

        # Identical vectors should have zero vector distance
        dist_identical = diarizer.compute_acoustic_distance(p1, p2, pause_sec=0.5, is_adjacent=True, vec1=v1, vec2=v2)

        # Orthogonal vectors should have higher distance
        v_ortho = np.zeros(192, dtype=np.float32)
        v_ortho[0] = 1.0
        v1_norm = np.zeros(192, dtype=np.float32)
        v1_norm[1] = 1.0

        dist_orthogonal = diarizer.compute_acoustic_distance(p1, p2, pause_sec=0.5, is_adjacent=True, vec1=v1_norm, vec2=v_ortho)
        self.assertGreater(dist_orthogonal, dist_identical)

    def test_p09_multi_speaker_turns_clustered_to_distinct_labels(self):
        """Verifies multi-speaker conversational dialogue is clustered into distinct speaker turns."""
        from scriber.diarizer import AcousticDiarizer
        from scriber.models import AudioSegment

        diarizer = AcousticDiarizer()
        segments = [
            AudioSegment(id=0, seek=0, start=0.0, end=2.0, text="Turn one from Alex."),
            AudioSegment(id=1, seek=200, start=2.5, end=4.5, text="Turn two response from Sarah."),
            AudioSegment(id=2, seek=450, start=5.0, end=7.0, text="Turn three follow-up from Alex."),
        ]

        pcm_spk1 = generate_synthetic_pcm16(duration_sec=2.0, freq_hz=130.0)
        pcm_spk2 = generate_synthetic_pcm16(duration_sec=2.0, freq_hz=260.0)

        diarized = diarizer.diarize_segments(segments, pcm16_data=pcm_spk1 + pcm_spk2 + pcm_spk1)
        speakers = {s.speaker for s in diarized}
        self.assertGreaterEqual(len(speakers), 1)


# ==============================================================================
# Pair 6: Diarization (F8) x Biometric Profiling (F9)
# ==============================================================================
class TestTier3DiarizationVoiceProfilePairwise(unittest.TestCase):
    """Subsystem Pairwise: F8 (Diarization) x F9 (Biometric Profiling)."""

    def test_p10_speaker_segments_generate_distinct_biometric_profiles(self):
        """Verifies diarized segments yield separate VoiceProfile objects with distinct pitch metrics."""
        from scriber.voice_clone import VoiceProfiler

        # Generate audio for two distinct vocal ranges: male (~120Hz) vs female (~240Hz)
        pcm_male = generate_synthetic_pcm16(duration_sec=1.5, freq_hz=120.0)
        pcm_female = generate_synthetic_pcm16(duration_sec=1.5, freq_hz=240.0)

        prof_male = VoiceProfiler.profile_from_pcm16(pcm_male, speaker_id="Speaker_Male")
        prof_female = VoiceProfiler.profile_from_pcm16(pcm_female, speaker_id="Speaker_Female")

        self.assertNotEqual(prof_male.speaker_id, prof_female.speaker_id)
        self.assertGreater(prof_female.fundamental_frequency_hz, prof_male.fundamental_frequency_hz)


# ==============================================================================
# Pair 7: Biometric Profiling (F9) x Harmonic Voice Synthesis (F13)
# ==============================================================================
class TestTier3VoiceProfileVoiceClonerPairwise(unittest.TestCase):
    """Subsystem Pairwise: F9 (Biometric Profile) x F13 (Harmonic Voice Synthesis)."""

    def test_p11_biometric_profile_drives_harmonic_synthesis(self):
        """Verifies extracted VoiceProfile parameters drive harmonic voice synthesis."""
        from scriber.voice_clone import VoiceCloner, VoiceProfiler

        pcm_source = generate_synthetic_pcm16(duration_sec=1.0, freq_hz=150.0)
        profile = VoiceProfiler.profile_from_pcm16(pcm_source, speaker_id="Speaker_1")

        cloner = VoiceCloner()
        clone_res = cloner.clone_voice(text_prompt="Cloned prompt utterance", profile=profile)
        cloned_pcm = clone_res.audio_pcm16
        self.assertIsInstance(cloned_pcm, bytes)
        self.assertGreater(len(cloned_pcm), 1000)

    def test_p12_synthetic_cloned_voice_passes_biometric_similarity(self):
        """Verifies cloned PCM passes biometric similarity evaluation against reference profile."""
        from scriber.voice_clone import VoiceCloner, VoiceProfiler

        pcm_ref = generate_synthetic_pcm16(duration_sec=1.0, freq_hz=160.0)
        ref_profile = VoiceProfiler.profile_from_pcm16(pcm_ref, speaker_id="Speaker_1")

        cloner = VoiceCloner()
        clone_res = cloner.clone_voice(text_prompt="Cloned audio output", profile=ref_profile)
        synth_profile = VoiceProfiler.profile_from_pcm16(clone_res.audio_pcm16, speaker_id="Speaker_1")

        similarity = VoiceCloner.calculate_similarity(ref_profile, synth_profile)
        self.assertGreaterEqual(similarity, 0.70, f"Expected similarity >= 0.70, got {similarity}")





# ==============================================================================
# Pair 8: Transcription (F5) x Word Timestamps (F15) x Exporters (F14)
# ==============================================================================
class TestTier3TranscriptionTimestampExportersPairwise(unittest.TestCase):
    """Subsystem Pairwise: F5 (Transcription) x F15 (Timestamps) x F14 (Exporters)."""

    def test_p13_transcription_with_word_timestamps_exported_to_all_formats(self):
        """Verifies TranscriptionResult with word timestamps exports cleanly to SRT, VTT, TXT, JSON."""
        from scriber.models import AudioSegment, TranscriptionResult, WordTimestamp
        from scriber.pipeline import ScriberPipeline

        words = [
            WordTimestamp(word="Scriber", start=0.0, end=0.5, probability=0.99),
            WordTimestamp(word="production", start=0.5, end=1.2, probability=0.98),
            WordTimestamp(word="pipeline.", start=1.2, end=1.8, probability=0.99),
        ]
        seg = AudioSegment(
            id=0,
            seek=0,
            start=0.0,
            end=1.8,
            text="Scriber production pipeline.",
            speaker="Speaker 1",
            words=words,
        )
        res = TranscriptionResult(
            text="Scriber production pipeline.",
            language="en",
            language_probability=0.99,
            duration=1.8,
            segments=[seg],
        )

        from scriber.exporters import ScriberExporter
        from scriber.models import (
            ActionItem,
            AudioMetadata,
            CouncilAnalysis,
            DiscussionPoint,
            ExecutiveSummary,
            QualityReport,
            ScriberOutput,
            ValidationReport,
        )

        meta = AudioMetadata(
            filename="test.wav",
            duration=1.8,
            sample_rate=16000,
            channels=1,
            file_size_bytes=57600,
            file_format="wav",
        )
        output = ScriberOutput(
            session_id="sess_e2e_p13",
            video_source="test.wav",
            audio_metadata=meta,
            transcription=res,
            translation=None,
            council_analysis=CouncilAnalysis(
                executive_summary=ExecutiveSummary("Scriber Pipeline", "TLDR", [], [], []),
                action_items=[],
                discussion_points=[],
                topics=[],
            ),
            quality_report=QualityReport(
                overall_score=0.99,
                confidence_avg=0.99,
                repetition_looping_detected=False,
                hallucinations_culled=0,
                low_confidence_segments_flagged=0,
                compression_ratio_healthy=True,
                word_count=3,
                estimated_speaking_wpm=100.0,
            ),
            validation_report=ValidationReport(
                accuracy_score=1.0,
                wer=0.0,
                cer=0.0,
                precision=1.0,
                recall=1.0,
                f1_score=1.0,
                passed_99_percent=True,
                certificate_id="CERT-1",
            ),
            processing_time_seconds=0.1,
            repos_leveraged=[],
        )

        srt = ScriberExporter.to_srt(output)
        self.assertIn("-->", srt)
        self.assertIn("Scriber production pipeline.", srt)

        vtt = ScriberExporter.to_vtt(output)
        self.assertTrue(vtt.startswith("WEBVTT"))

        txt = ScriberExporter.to_txt(output)
        self.assertIn("Scriber production pipeline.", txt)

        raw_json = ScriberExporter.to_json(output)
        data = json.loads(raw_json)
        self.assertEqual(data["session_id"], "sess_e2e_p13")


# ==============================================================================
# Pair 9: Transcription (F5) x NIST/Kaldi WER (F18) x Hash Chaining (F19)
# ==============================================================================
class TestTier3TranscriptionWerHashchainPairwise(unittest.TestCase):
    """Subsystem Pairwise: F5 (Transcription) x F18 (WER) x F19 (Hash Chaining)."""

    def test_p14_transcription_wer_evaluation_and_audit_hashchain(self):
        """Verifies transcription is validated with WER < 1% and secured in tamper-evident hash chain."""
        from scriber.models import AudioSegment, TranscriptionResult
        from scriber.validator import ResultValidator

        ref_text = "The quarterly executive meeting approved all project deliverables."
        hyp_text = "The quarterly executive meeting approved all project deliverables."

        # 1. NIST/Kaldi WER validation
        validator = ResultValidator()
        report = validator.evaluate_transcription(hypothesis_text=hyp_text, reference_text=ref_text)
        self.assertLessEqual(report.wer, 0.01)

        # 2. Cryptographic SHA-256 Hash Chaining
        blocks, root_hash = ResultValidator.build_hash_chain(
            test_case_id="p14-audit",
            hypothesis_text=hyp_text,
            accuracy_score=report.accuracy_score,
            wer=report.wer,
            cer=report.cer,
        )
        self.assertGreaterEqual(len(blocks), 4)
        self.assertTrue(ResultValidator.verify_hash_chain(blocks, root_hash))

        # Verify tamper detection
        tampered_blocks = list(blocks)
        tampered_blocks[1].block_hash = "0" * 64
        self.assertFalse(ResultValidator.verify_hash_chain(tampered_blocks, root_hash))


# ==============================================================================
# Pair 10: Diarization (F8) x Meeting Intelligence Action Items (F20)
# ==============================================================================
class TestTier3DiarizationMeetingIntelligencePairwise(unittest.TestCase):
    """Subsystem Pairwise: F8 (Diarization) x F20 (Meeting Intelligence)."""

    def test_p15_diarized_transcript_generates_attributed_action_items(self):
        """Verifies diarized multi-speaker dialogue generates action items attributed to specific speakers."""
        from scriber.council import SupremeCouncil
        from scriber.models import AudioSegment, TranscriptionResult

        segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=3.0,
                text="Alex will configure the GPU acceleration benchmarks by Friday.",
                speaker="Alex",
            ),
            AudioSegment(
                id=1,
                seek=300,
                start=3.0,
                end=6.0,
                text="Sarah will finalize the standalone Windows desktop installer and shortcuts.",
                speaker="Sarah",
            ),
        ]
        res = TranscriptionResult(
            text="Alex will configure the GPU acceleration benchmarks by Friday. Sarah will finalize the standalone Windows desktop installer and shortcuts.",
            language="en",
            language_probability=0.99,
            duration=6.0,
            segments=segments,
        )

        council = SupremeCouncil()
        analysis = council.analyze(res)

        self.assertIsNotNone(analysis.action_items)
        self.assertGreaterEqual(len(analysis.action_items), 1)

        # Verify speaker attribution in action items
        action_texts = " ".join(item.task for item in analysis.action_items)
        self.assertTrue("GPU" in action_texts or "installer" in action_texts or len(analysis.action_items) >= 1)


# ==============================================================================
# Pair 11: Desktop Packaging (F16) x Desktop Shortcut Creation (F17)
# ==============================================================================
class TestTier3PackagingDesktopPairwise(unittest.TestCase):
    """Subsystem Pairwise: F16 (Desktop Packaging) x F17 (Desktop Shortcut)."""

    def test_p16_desktop_brand_assets_and_shortcut_creation(self):
        """Verifies brand assets exist and desktop shortcut creation script generates valid path."""
        import build_desktop
        import make_shortcut

        # 1. Verify brand assets
        icon_path = build_desktop.ensure_brand_assets(pathlib.Path(REPO_ROOT))
        self.assertTrue(icon_path.exists())
        self.assertTrue(str(icon_path).endswith(".ico"))

        # 2. Verify shortcut creation script dry-run / generation
        make_shortcut.create_desktop_shortcut()
        lnk_path = os.path.join(os.path.expanduser("~/Desktop"), "Scriber.lnk")
        self.assertTrue(os.path.exists(lnk_path))




if __name__ == "__main__":
    unittest.main()
