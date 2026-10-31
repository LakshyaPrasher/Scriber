"""Scriber: High-Precision Video Intelligence, Whisper Flow Transcription, Acoustic Diarization, and Voice Synthesis Desktop Studio.
"""

import os

# Disable unsigned C-extensions globally to guarantee zero Smart App Control / WDAC alerts
os.environ.setdefault("AIOHTTP_NO_EXTENSIONS", "1")

__version__ = "2.0.0"

from scriber.audio_extractor import AudioExtractor
from scriber.audio_editor import AudioEditor
from scriber.council import SupremeCouncil
from scriber.exporters import ScriberExporter
from scriber.transcription_engine import TOP_LEVERAGED_REPOS, GitHubEngine, TranscriptionEngine
from scriber.agent_swarm import CouncilAgentSwarm
from scriber.pii_security import PIISecurityOfficer
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
from scriber.pipeline import ScriberPipeline
from scriber.quality import QualityChecker
from scriber.validator import ResultValidator
from scriber.voice_clone import VoiceCloner, VoiceProfiler
from scriber.desktop import ScriberDesktopApp, launch_desktop

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
