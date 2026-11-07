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
            'id="btn-ecosystem-modal"',
            'id="ecosystem-modal"',
            "Architectural Ecosystem",
            "FOUNDING ARCHITECT",
            "The Anti-Slop Philosophy",
            "Core Craft & Audio Intelligence",
            "Desktop Native",
            "Sys ASR Engine Console",
            "ASR ENGINE CONSOLE",
            "[SYS // ASR ENGINE CONSOLE]",
            "VOICE SYNTHESIS CONSOLE",
            "[SYS // VOICE SYNTHESIS CONSOLE]",
            "Active Engine Spec",
            "ACTIVE ENGINE SPEC",
            "Active Voice Engine",
            "ACTIVE VOICE ENGINE",
            "Production Stability Verified",
            "Ingestion Bay",
            "INGESTION BAY",
            "[INGESTION BAY // MULTI-FORMAT AUDIO & VIDEO]",
            "Zero Bulk Download",
            "Zero Bulk Download On-Demand Streaming",
            "UNIVERSAL INGESTION",
            "engine-manifest-panel",
            "PARAMETER COUNT",
            "CTranslate2 INT8",
            "Dynamic On-Demand Stream",
            "ACCURACY TIER",
            'id="desktop-badge"',
        ]
        for element in cluttered_elements:
            self.assertNotIn(element, self.html, f"Cluttered element '{element}' must be removed from the UI")

    def test_about_creator_portfolio(self):
        """Verifies presence of clean, animated, fluid name card for Lakshya Prasher."""
        self.assertIn("Lakshya Prasher", self.html)
        self.assertIn("https://www.instagram.com/laksh._.ya/", self.html)
        self.assertIn("https://www.linkedin.com/in/lakshyaprasher/", self.html)
        self.assertIn("https://github.com/LakshyaPrasher", self.html)
        self.assertIn('id="about-view"', self.html)
        self.assertIn('id="btn-mode-about"', self.html)
        self.assertIn("initBentoSpotlight", self.html)
        self.assertIn(".about-bento-grid", self.html)
        self.assertIn(".social-node-card", self.html)
        self.assertIn("/assets/avatar.png", self.html)
        self.assertIn("creator-avatar-img", self.html)
        self.assertIn("about-name-card", self.html)
        self.assertNotIn("The Anti-Slop Philosophy", self.html)
        self.assertNotIn("FOUNDING ARCHITECT", self.html)
        self.assertNotIn("Core Craft", self.html)

    def test_ecosystem_bar_eliminated(self):
        """Verifies that the ecosystem bar, button, and modal are completely eliminated."""
        self.assertNotIn("btn-ecosystem-modal", self.html)
        self.assertNotIn("ecosystem-modal", self.html)
        self.assertNotIn("openEcosystemModal", self.html)
        self.assertNotIn("Architectural Ecosystem", self.html)

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
        """Verifies presence of sleek, animated model switchers with tier badges in both modes."""
        self.assertIn('id="transcribe-model-switcher"', self.html)
        self.assertIn('id="voice-model-switcher"', self.html)
        self.assertIn('id="transcribe-dropdown-trigger"', self.html)
        self.assertIn('id="transcribe-dropdown-menu"', self.html)
        self.assertIn('id="voice-dropdown-trigger"', self.html)
        self.assertIn('id="voice-dropdown-menu"', self.html)
        self.assertIn("selectTranscribeModel", self.html)
        self.assertIn("selectVoiceModel", self.html)
        self.assertIn("toggleModelDropdown", self.html)
        # All models present
        self.assertIn("Whisper Turbo", self.html)
        self.assertIn("Distil-Whisper Large-v3", self.html)
        self.assertIn("Whisper Base", self.html)
        self.assertIn("WhisperX", self.html)
        self.assertIn("Edge Neural TTS", self.html)
        self.assertIn("WhisperSpeech (not bundled)", self.html)
        self.assertIn("GPT-SoVITS (not bundled)", self.html)
        # Specific model option IDs
        self.assertIn('id="model-opt-turbo"', self.html)
        self.assertIn('id="model-opt-distil-large-v3"', self.html)
        self.assertIn('id="model-opt-base"', self.html)
        self.assertIn('id="model-opt-whisperx"', self.html)
        self.assertIn('id="voice-opt-edge-neural"', self.html)
        self.assertIn('id="voice-opt-whisperspeech"', self.html)
        self.assertIn('id="voice-opt-gpt-sovits"', self.html)
        # Model tier badges
        self.assertIn("model-tier-badge", self.html)
        self.assertIn("Best Accuracy · Recommended", self.html)
        self.assertIn("High Speed", self.html)
        self.assertIn("Lightweight / Low-RAM", self.html)
        self.assertIn("Phoneme Aligned", self.html)
        self.assertIn("Network · Pitch-matched", self.html)
        self.assertIn("Unavailable · Fallback", self.html)

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

    def test_voice_advanced_controls_collapsible_accordion(self):
        """Verifies Voice Cloning UI puts advanced studio knobs into a collapsible accordion."""
        self.assertIn("voice-advanced-controls", self.html)
        self.assertIn("voice-advanced-summary", self.html)
        self.assertIn("Advanced Audio Studio & Fine-Tuning Controls", self.html)
        self.assertIn('id="voice-advanced-controls"', self.html)

    def test_model_dropdown_lockout_contracts(self):
        """Verifies model selector dropdown triggers have lockout handlers and styling to prevent race conditions."""
        self.assertIn("setTranscribeModelLocked", self.html)
        self.assertIn("setVoiceModelLocked", self.html)
        self.assertIn(".model-dropdown-trigger.locked", self.html)
        self.assertIn(".model-dropdown-trigger:disabled", self.html)

    def test_transcribed_speaker_pills_and_voice_dialog(self):
        """Verifies multi-speaker selection pills and native voice file dialog contracts."""
        self.assertIn("transcribed-speakers-pill-wrap", self.html)
        self.assertIn(".speaker-select-pill", self.html)
        self.assertIn("triggerVoiceRefFileDialog", self.html)
        self.assertIn("handleVoiceRefPath", self.html)
        self.assertIn("selectVoiceProfileByIndex", self.html)

    def test_m12_progressive_disclosure_and_drawer(self):
        """Verifies Mode 1 audio studio is tucked into a collapsible drawer with trigger button and quiet HUD."""
        self.assertIn('id="audio-tools-drawer"', self.html)
        self.assertIn('style="display: none;"', self.html, "Audio tools drawer must start hidden")
        self.assertIn('id="btn-audio-tools"', self.html)
        self.assertIn('id="audio-tools-toggle"', self.html)
        self.assertIn('onclick="toggleAudioToolsDrawer()"', self.html)
        self.assertIn('onclick="toggleAudioToolsDrawer(false)"', self.html)
        self.assertIn('id="mode1-audio-editor"', self.html)
        self.assertIn("toggleAudioToolsDrawer", self.html)
        self.assertIn('id="m1-vol-slider"', self.html)
        self.assertIn('id="m1-pitch-slider"', self.html)
        self.assertIn('id="m1-trim-start"', self.html)
        self.assertIn('id="m1-trim-end"', self.html)
        self.assertIn('id="m1-trim-start-bar"', self.html)
        self.assertIn('id="m1-trim-end-bar"', self.html)
        self.assertIn('id="m1-preview-btn"', self.html)
        self.assertIn('id="m1-export-btn"', self.html)
        # Quiet Obsidian Telemetry HUD
        self.assertIn("quiet-obsidian-hud", self.html)
        self.assertIn("hud-pill", self.html)
        self.assertIn('id="live-timecode"', self.html)
        self.assertIn('id="live-speaker"', self.html)
        self.assertIn('id="live-word-count"', self.html)

    def test_m12_consolidated_export_dropdown(self):
        """Verifies consolidated export trigger and dropdown menu supporting all 6 formats (.TXT, .MD, .SRT, .VTT, .JSON, FOLDER)."""
        self.assertIn('id="export-dropdown-wrapper"', self.html)
        self.assertIn('id="export-dropdown-trigger"', self.html)
        self.assertIn('onclick="toggleExportDropdown(event)"', self.html)
        self.assertIn('id="export-menu"', self.html)
        self.assertIn('style="display:none;"', self.html, "Export menu must start hidden")
        self.assertIn("toggleExportDropdown", self.html)
        self.assertIn("handleExportSelect", self.html)
        # Verify all 6 format handlers are explicitly wired
        self.assertIn("handleExportSelect('txt')", self.html)
        self.assertIn("handleExportSelect('md')", self.html)
        self.assertIn("handleExportSelect('srt')", self.html)
        self.assertIn("handleExportSelect('vtt')", self.html)
        self.assertIn("handleExportSelect('json')", self.html)
        self.assertIn("handleExportSelect('folder')", self.html)
        # Verify format labels and folder reveal button
        self.assertIn(".TXT", self.html)
        self.assertIn(".MD", self.html)
        self.assertIn(".SRT", self.html)
        self.assertIn(".VTT", self.html)
        self.assertIn(".JSON", self.html)
        self.assertIn('id="btn-reveal-folder"', self.html)
        self.assertIn("Open Output Folder", self.html)
        self.assertIn("revealExportFolder", self.html)

    def test_m12_voice_studio_three_step_flow(self):
        """Verifies Voice Cloning Studio is organized into a clean 3-step sequential flow with collapsible accordion."""
        self.assertIn('id="voice-ref-step"', self.html)
        self.assertIn('id="voice-text-step"', self.html)
        self.assertIn('id="voice-synthesize-step"', self.html)
        self.assertIn('id="voice-advanced-accordion"', self.html)
        self.assertIn('id="cancel-voice-btn"', self.html)
        self.assertIn("cancelVoiceSynthesis", self.html)
        # Verify sequential ordering: Step 1 -> Step 2 -> Step 3
        idx_step1 = self.html.index('id="voice-ref-step"')
        idx_step2 = self.html.index('id="voice-text-step"')
        idx_step3 = self.html.index('id="voice-synthesize-step"')
        idx_accordion = self.html.index('id="voice-advanced-accordion"')
        self.assertLess(idx_step1, idx_step2, "Step 1 must precede Step 2")
        self.assertLess(idx_step2, idx_step3, "Step 2 must precede Step 3")
        self.assertLess(idx_step3, idx_accordion, "Accordion must follow the 3 primary steps")
        # Step components
        self.assertIn('id="voice-ref-dropzone"', self.html)
        self.assertIn('id="voice-ref-input"', self.html)
        self.assertIn('id="clone-text"', self.html)
        self.assertIn('id="synthesize-btn"', self.html)
        self.assertIn('id="clone-result-box"', self.html)
        # Advanced parameters inside collapsible accordion
        self.assertIn("<details", self.html)
        self.assertIn("<summary", self.html)
        self.assertIn('id="pitch-slider"', self.html)
        self.assertIn('id="rate-slider"', self.html)
        self.assertIn('id="voice-model-switcher"', self.html)

    def test_m12_cancellation_controller_and_voice_ui_hooks(self):
        """Keeps cancellation handling for active jobs without restoring removed processing chrome."""
        self.assertNotIn('id="cancel-processing-btn"', self.html)
        self.assertIn('id="cancel-voice-btn"', self.html)
        self.assertIn('onclick="cancelVoiceSynthesis(event)"', self.html)
        self.assertIn("cancelActiveProcessing", self.html)
        self.assertIn("cancelVoiceSynthesis", self.html)
        self.assertIn("activeProcessAbortController", self.html)
        self.assertIn("activeVoiceAbortController", self.html)
        self.assertIn("/api/cancel", self.html)

    def test_processing_status_has_compact_responsive_hierarchy(self):
        """Keeps the live processing state legible without clipping at phone widths."""
        self.assertIn('class="processing-topline"', self.html)
        self.assertIn('class="processing-progress-summary"', self.html)
        self.assertIn('role="status" aria-live="polite"', self.html)
        self.assertIn('@media (max-width: 640px)', self.html)
        self.assertIn('grid-template-columns: repeat(3, minmax(0, 1fr))', self.html)
        self.assertNotIn('id="processing-file-name"', self.html)
        self.assertNotIn('id="processing-stage-pill"', self.html)
        self.assertIn("liquidCanvas.style.width = '';", self.html)
        self.assertNotIn("liquidCanvas.style.width = '220px';", self.html)
        self.assertNotIn("window.pollPerformanceTelemetry = pollPerformanceTelemetry;", self.html)

    def test_m12_white_flash_elimination(self):
        """Verifies dark background inline styling on root html, css rules, and pywebview flags."""
        self.assertIn('style="background-color: #08090C; color-scheme: dark;"', self.html)
        self.assertIn('background-color: #08090C !important', self.html)
        # Verify desktop pywebview flags in desktop.py
        from scriber import desktop
        import inspect
        desktop_src = inspect.getsource(desktop.ScriberDesktopApp._run_webview)
        self.assertIn('background_color="#08090C"', desktop_src)
        self.assertIn('--force-dark-mode', desktop_src)
        self.assertIn('--blink-settings=darkMode=4', desktop_src)


if __name__ == "__main__":
    unittest.main()



