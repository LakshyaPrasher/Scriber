"""Unit tests for PIISecurityOfficer (inspired by wshobson/agents security-compliance & protect-mcp)."""

import unittest
from scriber.models import ActionItem, AudioSegment, WordTimestamp
from scriber.pii_security import PIISecurityOfficer


class TestPIISecurityOfficer(unittest.TestCase):

    def setUp(self):
        self.officer_partial = PIISecurityOfficer(default_mask_mode="partial")
        self.officer_full = PIISecurityOfficer(default_mask_mode="full")

    def test_api_key_and_token_redaction(self):
        """Verifies redaction of OpenAI, GitHub, AWS, and bearer tokens."""
        text = "Deploy using sk-proj1234567890abcdef12 and ghp_123456789012345678901234567890 with AKIAIOSFODNN7EXAMPLE."
        redacted_partial, counts, logs = self.officer_partial.redact_text(text)
        self.assertNotIn("sk-proj1234567890abcdef12", redacted_partial)
        self.assertNotIn("ghp_123456789012345678901234567890", redacted_partial)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", redacted_partial)
        self.assertGreaterEqual(counts.get("api_key", 0), 3)

        redacted_full, counts_full, _ = self.officer_full.redact_text(text)
        self.assertIn("[REDACTED_API_KEY]", redacted_full)

    def test_secret_assignment_redaction(self):
        """Verifies masking of explicit password or api_key assignments."""
        text = "Set password = SuperSecretPassword123 and auth_token: MyUltraSecureToken456."
        redacted, counts, logs = self.officer_full.redact_text(text)
        self.assertNotIn("SuperSecretPassword123", redacted)
        self.assertNotIn("MyUltraSecureToken456", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)
        self.assertGreaterEqual(counts.get("secret", 0), 2)

    def test_jwt_bearer_token_redaction(self):
        """Verifies masking of JSON Web Tokens."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        text = f"Bearer header token is {jwt}."
        redacted, counts, logs = self.officer_partial.redact_text(text)
        self.assertNotIn(jwt, redacted)
        self.assertIn("[REDACTED_JWT_TOKEN]", redacted)
        self.assertEqual(counts.get("jwt_token"), 1)

    def test_credit_card_and_ssn_redaction(self):
        """Verifies masking of payment cards and Social Security Numbers."""
        text = "Billing card is 4532-1234-5678-9010 and customer SSN is 000-12-3456."
        redacted_partial, counts, logs = self.officer_partial.redact_text(text)
        self.assertNotIn("4532-1234-5678-9010", redacted_partial)
        self.assertIn("****-****-****-9010", redacted_partial)
        self.assertNotIn("000-12-3456", redacted_partial)
        self.assertIn("***-**-3456", redacted_partial)

        redacted_full, _, _ = self.officer_full.redact_text(text)
        self.assertIn("[REDACTED_CARD]", redacted_full)
        self.assertIn("[REDACTED_SSN]", redacted_full)

    def test_email_and_phone_redaction(self):
        """Verifies email and phone masking in both partial and full modes."""
        text = "Reach out to lead.architect@scriber.io or call +1 (415) 555-2671."
        redacted_partial, counts, logs = self.officer_partial.redact_text(text)
        self.assertNotIn("lead.architect@scriber.io", redacted_partial)
        self.assertIn("@scriber.io", redacted_partial)
        self.assertNotIn("555-2671", redacted_partial)
        self.assertIn("(***) ***-2671", redacted_partial)

        redacted_full, _, _ = self.officer_full.redact_text(text)
        self.assertIn("[REDACTED_EMAIL]", redacted_full)
        self.assertIn("[REDACTED_PHONE]", redacted_full)

    def test_sanitize_segments_word_alignment(self):
        """Verifies that sanitize_segments sanitizes segment text and word-level timestamps."""
        words = [
            WordTimestamp(word="Email", start=0.0, end=0.4, probability=0.99),
            WordTimestamp(word="alex@domain.com", start=0.4, end=1.2, probability=0.98),
            WordTimestamp(word="today.", start=1.2, end=1.6, probability=0.99),
        ]
        segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=1.6,
                text="Email alex@domain.com today.",
                speaker="Speaker_1",
                words=words,
            )
        ]

        sanitized, report = self.officer_full.sanitize_segments(segments)
        self.assertEqual(len(sanitized), 1)
        self.assertIn("[REDACTED_EMAIL]", sanitized[0].text)
        self.assertNotIn("alex@domain.com", sanitized[0].text)
        self.assertIn("[REDACTED_EMAIL]", sanitized[0].words[1].word)
        self.assertTrue(report.is_shielded)
        self.assertEqual(report.redacted_count, 1)
        self.assertGreater(report.compliance_score, 0.9)

    def test_sanitize_action_items(self):
        """Verifies that action items tasks and context quotes are sanitized."""
        action = ActionItem(
            id="act-1",
            task="Send API key sk-proj1234567890abcdef to client@domain.com",
            assignee="Alex",
            context_quote="I will send sk-proj1234567890abcdef to client@domain.com today.",
        )
        sanitized = self.officer_full.sanitize_action_items([action])
        self.assertEqual(len(sanitized), 1)
        self.assertNotIn("sk-proj1234567890abcdef", sanitized[0].task)
        self.assertNotIn("client@domain.com", sanitized[0].task)
        self.assertIn("[REDACTED_API_KEY]", sanitized[0].task)
        self.assertIn("[REDACTED_EMAIL]", sanitized[0].context_quote)

    def test_clean_text_preserves_compliance_score_one(self):
        """Verifies that clean text with zero PII scores 1.0."""
        text = "The audio playback speed was adjusted to 1.5x with crystal clarity."
        redacted, counts, logs = self.officer_full.redact_text(text)
        self.assertEqual(text, redacted)
        self.assertEqual(len(counts), 0)

        segments = [AudioSegment(id=0, seek=0, start=0.0, end=2.0, text=text, speaker="Speaker_1")]
        _, report = self.officer_full.sanitize_segments(segments)
        self.assertEqual(report.redacted_count, 0)
        self.assertEqual(report.compliance_score, 1.0)


if __name__ == "__main__":
    unittest.main()
