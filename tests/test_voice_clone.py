"""Unit and integration tests for Scriber Voice Cloning module."""

import unittest
from scriber.audio_extractor import AudioExtractor
from scriber.models import VoiceProfile
from scriber.pipeline import ScriberPipeline
from scriber.voice_clone import VoiceCloner, VoiceProfiler


class TestVoiceClone(unittest.TestCase):

    def setUp(self):
        self.extractor = AudioExtractor()
        # Generate 2 seconds of 16kHz test speech-like synthetic audio
        self.sample_pcm = self.extractor.create_synthetic_wav("Test speech signal", duration_sec=2.0)[44:]

    def test_voice_profiler_extraction(self):
        """Verifies acoustic biometric feature extraction from PCM audio."""
        profile = VoiceProfiler.profile_from_pcm16(self.sample_pcm, speaker_id="TestSpeaker_1")

        self.assertEqual(profile.speaker_id, "TestSpeaker_1")
        self.assertGreater(profile.fundamental_frequency_hz, 0.0)
        self.assertGreater(profile.spectral_centroid_hz, 0.0)
        self.assertGreater(profile.zero_crossing_rate, 0.0)
        self.assertGreater(profile.estimated_wpm, 0.0)
        self.assertIn(profile.gender_estimate, ["masculine", "feminine", "androgynous"])
        self.assertEqual(len(profile.voice_vector), 16)

    def test_voice_profiler_empty_or_silence(self):
        """Verifies safe fallback profiling on empty or zero-byte audio."""
        empty_profile = VoiceProfiler.profile_from_pcm16(b"", speaker_id="Empty")
        self.assertEqual(empty_profile.speaker_id, "Empty")
        self.assertEqual(len(empty_profile.voice_vector), 16)

    def test_voice_cloner_harmonic_synthesis(self):
        """Verifies offline harmonic formant synthesis produces valid audio and high fidelity."""
        cloner = VoiceCloner(preferred_backend="formant-harmonic-engine")
        profile = VoiceProfiler.profile_from_pcm16(self.sample_pcm, speaker_id="Speaker_Alpha")

        result = cloner.clone_voice(
            profile=profile,
            text_prompt="Scriber intelligent speech synthesis test.",
            pitch_shift_hz=5.0,
            rate_shift_pct=0.0,
        )

        self.assertGreater(len(result.audio_pcm16), 1000)
        self.assertIn(result.audio_format, ["wav", "mp3"])
        self.assertTrue(result.audio_base64.startswith("data:audio/wav;base64,"))
        self.assertGreater(result.duration, 0.5)
        # Similarity should meet the 99%+ target requirement
        self.assertGreaterEqual(result.similarity_score, 0.990)

    def test_similarity_calculation(self):
        """Verifies mathematical correctness of biometric cosine similarity."""
        p1 = VoiceProfile(
            speaker_id="S1",
            fundamental_frequency_hz=145.0,
            pitch_min_hz=120.0,
            pitch_max_hz=170.0,
            pitch_std_hz=10.0,
            spectral_centroid_hz=1600.0,
            zero_crossing_rate=0.05,
            estimated_wpm=150.0,
            energy_rms=0.15,
            gender_estimate="masculine",
            sample_duration=2.0,
            voice_vector=[0.25] * 16,
        )
        p2 = VoiceProfile(
            speaker_id="S2",
            fundamental_frequency_hz=146.0,
            pitch_min_hz=121.0,
            pitch_max_hz=171.0,
            pitch_std_hz=10.2,
            spectral_centroid_hz=1610.0,
            zero_crossing_rate=0.051,
            estimated_wpm=151.0,
            energy_rms=0.151,
            gender_estimate="masculine",
            sample_duration=2.0,
            voice_vector=[0.25] * 16,
        )

        sim = VoiceCloner.calculate_similarity(p1, p2)
        self.assertGreaterEqual(sim, 0.990)

    def test_pipeline_integration(self):
        """Verifies voice profiles are automatically extracted in ScriberPipeline."""
        pipeline = ScriberPipeline()
        output = pipeline.process_pcm(
            pcm16_data=self.sample_pcm,
            source_name="team_meeting.wav",
            reference_text="Alice will review the deployment by Friday.",
        )

        self.assertGreaterEqual(len(output.voice_profiles), 1)
        first_prof = output.voice_profiles[0]
        self.assertGreater(first_prof.fundamental_frequency_hz, 0.0)

        # Clone voice directly from pipeline
        clone_res = pipeline.clone_voice(
            profile=first_prof,
            text_prompt="Action item confirmed and completed.",
        )
        self.assertIsNotNone(clone_res)
        self.assertGreater(len(clone_res.audio_pcm16), 0)
        self.assertGreaterEqual(clone_res.similarity_score, 0.990)


if __name__ == "__main__":
    unittest.main()
