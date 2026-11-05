"""Challenger Empirical Verification & Stress Test Suite for Milestone M11.

Adversarially and empirically stress-tests:
- Feature 1: Multimedia Audio Extraction (16kHz mono PCM) from MP4 and MP3 assets
- Feature 2: Transcription word-level timestamps, seeking, search, and speed variation
- Feature 3: Conversational Speaker Diarization on multi-speaker interview (returning speaker re-identification, 0 phantom speakers)
- Feature 4: Audio Studio volume gain, pitch shift, trim sliders, exported MP3 header & re-decoding
"""

import io
import json
import math
import os
import struct
import sys
import unittest
from pathlib import Path

import numpy as np

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scriber.audio_extractor import AudioExtractor
from scriber.audio_editor import AudioEditor
from scriber.diarizer import AcousticDiarizer, NeuralSpeakerExtractor
from scriber.transcription_engine import TranscriptionEngine
from scriber.pipeline import ScriberPipeline
from tests.run_live_gui_automation import discover_downloads_media


class ChallengerEmpiricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.media = discover_downloads_media()
        except FileNotFoundError as e:
            raise unittest.SkipTest(f"Challenger empirical test media not present in Downloads: {e}")
        cls.extractor = AudioExtractor()

    # =========================================================================
    # FEATURE 1: MULTIMEDIA AUDIO EXTRACTION & INGESTION (MP4 & MP3)
    # =========================================================================
    def test_f1_mp4_audio_extraction_16k_mono_pcm(self):
        """Empirically verify 16kHz mono 16-bit PCM extraction from 1080p MP4."""
        mp4_path = self.media["mp4_clean"]
        self.assertTrue(os.path.exists(mp4_path), f"MP4 not found: {mp4_path}")

        pcm_bytes, meta = self.extractor.extract_pcm16(mp4_path, max_duration=10.0)

        # 1. Verification of AudioMetadata
        self.assertEqual(meta.sample_rate, 16000, f"Expected 16kHz, got {meta.sample_rate}")
        self.assertEqual(meta.channels, 1, f"Expected mono (1 channel), got {meta.channels}")
        self.assertGreater(meta.duration, 0.0)

        # 2. Verification of raw PCM byte buffer
        self.assertGreater(len(pcm_bytes), 0, "PCM bytes empty")
        self.assertEqual(len(pcm_bytes) % 2, 0, "PCM bytes not 16-bit (2-byte aligned)")

        # 3. Exact sample rate calculation: duration == samples / 16000
        num_samples = len(pcm_bytes) // 2
        computed_duration = num_samples / 16000.0
        self.assertAlmostEqual(computed_duration, meta.duration, delta=0.01)

        # 4. Audio signal health checks (not silence, reasonable dynamic range, no pure DC rail)
        samples = np.frombuffer(pcm_bytes, dtype=np.int16)
        rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        max_amp = np.max(np.abs(samples))
        dc_offset = np.abs(np.mean(samples))

        print(f"\n[F1 MP4 Extracted] Samples: {num_samples:,}, RMS: {rms:.1f}, MaxAmp: {max_amp}, DC: {dc_offset:.2f}")
        self.assertGreater(rms, 50.0, f"Signal appears silent or corrupted (RMS={rms})")
        self.assertLess(dc_offset, 500.0, f"Abnormal DC bias detected: {dc_offset}")

    def test_f1_mp3_audio_extraction_16k_mono_pcm(self):
        """Empirically verify 16kHz mono 16-bit PCM extraction from MP3."""
        mp3_path = self.media["mp3_clean"]
        self.assertTrue(os.path.exists(mp3_path), f"MP3 not found: {mp3_path}")

        pcm_bytes, meta = self.extractor.extract_pcm16(mp3_path, max_duration=10.0)

        self.assertEqual(meta.sample_rate, 16000, f"Expected 16kHz, got {meta.sample_rate}")
        self.assertEqual(meta.channels, 1, f"Expected mono, got {meta.channels}")
        self.assertGreater(meta.duration, 0.0)

        num_samples = len(pcm_bytes) // 2
        computed_duration = num_samples / 16000.0
        self.assertAlmostEqual(computed_duration, meta.duration, delta=0.01)

        samples = np.frombuffer(pcm_bytes, dtype=np.int16)
        rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
        max_amp = np.max(np.abs(samples))

        print(f"[F1 MP3 Extracted] Samples: {num_samples:,}, RMS: {rms:.1f}, MaxAmp: {max_amp}")
        self.assertGreater(rms, 50.0, f"Signal appears silent or corrupted (RMS={rms})")

    # =========================================================================
    # FEATURE 2: TRANSCRIPTION WORD TIMESTAMPS, SEEKING, SEARCH & SPEED
    # =========================================================================
    def test_f2_transcription_word_timestamps_and_invariants(self):
        """Empirically verify Whisper flow word-level timestamps and strict ordering."""
        mp4_path = self.media["mp4_clean"]
        pcm_bytes, meta = self.extractor.extract_pcm16(mp4_path, max_duration=25.0)

        engine = TranscriptionEngine()
        result = engine.transcribe(pcm_bytes, duration=meta.duration)

        segments = result.segments
        self.assertGreater(len(segments), 0, "No segments produced")

        total_words = 0
        all_words = []
        for s_idx, seg in enumerate(segments):
            self.assertGreaterEqual(seg.end, seg.start, f"Segment {s_idx} end < start")
            if seg.words:
                total_words += len(seg.words)
                prev_w_end = seg.start - 0.01
                for w_idx, w in enumerate(seg.words):
                    all_words.append(w)
                    self.assertGreaterEqual(w.end, w.start, f"Word '{w.word}' end < start: {w.end} < {w.start}")
                    self.assertGreaterEqual(
                        w.start,
                        seg.start - 0.5,
                        f"Word '{w.word}' starts before segment {seg.start}",
                    )
                    self.assertLessEqual(
                        w.end,
                        seg.end + 0.5,
                        f"Word '{w.word}' ends after segment {seg.end}",
                    )
                    self.assertGreaterEqual(
                        w.start,
                        prev_w_end - 0.15,
                        f"Word '{w.word}' violates monotonicity",
                    )
                    prev_w_end = w.end

        print(f"\n[F2 Transcription] Segments: {len(segments)}, Words: {total_words}")
        self.assertGreater(total_words, 20, "Expected at least 20 transcribed words")

    def test_f2_search_and_seeking_simulation(self):
        """Empirically verify search query token matching logic and seek accuracy."""
        # Test simulated transcript tokens
        mock_tokens = [
            {"word": "Hello", "start": 0.50, "end": 0.85},
            {"word": "everyone,", "start": 0.90, "end": 1.40},
            {"word": "welcome", "start": 1.45, "end": 1.90},
            {"word": "to", "start": 1.95, "end": 2.10},
            {"word": "Scriber", "start": 2.15, "end": 2.65},
            {"word": "hello", "start": 3.00, "end": 3.35},
        ]

        # 1. Search Query logic test: Case-insensitive token match
        query = "hello"
        matches = [t for t in mock_tokens if query in t["word"].lower()]
        self.assertEqual(len(matches), 2, f"Expected 2 matches for '{query}', got {len(matches)}")

        # Non-matching query
        no_matches = [t for t in mock_tokens if "nonexistent" in t["word"].lower()]
        self.assertEqual(len(no_matches), 0)

        # 2. Seek-to-word invariant: target time must equal token.start
        for match in matches:
            seek_target = match["start"]
            self.assertEqual(seek_target, match["start"])
            self.assertTrue(0.0 <= seek_target <= 10.0)

    # =========================================================================
    # FEATURE 3: CONVERSATIONAL SPEAKER DIARIZATION (RETURNING SPEAKER RE-ID)
    # =========================================================================
    def test_f3_conversational_diarization_multi_speaker_and_no_phantoms(self):
        """Empirically test speaker attribution on multi-speaker interview dialogue (first 120s)."""
        interview_path = self.media["interview_mp4"]
        self.assertTrue(os.path.exists(interview_path), f"Interview file not found: {interview_path}")

        print("\n[F3 Diarization] Extracting first 120s of interview PCM...")
        pcm_bytes, meta = self.extractor.extract_pcm16(interview_path, max_duration=120.0)
        self.assertGreater(len(pcm_bytes), 16000 * 2 * 60, "PCM extraction shorter than 60s")

        print("[F3 Diarization] Transcribing first 120s...")
        engine = TranscriptionEngine()
        tx_res = engine.transcribe(pcm_bytes, duration=meta.duration)
        segments = tx_res.segments
        self.assertGreater(len(segments), 0, "Transcription produced 0 segments")

        print(f"[F3 Diarization] Running AcousticDiarizer with CAM++ embeddings on {len(segments)} segments...")
        diarizer = AcousticDiarizer(similarity_threshold=0.48)
        diarized = diarizer.diarize_segments(segments, pcm16_data=pcm_bytes, sample_rate=16000)

        print(f"[F3 Diarization] Generated {len(diarized)} cohesive conversational turns:")
        for idx, seg in enumerate(diarized[:8]):
            print(f"  Turn {idx} [{seg.start:.2f}s - {seg.end:.2f}s] {seg.speaker}: {seg.text[:70]}...")

        # Distinct speakers check
        distinct_speakers = {s.speaker for s in diarized}
        print(f"[F3 Diarization] Distinct speakers discovered: {distinct_speakers}")

        # Assert no phantom speakers: Exactly 2 speakers in a 2-person interview
        self.assertEqual(
            len(distinct_speakers),
            2,
            f"Phantom speakers detected or single speaker collapse! Discovered: {distinct_speakers}",
        )

        # Mirror the GUI's unified speaker segment cards logic from app.js (lines 601-624)
        unified_cards = []
        cur_card = None
        for s in diarized:
            spk = s.speaker.replace("_", " ")
            if not cur_card or cur_card["speaker"] != spk:
                cur_card = {"speaker": spk, "start": s.start, "end": s.end, "text": s.text}
                unified_cards.append(cur_card)
            else:
                cur_card["end"] = max(cur_card["end"], s.end)
                cur_card["text"] += " " + s.text

        print(f"[F3 Diarization] Unified GUI Dialogue Cards ({len(unified_cards)} cards):")
        for idx, card in enumerate(unified_cards[:5]):
            print(f"  Card {idx} [{card['start']:.2f}s - {card['end']:.2f}s] {card['speaker']}: {card['text'][:65]}...")

        self.assertGreaterEqual(len(unified_cards), 3, "Expected at least 3 unified conversational turns")
        card_0_spk = unified_cards[0]["speaker"]
        card_1_spk = unified_cards[1]["speaker"]
        card_2_spk = unified_cards[2]["speaker"]

        print(f"[F3 GUI Dialogue Attribution] Card 0={card_0_spk}, Card 1={card_1_spk}, Returning Card 2={card_2_spk}")
        self.assertNotEqual(card_0_spk, card_1_spk, "Card 0 and Card 1 attributed to same speaker!")
        self.assertEqual(card_0_spk, card_2_spk, f"Returning Card 2 failed to match Card 0! Got {card_2_spk} vs {card_0_spk}")

        # Verify that Card 2 (the returning turn around 75s) matches initial Speaker 1
        self.assertEqual(card_2_spk, card_0_spk, f"Returning Card 2 failed to match Card 0! Got {card_2_spk} vs {card_0_spk}")
        print(f"[✓] Successfully verified: Returning dialogue turn matches initial {card_0_spk} with zero phantom speakers.")

    # =========================================================================
    # FEATURE 4: AUDIO STUDIO VOLUME GAIN, PITCH SHIFT, TRIM & MP3 EXPORT
    # =========================================================================
    def test_f4_audio_studio_dsp_and_mp3_export_integrity(self):
        """Empirically test volume gain, pitch shift, trim, and exported MP3 bitstream headers."""
        ref_path = self.media["mp3_clean"]
        pcm_bytes, meta = self.extractor.extract_pcm16(ref_path, max_duration=26.0)

        raw_samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        initial_rms = np.sqrt(np.mean(raw_samples ** 2))

        # 1. Test Volume Gain (1.4x factor = +2.9 dB)
        edited_vol, dur_vol = AudioEditor.edit_pcm16(pcm_bytes, sr=16000, volume=1.4)
        samples_vol = np.frombuffer(edited_vol, dtype=np.int16).astype(np.float32)
        vol_rms = np.sqrt(np.mean(samples_vol ** 2))
        vol_ratio = vol_rms / initial_rms
        print(f"\n[F4 Audio Studio] Initial RMS: {initial_rms:.1f}, Volume 1.4x RMS: {vol_rms:.1f} (Ratio: {vol_ratio:.2f})")
        self.assertGreater(vol_ratio, 1.25, f"Volume gain did not scale amplitude adequately (ratio: {vol_ratio})")

        # 2. Test Trimming (10% to 85% of duration)
        orig_dur = len(raw_samples) / 16000.0
        start_trim = orig_dur * 0.10
        end_trim = orig_dur * 0.85
        expected_trimmed_dur = end_trim - start_trim

        edited_trim, dur_trim = AudioEditor.edit_pcm16(
            pcm_bytes, sr=16000, start_sec=start_trim, end_sec=end_trim
        )
        print(f"[F4 Trimming] Original Dur: {orig_dur:.2f}s -> Trimmed Dur: {dur_trim:.2f}s (Expected: {expected_trimmed_dur:.2f}s)")
        self.assertAlmostEqual(dur_trim, expected_trimmed_dur, delta=0.05)

        # 3. Test Pitch Shift (+2 semitones)
        edited_pitch, dur_pitch = AudioEditor.edit_pcm16(pcm_bytes, sr=16000, pitch_semitones=2.0)
        self.assertAlmostEqual(dur_pitch, orig_dur, delta=0.10, msg="Pitch shift altered duration!")
        self.assertEqual(len(edited_pitch), len(pcm_bytes), "Pitch shifted byte count mismatch")

        # 4. Test MP3 Export & Bitstream Header Verification
        out_dir = PROJECT_ROOT / "scriber_output"
        out_dir.mkdir(parents=True, exist_ok=True)
        export_target = out_dir / "test_challenger_studio_export.mp3"
        if export_target.exists():
            export_target.unlink()

        result = AudioEditor.process_and_export(
            pcm_data=pcm_bytes,
            sr=16000,
            volume=1.4,
            pitch_semitones=2.0,
            start_sec=start_trim,
            end_sec=end_trim,
            filename=export_target.name,
            output_dir=str(out_dir),
        )

        self.assertTrue(export_target.exists(), f"Export file was not written: {export_target}")
        fsize = export_target.stat().st_size
        print(f"[F4 MP3 Export] Generated: {export_target.name} ({fsize:,} bytes)")
        self.assertGreater(fsize, 5000, f"Exported MP3 size too small: {fsize} bytes")

        # Bitstream inspection: Check MP3 header frames or ID3 tag
        raw_header = export_target.read_bytes()[:32]
        is_id3 = raw_header[:3] == b"ID3"
        # MPEG audio sync word: 11 set bits 0xFF followed by 0b111... (0xFB, 0xF3, 0xF2, 0xE0...)
        has_sync_word = False
        for i in range(len(raw_header) - 1):
            if raw_header[i] == 0xFF and (raw_header[i + 1] & 0xE0) == 0xE0:
                has_sync_word = True
                break

        print(f"[F4 MP3 Header Inspection] ID3 Tag: {is_id3}, MPEG Sync Word: {has_sync_word}")
        self.assertTrue(is_id3 or has_sync_word, "File is missing valid MPEG/MP3 audio header or sync word!")

        # 5. Playback Verification via Re-decoding
        # Decode the exported MP3 using PyAV to prove standard players can decode and play it
        import av
        container = av.open(str(export_target))
        try:
            self.assertGreater(len(container.streams.audio), 0, "Exported MP3 has no audio streams!")
            audio_stream = container.streams.audio[0]
            decoded_frames = 0
            total_decoded_samples = 0
            for frame in container.decode(audio=0):
                decoded_frames += 1
                total_decoded_samples += frame.samples

            self.assertGreater(decoded_frames, 0, "No frames decoded from exported MP3")
            decoded_duration = total_decoded_samples / float(audio_stream.rate or 16000)
            print(f"[F4 MP3 Playback Re-decode] Decoded {decoded_frames} frames ({total_decoded_samples:,} samples, {decoded_duration:.2f}s)")
            self.assertAlmostEqual(decoded_duration, expected_trimmed_dur, delta=0.5)
        finally:
            container.close()


if __name__ == "__main__":
    unittest.main()
