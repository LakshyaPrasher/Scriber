"""Standalone Web Server & REST API for Scriber.
Runs entirely on Python's standard library (http.server, email) with zero external server dependencies.
"""

from __future__ import annotations

import base64
import email
import http.server
import json
import logging
import math
import os
import re
import shutil
import mimetypes
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import wave
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple, Union

from scriber import __version__

try:
    from scriber.agent_swarm import CouncilAgentSwarm
except ImportError:
    CouncilAgentSwarm = None

try:
    from scriber.audio_editor import AudioEditor
except ImportError:
    AudioEditor = None

from scriber.exceptions import JobCancelledException, TranscriptionUnavailableError
from scriber.exporters import ScriberExporter
from scriber.models import VoiceProfile

try:
    from scriber.voice_clone import VoiceCloner
except ImportError:
    VoiceCloner = None

from scriber.web.ui import get_embedded_html

logger = logging.getLogger(__name__)

# Hard ceiling for any single request body. Prevents a local client (or a
# mistakenly selected multi-gigabyte file) from exhausting process memory.
MAX_UPLOAD_SIZE = 1024 * 1024 * 1024  # 1 GiB

_ALLOWED_MEDIA_FILES: Set[str] = set()
_ALLOWED_MEDIA_LOCK = threading.Lock()


def register_allowed_media_file(path: Union[str, Path, None]) -> None:
    """Registers an explicit file path allowed to be served via /api/media."""
    if not path:
        return
    try:
        norm = os.path.normcase(os.path.realpath(str(path)))
        with _ALLOWED_MEDIA_LOCK:
            _ALLOWED_MEDIA_FILES.add(norm)
    except Exception:
        pass


def is_allowed_media_file(path: Union[str, Path, None]) -> bool:
    """Checks whether an explicit path has been registered in the allow-list."""
    if not path:
        return False
    try:
        norm = os.path.normcase(os.path.realpath(str(path)))
        with _ALLOWED_MEDIA_LOCK:
            return norm in _ALLOWED_MEDIA_FILES
    except Exception:
        return False


def _output_root() -> Path:
    """Directory where Scriber writes exports and persistent media.

    Override with SCRIBER_OUTPUT_DIR so automated/live tests never overwrite a
    user's real transcript exports in the repository's scriber_output folder.
    """
    override = os.environ.get("SCRIBER_OUTPUT_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.cwd() / "scriber_output").resolve()


def _media_roots() -> Tuple[Path, ...]:
    """Roots that may be served by /api/media without prior registration."""
    return (_output_root(), Path(tempfile.gettempdir()).resolve())


def _is_within(path: str, roots: Iterable[Path]) -> bool:
    """Case-insensitive containment check using realpath to prevent link traversal."""
    try:
        candidate = os.path.normcase(os.path.realpath(str(path)))
    except (TypeError, ValueError):
        return False
    for root in roots:
        try:
            root_s = os.path.normcase(os.path.realpath(str(root)))
        except (TypeError, ValueError):
            continue
        if candidate == root_s or candidate.startswith(root_s + os.sep):
            return True
    return False


def _as_bool(value: Any, default: bool = False) -> bool:
    """Parse booleans from JSON values without treating 'false' as truthy."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return default


def _is_local_origin(value: str) -> bool:
    """Return True when an Origin/Referer URL points at this machine."""
    if not value:
        return True
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and parsed.hostname in ("127.0.0.1", "localhost", "::1")


BROWSER_PLAYABLE_CONTAINERS: Set[str] = {
    ".mp3",
    ".wav",
    ".mp4",
    ".webm",
    ".aac",
    ".m4a",
    ".ogg",
    ".flac",
    ".opus",
    ".mov",
    ".m4v",
}


def _prepare_playable_media_path(
    source_file_path: str,
    session_id: str,
    pcm_data: Optional[bytes] = None,
    output_dir: Optional[Union[str, Path]] = None,
) -> str:
    """Guarantees a browser-playable audio path for HTML5 <audio> / WebView2.

    If source_file_path is an audio or video format natively supported by Chromium/WebView2
    (.mp3, .wav, .mp4, .webm, .aac, .m4a, .ogg, .flac, .opus, .mov, .m4v) and is accessible on disk, registers and
    returns that original source path directly for pristine quality and instant streaming.
    Otherwise (for non-browser containers like .mkv, .avi, .wmv), if pcm_data
    is available (or extracted on-the-fly), writes a clean 16kHz mono WAV speech track to output_dir,
    registers it, and returns its path.
    """
    ext = os.path.splitext(source_file_path)[1].lower()
    if ext in BROWSER_PLAYABLE_CONTAINERS and os.path.isfile(source_file_path):
        register_allowed_media_file(source_file_path)
        return source_file_path

    out_root = _output_root() if output_dir is None else Path(output_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if not pcm_data and os.path.isfile(source_file_path):
        try:
            from scriber.audio_extractor import AudioExtractor
            extractor = AudioExtractor()
            pcm_data, _ = extractor.extract_pcm16(source_file_path)
        except Exception as exc:
            logger.warning("Fallback audio extraction failed: %s", exc)

    if pcm_data:
        try:
            clean_base = re.sub(r"[^\w\.-]", "_", os.path.splitext(os.path.basename(source_file_path))[0])
            prefix = f"{session_id}_" if not clean_base.startswith(f"{session_id}_") else ""
            wav_path = str(out_root / f"{prefix}{clean_base}_speech.wav")
            expected_size = 44 + len(pcm_data)
            # Only reuse an exact, fully-written copy. A partially written or stale
            # file must never be handed to the player.
            if os.path.isfile(wav_path) and os.path.getsize(wav_path) == expected_size:
                register_allowed_media_file(wav_path)
                return wav_path
            tmp_path = wav_path + ".part"
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(pcm_data)
            os.replace(tmp_path, wav_path)
            register_allowed_media_file(wav_path)
            return wav_path
        except Exception as exc:
            logger.warning("Failed to write playable speech WAV: %s", exc)

    register_allowed_media_file(source_file_path)
    return source_file_path


def _compute_waveform_peaks(pcm_data: Optional[bytes], num_bars: int = 64) -> list:
    """Downsamples 16 kHz mono PCM into normalized RMS bars for the player waveform.

    Returns real audio energy (never a synthetic shape). Silence yields a short flat
    line instead of invented bars.
    """
    if not pcm_data or num_bars <= 0:
        return []
    usable = len(pcm_data) - (len(pcm_data) % 2)
    if usable < 4:
        return []
    samples = memoryview(pcm_data)[:usable]
    try:
        import numpy as np

        arr = np.frombuffer(samples, dtype="<i2").astype(np.float32) / 32768.0
        edges = np.linspace(0, arr.size, num_bars + 1).astype(np.int64)
        peaks = []
        for i in range(num_bars):
            a, b = int(edges[i]), int(edges[i + 1])
            if b <= a:
                peaks.append(0.0)
                continue
            block = arr[a:b]
            peaks.append(float(np.sqrt(np.mean(block * block))))
    except Exception:
        total = usable // 2
        edges = [int(total * i / num_bars) for i in range(num_bars + 1)]
        peaks = []
        for i in range(num_bars):
            a, b = edges[i] * 2, edges[i + 1] * 2
            if b <= a:
                peaks.append(0.0)
                continue
            acc = 0.0
            count = 0
            for off in range(a, b, 2):
                v = int.from_bytes(samples[off:off + 2], "little", signed=True) / 32768.0
                acc += v * v
                count += 1
            peaks.append(math.sqrt(acc / max(1, count)))

    positive = sorted(p for p in peaks if p > 1e-5)
    if not positive:
        return [0.03] * num_bars
    ref = positive[min(len(positive) - 1, int(len(positive) * 0.9))]
    if ref <= 0:
        return [0.03] * num_bars
    return [round(max(0.03, min(1.0, p / ref)), 4) for p in peaks]


def _attach_playback_payload(
    resp_data: Dict[str, Any],
    output: Any,
    source_path: str,
    output_dir: Optional[Union[str, Path]] = None,
    fallback_pcm: Optional[bytes] = None,
) -> None:
    """Attach a session-scoped playable track and its real waveform envelope.

    The PCM comes from the output object that this request produced, never from
    mutable pipeline state shared with concurrent jobs (voice previews, cloning,
    other uploads), which is what previously produced a truncated/mismatched WAV.
    """
    pcm = getattr(output, "audio_pcm16", None) or fallback_pcm or b""
    if pcm:
        resp_data["waveform_peaks"] = _compute_waveform_peaks(pcm, 64)
        resp_data["media_duration_sec"] = round(len(pcm) / 32000.0, 3)

    playable_path = _prepare_playable_media_path(
        source_path,
        getattr(output, "session_id", "session"),
        pcm_data=pcm or None,
        output_dir=output_dir,
    )
    resp_data["media_url"] = f"/api/media?path={urllib.parse.quote(playable_path)}"


class CancellationManager:
    """Manages active job cancellation signals and temporary file tracking."""

    def __init__(self):
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._temp_files: set[str] = set()

    def request_cancel(self) -> None:
        with self._lock:
            self._event.set()
        self.purge_temp_files()

    def reset(self) -> None:
        with self._lock:
            self._event.clear()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def register_temp_file(self, filepath: str) -> None:
        if not filepath:
            return
        with self._lock:
            self._temp_files.add(os.path.abspath(filepath))

    def unregister_temp_file(self, filepath: str) -> None:
        if not filepath:
            return
        with self._lock:
            self._temp_files.discard(os.path.abspath(filepath))

    def purge_temp_files(self) -> None:
        with self._lock:
            for p in list(self._temp_files):
                try:
                    if os.path.isfile(p):
                        os.remove(p)
                except Exception:
                    pass
            self._temp_files.clear()


_CANCEL_MGR = CancellationManager()

_ACTIVE_PROGRESS: Dict[str, Any] = {
    "active": False,
    "percent": 0,
    "stage": "idle",
    "phase": "Ready",
    "title": "Ready",
    "subtitle": "Standing by",
    "file_name": "",
    "current_time_sec": 0.0,
    "total_duration_sec": 0.0,
    "speed_factor": 0.0,
    "elapsed_sec": 0.0,
    "eta_sec": 0.0,
}
_PROGRESS_LOCK = threading.Lock()

def update_progress_state(data: Dict[str, Any]) -> None:
    """Updates global active progress state safely across threads."""
    clean = {}
    for k, v in data.items():
        if hasattr(v, "item"):
            clean[k] = v.item()
        elif isinstance(v, (int, float, str, bool, list, dict)) or v is None:
            clean[k] = v
        else:
            clean[k] = str(v)
    with _PROGRESS_LOCK:
        _ACTIVE_PROGRESS.update(clean)
        _ACTIVE_PROGRESS["active"] = True

def reset_progress_state(file_name: str = "") -> None:
    """Resets global progress state back to clean baseline."""
    with _PROGRESS_LOCK:
        _ACTIVE_PROGRESS.update({
            "active": False,
            "percent": 0,
            "stage": "idle",
            "phase": "Ready",
            "title": "Ready",
            "subtitle": "Standing by",
            "file_name": file_name,
            "current_time_sec": 0.0,
            "total_duration_sec": 0.0,
            "speed_factor": 0.0,
            "elapsed_sec": 0.0,
            "eta_sec": 0.0,
        })


class _PipelineDescriptor:
    """Lazily instantiates ScriberPipeline on first access."""

    def __init__(self):
        self._default = None
        self._lock = threading.Lock()

    def __get__(self, instance, owner=None):
        if instance is not None and "_instance_pipeline" in instance.__dict__:
            return instance.__dict__["_instance_pipeline"]
        if self._default is None:
            with self._lock:
                if self._default is None:
                    from scriber.pipeline import ScriberPipeline
                    self._default = ScriberPipeline()
        return self._default

    def __set__(self, instance, value):
        if instance is None:
            self._default = value
        else:
            instance.__dict__["_instance_pipeline"] = value


class ScriberHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for Scriber Web UI and REST API."""

    protocol_version = "HTTP/1.0"
    pipeline = _PipelineDescriptor()

    def _request_allowed(self) -> bool:
        """Reject cross-site browser requests and non-local Host headers.

        The UI is served from the same localhost origin, so it never needs a
        wildcard CORS policy. This blocks a malicious website from driving the
        local API through the user's browser.
        """
        host_header = self.headers.get("Host") or ""
        host = urllib.parse.urlparse("//" + host_header).hostname or ""
        if host and host.lower() not in ("127.0.0.1", "localhost", "::1"):
            return False
        origin = self.headers.get("Origin") or ""
        if origin and not _is_local_origin(origin):
            return False
        referer = self.headers.get("Referer") or ""
        if referer and not _is_local_origin(referer):
            return False
        if (self.headers.get("Sec-Fetch-Site") or "").lower() == "cross-site":
            return False
        return True

    def _send_cors_origin(self) -> None:
        """Echo only a validated loopback Origin; same-origin requests need no header."""
        origin = self.headers.get("Origin") or ""
        if origin and _is_local_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self):
        """Handles preflight requests with CORS headers."""
        if not self._request_allowed():
            self._send_json_response(403, {"error": "Forbidden origin"})
            return
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, OPTIONS")
        self._send_cors_origin()
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Range, Content-Type, Accept, Authorization")
        self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def do_HEAD(self):
        """Handles HEAD requests for media probing, range probing, and health checks."""
        self.do_GET(head_only=True)

    def do_GET(self, head_only: bool = False):
        if not self._request_allowed():
            self._send_json_response(403, {"error": "Forbidden origin"})
            return
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._serve_embedded_ui(head_only=head_only)
        elif path in ("/favicon.ico", "/icon.ico"):
            self._serve_icon(head_only=head_only)
        elif path.startswith("/assets/") or path.startswith("/api/assets/"):
            asset_filename = os.path.basename(path)
            from scriber.assets import get_asset_path
            asset_file = get_asset_path(asset_filename)
            if asset_file.exists():
                self._serve_static_file(str(asset_file), head_only=head_only)
            else:
                self._send_json_response(404, {"error": "Asset not found"})
        elif path.startswith("/static/"):
            from scriber.web.ui import get_static_dir
            static_dir = get_static_dir()
            rel_name = path[len("/static/"):].lstrip("/\\")
            static_file = (static_dir / rel_name).resolve()
            if static_file.is_file() and _is_within(str(static_file), (static_dir.resolve(),)):
                self._serve_static_file(str(static_file), head_only=head_only)
            else:
                self._send_json_response(404, {"error": "Static file not found"})
        elif path == "/api/health":
            self._send_json_response(200, {"status": "ok", "app": "Scriber"})
        elif path == "/api/media":
            query = urllib.parse.parse_qs(parsed.query)
            media_path = query.get("path", [""])[0]
            try:
                candidate = Path(media_path).resolve() if media_path else None
            except (OSError, ValueError):
                candidate = None
            ext = candidate.suffix.lower() if candidate else ""
            if (
                candidate is not None
                and candidate.is_file()
                and (
                    _is_within(str(candidate), _media_roots())
                    or is_allowed_media_file(candidate)
                    or (self.pipeline and str(candidate) == str(getattr(self.pipeline, "last_file_path", None)))
                    or (self._check_host_origin() and ext in BROWSER_PLAYABLE_CONTAINERS)
                )
            ):
                register_allowed_media_file(candidate)
                self._serve_static_file(str(candidate), head_only=head_only)
            else:
                self._send_json_response(404, {"error": "Media file not found"})
        elif path == "/api/progress":
            with _PROGRESS_LOCK:
                resp = dict(_ACTIVE_PROGRESS)
            self._send_json_response(200, resp)
        elif path == "/api/hardware":
            from scriber.hardware import get_hardware_capabilities
            caps = get_hardware_capabilities()
            self._send_json_response(200, caps.to_dict())
        elif path == "/api/desktop/info":
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
            from scriber.validator import ResultValidator
            results = ResultValidator.run_benchmark_suite()
            self._send_json_response(200, results)
        elif path == "/api/models":
            from scriber.transcription_engine import TOP_TRANSCRIBE_MODELS, get_model_evaluation_matrix
            from scriber.voice_clone import TOP_VOICE_MODELS
            self._send_json_response(200, {
                "transcribe_models": TOP_TRANSCRIBE_MODELS,
                "voice_models": TOP_VOICE_MODELS,
                "studio_voices": VoiceCloner.get_studio_voices(),
                "evaluation_matrix": get_model_evaluation_matrix(),
            })
        elif path == "/api/voices":
            self._send_json_response(200, {
                "voices": VoiceCloner.get_studio_voices(),
                "total": len(VoiceCloner.get_studio_voices()),
            })
        elif path == "/api/performance":
            from scriber.hardware import get_system_performance_telemetry
            self._send_json_response(200, get_system_performance_telemetry())
        elif path == "/api/voice/credentials":
            vm_key = os.environ.get("VOICEMAKER_API_KEY", "")
            el_key = os.environ.get("ELEVENLABS_API_KEY", "")
            vm_active = bool(vm_key)
            el_active = bool(el_key)
            self._send_json_response(200, {
                "voicemaker_configured": vm_active,
                "elevenlabs_configured": el_active,
                "voicemaker_masked_key": (vm_key[:4] + "..." + vm_key[-4:]) if len(vm_key) >= 8 else ("***" if vm_key else ""),
                "elevenlabs_masked_key": (el_key[:4] + "..." + el_key[-4:]) if len(el_key) >= 8 else ("***" if el_key else ""),
                "zero_financial_exposure": True,
                "note": "Stored in process memory only; not used by local synthesis engines.",
            })
        elif path == "/api/agents":
            swarm = CouncilAgentSwarm()
            agents = [a.to_dict() for a in swarm.get_registered_agents()]
            self._send_json_response(200, {
                "agents": agents,
                "framework": "scriber-native",
                "framework_url": "https://github.com/LakshyaPrasher/Scriber",
                "count": len(agents),
            })
        elif path == "/api/council/swarm":
            swarm = CouncilAgentSwarm()
            agents = [a.to_dict() for a in swarm.get_registered_agents()]
            telemetry = [t.to_dict() for t in getattr(self.pipeline.supreme_council, "swarm", swarm).last_telemetry]
            self._send_json_response(200, {
                "agents": agents,
                "telemetry": telemetry,
                "framework": "scriber-native",
            })
        elif path == "/api/plugin/manifest":
            manifest_file = Path(__file__).resolve().parent.parent.parent / ".antigravity" / "plugins" / "scriber" / "plugin.json"
            if manifest_file.exists():
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                self._send_json_response(200, manifest_data)
            else:
                self._send_json_response(404, {"error": "Plugin manifest not found"})
        elif path == "/api/info":
            from scriber.transcription_engine import TOP_LEVERAGED_REPOS
            swarm = CouncilAgentSwarm()
            self._send_json_response(200, {
                "name": "Scriber",
                "version": __version__,
                "description": "High-Performance Speech Intelligence, Diarization, and Voice Studio",
                "repos": TOP_LEVERAGED_REPOS,
                "agent_swarm_count": len(swarm.get_registered_agents()),
                "framework": "scriber-native",
            })
        else:
            # No arbitrary CWD file serving: only the embedded UI, /static, and
            # registered media are reachable. Everything else is a 404.
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _serve_icon(self, head_only: bool = False):
        """Serves the Scriber brand icon (ICO format)."""
        try:
            from scriber.assets import get_icon_path
            icon_path = get_icon_path()
            if icon_path.exists():
                self._serve_static_file(str(icon_path), head_only=head_only)
                return
        except Exception:
            pass
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _serve_static_file(self, filepath: str, head_only: bool = False):
        """Serves static audio, video, image, or document files with full HTTP Range (206) seeking support."""
        fp_lower = filepath.lower()
        if fp_lower.endswith(".wav"):
            mime = "audio/wav"
        elif fp_lower.endswith(".mp3"):
            mime = "audio/mpeg"
        elif fp_lower.endswith(".mp4") or fp_lower.endswith(".m4v"):
            mime = "video/mp4"
        elif fp_lower.endswith(".mov"):
            mime = "video/quicktime"
        elif fp_lower.endswith(".m4a"):
            mime = "audio/mp4"
        elif fp_lower.endswith(".aac"):
            mime = "audio/aac"
        elif fp_lower.endswith(".ogg"):
            mime = "audio/ogg"
        elif fp_lower.endswith(".opus"):
            mime = "audio/opus"
        elif fp_lower.endswith(".webm"):
            mime = "audio/webm"
        elif fp_lower.endswith(".flac"):
            mime = "audio/flac"
        else:
            mime, _ = mimetypes.guess_type(filepath)
            if not mime:
                if fp_lower.endswith(".png"):
                    mime = "image/png"
                else:
                    mime = "application/octet-stream"

        try:
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", "0")
                self.send_header("Accept-Ranges", "bytes")
                self._send_cors_origin()
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                return

            range_header = self.headers.get("Range")

            start = 0
            end = file_size - 1
            status_code = 200

            if range_header and range_header.strip().startswith("bytes="):
                range_val = range_header.strip()[6:]
                parts = range_val.split("-", 1)
                try:
                    if parts[0]:
                        start = int(parts[0])
                        if len(parts) > 1 and parts[1]:
                            end = int(parts[1])
                    elif len(parts) > 1 and parts[1]:
                        suffix_len = int(parts[1])
                        start = max(0, file_size - suffix_len)
                        end = file_size - 1
                    if start >= file_size:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{file_size}")
                        self.send_header("Content-Length", "0")
                        self._send_cors_origin()
                        self.send_header("Connection", "close")
                        self.end_headers()
                        self.close_connection = True
                        return
                    end = min(end, file_size - 1)
                    if start <= end:
                        status_code = 206
                    else:
                        start = 0
                        end = file_size - 1
                except ValueError:
                    start = 0
                    end = file_size - 1

            content_length = max(0, (end - start) + 1)

            self.send_response(status_code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(content_length))
            self.send_header("Accept-Ranges", "bytes")
            if status_code == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Range, Content-Type, Accept")
            self.send_header("Access-Control-Expose-Headers", "Content-Range, Content-Length, Accept-Ranges")
            self._send_cors_origin()
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Connection", "close")
            self.end_headers()

            if head_only:
                self.close_connection = True
                return

            with open(filepath, "rb") as f:
                if start > 0:
                    f.seek(start)
                bytes_left = content_length
                while bytes_left > 0:
                    read_amount = min(65536, bytes_left)
                    chunk = f.read(read_amount)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    bytes_left -= len(chunk)
            self.wfile.flush()
            self.close_connection = True
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            # Client closed the byte-range connection or scrubbed to another timestamp
            self.close_connection = True
        except Exception as e:
            try:
                self._send_json_response(500, {"error": str(e)})
            except Exception:
                pass

    def do_POST(self):
        if not self._request_allowed():
            self._send_json_response(403, {"error": "Forbidden origin"})
            return
        try:
            declared_length = int(self.headers.get("Content-Length", 0) or 0)
        except (TypeError, ValueError):
            declared_length = 0
        if declared_length > MAX_UPLOAD_SIZE:
            self._send_json_response(413, {"error": "File size exceeds 1 GB limit."})
            return
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
        elif path == "/api/cancel":
            self._handle_cancel()
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _handle_cancel(self):
        """Cancels active processing jobs, purges temporary files, and resets progress."""
        _CANCEL_MGR.request_cancel()
        reset_progress_state()
        with _PROGRESS_LOCK:
            _ACTIVE_PROGRESS.update({
                "active": False,
                "stage": "cancelled",
                "phase": "Cancelled",
                "title": "Operation Cancelled",
                "subtitle": "Job aborted by user; temporary files purged",
            })
        self._send_json_response(200, {
            "status": "cancelled",
            "success": True,
            "cancelled": True,
            "message": "Active job cancelled successfully",
        })

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
        """Redacts sensitive PII from transcript segments or arbitrary text."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            req_data = json.loads(body_bytes.decode("utf-8"))
            mask_mode = req_data.get("mask_mode", "partial")
            if mask_mode not in ("partial", "full"):
                mask_mode = "partial"
            from scriber.pii_security import PIISecurityOfficer
            officer = PIISecurityOfficer()

            # Preferred API: sanitize the transcript's segments and return the
            # same shape the UI renders. The legacy {"text": ...} contract is
            # kept below for backwards compatibility.
            segments_payload = req_data.get("segments")
            if isinstance(segments_payload, list) and segments_payload:
                from scriber.models import AudioSegment, WordTimestamp

                segments = []
                for idx, raw in enumerate(segments_payload):
                    if not isinstance(raw, dict):
                        continue
                    words = []
                    for w in raw.get("words", []) or []:
                        if isinstance(w, dict):
                            raw_prob = w.get("probability")
                            prob_val = float(raw_prob) if raw_prob not in (None, "") else None
                            words.append(
                                WordTimestamp(
                                    word=str(w.get("word", "")),
                                    start=float(w.get("start", 0.0) or 0.0),
                                    end=float(w.get("end", 0.0) or 0.0),
                                    probability=prob_val,
                                )
                            )
                    segments.append(
                        AudioSegment(
                            id=int(raw.get("id", idx) or idx),
                            seek=int(raw.get("seek", 0) or 0),
                            start=float(raw.get("start", 0.0) or 0.0),
                            end=float(raw.get("end", 0.0) or 0.0),
                            text=str(raw.get("text", "")),
                            speaker=raw.get("speaker"),
                            words=words,
                        )
                    )
                sanitized, report = officer.sanitize_segments(segments, mask_mode=mask_mode)
                self._send_json_response(200, {
                    "sanitized_segments": [
                        {
                            "id": s.id,
                            "start": s.start,
                            "end": s.end,
                            "speaker": s.speaker,
                            "text": s.text,
                        }
                        for s in sanitized
                    ],
                    "report": report.to_dict(),
                    "entities_found": report.entities_found,
                    "redacted_count": report.redacted_count,
                    "audit_log": report.audit_log,
                })
                return

            text = req_data.get("text", "")
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
            import time
            home = Path.home()
            dest_dir = home / ".gemini" / "config" / "plugins" / "scriber"
            src_dir = Path(__file__).resolve().parent.parent.parent / ".antigravity" / "plugins" / "scriber"
            if not src_dir.exists():
                self._send_json_response(404, {"error": "Plugin source bundle not found"})
                return
            if dest_dir.exists():
                backup_dir = dest_dir.with_name(f"scriber.bak-{int(time.time())}")
                shutil.move(str(dest_dir), str(backup_dir))
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_dir, dest_dir)
            self._send_json_response(200, {
                "success": True,
                "status": "success",
                "message": "Scriber plugin successfully installed into Google Antigravity",
                "path": str(dest_dir),
                "target_dir": str(dest_dir),
            })
        except Exception as e:
            self._send_json_response(500, {"error": str(e), "success": False})

    def _handle_media_upload(self):
        """Handles upload of video/audio file via multipart form-data or direct JSON file_path."""
        tmp_path = None
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            if content_length <= 0:
                self._send_json_response(400, {"error": "Content-Length header is missing or empty"})
                return

            if content_length > MAX_UPLOAD_SIZE:
                self._send_json_response(413, {"error": "File size exceeds 1 GB limit."})
                return

            body_bytes = self.rfile.read(content_length)

            # Support direct JSON payload: {"file_path": "path/to/media.mp3", "task": "translate", "model": "turbo"}
            if content_type.startswith("application/json"):
                data = json.loads(body_bytes.decode("utf-8"))
                file_path_arg = data.get("file_path", "")
                if not file_path_arg or not os.path.isfile(file_path_arg):
                    self._send_json_response(400, {"error": f"File '{file_path_arg}' not found on server"})
                    return
                register_allowed_media_file(file_path_arg)
                redact_pii_val = _as_bool(data.get("redact_pii", False))
                max_dur_raw = data.get("max_duration")
                max_dur_val = float(max_dur_raw) if max_dur_raw not in (None, "", 0) else None
                _CANCEL_MGR.reset()
                reset_progress_state(file_name=os.path.basename(file_path_arg))
                try:
                    output = self.pipeline.process_file(
                        file_path=file_path_arg,
                        task=data.get("task", "translate"),
                        language=None if data.get("language") in ("auto", "none", "", None) else data.get("language"),
                        reference_text=data.get("reference_text"),
                        ground_truth_hint=data.get("ground_truth_hint"),
                        demo_mode=_as_bool(data.get("demo_mode", False)),
                        model=data.get("model", "turbo"),
                        redact_pii=redact_pii_val,
                        progress_callback=update_progress_state,
                        max_duration=max_dur_val,
                        cancel_checker=_CANCEL_MGR.is_cancelled,
                    )
                except JobCancelledException:
                    _CANCEL_MGR.purge_temp_files()
                    reset_progress_state()
                    self._send_json_response(200, {
                        "status": "cancelled",
                        "message": "Processing cancelled by user request",
                        "cancelled": True,
                    })
                    return
                except TranscriptionUnavailableError as exc:
                    reset_progress_state()
                    self._send_json_response(503, {
                        "error": str(exc),
                        "error_code": "transcription_unavailable",
                    })
                    return
                finally:
                    reset_progress_state()
                    _CANCEL_MGR.reset()
                output.video_source = os.path.basename(file_path_arg)
                try:
                    self.pipeline._export_all_formats(output, str(_output_root()), ["json", "md", "srt", "vtt", "txt", "html"])
                except Exception:
                    pass
                resp_data = output.to_dict()
                resp_data["exports"] = {
                    "txt": ScriberExporter.to_txt(output),
                    "markdown": ScriberExporter.to_markdown(output),
                    "srt": ScriberExporter.to_srt(output),
                    "vtt": ScriberExporter.to_vtt(output),
                }
                _attach_playback_payload(
                    resp_data,
                    output,
                    file_path_arg,
                    fallback_pcm=getattr(self.pipeline, "last_pcm_data", None),
                )
                self._send_json_response(200, resp_data)
                return

            if not content_type.startswith("multipart/form-data"):
                self._send_json_response(400, {"error": "Content-Type must be multipart/form-data or application/json"})
                return

            # High-performance multipart boundary parsing with zero memory duplication
            boundary = None
            for param in content_type.split(";"):
                param = param.strip()
                if param.lower().startswith("boundary="):
                    boundary = param.split("=", 1)[1].strip().strip('"').encode("latin-1")
                    break

            file_data = None
            filename = "uploaded_media.mp4"
            task = "translate"
            language = "auto"
            ref_text = None
            ground_truth_hint = None
            demo_mode = False
            file_path_param = None
            model = "turbo"
            redact_pii = False

            if boundary and (b"--" + boundary) in body_bytes:
                marker = b"--" + boundary
                parts = body_bytes.split(marker)
                for p in parts:
                    if not p or p == b"--\r\n" or p == b"--":
                        continue
                    header_blob, sep, body_part = p.partition(b"\r\n\r\n")
                    if not sep:
                        continue
                    if body_part.endswith(b"\r\n"):
                        body_part = body_part[:-2]

                    header_str = header_blob.decode("latin-1", errors="replace")
                    cd_match = re.search(r'Content-Disposition:\s*form-data;\s*name="([^"]+)"(?:;\s*filename="([^"]+)")?', header_str, re.IGNORECASE)
                    if not cd_match:
                        continue
                    part_name = cd_match.group(1)
                    part_filename = cd_match.group(2)

                    if part_name == "file":
                        file_data = body_part
                        if part_filename:
                            filename = part_filename
                    elif part_name == "file_path":
                        file_path_param = body_part.decode("utf-8", errors="replace").strip()
                    elif part_name == "task":
                        task = body_part.decode("utf-8", errors="replace").strip() or "translate"
                    elif part_name == "language":
                        language = body_part.decode("utf-8", errors="replace").strip() or "auto"
                    elif part_name == "model":
                        model = body_part.decode("utf-8", errors="replace").strip() or "turbo"
                    elif part_name == "reference_text":
                        ref_text = body_part.decode("utf-8", errors="replace").strip() or None
                    elif part_name == "ground_truth_hint":
                        ground_truth_hint = body_part.decode("utf-8", errors="replace").strip() or None
                    elif part_name == "demo_mode":
                        demo_mode = _as_bool(body_part.decode("utf-8", errors="replace").strip())
                    elif part_name == "redact_pii":
                        val = body_part.decode("utf-8", errors="replace").strip().lower()
                        redact_pii = _as_bool(val)
            else:
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
                    elif name == "ground_truth_hint":
                        payload = part.get_payload(decode=True)
                        if payload:
                            ground_truth_hint = payload.decode("utf-8", errors="replace").strip() or None
                    elif name == "demo_mode":
                        payload = part.get_payload(decode=True)
                        if payload:
                            demo_mode = _as_bool(payload.decode("utf-8", errors="replace").strip())
                    elif name == "redact_pii":
                        payload = part.get_payload(decode=True)
                        if payload:
                            val = payload.decode("utf-8", errors="replace").strip().lower()
                            redact_pii = _as_bool(val)

            # Handle file_path parameter if provided and valid
            if file_path_param and os.path.isfile(file_path_param):
                register_allowed_media_file(file_path_param)
                _CANCEL_MGR.reset()
                reset_progress_state(file_name=os.path.basename(file_path_param))
                try:
                    output = self.pipeline.process_file(
                        file_path=file_path_param,
                        task=task,
                        language=None if language in ("auto", "none", "", None) else language,
                        reference_text=ref_text,
                        ground_truth_hint=ground_truth_hint,
                        demo_mode=demo_mode,
                        model=model,
                        redact_pii=redact_pii,
                        progress_callback=update_progress_state,
                        cancel_checker=_CANCEL_MGR.is_cancelled,
                    )
                except JobCancelledException:
                    _CANCEL_MGR.purge_temp_files()
                    reset_progress_state()
                    self._send_json_response(200, {
                        "status": "cancelled",
                        "message": "Processing cancelled by user request",
                        "cancelled": True,
                    })
                    return
                except TranscriptionUnavailableError as exc:
                    reset_progress_state()
                    self._send_json_response(503, {
                        "error": str(exc),
                        "error_code": "transcription_unavailable",
                    })
                    return
                finally:
                    reset_progress_state()
                    _CANCEL_MGR.reset()
                output.video_source = os.path.basename(file_path_param)
                try:
                    self.pipeline._export_all_formats(output, str(_output_root()), ["json", "md", "srt", "vtt", "txt", "html"])
                except Exception:
                    pass
                resp_data = output.to_dict()
                resp_data["exports"] = {
                    "txt": ScriberExporter.to_txt(output),
                    "markdown": ScriberExporter.to_markdown(output),
                    "srt": ScriberExporter.to_srt(output),
                    "vtt": ScriberExporter.to_vtt(output),
                }
                if file_path_param:
                    _attach_playback_payload(
                        resp_data,
                        output,
                        file_path_param,
                        fallback_pcm=getattr(self.pipeline, "last_pcm_data", None),
                    )
                self._send_json_response(200, resp_data)
                return

            if not file_data:
                self._send_json_response(400, {"error": "No file uploaded under form key 'file'"})
                return

            ext = os.path.splitext(filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(file_data)
            register_allowed_media_file(tmp_path)

            _CANCEL_MGR.reset()
            _CANCEL_MGR.register_temp_file(tmp_path)
            reset_progress_state(file_name=filename)
            try:
                output = self.pipeline.process_file(
                    file_path=tmp_path,
                    task=task,
                    language=None if language in ("auto", "none", "", None) else language,
                    reference_text=ref_text,
                    ground_truth_hint=ground_truth_hint,
                    demo_mode=demo_mode,
                    model=model,
                    redact_pii=redact_pii,
                    progress_callback=update_progress_state,
                    cancel_checker=_CANCEL_MGR.is_cancelled,
                )
            except JobCancelledException:
                _CANCEL_MGR.purge_temp_files()
                reset_progress_state()
                self._send_json_response(200, {
                    "status": "cancelled",
                    "message": "Processing cancelled by user request",
                    "cancelled": True,
                })
                return
            except TranscriptionUnavailableError as exc:
                reset_progress_state()
                self._send_json_response(503, {
                    "error": str(exc),
                    "error_code": "transcription_unavailable",
                })
                return
            finally:
                reset_progress_state()
                _CANCEL_MGR.unregister_temp_file(tmp_path)
                _CANCEL_MGR.reset()
            output.video_source = filename
            try:
                self.pipeline._export_all_formats(output, str(_output_root()), ["json", "md", "srt", "vtt", "txt", "html"])
            except Exception:
                pass
            resp_data = output.to_dict()
            resp_data["exports"] = {
                "txt": ScriberExporter.to_txt(output),
                "markdown": ScriberExporter.to_markdown(output),
                "srt": ScriberExporter.to_srt(output),
                "vtt": ScriberExporter.to_vtt(output),
            }
            # Save uploaded media file to persistent output directory
            try:
                export_dir = str(_output_root())
                os.makedirs(export_dir, exist_ok=True)
                clean_fname = re.sub(r"[^\w\.-]", "_", os.path.basename(filename))
                persistent_path = os.path.join(export_dir, f"{output.session_id}_{clean_fname}")
                shutil.copy2(tmp_path, persistent_path)
                _attach_playback_payload(
                    resp_data,
                    output,
                    persistent_path,
                    output_dir=export_dir,
                    fallback_pcm=getattr(self.pipeline, "last_pcm_data", None),
                )
            except Exception as exc:
                logger.warning("Could not persist uploaded media: %s", exc)

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
                ground_truth_hint=demo_text,
                demo_mode=True,
            )
            resp_data = output.to_dict()
            resp_data["audio_base64"] = "data:audio/wav;base64," + base64.b64encode(demo_audio).decode("ascii")
            try:
                export_dir = _output_root()
                export_dir.mkdir(parents=True, exist_ok=True)
                demo_wav_path = str(export_dir / f"{output.session_id}_demo_speech.wav")
                with wave.open(demo_wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(demo_audio)
                register_allowed_media_file(demo_wav_path)
                resp_data["media_url"] = f"/api/media?path={urllib.parse.quote(demo_wav_path)}"
            except Exception as exc:
                logger.warning("Could not persist demo audio: %s", exc)
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
                from scriber.voice_clone import VoiceProfiler
                profile = VoiceProfiler._empty_profile("Speaker_1")

            # Never seed cloning from server-wide state: the client sends the exact
            # reference for this speaker (file_path or reference_audio), and a missing
            # reference must synthesize from the profile alone.
            ref_pcm = None

            # Direct file_path reference support (bypasses base64 upload overhead)
            ref_file_path = req_data.get("file_path") or req_data.get("reference_file_path")
            if ref_file_path and os.path.isfile(ref_file_path):
                try:
                    extracted_pcm, _ = self.pipeline.audio_extractor.extract_pcm16(ref_file_path, max_duration=45.0)
                    if extracted_pcm and len(extracted_pcm) > 320:
                        max_bytes = 16000 * 2 * 20
                        ref_pcm = extracted_pcm[:max_bytes] if len(extracted_pcm) > max_bytes else extracted_pcm
                except Exception as e:
                    logger.debug(f"Direct file_path extraction for voice cloning error: {e}")

            # If client provided reference audio base64, decode directly to guarantee accurate timbre match
            ref_b64 = req_data.get("reference_audio") or req_data.get("reference_base64")
            if ref_b64 and isinstance(ref_b64, str) and len(ref_b64.strip()) > 50:
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
                            # Cap to 20s maximum to prevent buffer bloat
                            max_bytes = 16000 * 2 * 20
                            if len(extracted_pcm) > max_bytes:
                                extracted_pcm = extracted_pcm[:max_bytes]
                            ref_pcm = extracted_pcm
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
            volume = float(req_data.get("volume", 1.0))
            _CANCEL_MGR.reset()
            try:
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
                    volume=volume,
                    cancel_checker=_CANCEL_MGR.is_cancelled,
                )
            except JobCancelledException:
                _CANCEL_MGR.purge_temp_files()
                self._send_json_response(200, {
                    "status": "cancelled",
                    "message": "Voice synthesis cancelled by user request",
                    "cancelled": True,
                })
                return
            finally:
                _CANCEL_MGR.reset()

            # "Voice match" is only measurable against a reference clip. Without one,
            # report it as unmeasured instead of presenting profile conformity as a
            # voice-identity match.
            resp = result.to_dict()
            if not ref_pcm:
                resp["similarity_score"] = None
                resp["similarity_percentage"] = None
                resp["similarity_measured"] = False

            self._send_json_response(200, resp)

        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_voice_profiling(self):
        """Extracts speaker acoustic VoiceProfile from an uploaded reference audio/video file or local path."""
        tmp_path = None
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b""

            file_path_param = None
            file_data = None
            filename = "reference_voice.mp3"
            speaker_name = "Custom Voice"

            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if "file_path" in query_params:
                file_path_param = query_params["file_path"][0]

            if "application/json" in content_type and body_bytes:
                req_json = json.loads(body_bytes.decode("utf-8", errors="replace"))
                file_path_param = req_json.get("file_path") or file_path_param
                speaker_name = req_json.get("speaker") or speaker_name
                if file_path_param:
                    filename = os.path.basename(file_path_param)
            elif content_type.startswith("multipart/form-data") and body_bytes:
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
                            filename = fname
                    elif name == "file_path":
                        payload = part.get_payload(decode=True)
                        if payload:
                            file_path_param = payload.decode("utf-8", errors="replace").strip()
                    elif name == "speaker":
                        payload = part.get_payload(decode=True)
                        if payload:
                            speaker_name = payload.decode("utf-8", errors="replace").strip() or speaker_name

            if file_path_param and os.path.isfile(file_path_param):
                target_file = file_path_param
                filename = os.path.basename(file_path_param)
            elif file_data:
                ext = os.path.splitext(filename)[1] or ".mp3"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp_path = tmp.name
                    tmp.write(file_data)
                target_file = tmp_path
            else:
                self._send_json_response(400, {"error": "No file or file_path provided for voice profiling"})
                return

            register_allowed_media_file(target_file)

            pcm_data, meta = self.pipeline.audio_extractor.extract_pcm16(target_file, max_duration=45.0)
            from scriber.voice_clone import VoiceProfiler
            profile = VoiceProfiler.profile_from_pcm16(pcm_data, speaker_id=speaker_name)

            # Extract a representative 15s high-RMS speech slice to avoid multi-megabyte base64 payload freezes
            preview_pcm = pcm_data
            bytes_15s = 16000 * 2 * 15
            if len(pcm_data) > bytes_15s:
                try:
                    import numpy as np
                    window_samples = 16000 * 15
                    hop_samples = 16000
                    arr = np.frombuffer(pcm_data, dtype=np.int16)
                    best_start = 0
                    best_energy = -1.0
                    for start in range(0, max(1, len(arr) - window_samples + 1), hop_samples):
                        chunk = arr[start : start + window_samples].astype(np.float32)
                        energy = float(np.mean(chunk ** 2))
                        if energy > best_energy:
                            best_energy = energy
                            best_start = start
                    preview_pcm = arr[best_start : best_start + window_samples].tobytes()
                except Exception:
                    preview_pcm = pcm_data[:bytes_15s]

            # The preview audio travels back to the client in the response; cloning
            # uses that explicit payload or the selected file path, not server state.
            self.pipeline.reference_filename = filename

            from scriber.audio_editor import AudioEditor
            mp3_bytes = AudioEditor.encode_mp3(preview_pcm, sr=16000, channels=1, bit_rate=192000)
            b64_str = base64.b64encode(mp3_bytes).decode("ascii")

            preview_dur = len(preview_pcm) / (16000.0 * 2.0)
            self._send_json_response(200, {
                "profile": profile.to_dict(),
                "filename": filename,
                "duration": round(preview_dur, 3),
                "total_duration": round(meta.duration, 3),
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
            file_path_arg = None

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
                    elif name == "file_path":
                        val = part.get_payload(decode=True)
                        if val:
                            file_path_arg = val.decode("utf-8", errors="replace").strip() or None
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

                file_path_arg = data.get("file_path") or data.get("source_path") or None

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
                _CANCEL_MGR.register_temp_file(tmp_path)
                pcm_data, _ = self.pipeline.audio_extractor.extract_pcm16(tmp_path)
            elif file_path_arg:
                # Session-safe source: the client sends the playable path that was
                # registered for this result, so editing never falls back to another
                # job's shared buffer.
                if os.path.isfile(file_path_arg) and is_allowed_media_file(file_path_arg):
                    pcm_data, _ = self.pipeline.audio_extractor.extract_pcm16(file_path_arg)

            if _CANCEL_MGR.is_cancelled():
                raise JobCancelledException("Audio editing cancelled by user")

            # Never trust a client-supplied output filename: strip directories and
            # restrict the character set before it reaches the audio editor.
            filename = os.path.basename(str(filename or "scriber_edited_audio.mp3")).strip()
            filename = re.sub(r"[^A-Za-z0-9_.\- ]", "_", filename) or "scriber_edited_audio.mp3"
            if not filename.lower().endswith(".mp3"):
                filename += ".mp3"

            res = self.pipeline.edit_audio(
                pcm_data=pcm_data,
                volume=volume,
                pitch_semitones=pitch_semitones,
                start_sec=start_sec,
                end_sec=end_sec,
                filename=filename,
                output_dir=str(_output_root()),
            )
            self._send_json_response(200, res)

        except JobCancelledException:
            _CANCEL_MGR.purge_temp_files()
            self._send_json_response(200, {
                "status": "cancelled",
                "message": "Audio editing cancelled by user request",
                "cancelled": True,
            })
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})
        finally:
            if tmp_path:
                _CANCEL_MGR.unregister_temp_file(tmp_path)
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
            _CANCEL_MGR.reset()

    def _handle_desktop_reveal(self):
        """Reveals an exported file or opens the managed output directory."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            out_root = _output_root()
            target = data.get("path") or data.get("file") or str(out_root)
            try:
                abs_path = str(Path(target).resolve())
            except (OSError, ValueError):
                self._send_json_response(400, {"error": "Invalid path"})
                return
            if not _is_within(abs_path, (out_root,)):
                self._send_json_response(403, {"error": "Path is outside the output directory"})
                return
            if not os.path.exists(abs_path):
                if os.path.normcase(abs_path) == os.path.normcase(str(out_root)):
                    out_root.mkdir(parents=True, exist_ok=True)
                else:
                    self._send_json_response(404, {"error": "Path not found"})
                    return

            opened = False
            if sys.platform == "win32":
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                if os.path.isfile(abs_path):
                    subprocess.Popen(["explorer.exe", f"/select,{abs_path}"], creationflags=flags, startupinfo=si)
                    opened = True
                else:
                    os.startfile(abs_path)
                    opened = True
            elif sys.platform == "darwin":
                subprocess.Popen(["open", abs_path])
                opened = True
            else:
                subprocess.Popen(["xdg-open", abs_path])
                opened = True

            self._send_json_response(200, {"success": True, "path": abs_path, "opened": opened})
        except Exception as e:
            self._send_json_response(500, {"error": str(e)})

    def _handle_desktop_save_file(self):
        """Saves text or base64 binary content into the managed output directory."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self._send_json_response(400, {"error": "Content-Length is required"})
                return
            if content_length > 50 * 1024 * 1024:
                self._send_json_response(413, {"error": "Content is too large"})
                return
            body_bytes = self.rfile.read(content_length)
            data = json.loads(body_bytes.decode("utf-8"))
            filename = os.path.basename(str(data.get("filename", "transcript_export.txt")))
            filename = re.sub(r"[^\w\.\- ]", "_", filename).strip(" .")
            if not filename or filename in (".", ".."):
                filename = "transcript_export.txt"
            reserved = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
            if os.path.splitext(filename)[0].upper() in reserved:
                filename = f"_{filename}"
            content = data.get("content", "")
            out_dir = _output_root()
            out_dir.mkdir(parents=True, exist_ok=True)
            target_path = (out_dir / filename).resolve()
            if not _is_within(str(target_path), (out_dir,)):
                self._send_json_response(400, {"error": "Invalid output path"})
                return

            if _as_bool(data.get("is_base64", False)):
                raw = base64.b64decode(content, validate=True)
                target_path.write_bytes(raw)
            else:
                target_path.write_text(str(content), encoding="utf-8")

            self._send_json_response(200, {"success": True, "saved_path": str(target_path)})
        except Exception as e:
            logger.exception("Failed to save desktop file")
            self._send_json_response(500, {"error": str(e)})

    def _send_json_response(self, status: int, data: Dict[str, Any]):
        """Encodes and transmits JSON response with chunked socket writes to prevent buffer stalls."""
        body = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            chunk_size = 65536
            for offset in range(0, len(body), chunk_size):
                self.wfile.write(body[offset : offset + chunk_size])
            self.wfile.flush()
        except Exception:
            pass
        self.close_connection = True

    def _serve_embedded_ui(self, head_only: bool = False):
        """Serves the standalone responsive dashboard with dynamic live source hot-reloading."""
        import importlib
        import importlib.util
        import scriber.web.ui
        html = None

        # Check local source tree first for live hot-reload
        for candidate in [
            Path(__file__).resolve().parent / "ui.py",
            Path.cwd() / "scriber" / "web" / "ui.py",
        ]:
            if candidate.is_file():
                try:
                    spec = importlib.util.spec_from_file_location("scriber_ui_live", str(candidate))
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "get_embedded_html"):
                            html = mod.get_embedded_html()
                            break
                except Exception:
                    pass

        if not html:
            try:
                importlib.reload(scriber.web.ui)
                html = scriber.web.ui.get_embedded_html()
            except Exception:
                html = get_embedded_html()

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Connection", "close")
        self.end_headers()
        if head_only:
            self.close_connection = True
            return
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

