"""Tests for ResultValidator (Sub-Agent 4: Accuracy Certification & WER Calculation)."""

import unittest

from scriber.models import ActionItem
from scriber.validator import ResultValidator


class TestResultValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ResultValidator()

    def test_perfect_transcription_accuracy(self):
        """Verifies exact match yields 100% accuracy, 0% WER, and 99%+ certification."""
        ref = "We are deploying the serverless transcription pipeline today."
        hyp = "We are deploying the serverless transcription pipeline today."

        report = self.validator.evaluate_transcription(hypothesis_text=hyp, reference_text=ref)

        self.assertEqual(report.accuracy_score, 1.0)
        self.assertEqual(report.wer, 0.0)
        self.assertEqual(report.cer, 0.0)
        self.assertTrue(report.passed_99_percent)
        self.assertTrue(report.certificate_id.startswith("CERT-CSCR-"))

    def test_wer_with_minor_substitution(self):
        """Verifies mathematical correctness of Levenshtein edit distance and WER."""
        ref = "the cat sat on the mat"  # 6 words
        hyp = "the cat sat on a mat"    # 1 substitution ("the" -> "a")

        report = self.validator.evaluate_transcription(hypothesis_text=hyp, reference_text=ref)

        expected_wer = 1.0 / 6.0
        self.assertAlmostEqual(report.wer, expected_wer, places=3)
        self.assertAlmostEqual(report.accuracy_score, 1.0 - expected_wer, places=3)
        self.assertFalse(report.passed_99_percent)  # ~83.3% is below 99%

    def test_action_item_precision_recall_f1(self):
        """Verifies evaluation of extracted action items against reference deliverables."""
        extracted = [
            ActionItem(
                id="ACT-001",
                task="Deploy desktop application bundle",
                assignee="Alex",
            ),
            ActionItem(
                id="ACT-002",
                task="Configure local audio cache rule",
                assignee="Sarah",
            ),
        ]
        references = [
            "Deploy desktop application",
            "Configure local audio cache",
        ]

        report = self.validator.evaluate_transcription(
            hypothesis_text="test",
            reference_text="test",
            extracted_actions=extracted,
            reference_actions=references,
        )

        self.assertEqual(report.precision, 1.0)
        self.assertEqual(report.recall, 1.0)
        self.assertEqual(report.f1_score, 1.0)

    def test_benchmark_suite_execution(self):
        """Verifies built-in benchmark test cases run and pass 99%+ threshold."""
        results = ResultValidator.run_benchmark_suite()
        self.assertTrue(results["all_passed_99_percent"])
        self.assertEqual(results["total_cases_evaluated"], 3)
        self.assertEqual(results["average_accuracy_percentage"], "100.00%")


if __name__ == "__main__":
    unittest.main()
