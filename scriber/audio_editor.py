"""Audio Editing, Trimming, Pitch-Shifting, Gain, and MP3 Export Engine for Scriber.
Enables high-fidelity volume gain, pitch manipulation, and non-destructive trimming
with native MP3 encoding via PyAV and standard libraries.
"""

from __future__ import annotations

import base64
import io
import math
import os
import wave
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np


class AudioEditor:
    """Provides non-destructive audio trimming, volume scaling, pitch-shifting, and MP3 generation."""

    @staticmethod
    def wsola_time_stretch(
        signal: np.ndarray,
        rate: float,
        win_size: int = 1024,
        hop: int = 256,
    ) -> np.ndarray:
        """Time-stretches a 1D audio signal by rate factor using Waveform Similarity Overlap-Add."""
        if abs(rate - 1.0) < 0.01 or len(signal) < win_size * 2:
            return signal

        out_len = int(len(signal) / rate)
        out = np.zeros(out_len + win_size, dtype=np.float32)
        norm = np.zeros(out_len + win_size, dtype=np.float32)
        window = np.hanning(win_size).astype(np.float32)

        in_pos = 0.0
        out_pos = 0
        delta_in = hop * rate

        while out_pos < out_len and int(in_pos) + win_size < len(signal):
            idx = int(in_pos)
            out[out_pos : out_pos + win_size] += signal[idx : idx + win_size] * window
            norm[out_pos : out_pos + win_size] += window
            in_pos += delta_in
            out_pos += hop

        mask = norm > 1e-4
        out[mask] /= norm[mask]
        return out[:out_len]

    @classmethod
    def pitch_shift(cls, signal: np.ndarray, semitones: float, sr: int = 16000) -> np.ndarray:
        """Shifts the pitch of a 1D audio signal by specified semitones while preserving duration."""
        if abs(semitones) < 0.05 or len(signal) < 32:
            return signal

        factor = 2.0 ** (semitones / 12.0)
        target_samples = max(16, int(len(signal) / factor))
        resampled = np.interp(
            np.linspace(0, len(signal) - 1, target_samples),
            np.arange(len(signal)),
            signal,
        )

        stretched = cls.wsola_time_stretch(resampled, 1.0 / factor)
        if len(stretched) < len(signal):
            stretched = np.pad(stretched, (0, len(signal) - len(stretched)))
        else:
            stretched = stretched[: len(signal)]
        return stretched

    @classmethod
    def edit_pcm16(
        cls,
        pcm_bytes: bytes,
        sr: int = 16000,
        volume: float = 1.0,
        pitch_semitones: float = 0.0,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None,
    ) -> Tuple[bytes, float]:
        """Edits raw 16-bit signed PCM audio bytes: trims range, shifts pitch, applies volume gain.

        Returns:
            Tuple of (edited_pcm_bytes, new_duration_seconds)
        """
        if not pcm_bytes:
            return b"", 0.0

        # Strip RIFF header if passed by mistake
        if pcm_bytes.startswith(b"RIFF") and len(pcm_bytes) > 44:
            data_idx = pcm_bytes.find(b"data")
            if data_idx != -1 and data_idx + 8 <= len(pcm_bytes):
                pcm_bytes = pcm_bytes[data_idx + 8 :]
            else:
                pcm_bytes = pcm_bytes[44:]

        # Guarantee 2-byte alignment
        if len(pcm_bytes) % 2 != 0:
            pcm_bytes = pcm_bytes[: len(pcm_bytes) - 1]

        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        total_samples = len(samples)
        if total_samples == 0:
            return b"", 0.0

        # 1. Trimming
        s_idx = max(0, int(start_sec * sr))
        e_idx = min(total_samples, int(end_sec * sr)) if (end_sec is not None and end_sec > start_sec) else total_samples
        if e_idx <= s_idx:
            e_idx = total_samples
        samples = samples[s_idx:e_idx]
        if len(samples) == 0:
            return b"", 0.0

        # 2. Pitch shifting
        if abs(pitch_semitones) >= 0.05:
            samples = cls.pitch_shift(samples, pitch_semitones, sr=sr)

        # 3. Volume Scaling
        vol_clamped = max(0.0, min(5.0, float(volume)))
        samples = samples * vol_clamped

        # Clip back to 16-bit PCM range
        final_samples = np.clip(samples, -32768, 32767).astype(np.int16)
        edited_bytes = final_samples.tobytes()
        duration_sec = len(final_samples) / float(sr)
        return edited_bytes, duration_sec

    @staticmethod
    def encode_mp3(
        pcm_bytes: bytes,
        sr: int = 16000,
        channels: int = 1,
        bit_rate: int = 192000,
    ) -> bytes:
        """Encodes raw 16-bit PCM into an MP3 byte buffer using PyAV (or WAV fallback)."""
        if not pcm_bytes:
            return b""

        # Guarantee 2-byte alignment
        if len(pcm_bytes) % 2 != 0:
            pcm_bytes = pcm_bytes[: len(pcm_bytes) - 1]

        try:
            import av

            samples = np.frombuffer(pcm_bytes, dtype=np.int16)
            layout = "stereo" if channels == 2 else "mono"
            out_buf = io.BytesIO()
            container = av.open(out_buf, mode="w", format="mp3")
            stream = container.add_stream("mp3", rate=sr)
            stream.bit_rate = bit_rate

            frame_samples = 1152
            frame_total = frame_samples * channels
            for i in range(0, len(samples), frame_total):
                chunk = samples[i : i + frame_total]
                if len(chunk) < frame_total:
                    chunk = np.pad(chunk, (0, frame_total - len(chunk)))
                frame = av.AudioFrame.from_ndarray(chunk.reshape(1, -1), format="s16", layout=layout)
                frame.sample_rate = sr
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
            container.close()
            return out_buf.getvalue()
        except Exception:
            # Fallback to standard WAV format
            out_buf = io.BytesIO()
            with wave.open(out_buf, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(pcm_bytes)
            return out_buf.getvalue()

    @classmethod
    def process_and_export(
        cls,
        pcm_data: bytes,
        sr: int = 16000,
        volume: float = 1.0,
        pitch_semitones: float = 0.0,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None,
        filename: Optional[str] = None,
        output_dir: Optional[str] = "./scriber_output",
    ) -> Dict[str, Any]:
        """Edits PCM audio with volume, pitch, and trimming, then exports to an MP3 file and base64."""
        edited_pcm, duration = cls.edit_pcm16(
            pcm_bytes=pcm_data,
            sr=sr,
            volume=volume,
            pitch_semitones=pitch_semitones,
            start_sec=start_sec,
            end_sec=end_sec,
        )

        mp3_bytes = cls.encode_mp3(edited_pcm, sr=sr, channels=1, bit_rate=192000)

        # Base64 data URI for direct web playback & download
        base64_str = base64.b64encode(mp3_bytes).decode("ascii")
        data_uri = f"data:audio/mp3;base64,{base64_str}"

        clean_name = filename or "scriber_edited_audio.mp3"
        if not clean_name.lower().endswith(".mp3"):
            clean_name += ".mp3"

        saved_path = None
        if output_dir:
            try:
                os.makedirs(output_dir, exist_ok=True)
                target = os.path.join(output_dir, clean_name)
                with open(target, "wb") as f:
                    f.write(mp3_bytes)
                saved_path = os.path.abspath(target)
            except Exception:
                pass

        return {
            "success": True,
            "filename": clean_name,
            "duration": round(duration, 3),
            "size_bytes": len(mp3_bytes),
            "audio_base64": data_uri,
            "saved_path": saved_path,
            "settings": {
                "volume": volume,
                "pitch_semitones": pitch_semitones,
                "start_sec": start_sec,
                "end_sec": end_sec,
            },
        }
