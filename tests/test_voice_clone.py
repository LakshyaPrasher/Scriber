"""Unit and integration tests for Scriber Voice Cloning module."""

import os
import unittest
import numpy as np

from scriber.audio_extractor import AudioExtractor
from scriber.models import VoiceProfile
from scriber.pipeline import ScriberPipeline
from scriber.voice_clone import VoiceCloner, VoiceProfiler


class TestVoiceClone(unittest.TestCase):

    def setUp(self):
        self.extractor = AudioExtractor()
        # Generate 2 seconds of 16kHz test speech-like synthetic audio
        self.sample_pcm = self.extractor.create_synthetic_wav("Test speech signal", duration_sec=2.0)[44:]
        self.user_mp3_path = "tests/suite_20_samples/sample_01_user_upload_ddos.mp3"

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
        self.assertGreater(len(profile.formants), 0)
        self.assertIsInstance(profile.hnr_db, float)
        self.assertIsInstance(profile.spectral_tilt, float)
        self.assertGreater(profile.pitch_stability, 0.0)
        self.assertIsInstance(profile.voice_timbre_label, str)
        self.assertIsInstance(profile.recommended_voice, str)

    def test_voice_profiler_empty_or_silence(self):
        """Verifies safe fallback profiling on empty or zero-byte audio."""
        empty_profile = VoiceProfiler.profile_from_pcm16(b"", speaker_id="Empty")
        self.assertEqual(empty_profile.speaker_id, "Empty")
        self.assertEqual(len(empty_profile.voice_vector), 16)
        self.assertEqual(len(empty_profile.formants), 3)

    def test_deep_acoustic_analysis_user_upload(self):
        """Verifies deep acoustic analysis (pitch/F0, formants, HNR, tilt, RMS) on real uploaded MP3."""
        if not os.path.exists(self.user_mp3_path):
            self.skipTest("User upload sample MP3 not present on disk")

        pcm, meta = self.extractor.extract_pcm16(self.user_mp3_path)
        prof = VoiceProfiler.profile_from_pcm16(pcm, speaker_id="User_DDoS_Speaker")

        # 1. Pitch / F0: user audio is a deep male speaker (100 - 125 Hz)
        self.assertGreaterEqual(prof.fundamental_frequency_hz, 95.0)
        self.assertLessEqual(prof.fundamental_frequency_hz, 128.0)
        self.assertEqual(prof.gender_estimate, "masculine")

        # 2. Formants: F1 (300-600Hz), F2 (1400-2000Hz), F3 (2500-3200Hz)
        self.assertEqual(len(prof.formants), 3)
        self.assertGreaterEqual(prof.formants[0], 300.0)
        self.assertLessEqual(prof.formants[0], 650.0)
        self.assertGreaterEqual(prof.formants[1], 1400.0)
        self.assertLessEqual(prof.formants[1], 2100.0)

        # 3. Spectral Tilt & Centroid: warm baritone rolloff
        self.assertLess(prof.spectral_tilt, 0.0)  # Negative slope indicates natural warm glottal rolloff
        self.assertGreaterEqual(prof.spectral_centroid_hz, 700.0)
        self.assertLessEqual(prof.spectral_centroid_hz, 1400.0)

        # 4. HNR & Energy RMS
        self.assertGreater(prof.hnr_db, 0.0)
        self.assertGreater(prof.energy_rms, 0.08)

        # 5. Timbre categorization & Recommended neural voice
        self.assertIn("Baritone", prof.voice_timbre_label)
        self.assertEqual(prof.recommended_voice, "en-US-ChristopherNeural")

    def test_voice_cloner_neural_timbre_cloning(self):
        """Verifies neural voice cloning closely matches the timbre and vocal characteristics of source audio."""
        if not os.path.exists(self.user_mp3_path):
            self.skipTest("User upload sample MP3 not present on disk")

        pcm, meta = self.extractor.extract_pcm16(self.user_mp3_path)
        ref_prof = VoiceProfiler.profile_from_pcm16(pcm, speaker_id="Source_Speaker")

        cloner = VoiceCloner()
        prompt = "The attackers are now targeting Steinmetz with distributed denial of service queries."
        result = cloner.clone_voice(
            profile=ref_prof,
            text_prompt=prompt,
            reference_pcm=pcm,
            backend="edge-neural",
            output_format="mp3",
        )

        self.assertIsNotNone(result.audio_pcm16)
        self.assertGreater(len(result.audio_pcm16), 16000)
        self.assertGreaterEqual(result.similarity_score, 0.990)
        self.assertEqual(result.audio_format, "mp3")
        self.assertIn("edge-tts-neural", result.synthesis_backend)

        # Verify acoustic characteristics of synthesized audio
        synth_prof = VoiceProfiler.profile_from_pcm16(result.audio_pcm16, speaker_id="Cloned_Speaker")

        # F0 should closely match reference within 8 Hz
        f0_delta = abs(ref_prof.fundamental_frequency_hz - synth_prof.fundamental_frequency_hz)
        self.assertLessEqual(f0_delta, 8.0, f"F0 mismatch: Ref={ref_prof.fundamental_frequency_hz}, Synth={synth_prof.fundamental_frequency_hz}")

        # Active speech RMS energy should be normalized and closely aligned
        rms_ratio = synth_prof.energy_rms / max(0.01, ref_prof.energy_rms)
        self.assertGreaterEqual(rms_ratio, 0.70)
        self.assertLessEqual(rms_ratio, 1.35)

        # Gender should remain masculine
        self.assertEqual(synth_prof.gender_estimate, "masculine")

    def test_voice_cloner_biquad_harmonic_synthesis(self):
        """Verifies offline biquad IIR harmonic formant vocoder produces stable audio and matches F0."""
        cloner = VoiceCloner(preferred_backend="formant-harmonic-engine")
        profile = VoiceProfiler.profile_from_pcm16(self.sample_pcm, speaker_id="Speaker_Alpha")

        result = cloner.clone_voice(
            profile=profile,
            text_prompt="Scriber intelligent speech synthesis test.",
            pitch_shift_hz=0.0,
            rate_shift_pct=0.0,
            backend="gpt-sovits",
        )

        self.assertGreater(len(result.audio_pcm16), 1000)
        self.assertIn(result.audio_format, ["wav", "mp3"])
        self.assertTrue(result.audio_base64.startswith("data:audio/wav;base64,"))
        self.assertGreater(result.duration, 0.5)
        self.assertGreaterEqual(result.similarity_score, 0.990)

        # Verify synthesized audio pitch conforms to profile F0
        synth_p = VoiceProfiler.profile_from_pcm16(result.audio_pcm16)
        f0_diff = abs(profile.fundamental_frequency_hz - synth_p.fundamental_frequency_hz)
        self.assertLessEqual(f0_diff, 15.0)

    def test_mel_filterbank_timbre_transfer_and_rms_normalization(self):
        """Verifies Mel-filterbank timbre transfer and RMS energy normalization without clipping."""
        # Create a test synthetic source and reference
        sr = 16000
        t = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
        ref_signal = ((0.4 * np.sin(2 * np.pi * 115 * t) + 0.2 * np.sin(2 * np.pi * 230 * t)) * 32767).astype(np.int16).tobytes()
        syn_signal = ((0.3 * np.sin(2 * np.pi * 125 * t) + 0.1 * np.sin(2 * np.pi * 250 * t)) * 32767).astype(np.int16).tobytes()

        filtered_pcm = VoiceCloner._apply_timbre_transfer(syn_signal, ref_signal, sr=sr)
        self.assertGreater(len(filtered_pcm), 0)
        self.assertEqual(len(filtered_pcm), len(syn_signal))

        # Ensure no clipping in output
        filtered_arr = np.frombuffer(filtered_pcm, dtype=np.int16)
        self.assertLessEqual(np.max(np.abs(filtered_arr)), 32767)

    def test_similarity_calculation_calibration_and_discrimination(self):
        """Verifies mathematical correctness of biometric similarity: high for match, lower for divergent voices."""
        # Matching / close profiles
        p_male1 = VoiceProfile(
            speaker_id="M1",
            fundamental_frequency_hz=115.0,
            pitch_min_hz=90.0,
            pitch_max_hz=150.0,
            pitch_std_hz=10.0,
            spectral_centroid_hz=1050.0,
            zero_crossing_rate=0.15,
            estimated_wpm=130.0,
            energy_rms=0.14,
            gender_estimate="masculine",
            sample_duration=3.0,
            voice_vector=[0.25] * 16,
            formants=[440.0, 1720.0, 2800.0],
            spectral_tilt=-7.0,
        )
        p_male2 = VoiceProfile(
            speaker_id="M2",
            fundamental_frequency_hz=113.0,
            pitch_min_hz=88.0,
            pitch_max_hz=148.0,
            pitch_std_hz=9.8,
            spectral_centroid_hz=1020.0,
            zero_crossing_rate=0.152,
            estimated_wpm=128.0,
            energy_rms=0.138,
            gender_estimate="masculine",
            sample_duration=3.0,
            voice_vector=[0.25] * 16,
            formants=[435.0, 1710.0, 2810.0],
            spectral_tilt=-7.2,
        )

        match_sim = VoiceCloner.calculate_similarity(p_male1, p_male2)
        self.assertGreaterEqual(match_sim, 0.990)

        # Mismatched female profile with high pitch and bright centroid
        p_female = VoiceProfile(
            speaker_id="F1",
            fundamental_frequency_hz=215.0,
            pitch_min_hz=180.0,
            pitch_max_hz=260.0,
            pitch_std_hz=22.0,
            spectral_centroid_hz=2100.0,
            zero_crossing_rate=0.25,
            estimated_wpm=170.0,
            energy_rms=0.08,
            gender_estimate="feminine",
            sample_duration=3.0,
            voice_vector=[-0.25] * 16,
            formants=[750.0, 2300.0, 3400.0],
            spectral_tilt=-3.0,
        )

        divergent_sim = VoiceCloner.calculate_similarity(p_male1, p_female)
        self.assertLess(divergent_sim, match_sim)
        self.assertLessEqual(divergent_sim, 0.550, f"Cross-gender similarity should be heavily penalized, got {divergent_sim}")

    def test_deep_acoustic_analysis_female_speech(self):
        """Verifies deep acoustic analysis accurately profiles female vocal characteristics without octave halving."""
        female_path = "tests/suite_20_samples/sample_04_single_spk_calm_female_turn_0_en-US-JennyNeural.mp3"
        if not os.path.exists(female_path):
            self.skipTest("Female speech sample not present on disk")

        pcm, meta = self.extractor.extract_pcm16(female_path)
        prof = VoiceProfiler.profile_from_pcm16(pcm, speaker_id="Jenny_Female")

        # Female pitch F0 should be around 170-195 Hz (NOT halved to 115 Hz)
        self.assertGreaterEqual(prof.fundamental_frequency_hz, 168.0)
        self.assertLessEqual(prof.fundamental_frequency_hz, 205.0)
        self.assertEqual(prof.gender_estimate, "feminine")
        self.assertEqual(prof.recommended_voice, "en-US-JennyNeural")
        self.assertIn("Alto", prof.voice_timbre_label)

    def test_frequency_sweep_pitch_accuracy(self):
        """Verifies normalized pitch tracking accuracy across the full human vocal frequency spectrum."""
        sr = 16000
        test_frequencies = [85, 111, 150, 180, 220, 260]
        for target_hz in test_frequencies:
            t = np.linspace(0, 1.0, sr, endpoint=False)
            sig = (0.6 * np.sin(2 * np.pi * target_hz * t) + 0.3 * np.sin(4 * np.pi * target_hz * t)).astype(np.float32)
            f0_med, _, _, _ = VoiceProfiler._extract_pitch_contour(sig, sr)
            err = abs(target_hz - f0_med)
            self.assertLessEqual(err, 2.5, f"Pitch tracking error too high for {target_hz} Hz: got {f0_med:.2f} Hz")

    def test_timbre_transfer_boundary_and_short_audio(self):
        """Verifies _apply_timbre_transfer does not silence short audio (< 1024 samples) and preserves signal tail."""
        sr = 16000
        # 1. Short audio (800 samples = 50ms)
        sig800 = (np.sin(2 * np.pi * 200 * np.linspace(0, 0.05, 800)) * 10000).astype(np.int16).tobytes()
        out800 = VoiceCloner._apply_timbre_transfer(sig800, sig800, sr=sr)
        arr800 = np.frombuffer(out800, dtype=np.int16)
        self.assertGreater(len(arr800), 0)
        self.assertGreater(np.max(np.abs(arr800)), 1000, "Short audio must not be reduced to digital silence")

        # 2. Normal audio tail preservation (no truncated zeroes at the end)
        sig16k = (np.sin(2 * np.pi * 200 * np.linspace(0, 1.0, sr)) * 10000).astype(np.int16).tobytes()
        out16k = VoiceCloner._apply_timbre_transfer(sig16k, sig16k, sr=sr)
        arr16k = np.frombuffer(out16k, dtype=np.int16)
        self.assertGreater(np.max(np.abs(arr16k[-128:])), 100, "Audio tail must not be truncated to zeros")

    def test_voice_profile_from_dict_preserves_all_features(self):
        """Verifies VoiceProfile.from_dict preserves formants, tilt, HNR, and recommended voice."""
        data = {
            "speaker_id": "Speaker_Test",
            "fundamental_frequency_hz": 115.5,
            "spectral_centroid_hz": 1050.0,
            "energy_rms": 0.14,
            "gender_estimate": "masculine",
            "formants": [440.0, 1720.0, 2830.0],
            "hnr_db": 12.5,
            "spectral_tilt": -7.2,
            "pitch_stability": 0.98,
            "voice_timbre_label": "Deep Baritone (Warm Resonant)",
            "recommended_voice": "en-US-ChristopherNeural",
        }
        prof = VoiceProfile.from_dict(data)
        self.assertEqual(prof.speaker_id, "Speaker_Test")
        self.assertEqual(prof.fundamental_frequency_hz, 115.5)
        self.assertEqual(prof.formants, [440.0, 1720.0, 2830.0])
        self.assertEqual(prof.hnr_db, 12.5)
        self.assertEqual(prof.spectral_tilt, -7.2)
        self.assertEqual(prof.recommended_voice, "en-US-ChristopherNeural")

    def test_pipeline_integration(self):
        """Verifies voice profiles are automatically extracted and cloned in ScriberPipeline."""
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
