"""Helper utilities for Scriber E2E Test Suite."""

import io
import math
import os
import struct
import wave
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS_DIR = os.path.join(REPO_ROOT, "scriber", "assets")
MODELS_DIR = os.path.join(ASSETS_DIR, "models")
CAMPPLUS_MODEL_PATH = os.path.join(MODELS_DIR, "campplus_cn_en_common_200k.onnx")


def generate_synthetic_pcm16(
    duration_sec: float = 2.0,
    sample_rate: int = 16000,
    frequency_hz: float = 120.0,
    amplitude: float = 0.5,
    freq_hz: Optional[float] = None,
) -> bytes:
    """Generates synthetic 16-bit mono PCM audio with fundamental and harmonic overtone."""
    if freq_hz is not None:
        frequency_hz = freq_hz
    num_samples = int(duration_sec * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / float(sample_rate)
        # Smooth attack and release envelope to prevent click artifacts
        envelope = min(1.0, 10.0 * t) * min(1.0, 10.0 * (duration_sec - t))
        val = math.sin(2.0 * math.pi * frequency_hz * t) * 0.7
        val += math.sin(2.0 * math.pi * (frequency_hz * 2.0) * t) * 0.2
        val += math.sin(2.0 * math.pi * (frequency_hz * 3.0) * t) * 0.1
        sample_int = int(val * envelope * amplitude * 32767.0)
        samples.append(max(-32768, min(32767, sample_int)))
    return struct.pack(f"<{len(samples)}h", *samples)


def generate_multi_speaker_pcm16(
    turns: List[Tuple[float, float, float]],
    sample_rate: int = 16000,
) -> bytes:
    """Generates contiguous PCM16 audio containing alternating speaker turns.
    Each turn is a tuple of (pitch_hz, duration_sec, pause_sec).
    """
    chunks = []
    for pitch_hz, dur_sec, pause_sec in turns:
        # Generate speech turn
        chunks.append(generate_synthetic_pcm16(dur_sec, sample_rate, pitch_hz))
        # Generate silence pause if any
        if pause_sec > 0:
            num_silence = int(pause_sec * sample_rate)
            chunks.append(b"\x00\x00" * num_silence)
    return b"".join(chunks)


def pack_wav_container(pcm16_bytes: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Wraps raw 16-bit PCM bytes inside a standard 44-byte RIFF/WAV header."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16_bytes)
    return buf.getvalue()


class MockHTTPResponse:
    """Lightweight mock HTTP response object for mocking network calls."""

    def __init__(self, status_code: int = 200, json_data: Optional[Dict[str, Any]] = None, content: bytes = b""):
        self.status = status_code
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content or b""

    def json(self) -> Dict[str, Any]:
        return self._json_data

    def read(self) -> bytes:
        return self.content
