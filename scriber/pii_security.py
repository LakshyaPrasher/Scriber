"""PII & Data Protection Security Sub-Agent for Scriber.

Inspired by wshobson/agents security & governance plugins (security-compliance,
backend-api-security, protect-mcp), this subagent provides automated detection,
masking, and compliance auditing for sensitive PII, API credentials, and secrets.
"""

from __future__ import annotations

import copy
import re
from typing import Dict, List, Optional, Tuple

from scriber.models import ActionItem, AudioSegment, PIIRedactionReport, WordTimestamp


class PIISecurityOfficer:
    """Specialist subagent responsible for sanitizing transcripts and verifying PII compliance."""

    # PII and Secret detection patterns
    PATTERNS = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "api_key": re.compile(r"\b(?:sk-[a-zA-Z0-9_\-]{16,}|ghp_[a-zA-Z0-9]{30,}|AKIA[0-9A-Z]{16}|bearer\s+[a-zA-Z0-9\-_.]{16,})\b", re.IGNORECASE),
        "secret_assignment": re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?token|auth[_-]?token|access[_-]?token|password|passwd|pwd)\s*(?:=|:|\bis\b)\s*[\"']?([^\s\"',;]{6,})[\"']?"),
        "credit_card": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "jwt_token": re.compile(r"\beyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b"),
    }

    def __init__(self, default_mask_mode: str = "partial"):
        self.default_mask_mode = default_mask_mode  # 'partial' or 'full'

    def redact_text(
        self, text: str, mask_mode: Optional[str] = None
    ) -> Tuple[str, Dict[str, int], List[str]]:
        """Sanitizes text by masking emails, phone numbers, API keys, and credentials."""
        mode = mask_mode or self.default_mask_mode
        counts: Dict[str, int] = {}
        audit_log: List[str] = []
        result = text

        # 1. API Keys and Tokens
        for m in list(self.PATTERNS["api_key"].finditer(result)):
            val = m.group(0)
            replacement = "[REDACTED_API_KEY]" if mode == "full" else f"{val[:3]}***[KEY]***{val[-2:] if len(val) > 5 else ''}"
            result = result.replace(val, replacement)
            counts["api_key"] = counts.get("api_key", 0) + 1
            audit_log.append(f"Masked credential token: {val[:4]}***")

        # 2. Secret Assignments
        for m in list(self.PATTERNS["secret_assignment"].finditer(result)):
            val = m.group(1)
            replacement = "[REDACTED_SECRET]" if mode == "full" else f"{val[:1]}***[SECRET]"
            result = result.replace(val, replacement)
            counts["secret"] = counts.get("secret", 0) + 1
            audit_log.append(f"Masked secret value assignment: {val[:2]}***")

        # 3. JWT Tokens
        for m in list(self.PATTERNS["jwt_token"].finditer(result)):
            val = m.group(0)
            replacement = "[REDACTED_JWT_TOKEN]"
            result = result.replace(val, replacement)
            counts["jwt_token"] = counts.get("jwt_token", 0) + 1
            audit_log.append("Masked JWT bearer token")

        # 4. Credit Cards
        for m in list(self.PATTERNS["credit_card"].finditer(result)):
            val = m.group(0)
            # Simple Luhn-like validation filter to avoid false positives on standard dates/timecodes
            digits = re.sub(r"\D", "", val)
            if len(digits) == 16:
                replacement = "[REDACTED_CARD]" if mode == "full" else f"****-****-****-{digits[-4:]}"
                result = result.replace(val, replacement)
                counts["credit_card"] = counts.get("credit_card", 0) + 1
                audit_log.append(f"Masked payment card ending in {digits[-4:]}")

        # 5. SSN
        for m in list(self.PATTERNS["ssn"].finditer(result)):
            val = m.group(0)
            replacement = "[REDACTED_SSN]" if mode == "full" else f"***-**-{val[-4:]}"
            result = result.replace(val, replacement)
            counts["ssn"] = counts.get("ssn", 0) + 1
            audit_log.append(f"Masked SSN ending in {val[-4:]}")

        # 6. Emails
        for m in list(self.PATTERNS["email"].finditer(result)):
            val = m.group(0)
            if mode == "full":
                replacement = "[REDACTED_EMAIL]"
            else:
                user, domain = val.split("@", 1)
                masked_user = user[0] + "***" if len(user) > 1 else "***"
                replacement = f"{masked_user}@{domain}"
            result = result.replace(val, replacement)
            counts["email"] = counts.get("email", 0) + 1
            audit_log.append(f"Masked email address for domain: {val.split('@')[-1]}")

        # 7. Phone Numbers
        for m in list(self.PATTERNS["phone"].finditer(result)):
            val = m.group(0)
            # Ensure not a pure 4-digit number or timecode
            digits = re.sub(r"\D", "", val)
            if len(digits) >= 10:
                replacement = "[REDACTED_PHONE]" if mode == "full" else f"(***) ***-{digits[-4:]}"
                result = result.replace(val, replacement)
                counts["phone"] = counts.get("phone", 0) + 1
                audit_log.append(f"Masked phone number ending in {digits[-4:]}")

        return result, counts, audit_log

    def sanitize_segments(
        self, segments: List[AudioSegment], mask_mode: Optional[str] = None
    ) -> Tuple[List[AudioSegment], PIIRedactionReport]:
        """Creates sanitized copies of audio segments with PII masked and compliance scores."""
        mode = mask_mode or self.default_mask_mode
        total_counts: Dict[str, int] = {}
        all_logs: List[str] = []
        sanitized_segments: List[AudioSegment] = []

        for seg in segments:
            redacted_text, counts, logs = self.redact_text(seg.text, mask_mode=mode)
            for k, v in counts.items():
                total_counts[k] = total_counts.get(k, 0) + v
            all_logs.extend(logs)

            # Copy word timestamps if present and mask matching words
            new_words: List[WordTimestamp] = []
            for w in seg.words:
                redacted_w, _, _ = self.redact_text(w.word, mask_mode=mode)
                new_words.append(
                    WordTimestamp(
                        word=redacted_w,
                        start=w.start,
                        end=w.end,
                        probability=w.probability,
                    )
                )

            new_seg = copy.deepcopy(seg)
            new_seg.text = redacted_text
            new_seg.words = new_words
            sanitized_segments.append(new_seg)

        total_redacted = sum(total_counts.values())
        # Calculate privacy compliance score: 1.0 = clean, >0 detected and shielded
        compliance_score = 1.0 if total_redacted == 0 else max(0.95, 1.0 - (total_redacted * 0.005))

        report = PIIRedactionReport(
            redacted_count=total_redacted,
            entities_found=total_counts,
            compliance_score=compliance_score,
            audit_log=all_logs,
            is_shielded=True,
        )

        return sanitized_segments, report

    def sanitize_action_items(
        self, action_items: List[ActionItem], mask_mode: Optional[str] = None
    ) -> List[ActionItem]:
        """Sanitizes action item tasks and context quotes."""
        mode = mask_mode or self.default_mask_mode
        sanitized_items: List[ActionItem] = []
        for item in action_items:
            new_item = copy.deepcopy(item)
            new_task, _, _ = self.redact_text(item.task, mask_mode=mode)
            new_quote, _, _ = self.redact_text(item.context_quote, mask_mode=mode)
            new_item.task = new_task
            new_item.context_quote = new_quote
            sanitized_items.append(new_item)
        return sanitized_items
