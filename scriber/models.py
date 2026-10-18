"""Data models and type definitions for Scriber."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WordTimestamp:
    """Word-level alignment timestamp matching WhisperX conventions."""
    word: str
    start: float
    end: float
    probability: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class AudioSegment:
    """Individual transcription segment matching OpenAI Whisper and WhisperX formats."""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int] = field(default_factory=list)
    temperature: float = 0.0
    avg_logprob: float = -0.1
    compression_ratio: float = 1.2
    no_speech_prob: float = 0.01
    words: List[WordTimestamp] = field(default_factory=list)
    speaker: Optional[str] = None
    confidence: float = 0.99

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "seek": self.seek,
            "start": round(self.start, 3),
            "end": round(self.end, 3),
            "text": self.text.strip(),
            "tokens": self.tokens,
            "temperature": round(self.temperature, 2),
            "avg_logprob": round(self.avg_logprob, 4),
            "compression_ratio": round(self.compression_ratio, 3),
            "no_speech_prob": round(self.no_speech_prob, 4),
            "words": [w.to_dict() for w in self.words],
            "speaker": self.speaker,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class AudioMetadata:
    """Metadata extracted from the raw media file."""
    filename: str
    duration: float
    sample_rate: int
    channels: int
    file_size_bytes: int
    file_format: str
    bitrate_kbps: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class TranscriptionResult:
    """Raw speech-to-text / translation result from the GitHub Whisper engine."""
    text: str
    language: str
    language_probability: float
    duration: float
    segments: List[AudioSegment] = field(default_factory=list)
    task: str = "transcribe"  # 'transcribe' or 'translate'
    backend_used: str = "whisper-flow"
    model_name: str = "whisper-base-en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "language_probability": round(self.language_probability, 4),
            "duration": round(self.duration, 3),
            "task": self.task,
            "backend_used": self.backend_used,
            "model_name": self.model_name,
            "segments": [s.to_dict() for s in self.segments],
        }


@dataclass
class ActionItem:
    """Action item extracted by the Supreme Council Sub-Agent."""
    id: str
    task: str
    assignee: str
    priority: str = "medium"  # urgent, high, medium, low
    status: str = "open"  # open, in_progress, completed
    due_date: Optional[str] = None
    context_quote: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    confidence: float = 0.99

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "assignee": self.assignee,
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date,
            "context_quote": self.context_quote,
            "timestamp": f"{self._format_ts(self.start_time)} - {self._format_ts(self.end_time)}",
            "start_time": round(self.start_time, 2),
            "end_time": round(self.end_time, 2),
            "confidence": round(self.confidence, 3),
        }

    @staticmethod
    def _format_ts(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


@dataclass
class DiscussionPoint:
    """Discussion point extracted by the Supreme Council Sub-Agent."""
    id: str
    title: str
    summary: str
    key_quotes: List[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    speakers: List[str] = field(default_factory=list)
    sentiment: str = "constructive"  # positive, constructive, neutral, critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "key_quotes": self.key_quotes,
            "timestamp_range": f"{self._format_ts(self.start_time)} - {self._format_ts(self.end_time)}",
            "start_time": round(self.start_time, 2),
            "end_time": round(self.end_time, 2),
            "speakers": self.speakers,
            "sentiment": self.sentiment,
        }

    @staticmethod
    def _format_ts(seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


@dataclass
class ExecutiveSummary:
    """High-level intelligent synthesis generated by Supreme Council."""
    headline: str
    tldr: str
    key_takeaways: List[str] = field(default_factory=list)
    decisions_reached: List[str] = field(default_factory=list)
    unresolved_questions: List[str] = field(default_factory=list)
    action_items_count: int = 0
    sentiment_overview: str = "productive"
    meeting_type_category: str = "technical_planning"

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class QualityReport:
    """Audit report generated by the Quality Check Sub-Agent."""
    overall_score: float  # 0.0 to 1.0
    confidence_avg: float
    repetition_looping_detected: bool
    hallucinations_culled: int
    low_confidence_segments_flagged: int
    compression_ratio_healthy: bool
    word_count: int
    estimated_speaking_wpm: float
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 4),
            "confidence_avg": round(self.confidence_avg, 4),
            "repetition_looping_detected": self.repetition_looping_detected,
            "hallucinations_culled": self.hallucinations_culled,
            "low_confidence_segments_flagged": self.low_confidence_segments_flagged,
            "compression_ratio_healthy": self.compression_ratio_healthy,
            "word_count": self.word_count,
            "estimated_speaking_wpm": round(self.estimated_speaking_wpm, 1),
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }


@dataclass
class ValidationReport:
    """Statistical audit and certification generated by the Validation Sub-Agent."""
    accuracy_score: float  # 0.0 to 1.0 (target: >= 0.99)
    wer: float  # Word Error Rate (target: <= 0.01)
    cer: float  # Character Error Rate
    precision: float
    recall: float
    f1_score: float
    passed_99_percent: bool
    test_case_id: Optional[str] = None
    evaluated_tokens: int = 0
    matched_tokens: int = 0
    certificate_id: str = ""
    audit_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy_score": round(self.accuracy_score, 4),
            "accuracy_percentage": f"{self.accuracy_score * 100:.2f}%",
            "wer": round(self.wer, 4),
            "cer": round(self.cer, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "passed_99_percent": self.passed_99_percent,
            "test_case_id": self.test_case_id,
            "evaluated_tokens": self.evaluated_tokens,
            "matched_tokens": self.matched_tokens,
            "certificate_id": self.certificate_id,
            "audit_notes": self.audit_notes,
        }


@dataclass
class CouncilAnalysis:
    """Consolidated output from Supreme Council Sub-Agent."""
    executive_summary: ExecutiveSummary
    action_items: List[ActionItem] = field(default_factory=list)
    discussion_points: List[DiscussionPoint] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    speaker_diarization: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "executive_summary": self.executive_summary.to_dict(),
            "action_items": [a.to_dict() for a in self.action_items],
            "discussion_points": [d.to_dict() for d in self.discussion_points],
            "topics": self.topics,
            "speaker_diarization": self.speaker_diarization,
        }


@dataclass
class VoiceProfile:
    """Speaker acoustic biometric profile for voice cloning."""
    speaker_id: str
    fundamental_frequency_hz: float  # Mean F0 pitch (Hz)
    pitch_min_hz: float
    pitch_max_hz: float
    pitch_std_hz: float
    spectral_centroid_hz: float  # Timbre brightness (Hz)
    zero_crossing_rate: float
    estimated_wpm: float
    energy_rms: float
    gender_estimate: str  # 'masculine', 'feminine', 'androgynous'
    sample_duration: float
    voice_vector: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class VoiceCloneResult:
    """Result of voice cloning and speech synthesis."""
    profile: VoiceProfile
    text_prompt: str
    audio_pcm16: bytes
    audio_format: str
    similarity_score: float  # Biometric match >= 0.99
    synthesis_backend: str
    audio_base64: str
    duration: float
    mp3_base64: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "speaker_id": self.profile.speaker_id,
            "text_prompt": self.text_prompt,
            "audio_format": self.audio_format,
            "similarity_score": round(self.similarity_score, 4),
            "similarity_percentage": f"{self.similarity_score * 100:.2f}%",
            "synthesis_backend": self.synthesis_backend,
            "audio_base64": self.audio_base64,
            "duration": round(self.duration, 3),
            "profile": self.profile.to_dict(),
        }
        if self.mp3_base64:
            d["mp3_base64"] = self.mp3_base64
        return d


@dataclass
class ScriberOutput:
    """Final comprehensive output returned by Scriber."""
    session_id: str
    video_source: str
    audio_metadata: AudioMetadata
    transcription: TranscriptionResult
    translation: Optional[TranscriptionResult]
    council_analysis: CouncilAnalysis
    quality_report: QualityReport
    validation_report: ValidationReport
    processing_time_seconds: float
    repos_leveraged: List[str] = field(default_factory=list)
    voice_profiles: List[VoiceProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "video_source": self.video_source,
            "audio_metadata": self.audio_metadata.to_dict(),
            "transcription": self.transcription.to_dict(),
            "translation": self.translation.to_dict() if self.translation else None,
            "council_analysis": self.council_analysis.to_dict(),
            "quality_report": self.quality_report.to_dict(),
            "validation_report": self.validation_report.to_dict(),
            "processing_time_seconds": round(self.processing_time_seconds, 3),
            "repos_leveraged": self.repos_leveraged,
            "voice_profiles": [vp.to_dict() for vp in self.voice_profiles],
        }





