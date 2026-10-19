"""Verification tests for Scriber Clean Modern UI, @happyhour.st color palette, and 2-mode production architecture."""

import unittest
from scriber.web.server import get_embedded_html


class TestUIContracts(unittest.TestCase):

    def setUp(self):
        self.html = get_embedded_html()

    def test_happyhour_color_palette(self):
        """Verifies strict adherence to @happyhour.st Tangerine & Antique Gold dark theme."""
        self.assertIn("#FF5E00", self.html, "Vibrant Tangerine Orange must be present")
        self.assertIn("#E5A93C", self.html, "Antique Gold must be present")
        self.assertIn("#08090C", self.html, "Deep Charcoal Canvas must be present")
        self.assertIn("#FF8A7A", self.html, "Blush Coral subtle accent must be present")

    def test_key_components_and_hooks(self):
        """Verifies all required DOM IDs, classes, and test assertion hooks."""
        self.assertIn("Scriber", self.html)
        self.assertIn("Voice Cloning Studio", self.html)
        self.assertIn("audio-player", self.html)
        self.assertIn("media-file-input", self.html)
        self.assertIn("dropzone", self.html)
        self.assertIn("copy-transcript-btn", self.html)
        self.assertIn("interactive", self.html.lower())

    def test_stock_emojis_eliminated(self):
        """Verifies no uninspired stock emojis are present in UI markup."""
        stock_emojis = ["🎬", "✨", "🎥", "🛡️", "🧬"]
        for emoji in stock_emojis:
            self.assertNotIn(emoji, self.html, f"Stock emoji {emoji} should be replaced with vector SVG")

    def test_cluttered_elements_eliminated(self):
        """Verifies total elimination of noisy elements per user specification."""
        cluttered_elements = [
            "4 Subagents Armed",
            "99.9% Mathematical Target",
            "Top 10 Leveraged GitHub Repositories",
            "Load Demo Meeting",
            "Subagent Army & Intelligence",
            "Acoustic Ingestion & VAD Stream Banner",
            'id="task-select"',
            'id="council-audit-seal-strip"',
            "Copy Seal",
            "Forensic Action Item Commitments",
            "Council Swarm Intelligence",
            "Autonomous Council Swarm",
            'id="swarm-view"',
            'id="swarm-agents-grid"',
        ]
        for element in cluttered_elements:
            self.assertNotIn(element, self.html, f"Cluttered element '{element}' must be removed from the UI")

    def test_about_creator_portfolio(self):
        """Verifies presence of aesthetic About Me Bento Grid for Lakshya Prasher."""
        self.assertIn("Lakshya Prasher", self.html)
        self.assertIn("https://www.instagram.com/laksh._.ya/", self.html)
        self.assertIn("https://www.linkedin.com/in/lakshyaprasher/", self.html)
        self.assertIn("https://github.com/LakshyaPrasher", self.html)
        self.assertIn('id="about-view"', self.html)
        self.assertIn('id="btn-mode-about"', self.html)
        self.assertIn("The Anti-Slop Philosophy", self.html)

    def test_liquid_morphing_animation(self):
        """Verifies Claude liquid gooey morphing animation filter and DOM nodes."""
        self.assertIn('id="goo"', self.html)
        self.assertIn("liquid-orb-stage", self.html)
        self.assertIn("orb-core", self.html)
        self.assertIn("orbitBlob", self.html)

    def test_kinetic_streaming_and_client_exports(self):
        """Verifies kinetic typography highlights, one-click copy, and dynamic client exports."""
        self.assertIn("copyFullTranscript", self.html)
        self.assertIn("formatSrtTimestamp", self.html)
        self.assertIn("formatVttTimestamp", self.html)
        self.assertIn("downloadArtifact", self.html)


    def test_two_mode_navigation(self):
        """Verifies clean 2-mode layout navigation between Transcribe and Voice Clone."""
        self.assertIn("switchMode", self.html)
        self.assertIn('id="transcribe-view"', self.html)
        self.assertIn('id="voice-view"', self.html)
        self.assertIn('id="btn-mode-transcribe"', self.html)
        self.assertIn('id="btn-mode-voice"', self.html)

    def test_speaker_color_blocks(self):
        """Verifies 4 vibrant speaker themes: Tangerine, Gold, Emerald, Coral."""
        self.assertIn(".spk-theme-1", self.html)
        self.assertIn(".spk-theme-2", self.html)
        self.assertIn(".spk-theme-3", self.html)
        self.assertIn(".spk-theme-4", self.html)
        self.assertIn("#10B981", self.html, "Emerald accent for speaker 3")
        self.assertIn("#FF8A7A", self.html, "Coral accent for speaker 4")

    def test_voice_cloning_studio_controls(self):
        """Verifies voice cloning controls: pitch slider, rate slider, prompt text, and download."""
        self.assertIn('id="pitch-slider"', self.html)
        self.assertIn('id="rate-slider"', self.html)
        self.assertIn('id="clone-text"', self.html)
        self.assertIn("synthesizeClonedVoice", self.html)
        self.assertIn('id="clone-download-btn"', self.html)

    def test_file_dialog_and_drop_handling(self):
        """Verifies reliable file dialog opening and drag/drop listeners."""
        self.assertIn('id="media-file-input"', self.html)
        self.assertIn("openFileDialog", self.html)
        self.assertIn("handleFileSelected", self.html)
        self.assertIn("drag-active", self.html)

    def test_voice_cloning_reference_audio_dropzone(self):
        """Verifies dedicated reference audio dropzone in Voice Cloning Studio."""
        self.assertIn('id="voice-ref-dropzone"', self.html)
        self.assertIn('id="voice-ref-input"', self.html)
        self.assertIn("handleVoiceRefSelected", self.html)

    def test_top_models_switchers(self):
        """Verifies presence of Top 3 Open-Source Models Switcher in both Transcribe & Voice Clone modes."""
        self.assertIn('id="transcribe-model-switcher"', self.html)
        self.assertIn('id="voice-model-switcher"', self.html)
        self.assertIn("selectTranscribeModel", self.html)
        self.assertIn("selectVoiceModel", self.html)
        self.assertIn("Whisper Turbo", self.html)
        self.assertIn("Whisper Base", self.html)
        self.assertIn("WhisperX", self.html)
        self.assertIn("Edge-Neural Studio", self.html)
        self.assertIn("WhisperSpeech", self.html)
        self.assertIn("GPT-SoVITS", self.html)
        self.assertIn("Zero Bulk Download", self.html)

    def test_minimalist_harmonic_logo_everywhere(self):
        """Verifies complete, authoritative harmonic S monogram emblem is present."""
        self.assertIn("Scriber Harmonic S Monogram Emblem", self.html)
        self.assertIn("scWaveGrad", self.html)
        self.assertIn("/assets/icon.svg", self.html)

    def test_realtime_audio_editor_controls(self):
        """Verifies real-time volume gain, pitch shift, and trimming sliders with Web Audio integration."""
        self.assertIn("handleVolumeInput", self.html)
        self.assertIn("handlePitchInput", self.html)
        self.assertIn("handleTrimBarInput", self.html)
        self.assertIn('id="m1-trim-start-bar"', self.html)
        self.assertIn('id="m1-trim-end-bar"', self.html)
        self.assertIn('id="m2-trim-start-bar"', self.html)
        self.assertIn('id="m2-trim-end-bar"', self.html)
        self.assertIn("getStudioGainNode", self.html)
        self.assertIn("triggerRealtimeAudition", self.html)


if __name__ == "__main__":
    unittest.main()
