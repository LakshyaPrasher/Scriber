"""Regression tests for shared-mutable-state / stale-data generalization.

These tests guard the cross-cutting state-safety contract across the whole
application, not any single file:

* A long job's ``audio_pcm16`` must never be mutated or overwritten by a
  subsequently processed short clip (concurrent/short-clip state isolation).
* ``process_file`` / ``process_pcm`` attach the exact input PCM to
  ``ScriberOutput.audio_pcm16`` and do not read shared pipeline state for
  playback.
* ``edit_audio`` must not silently fall back to a previous job's
  ``last_pcm_data``.
* Voice cloning must use the explicitly-selected speaker reference PCM, not an
  unrelated earlier job's audio, and must report ``similarity_measured=False``
  when similarity is unmeasurable.
"""

import os
import tempfile
import unittest
import wave

import numpy as np

from scriber.models import VoiceProfile
from scriber.pipeline import ScriberPipeline
from scriber.voice_clone import VoiceProfiler

SAMPLE_RATE = 16000


def _sine_pcm(duration_sec: float, frequency_hz: float, sr: int = SAMPLE_RATE) -> bytes:
    t = np.linspace(0, duration_sec, int(duration_sec * sr), endpoint=False)
    return (np.sin(2 * np.pi * frequency_hz * t) * 20000).astype(np.int16).tobytes()


class TestStateGeneralization(unittest.TestCase):
    """Shared-state / stale-data regression tests spanning pipeline + editor + cloner."""

    def setUp(self):
        self.pipeline = ScriberPipeline()

    def test_long_output_audio_pcm16_is_not_overwritten_by_short_clip_state(self):
        """Concurrent/short-clip state cannot change a long output's audio_pcm16.

        Simulates a multi-threaded server: a long job completes and attaches its
        PCM, then a short job overwrites the pipeline-global last_pcm_data. The
        long output's attached PCM must remain the long audio.
        """
        long_pcm = _sine_pcm(5.0, 220.0)
        short_pcm = _sine_pcm(0.3, 440.0)

        long_out = self.pipeline.process_pcm(
            pcm16_data=long_pcm,
            source_name="long.wav",
            ground_truth_hint="long clip reference",
        )
        # Another job overwrites the shared pipeline cursor.
        self.pipeline.last_pcm_data = short_pcm
        self.pipeline.last_file_path = "short.wav"

        self.assertEqual(long_out.audio_pcm16, long_pcm)
        self.assertEqual(len(long_out.audio_pcm16), len(long_pcm))
        self.assertNotEqual(long_out.audio_pcm16, short_pcm)
        # The shared cursor now points at the short clip, but the long output
        # is decoupled from it.
        self.assertEqual(self.pipeline.last_pcm_data, short_pcm)
        self.assertNotEqual(self.pipeline.last_pcm_data, long_out.audio_pcm16)

    def test_process_pcm_attaches_exact_input_pcm_not_shared_state(self):
        """process_pcm attaches the exact input PCM, independent of shared state."""
        pcm = _sine_pcm(2.0, 330.0)
        out = self.pipeline.process_pcm(
            pcm16_data=pcm,
            source_name="stream.wav",
            ground_truth_hint="stream reference",
        )

        self.assertEqual(out.audio_pcm16, pcm)
        self.assertEqual(out.audio_metadata.duration, len(pcm) / (SAMPLE_RATE * 2.0))
        # Mutating the shared cursor afterwards must not alter the attached PCM.
        self.pipeline.last_pcm_data = b"\x00\x00" * 10
        self.assertEqual(out.audio_pcm16, pcm)

    def test_edit_audio_raises_without_explicit_audio_no_shared_fallback(self):
        """edit_audio must not silently edit a previous job's last_pcm_data."""
        # Prime the shared cursor with one job's audio.
        self.pipeline.last_pcm_data = _sine_pcm(1.0, 220.0)

        with self.assertRaises(ValueError):
            self.pipeline.edit_audio()  # no pcm_data, no file_path

        # Supplying audio explicitly still works and is not sourced from state.
        with tempfile.TemporaryDirectory() as tmp:
            res = self.pipeline.edit_audio(pcm_data=_sine_pcm(1.0, 440.0), filename="x.mp3", output_dir=tmp)
            self.assertTrue(res["success"])
            self.assertAlmostEqual(res["duration"], 1.0, places=1)

    def test_clone_voice_uses_passed_reference_not_stale_last_pcm_data(self):
        """clone_voice uses the selected speaker's reference PCM, not an earlier job's."""
        long_pcm = _sine_pcm(1.0, 220.0)
        short_pcm = _sine_pcm(1.0, 440.0)

        # Prime shared state with an unrelated earlier job's audio.
        self.pipeline.last_pcm_data = short_pcm

        profile = VoiceProfiler.profile_from_pcm16(long_pcm, speaker_id="TargetSpeaker")
        profile_f0 = profile.fundamental_frequency_hz
        self.assertGreater(profile_f0, 0.0)

        # No reference_pcm passed -> must synthesize from the passed profile only,
        # never fall back to pipeline.last_pcm_data (the short clip).
        result = self.pipeline.clone_voice(
            profile=profile,
            text_prompt="Regression check.",
            backend="formant-harmonic-engine",
        )
        self.assertIsInstance(result.profile, VoiceProfile)
        self.assertAlmostEqual(
            result.profile.fundamental_frequency_hz,
            profile_f0,
            delta=1.0,
            msg="clone used a previous job's reference audio instead of the passed profile",
        )

        # Explicit reference_pcm is honored.
        result_ref = self.pipeline.clone_voice(
            profile=profile,
            text_prompt="Regression check.",
            reference_pcm=long_pcm,
            backend="formant-harmonic-engine",
        )
        self.assertAlmostEqual(
            result_ref.profile.fundamental_frequency_hz,
            profile_f0,
            delta=1.0,
        )

    def test_voice_profiles_are_honestly_empty_for_silence(self):
        """Silence/unvoiced audio yields empty profiles, no fabricated 130 Hz pitch."""
        silence = bytes(SAMPLE_RATE * 2)  # 1 s of zeros
        profile = VoiceProfiler.profile_from_pcm16(silence, speaker_id="Silent")
        self.assertEqual(profile.fundamental_frequency_hz, 0.0)
        self.assertEqual(profile.gender_estimate, "unmeasured")
        self.assertEqual(profile.energy_rms, 0.0)
        self.assertEqual(profile.voice_vector, [0.0] * 16)

        # A recording with no speech segments yields one honest empty profile.
        empty = self.pipeline._extract_speaker_voice_profiles(silence, [])
        self.assertEqual(len(empty), 1)
        self.assertEqual(empty[0].fundamental_frequency_hz, 0.0)
        self.assertEqual(empty[0].gender_estimate, "unmeasured")


if __name__ == "__main__":
    unittest.main()
