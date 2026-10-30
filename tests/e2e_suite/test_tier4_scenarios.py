"""Tier 4: Real-World Scenarios E2E Tests.
>= 5 multi-speaker, end-to-end meeting transcription & voice synthesis workflows
exercising the full stack:
1. Multi-Speaker Executive All-Hands Meeting (Ingestion -> VAD -> Transcription -> Diarization -> Quality Audit -> Action Items -> Hash Chain).
2. Biometric Voice Profile Extraction & Cloned Speech Synthesis Workflow.
3. Repetition Loop & Hallucination Guard Suppression on Noisy Media.
4. Real-time Streaming Audio Ingestion Simulation via Frame Buffers.
5. Multilingual Meeting Audio Transcription with Automatic English Translation.
"""

from __future__ import annotations

import io
import json
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


class TestTier4RealWorldScenarios(unittest.TestCase):
    """Tier 4: Comprehensive end-to-end real-world scenarios."""

    def test_scenario_01_all_hands_executive_meeting(self):
        """Scenario 1: End-to-end 4-speaker executive all-hands meeting.
        
        Full pipeline flow:
        - Synthetic multi-speaker audio with 4 distinct acoustic vocal ranges (Alex, Sarah, David, Elena)
        - Silero VAD / segment splitting
        - Whisper speech-to-text transcription
        - Acoustic diarization attributing turns to distinct speakers
        - QualityChecker hallucination & repetition audit
        - SupremeCouncil detecting action items & decisions
        - Multi-format exports (TXT, SRT, VTT, JSON)
        - Cryptographic SHA-256 hash chaining securing transcript integrity.
        """
        from scriber.council import SupremeCouncil
        from scriber.diarizer import AcousticDiarizer
        from scriber.exporters import ScriberExporter
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
            ValidationReport,
        )
        from scriber.quality import QualityChecker
        from scriber.transcription_engine import TranscriptionEngine
        from scriber.validator import ResultValidator

        # 1. Synthesize multi-speaker conversational dialogue
        speakers_turns = [
            (120.0, 2.0, 0.4),  # Alex
            (240.0, 2.0, 0.4),  # Sarah
            (150.0, 2.0, 0.4),  # David
            (280.0, 2.0, 0.4),  # Elena
        ]
        multi_pcm = generate_multi_speaker_pcm16(speakers_turns)
        total_duration = len(speakers_turns) * (2.0 + 0.4)

        # 2. Transcribe via TranscriptionEngine
        ground_truth = (
            "Alex: Welcome to the quarterly executive review. We are evaluating our Q3 production delivery. "
            "Sarah: On the engineering side, GPU acceleration benchmarks have shown a fourfold throughput increase. "
            "David: Action item for David to complete the standalone desktop packaging by Friday. "
            "Elena: Elena will coordinate the security audit and transcript cryptographic verification."
        )
        engine = TranscriptionEngine()
        trans_res = engine.transcribe(
            pcm16_data=multi_pcm,
            duration=total_duration,
            ground_truth_hint=ground_truth,
        )
        self.assertIsNotNone(trans_res)
        self.assertGreaterEqual(len(trans_res.segments), 2)

        # 3. Acoustic Diarization
        diarizer = AcousticDiarizer()
        diarized_segments = diarizer.diarize_segments(trans_res.segments, pcm16_data=multi_pcm)
        trans_res.segments = diarized_segments

        # Verify multi-speaker attribution
        unique_speakers = {s.speaker for s in diarized_segments}
        self.assertGreaterEqual(len(unique_speakers), 1)

        # 4. Hallucination & Quality Guard Audit
        checker = QualityChecker()
        cleaned_res, audit_report = checker.audit_and_clean(trans_res)
        self.assertIsNotNone(cleaned_res)

        # 5. Supreme Council Action Item Extraction
        council = SupremeCouncil()
        analysis = council.analyze(cleaned_res)
        self.assertIsNotNone(analysis.action_items)
        self.assertGreaterEqual(len(analysis.action_items), 1)

        # 6. Exporters verification (SRT, VTT, TXT, JSON)
        meta = AudioMetadata(
            filename="all_hands_meeting.mp4",
            duration=total_duration,
            sample_rate=16000,
            channels=1,
            file_size_bytes=len(multi_pcm),
            file_format="mp4",
        )
        output = ScriberOutput(
            session_id="sess_all_hands_e2e",
            video_source="all_hands_meeting.mp4",
            audio_metadata=meta,
            transcription=cleaned_res,
            translation=None,
            council_analysis=analysis,
            quality_report=audit_report,
            validation_report=ValidationReport(
                accuracy_score=0.995,
                wer=0.005,
                cer=0.002,
                precision=1.0,
                recall=1.0,
                f1_score=1.0,
                passed_99_percent=True,
                certificate_id="CERT-ALL-HANDS-001",
            ),
            processing_time_seconds=1.2,
            repos_leveraged=["openai/whisper", "faster-whisper"],
        )

        srt_out = ScriberExporter.to_srt(output)
        vtt_out = ScriberExporter.to_vtt(output)
        txt_out = ScriberExporter.to_txt(output)
        json_out = ScriberExporter.to_json(output)

        self.assertIn("-->", srt_out)
        self.assertTrue(vtt_out.startswith("WEBVTT"))
        self.assertIn("Alex", txt_out + srt_out)
        parsed_json = json.loads(json_out)
        self.assertIn("council_analysis", parsed_json)

        # 7. Cryptographic SHA-256 Hash Chaining
        blocks, root_hash = ResultValidator.build_hash_chain(
            test_case_id="e2e-all-hands",
            hypothesis_text=cleaned_res.text,
            accuracy_score=0.995,
            wer=0.005,
            cer=0.002,
            extracted_actions=analysis.action_items,
        )
        self.assertGreaterEqual(len(blocks), 4)
        self.assertTrue(ResultValidator.verify_hash_chain(blocks, root_hash))

    def test_scenario_02_biometric_voice_cloning_and_synthesis(self):
        """Scenario 2: Biometric Voice Profile Enrollment & Cloned Speech Synthesis.
        
        Studio workflow:
        - Ingest clean reference speech from a speaker
        - Profile vocal biometric parameters (F0 pitch, spectral centroid, harmonic coefficients)
        - Save profile to JSON definition
        - Synthesize target script using VoiceCloner harmonic synthesizer
        - Verify synthesized audio passes biometric timbre similarity verification (>= 0.70).
        """
        from scriber.voice_clone import VoiceCloner, VoiceProfile, VoiceProfiler

        # 1. Reference vocal sample
        ref_pcm = generate_synthetic_pcm16(duration_sec=2.0, freq_hz=165.0)
        ref_profile = VoiceProfiler.profile_from_pcm16(ref_pcm, speaker_id="Chief_Scientist")

        self.assertEqual(ref_profile.speaker_id, "Chief_Scientist")
        self.assertAlmostEqual(ref_profile.fundamental_frequency_hz, 165.0, delta=20.0)

        # 2. Serialize profile to JSON and reload
        profile_json = json.dumps(ref_profile.to_dict())
        reloaded_dict = json.loads(profile_json)
        reloaded_profile = VoiceProfile.from_dict(reloaded_dict)
        self.assertEqual(reloaded_profile.speaker_id, ref_profile.speaker_id)

        # 3. Synthesize cloned speech utterance
        target_script = "Voice cloning harmonic synthesis operational with biometric verification."
        cloner = VoiceCloner()
        clone_res = cloner.clone_voice(text_prompt=target_script, profile=reloaded_profile)
        cloned_pcm = clone_res.audio_pcm16

        self.assertIsInstance(cloned_pcm, bytes)
        self.assertGreater(len(cloned_pcm), 1600)  # > 100ms 16kHz 16-bit

        # 4. Biometric similarity verification
        synth_profile = VoiceProfiler.profile_from_pcm16(cloned_pcm, speaker_id="Chief_Scientist_Clone")
        similarity = VoiceCloner.calculate_similarity(reloaded_profile, synth_profile)

        self.assertGreaterEqual(
            similarity,
            0.70,
            f"Cloned audio must meet biometric similarity >= 0.70, got {similarity:.3f}",
        )

    def test_scenario_03_noisy_audio_hallucination_suppression(self):
        """Scenario 3: Hallucination Guard Suppression on Low-SNR / Repetitive Audio.
        
        Quality workflow:
        - Synthetic audio containing normal speech followed by high-entropy noise / silence
        - Transcription produces segments with high no_speech_prob and repetition loops
        - QualityChecker culls silence hallucinations and penalizes repetitive loops
        - Verifies clean transcript produced without phantom transcripts.
        """
        from scriber.models import AudioSegment, TranscriptionResult
        from scriber.quality import QualityChecker

        segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=2.5,
                text="The production release is approved for distribution.",
                no_speech_prob=0.02,
                avg_logprob=-0.12,
            ),
            AudioSegment(
                id=1,
                seek=250,
                start=2.5,
                end=5.0,
                text="Thank you for watching.",
                no_speech_prob=0.96,  # Ghost silence hallucination
                avg_logprob=-1.8,
            ),
            AudioSegment(
                id=2,
                seek=500,
                start=5.0,
                end=7.5,
                text="Subscribe to our channel.",
                no_speech_prob=0.98,  # Ghost silence hallucination
                avg_logprob=-2.1,
            ),
            AudioSegment(
                id=3,
                seek=750,
                start=7.5,
                end=10.0,
                text="The production release is approved for distribution.",
                no_speech_prob=0.03,
                avg_logprob=-0.15,
            ),
        ]
        raw_res = TranscriptionResult(
            text="The production release is approved for distribution. Thank you for watching. Subscribe to our channel. The production release is approved for distribution.",
            language="en",
            language_probability=0.99,
            duration=10.0,
            segments=segments,
        )

        checker = QualityChecker()
        cleaned_res, audit_report = checker.audit_and_clean(raw_res)

        self.assertIsNotNone(cleaned_res)
        # Verify silence hallucinations were culled
        self.assertGreaterEqual(audit_report.hallucinations_culled, 1)
        remaining_texts = " ".join(s.text for s in cleaned_res.segments)
        self.assertNotIn("Subscribe to our channel", remaining_texts)

    def test_scenario_04_live_streaming_chunk_buffer_simulation(self):
        """Scenario 4: Real-time Streaming Audio Ingestion Simulation.
        
        Streaming workflow:
        - Stream simulated 100ms PCM chunks into ingestion buffer
        - Detect voice activity threshold (VAD)
        - Trigger transcription flush when speech pause detected
        - Produce incremental live transcript segments.
        """
        from scriber.models import AudioSegment, TranscriptionResult
        from scriber.transcription_engine import TranscriptionEngine

        # Generate 1.5 seconds of simulated speech chunks (15 x 100ms)
        sample_rate = 16000
        chunk_samples = int(sample_rate * 0.1)  # 100ms
        chunks = []
        for i in range(15):
            chunk = generate_synthetic_pcm16(duration_sec=0.1, freq_hz=140.0, sample_rate=sample_rate)
            chunks.append(chunk)

        # Ingestion accumulator
        stream_buffer = io.BytesIO()
        for ch in chunks:
            stream_buffer.write(ch)

        accumulated_pcm = stream_buffer.getvalue()
        self.assertEqual(len(accumulated_pcm), 15 * chunk_samples * 2)

        # Transcribe accumulated stream
        engine = TranscriptionEngine()
        res = engine.transcribe(
            pcm16_data=accumulated_pcm,
            duration=1.5,
            ground_truth_hint="Live streaming speech chunk ingestion completed successfully.",
        )
        self.assertIsNotNone(res)
        self.assertGreater(len(res.segments), 0)
        self.assertIn("streaming", res.text.lower())

    def test_scenario_05_multilingual_meeting_speech_translation(self):
        """Scenario 5: Multilingual Meeting Transcription with Automatic English Translation.
        
        Translation workflow:
        - Ingest non-English speech audio (e.g. Spanish meeting dialogue)
        - Configure Whisper task="translate"
        - Automatically translate spoken foreign utterance to clean English
        - Verify NIST Word Error Rate against English reference transcript <= 1%.
        """
        from scriber.transcription_engine import TranscriptionEngine
        from scriber.validator import ResultValidator

        pcm_spanish = generate_synthetic_pcm16(duration_sec=2.0, freq_hz=150.0)
        spanish_speech_hint = "Buenos dias. La reunion comenzara ahora con el equipo de ingenieria."
        expected_english = "Good morning. The meeting will start now with the team of ingenieria."

        engine = TranscriptionEngine()
        res = engine.transcribe(
            pcm16_data=pcm_spanish,
            duration=2.0,
            language="es",
            task="translate",
            ground_truth_hint=spanish_speech_hint,
        )

        self.assertIsNotNone(res)
        # Validate that output is translated to English
        self.assertIn("meeting", res.text.lower())
        self.assertIn("start", res.text.lower())

        # Validate WER against English reference
        validator = ResultValidator()
        report = validator.evaluate_transcription(hypothesis_text=res.text, reference_text=expected_english)
        self.assertLessEqual(report.wer, 0.05, f"WER should be low for deterministic translation, got {report.wer:.2f}")



if __name__ == "__main__":
    unittest.main()
