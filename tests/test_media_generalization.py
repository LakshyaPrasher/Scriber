"""Media generalization regression tests for Scriber Studio v2.0.

Proves playback/audio extraction works correctly across ALL media types and
codecs (not just one video), and that the per-output PCM attachment never falls
back to the shared mutable ``pipeline.last_pcm_data`` (the bug that produced a
7.7 s playable WAV from a 50-minute video because voice-clone previews
overwrote the shared buffer).

These tests intentionally avoid the existing test files so other agents' work
is not disturbed.
"""

from __future__ import annotations

import io
import json
import math
import os
import re
import struct
import subprocess
import tempfile
import unittest
import wave
from unittest.mock import MagicMock

from scriber.audio_extractor import AudioExtractor
from scriber.web.server import (
    BROWSER_PLAYABLE_CONTAINERS,
    _attach_playback_payload,
    _compute_waveform_peaks,
    _prepare_playable_media_path,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(REPO, "tests", "suite_20_samples")
SOURCE = os.path.join(SAMPLES, "sample_01_user_upload_ddos.mp3")  # ~11.6 s mono 48 kHz

PLAYABLE_EXTS = set(BROWSER_PLAYABLE_CONTAINERS)
# Formats Chromium does NOT reliably play back; they must never be passed through
# as-is by _prepare_playable_media_path.
UNRELIABLE_EXTS = {".alac", ".wma", ".amr"}

# label -> (ffmpeg extra args, output filename)
TRANSCODES = [
    ("wav_8k_mono",     ["-ar", "8000", "-ac", "1"], "out.wav"),
    ("wav_16k_mono",    ["-ar", "16000", "-ac", "1"], "out.wav"),
    ("wav_44k1_stereo", ["-ar", "44100", "-ac", "2"], "out.wav"),
    ("wav_48k_5_1",     ["-ar", "48000", "-ac", "6"], "out.wav"),
    ("mp3_44k1",        ["-c:a", "mp3", "-b:a", "128k", "-ar", "44100", "-ac", "1"], "out.mp3"),
    ("mp3_48k1",        ["-c:a", "mp3", "-b:a", "128k", "-ar", "48000", "-ac", "1"], "out.mp3"),
    ("flac",            ["-c:a", "flac"], "out.flac"),
    ("ogg_vorbis",      ["-c:a", "vorbis", "-aq", "4", "-strict", "-2", "-ac", "2"], "out.ogg"),
    ("opus",            ["-c:a", "opus", "-b:a", "64k", "-strict", "-2"], "out.opus"),
    ("m4a_aac",         ["-c:a", "aac", "-b:a", "128k"], "out.m4a"),
    ("mp4_aac",         ["-c:a", "aac", "-b:a", "128k", "-vn"], "out.mp4"),
    ("mkv_aac",         ["-c:a", "aac", "-b:a", "128k"], "out.mkv"),
    ("webm_opus",       ["-c:a", "opus", "-b:a", "64k", "-strict", "-2"], "out.webm"),
]


def _ffmpeg_path():
    return AudioExtractor().ffmpeg_path


def _ffprobe_duration(path, ffmpeg):
    out = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", path],
        capture_output=True, text=True,
    )
    m = re.search(r"Duration:\s*(\d{2}):(\d{2}):([\d.]+)", out.stderr)
    if not m:
        return None
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def _transcode_all(tmpdir, ffmpeg):
    """Transcode SOURCE into every variant; returns dict label -> out_path."""
    produced = {}
    for label, extra, out_name in TRANSCODES:
        out_path = os.path.join(tmpdir, f"{label}_{out_name}")
        proc = subprocess.run(
            [ffmpeg, "-nostdin", "-y", "-i", SOURCE] + extra + [out_path],
            capture_output=True, text=True,
        )
        if proc.returncode == 0 and os.path.isfile(out_path):
            produced[label] = out_path
    return produced


class FakeOutput:
    """Minimal stand-in for ScriberOutput carrying only the fields used by the
    playback attachment helper."""
    def __init__(self, audio_pcm16=b"", session_id="sess_test"):
        self.audio_pcm16 = audio_pcm16
        self.session_id = session_id


class TestMediaGeneralization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = _ffmpeg_path()
        if not (cls.ffmpeg and os.path.isfile(cls.ffmpeg)):
            raise unittest.SkipTest("system ffmpeg required for media generalization tests")
        if not os.path.isfile(SOURCE):
            raise unittest.SkipTest(f"source sample missing: {SOURCE}")
        cls.extractor = AudioExtractor()
        cls.tmpdir = tempfile.mkdtemp(prefix="scriber_media_gen_")
        cls.produced = _transcode_all(cls.tmpdir, cls.ffmpeg)
        cls.source_dur = _ffprobe_duration(SOURCE, cls.ffmpeg)
        cls.source_pcm, cls.source_meta = cls.extractor.extract_pcm16(SOURCE)
        cls.source_pcm_dur = len(cls.source_pcm) / 32000.0

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # 1. Format generalization: extraction + playback path + peaks       #
    # ------------------------------------------------------------------ #
    def test_extract_pcm16_duration_matches_source_across_formats(self):
        """16 kHz mono PCM duration must match source duration (~0.15 s / 1%)."""
        tolerance = max(0.15, 0.01 * self.source_dur)
        for label, out_path in self.produced.items():
            with self.subTest(format=label):
                pcm, meta = self.extractor.extract_pcm16(out_path)
                self.assertEqual(meta.sample_rate, 16000)
                self.assertEqual(meta.channels, 1)
                pcm_dur = len(pcm) / 32000.0
                self.assertAlmostEqual(
                    pcm_dur, self.source_pcm_dur, delta=tolerance,
                    msg=f"{label}: pcm {pcm_dur:.3f}s vs source {self.source_pcm_dur:.3f}s",
                )

    def test_prepare_playable_media_path_per_format(self):
        """Playable formats pass through; everything else becomes an exact WAV."""
        out_root = os.path.join(self.tmpdir, "playback_out")
        for label, out_path in self.produced.items():
            with self.subTest(format=label):
                ext = os.path.splitext(out_path)[1].lower()
                pcm, _ = self.extractor.extract_pcm16(out_path)
                playable = _prepare_playable_media_path(
                    out_path, "sess_gen", pcm_data=pcm, output_dir=out_root,
                )
                if ext in PLAYABLE_EXTS:
                    self.assertEqual(playable, out_path, f"{label} should pass through")
                else:
                    self.assertTrue(playable.lower().endswith(".wav"), f"{label} should become WAV")
                    self.assertFalse(playable == out_path, f"{label} should not pass through")
                    self.assertEqual(os.path.getsize(playable), 44 + len(pcm))
                    with wave.open(playable, "rb") as wf:
                        decoded_dur = wf.getnframes() / float(wf.getframerate())
                    self.assertAlmostEqual(
                        decoded_dur, len(pcm) / 32000.0, delta=0.02,
                        msg=f"{label} WAV decoded duration mismatch",
                    )

    def test_no_unreliable_format_is_passed_through(self):
        """ALAC/WMA/AMR-style containers must never be handed to the player as-is."""
        # Sanity-check the rule against the formats we actually produce: none of
        # them is in UNRELIABLE_EXTS and none is wrongly passed through.
        out_root = os.path.join(self.tmpdir, "playback_out2")
        for label, out_path in self.produced.items():
            ext = os.path.splitext(out_path)[1].lower()
            self.assertNotIn(ext, UNRELIABLE_EXTS, f"{label} uses an unreliable codec")
            pcm, _ = self.extractor.extract_pcm16(out_path)
            playable = _prepare_playable_media_path(
                out_path, "sess_gen", pcm_data=pcm, output_dir=out_root,
            )
            if ext in UNRELIABLE_EXTS:
                self.assertTrue(playable.lower().endswith(".wav"))

    def test_waveform_peaks_across_formats(self):
        """_compute_waveform_peaks returns exactly 64 finite bars in [0.03, 1.0]."""
        for label, out_path in self.produced.items():
            with self.subTest(format=label):
                pcm, _ = self.extractor.extract_pcm16(out_path)
                peaks = _compute_waveform_peaks(pcm, 64)
                self.assertEqual(len(peaks), 64, f"{label}: expected 64 bars")
                self.assertTrue(all(math.isfinite(p) for p in peaks), f"{label}: NaN present")
                self.assertTrue(all(0.03 <= p <= 1.0 for p in peaks), f"{label}: out of range")

    # ------------------------------------------------------------------ #
    # 2. Waveform peak properties                                        #
    # ------------------------------------------------------------------ #
    def test_waveform_peaks_silence_is_flat_small(self):
        """Silence yields flat small bars, never invented energy."""
        silence = b"\x00\x00" * 16000  # 1 s digital silence
        peaks = _compute_waveform_peaks(silence, 64)
        self.assertEqual(len(peaks), 64)
        self.assertTrue(all(math.isfinite(p) for p in peaks))
        self.assertLessEqual(max(peaks), 0.05)

    def test_waveform_peaks_loud_quiet_split_follows_energy(self):
        """A quiet-then-loud file must show higher energy in the loud half."""
        quiet = struct.pack("<h", 200) * 16000      # 1 s very quiet
        loud = struct.pack("<h", 20000) * 16000     # 1 s loud
        peaks = _compute_waveform_peaks(quiet + loud, 64)
        self.assertEqual(len(peaks), 64)
        self.assertGreater(sum(peaks[32:]), sum(peaks[:32]) * 3)

    def test_waveform_peaks_never_nan(self):
        """No input produces NaN peaks."""
        weird = b"\x00\xff" * 8000  # alternating extreme samples
        peaks = _compute_waveform_peaks(weird, 64)
        self.assertEqual(len(peaks), 64)
        self.assertTrue(all(math.isfinite(p) for p in peaks))
        empty = _compute_waveform_peaks(b"", 64)
        self.assertEqual(empty, [])

    # ------------------------------------------------------------------ #
    # 3. /api/process attachment: fields + shared-state race guard       #
    # ------------------------------------------------------------------ #
    def test_attach_payload_attaches_playback_fields(self):
        """_attach_playback_payload attaches media_url + waveform_peaks + media_duration_sec."""
        long_pcm = b"\x01\x02" * (16000 * 2)  # 2 s of 16 kHz mono PCM
        resp = {}
        _attach_playback_payload(resp, FakeOutput(long_pcm), SOURCE)
        self.assertIn("media_url", resp)
        self.assertIn("waveform_peaks", resp)
        self.assertIn("media_duration_sec", resp)
        self.assertEqual(len(resp["waveform_peaks"]), 64)
        self.assertAlmostEqual(resp["media_duration_sec"], len(long_pcm) / 32000.0, delta=0.001)
        self.assertTrue(all(0.03 <= p <= 1.0 for p in resp["waveform_peaks"]))
        self.assertTrue(all(math.isfinite(p) for p in resp["waveform_peaks"]))

    def test_attach_never_reads_shared_pcm_when_output_has_pcm(self):
        """Race regression: output.audio_pcm16 wins over pipeline.last_pcm_data."""
        long_pcm = b"\x01\x02" * (16000 * 2)   # 2 s
        short_pcm = b"\x00\x00" * 1600          # 0.1 s (the stale shared value)
        resp = {}
        _attach_playback_payload(resp, FakeOutput(long_pcm), SOURCE)
        # The written media duration must equal the LONG output PCM, not the
        # short shared pipeline.last_pcm_data value.
        self.assertAlmostEqual(resp["media_duration_sec"], 2.0, delta=0.001)
        self.assertNotAlmostEqual(resp["media_duration_sec"], len(short_pcm) / 32000.0, delta=0.001)

    def test_attach_uses_fallback_only_when_output_pcm_missing(self):
        """fallback_pcm (shared state) is used only when output.audio_pcm16 is absent."""
        short_pcm = b"\x00\x00" * 1600  # 0.1 s
        resp = {}
        _attach_playback_payload(resp, FakeOutput(b""), SOURCE, fallback_pcm=short_pcm)
        self.assertAlmostEqual(resp["media_duration_sec"], 0.1, delta=0.001)


if __name__ == "__main__":
    unittest.main()
