"""Tests for Scriber canonical package imports and symbol exports."""

import unittest


class TestScriberPackageExports(unittest.TestCase):

    def test_canonical_scriber_imports(self):
        """Verifies canonical imports from scriber package."""
        from scriber import (
            ScriberPipeline,
            ScriberExporter,
            ScriberOutput,
            ScriberDesktopApp,
            TranscriptionEngine,
            GitHubEngine,
            SupremeCouncil,
            QualityChecker,
            ResultValidator,
            VoiceProfiler,
            VoiceCloner,
            VoiceProfile,
            VoiceCloneResult,
            AudioExtractor,
            AudioEditor,
            AudioMetadata,
            AudioSegment,
            WordTimestamp,
            ExecutiveSummary,
            ActionItem,
            DiscussionPoint,
            launch_desktop,
        )

        p = ScriberPipeline()
        self.assertIsNotNone(p)
        self.assertIsNotNone(p.voice_cloner)
        self.assertIsNotNone(p.audio_extractor)
        self.assertIsNotNone(p.diarizer)
        self.assertIsNotNone(p.supreme_council)
        self.assertIsNotNone(p.quality_checker)
        self.assertIsNotNone(p.result_validator)


if __name__ == "__main__":
    unittest.main()
