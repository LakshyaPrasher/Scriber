"""Custom exceptions for Scriber speech intelligence and voice synthesis."""

from __future__ import annotations


class JobCancelledException(Exception):
    """Raised when an active processing job is aborted by user cancellation."""
    pass
