"""Tests for SupremeCouncil (Sub-Agent 2: Action Items, Discussion Points, and Summaries)."""

import unittest

from scriber.council import SupremeCouncil
from scriber.models import AudioSegment, TranscriptionResult


class TestSupremeCouncil(unittest.TestCase):

    def setUp(self):
        self.council = SupremeCouncil()

    def test_action_item_extraction_with_owners_and_deadlines(self):
        """Verifies parsing of action items, owners, priorities, and deadlines."""
        segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=4.0,
                text="Alex will configure the S3 bucket by Friday.",
                speaker="Speaker_1",
            ),
            AudioSegment(
                id=1,
                seek=400,
                start=4.0,
                end=8.0,
                text="Sarah needs to test the audio VAD pipeline urgently today.",
                speaker="Speaker_2",
            ),
            AudioSegment(
                id=2,
                seek=800,
                start=8.0,
                end=12.0,
                text="I will update the documentation for the standalone studio deployment.",
                speaker="Lead_Dev",
            ),
        ]
        transcription = TranscriptionResult(
            text="Alex will configure the desktop bundle by Friday. Sarah needs to test the audio VAD pipeline urgently today. I will update the documentation for the standalone studio deployment.",
            language="en",
            language_probability=0.99,
            duration=12.0,
            segments=segments,
        )

        analysis = self.council.analyze(transcription)
        actions = analysis.action_items

        self.assertGreaterEqual(len(actions), 3)

        # Check action 1
        a1 = next((a for a in actions if "S3 bucket" in a.task), None)
        self.assertIsNotNone(a1)
        self.assertEqual(a1.assignee, "Alex")
        self.assertIn("Friday", a1.due_date)

        # Check action 2
        a2 = next((a for a in actions if "VAD" in a.task), None)
        self.assertIsNotNone(a2)
        self.assertEqual(a2.assignee, "Sarah")
        self.assertEqual(a2.priority, "urgent")

        # Check action 3 (first person normalized to speaker)
        a3 = next((a for a in actions if "documentation" in a.task), None)
        self.assertIsNotNone(a3)
        self.assertEqual(a3.assignee, "Lead_Dev")

    def test_executive_summary_and_decisions(self):
        """Verifies executive summary synthesis, ratified decisions, and open questions."""
        segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=5.0,
                text="We agreed that the desktop studio deployment must remain completely offline with local models.",
                speaker="Speaker_1",
            ),
            AudioSegment(
                id=1,
                seek=500,
                start=5.0,
                end=10.0,
                text="How do we ensure startup time remains under 500 milliseconds?",
                speaker="Speaker_2",
            ),
        ]
        transcription = TranscriptionResult(
            text="We agreed that the desktop studio deployment must remain completely offline with local models. How do we ensure startup time remains under 500 milliseconds?",
            language="en",
            language_probability=0.99,
            duration=10.0,
            segments=segments,
        )

        analysis = self.council.analyze(transcription)
        summary = analysis.executive_summary

        self.assertIn("Desktop Studio", summary.headline)
        self.assertGreater(len(summary.decisions_reached), 0)
        self.assertTrue(any("offline" in d.lower() for d in summary.decisions_reached))
        self.assertGreater(len(summary.unresolved_questions), 0)


if __name__ == "__main__":
    unittest.main()
