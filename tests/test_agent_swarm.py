"""Unit tests for CouncilAgentSwarm & Specialist Subagents (inspired by wshobson/agents)."""

import unittest
from scriber.agent_swarm import (
    CouncilAgentSwarm,
    ExecutiveBrieferAgent,
    ActionItemAuditorAgent,
    ThematicChapterArchitectAgent,
    PIISecurityOfficerAgent,
    AcousticQAAgent,
)
from scriber.models import AudioSegment, TranscriptionResult


class TestCouncilAgentSwarm(unittest.TestCase):

    def setUp(self):
        self.swarm = CouncilAgentSwarm()
        self.segments = [
            AudioSegment(
                id=0,
                seek=0,
                start=0.0,
                end=5.0,
                text="We decided to launch the Scriber desktop studio tomorrow. Alex must review the production release checklist.",
                speaker="Speaker_1",
            ),
            AudioSegment(
                id=1,
                seek=500,
                start=5.0,
                end=10.0,
                text="The major blocker is verifying the Web Audio API pitch tuning latency.",
                speaker="Speaker_2",
            ),
            AudioSegment(
                id=2,
                seek=1000,
                start=10.0,
                end=15.0,
                text="Contact admin@scriber.ai or call 555-0199 for root cluster access keys.",
                speaker="Speaker_1",
            ),
        ]
        self.transcription = TranscriptionResult(
            text="We decided to launch the Scriber desktop studio tomorrow. Alex must review the production release checklist. The major blocker is verifying the Web Audio API pitch tuning latency. Contact admin@scriber.ai or call 555-0199 for root cluster access keys.",
            language="en",
            language_probability=0.99,
            duration=15.0,
            segments=self.segments,
        )

    def test_roster_contains_five_specialist_agents(self):
        """Verifies CouncilAgentSwarm registers exactly 5 specialist agents with appropriate tiers."""
        roster = self.swarm.get_registered_agents()
        self.assertEqual(len(roster), 5)

        agent_ids = [a.id for a in roster]
        self.assertIn("executive-briefer", agent_ids)
        self.assertIn("action-auditor", agent_ids)
        self.assertIn("chapter-architect", agent_ids)
        self.assertIn("pii-security-officer", agent_ids)
        self.assertIn("acoustic-qa-inspector", agent_ids)

        # Verify model tiers
        briefer = next(a for a in roster if a.id == "executive-briefer")
        self.assertEqual(briefer.model_tier, "pro")
        self.assertIn("Executive Briefer Agent", briefer.name)

        action_agent = next(a for a in roster if a.id == "action-auditor")
        self.assertEqual(action_agent.model_tier, "pro")

        pii_agent = next(a for a in roster if a.id == "pii-security-officer")
        self.assertEqual(pii_agent.model_tier, "flash")

    def test_swarm_execution_telemetry_and_synthesis(self):
        """Verifies coordinated execution of all 5 agents and telemetry collection."""
        analysis = self.swarm.execute_swarm(self.transcription, redact_pii=False)

        # Check telemetry
        self.assertEqual(len(analysis.agent_telemetry), 5)
        for t in analysis.agent_telemetry:
            self.assertEqual(t.status, "completed")
            self.assertGreater(t.runtime_ms, 0)
            self.assertGreater(t.confidence, 0.9)

        # Check executive summary
        self.assertIsNotNone(analysis.executive_summary)
        self.assertTrue(len(analysis.executive_summary.tldr) > 0)
        self.assertGreaterEqual(len(analysis.executive_summary.decisions_reached), 1)

        # Check action items
        self.assertGreaterEqual(len(analysis.action_items), 1)
        alex_action = next((a for a in analysis.action_items if "Alex" in a.assignee or "Alex" in a.task), None)
        self.assertIsNotNone(alex_action)

        # Check discussion points
        self.assertGreaterEqual(len(analysis.discussion_points), 1)

        # Check PII Report
        self.assertIsNotNone(analysis.pii_report)
        self.assertGreaterEqual(analysis.pii_report.redacted_count, 1)

    def test_executive_briefer_agent(self):
        """Verifies ExecutiveBrieferAgent extraction of TL;DR, decisions, and blockers."""
        agent = ExecutiveBrieferAgent()
        self.assertEqual(agent.PROFILE.model_tier, "pro")

        summary, telemetry = agent.execute(
            full_text=self.transcription.text,
            action_items=[],
            discussion_points=[],
            decisions=["Approved: Launch Scriber studio tomorrow."],
            open_questions=["What about pitch tuning latency?"],
            duration=15.0,
        )
        self.assertIsNotNone(summary)
        self.assertIn("Launch Scriber studio", summary.decisions_reached[0])
        self.assertEqual(telemetry.agent_id, "executive-briefer")
        self.assertEqual(telemetry.status, "completed")

    def test_action_item_auditor_agent(self):
        """Verifies ActionItemAuditorAgent extracts commitments with deadlines and seek offsets."""
        agent = ActionItemAuditorAgent()
        actions, telemetry = agent.execute(self.segments)
        self.assertGreaterEqual(len(actions), 1)
        self.assertTrue(hasattr(actions[0], "start_time"))
        self.assertGreaterEqual(actions[0].start_time, 0.0)
        self.assertEqual(telemetry.agent_id, "action-auditor")

    def test_thematic_chapter_architect_agent(self):
        """Verifies ThematicChapterArchitectAgent clusters topics into structured chapters."""
        agent = ThematicChapterArchitectAgent()
        points, topics, telemetry = agent.execute(self.segments, self.transcription.text)
        self.assertGreaterEqual(len(points), 1)
        self.assertTrue(hasattr(points[0], "title"))
        self.assertTrue(hasattr(points[0], "summary"))
        self.assertEqual(telemetry.agent_id, "chapter-architect")

    def test_pii_security_officer_agent(self):
        """Verifies PIISecurityOfficerAgent detects emails and phone numbers."""
        agent = PIISecurityOfficerAgent()
        report, telemetry = agent.execute(self.segments, self.transcription.text)
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report.redacted_count, 1)
        self.assertIn("email", report.entities_found)
        self.assertEqual(telemetry.agent_id, "pii-security-officer")

    def test_acoustic_qa_agent(self):
        """Verifies AcousticQAAgent validates speech continuity and acoustic speaker distribution."""
        agent = AcousticQAAgent()
        speaker_stats, telemetry = agent.execute(self.segments)
        self.assertGreaterEqual(len(speaker_stats), 2)
        self.assertEqual(telemetry.agent_id, "acoustic-qa-inspector")


if __name__ == "__main__":
    unittest.main()
