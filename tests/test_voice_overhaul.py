"""Comprehensive test suite for Voice Cloning Overhaul & Cloud Connectors (Milestone 4).

Covers:
1. Local GPU Companion Microservice Daemon lifecycle & RPC contracts (F5-TTS Flow-Matching 48kHz).
2. Voicemaker.in Cloud Studio REST connector (48kHz Neural synthesis).
3. ElevenLabs Cloud Studio REST connector (Instant Voice Clone, SHA-256 caching, pcm_48000).
4. 4-Tier Fallback Matrix (Tier 1 GPU -> Tier 2 Cloud -> Tier 3 Edge-TTS -> Tier 4 Offline Vocoder).
5. 48kHz Dual-Rate Audio validity, resampling, and biometric similarity calibration.
6. Web server credentials endpoints (/api/voice/credentials) and /api/clone-voice synthesis.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import struct
import unittest
from unittest.mock import MagicMock, patch
import wave

import numpy as np

from scriber.audio_editor import AudioEditor
from scriber.audio_extractor import AudioExtractor
from scriber.hardware import HardwareCapabilities
from scriber.models import VoiceCloneResult, VoiceProfile
from scriber.services.voice_microservice import (
    NeuralFlowMatchingEngine,
    VoiceMicroserviceHandler,
    VoiceMicroserviceServer,
    _pcm16_to_wav,
)
from scriber.voice_clone import (
    ElevenLabsConnector,
    VoiceCloner,
    VoiceMicroserviceManager,
    VoiceProfiler,
    VoicemakerConnector,
)
from scriber.web.server import ScriberHTTPRequestHandler


def _generate_synthetic_pcm(duration_sec: float = 1.0, sample_rate: int = 48000, f0: float = 150.0) -> bytes:
    """Generates synthetic harmonic speech-like PCM16 bytes for testing."""
    t = np.linspace(0, duration_sec, int(duration_sec * sample_rate), endpoint=False, dtype=np.float32)
    signal = 0.5 * np.sin(2.0 * np.pi * f0 * t) + 0.25 * np.sin(2.0 * np.pi * 2.0 * f0 * t)
    pcm = (signal * 32767.0).astype(np.int16).tobytes()
    return pcm


class TestVoiceMicroserviceLifecycle(unittest.TestCase):
    """Verifies local zero-shot speech companion microservice daemon lifecycle & contracts."""

    def test_manager_initialization(self):
        """Verifies microservice manager initializes with expected host, port, and base_url."""
        mgr = VoiceMicroserviceManager(host="127.0.0.1", port=18849)
        self.assertEqual(mgr.host, "127.0.0.1")
        self.assertEqual(mgr.port, 18849)
        self.assertEqual(mgr.base_url, "http://127.0.0.1:18849")
        self.assertFalse(mgr.is_available(timeout_sec=0.05))

    def test_flow_matching_engine_synthesis(self):
        """Verifies in-process neural flow-matching engine synthesizes 48kHz audio."""
        engine = NeuralFlowMatchingEngine(device="cpu", fp16=False)
        ref_pcm = _generate_synthetic_pcm(duration_sec=0.5, sample_rate=48000, f0=130.0)
        pcm_out, dur, sim = engine.synthesize(
            text="Scriber flow matching speech synthesis test.",
            ref_audio_pcm=ref_pcm,
            sample_rate=48000,
        )
        self.assertGreater(len(pcm_out), 48000)  # At least 0.5s of 16-bit audio
        self.assertGreaterEqual(dur, 0.5)
        self.assertGreaterEqual(sim, 0.990)
        self.assertEqual(len(pcm_out) % 2, 0)

    def test_pcm16_to_wav_helper(self):
        """Verifies standard RIFF WAV header generation at 48kHz."""
        raw_pcm = b"\x00\x00" * 48000  # 1 second of silence
        wav_bytes = _pcm16_to_wav(raw_pcm, sample_rate=48000)
        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        self.assertIn(b"WAVE", wav_bytes[:12])
        sr = struct.unpack_from("<I", wav_bytes, 24)[0]
        self.assertEqual(sr, 48000)

    def test_microservice_manager_synthesize_contract(self):
        """Verifies manager.synthesize RPC contract returns pcm, sample_rate, duration."""
        mgr = VoiceMicroserviceManager()
        mock_pcm = _generate_synthetic_pcm(duration_sec=1.0, sample_rate=48000)
        b64_pcm = base64.b64encode(mock_pcm).decode("ascii")

        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps({
            "audio_pcm16_base64": b64_pcm,
            "sample_rate": 48000,
            "duration": 1.0,
            "similarity_score": 0.996,
        }).encode("utf-8")

        with patch.object(mgr, "ensure_running", return_value=True):
            with patch("urllib.request.urlopen", return_value=mock_resp):
                pcm, sr, dur = mgr.synthesize(text="Testing microservice RPC", sample_rate=48000)
                self.assertEqual(sr, 48000)
                self.assertEqual(len(pcm), len(mock_pcm))
                self.assertAlmostEqual(dur, 1.0, delta=0.01)

    def test_microservice_shutdown_contract(self):
        """Verifies manager.shutdown posts to /shutdown endpoint."""
        mgr = VoiceMicroserviceManager()
        mock_resp = MagicMock()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            success = mgr.shutdown()
            self.assertTrue(success)


class TestVoicemakerConnector(unittest.TestCase):
    """Verifies Voicemaker.in Cloud Studio REST connector at 48,000 Hz."""

    def test_connector_init_and_env(self):
        """Verifies initialization and API key retrieval."""
        conn = VoicemakerConnector(api_key="vm_key_test_123")
        self.assertEqual(conn.api_key, "vm_key_test_123")

    def test_payload_structure(self):
        """Verifies Voicemaker payload declares neural engine and 48kHz sample rate."""
        conn = VoicemakerConnector(api_key="key")
        payload = conn._build_payload(text="Voice cloning test", voice_id="ai3-Jony")
        self.assertEqual(payload["Engine"], "neural")
        self.assertEqual(payload["VoiceId"], "ai3-Jony")
        self.assertEqual(payload["AudioSampleRate"], 48000)
        self.assertEqual(payload["Text"], "Voice cloning test")

    def test_headers_formatting(self):
        """Verifies Bearer token authorization header."""
        conn = VoicemakerConnector(api_key="my_secret_token")
        headers = conn._build_headers()
        self.assertEqual(headers["Authorization"], "Bearer my_secret_token")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_synthesize_missing_api_key_raises(self):
        """Verifies synthesizing without an API key raises ValueError."""
        with patch.dict(os.environ, {"VOICEMAKER_API_KEY": ""}):
            conn = VoicemakerConnector()
            with self.assertRaises(ValueError):
                conn.synthesize("Missing key test")

    def test_synthesize_mock_success(self):
        """Verifies Voicemaker synthesis decodes audio response into 48kHz PCM."""
        conn = VoicemakerConnector(api_key="vm_valid_key")
        mock_pcm = _generate_synthetic_pcm(duration_sec=0.8, sample_rate=48000)
        mock_wav = _pcm16_to_wav(mock_pcm, sample_rate=48000)

        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps({
            "status": "success",
            "audio_base64": base64.b64encode(mock_wav).decode("ascii"),
        }).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=mock_resp):
            pcm, sr = conn.synthesize(text="Voicemaker cloud voice synthesis.")
            self.assertEqual(sr, 48000)
            self.assertEqual(len(pcm), len(mock_pcm))


class TestElevenLabsConnector(unittest.TestCase):
    """Verifies ElevenLabs Cloud Studio REST connector with Instant Voice Cloning."""

    def test_connector_init_and_defaults(self):
        """Verifies initialization and default parameters."""
        conn = ElevenLabsConnector(api_key="eleven_key_abc")
        self.assertEqual(conn.api_key, "eleven_key_abc")
        self.assertEqual(conn.DEFAULT_VOICE_ID, "21m00Tcm4TlvDq8ikWAM")

    def test_params_output_format_pcm_48000(self):
        """Verifies output_format query parameter is pcm_48000."""
        conn = ElevenLabsConnector(api_key="key")
        params = conn._build_params()
        self.assertEqual(params["output_format"], "pcm_48000")

    def test_headers_xi_api_key(self):
        """Verifies xi-api-key header formatting."""
        conn = ElevenLabsConnector(api_key="test_xi_token")
        headers = conn._build_headers()
        self.assertEqual(headers["xi-api-key"], "test_xi_token")

    def test_audio_hash_deduplication(self):
        """Verifies SHA-256 reference audio hash prevents redundant IVC uploads."""
        conn = ElevenLabsConnector(api_key="mock_key")
        ref_pcm = _generate_synthetic_pcm(duration_sec=2.0, sample_rate=16000)
        h1 = conn._compute_audio_hash(ref_pcm)
        h2 = hashlib.sha256(ref_pcm).hexdigest()
        self.assertEqual(h1, h2)

        # First call caches ID
        id1 = conn.clone_voice_profile(ref_pcm)
        self.assertTrue(id1.startswith("ivc_"))
        # Second call returns cached ID directly without network
        id2 = conn.clone_voice_profile(ref_pcm)
        self.assertEqual(id1, id2)

    def test_synthesize_missing_api_key_raises(self):
        """Verifies synthesizing without API key raises ValueError."""
        with patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}):
            conn = ElevenLabsConnector()
            with self.assertRaises(ValueError):
                conn.synthesize("ElevenLabs key required")

    def test_synthesize_mock_success(self):
        """Verifies ElevenLabs synthesis returns streaming 48kHz PCM bytes."""
        conn = ElevenLabsConnector(api_key="el_valid_key")
        mock_pcm = _generate_synthetic_pcm(duration_sec=1.2, sample_rate=48000)

        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = mock_pcm

        with patch("urllib.request.urlopen", return_value=mock_resp):
            pcm, sr = conn.synthesize(text="Instant voice cloning text prompt.")
            self.assertEqual(sr, 48000)
            self.assertEqual(len(pcm), len(mock_pcm))


class TestFourTierFallbackMatrix(unittest.TestCase):
    """Verifies 4-tier fallback matrix in VoiceCloner.clone_voice."""

    def setUp(self):
        self.cloner = VoiceCloner()
        self.profile = VoiceProfiler._empty_profile("Speaker_Test")

    def test_tier1_local_gpu_selection(self):
        """Verifies Tier 1 (Local GPU microservice) is engaged when eligible GPU is present."""
        synth_pcm = _generate_synthetic_pcm(duration_sec=0.8, sample_rate=48000)
        with patch.object(self.cloner.microservice_mgr, "is_available", return_value=True):
            with patch.object(self.cloner.microservice_mgr, "synthesize", return_value=(synth_pcm, 48000, 0.8)):
                result = self.cloner.clone_voice(
                    profile=self.profile,
                    text_prompt="Local GPU synthesis",
                    backend="local-gpu",
                )
                self.assertIsInstance(result, VoiceCloneResult)
                self.assertEqual(result.provider, "local-gpu")
                self.assertEqual(result.sample_rate_hz, 48000)
                self.assertIn("f5-tts-flow-matching", result.synthesis_backend)
                self.assertTrue(any("Tier 1" in step and "success" in step for step in result.fallback_chain))

    def test_tier2_voicemaker_cloud_studio(self):
        """Verifies Tier 2 Voicemaker.in is engaged when requested with API key."""
        synth_pcm = _generate_synthetic_pcm(duration_sec=0.8, sample_rate=48000)
        with patch.object(self.cloner.voicemaker_conn, "synthesize", return_value=(synth_pcm, 48000)):
            result = self.cloner.clone_voice(
                profile=self.profile,
                text_prompt="Voicemaker cloud synthesis",
                backend="voicemaker",
                voicemaker_api_key="vm_dummy_key",
            )
            self.assertEqual(result.provider, "voicemaker")
            self.assertEqual(result.sample_rate_hz, 48000)
            self.assertEqual(result.synthesis_backend, "voicemaker-neural")
            self.assertTrue(any("Tier 2 (Voicemaker.in" in step and "success" in step for step in result.fallback_chain))

    def test_tier2_elevenlabs_cloud_studio(self):
        """Verifies Tier 2 ElevenLabs is engaged when requested with API key."""
        synth_pcm = _generate_synthetic_pcm(duration_sec=0.8, sample_rate=48000)
        with patch.object(self.cloner.elevenlabs_conn, "synthesize", return_value=(synth_pcm, 48000)):
            result = self.cloner.clone_voice(
                profile=self.profile,
                text_prompt="ElevenLabs cloud synthesis",
                backend="elevenlabs",
                elevenlabs_api_key="el_dummy_key",
            )
            self.assertEqual(result.provider, "elevenlabs")
            self.assertEqual(result.sample_rate_hz, 48000)
            self.assertEqual(result.synthesis_backend, "elevenlabs-studio")
            self.assertTrue(any("Tier 2 (ElevenLabs" in step and "success" in step for step in result.fallback_chain))

    def test_tier3_edge_tts_fallback_with_48khz_resampling(self):
        """Verifies Tier 3 Edge-TTS synthesizes and resamples to 48kHz."""
        synth_16k = _generate_synthetic_pcm(duration_sec=0.5, sample_rate=16000)
        with patch.object(self.cloner, "_synthesize_with_edge_tts", return_value=synth_16k):
            result = self.cloner.clone_voice(
                profile=self.profile,
                text_prompt="Edge-TTS neural fallback",
                backend="edge-neural",
            )
            self.assertEqual(result.provider, "edge-tts")
            self.assertEqual(result.sample_rate_hz, 48000)
            self.assertEqual(len(result.audio_pcm16), len(synth_16k) * 3)  # Exact 3x upsampling
            self.assertTrue(any("Tier 3" in step and "success" in step for step in result.fallback_chain))

    def test_tier4_offline_vocoder_guarantee(self):
        """Verifies Tier 4 Offline Parametric Biquad IIR Vocoder produces valid 48kHz audio without network."""
        result = self.cloner.clone_voice(
            profile=self.profile,
            text_prompt="Offline vocoder non-negotiable guarantee.",
            backend="formant-harmonic-engine",
        )
        self.assertEqual(result.provider, "offline-vocoder")
        self.assertEqual(result.sample_rate_hz, 48000)
        self.assertGreater(len(result.audio_pcm16), 1000)
        self.assertGreater(result.duration, 0.2)
        self.assertGreaterEqual(result.similarity_score, 0.990)
        self.assertTrue(any("Tier 4" in step and "success" in step for step in result.fallback_chain))


class TestDualRate48kHzAudioValidity(unittest.TestCase):
    """Verifies dual-rate audio conversions, WAV headers, and biometric verification."""

    def test_resample_pcm_16k_to_48k_and_back(self):
        """Verifies lossless round-trip sinc resampling between 16kHz and 48kHz."""
        pcm_16k = _generate_synthetic_pcm(duration_sec=0.5, sample_rate=16000, f0=140.0)
        pcm_48k = AudioEditor.resample_pcm(pcm_16k, src_sr=16000, dst_sr=48000)
        self.assertEqual(len(pcm_48k), len(pcm_16k) * 3)

        pcm_back_16k = AudioEditor.resample_pcm(pcm_48k, src_sr=48000, dst_sr=16000)
        self.assertEqual(len(pcm_back_16k), len(pcm_16k))

        # Check waveform correlation between original and round-trip
        s_orig = np.frombuffer(pcm_16k, dtype=np.int16).astype(np.float32)
        s_back = np.frombuffer(pcm_back_16k, dtype=np.int16).astype(np.float32)
        corr = np.corrcoef(s_orig, s_back)[0, 1]
        self.assertGreater(corr, 0.98)

    def test_voice_profiler_48k_auto_detection(self):
        """Verifies VoiceProfiler handles 48kHz audio and extracts calibrated F0."""
        pcm_48k = _generate_synthetic_pcm(duration_sec=1.5, sample_rate=48000, f0=150.0)
        profile = VoiceProfiler.profile_from_pcm16(pcm_48k, speaker_id="Speaker_48k")
        self.assertEqual(profile.speaker_id, "Speaker_48k")
        # Pitch should be near 150 Hz, not divided by 3 (50 Hz)
        self.assertAlmostEqual(profile.fundamental_frequency_hz, 150.0, delta=12.0)


class TestServerVoiceEndpoints(unittest.TestCase):
    """Verifies REST API endpoints for credentials and voice cloning."""

    def setUp(self):
        self.handler = ScriberHTTPRequestHandler.__new__(ScriberHTTPRequestHandler)
        self.handler.wfile = io.BytesIO()
        self.handler.rfile = io.BytesIO()
        self.handler.headers = {}
        self.handler.send_response = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.end_headers = MagicMock()

    def test_get_voice_credentials(self):
        """Verifies GET /api/voice/credentials returns configuration state."""
        self.handler.path = "/api/voice/credentials"
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        body = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("voicemaker_configured", body)
        self.assertIn("elevenlabs_configured", body)
        self.assertIn("voicemaker_masked_key", body)
        self.assertIn("elevenlabs_masked_key", body)

    def test_post_voice_credentials(self):
        """Verifies POST /api/voice/credentials updates API keys."""
        req_data = {
            "voicemaker_api_key": "vm_test_live_key_12345",
            "elevenlabs_api_key": "el_test_live_key_67890",
        }
        body_bytes = json.dumps(req_data).encode("utf-8")
        self.handler.path = "/api/voice/credentials"
        self.handler.headers = {"Content-Length": str(len(body_bytes))}
        self.handler.rfile = io.BytesIO(body_bytes)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        resp = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(resp["status"], "success")
        self.assertTrue(resp["voicemaker_configured"])
        self.assertTrue(resp["elevenlabs_configured"])
        self.assertEqual(os.environ.get("VOICEMAKER_API_KEY"), "vm_test_live_key_12345")
        self.assertEqual(os.environ.get("ELEVENLABS_API_KEY"), "el_test_live_key_67890")

    def test_post_clone_voice_with_48khz_response(self):
        """Verifies POST /api/clone-voice returns 48kHz audio and valid dataclass fields."""
        req_data = {
            "text": "Scriber 48kHz voice synthesis verified by server endpoint.",
            "backend": "offline-formant",
            "sample_rate": 48000,
        }
        body_bytes = json.dumps(req_data).encode("utf-8")
        self.handler.path = "/api/clone-voice"
        self.handler.headers = {"Content-Length": str(len(body_bytes))}
        self.handler.rfile = io.BytesIO(body_bytes)

        self.handler.do_POST()
        self.handler.send_response.assert_called_with(200)
        resp = json.loads(self.handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("audio_base64", resp)
        self.assertEqual(resp["sample_rate_hz"], 48000)
        self.assertGreaterEqual(resp["similarity_score"], 0.990)
        self.assertIn("fallback_chain", resp)


if __name__ == "__main__":
    unittest.main()
