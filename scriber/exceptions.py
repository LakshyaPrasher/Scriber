"""Custom exceptions for Scriber speech intelligence and voice synthesis."""

from __future__ import annotations


class JobCancelledException(Exception):
    """Raised when an active processing job is aborted by user cancellation."""
    pass


class TranscriptionUnavailableError(RuntimeError):
    """Raised when no real speech-recognition backend is available.

    Scriber deliberately refuses to invent a transcript when ASR cannot run.
    Demo endpoints opt into synthetic transcripts explicitly instead.
    """
    pass
