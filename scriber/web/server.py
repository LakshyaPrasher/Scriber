"""Standalone Web Server & REST API for Scriber.
Runs entirely on Python's standard library (http.server, email) with zero external server dependencies.
"""

from __future__ import annotations

import base64
import email
import http.server
import json
import os
import socket
import socketserver
import sys
import tempfile
import threading
import urllib.parse
from typing import Any, Dict, Optional, Tuple

from scriber.exporters import ScriberExporter
from scriber.transcription_engine import TOP_LEVERAGED_REPOS
from scriber.models import VoiceProfile
from scriber.pipeline import ScriberPipeline
from scriber.validator import ResultValidator
from scriber.voice_clone import VoiceCloner, VoiceProfiler
from scriber.web.ui import get_embedded_html


class ScriberHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for Scriber Web UI and REST API."""

    protocol_version = "HTTP/1.0"
    pipeline = ScriberPipeline()

    def do_OPTIONS(self):
        """Handles CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._serve_embedded_ui()
        elif path in ("/favicon.ico", "/icon.ico"):
            self._serve_icon()
        elif path.startswith("/assets/") or path.startswith("/api/assets/"):
            asset_filename = os.path.basename(path)
            from scriber.assets import get_asset_path
            asset_file = get_asset_path(asset_filename)
            if asset_file.exists():
                self._serve_static_file(str(asset_file))
            else:
                self._send_json_response(404, {"error": "Asset not found"})
        elif path == "/api/health":
            self._send_json_response(200, {"status": "ok", "app": "Scriber"})
        elif path == "/api/hardware":
            from scriber.hardware import get_hardware_capabilities
            caps = get_hardware_capabilities()
            self._send_json_response(200, caps.to_dict())
        elif path == "/api/desktop/info":
            from scriber import __version__
            self._send_json_response(200, {
                "name": "Scriber Studio Desktop",
                "app_name": "Scriber Studio Desktop",
                "version": __version__,
                "desktop_mode": True,
                "is_desktop": True,
                "platform": sys.platform,
                "is_frozen": getattr(sys, "frozen", False),
            })
        elif path == "/api/benchmark":
            results = ResultValidator.run_benchmark_suite()
            self._send_json_response(200, results)
        elif path == "/api/models":
            from scriber.transcription_engine import TOP_TRANSCRIBE_MODELS, get_model_evaluation_matrix
            from scriber.voice_clone import TOP_VOICE_MODELS
            self._send_json_response(200, {
                "transcribe_models": TOP_TRANSCRIBE_MODELS,
                "voice_models": TOP_VOICE_MODELS,
                "evaluation_matrix": get_model_evaluation_matrix(),
            })
        elif path == "/api/voice/credentials":
            # Paid cloud APIs removed for zero financial exposure
            self._send_json_response(200, {
                "voicemaker_configured": False,
                "elevenlabs_configured": False,
                "voicemaker_masked_key": "",
                "elevenlabs_masked_key": "",
                "zero_financial_exposure": True,
            })
        elif path == "/api/agents":
            from scriber.agent_swarm import CouncilAgentSwarm
            swarm = CouncilAgentSwarm()
            agents = [a.to_dict() for a in swarm.get_registered_agents()]
            self._send_json_response(200, {
                "agents": agents,
                "framework": "wshobson/agents",
                "framework_url": "https://github.com/wshobson/agents",
                "count": len(agents),
            })
        elif path == "/api/council/swarm":
            from scriber.agent_swarm import CouncilAgentSwarm
            swarm = CouncilAgentSwarm()
            agents = [a.to_dict() for a in swarm.get_registered_agents()]
            telemetry = [t.to_dict() for t in getattr(self.pipeline.supreme_council, "swarm", swarm).last_telemetry]
            self._send_json_response(200, {
                "agents": agents,
                "telemetry": telemetry,
                "framework": "wshobson/agents",
            })
        elif path == "/api/plugin/manifest":
            from pathlib import Path
            manifest_file = Path(__file__).resolve().parent.parent.parent / ".antigravity" / "plugins" / "scriber" / "plugin.json"
            if manifest_file.exists():
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                self._send_json_response(200, manifest_data)
            else:
                self._send_json_response(404, {"error": "Plugin manifest not found"})
        elif path == "/api/info":
            from scriber import __version__
            from scriber.agent_swarm import CouncilAgentSwarm
            swarm = CouncilAgentSwarm()
            self._send_json_response(200, {
                "name": "Scriber",
                "version": __version__,
                "description": "Autonomous Video Intelligence, Whisper Flow Transcription, and Voice Cloning Pipeline",
                "repos": TOP_LEVERAGED_REPOS,
                "agent_swarm_count": len(swarm.get_registered_agents()),
                "framework": "wshobson/agents",
            })
        else:
            # Check if file exists in current working directory / workspace
            clean_path = path.lstrip("/").replace("%20", " ")
            if clean_path and os.path.isfile(clean_path):
                self._serve_static_file(clean_path)
            else:
                self._send_json_response(404, {"error": "Endpoint not found"})

    def _serve_icon(self):
        """Serves the Scriber brand icon (ICO format)."""
        try:
            from scriber.assets import get_icon_path
            icon_path = get_icon_path()
            if icon_path.exists():
                self._serve_static_file(str(icon_path))
                return
        except Exception:
            pass
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _serve_static_file(self, filepath: str):
        """Serves static audio, video, image, or document files from the workspace."""
        import mimetypes
        mime, _ = mimetypes.guess_type(filepath)
        if not mime:
            if filepath.endswith(".mp3"):
                mime = "audio/mpeg"
            elif filepath.endswith(".wav"):
                mime = "audio/wav"
            elif filepath.endswith(".mp4"):
                mime = "video/mp4"
            elif filepath.endswith(".png"):
                mime = "image/png"
            else:
                mime = "application/octet-stream"

        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                self.wfile.write(content)
                self.wfile.flush()
            except Exception:
                pass
            self.close_connection = True
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/process":
            self._handle_media_upload()
        elif path == "/api/process-demo":
            self._handle_demo_process()
        elif path == "/api/clone-voice":
            self._handle_voice_cloning()
        elif path == "/api/profile-voice":
            self._handle_voice_profiling()
        elif path == "/api/edit-audio":
            self._handle_edit_audio()
        elif path == "/api/desktop/reveal":
            self._handle_desktop_reveal()
        elif path == "/api/desktop/save-file":
            self._handle_desktop_save_file()
        elif path == "/api/pii/redact":
            self._handle_pii_redact()
        elif path == "/api/plugin/install":
            self._handle_plugin_install()
        elif path == "/api/voice/credentials":
            self._handle_voice_credentials()
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _handle_voice_credentials(self):
        """Saves Voicemaker and ElevenLabs API credentials."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            req_data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

            vm_key = req_data.get("voicemaker_api_key")
            el_key = req_data.get("elevenlabs_api_key")

            if vm_key is not None:
                vm_key_str = str(vm_key).strip()
                os.environ["VOICEMAKER_API_KEY"] = vm_key_str
                if hasattr(self, "pipeline") and hasattr(self.pipeline, "voice_cloner") and hasattr(self.pipeline.voice_cloner, "voicemaker_conn"):
                    self.pipeline.voice_cloner.voicemaker_conn.api_key = vm_key_str

            if el_key is not None:
                el_key_str = str(el_key).strip()
                os.environ["ELEVENLABS_API_KEY"] = el_key_str
                if hasattr(self, "pipeline") and hasattr(self.pipeline, "voice_cloner") and hasattr(self.pipeline.voice_cloner, "elevenlabs_conn"):
                    self.pipeline.voice_cloner.elevenlabs_conn.api_key = el_key_str

            vm_active = bool(os.environ.get("VOICEMAKER_API_KEY"))
            el_active = bool(os.environ.get("ELEVENLABS_API_KEY"))

            self._send_json_response(200, {
                "status": "success",
                "message": "Voice studio credentials updated successfully",
                "voicemaker_configured": vm_active,
                "elevenlabs_configured": el_active,
            })
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_pii_redact(self):
        """Redacts sensitive PII and secrets from arbitrary input text."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            req_data = json.loads(body_bytes.decode("utf-8"))
            text = req_data.get("text", "")
            mask_mode = req_data.get("mask_mode", "partial")
            from scriber.pii_security import PIISecurityOfficer
            officer = PIISecurityOfficer()
            redacted_text, counts, audit_log = officer.redact_text(text, mask_mode=mask_mode)
            self._send_json_response(200, {
                "original_text": text,
                "redacted_text": redacted_text,
                "entities_found": counts,
                "redacted_count": sum(counts.values()),
                "audit_log": audit_log,
                "compliance_score": 1.0 if not counts else max(0.95, 1.0 - sum(counts.values()) * 0.005),
            })
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_plugin_install(self):
        """Installs Scriber plugin into Google Antigravity configuration directory."""
        try:
            import shutil
            from pathlib import Path
            home = Path.home()
            dest_dir = home / ".gemini" / "config" / "plugins" / "scriber"
            src_dir = Path(__file__).resolve().parent.parent.parent / ".antigravity" / "plugins" / "scriber"
            if not src_dir.exists():
                self._send_json_response(404, {"error": "Plugin source bundle not found"})
                return
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_dir, dest_dir)
            self._send_json_response(200, {
                "status": "success",
                "message": "Scriber plugin successfully installed into Google Antigravity",
                "path": str(dest_dir),
            })
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_media_upload(self):
        """Handles upload of video/audio file via multipart form-data or direct JSON file_path."""
        tmp_path = None
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            if content_length <= 0:
                self._send_json_response(400, {"error": "Content-Length header is missing or empty"})
                return

            body_bytes = self.rfile.read(content_length)

            # Support direct JSON payload: {"file_path": "path/to/media.mp3", "task": "translate", "model": "turbo"}
            if content_type.startswith("application/json"):
                data = json.loads(body_bytes.decode("utf-8"))
                file_path_arg = data.get("file_path", "")
                if not file_path_arg or not os.path.isfile(file_path_arg):
                    self._send_json_response(400, {"error": f"File '{file_path_arg}' not found on server"})
                    return
                redact_pii_val = bool(data.get("redact_pii", False))
                output = self.pipeline.process_file(
                    file_path=file_path_arg,
                    task=data.get("task", "translate"),
                    language=None if data.get("language") in ("auto", "none", "", None) else data.get("language"),
                    reference_text=data.get("reference_text"),
                    model=data.get("model", "turbo"),
                    redact_pii=redact_pii_val,
                )
                output.video_source = os.path.basename(file_path_arg)
                try:
                    self.pipeline._export_all_formats(output, "./scriber_output", ["json", "md", "srt", "vtt", "txt", "html"])
                except Exception:
                    pass
                resp_data = output.to_dict()
                resp_data["exports"] = {
                    "txt": ScriberExporter.to_txt(output),
                    "markdown": ScriberExporter.to_markdown(output),
                    "srt": ScriberExporter.to_srt(output),
                    "vtt": ScriberExporter.to_vtt(output),
                }
                self._send_json_response(200, resp_data)
                return

            if not content_type.startswith("multipart/form-data"):
                self._send_json_response(400, {"error": "Content-Type must be multipart/form-data or application/json"})
                return

            # Standard library email parser for multipart boundaries (PEP 594 compliant, no cgi)
            msg_bytes = f"Content-Type: {content_type}\r\n\r\n".encode("latin-1") + body_bytes
            msg = email.message_from_bytes(msg_bytes)

            file_data = None
            filename = "uploaded_media.mp4"
            task = "translate"
            language = "auto"
            ref_text = None
            file_path_param = None
            model = "turbo"
            redact_pii = False

            for part in msg.walk():
                if part.is_multipart():
                    continue
                name = part.get_param("name", header="content-disposition")
                if not name:
                    continue

                if name == "file":
                    file_data = part.get_payload(decode=True)
                    fname = part.get_filename()
                    if fname:
                        filename = fname
                elif name == "file_path":
                    payload = part.get_payload(decode=True)
                    if payload:
                        file_path_param = payload.decode("utf-8", errors="replace").strip()
                elif name == "task":
                    payload = part.get_payload(decode=True)
                    if payload:
                        task = payload.decode("utf-8", errors="replace").strip() or "translate"
                elif name == "language":
                    payload = part.get_payload(decode=True)
                    if payload:
                        language = payload.decode("utf-8", errors="replace").strip() or "auto"
                elif name == "model":
                    payload = part.get_payload(decode=True)
                    if payload:
                        model = payload.decode("utf-8", errors="replace").strip() or "turbo"
                elif name == "reference_text":
                    payload = part.get_payload(decode=True)
                    if payload:
                        ref_text = payload.decode("utf-8", errors="replace").strip() or None
                elif name == "redact_pii":
                    payload = part.get_payload(decode=True)
                    if payload:
                        val = payload.decode("utf-8", errors="replace").strip().lower()
                        redact_pii = val in ("1", "true", "yes", "on")

            # Handle file_path parameter if provided and valid
            if file_path_param and os.path.isfile(file_path_param):
                output = self.pipeline.process_file(
                    file_path=file_path_param,
                    task=task,
                    language=None if language in ("auto", "none", "", None) else language,
                    reference_text=ref_text,
                    model=model,
                    redact_pii=redact_pii,
                )
                output.video_source = os.path.basename(file_path_param)
                try:
                    self.pipeline._export_all_formats(output, "./scriber_output", ["json", "md", "srt", "vtt", "txt", "html"])
                except Exception:
                    pass
                resp_data = output.to_dict()
                resp_data["exports"] = {
                    "txt": ScriberExporter.to_txt(output),
                    "markdown": ScriberExporter.to_markdown(output),
                    "srt": ScriberExporter.to_srt(output),
                    "vtt": ScriberExporter.to_vtt(output),
                }
                if self.pipeline.last_pcm_data:
                    try:
                        from scriber.audio_editor import AudioEditor
                        mp3_b = AudioEditor.encode_mp3(self.pipeline.last_pcm_data, sr=16000, channels=1, bit_rate=192000)
                        resp_data["audio_base64"] = f"data:audio/mp3;base64,{base64.b64encode(mp3_b).decode('ascii')}"
                    except Exception:
                        pass
                self._send_json_response(200, resp_data)
                return

            if not file_data:
                self._send_json_response(400, {"error": "No file uploaded under form key 'file'"})
                return

            ext = os.path.splitext(filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(file_data)

            output = self.pipeline.process_file(
                file_path=tmp_path,
                task=task,
                language=None if language in ("auto", "none", "", None) else language,
                reference_text=ref_text,
                model=model,
                redact_pii=redact_pii,
            )
            output.video_source = filename
            try:
                self.pipeline._export_all_formats(output, "./scriber_output", ["json", "md", "srt", "vtt", "txt", "html"])
            except Exception:
                pass
            resp_data = output.to_dict()
            resp_data["exports"] = {
                "txt": ScriberExporter.to_txt(output),
                "markdown": ScriberExporter.to_markdown(output),
                "srt": ScriberExporter.to_srt(output),
                "vtt": ScriberExporter.to_vtt(output),
            }
            if self.pipeline.last_pcm_data:
                try:
                    from scriber.audio_editor import AudioEditor
                    mp3_b = AudioEditor.encode_mp3(self.pipeline.last_pcm_data, sr=16000, channels=1, bit_rate=192000)
                    resp_data["audio_base64"] = f"data:audio/mp3;base64,{base64.b64encode(mp3_b).decode('ascii')}"
                except Exception:
                    pass
            self._send_json_response(200, resp_data)

        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _handle_demo_process(self):
        """Processes built-in demo video/audio scenario without requiring manual upload."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                self.rfile.read(content_length)

            demo_audio = self.pipeline.audio_extractor.create_synthetic_wav(
                "Demo operational meeting session", duration_sec=5.0
            )
            demo_text = (
                "Welcome to the Scriber engineering standup. "
                "Alex will finalize the desktop application release by Thursday. "
                "Sarah should implement the Whisper VAD audio chunking algorithm today. "
                "We agreed that 99 percent accuracy is our non-negotiable benchmark. "
                "What is the projected startup latency for the desktop bundle?"
            )
            output = self.pipeline.process_pcm(
                pcm16_data=demo_audio,
                source_name="Scriber_Engineering_Sync_Demo.mp4",
                reference_text=demo_text,
            )
            resp_data = output.to_dict()
            resp_data["audio_base64"] = "data:audio/wav;base64," + base64.b64encode(demo_audio).decode("ascii")
            resp_data["exports"] = {
                "txt": ScriberExporter.to_txt(output),
                "markdown": ScriberExporter.to_markdown(output),
                "srt": ScriberExporter.to_srt(output),
                "vtt": ScriberExporter.to_vtt(output),
            }
            self._send_json_response(200, resp_data)
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_voice_cloning(self):
        """Handles voice cloning synthesis request for a given speaker profile and prompt."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            req_data = json.loads(body_bytes.decode("utf-8"))

            text_prompt = req_data.get("text", "Welcome to Scriber voice cloning synthesis.")
            pitch_shift = float(req_data.get("pitch_shift", 0.0))
            rate_shift = float(req_data.get("rate_shift", 0.0))
            profile_dict = req_data.get("profile")

            if profile_dict and isinstance(profile_dict, dict):
                profile = VoiceProfile.from_dict(profile_dict)
            else:
                profile = VoiceProfiler._empty_profile("Speaker_1")

            ref_pcm = getattr(self.pipeline, "reference_pcm", None) or getattr(self.pipeline, "last_pcm_data", None)

            # If client provided reference audio base64, decode directly to guarantee accurate timbre match
            ref_b64 = req_data.get("reference_audio") or req_data.get("reference_base64")
            if ref_b64 and isinstance(ref_b64, str):
                try:
                    if "," in ref_b64:
                        ref_b64 = ref_b64.split(",", 1)[1]
                    raw_ref_bytes = base64.b64decode(ref_b64)
                    suffix = ".wav" if raw_ref_bytes.startswith(b"RIFF") else ".mp3"
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_ref:
                        tmp_ref.write(raw_ref_bytes)
                        tmp_ref_path = tmp_ref.name
                    try:
                        extracted_pcm, _ = self.pipeline.audio_extractor.extract_pcm16(tmp_ref_path)
                        if extracted_pcm and len(extracted_pcm) > 320:
                            ref_pcm = extracted_pcm
                            self.pipeline.reference_pcm = extracted_pcm
                    finally:
                        if os.path.exists(tmp_ref_path):
                            try:
                                os.remove(tmp_ref_path)
                            except Exception:
                                pass
                except Exception:
                    pass

            backend = req_data.get("backend") or req_data.get("model") or "edge-neural"
            output_format = req_data.get("output_format") or req_data.get("format") or "mp3"
            sample_rate = int(req_data.get("sample_rate", 48000))
            voice_id = req_data.get("voice_id")
            result = self.pipeline.clone_voice(
                profile=profile,
                text_prompt=text_prompt,
                pitch_shift_hz=pitch_shift,
                rate_shift_pct=rate_shift,
                output_format=output_format,
                reference_pcm=ref_pcm,
                backend=backend,
                sample_rate=sample_rate,
                voice_id=voice_id,
            )
            if result.audio_pcm16:
                self.pipeline.last_pcm_data = result.audio_pcm16
                self.pipeline.last_file_path = f"cloned_{profile.speaker_id}.mp3"

            self._send_json_response(200, result.to_dict())

        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_voice_profiling(self):
        """Extracts speaker biometric VoiceProfile from an uploaded reference audio/video file."""
        tmp_path = None
        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self._send_json_response(400, {"error": "Content-Type must be multipart/form-data"})
                return

            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self._send_json_response(400, {"error": "Content-Length header is missing or empty"})
                return

            body_bytes = self.rfile.read(content_length)
            msg_bytes = f"Content-Type: {content_type}\r\n\r\n".encode("latin-1") + body_bytes
            msg = email.message_from_bytes(msg_bytes)

            file_data = None
            filename = "reference_voice.mp3"
            speaker_name = "Custom Voice"

            for part in msg.walk():
                if part.is_multipart():
                    continue
                name = part.get_param("name", header="content-disposition")
                if not name:
                    continue
                if name == "file":
                    file_data = part.get_payload(decode=True)
                    fname = part.get_filename()
                    if fname:
                        filename = fname
                elif name == "speaker":
                    payload = part.get_payload(decode=True)
                    if payload:
                        speaker_name = payload.decode("utf-8", errors="replace").strip() or speaker_name

            if not file_data:
                self._send_json_response(400, {"error": "No file uploaded under form key 'file'"})
                return

            ext = os.path.splitext(filename)[1] or ".mp3"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(file_data)

            pcm_data, meta = self.pipeline.audio_extractor.extract_pcm16(tmp_path)
            profile = VoiceProfiler.profile_from_pcm16(pcm_data, speaker_id=speaker_name)

            # Store in pipeline for immediate voice cloning and audio editor
            self.pipeline.reference_pcm = pcm_data
            self.pipeline.reference_filename = filename
            self.pipeline.last_pcm_data = pcm_data
            self.pipeline.last_file_path = filename

            from scriber.audio_editor import AudioEditor
            mp3_bytes = AudioEditor.encode_mp3(pcm_data, sr=16000, channels=1, bit_rate=192000)
            b64_str = base64.b64encode(mp3_bytes).decode("ascii")

            self._send_json_response(200, {
                "profile": profile.to_dict(),
                "filename": filename,
                "duration": round(meta.duration, 3),
                "audio_base64": f"data:audio/mp3;base64,{b64_str}",
            })
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _handle_edit_audio(self):
        """Handles audio editing requests: volume gain, pitch-shift, trimming, and MP3 generation."""
        tmp_path = None
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            volume = 1.0
            pitch_semitones = 0.0
            start_sec = 0.0
            end_sec = None
            filename = "scriber_edited.mp3"
            file_data = None

            if content_type.startswith("multipart/form-data"):
                body_bytes = self.rfile.read(content_length)
                msg_bytes = f"Content-Type: {content_type}\r\n\r\n".encode("latin-1") + body_bytes
                msg = email.message_from_bytes(msg_bytes)

                for part in msg.walk():
                    if part.is_multipart():
                        continue
                    name = part.get_param("name", header="content-disposition")
                    if not name:
                        continue
                    if name == "file":
                        file_data = part.get_payload(decode=True)
                        fname = part.get_filename()
                        if fname:
                            filename = os.path.splitext(fname)[0] + "_edited.mp3"
                    elif name == "volume":
                        val = part.get_payload(decode=True)
                        if val:
                            try:
                                volume = float(val.decode("utf-8").strip())
                            except Exception:
                                pass
                    elif name in ("pitch_semitones", "pitch"):
                        val = part.get_payload(decode=True)
                        if val:
                            try:
                                pitch_semitones = float(val.decode("utf-8").strip())
                            except Exception:
                                pass
                    elif name in ("start_sec", "start"):
                        val = part.get_payload(decode=True)
                        if val:
                            try:
                                start_sec = float(val.decode("utf-8").strip())
                            except Exception:
                                pass
                    elif name in ("end_sec", "end"):
                        val = part.get_payload(decode=True)
                        if val:
                            try:
                                raw_val = val.decode("utf-8").strip()
                                if raw_val and raw_val.lower() not in ("none", "null", ""):
                                    end_sec = float(raw_val)
                            except Exception:
                                pass
                    elif name == "filename":
                        val = part.get_payload(decode=True)
                        if val:
                            f = val.decode("utf-8").strip()
                            if f:
                                filename = f
            else:
                body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                volume = float(data.get("volume", 1.0))
                pitch_semitones = float(data.get("pitch_semitones", data.get("pitch", 0.0)))
                start_sec = float(data.get("start_sec", data.get("start", 0.0)))
                end_val = data.get("end_sec", data.get("end"))
                if end_val is not None and str(end_val).strip() != "":
                    end_sec = float(end_val)
                filename = data.get("filename", "scriber_edited.mp3")

                audio_b64 = data.get("audio_base64")
                if audio_b64:
                    if "," in audio_b64:
                        audio_b64 = audio_b64.split(",", 1)[1]
                    file_data = base64.b64decode(audio_b64)

            pcm_data = None
            if file_data:
                ext = ".wav" if file_data.startswith(b"RIFF") else ".mp3"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp_path = tmp.name
                    tmp.write(file_data)
                pcm_data, _ = self.pipeline.audio_extractor.extract_pcm16(tmp_path)

            res = self.pipeline.edit_audio(
                pcm_data=pcm_data,
                volume=volume,
                pitch_semitones=pitch_semitones,
                start_sec=start_sec,
                end_sec=end_sec,
                filename=filename,
            )
            self._send_json_response(200, res)

        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _handle_desktop_reveal(self):
        """Reveals a target file or opens directory in native file explorer."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            target = data.get("path") or data.get("file") or "./scriber_output"
            abs_path = os.path.abspath(target)

            if not os.path.exists(abs_path):
                os.makedirs(abs_path, exist_ok=True)

            opened = False
            if sys.platform == "win32":
                import subprocess
                if os.path.isfile(abs_path):
                    subprocess.Popen(["explorer.exe", f"/select,{abs_path}"])
                    opened = True
                else:
                    os.startfile(abs_path)
                    opened = True
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", abs_path])
                opened = True
            else:
                import subprocess
                subprocess.Popen(["xdg-open", abs_path])
                opened = True

            self._send_json_response(200, {"success": True, "path": abs_path, "opened": opened})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_desktop_save_file(self):
        """Saves text or base64 binary content directly into a local file."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            data = json.loads(body_bytes.decode("utf-8"))
            filename = data.get("filename", "transcript_export.txt")
            content = data.get("content", "")
            out_dir = data.get("dir", "./scriber_output")
            os.makedirs(out_dir, exist_ok=True)
            target_path = os.path.join(out_dir, os.path.basename(filename))

            if data.get("is_base64", False):
                raw = base64.b64decode(content)
                with open(target_path, "wb") as f:
                    f.write(raw)
            else:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(content)

            self._send_json_response(200, {"success": True, "saved_path": os.path.abspath(target_path)})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _send_json_response(self, status: int, data: Dict[str, Any]):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except Exception:
            pass
        self.close_connection = True

    def _serve_embedded_ui(self):
        """Serves the standalone responsive dashboard."""
        import importlib
        import scriber.web.ui
        try:
            importlib.reload(scriber.web.ui)
            html = scriber.web.ui.get_embedded_html()
        except Exception:
            html = get_embedded_html()
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except Exception:
            pass
        self.close_connection = True


class ScriberServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Multi-threaded TCPServer with address reuse and daemon worker threads for desktop runtime."""
    allow_reuse_address = True
    daemon_threads = True
    block_on_close = False
    request_queue_size = 64


def find_available_port(host: str = "127.0.0.1", preferred_port: int = 8080) -> int:
    """Finds an available TCP port, preferring preferred_port if free."""
    if preferred_port and preferred_port > 0:
        # 1. Probe if a service is actively listening on preferred_port
        try:
            with socket.create_connection((host, preferred_port), timeout=0.1):
                pass
            # Connected successfully -> port is occupied!
        except (OSError, ConnectionRefusedError):
            # 2. Port is not accepting connections; test exclusive bind
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((host, preferred_port))
                    return preferred_port
            except OSError:
                pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


class ScriberBackgroundServer:
    """Manages the lifecycle of a background Scriber HTTP server thread."""

    def __init__(self, host: str = "127.0.0.1", port: Optional[int] = None):
        self.host = host
        self.port = find_available_port(host, 8080 if port is None else port)
        self.httpd: Optional[ScriberServer] = None
        self.thread: Optional[threading.Thread] = None
        self._is_running = False

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self, timeout: float = 6.0) -> ScriberBackgroundServer:
        """Starts server in background thread and waits until socket is actively listening."""
        if self._is_running:
            return self

        handler = ScriberHTTPRequestHandler
        self.httpd = ScriberServer((self.host, self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True, name="ScriberServerThread")
        self.thread.start()
        self._is_running = True

        # Wait for server to become responsive
        import time
        start_time = time.time()
        server_ready = False
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((self.host, self.port), timeout=0.2) as sock:
                    sock.sendall(b"GET /api/health HTTP/1.0\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
                    data = sock.recv(256)
                    if b"200 OK" in data:
                        server_ready = True
                        break
            except (OSError, ConnectionRefusedError):
                time.sleep(0.05)

        if not server_ready:
            logger.warning("Scriber background server did not confirm 200 OK within %.1fs timeout", timeout)

        return self

    def stop(self):
        """Cleanly shuts down the server."""
        if self._is_running and self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
            self._is_running = False

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()




def run_server(host: str = "127.0.0.1", port: int = 8080):
    """Starts the local web server."""
    port = find_available_port(host, port)
    handler = ScriberHTTPRequestHandler
    with ScriberServer((host, port), handler) as httpd:
        print(f"\n=======================================================")
        print(f"  🌐 Scriber Web UI Active (Transcription, Diarization & Voice Cloning)")
        print(f"=======================================================")
        print(f"  URL: http://{host}:{port}")
        print(f"  Press Ctrl+C to terminate server.")
        print(f"-------------------------------------------------------\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Scriber server.")
            httpd.server_close()

