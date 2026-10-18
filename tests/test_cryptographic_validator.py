"""Unit tests for Cryptographic SHA-256 Hash Chaining & Tamper-Evident Validation (inspired by wshobson/agents signed-audit-trails & protect-mcp)."""

import copy
import unittest
from scriber.models import ActionItem, HashChainBlock, PIIRedactionReport
from scriber.validator import ResultValidator


class TestCryptographicValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ResultValidator()

    def test_build_hash_chain_structure(self):
        """Verifies construction of a 5-block cryptographic SHA-256 chain."""
        actions = [
            ActionItem(id="act-1", task="Deploy desktop studio", assignee="Alex"),
            ActionItem(id="act-2", task="Review PII shield", assignee="Sarah"),
        ]
        pii_report = PIIRedactionReport(
            redacted_count=2,
            entities_found={"api_key": 1, "email": 1},
            compliance_score=0.99,
            is_shielded=True,
        )

        blocks, root_hash = ResultValidator.build_hash_chain(
            test_case_id="session-test-001",
            hypothesis_text="Deploy desktop studio and review PII shield.",
            accuracy_score=0.995,
            wer=0.005,
            cer=0.002,
            extracted_actions=actions,
            pii_report=pii_report,
        )

        self.assertEqual(len(blocks), 5)
        self.assertEqual(blocks[0].prev_hash, "0" * 64)
        self.assertEqual(blocks[1].prev_hash, blocks[0].block_hash)
        self.assertEqual(blocks[2].prev_hash, blocks[1].block_hash)
        self.assertEqual(blocks[3].prev_hash, blocks[2].block_hash)
        self.assertEqual(blocks[4].prev_hash, blocks[3].block_hash)
        self.assertEqual(blocks[4].block_hash, root_hash)
        self.assertEqual(len(root_hash), 64)

    def test_verify_hash_chain_success(self):
        """Verifies mathematical verification passes for an authentic chain."""
        blocks, root_hash = ResultValidator.build_hash_chain(
            test_case_id="valid-session",
            hypothesis_text="Authentic spoken media.",
            accuracy_score=1.0,
            wer=0.0,
            cer=0.0,
        )
        is_valid = ResultValidator.verify_hash_chain(blocks, root_hash)
        self.assertTrue(is_valid)

    def test_tamper_detection_on_intermediate_block(self):
        """Verifies tampering with an intermediate block is immediately detected and rejected."""
        blocks, root_hash = ResultValidator.build_hash_chain(
            test_case_id="tamper-session",
            hypothesis_text="Authentic spoken media.",
            accuracy_score=1.0,
            wer=0.0,
            cer=0.0,
        )

        # Alter Block 1 (STT payload)
        tampered_blocks = copy.deepcopy(blocks)
        tampered_blocks[1].block_hash = "deadbeef" * 8

        is_valid = ResultValidator.verify_hash_chain(tampered_blocks, root_hash)
        self.assertFalse(is_valid)

    def test_tamper_detection_on_root_hash(self):
        """Verifies tampering with the final root hash is detected."""
        blocks, root_hash = ResultValidator.build_hash_chain(
            test_case_id="tamper-root",
            hypothesis_text="Authentic spoken media.",
            accuracy_score=1.0,
            wer=0.0,
            cer=0.0,
        )

        fake_root = "0123456789abcdef" * 4
        is_valid = ResultValidator.verify_hash_chain(blocks, fake_root)
        self.assertFalse(is_valid)

    def test_empty_or_broken_chain_fails(self):
        """Verifies empty chains or corrupt genesis blocks fail verification."""
        self.assertFalse(ResultValidator.verify_hash_chain([], "root"))
        self.assertFalse(ResultValidator.verify_hash_chain(None, "root"))

        corrupt_genesis = [
            HashChainBlock(
                index=0,
                block_name="Genesis Anchor",
                timestamp=0.0,
                prev_hash="corrupted_prev_hash",
                block_hash="abc",
                payload_summary="corrupt",
            )
        ]
        self.assertFalse(ResultValidator.verify_hash_chain(corrupt_genesis, "abc"))

    def test_validation_report_contains_certificate_and_hash_chain(self):
        """Verifies that evaluate_transcription generates a CERT-CSCR-*-CHAIN certificate and hash chain."""
        report = self.validator.evaluate_transcription(
            hypothesis_text="Scriber multi-agent intelligence.",
            reference_text="Scriber multi-agent intelligence.",
        )
        self.assertTrue(report.certificate_id.startswith("CERT-CSCR-"))
        self.assertTrue(report.certificate_id.endswith("-CHAIN"))
        self.assertEqual(len(report.hash_chain), 5)
        self.assertEqual(len(report.root_hash), 64)
        self.assertTrue(ResultValidator.verify_hash_chain(report.hash_chain, report.root_hash))


if __name__ == "__main__":
    unittest.main()
