"""Scriber: High-Precision Video Intelligence, Whisper Flow Transcription, Acoustic Diarization, and Voice Synthesis Desktop Studio.
"""

import os

# Disable unsigned C-extensions globally to guarantee zero Smart App Control / WDAC alerts
os.environ.setdefault("AIOHTTP_NO_EXTENSIONS", "1")

__version__ = "2.0.0"

from scriber.models import (
    ActionItem,
    AgentProfile,
    AgentTelemetry,
    AudioMetadata,
    AudioSegment,
    CouncilAnalysis,
    ScriberOutput,
    DiscussionPoint,
    ExecutiveSummary,
    HashChainBlock,
    PIIRedactionReport,
    QualityReport,
    TranscriptionResult,
    ValidationReport,
    VoiceCloneResult,
    VoiceProfile,
    WordTimestamp,
)

_LAZY_IMPORTS = {
    "AudioExtractor": ("scriber.audio_extractor", "AudioExtractor"),
    "AudioEditor": ("scriber.audio_editor", "AudioEditor"),
    "SupremeCouncil": ("scriber.council", "SupremeCouncil"),
    "ScriberExporter": ("scriber.exporters", "ScriberExporter"),
    "TOP_LEVERAGED_REPOS": ("scriber.transcription_engine", "TOP_LEVERAGED_REPOS"),
    "GitHubEngine": ("scriber.transcription_engine", "GitHubEngine"),
    "TranscriptionEngine": ("scriber.transcription_engine", "TranscriptionEngine"),
    "CouncilAgentSwarm": ("scriber.agent_swarm", "CouncilAgentSwarm"),
    "PIISecurityOfficer": ("scriber.pii_security", "PIISecurityOfficer"),
    "ScriberPipeline": ("scriber.pipeline", "ScriberPipeline"),
    "QualityChecker": ("scriber.quality", "QualityChecker"),
    "ResultValidator": ("scriber.validator", "ResultValidator"),
    "VoiceCloner": ("scriber.voice_clone", "VoiceCloner"),
    "VoiceProfiler": ("scriber.voice_clone", "VoiceProfiler"),
    "ScriberDesktopApp": ("scriber.desktop", "ScriberDesktopApp"),
    "launch_desktop": ("scriber.desktop", "launch_desktop"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        mod_name, attr_name = _LAZY_IMPORTS[name]
        import importlib
        mod = importlib.import_module(mod_name)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module 'scriber' has no attribute '{name}'")


__all__ = [
    "AudioExtractor",
    "AudioEditor",
    "TranscriptionEngine",
    "GitHubEngine",
    "SupremeCouncil",
    "CouncilAgentSwarm",
    "PIISecurityOfficer",
    "QualityChecker",
    "ResultValidator",
    "VoiceCloner",
    "VoiceProfiler",
    "ScriberPipeline",
    "ScriberExporter",
    "ScriberOutput",
    "AudioSegment",
    "AudioMetadata",
    "TranscriptionResult",
    "ActionItem",
    "DiscussionPoint",
    "ExecutiveSummary",
    "QualityReport",
    "ValidationReport",
    "VoiceProfile",
    "VoiceCloneResult",
    "CouncilAnalysis",
    "WordTimestamp",
    "AgentProfile",
    "AgentTelemetry",
    "PIIRedactionReport",
    "HashChainBlock",
    "TOP_LEVERAGED_REPOS",
    "ScriberDesktopApp",
    "launch_desktop",
]

