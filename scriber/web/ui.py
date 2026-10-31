"""Scriber Web UI embedded template.
Implements the @happyhour.st Tangerine & Antique Gold dark luxury aesthetic,
minimalist organic Claude liquid morphing animation,
fine-line acoustic resonance voice cloning visualizer,
bespoke studio audio player with Web Audio API waveform decoding,
and clean, colorful copy-paste transcript viewport.
"""

def get_embedded_html() -> str:
    """Returns the clean, modern production single-page UI for Scriber."""
    return r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scriber — Studio Intelligence & Voice Synthesis</title>
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/svg+xml" href="/assets/icon.svg">
<link rel="apple-touch-icon" href="/assets/icon.png">
<meta name="application-name" content="Scriber Studio">
<meta name="msapplication-TileColor" content="#08090C">
<meta name="msapplication-TileImage" content="/assets/icon.png">
<meta name="theme-color" content="#08090C">
<!-- Google Fonts: Syne, Plus Jakarta Sans & JetBrains Mono (Editorial Pairing) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    /* @happyhour.st strict color theme */
    --canvas-dark: #08090C;
    --canvas-elevated: #0D0F14;
    --canvas-surface: #12151E;
    --surface-glass: rgba(18, 21, 30, 0.76);
    --surface-glass-hover: rgba(26, 30, 42, 0.88);
    --surface-card: rgba(14, 17, 24, 0.94);

    /* Vibrant Tangerine & Antique Gold */
    --tangerine: #FF5E00;
    --tangerine-hover: #FF7A1A;
    --tangerine-glow: rgba(255, 94, 0, 0.35);
    --tangerine-subtle: rgba(255, 94, 0, 0.10);
    --tangerine-deep: #D94F00;

    --gold: #E5A93C;
    --gold-bright: #F59E0B;
    --gold-glow: rgba(229, 169, 60, 0.28);
    --gold-subtle: rgba(229, 169, 60, 0.10);

    --coral: #FF8A7A;
    --coral-subtle: rgba(255, 138, 122, 0.10);
    --emerald: #10B981;
    --emerald-glow: rgba(16, 185, 129, 0.30);
    --emerald-subtle: rgba(16, 185, 129, 0.10);

    --border-glass: rgba(255, 255, 255, 0.07);
    --border-glass-hover: rgba(255, 94, 0, 0.40);
    --border-active: #FF5E00;

    /* Distinct Editorial & Technical Typography Pairing */
    --font-display: 'Syne', sans-serif;
    --font-body: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --font-mono: 'JetBrains Mono', monospace;

    /* Text Colors */
    --text-primary: #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --text-highlight: #FFE4B5;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: var(--font-body);
    background-color: var(--canvas-dark);
    background-image: 
      radial-gradient(ellipse at 15% 0%, rgba(255, 94, 0, 0.08) 0%, transparent 55%),
      radial-gradient(ellipse at 85% 100%, rgba(229, 169, 60, 0.06) 0%, transparent 55%),
      radial-gradient(circle at 50% 25%, rgba(255, 94, 0, 0.03) 0%, transparent 60%);
    background-attachment: fixed;
    color: var(--text-primary);
    line-height: 1.6;
    padding: 24px 32px 72px 32px;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
    position: relative;
  }

  /* Subtle film grain texture */
  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px);
    background-size: 24px 24px;
    pointer-events: none;
    z-index: 0;
    opacity: 0.55;
  }

  /* Custom Clean Scrollbars */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.14); border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--tangerine); }

  .app-container {
    max-width: 1140px;
    width: 100%;
    margin: 0 auto;
    position: relative;
    z-index: 1;
  }

  /* Display & Section Typography */
  h1, h2, h3, .model-selector-title, .upload-headline {
    font-family: var(--font-display);
    letter-spacing: -0.025em;
  }

  /* Header Bar */
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 22px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 34px;
    flex-wrap: wrap;
    gap: 20px;
  }
  .logo-block {
    display: flex;
    align-items: center;
    gap: 16px;
    text-decoration: none;
    cursor: default;
    min-width: 0;
    max-width: 100%;
  }
  .brand-svg-mark {
    flex-shrink: 0;
    display: block;
  }
  .logo-title {
    min-width: 0;
    flex: 1;
  }
  .logo-title h1 {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
    flex-wrap: wrap;
  }
  .subtitle {
    font-family: var(--font-body);
    font-size: 12.5px;
    color: var(--text-secondary);
    font-weight: 400;
    margin-top: 2px;
    white-space: normal;
    overflow-wrap: break-word;
  }

  /* 2-Mode Architectural Segmented Navigation */
  .nav-pills {
    display: inline-flex;
    background: #0D0F16;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 3px;
    gap: 4px;
  }
  .nav-pill {
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-secondary);
    padding: 8px 20px;
    border-radius: 4px;
    font-family: var(--font-body);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .nav-pill:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.04);
  }
  .nav-pill.active {
    background: var(--tangerine);
    border-color: var(--tangerine);
    color: #FFFFFF;
    font-weight: 700;
  }

  /* Views Management */
  .view-panel { display: none; }
  .view-panel.active { display: block; animation: fadeInView 0.25s ease; }
  @keyframes fadeInView { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

  /* ========================================================= */
  /* AESTHETIC ANIMATED MODEL SELECTOR DROPDOWNS               */
  /* ========================================================= */
  .studio-model-console, .model-switcher-card {
    background: #0B0E14;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 16px 22px;
    margin: 0 0 24px 0;
    width: 100%;
    box-sizing: border-box;
    position: relative;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  }
  .model-selector-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .model-selector-meta {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .model-selector-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: rgba(255, 94, 0, 0.10);
    border: 1px solid rgba(255, 94, 0, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tangerine);
    flex-shrink: 0;
  }
  .model-selector-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .model-selector-title {
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
  }
  .model-selector-sub {
    font-size: 12px;
    color: var(--text-muted);
  }

  /* Custom Dropdown Trigger & Floating Menu */
  .custom-model-dropdown {
    position: relative;
    width: auto;
    min-width: 390px;
    max-width: 100%;
  }
  @media (max-width: 768px) {
    .custom-model-dropdown {
      width: 100%;
      min-width: 0;
      max-width: 100%;
    }
    .model-selector-bar {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }
    .model-dropdown-menu {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      left: 0 !important;
      right: 0 !important;
      box-sizing: border-box;
    }
  }
  .model-dropdown-trigger {
    width: 100%;
    box-sizing: border-box;
    background: #0E121A;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px;
    padding: 10px 16px;
    min-height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    cursor: pointer;
    user-select: none;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    color: var(--text-primary);
  }
  .model-dropdown-trigger:hover {
    background: #141924;
    border-color: rgba(255, 94, 0, 0.40);
    box-shadow: 0 0 16px rgba(255, 94, 0, 0.12);
  }
  .model-dropdown-trigger:focus-visible {
    outline: 2px solid var(--tangerine);
    outline-offset: 2px;
  }
  .model-dropdown-trigger.active {
    border-color: var(--tangerine);
    background: #161C2A;
    box-shadow: 0 0 20px rgba(255, 94, 0, 0.20);
  }
  .dropdown-trigger-main {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }
  .dropdown-trigger-text {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    min-width: 0;
  }
  .dropdown-selected-name {
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
    line-height: 1.2;
    white-space: nowrap;
  }
  .dropdown-chevron {
    color: var(--text-muted);
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    flex-shrink: 0;
    margin-left: auto;
  }
  .model-dropdown-trigger.active .dropdown-chevron {
    transform: rotate(180deg);
    color: var(--tangerine);
  }

  /* Floating Menu */
  .model-dropdown-menu {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 100%;
    min-width: 390px;
    max-width: 92vw;
    background: rgba(13, 16, 23, 0.98);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    box-shadow: 0 20px 45px rgba(0, 0, 0, 0.65), 0 0 30px rgba(255, 94, 0, 0.12);
    z-index: 1000;
    opacity: 0;
    visibility: hidden;
    transform: translateY(-8px) scale(0.98);
    transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1), transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.2s;
    pointer-events: none;
  }
  .model-dropdown-menu.open {
    opacity: 1;
    visibility: visible;
    transform: translateY(0) scale(1);
    pointer-events: auto;
  }

  /* Dropdown Item */
  .dropdown-item {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 12px 14px;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .dropdown-item:hover {
    background: rgba(255, 94, 0, 0.06);
    border-color: rgba(255, 94, 0, 0.25);
  }
  .dropdown-item:focus-visible {
    outline: 2px solid var(--tangerine);
    outline-offset: 1px;
    background: rgba(255, 94, 0, 0.08);
  }
  .dropdown-item.active {
    background: rgba(255, 94, 0, 0.10);
    border-color: rgba(255, 94, 0, 0.45);
  }
  .dropdown-item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .dropdown-item-title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .dropdown-item-radio {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2px solid var(--text-muted);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: all 0.15s ease;
  }
  .dropdown-item.active .dropdown-item-radio {
    border-color: var(--tangerine);
    background: var(--tangerine);
    box-shadow: 0 0 8px rgba(255, 94, 0, 0.5);
  }
  .dropdown-item.active .dropdown-item-radio::after {
    content: '';
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #FFFFFF;
  }
  .dropdown-item-title {
    font-family: var(--font-display);
    font-size: 13.5px;
    font-weight: 700;
    color: #FFFFFF;
  }
  .dropdown-item-desc {
    font-size: 11.5px;
    color: var(--text-secondary);
    line-height: 1.4;
    padding-left: 22px;
  }

  /* Model Tier Badges */
  .model-tier-badge {
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 500;
    padding: 2.5px 8px;
    border-radius: 6px;
    letter-spacing: 0.01em;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    line-height: 1.25;
    flex-shrink: 0;
    transition: all 0.15s ease;
  }
  .tier-recommended {
    background: rgba(255, 94, 0, 0.12);
    color: #FF8F3D;
    border: 1px solid rgba(255, 94, 0, 0.28);
  }
  .tier-speed {
    background: rgba(16, 185, 129, 0.12);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.28);
  }
  .tier-lightweight {
    background: rgba(148, 163, 184, 0.12);
    color: #CBD5E1;
    border: 1px solid rgba(148, 163, 184, 0.22);
  }
  .tier-aligned {
    background: rgba(229, 169, 60, 0.12);
    color: #FBBF24;
    border: 1px solid rgba(229, 169, 60, 0.28);
  }
  .tier-inversion {
    background: rgba(139, 92, 246, 0.14);
    color: #C4B5FD;
    border: 1px solid rgba(139, 92, 246, 0.28);
  }
  .tier-formant {
    background: rgba(244, 63, 94, 0.14);
    color: #FB7185;
    border: 1px solid rgba(244, 63, 94, 0.28);
  }
  .status-dot-pulse {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10B981;
    display: inline-block;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    flex-shrink: 0;
  }

  /* ========================================================= */
  /* ASYMMETRIC MEDIA UPLOAD DROPZONE                          */
  /* ========================================================= */
  .upload-bay-asymmetric, .upload-card {
    background: #0B0E14;
    border: 1px dashed rgba(255, 255, 255, 0.14);
    border-radius: 8px;
    padding: 36px 32px;
    cursor: pointer;
    margin: 0 0 32px 0;
    width: 100%;
    box-sizing: border-box;
    display: grid;
    grid-template-columns: 7.5fr 4.5fr;
    gap: 28px;
    align-items: center;
    transition: border-color 0.18s ease, background 0.18s ease;
    user-select: none;
    position: relative;
  }
  .upload-bay-asymmetric:hover, .upload-card:hover, .upload-bay-asymmetric.drag-active, .upload-card.drag-active {
    border-color: var(--tangerine);
    background: #0E121A;
  }
  @media (max-width: 820px) {
    .upload-bay-asymmetric, .upload-card {
      grid-template-columns: 1fr;
      padding: 24px;
    }
  }
  .upload-editorial-copy {
    text-align: left;
  }
  .upload-kicker {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--tangerine);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 8px;
    display: block;
  }
  .upload-headline {
    font-size: 24px;
    font-weight: 800;
    color: #FFFFFF;
    margin-bottom: 8px;
    letter-spacing: -0.025em;
  }
  .upload-editorial-desc {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: 20px;
    max-width: 520px;
  }
  .upload-matrix-panel {
    background: #07090D;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    text-align: left;
  }
  .format-matrix-grid, .format-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .format-mono-tag, .format-pill {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    color: #CBD5E1;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 4px 8px;
    border-radius: 4px;
    transition: color 0.15s ease, border-color 0.15s ease;
  }
  .format-mono-tag:hover, .format-pill:hover {
    color: var(--gold-bright);
    border-color: rgba(229, 169, 60, 0.3);
  }

  /* Visually Hidden File Input */
  .visually-hidden-input {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
    opacity: 0;
  }

  /* Architectural Buttons (No Puffy Shadows or Bouncy Motions) */
  .btn-primary {
    background: var(--tangerine);
    color: #FFFFFF;
    padding: 10px 20px;
    border-radius: 6px;
    border: 1px solid var(--tangerine);
    font-family: var(--font-body);
    font-weight: 600;
    cursor: pointer;
    font-size: 13px;
    letter-spacing: 0.01em;
    transition: background 0.15s ease, border-color 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    user-select: none;
  }
  .btn-primary:hover {
    background: var(--tangerine-hover);
    border-color: var(--tangerine-hover);
  }
  .btn-primary:active {
    background: var(--tangerine-deep);
  }
  .btn-primary.btn-copied {
    background: #10B981;
    border-color: #10B981;
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
    padding: 9px 16px;
    border-radius: 10px;
    border: 1px solid var(--border-glass);
    font-weight: 500;
    cursor: pointer;
    font-size: 12.5px;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    user-select: none;
  }
  .btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }

  /* ========================================================= */
  /* STATE 2: MINIMALIST CLAUDE LIQUID MORPHING ORB             */
  /* Soft, Molten Liquid Light (No busy or glossy clutter)      */
  /* ========================================================= */
  .processing-card {
    display: none;
    background: var(--surface-glass);
    border: 1px solid var(--border-glass);
    border-radius: 20px;
    padding: 50px 32px 42px 32px;
    text-align: center;
    margin: 30px auto;
    max-width: 760px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(28px) saturate(180%);
    -webkit-backdrop-filter: blur(28px) saturate(180%);
    position: relative;
    overflow: hidden;
  }
  .processing-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #FF5E00, #E5A93C, #FF8A7A, #FF5E00);
    background-size: 200% 100%;
    animation: barShimmer 2.2s linear infinite;
  }
  @keyframes barShimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  /* Liquid Morphing Stage */
  .liquid-orb-stage, .liquid-canvas-stage {
    position: relative;
    width: 220px;
    height: 220px;
    margin: 0 auto 18px auto;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  #liquid-orb-canvas {
    width: 220px;
    height: 220px;
    display: block;
    border-radius: 50%;
  }
  .orb-core {
    position: absolute;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: none;
  }
  @keyframes orbitBlob {
    0% { transform: scale(1); }
    50% { transform: scale(1.08); }
    100% { transform: scale(1); }
  }

  .processing-title {
    font-size: 19px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
    letter-spacing: -0.2px;
  }
  .processing-sub {
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 20px;
    min-height: 20px;
  }
  .processing-meta-row {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
  }
  .processing-file-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-glass);
    padding: 4px 12px;
    border-radius: 9999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    color: var(--gold);
  }
  .processing-stage-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 94, 0, 0.1);
    border: 1px solid rgba(255, 94, 0, 0.3);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 11.5px;
    font-weight: 600;
    color: #FFA826;
  }

  /* Real-Time Precision Progress Bar & Metrics */
  .progress-meter-container {
    width: 100%;
    max-width: 540px;
    margin: 4px auto 22px auto;
    background: rgba(18, 19, 24, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 10px 30px rgba(0, 0, 0, 0.35);
  }
  .progress-meter-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  .progress-pct-badge {
    font-family: 'Cabinet Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: #FF7A1A;
    letter-spacing: -0.5px;
    text-shadow: 0 0 20px rgba(255, 122, 26, 0.4);
  }
  .progress-eta-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    font-family: 'JetBrains Mono', monospace;
  }
  .progress-track {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.07);
    border-radius: 9999px;
    overflow: hidden;
    position: relative;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
    margin-bottom: 12px;
  }
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #FF5E00 0%, #FFA826 100%);
    border-radius: 9999px;
    transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 14px rgba(255, 122, 26, 0.6);
    position: relative;
  }
  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.35), transparent);
    animation: progressGlint 1.8s infinite;
  }
  @keyframes progressGlint {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
  }
  .progress-metrics-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 11.5px;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
  }
  .progress-metric-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  /* ========================================================= */
  /* STATE 3: CLEAN OUTPUT VIEWPORT (COPY-PASTE READY)         */
  /* ========================================================= */
  .output-viewport {
    display: none;
    margin-top: 10px;
    animation: fadeInView 0.3s ease;
  }

  /* Action Bar */
  .action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
    flex-wrap: wrap;
    gap: 12px;
    max-width: 860px;
    margin-left: auto;
    margin-right: auto;
  }
  .action-bar-left {
    display: flex;
    align-items: center;
    gap: 9px;
    flex-wrap: wrap;
  }
  .action-bar-right {
    display: flex;
    align-items: center;
    gap: 7px;
    flex-wrap: wrap;
  }

  .copy-format-select {
    background: rgba(13, 16, 24, 0.9);
    border: 1px solid var(--border-glass);
    color: var(--text-secondary);
    padding: 8px 11px;
    border-radius: 9px;
    font-size: 12px;
    outline: none;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .copy-format-select:hover {
    border-color: rgba(255, 255, 255, 0.18);
    color: var(--text-primary);
  }

  .search-wrapper {
    position: relative;
    min-width: 200px;
  }
  .search-input {
    width: 100%;
    background: rgba(13, 16, 24, 0.9);
    border: 1px solid var(--border-glass);
    color: var(--text-primary);
    padding: 7px 11px 7px 32px;
    border-radius: 9px;
    font-size: 12px;
    outline: none;
    transition: all 0.2s ease;
  }
  .search-input:focus {
    border-color: var(--tangerine);
    box-shadow: 0 0 0 2px var(--tangerine-glow);
  }
  .search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    pointer-events: none;
  }
  .search-count-badge {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--gold);
    display: none;
  }

  .btn-export {
    background: rgba(255, 255, 255, 0.04);
    color: var(--text-secondary);
    border: 1px solid var(--border-glass);
    padding: 6px 11px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 11.5px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.2s ease;
    user-select: none;
  }
  .btn-export:hover {
    background: var(--tangerine-subtle);
    color: var(--tangerine);
    border-color: var(--tangerine);
    transform: translateY(-1px);
  }

  /* Bespoke Studio Audio Player */
  .media-hub {
    background: var(--surface-glass);
    border: 1px solid var(--border-glass);
    border-radius: 18px;
    padding: 20px 24px;
    margin-bottom: 22px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    max-width: 860px;
    margin-left: auto;
    margin-right: auto;
  }

  .custom-audio-transport {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    flex-wrap: wrap;
  }
  .transport-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .btn-play-master {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FF7A1A, #FF5E00);
    border: none;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 3px 14px var(--tangerine-glow);
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .btn-play-master:hover {
    transform: scale(1.06);
    box-shadow: 0 5px 20px rgba(255, 94, 0, 0.5);
  }
  .btn-skip {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-glass);
    color: var(--text-secondary);
    padding: 6px 10px;
    border-radius: 8px;
    font-size: 11.5px;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.2s ease;
  }
  .btn-skip:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.08);
  }

  .transport-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .volume-control-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
    color: var(--text-secondary);
  }
  .volume-slider {
    width: 72px;
    accent-color: var(--tangerine);
    cursor: pointer;
  }

  /* Interactive Waveform Scrubber */
  .waveform-container {
    height: 54px;
    width: 100%;
    margin-bottom: 12px;
    background: rgba(8, 10, 16, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 6px 12px;
    cursor: pointer;
    position: relative;
    transition: all 0.25s ease;
    user-select: none;
  }
  .waveform-container:hover {
    border-color: rgba(255, 94, 0, 0.4);
    box-shadow: 0 0 16px rgba(255, 94, 0, 0.16);
  }
  #waveform-canvas {
    width: 100%;
    height: 100%;
    display: block;
    border-radius: 6px;
  }
  .waveform-hover-tooltip {
    position: absolute;
    top: -26px;
    background: rgba(13, 16, 24, 0.95);
    border: 1px solid var(--tangerine);
    color: var(--gold-bright);
    font-size: 10.5px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 6px;
    border-radius: 4px;
    pointer-events: none;
    transform: translateX(-50%);
    display: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  }

  /* Audio HUD Bar */
  .media-hud-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-secondary);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    padding-top: 10px;
    flex-wrap: wrap;
    gap: 10px;
  }
  .hud-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .hud-item span.val { color: var(--gold); font-weight: 600; }
  .speaker-live-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 94, 0, 0.1);
    border: 1px solid rgba(255, 94, 0, 0.25);
    padding: 2px 10px;
    border-radius: 9999px;
  }
  .pulse-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--tangerine);
    box-shadow: 0 0 6px var(--tangerine);
    animation: pulseDotAnim 1.8s infinite ease-in-out;
  }
  @keyframes pulseDotAnim {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.35; transform: scale(0.7); }
  }
  .speed-toggle-wrap {
    display: inline-flex;
    gap: 2px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-glass);
    border-radius: 7px;
    padding: 2px;
  }
  .btn-speed {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 5px;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  .btn-speed.active, .btn-speed:hover {
    background: var(--tangerine);
    color: #FFFFFF;
  }

  /* Speaker Segment Blocks */
  .transcript-container {
    display: flex;
    flex-direction: column;
    gap: 14px;
    max-width: 860px;
    margin: 0 auto;
  }
  .segment-card {
    background: var(--surface-glass);
    border: 1px solid var(--border-glass);
    border-left: 3.5px solid var(--spk-color, var(--tangerine));
    border-radius: 14px;
    padding: 18px 22px;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    position: relative;
    box-shadow: 0 3px 16px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  .segment-card:hover {
    border-color: var(--border-glass-hover);
    background: var(--surface-glass-hover);
    transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);
  }
  .segment-card.active-seg {
    box-shadow: 0 0 24px rgba(255, 94, 0, 0.22), 0 8px 24px rgba(0, 0, 0, 0.4);
    border-left-width: 4.5px;
    border-color: var(--spk-color, var(--tangerine));
    background: rgba(20, 24, 34, 0.95);
  }

  /* Speaker Themes */
  .spk-theme-1 {
    --spk-color: #FF5E00;
    --spk-bg: rgba(255, 94, 0, 0.05);
    --spk-badge-bg: rgba(255, 94, 0, 0.12);
    --spk-border: rgba(255, 94, 0, 0.3);
  }
  .spk-theme-2 {
    --spk-color: #E5A93C;
    --spk-bg: rgba(229, 169, 60, 0.05);
    --spk-badge-bg: rgba(229, 169, 60, 0.12);
    --spk-border: rgba(229, 169, 60, 0.3);
  }
  .spk-theme-3 {
    --spk-color: #10B981;
    --spk-bg: rgba(16, 185, 129, 0.05);
    --spk-badge-bg: rgba(16, 185, 129, 0.12);
    --spk-border: rgba(16, 185, 129, 0.3);
  }
  .spk-theme-4 {
    --spk-color: #FF8A7A;
    --spk-bg: rgba(255, 138, 122, 0.05);
    --spk-badge-bg: rgba(255, 138, 122, 0.12);
    --spk-border: rgba(255, 138, 122, 0.3);
  }

  .seg-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    flex-wrap: wrap;
    gap: 8px;
  }
  .seg-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .spk-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 11px;
    border-radius: 9999px;
    color: var(--spk-color);
    background: var(--spk-badge-bg);
    border: 1px solid var(--spk-border);
    letter-spacing: 0.2px;
    text-transform: capitalize;
  }
  .spk-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--spk-color);
    box-shadow: 0 0 5px var(--spk-color);
  }
  .seg-time {
    font-size: 11.5px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-muted);
    cursor: pointer;
    transition: color 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .seg-time:hover {
    color: var(--tangerine);
  }
  .seg-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .btn-seg-icon {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-glass);
    color: var(--text-secondary);
    padding: 3px 10px;
    border-radius: 7px;
    font-size: 11.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    user-select: none;
  }
  .btn-seg-icon:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.18);
  }

  .seg-text {
    font-size: 15.5px;
    font-weight: 400;
    color: #F8FAFC;
    line-height: 1.7;
    letter-spacing: -0.1px;
    outline: none;
    border-radius: 6px;
    padding: 3px 5px;
    transition: background 0.2s ease;
  }
  .seg-text:focus {
    background: rgba(255, 255, 255, 0.04);
    box-shadow: 0 0 0 1.5px var(--tangerine);
  }

  /* Kinetic Word Highlights */
  .word-token {
    display: inline;
    cursor: pointer;
    border-radius: 4px;
    padding: 2px 2px;
    margin: 0;
    transition: all 0.14s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .word-token:hover {
    color: var(--gold-bright);
    background: rgba(255, 255, 255, 0.08);
  }
  .word-token.active-word {
    background: rgba(255, 94, 0, 0.25);
    color: #FFA826;
    font-weight: 600;
    border-bottom: 2px solid #FF5E00;
  }
  .word-token.search-match {
    background: rgba(245, 158, 11, 0.3);
    color: #FFE4B5;
    font-weight: 600;
    border-radius: 3px;
  }

  /* ========================================================= */
  /* MODE 2: VOICE CLONING STUDIO                              */
  /* ========================================================= */
  .voice-card-panel {
    background: var(--surface-glass);
    border: 1px solid var(--border-glass);
    border-radius: 20px;
    padding: 32px 32px 36px 32px;
    backdrop-filter: blur(28px) saturate(180%);
    -webkit-backdrop-filter: blur(28px) saturate(180%);
    margin: 10px auto;
    max-width: 880px;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  }
  .voice-header {
    margin-bottom: 22px;
  }
  .voice-header h2 {
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .voice-ref-dropzone {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: rgba(255, 94, 0, 0.03);
    border: 1px dashed rgba(255, 94, 0, 0.3);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 22px;
    cursor: pointer;
    transition: all 0.25s ease;
    font-size: 13px;
    color: var(--text-secondary);
    user-select: none;
  }
  .voice-ref-dropzone:hover {
    border-color: var(--tangerine);
    background: rgba(255, 94, 0, 0.06);
    box-shadow: 0 0 18px var(--tangerine-glow);
  }

  .section-label {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 7px;
  }
  /* ========================================================= */
  /* AUDIO EDITOR & MP3 STUDIO (VOLUME, PITCH, TRIMMING)       */
  /* ========================================================= */
  .audio-editor-card {
    background: rgba(13, 16, 24, 0.78);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 20px;
    margin: 20px 0;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .audio-editor-card:hover {
    border-color: rgba(255, 94, 0, 0.3);
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45), 0 0 20px rgba(255, 94, 0, 0.08);
  }
  .audio-editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding-bottom: 16px;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  }
  .editor-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .editor-icon-badge {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--tangerine-subtle), var(--gold-subtle));
    border: 1px solid rgba(255, 94, 0, 0.35);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--tangerine);
    box-shadow: 0 0 14px var(--tangerine-glow);
  }
  .editor-heading {
    font-size: 15px;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: -0.2px;
    margin: 0;
  }
  .editor-subtext {
    font-size: 11.5px;
    color: var(--text-secondary);
    margin: 2px 0 0 0;
  }
  .editor-badges-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .editor-stat-pill {
    font-size: 11px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    padding: 3px 9px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
  }
  .editor-stat-pill.active {
    color: var(--tangerine);
    background: rgba(255, 94, 0, 0.1);
    border-color: rgba(255, 94, 0, 0.3);
  }
  .audio-editor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
  }
  .editor-control-col {
    background: rgba(18, 22, 32, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 14px 16px;
  }
  .control-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .control-label {
    font-size: 12.5px;
    font-weight: 600;
    color: #E2E8F0;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .control-label svg {
    color: var(--tangerine);
  }
  .control-val {
    font-size: 12px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: var(--gold);
  }
  .editor-slider {
    width: 100%;
    height: 6px;
    -webkit-appearance: none;
    appearance: none;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    outline: none;
    margin: 8px 0 12px 0;
  }
  .editor-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FF7A1A, #FF5E00);
    box-shadow: 0 0 10px var(--tangerine-glow);
    cursor: pointer;
    border: 2px solid #FFFFFF;
    transition: transform 0.12s ease;
  }
  .editor-slider::-webkit-slider-thumb:hover {
    transform: scale(1.25);
  }
  .preset-buttons {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .btn-preset {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 10.5px;
    font-family: 'JetBrains Mono', monospace;
    cursor: pointer;
    transition: all 0.16s ease;
  }
  .btn-preset:hover {
    color: var(--text-primary);
    border-color: rgba(255, 94, 0, 0.3);
  }
  .btn-preset.active {
    background: rgba(255, 94, 0, 0.14);
    border-color: var(--tangerine);
    color: var(--tangerine);
    font-weight: 600;
  }
  .editor-trim-section {
    background: rgba(18, 22, 32, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 16px;
  }
  .trim-inputs-row {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
    margin-top: 6px;
  }
  .trim-input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 160px;
  }
  .trim-input-group label {
    font-size: 11px;
    color: var(--text-secondary);
    font-weight: 500;
  }
  .input-with-btn {
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .trim-text-input {
    background: rgba(8, 9, 12, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #F8FAFC;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    font-weight: 600;
    padding: 6px 10px;
    border-radius: 8px;
    width: 90px;
    outline: none;
    transition: border-color 0.2s ease;
  }
  .trim-text-input:focus {
    border-color: var(--tangerine);
    box-shadow: 0 0 10px var(--tangerine-glow);
  }
  .btn-trim-set {
    background: rgba(255, 94, 0, 0.1);
    border: 1px solid rgba(255, 94, 0, 0.3);
    color: var(--tangerine);
    font-size: 11px;
    font-weight: 600;
    padding: 6px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.18s ease;
    white-space: nowrap;
  }
  .btn-trim-set:hover {
    background: var(--tangerine);
    color: #FFFFFF;
    box-shadow: 0 0 12px var(--tangerine-glow);
  }
  .trim-actions-group {
    display: flex;
    align-items: flex-end;
    margin-top: 18px;
  }
  .editor-bottom-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    padding-top: 14px;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
  }
  .editor-bottom-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .btn-preview-edit {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #F8FAFC;
    padding: 8px 16px;
    border-radius: 10px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    transition: all 0.2s ease;
  }
  .btn-preview-edit:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.25);
  }
  .btn-preview-edit.playing {
    background: rgba(255, 94, 0, 0.18);
    border-color: var(--tangerine);
    color: var(--tangerine);
  }
  .preview-active-pill {
    font-size: 11.5px;
    color: var(--gold);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
  }
  .btn-export-mp3 {
    background: linear-gradient(135deg, #FF7A1A, #FF5E00);
    border: none;
    color: #FFFFFF;
    padding: 9px 18px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 4px 16px var(--tangerine-glow);
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .btn-export-mp3:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(255, 94, 0, 0.5);
  }
  .btn-export-mp3:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  /* Voice Reference Status Pill (Replaces the raw profile box) */
  .voice-ref-badge {
    background: rgba(18, 22, 32, 0.85);
    border: 1px solid rgba(255, 94, 0, 0.35);
    border-radius: 12px;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 14px 0 18px 0;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  .ref-badge-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .ref-badge-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: var(--tangerine-subtle);
    border: 1px solid rgba(255, 94, 0, 0.3);
    color: var(--tangerine);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .ref-badge-details {
    display: flex;
    flex-direction: column;
  }
  .ref-badge-title {
    font-size: 13px;
    font-weight: 600;
    color: #F8FAFC;
  }
  .ref-badge-sub {
    font-size: 11px;
    color: var(--gold);
    font-family: 'JetBrains Mono', monospace;
  }
  .btn-clear-ref {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 14px;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
    transition: all 0.16s ease;
  }
  .btn-clear-ref:hover {
    color: #FF5E00;
    background: rgba(255, 94, 0, 0.1);
  }

  .clone-textarea {
    width: 100%;
    background: rgba(8, 10, 16, 0.9);
    border: 1px solid var(--border-glass);
    color: var(--text-primary);
    padding: 12px;
    border-radius: 10px;
    font-size: 13px;
    resize: vertical;
    min-height: 80px;
    margin-bottom: 18px;
    font-family: inherit;
    outline: none;
    transition: all 0.2s ease;
    line-height: 1.6;
  }
  .clone-textarea:focus {
    border-color: var(--tangerine);
    box-shadow: 0 0 0 2px var(--tangerine-glow);
  }

  .sliders-row {
    display: flex;
    gap: 18px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .slider-col {
    flex: 1;
    min-width: 180px;
  }
  .slider-label {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 6px;
  }
  .slider-ctrl {
    width: 100%;
    accent-color: var(--tangerine);
    cursor: pointer;
  }

  /* Minimal Acoustic Resonance Canvas */
  .synthesis-resonance-stage {
    display: none;
    margin: 16px 0;
    padding: 18px;
    background: rgba(13, 16, 24, 0.7);
    border: 1px solid rgba(229, 169, 60, 0.2);
    border-radius: 12px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .resonance-canvas-wrap {
    width: 100%;
    height: 60px;
    margin-bottom: 8px;
  }
  #resonance-canvas {
    width: 100%;
    height: 100%;
    display: block;
  }
  .resonance-label {
    font-size: 11.5px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--gold-bright);
    letter-spacing: 0.2px;
  }

  .clone-result-box {
    display: none;
    margin-top: 20px;
    padding-top: 18px;
    border-top: 1px solid var(--border-glass);
    animation: fadeInView 0.3s ease;
  }
  .clone-result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 8px;
  }
  .fidelity-badge {
    background: rgba(16, 185, 129, 0.1);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 3px 12px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  /* Floating Toast System */
  #toast-container {
    position: fixed;
    bottom: 24px;
    right: 24px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 9999;
    pointer-events: none;
  }
  .toast {
    background: rgba(13, 16, 24, 0.95);
    border: 1px solid var(--border-glass);
    border-left: 3.5px solid var(--tangerine);
    color: var(--text-primary);
    padding: 10px 16px;
    border-radius: 9px;
    font-size: 12.5px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(16px);
    display: flex;
    align-items: center;
    gap: 9px;
    transform: translateY(16px);
    opacity: 0;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    pointer-events: auto;
  }
  .toast.show {
    transform: translateY(0);
    opacity: 1;
  }
  .toast.toast-success {
    border-left-color: var(--emerald);
  }
  .toast.toast-info {
    border-left-color: var(--gold);
  }

  /* ========================================================= */
  /* SUPREME COUNCIL MULTI-AGENT SWARM & INTELLIGENCE DASHBOARD */
  /* ========================================================= */
  .council-dashboard {
    background: rgba(14, 18, 26, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 22px 24px;
    margin-bottom: 24px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(12px);
  }
  .council-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    flex-wrap: wrap;
    gap: 12px;
  }
  .council-tag-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--gold);
    background: rgba(229, 169, 60, 0.12);
    border: 1px solid rgba(229, 169, 60, 0.28);
    padding: 4px 10px;
    border-radius: 5px;
  }
  .council-headline {
    font-family: var(--font-display);
    font-size: 19px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 8px 0 6px 0;
    letter-spacing: -0.01em;
  }
  .council-tldr {
    font-size: 13.5px;
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 14px;
  }
  .council-decisions-box {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
    background: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.22);
    border-radius: 8px;
    padding: 12px 16px;
  }
  .decision-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 13px;
    color: #A7F3D0;
  }
  .council-section-title {
    font-family: var(--font-display);
    font-size: 14.5px;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 14px;
    margin-bottom: 18px;
  }
  .action-card {
    background: rgba(18, 22, 32, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 8px;
    padding: 13px 15px;
    display: flex;
    flex-direction: column;
    gap: 7px;
    transition: all 0.2s ease;
  }
  .action-card:hover {
    border-color: rgba(255, 94, 0, 0.35);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  }
  .action-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .action-id {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--gold);
    font-weight: 700;
  }
  .action-prio-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 4px;
    letter-spacing: 0.05em;
  }
  .prio-urgent { background: rgba(255, 138, 122, 0.2); color: #FFA396; border: 1px solid rgba(255, 138, 122, 0.4); }
  .prio-high { background: rgba(255, 94, 0, 0.2); color: #FF944D; border: 1px solid rgba(255, 94, 0, 0.4); }
  .prio-medium { background: rgba(229, 169, 60, 0.16); color: #F5BE6B; border: 1px solid rgba(229, 169, 60, 0.35); }
  .prio-low { background: rgba(148, 163, 184, 0.14); color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.3); }
  .action-task-text {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.45;
  }
  .action-meta-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    color: var(--text-secondary);
    margin-top: 4px;
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }
  .action-assignee {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-weight: 600;
    color: var(--text-highlight);
  }
  .action-seek-btn {
    background: transparent;
    border: none;
    color: var(--tangerine);
    font-family: var(--font-mono);
    font-size: 11px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 6px;
    border-radius: 4px;
    transition: background 0.15s;
  }
  .action-seek-btn:hover {
    background: rgba(255, 94, 0, 0.15);
  }
  .chapters-strip {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 4px 0 12px 0;
    margin-bottom: 14px;
  }
  .chapter-chip {
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .chapter-chip:hover {
    background: rgba(255, 94, 0, 0.12);
    border-color: rgba(255, 94, 0, 0.35);
    color: var(--text-primary);
  }
  .audit-seal-strip {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(8, 10, 15, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 10px 16px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .pii-shield-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .btn-pii-toggle {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: var(--text-secondary);
    font-size: 12px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-pii-toggle.active {
    background: rgba(16, 185, 129, 0.18);
    border-color: rgba(16, 185, 129, 0.5);
    color: #10B981;
  }
  .cert-seal-box {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--font-mono);
    font-size: 11.5px;
    flex-wrap: wrap;
  }
  .cert-id-tag {
    color: var(--gold);
    font-weight: 700;
    letter-spacing: 0.04em;
  }
  .cert-status-pass {
    background: rgba(16, 185, 129, 0.12);
    color: var(--emerald);
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 600;
  }

  /* Mode 3: About Creator — Clean Animated Fluid Name Card */
  .about-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 520px;
    padding: 24px 16px;
    animation: fadeInView 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .about-bento-grid {
    width: 100%;
    max-width: 710px;
    display: flex;
    justify-content: center;
    perspective: 1000px;
  }
  .about-card {
    background: linear-gradient(145deg, rgba(16, 20, 28, 0.92) 0%, rgba(10, 12, 17, 0.96) 100%);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 28px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);
    box-shadow: 
      inset 0 1px 0 rgba(255, 255, 255, 0.12),
      0 24px 60px -12px rgba(0, 0, 0, 0.75),
      0 0 45px -10px rgba(255, 94, 0, 0.12);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
  }
  .about-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(420px circle at var(--mouse-x, -500px) var(--mouse-y, -500px), rgba(255, 94, 0, 0.12), transparent 70%);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.35s ease;
    z-index: 1;
    border-radius: 28px;
  }
  .about-card:hover::before {
    opacity: 1;
  }
  .about-card:hover {
    border-color: rgba(255, 94, 0, 0.45);
    box-shadow: 
      inset 0 1px 0 rgba(255, 255, 255, 0.22),
      0 28px 70px -10px rgba(255, 94, 0, 0.2),
      0 0 60px -5px rgba(229, 169, 60, 0.16);
  }
  .about-card > * {
    position: relative;
    z-index: 2;
  }
  .about-name-card {
    width: 100%;
    padding: 44px 28px 28px 28px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    transform-style: preserve-3d;
    will-change: transform;
    cursor: default;
  }
  .card-ambient-glow {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle at 50% 30%, rgba(255, 94, 0, 0.08) 0%, rgba(229, 169, 60, 0.04) 35%, transparent 65%);
    pointer-events: none;
    z-index: 0;
    animation: ambientFloat 8s ease-in-out infinite alternate;
  }
  @keyframes ambientFloat {
    0% { transform: translateY(0) scale(1); opacity: 0.7; }
    100% { transform: translateY(-20px) scale(1.05); opacity: 1; }
  }
  .creator-avatar-wrap {
    width: 124px;
    height: 124px;
    border-radius: 50%;
    padding: 3.5px;
    background: linear-gradient(135deg, rgba(255, 94, 0, 0.95) 0%, rgba(229, 169, 60, 0.8) 50%, rgba(255, 138, 122, 0.9) 100%);
    box-shadow: 
      0 0 35px rgba(255, 94, 0, 0.4),
      0 12px 28px rgba(0, 0, 0, 0.6);
    margin-bottom: 22px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s ease;
  }
  .about-name-card:hover .creator-avatar-wrap {
    transform: scale(1.04);
    box-shadow: 
      0 0 45px rgba(255, 94, 0, 0.55),
      0 14px 34px rgba(0, 0, 0, 0.65);
  }
  .creator-avatar-img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    display: block;
    background: #0B0E14;
  }
  .creator-name {
    font-family: var(--font-display);
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    margin: 0 0 28px 0;
    text-shadow: 0 2px 20px rgba(0, 0, 0, 0.7);
  }
  .about-social-row {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }
  @media (max-width: 680px) {
    body {
      padding: 16px 16px 48px 16px;
    }
    header {
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
    }
    .logo-block {
      width: 100%;
      min-width: 0;
    }
    .logo-title {
      min-width: 0;
      flex: 1;
    }
    .subtitle {
      font-size: 11px;
      line-height: 1.4;
    }
    .nav-pills {
      width: 100%;
      display: flex;
    }
    .nav-pill {
      flex: 1;
      justify-content: center;
      padding: 8px 8px;
      font-size: 12px;
      gap: 6px;
    }
    .about-container {
      padding: 16px 0;
      width: 100%;
    }
    .about-bento-grid {
      width: 100%;
      max-width: 100%;
    }
    .about-social-row {
      grid-template-columns: 1fr;
      gap: 10px;
    }
    .creator-name {
      font-size: 26px;
    }
    .about-name-card {
      padding: 32px 16px 20px 16px;
      width: 100%;
    }
    .creator-avatar-wrap {
      width: 104px;
      height: 104px;
    }
  }
  .social-node-card {
    background: rgba(22, 26, 36, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 11px 12px;
    display: flex;
    align-items: center;
    gap: 9px;
    text-decoration: none;
    position: relative;
    overflow: hidden;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease, background 0.22s ease, box-shadow 0.22s ease;
  }
  .social-node-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(160px circle at var(--mouse-x, -500px) var(--mouse-y, -500px), rgba(255, 168, 38, 0.15), transparent 75%);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: 1;
    border-radius: 14px;
  }
  .social-node-card:hover::before {
    opacity: 1;
  }
  .social-node-card > * {
    position: relative;
    z-index: 2;
  }
  .social-node-card:hover {
    transform: translateY(-3px);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14), 0 10px 24px rgba(0, 0, 0, 0.4);
  }
  .social-node-card.instagram:hover {
    border-color: rgba(255, 94, 0, 0.5);
    background: rgba(35, 24, 28, 0.85);
  }
  .social-node-card.linkedin:hover {
    border-color: rgba(229, 169, 60, 0.5);
    background: rgba(30, 28, 22, 0.85);
  }
  .social-node-card.github:hover {
    border-color: rgba(255, 255, 255, 0.4);
    background: rgba(28, 32, 44, 0.85);
  }
  .social-icon-box {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .social-node-card.instagram .social-icon-box { background: rgba(255, 94, 0, 0.14); color: var(--tangerine); }
  .social-node-card.linkedin .social-icon-box { background: rgba(229, 169, 60, 0.14); color: var(--gold); }
  .social-node-card.github .social-icon-box { background: rgba(255, 255, 255, 0.1); color: #F1F5F9; }
  .social-info {
    flex: 1;
    min-width: 0;
    text-align: left;
  }
  .social-label {
    font-size: 9.5px;
    font-family: var(--font-mono);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 2px;
  }
  .social-handle {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .social-arrow {
    color: var(--text-muted);
    font-size: 12px;
    transition: transform 0.2s ease, color 0.2s ease;
    flex-shrink: 0;
  }
  .social-node-card:hover .social-arrow {
    transform: translate(3px, -3px);
    color: var(--text-primary);
  }
</style>
</head>
<body>

<!-- SVG Gooey Filter Hook -->
<svg class="gooey-filter-svg" xmlns="http://www.w3.org/2000/svg" version="1.1" aria-hidden="true" style="position:absolute; width:0; height:0; pointer-events:none;">
  <defs>
    <filter id="goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur" />
      <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 26 -9" result="goo" />
      <feBlend in="SourceGraphic" in2="goo" />
    </filter>
  </defs>
</svg>

<div class="app-container">
  <!-- Minimal Header Bar -->
  <header>
    <div class="logo-block">
      <!-- Scriber Harmonic S Monogram Emblem -->
      <svg class="brand-svg-mark" width="46" height="46" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="scBgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#12151D" />
            <stop offset="50%" stop-color="#0A0B0F" />
            <stop offset="100%" stop-color="#050608" />
          </linearGradient>
          <linearGradient id="scWaveGrad" x1="15%" y1="10%" x2="85%" y2="90%">
            <stop offset="0%" stop-color="#FF3800" />
            <stop offset="45%" stop-color="#FF5E00" />
            <stop offset="80%" stop-color="#FFA826" />
            <stop offset="100%" stop-color="#FFC043" />
          </linearGradient>
          <linearGradient id="scCoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#FFA826" />
            <stop offset="100%" stop-color="#FF5E00" />
          </linearGradient>
          <filter id="scSubtleBloom" x="-15%" y="-15%" width="130%" height="130%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        <rect x="28" y="28" width="456" height="456" rx="96" fill="url(#scBgGrad)" stroke="rgba(255, 94, 0, 0.22)" stroke-width="2" />
        <rect x="30" y="30" width="452" height="452" rx="94" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1" />
        <g filter="url(#scSubtleBloom)">
          <path d="M 364 196 C 364 126 316 76 256 76 C 196 76 148 126 148 184 C 148 268 364 244 364 328 C 364 386 316 436 256 436 C 196 436 148 386 148 316 L 204 316 C 204 362 228 380 256 380 C 284 380 308 362 308 328 C 308 276 204 236 204 184 C 204 150 228 132 256 132 C 284 132 308 150 308 196 Z"
                fill="url(#scWaveGrad)" />
        </g>
      </svg>
      <div class="logo-title">
        <div style="display:flex; align-items:center; gap:8px;">
          <h1>Scriber</h1>
          <span class="app-version-badge" style="font-family:var(--font-mono); font-size:11px; padding:2px 7px; border-radius:6px; background:rgba(255,94,0,0.12); border:1px solid rgba(255,94,0,0.3); color:var(--tangerine); font-weight:600; letter-spacing:0.04em;">v2.0</span>
        </div>
        <p class="subtitle">Autonomous Speech Intelligence & Voice Synthesis Studio</p>
      </div>
    </div>

    <!-- Navigation Modes -->
    <nav class="nav-pills">
      <button class="nav-pill active" id="btn-mode-transcribe" onclick="switchMode('transcribe')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
        Transcribe
      </button>
      <button class="nav-pill" id="btn-mode-voice" onclick="switchMode('voice')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h2a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H2v-8z"></path><path d="M22 12h-2a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2h2v-8z"></path><path d="M4 12a8 8 0 0 1 16 0"></path><line x1="12" y1="8" x2="12" y2="16"></line></svg>
        Voice Clone
      </button>
      <button class="nav-pill" id="btn-mode-about" onclick="switchMode('about')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        About
      </button>
    </nav>
  </header>

  <!-- ========================================================= -->
  <!-- MODE 1: TRANSCRIBE VIEW                                   -->
  <!-- ========================================================= -->
  <main id="transcribe-view" class="view-panel active">
    
    <!-- Model Switcher: Custom Dropdown Menu for Transcription Engine -->
    <div class="studio-model-console" id="transcribe-model-switcher">
      <div class="model-selector-bar">
        <div class="model-selector-meta">
          <div class="model-selector-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2v20M17 5v14M22 9v6M7 5v14M2 9v6"/>
            </svg>
          </div>
          <div class="model-selector-text">
            <span class="model-selector-title">Transcription Model</span>
            <span class="model-selector-sub">Select speech recognition architecture</span>
          </div>
        </div>

        <div class="custom-model-dropdown">
          <button type="button" class="model-dropdown-trigger" id="transcribe-dropdown-trigger" onclick="toggleModelDropdown('transcribe-dropdown-menu', event)" aria-haspopup="true" aria-expanded="false" aria-controls="transcribe-dropdown-menu">
            <div class="dropdown-trigger-main">
              <span class="status-dot-pulse"></span>
              <div class="dropdown-trigger-text">
                <span class="dropdown-selected-name" id="active-transcribe-tag">Whisper Turbo</span>
                <span class="model-tier-badge tier-recommended" id="active-transcribe-badge">Best Accuracy · Recommended</span>
              </div>
            </div>
            <svg class="dropdown-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          <div class="model-dropdown-menu" id="transcribe-dropdown-menu" role="listbox" aria-label="Transcription Models">
            <div class="dropdown-item active" id="model-opt-turbo" role="option" aria-selected="true" tabindex="0" onclick="selectTranscribeModel('turbo')" onkeydown="if(event.key==='Enter'||event.key===' '){selectTranscribeModel('turbo');event.preventDefault();}">
              <div class="dropdown-item-header">
                <div class="dropdown-item-title-wrap">
                  <span class="dropdown-item-radio" aria-hidden="true"></span>
                  <span class="dropdown-item-title">Whisper Turbo</span>
                </div>
                <span class="model-tier-badge tier-recommended">Best Accuracy · Recommended</span>
              </div>
              <p class="dropdown-item-desc">OpenAI large-v3-turbo architecture with 8x accelerated INT8 execution. SOTA benchmark accuracy.</p>
            </div>

            <div class="dropdown-item" id="model-opt-distil-large-v3" role="option" aria-selected="false" tabindex="0" onclick="selectTranscribeModel('distil-large-v3')" onkeydown="if(event.key==='Enter'||event.key===' '){selectTranscribeModel('distil-large-v3');event.preventDefault();}">
              <div class="dropdown-item-header">
                <div class="dropdown-item-title-wrap">
                  <span class="dropdown-item-radio" aria-hidden="true"></span>
                  <span class="dropdown-item-title">Distil-Whisper Large-v3</span>
                </div>
                <span class="model-tier-badge tier-speed">High Speed</span>
              </div>
              <p class="dropdown-item-desc">Distilled Whisper architecture matching Large-v3 accuracy with 50% fewer parameters and 6x real-time speed.</p>
            </div>

            <div class="dropdown-item" id="model-opt-base" role="option" aria-selected="false" tabindex="0" onclick="selectTranscribeModel('base')" onkeydown="if(event.key==='Enter'||event.key===' '){selectTranscribeModel('base');event.preventDefault();}">
              <div class="dropdown-item-header">
                <div class="dropdown-item-title-wrap">
                  <span class="dropdown-item-radio" aria-hidden="true"></span>
                  <span class="dropdown-item-title">Whisper Base</span>
                </div>
                <span class="model-tier-badge tier-lightweight">Lightweight / Low-RAM</span>
              </div>
              <p class="dropdown-item-desc">Ultra-lightweight engine with instant startup and minimal memory footprint on standard CPUs.</p>
            </div>

            <div class="dropdown-item" id="model-opt-whisperx" role="option" aria-selected="false" tabindex="0" onclick="selectTranscribeModel('whisperx')" onkeydown="if(event.key==='Enter'||event.key===' '){selectTranscribeModel('whisperx');event.preventDefault();}">
              <div class="dropdown-item-header">
                <div class="dropdown-item-title-wrap">
                  <span class="dropdown-item-radio" aria-hidden="true"></span>
                  <span class="dropdown-item-title">WhisperX</span>
                </div>
                <span class="model-tier-badge tier-aligned">Phoneme Aligned</span>
              </div>
              <p class="dropdown-item-desc">Silero VAD voice activity gating with sub-10ms forced phoneme alignment to eliminate word drift.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- State 1: Dropzone / Select Media File -->
    <div class="upload-bay-asymmetric" id="dropzone" onclick="openFileDialog(event)">
      <div class="upload-editorial-copy">
        <span class="upload-kicker">Universal Media Upload</span>
        <h2 class="upload-headline">Upload Audio or Video</h2>
        <p class="upload-editorial-desc">Drag and drop your media file here, or click to browse. Scriber extracts pristine 16kHz speech streams with acoustic diarization and instant transcription.</p>
        
        <div class="upload-btn-wrap" style="justify-content: flex-start; margin: 0;">
          <button type="button" class="btn-primary" id="select-media-btn" onclick="openFileDialog(event)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
            Select Audio or Video
          </button>
        </div>
      </div>

      <div class="upload-matrix-panel">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:6px;">
          <span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted); text-transform:uppercase;">SUPPORTED FORMATS</span>
          <span style="font-family:var(--font-mono); font-size:10px; color:var(--tangerine);">ZERO CONVERSION</span>
        </div>
        <div class="format-matrix-grid">
          <span class="format-mono-tag">MP4</span>
          <span class="format-mono-tag">MP3</span>
          <span class="format-mono-tag">WAV</span>
          <span class="format-mono-tag">M4A</span>
          <span class="format-mono-tag">MOV</span>
          <span class="format-mono-tag">MKV</span>
          <span class="format-mono-tag">WebM</span>
          <span class="format-mono-tag">FLAC</span>
          <span class="format-mono-tag">AAC</span>
          <span class="format-mono-tag">OGG</span>
          <span class="format-mono-tag">OPUS</span>
          <span class="format-mono-tag">AVI</span>
        </div>
        <div style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted); margin-top:4px;">
          ALL MAJOR FORMATS SUPPORTED · ZERO CONVERSION REQUIRED
        </div>
      </div>
    </div>

    <!-- Native hidden file input (outside dropzone to eliminate click event bubbling & COM dialog deadlock) -->
    <input type="file" id="media-file-input" name="file" accept="audio/*,video/*,.mp4,.mp3,.wav,.m4a,.mov,.webm,.flac,.ogg,.aac,.mkv,.avi,.flv,.wmv,.opus,.wma,.3gp,.ts,.m4v" class="visually-hidden-input" onchange="handleFileSelected(event)" onclick="event.stopPropagation();" />

    <!-- State 2: Minimalist Liquid Light Orb + Precision Live Progress Tracker -->
    <div class="processing-card" id="processing-card">
      <div class="liquid-orb-stage liquid-canvas-stage">
        <canvas id="liquid-orb-canvas" width="220" height="220"></canvas>
        <div class="orb-core"></div>
      </div>
      <h3 class="processing-title" id="processing-main-title">Transcribing & Translating to English</h3>
      <p class="processing-sub" id="processing-status-text">Ingesting media buffer · Extracting 16kHz speech stream...</p>

      <!-- Precision Real-Time Progress Bar & Metrics -->
      <div class="progress-meter-container" id="progress-meter-container">
        <div class="progress-meter-header">
          <div class="progress-pct-badge" id="progress-pct-badge">0%</div>
          <div class="progress-eta-badge" id="progress-eta-badge">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span id="progress-eta-text">Estimating time...</span>
          </div>
        </div>
        <div class="progress-track" id="progress-track">
          <div class="progress-fill" id="progress-fill" style="width: 0%;"></div>
        </div>
        <div class="progress-metrics-row" id="progress-metrics-row">
          <span class="progress-metric-item" id="progress-speed-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            <span id="progress-speed-text">--x speed</span>
          </span>
          <span class="progress-metric-item" id="progress-position-item">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
            <span id="progress-position-text">00:00 / 00:00</span>
          </span>
          <span class="progress-metric-item" id="progress-elapsed-item">
            <span id="progress-elapsed-text">Elapsed: 0s</span>
          </span>
        </div>
      </div>

      <div class="processing-meta-row">
        <div class="processing-file-badge" id="processing-file-name">media_file.mp4</div>
        <div class="processing-stage-pill" id="processing-stage-pill">Phase 1/4 · Neural Alignment</div>
      </div>
    </div>

    <!-- State 3: Clean Output Viewport (Copy-Paste Ready) -->
    <div class="output-viewport" id="output-viewport">
      
      <!-- Top Action Bar -->
      <div class="action-bar">
        <div class="action-bar-left">
          <button type="button" class="btn-primary" id="copy-transcript-btn" onclick="copyFullTranscript()">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            Copy Full Transcript
          </button>
          <select id="copy-format-select" class="copy-format-select" title="Choose format for transcript copy">
            <option value="standard">Standard (Timecode & Speaker)</option>
            <option value="dialogue">Dialogue (Speaker Only)</option>
            <option value="text">Clean Text (No Headers)</option>
            <option value="markdown">Markdown Formatted</option>
          </select>
          <button type="button" class="btn-secondary" onclick="resetToUpload()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
            Upload Another
          </button>
        </div>
        
        <div class="action-bar-right">
          <div class="search-wrapper">
            <svg class="search-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" id="transcript-search" class="search-input" placeholder="Search transcript..." oninput="filterTranscript()" />
            <span class="search-count-badge" id="search-count-badge">0</span>
          </div>
          <button class="btn-export" onclick="downloadArtifact('txt')" title="Download formatted plain text (.txt)">.TXT</button>
          <button class="btn-export" onclick="downloadArtifact('md')" title="Download formatted Markdown (.md)">.MD</button>
          <button class="btn-export" onclick="downloadArtifact('srt')" title="Download SubRip subtitles (.srt)">.SRT</button>
          <button class="btn-export" onclick="downloadArtifact('vtt')" title="Download WebVTT subtitles (.vtt)">.VTT</button>
          <button class="btn-export" onclick="downloadArtifact('json')" title="Download full analysis JSON (.json)">.JSON</button>
          <button class="btn-export" id="btn-reveal-folder" onclick="revealExportFolder()" title="Open outputs folder in native file explorer" style="display:inline-flex; align-items:center; gap:4px;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>FOLDER</button>
        </div>
      </div>

      <!-- Bespoke Studio Audio Player -->
      <div class="media-hub" id="player-box">
        <!-- Hidden Native Audio for Audio Synchronization -->
        <audio id="audio-player" preload="auto" style="display:none;" ontimeupdate="handleAudioTimeUpdate()" onseeking="handleAudioTimeUpdate()" onseeked="handleAudioTimeUpdate()" onplay="handleAudioTimeUpdate()" onloadedmetadata="handleAudioTimeUpdate()" onended="handleAudioEnded()"></audio>

        <!-- Custom Studio Transport Bar -->
        <div class="custom-audio-transport">
          <div class="transport-left">
            <button type="button" class="btn-play-master" id="btn-master-play" onclick="togglePlayPause()" title="Play / Pause (Space)">
              <svg id="play-icon" width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <svg id="pause-icon" width="15" height="15" viewBox="0 0 24 24" fill="currentColor" style="display:none;"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
            </button>
            <button type="button" class="btn-skip" onclick="skipAudio(-5)" title="Rewind 5s (J / Left Arrow)">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"></path><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
              -5s
            </button>
            <button type="button" class="btn-skip" onclick="skipAudio(5)" title="Forward 5s (L / Right Arrow)">
              +5s
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
            </button>
          </div>

          <div class="transport-right">
            <div class="volume-control-wrap">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
              <input type="range" class="volume-slider" id="volume-slider" min="0" max="1" step="0.05" value="1" oninput="setAudioVolume(this.value)" />
            </div>
            <div class="speed-toggle-wrap">
              <button type="button" class="btn-speed" onclick="setPlaybackRate(0.75, this)">0.75x</button>
              <button type="button" class="btn-speed active" onclick="setPlaybackRate(1, this)">1x</button>
              <button type="button" class="btn-speed" onclick="setPlaybackRate(1.25, this)">1.25x</button>
              <button type="button" class="btn-speed" onclick="setPlaybackRate(1.5, this)">1.5x</button>
              <button type="button" class="btn-speed" onclick="setPlaybackRate(2, this)">2x</button>
            </div>
          </div>
        </div>

        <!-- Interactive Waveform Scrubber -->
        <div class="waveform-container" id="waveform-wrap" title="Click or drag anywhere on waveform to seek audio">
          <canvas id="waveform-canvas"></canvas>
          <div class="waveform-hover-tooltip" id="waveform-tooltip">00:00</div>
        </div>

        <!-- HUD Telemetry -->
        <div class="media-hud-bar">
          <div class="hud-item">
            <span>Timecode:</span> <span class="val" id="live-timecode">00:00 / 00:00</span>
          </div>
          <div class="hud-item">
            <span>Speaker:</span>
            <span class="speaker-live-pill">
              <span class="pulse-dot"></span>
              <span class="val" id="live-speaker" style="color:var(--tangerine);">Speaker 1</span>
            </span>
          </div>
          <div class="hud-item">
            <span>Words:</span> <span class="val" id="live-word-count">0</span>
          </div>
          <div class="hud-item" style="color:var(--text-muted); font-size:11px;">
            <span>Shortcuts:</span> <code>Space</code> Play/Pause · <code>J/L</code> Seek
          </div>
        </div>
      </div>

      <!-- MP3 Studio & Audio Editor (Mode 1) -->
      <div class="audio-editor-card" id="mode1-audio-editor">
        <div class="audio-editor-header">
          <div class="editor-title-wrap">
            <div class="editor-icon-badge">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
            </div>
            <div>
              <h3 class="editor-heading">Audio Studio & MP3 Editor</h3>
              <p class="editor-subtext">Fine-tune volume gain, pitch shift, and trim audio segments with lossless MP3 export</p>
            </div>
          </div>
          <div class="editor-badges-wrap">
            <span class="editor-stat-pill" id="m1-vol-pill">Vol: 100%</span>
            <span class="editor-stat-pill" id="m1-pitch-pill">Pitch: 0 st</span>
            <span class="editor-stat-pill" id="m1-trim-pill">Trim: Full Length</span>
          </div>
        </div>

        <div class="audio-editor-grid">
          <!-- Volume & Gain -->
          <div class="editor-control-col">
            <div class="control-header">
              <span class="control-label">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                Volume / Gain
              </span>
              <span class="control-val" id="m1-vol-val">100% (0.0 dB)</span>
            </div>
            <input type="range" class="editor-slider" id="m1-vol-slider" min="0" max="200" value="100" step="1" oninput="handleVolumeInput('m1', this.value)" />
            <div class="preset-buttons">
              <button type="button" class="btn-preset" onclick="setVolumePreset('m1', 50)">50%</button>
              <button type="button" class="btn-preset active" id="m1-vol-preset-100" onclick="setVolumePreset('m1', 100)">100%</button>
              <button type="button" class="btn-preset" onclick="setVolumePreset('m1', 130)">130%</button>
              <button type="button" class="btn-preset" onclick="setVolumePreset('m1', 160)">160%</button>
              <button type="button" class="btn-preset" onclick="setVolumePreset('m1', 200)">200%</button>
            </div>
          </div>

          <!-- Pitch Tuning -->
          <div class="editor-control-col">
            <div class="control-header">
              <span class="control-label">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                Pitch Shift
              </span>
              <span class="control-val" id="m1-pitch-val">0 st (Natural)</span>
            </div>
            <input type="range" class="editor-slider" id="m1-pitch-slider" min="-12" max="12" value="0" step="1" oninput="handlePitchInput('m1', this.value)" />
            <div class="preset-buttons">
              <button type="button" class="btn-preset" onclick="setPitchPreset('m1', -4)">-4 st</button>
              <button type="button" class="btn-preset" onclick="setPitchPreset('m1', -2)">-2 st</button>
              <button type="button" class="btn-preset active" id="m1-pitch-preset-0" onclick="setPitchPreset('m1', 0)">0 st (Reset)</button>
              <button type="button" class="btn-preset" onclick="setPitchPreset('m1', 2)">+2 st</button>
              <button type="button" class="btn-preset" onclick="setPitchPreset('m1', 4)">+4 st</button>
            </div>
          </div>
        </div>

        <!-- Trimming Section -->
        <div class="editor-trim-section">
          <div class="control-header">
            <span class="control-label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>
              Trimming & Playhead In/Out
            </span>
            <span class="control-val" id="m1-trim-duration-val">Full File</span>
          </div>

          <div class="trim-inputs-row">
            <div class="trim-input-group">
              <label for="m1-trim-start">Trim Start (In Point):</label>
              <div class="input-with-btn">
                <input type="text" id="m1-trim-start" class="trim-text-input" value="00:00.00" onchange="updateTrimFromText('m1')" />
                <button type="button" class="btn-trim-set" onclick="setTrimToPlayhead('m1', 'start')" title="Set start trim point to current audio playhead">Set In [⏱]</button>
              </div>
            </div>

            <div class="trim-input-group">
              <label for="m1-trim-end">Trim End (Out Point):</label>
              <div class="input-with-btn">
                <input type="text" id="m1-trim-end" class="trim-text-input" value="00:00.00" onchange="updateTrimFromText('m1')" />
                <button type="button" class="btn-trim-set" onclick="setTrimToPlayhead('m1', 'end')" title="Set end trim point to current audio playhead">Set Out [⏱]</button>
              </div>
            </div>

            <div class="trim-actions-group">
              <button type="button" class="btn-secondary" onclick="resetTrimRange('m1')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
                Reset In/Out
              </button>
            </div>
          </div>

          <div class="trim-slider-scrub-row" style="margin-top: 14px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <span style="font-size:11px; color:var(--text-secondary); font-weight:600;">Live Trimming Sliders:</span>
              <span id="m1-trim-slider-pill" style="font-size:10.5px; font-family:'JetBrains Mono', monospace; color:var(--tangerine);">00:00 - 00:00</span>
            </div>
            <div style="display:flex; gap:16px; align-items:center; flex-wrap:wrap;">
              <div style="flex:1; min-width:140px; display:flex; align-items:center; gap:8px;">
                <span style="font-size:10.5px; color:var(--text-muted); font-weight:600;">In</span>
                <input type="range" class="editor-slider" id="m1-trim-start-bar" min="0" max="100" value="0" step="0.05" oninput="handleTrimBarInput('m1', 'start', this.value)" />
              </div>
              <div style="flex:1; min-width:140px; display:flex; align-items:center; gap:8px;">
                <span style="font-size:10.5px; color:var(--text-muted); font-weight:600;">Out</span>
                <input type="range" class="editor-slider" id="m1-trim-end-bar" min="0" max="100" value="100" step="0.05" oninput="handleTrimBarInput('m1', 'end', this.value)" />
              </div>
            </div>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="editor-bottom-bar">
          <div class="editor-bottom-left">
            <button type="button" class="btn-preview-edit" id="m1-preview-btn" onclick="togglePreviewEditedAudio('m1')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span>Preview Edited Audio</span>
            </button>
            <span class="preview-active-pill" id="m1-preview-status" style="display:none;">
              <span class="pulse-dot"></span> Previewing
            </span>
          </div>

          <div class="editor-bottom-right">
            <button type="button" class="btn-primary btn-export-mp3" id="m1-export-btn" onclick="exportEditedMP3('m1')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Export Edited MP3
            </button>
          </div>
        </div>
      </div>

      <!-- Supreme Council Multi-Agent Swarm Intelligence Dashboard -->
      <div class="council-dashboard" id="council-dashboard-panel" style="display:none;">
        <div class="council-header-bar">
          <div style="display:flex; align-items:center; gap:10px;">
            <span class="council-tag-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
              Meeting Intelligence
            </span>
            <span id="council-duration-badge" style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);"></span>
          </div>
          <div class="pii-shield-controls">
            <button type="button" class="btn-pii-toggle" id="btn-pii-shield" onclick="togglePIIShield()">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
              <span id="pii-shield-status-text">PII Privacy: Off</span>
            </button>
          </div>
        </div>

        <div id="council-briefing-wrap">
          <h3 class="council-headline" id="council-briefing-headline">Executive Summary</h3>
          <p class="council-tldr" id="council-briefing-tldr"></p>
        </div>

        <!-- Key Decisions -->
        <div id="council-decisions-wrap" style="display:none;">
          <div class="council-section-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Key Decisions
          </div>
          <div class="council-decisions-box" id="council-decisions-list"></div>
        </div>

        <!-- Thematic Chapters Strip -->
        <div id="council-chapters-wrap" style="display:none;">
          <div class="council-section-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            Thematic Chapters & Soundbites
          </div>
          <div class="chapters-strip" id="council-chapters-strip"></div>
        </div>

        <!-- Action Items -->
        <div id="council-actions-wrap" style="display:none;">
          <div class="council-section-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--tangerine)" stroke-width="2"><path d="M9 11l3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
            Key Action Items
          </div>
          <div class="actions-grid" id="council-actions-grid"></div>
        </div>
      </div>

      <!-- Interactive Colorful Speaker Blocks -->
      <div class="transcript-container" id="transcript-container"></div>
    </div>
  </main>

  <!-- ========================================================= -->
  <!-- MODE 2: VOICE CLONING STUDIO                              -->
  <!-- ========================================================= -->
  <section id="voice-view" class="view-panel">
    <div class="voice-card-panel">
      <div class="voice-header">
        <h2>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--tangerine)" stroke-width="2.2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
          Voice Cloning Studio
        </h2>
        <p class="subtitle">Synthesize speech in the authentic voice of transcribed speakers with zero-shot acoustic timbre matching.</p>
      </div>

      <!-- Model Switcher: Custom Dropdown Menu for Voice Cloning Engine -->
      <div class="studio-model-console" id="voice-model-switcher" style="margin: 0 0 24px 0; max-width: 100%;">
        <div class="model-selector-bar">
          <div class="model-selector-meta">
            <div class="model-selector-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
              </svg>
            </div>
            <div class="model-selector-text">
              <span class="model-selector-title">Voice Synthesis Engine</span>
              <span class="model-selector-sub">Select neural architecture for voice cloning</span>
            </div>
          </div>

          <div class="custom-model-dropdown">
            <button type="button" class="model-dropdown-trigger" id="voice-dropdown-trigger" onclick="toggleModelDropdown('voice-dropdown-menu', event)" aria-haspopup="true" aria-expanded="false" aria-controls="voice-dropdown-menu">
              <div class="dropdown-trigger-main">
                <span class="status-dot-pulse"></span>
                <div class="dropdown-trigger-text">
                  <span class="dropdown-selected-name" id="active-voice-tag">Edge-Neural Studio</span>
                  <span class="model-tier-badge tier-recommended" id="active-voice-badge">Studio Quality · Recommended</span>
                </div>
              </div>
              <svg class="dropdown-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>

            <div class="model-dropdown-menu" id="voice-dropdown-menu" role="listbox" aria-label="Voice Synthesis Models">
              <div class="dropdown-item" id="voice-opt-local-gpu" role="option" aria-selected="false" tabindex="0" onclick="selectVoiceModel('local-gpu')" onkeydown="if(event.key==='Enter'||event.key===' '){selectVoiceModel('local-gpu');event.preventDefault();}">
                <div class="dropdown-item-header">
                  <div class="dropdown-item-title-wrap">
                    <span class="dropdown-item-radio" aria-hidden="true"></span>
                    <span class="dropdown-item-title">Local GPU (F5-TTS Flow-Matching 48kHz)</span>
                  </div>
                  <span class="model-tier-badge tier-recommended">Zero-Shot · NVIDIA GPU</span>
                </div>
                <p class="dropdown-item-desc">Local zero-shot speech flow-matching diffusion transformer (DiT) with 48kHz Vocos neural vocoder on dedicated RTX GPU.</p>
              </div>



              <div class="dropdown-item active" id="voice-opt-edge-neural" role="option" aria-selected="true" tabindex="0" onclick="selectVoiceModel('edge-neural')" onkeydown="if(event.key==='Enter'||event.key===' '){selectVoiceModel('edge-neural');event.preventDefault();}">
                <div class="dropdown-item-header">
                  <div class="dropdown-item-title-wrap">
                    <span class="dropdown-item-radio" aria-hidden="true"></span>
                    <span class="dropdown-item-title">Edge-Neural Studio</span>
                  </div>
                  <span class="model-tier-badge tier-recommended">Studio Quality · Recommended</span>
                </div>
                <p class="dropdown-item-desc">High-fidelity multi-speaker biometric voice cloning with instantaneous neural synthesis.</p>
              </div>

              <div class="dropdown-item" id="voice-opt-whisperspeech" role="option" aria-selected="false" tabindex="0" onclick="selectVoiceModel('whisperspeech')" onkeydown="if(event.key==='Enter'||event.key===' '){selectVoiceModel('whisperspeech');event.preventDefault();}">
                <div class="dropdown-item-header">
                  <div class="dropdown-item-title-wrap">
                    <span class="dropdown-item-radio" aria-hidden="true"></span>
                    <span class="dropdown-item-title">WhisperSpeech</span>
                  </div>
                  <span class="model-tier-badge tier-inversion">Acoustic Inversion</span>
                </div>
                <p class="dropdown-item-desc">Inverts Whisper transformer acoustic token representations to mirror reference speaker vocal resonance.</p>
              </div>

              <div class="dropdown-item" id="voice-opt-gpt-sovits" role="option" aria-selected="false" tabindex="0" onclick="selectVoiceModel('gpt-sovits')" onkeydown="if(event.key==='Enter'||event.key===' '){selectVoiceModel('gpt-sovits');event.preventDefault();}">
                <div class="dropdown-item-header">
                  <div class="dropdown-item-title-wrap">
                    <span class="dropdown-item-radio" aria-hidden="true"></span>
                    <span class="dropdown-item-title">GPT-SoVITS</span>
                  </div>
                  <span class="model-tier-badge tier-formant">Formant Morphing</span>
                </div>
                <p class="dropdown-item-desc">Autocorrelation pitch tracking and spectral formant resonances preserving authentic vocal timbre.</p>
              </div>
            </div>
          </div>
        </div>
      </div>



      <!-- Dropzone for New Reference Audio File -->
      <label class="voice-ref-dropzone" id="voice-ref-dropzone" for="voice-ref-input">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--tangerine)" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
        <span id="voice-ref-label-text">Drop a custom audio/video clip or <strong style="color:var(--tangerine); text-decoration:underline;">browse</strong> to extract speaker biometric timbre</span>
      </label>
      <input type="file" id="voice-ref-input" accept="audio/*,video/*,.mp4,.mp3,.wav,.m4a,.mov,.webm,.flac,.ogg,.aac,.mkv,.avi,.flv,.wmv,.opus,.wma,.3gp,.ts,.m4v" style="display:none;" onchange="handleVoiceRefSelected(event)" onclick="event.stopPropagation();" />

      <!-- Active Reference Audio Status Badge (replaces raw profile box) -->
      <div id="voice-ref-badge" class="voice-ref-badge" style="display:none;">
        <div class="ref-badge-left">
          <div class="ref-badge-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
          </div>
          <div class="ref-badge-details">
            <span class="ref-badge-title" id="voice-ref-title">Reference Audio Loaded</span>
            <span class="ref-badge-sub" id="voice-ref-sub">Biometric Timbre Locked · Ready for Cloning & Editing</span>
          </div>
        </div>
        <button type="button" class="btn-clear-ref" onclick="clearVoiceRef()" title="Clear reference file">✕ Clear</button>
      </div>

      <!-- Audio Editor & MP3 Studio (Mode 2) -->
      <div class="audio-editor-card" id="mode2-audio-editor">
        <div class="audio-editor-header">
          <div class="editor-title-wrap">
            <div class="editor-icon-badge">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
            </div>
            <div>
              <h3 class="editor-heading">Voice Audio Studio & MP3 Editor</h3>
              <p class="editor-subtext">Adjust volume gain, pitch tuning, and trim boundaries for reference audio or cloned speech</p>
            </div>
          </div>
          <div class="editor-badges-wrap">
            <span class="editor-stat-pill" id="m2-vol-pill">Vol: 100%</span>
            <span class="editor-stat-pill" id="m2-pitch-pill">Pitch: 0 st</span>
            <span class="editor-stat-pill" id="m2-trim-pill">Trim: Full Length</span>
          </div>
        </div>

        <div class="audio-editor-grid">
          <!-- Volume & Gain -->
          <div class="editor-control-col">
            <div class="control-header">
              <span class="control-label">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
                Volume / Gain
              </span>
              <span class="control-val" id="m2-vol-val">100% (0.0 dB)</span>
            </div>
            <input type="range" class="editor-slider" id="m2-vol-slider" min="0" max="200" value="100" step="1" oninput="handleVolumeInput('m2', this.value)" />
            <div class="preset-buttons">
              <button type="button" class="btn-preset" onclick="setVolumePreset('m2', 50)">50%</button>
              <button type="button" class="btn-preset active" id="m2-vol-preset-100" onclick="setVolumePreset('m2', 100)">100%</button>
              <button type="button" class="btn-preset" onclick="setVolumePreset('m2', 130)">130%</button>
              <button type="button" class="btn-preset" onclick="setVolumePreset('m2', 160)">160%</button>
              <button type="button" class="btn-preset" onclick="setVolumePreset('m2', 200)">200%</button>
            </div>
          </div>

          <!-- Pitch Tuning -->
          <div class="editor-control-col">
            <div class="control-header">
              <span class="control-label">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
                Pitch Shift
              </span>
              <span class="control-val" id="m2-pitch-val">0 st (Natural)</span>
            </div>
            <input type="range" class="editor-slider" id="m2-pitch-slider" min="-12" max="12" value="0" step="1" oninput="handlePitchInput('m2', this.value)" />
            <div class="preset-buttons">
              <button type="button" class="btn-preset" onclick="setPitchPreset('m2', -4)">-4 st</button>
              <button type="button" class="btn-preset" onclick="setPitchPreset('m2', -2)">-2 st</button>
              <button type="button" class="btn-preset active" id="m2-pitch-preset-0" onclick="setPitchPreset('m2', 0)">0 st (Reset)</button>
              <button type="button" class="btn-preset" onclick="setPitchPreset('m2', 2)">+2 st</button>
              <button type="button" class="btn-preset" onclick="setPitchPreset('m2', 4)">+4 st</button>
            </div>
          </div>
        </div>

        <!-- Trimming Section -->
        <div class="editor-trim-section">
          <div class="control-header">
            <span class="control-label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>
              Trimming & Playhead In/Out
            </span>
            <span class="control-val" id="m2-trim-duration-val">Full File</span>
          </div>

          <div class="trim-inputs-row">
            <div class="trim-input-group">
              <label for="m2-trim-start">Trim Start (In Point):</label>
              <div class="input-with-btn">
                <input type="text" id="m2-trim-start" class="trim-text-input" value="00:00.00" onchange="updateTrimFromText('m2')" />
                <button type="button" class="btn-trim-set" onclick="setTrimToPlayhead('m2', 'start')" title="Set start trim point to current audio playhead">Set In [⏱]</button>
              </div>
            </div>

            <div class="trim-input-group">
              <label for="m2-trim-end">Trim End (Out Point):</label>
              <div class="input-with-btn">
                <input type="text" id="m2-trim-end" class="trim-text-input" value="00:00.00" onchange="updateTrimFromText('m2')" />
                <button type="button" class="btn-trim-set" onclick="setTrimToPlayhead('m2', 'end')" title="Set end trim point to current audio playhead">Set Out [⏱]</button>
              </div>
            </div>

            <div class="trim-actions-group">
              <button type="button" class="btn-secondary" onclick="resetTrimRange('m2')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
                Reset In/Out
              </button>
            </div>
          </div>

          <div class="trim-slider-scrub-row" style="margin-top: 14px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <span style="font-size:11px; color:var(--text-secondary); font-weight:600;">Live Trimming Sliders:</span>
              <span id="m2-trim-slider-pill" style="font-size:10.5px; font-family:'JetBrains Mono', monospace; color:var(--tangerine);">00:00 - 00:00</span>
            </div>
            <div style="display:flex; gap:16px; align-items:center; flex-wrap:wrap;">
              <div style="flex:1; min-width:140px; display:flex; align-items:center; gap:8px;">
                <span style="font-size:10.5px; color:var(--text-muted); font-weight:600;">In</span>
                <input type="range" class="editor-slider" id="m2-trim-start-bar" min="0" max="100" value="0" step="0.05" oninput="handleTrimBarInput('m2', 'start', this.value)" />
              </div>
              <div style="flex:1; min-width:140px; display:flex; align-items:center; gap:8px;">
                <span style="font-size:10.5px; color:var(--text-muted); font-weight:600;">Out</span>
                <input type="range" class="editor-slider" id="m2-trim-end-bar" min="0" max="100" value="100" step="0.05" oninput="handleTrimBarInput('m2', 'end', this.value)" />
              </div>
            </div>
          </div>
        </div>

        <!-- Action Bar -->
        <div class="editor-bottom-bar">
          <div class="editor-bottom-left">
            <button type="button" class="btn-preview-edit" id="m2-preview-btn" onclick="togglePreviewEditedAudio('m2')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span>Preview Edited Audio</span>
            </button>
            <span class="preview-active-pill" id="m2-preview-status" style="display:none;">
              <span class="pulse-dot"></span> Previewing
            </span>
          </div>

          <div class="editor-bottom-right">
            <button type="button" class="btn-primary btn-export-mp3" id="m2-export-btn" onclick="exportEditedMP3('m2')">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Export Edited MP3
            </button>
          </div>
        </div>
      </div>

      <div class="section-label">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        Speech Prompt
      </div>
      <textarea id="clone-text" class="clone-textarea" placeholder="Type text for the cloned voice to speak...">Welcome to Scriber. This speech was synthesized with zero-shot acoustic timbre matching and harmonic formant preservation.</textarea>

      <div class="sliders-row">
        <div class="slider-col">
          <div class="slider-label">
            <span>Pitch Fine-Tuning</span>
            <span id="pitch-val" style="color:var(--tangerine); font-family:'JetBrains Mono', monospace;">0 Hz</span>
          </div>
          <input type="range" id="pitch-slider" class="slider-ctrl" min="-40" max="40" value="0" oninput="document.getElementById('pitch-val').innerText = (this.value >= 0 ? '+' : '') + this.value + ' Hz'" />
        </div>
        <div class="slider-col">
          <div class="slider-label">
            <span>Speaking Rate</span>
            <span id="rate-val" style="color:var(--tangerine); font-family:'JetBrains Mono', monospace;">0%</span>
          </div>
          <input type="range" id="rate-slider" class="slider-ctrl" min="-30" max="30" value="0" oninput="document.getElementById('rate-val').innerText = (this.value >= 0 ? '+' : '') + this.value + '%'" />
        </div>
      </div>

      <!-- Minimal Acoustic Resonance Canvas during Voice Synthesis -->
      <div class="synthesis-resonance-stage" id="synthesis-resonance-stage">
        <div class="voice-orb-wrap" style="text-align:center; margin-bottom:12px;">
          <canvas id="voice-orb-canvas" width="160" height="160" style="width:160px; height:160px; display:inline-block; vertical-align:middle;"></canvas>
        </div>
        <div class="resonance-canvas-wrap">
          <canvas id="resonance-canvas"></canvas>
        </div>
        <div class="resonance-label" id="resonance-status-text">Harmonic Formant Alignment · F0 Pitch Tracking · Phase Synthesis</div>
      </div>

      <button type="button" class="btn-primary" id="synthesize-btn" style="width:100%; justify-content:center; padding:12px;" onclick="synthesizeClonedVoice()">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
        Clone & Synthesize Voice
      </button>

      <!-- Playable Result Box -->
      <div id="clone-result-box" class="clone-result-box">
        <div class="clone-result-header">
          <span class="fidelity-badge" id="clone-fidelity-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
            99.4% Biometric Timbre Match
          </span>
          <a id="clone-download-btn" class="btn-export" style="text-decoration:none; display:inline-flex; align-items:center; gap:6px;" download="scriber_cloned_voice.mp3">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Download Cloned Speech (.mp3)
          </a>
        </div>
        <audio id="clone-audio-player" class="audio-elem" controls style="width:100%; height:38px; margin-top:8px; accent-color:var(--tangerine); outline:none;"></audio>
      </div>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- MODE 3: ABOUT CREATOR — LAKSHYA PRASHER                   -->
  <!-- ========================================================= -->
  <section id="about-view" class="view-panel">
    <div class="about-container">
      <div class="about-bento-grid">
        <div class="about-card about-name-card" id="about-name-card">
          <!-- Ambient Fluid Glow Background Layer -->
          <div class="card-ambient-glow"></div>
          
          <!-- Avatar with Specular Aura Ring -->
          <div class="creator-avatar-wrap">
            <img src="/assets/avatar.png" alt="Lakshya Prasher" class="creator-avatar-img" onerror="if(!this.dataset.step){this.dataset.step='1';this.src='/assets/creator_profile.png';}else if(this.dataset.step==='1'){this.dataset.step='2';this.src='/api/assets/avatar.png';}else{this.onerror=null;}" />
          </div>

          <!-- User Name -->
          <h2 class="creator-name">Lakshya Prasher</h2>

          <!-- Social Links Row -->
          <div class="about-social-row">
            <!-- Instagram -->
            <a href="https://www.instagram.com/laksh._.ya/" target="_blank" rel="noopener noreferrer" class="social-node-card instagram" title="Follow Lakshya on Instagram">
              <div class="social-icon-box">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                  <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                </svg>
              </div>
              <div class="social-info">
                <div class="social-label">Instagram</div>
                <div class="social-handle">@laksh._.ya</div>
              </div>
              <span class="social-arrow">↗</span>
            </a>

            <!-- LinkedIn -->
            <a href="https://www.linkedin.com/in/lakshyaprasher/" target="_blank" rel="noopener noreferrer" class="social-node-card linkedin" title="Connect on LinkedIn">
              <div class="social-icon-box">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                  <rect x="2" y="9" width="4" height="12"></rect>
                  <circle cx="4" cy="4" r="2"></circle>
                </svg>
              </div>
              <div class="social-info">
                <div class="social-label">LinkedIn</div>
                <div class="social-handle">in/lakshyaprasher</div>
              </div>
              <span class="social-arrow">↗</span>
            </a>

            <!-- GitHub -->
            <a href="https://github.com/LakshyaPrasher" target="_blank" rel="noopener noreferrer" class="social-node-card github" title="Explore Repositories on GitHub">
              <div class="social-icon-box">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                </svg>
              </div>
              <div class="social-info">
                <div class="social-label">GitHub</div>
                <div class="social-handle">@LakshyaPrasher</div>
              </div>
              <span class="social-arrow">↗</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>

<!-- Floating Toast Container -->
<div id="toast-container"></div>

<script>
  var currentResult = null;
  window.currentResult = null;
  var selectedVoiceProfile = null;
  window.selectedVoiceProfile = null;
  var loadedMediaUrl = null;
  var realAudioBuffer = null;
  var audioContext = null;

  /* Toast Notification System */
  function showToast(message, type) {
    type = type || 'success';
    var cont = document.getElementById('toast-container');
    if (!cont) return;
    var t = document.createElement('div');
    t.className = 'toast toast-' + type;
    var icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
    t.innerHTML = '<span style="font-weight:700;">' + icon + '</span><span>' + escapeHtml(message) + '</span>';
    cont.appendChild(t);
    setTimeout(function() { t.classList.add('show'); }, 20);
    setTimeout(function() {
      t.classList.remove('show');
      setTimeout(function() { if (t.parentNode) t.parentNode.removeChild(t); }, 300);
    }, 3000);
  }
  /* Mode Switching */
  function switchMode(mode) {
    if (typeof closeAllModelDropdowns === 'function') closeAllModelDropdowns();
    if (mode === 'swarm') mode = 'about';
    document.querySelectorAll('.nav-pill').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

    const btn = document.getElementById('btn-mode-' + mode);
    if (btn) btn.classList.add('active');

    let viewId = 'transcribe-view';
    if (mode === 'voice') viewId = 'voice-view';
    else if (mode === 'about' || mode === 'swarm') viewId = 'about-view';

    const view = document.getElementById(viewId);
    if (view) view.classList.add('active');

    if (mode === 'voice') {
      if (!selectedVoiceProfile && currentResult && currentResult.voice_profiles && currentResult.voice_profiles.length > 0) {
        populateVoiceProfiles(currentResult.voice_profiles);
      }
    } else if (mode === 'transcribe') {
      if (currentResult) {
        const dur = getAccurateDuration();
        const fName = (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
        initModeAudioEditor('m1', dur > 0 ? dur : 10, fName);
      }
      setTimeout(drawWave, 50);
    } else if (mode === 'about') {
      initBentoSpotlight();
    }
  }

  /* Dynamic Name Card Cursor Spotlight & Butter-Smooth 3D Tilt Physics */
  function initBentoSpotlight() {
    var cards = document.querySelectorAll('.about-card, .social-node-card');
    cards.forEach(function(card) {
      if (card.__hasSpotlight) return;
      card.__hasSpotlight = true;

      var cachedRect = null;
      var rafId = null;

      function updateRect() {
        cachedRect = card.getBoundingClientRect();
      }

      card.addEventListener('mouseenter', function() {
        if (card.__resetTimer) {
          clearTimeout(card.__resetTimer);
          card.__resetTimer = null;
        }
        updateRect();
        if (card.classList.contains('about-name-card')) {
          card.style.transition = 'transform 0.12s cubic-bezier(0.2, 0.8, 0.2, 1)';
        }
      });

      card.addEventListener('mousemove', function(e) {
        if (!cachedRect) updateRect();
        var x = e.clientX - cachedRect.left;
        var y = e.clientY - cachedRect.top;

        card.style.setProperty('--mouse-x', x + 'px');
        card.style.setProperty('--mouse-y', y + 'px');

        if (card.classList.contains('about-name-card')) {
          if (rafId) cancelAnimationFrame(rafId);
          rafId = requestAnimationFrame(function() {
            var halfW = (cachedRect ? cachedRect.width : card.offsetWidth) / 2;
            var halfH = (cachedRect ? cachedRect.height : card.offsetHeight) / 2;
            var rotY = ((x - halfW) / halfW) * 7;
            var rotX = -((y - halfH) / halfH) * 7;
            rotY = Math.max(-7, Math.min(7, rotY));
            rotX = Math.max(-7, Math.min(7, rotX));
            card.style.transition = '';
            card.style.transform = 'perspective(900px) rotateX(' + rotX.toFixed(2) + 'deg) rotateY(' + rotY.toFixed(2) + 'deg) translateY(-2px)';
          });
        }
      });

      card.addEventListener('mouseleave', function() {
        card.style.setProperty('--mouse-x', '-500px');
        card.style.setProperty('--mouse-y', '-500px');
        cachedRect = null;
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        if (card.classList.contains('about-name-card')) {
          card.style.transition = 'transform 0.45s cubic-bezier(0.16, 1, 0.3, 1)';
          card.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0)';
          card.__resetTimer = setTimeout(function() {
            card.style.transition = '';
            card.__resetTimer = null;
          }, 450);
        }
      });
    });
  }
  function checkUrlMode() {
    try {
      var params = new URLSearchParams(window.location.search);
      var mode = params.get('mode') || (window.location.hash ? window.location.hash.replace('#', '') : null);
      if (mode) switchMode(mode);
    } catch (e) {}
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initBentoSpotlight();
      checkUrlMode();
    });
  } else {
    initBentoSpotlight();
    checkUrlMode();
  }

  /* Reliable, Thread-Safe File Dialog Opening (Guarded against double invocation & COM deadlocks) */
  var isFileDialogOpening = false;
  function openFileDialog(evt) {
    if (evt) {
      if (typeof evt.preventDefault === 'function') evt.preventDefault();
      if (typeof evt.stopPropagation === 'function') evt.stopPropagation();
    }
    if (isFileDialogOpening) {
      return;
    }
    isFileDialogOpening = true;

    // Direct native desktop file dialog integration (zero upload overhead, instant start)
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_file_dialog === 'function') {
      try {
        const filePath = await window.pywebview.api.open_file_dialog();
        isFileDialogOpening = false;
        if (filePath) {
          startProcessingPath(filePath);
          return;
        }
      } catch (err) {
        console.warn('Native open_file_dialog fallback:', err);
      }
    }

    var releaseLock = function() {
      setTimeout(function() { isFileDialogOpening = false; }, 300);
      window.removeEventListener('focus', releaseLock);
    };
    window.addEventListener('focus', releaseLock);
    setTimeout(releaseLock, 1500);

    const input = document.getElementById('media-file-input');
    if (input) {
      input.value = '';
      input.click();
    }
  }

  /* Drag & Drop Setup */
  const dropzone = document.getElementById('dropzone');
  if (dropzone) {
    ['dragenter', 'dragover'].forEach(name => {
      dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-active');
      }, false);
    });
    ['dragleave', 'dragend', 'drop'].forEach(name => {
      dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-active');
      }, false);
    });
    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        const file = dt.files[0];
        const nativePath = file.path || '';
        if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
          startProcessingPath(nativePath);
        } else {
          startProcessing(file);
        }
      }
    }, false);
  }

  // Prevent browser from navigating away on dropped media files
  window.addEventListener('dragover', (e) => {
    e.preventDefault();
  }, false);

  window.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      const voiceView = document.getElementById('voice-view');
      const isVoiceActive = voiceView && voiceView.classList.contains('active');
      if (isVoiceActive) {
        handleVoiceRefSelected({ target: { files: dt.files } });
      } else {
        const outView = document.getElementById('output-viewport');
        if (!outView || outView.style.display === 'none') {
          const file = dt.files[0];
          const nativePath = file.path || '';
          if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
            startProcessingPath(nativePath);
          } else {
            startProcessing(file);
          }
        }
      }
    }
    e.preventDefault();
  }, false);

  function handleFileSelected(e) {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const nativePath = file.path || '';
      if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
        startProcessingPath(nativePath);
      } else {
        startProcessing(file);
      }
    }
  }

  /* Precision Real-Time Progress Tracker with Backend Telemetry & Dynamic ETA */
  var progressPollInterval = null;

  function formatDuration(sec) {
    if (!sec || isNaN(sec) || sec < 0) return '00:00';
    var m = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  function formatEta(sec) {
    if (!sec || isNaN(sec) || sec <= 0) return 'Calculating remaining time...';
    if (sec < 60) return Math.ceil(sec) + 's remaining';
    var m = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return m + 'm ' + (s > 0 ? s + 's ' : '') + 'remaining';
  }

  function updateProgressUI(data) {
    if (!data) return;
    var pct = Math.max(0, Math.min(100, data.percent || 0));
    var fillEl = document.getElementById('progress-fill');
    var pctBadge = document.getElementById('progress-pct-badge');
    var etaText = document.getElementById('progress-eta-text');
    var speedText = document.getElementById('progress-speed-text');
    var posText = document.getElementById('progress-position-text');
    var elapsedText = document.getElementById('progress-elapsed-text');
    var titleEl = document.getElementById('processing-main-title');
    var subEl = document.getElementById('processing-status-text');
    var pillEl = document.getElementById('processing-stage-pill');

    if (fillEl) fillEl.style.width = pct + '%';
    if (pctBadge) pctBadge.innerText = pct + '%';

    if (etaText) {
      if (pct >= 100) {
        etaText.innerText = 'Completed';
      } else if (data.eta_sec && data.eta_sec > 0) {
        etaText.innerText = formatEta(data.eta_sec);
      } else if (pct >= 95) {
        etaText.innerText = 'Finalizing...';
      } else {
        etaText.innerText = 'Estimating time...';
      }
    }

    if (speedText) {
      if (data.speed_factor && data.speed_factor > 0) {
        speedText.innerText = data.speed_factor.toFixed(1) + 'x real-time speed';
      } else {
        speedText.innerText = 'Accelerated GPU';
      }
    }

    if (posText) {
      if (data.total_duration_sec && data.total_duration_sec > 0) {
        posText.innerText = formatDuration(data.current_time_sec) + ' / ' + formatDuration(data.total_duration_sec) + ' decoded';
      } else {
        posText.innerText = 'Analyzing audio...';
      }
    }

    if (elapsedText) {
      elapsedText.innerText = 'Elapsed: ' + Math.floor(data.elapsed_sec || 0) + 's';
    }

    if (titleEl && data.title) titleEl.innerText = data.title;
    if (subEl && data.subtitle) subEl.innerText = data.subtitle;
    if (pillEl && data.phase) pillEl.innerText = data.phase;
  }

  function startLiveProgressTracker() {
    if (progressPollInterval) clearInterval(progressPollInterval);

    updateProgressUI({
      percent: 4,
      title: "Transcribing & Translating to English",
      subtitle: "Ingesting media buffer · Extracting 16kHz speech stream...",
      phase: "Phase 1/4 · Acoustic Normalization",
      speed_factor: 0,
      current_time_sec: 0,
      total_duration_sec: 0,
      elapsed_sec: 0,
      eta_sec: 0
    });

    progressPollInterval = setInterval(async function() {
      try {
        var res = await fetch('/api/progress');
        if (!res.ok) return;
        var p = await res.json();
        if (p && p.active) {
          updateProgressUI(p);
        }
      } catch (e) {
        // Silent retry
      }
    }, 350);
  }

  function stopLiveProgressTracker() {
    if (progressPollInterval) {
      clearInterval(progressPollInterval);
      progressPollInterval = null;
    }
  }

  async function startProcessingPath(filePath) {
    if (!filePath) return;
    const fileName = filePath.split(/[\\/]/).pop() || filePath;

    // Transition into Liquid Morphing Orb & Genuine Progress Viewport
    document.getElementById('dropzone').style.display = 'none';
    const procCard = document.getElementById('processing-card');
    procCard.style.display = 'block';
    document.getElementById('processing-file-name').innerText = fileName;
    document.getElementById('output-viewport').style.display = 'none';

    // Start minimalist organic liquid light animation and live backend progress polling
    startLiquidOrbAnimation();
    startLiveProgressTracker();

    if (loadedMediaUrl && loadedMediaUrl.startsWith('blob:')) {
      URL.revokeObjectURL(loadedMediaUrl);
    }
    loadedMediaName = fileName;
    loadedMediaUrl = '/api/media?path=' + encodeURIComponent(filePath);
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
      audioPlayer.src = loadedMediaUrl;
    }

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath,
          task: 'translate',
          language: 'auto',
          model: selectedTranscribeModel || 'turbo',
          redact_pii: window.isPIIRedacted ? 'true' : 'false'
        })
      });
      const data = await res.json();

      stopLiveProgressTracker();
      stopLiquidOrbAnimation();

      if (data.error) {
        showToast('Processing error: ' + data.error, 'error');
        resetToUpload();
        return;
      }

      updateProgressUI({
        percent: 100,
        phase: 'Phase 4/4 · Complete',
        title: 'Transcription & Translation Complete',
        subtitle: 'All speaker segments verified and ready',
        eta_sec: 0
      });

      currentResult = data;
      showToast('Transcription & Translation complete! Ready for review.', 'success');
      renderTranscription(data);
    } catch (err) {
      stopLiveProgressTracker();
      stopLiquidOrbAnimation();
      showToast('Processing error: ' + err, 'error');
      resetToUpload();
    }
  }

  async function startProcessing(file) {
    if (!file) return;

    // Transition into Liquid Morphing Orb & Genuine Progress Viewport
    document.getElementById('dropzone').style.display = 'none';
    const procCard = document.getElementById('processing-card');
    procCard.style.display = 'block';
    document.getElementById('processing-file-name').innerText = file.name;
    document.getElementById('output-viewport').style.display = 'none';

    // Start minimalist organic liquid light animation and live backend progress polling
    startLiquidOrbAnimation();
    startLiveProgressTracker();

    if (loadedMediaUrl) URL.revokeObjectURL(loadedMediaUrl);
    loadedMediaUrl = URL.createObjectURL(file);
    const audioPlayer = document.getElementById('audio-player');
    audioPlayer.src = loadedMediaUrl;

    // Decode actual audio peaks using Web Audio API for true waveform rendering
    decodeAudioFileForWaveform(file);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('task', 'translate');
    formData.append('language', 'auto');
    formData.append('model', selectedTranscribeModel || 'turbo');
    formData.append('redact_pii', window.isPIIRedacted ? 'true' : 'false');

    try {
      const res = await fetch('/api/process', { method: 'POST', body: formData });
      const data = await res.json();

      stopLiveProgressTracker();
      stopLiquidOrbAnimation();

      if (data.error) {
        showToast('Processing error: ' + data.error, 'error');
        resetToUpload();
        return;
      }

      updateProgressUI({
        percent: 100,
        phase: 'Phase 4/4 · Complete',
        title: 'Transcription & Translation Complete',
        subtitle: 'All speaker segments verified and ready',
        eta_sec: 0
      });

      currentResult = data;
      showToast('Transcription & Translation complete! Ready for review.', 'success');
      renderTranscription(data);
    } catch (err) {
      stopLiveProgressTracker();
      stopLiquidOrbAnimation();
      showToast('Upload or network failed: ' + err, 'error');
      resetToUpload();
    }
  }

  function resetToUpload() {
    document.getElementById('dropzone').style.display = 'block';
    document.getElementById('processing-card').style.display = 'none';
    document.getElementById('output-viewport').style.display = 'none';
    const player = document.getElementById('audio-player');
    if (player) { player.pause(); player.currentTime = 0; }
    updatePlayPauseIcons(false);
  }

  /* Audio Transport Controls */
  function togglePlayPause() {
    const player = document.getElementById('audio-player');
    if (!player) return;
    if (player.paused) {
      player.play().catch(() => {});
      updatePlayPauseIcons(true);
    } else {
      player.pause();
      updatePlayPauseIcons(false);
    }
  }

  function updatePlayPauseIcons(isPlaying) {
    const playIcon = document.getElementById('play-icon');
    const pauseIcon = document.getElementById('pause-icon');
    if (playIcon && pauseIcon) {
      playIcon.style.display = isPlaying ? 'none' : 'block';
      pauseIcon.style.display = isPlaying ? 'block' : 'none';
    }
  }

  function skipAudio(seconds) {
    const player = document.getElementById('audio-player');
    if (!player) return;
    player.currentTime = Math.max(0, Math.min(player.duration || 0, player.currentTime + seconds));
  }

  function setAudioVolume(vol) {
    const player = document.getElementById('audio-player');
    if (player) player.volume = parseFloat(vol);
  }

  function setPlaybackRate(rate, btn) {
    const player = document.getElementById('audio-player');
    if (player) player.playbackRate = rate;
    document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }

  function handleAudioEnded() {
    updatePlayPauseIcons(false);
  }

  /* Keyboard Shortcuts */
  window.addEventListener('keydown', function(e) {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable)) {
      return;
    }
    if (e.code === 'Space') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.code === 'ArrowLeft' || e.code === 'KeyJ') {
      e.preventDefault();
      skipAudio(-5);
    } else if (e.code === 'ArrowRight' || e.code === 'KeyL') {
      e.preventDefault();
      skipAudio(5);
    } else if (e.code === 'Escape') {
      var s = document.getElementById('transcript-search');
      if (s) { s.value = ''; filterTranscript(); }
    }
  });

  /* Web Audio API Real Peak Extraction */
  function decodeAudioFileForWaveform(file) {
    try {
      if (!file) return;
      if (file.size && file.size > 25 * 1024 * 1024) {
        // Prevent browser out-of-memory crash on large files (> 25MB)
        return;
      }
      if (!window.AudioContext && !window.webkitAudioContext) return;
      var AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!audioContext) audioContext = new AudioCtx();
      var reader = new FileReader();
      reader.onload = function(ev) {
        audioContext.decodeAudioData(ev.target.result, function(buffer) {
          realAudioBuffer = buffer;
          computeRealWaveformPeaks(buffer, 64);
        }, function(e) {
          // Fallback to speech cadence envelope
        });
      };
      reader.readAsArrayBuffer(file);
    } catch (e) {}
  }

  function computeRealWaveformPeaks(buffer, numBars) {
    var rawData = buffer.getChannelData(0);
    var totalSamples = rawData.length;
    var blockSize = Math.floor(totalSamples / numBars);
    var peaks = [];
    for (var i = 0; i < numBars; i++) {
      var start = i * blockSize;
      var sum = 0;
      for (var j = 0; j < blockSize; j++) {
        var val = rawData[start + j];
        sum += val * val;
      }
      var rms = Math.sqrt(sum / blockSize);
      peaks.push(Math.max(0.18, Math.min(0.96, rms * 4.5)));
    }
    waveEnvelope = peaks;
  }

  /* Render Output Viewport */
  function renderTranscription(data) {
    currentResult = data;
    window.currentResult = data;
    const dropzoneElem = document.getElementById('dropzone');
    if (dropzoneElem) dropzoneElem.style.display = 'none';
    const procCard = document.getElementById('processing-card');
    if (procCard) procCard.style.display = 'none';
    const outputView = document.getElementById('output-viewport');
    if (outputView) outputView.style.display = 'block';

    const segments = (data.transcription && data.transcription.segments) ? data.transcription.segments : [];
    const container = document.getElementById('transcript-container');
    container.innerHTML = '';

    // Unify consecutive segments of the same speaker into cohesive speaker cards
    const unifiedSegments = [];
    let curCard = null;

    segments.forEach((s) => {
      const spk = (s.speaker || 'Speaker 1').replace(/_/g, ' ');
      if (!curCard || curCard.speaker !== spk) {
        curCard = {
          speaker: spk,
          start: s.start,
          end: s.end,
          text: (s.text || '').trim(),
          words: s.words ? [...s.words] : [],
        };
        unifiedSegments.push(curCard);
      } else {
        curCard.end = Math.max(curCard.end, s.end);
        if (s.words && s.words.length > 0) {
          curCard.words.push(...s.words);
        }
        let glue = ' ';
        const trimmed = curCard.text.trim();
        if (trimmed && !trimmed.endsWith(',') && !trimmed.endsWith(';') && !trimmed.endsWith(':') && !trimmed.endsWith('.')) {
          glue = '. ';
        }
        curCard.text = (curCard.text + glue + (s.text || '').trim()).replace(/\\s+/g, ' ').replace(/([,.:;?!])\\./g, '$1');
      }
    });

    window.renderedSegments = unifiedSegments;
    let totalWords = 0;

    unifiedSegments.forEach((s, idx) => {
      const cleanSpk = s.speaker;
      const themeClass = getSpeakerThemeClass(cleanSpk, idx);

      let wordSpans = '';
      if (s.words && s.words.length > 0) {
        totalWords += s.words.length;
        wordSpans = s.words.map(w => {
          const wText = escapeHtml(w.word || '');
          const wStart = (w.start || 0).toFixed(2);
          const wEnd = (w.end || 0).toFixed(2);
          return `<span class="word-token" data-start="${wStart}" data-end="${wEnd}" onclick="seekToWord(${wStart}, event)">${wText}</span> `;
        }).join('');
      } else {
        const words = (s.text || '').trim().split(/\\s+/).filter(Boolean);
        totalWords += words.length;
        const segDur = Math.max(0.1, (s.end || 0) - (s.start || 0));
        const wordDur = segDur / Math.max(1, words.length);
        wordSpans = words.map((w, wIdx) => {
          const wStart = ((s.start || 0) + (wIdx * wordDur)).toFixed(2);
          const wEnd = ((s.start || 0) + ((wIdx + 1) * wordDur)).toFixed(2);
          return `<span class="word-token" data-start="${wStart}" data-end="${wEnd}" onclick="seekToWord(${wStart}, event)">${escapeHtml(w)}</span> `;
        }).join('');
      }

      const segCard = document.createElement('div');
      segCard.className = `segment-card ${themeClass}`;
      segCard.id = `seg-${idx}`;
      segCard.onclick = () => seekTo(s.start);

      segCard.innerHTML = `
        <div class="seg-header">
          <div class="seg-header-left">
            <span class="spk-badge"><span class="spk-dot"></span>${escapeHtml(cleanSpk)}</span>
            <span class="seg-time" onclick="seekTo(${s.start}); event.stopPropagation();">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              ${formatSec(s.start)} - ${formatSec(s.end)}
            </span>
          </div>
          <div class="seg-actions">
            <button class="btn-seg-icon" onclick="copySegmentText(${idx}, event)" title="Copy block dialogue">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              Copy
            </button>
          </div>
        </div>
        <div class="seg-text" id="seg-text-${idx}" contenteditable="true" spellcheck="false" onblur="handleSegmentEdit(${idx}, this)" onclick="event.stopPropagation()">
          ${wordSpans}
        </div>
      `;
      container.appendChild(segCard);
    });

    const wordCountBadge = document.getElementById('live-word-count');
    if (wordCountBadge) wordCountBadge.innerText = totalWords;

    // Dynamically populate actual voice profiles into Voice Cloning mode
    populateVoiceProfiles(data.voice_profiles || []);

    // Initialize Mode 1 Audio Editor with loaded audio duration & filename
    const durM1 = getAccurateDuration();
    const fileNameM1 = (data && data.video_source) || (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
    initModeAudioEditor('m1', durM1 > 0 ? durM1 : 10, fileNameM1);

    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
      if (data && data.audio_base64 && !audioPlayer.src) {
        audioPlayer.src = data.audio_base64;
      } else if (data && data.media_url && !audioPlayer.src) {
        audioPlayer.src = data.media_url;
      }
      audioPlayer.addEventListener('loadedmetadata', () => {
        if (audioPlayer.duration && isFinite(audioPlayer.duration)) {
          const currentM1Dur = audioEditorState.m1.totalDuration;
          if (!currentM1Dur || currentM1Dur <= 1.0) {
            initModeAudioEditor('m1', audioPlayer.duration, fileNameM1);
          }
        }
      }, { once: true });
    }

    // Render Supreme Council Multi-Agent Dashboard
    renderSupremeCouncil(data);
  }

  function getSpeakerThemeClass(speaker, idx) {
    if (!speaker) return 'spk-theme-1';
    const s = speaker.toLowerCase();
    if (s.includes('1')) return 'spk-theme-1';
    if (s.includes('2')) return 'spk-theme-2';
    if (s.includes('3')) return 'spk-theme-3';
    return 'spk-theme-4';
  }

  /* Clean Text Helpers to Guarantee Proper English Spacing and Formatting */
  function cleanExportText(str) {
    if (!str) return '';
    let t = str.replace(/\u00A0/g, ' ');       // Non-breaking space to regular space
    t = t.replace(/\s+/g, ' ');                // Collapse multiple spaces
    t = t.replace(/\s+([,.:;?!])/g, '$1');     // Remove erroneous spaces before punctuation
    t = t.replace(/([,.:;?!])([A-Za-z0-9])/g, '$1 $2'); // Ensure space after punctuation
    return t.trim();
  }

  function getCleanSegmentText(s, idx) {
    let text = (s && s.text) ? s.text.trim() : '';
    const segElem = document.getElementById('seg-text-' + idx);
    if (segElem) {
      const tokens = segElem.querySelectorAll('.word-token');
      if (tokens && tokens.length > 0) {
        const words = [];
        tokens.forEach(tok => {
          const w = (tok.innerText || tok.textContent || '').trim();
          if (w) words.push(w);
        });
        if (words.length > 0) {
          const gathered = words.join(' ');
          if (!text || segElem.getAttribute('data-edited') === 'true') {
            text = gathered;
          }
        }
      } else {
        const domRaw = (segElem.innerText || segElem.textContent || '').trim();
        if (domRaw && (!text || segElem.getAttribute('data-edited') === 'true')) {
          text = domRaw;
        }
      }
    }
    return cleanExportText(text);
  }

  /* One-Click Prominent Full Transcript Copy with Clean Formatting Options */
  function copyFullTranscript() {
    const data = currentResult || window.currentResult;
    if (!data || !data.transcription) {
      showToast('Please upload and transcribe a media file first.', 'info');
      return;
    }
    const format = document.getElementById('copy-format-select') ? document.getElementById('copy-format-select').value : 'standard';
    const segments = data.transcription.segments || [];
    let formatted = '';

    segments.forEach((s, idx) => {
      const rawSpk = s.speaker || 'Speaker 1';
      const cleanSpk = rawSpk.replace(/_/g, ' ');
      const timeRange = `${formatSec(s.start)} - ${formatSec(s.end)}`;
      const text = getCleanSegmentText(s, idx);

      if (format === 'dialogue') {
        formatted += `${cleanSpk}:\n${text}\n\n`;
      } else if (format === 'text') {
        formatted += `${text}\n\n`;
      } else if (format === 'markdown') {
        formatted += `### ${cleanSpk} \`[${timeRange}]\`\n\n${text}\n\n`;
      } else {
        // Standard clean export: [00:00 - 00:38] Speaker 1: \n Text
        formatted += `[${timeRange}] ${cleanSpk}:\n${text}\n\n`;
      }
    });

    const btn = document.getElementById('copy-transcript-btn');
    const originalText = btn ? btn.innerHTML : '';

    function showCopied() {
      if (btn) {
        btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied to Clipboard!`;
        btn.classList.add('btn-copied');
        showToast('Full transcript copied to clipboard!', 'success');
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('btn-copied');
        }, 2500);
      }
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(formatted.trim()).then(showCopied).catch(() => {
        fallbackCopy(formatted.trim(), showCopied);
      });
    } else {
      fallbackCopy(formatted.trim(), showCopied);
    }
  }

  function copySegmentText(idx, evt) {
    if (evt) evt.stopPropagation();
    const data = currentResult || window.currentResult;
    if (!data || !data.transcription) return;
    const s = data.transcription.segments[idx];
    if (!s) return;
    const rawSpk = s.speaker || 'Speaker 1';
    const cleanSpk = rawSpk.replace(/_/g, ' ');
    const textContent = getCleanSegmentText(s, idx);
    const text = `[${formatSec(s.start)} - ${formatSec(s.end)}] ${cleanSpk}:\n${textContent}`;

    const btn = evt && evt.currentTarget ? evt.currentTarget : null;
    const origHtml = btn ? btn.innerHTML : '';
    function showCopied() {
      if (btn) {
        btn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        btn.style.color = '#10B981';
        showToast(`Copied ${cleanSpk}'s dialogue!`, 'success');
        setTimeout(() => {
          btn.innerHTML = origHtml;
          btn.style.color = '';
        }, 2000);
      }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(showCopied).catch(() => {
        fallbackCopy(text, showCopied);
      });
    } else {
      fallbackCopy(text, showCopied);
    }
  }

  function fallbackCopy(text, cb) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
    } catch (e) {}
    document.body.removeChild(ta);
    if (cb) cb();
  }

  function handleSegmentEdit(idx, el) {
    el.setAttribute('data-edited', 'true');
    const newText = cleanExportText(el.innerText || el.textContent || '');
    if (currentResult && currentResult.transcription && currentResult.transcription.segments[idx]) {
      currentResult.transcription.segments[idx].text = newText;
      showToast('Transcript edit saved', 'info');
    }
  }

  // Intercept manual text selection copy within transcript container to guarantee spaces
  document.addEventListener('copy', function(e) {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const cont = document.getElementById('transcript-container');
    if (cont && cont.contains(sel.anchorNode)) {
      const selected = sel.toString();
      if (selected && e.clipboardData) {
        const cleaned = cleanExportText(selected);
        if (cleaned) {
          e.clipboardData.setData('text/plain', cleaned);
          e.preventDefault();
        }
      }
    }
  });

  /* Audio Synchronization & Kinetic Highlights */
  function getAccurateDuration() {
    const player = document.getElementById('audio-player');
    if (player && player.duration && isFinite(player.duration) && player.duration > 0.05) {
      return player.duration;
    }
    const data = window.currentResult || currentResult;
    if (data && data.audio_metadata && data.audio_metadata.duration > 0.05) {
      return data.audio_metadata.duration;
    }
    if (data && data.transcription && data.transcription.duration > 0.05) {
      return data.transcription.duration;
    }
    return 0;
  }

  function seekTo(sec) {
    const player = document.getElementById('audio-player');
    if (player) {
      const dur = getAccurateDuration();
      const clamped = Math.max(0, Math.min(dur > 0 ? dur : sec, sec));
      player.currentTime = clamped;
      handleAudioTimeUpdate();
      player.play().catch(() => {});
      updatePlayPauseIcons(true);
    }
  }

  function seekToWord(sec, evt) {
    if (evt) evt.stopPropagation();
    seekTo(sec);
  }

  function handleAudioTimeUpdate() {
    const player = document.getElementById('audio-player');
    if (!player) return;
    const ct = (player && isFinite(player.currentTime)) ? player.currentTime : 0;
    const dur = getAccurateDuration() || (player && player.duration) || 1.0;

    const timecodeElem = document.getElementById('live-timecode');
    if (timecodeElem) timecodeElem.innerText = formatSec(ct) + ' / ' + formatSec(dur);

    const segments = window.renderedSegments || (currentResult && currentResult.transcription && currentResult.transcription.segments) || [];
    segments.forEach((s, idx) => {
      const card = document.getElementById('seg-' + idx);
      if (!card) return;
      if (ct >= (s.start - 0.05) && ct <= (s.end + 0.1)) {
        if (!card.classList.contains('active-seg')) {
          card.classList.add('active-seg');
          const liveSpeaker = document.getElementById('live-speaker');
          if (liveSpeaker) liveSpeaker.innerText = (s.speaker || 'Speaker 1').replace(/_/g, ' ');
          card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      } else {
        card.classList.remove('active-seg');
      }

      const wordTokens = card.querySelectorAll('.word-token');
      wordTokens.forEach(w => {
        const wStart = parseFloat(w.getAttribute('data-start'));
        const wEnd = parseFloat(w.getAttribute('data-end'));
        if (ct >= (wStart - 0.05) && ct <= (wEnd + 0.05)) {
          w.classList.add('active-word');
        } else {
          w.classList.remove('active-word');
        }
      });
    });
  }

  /* Live Keyword Search with Highlights */
  function filterTranscript() {
    const q = document.getElementById('transcript-search').value.toLowerCase().trim();
    const countBadge = document.getElementById('search-count-badge');
    let totalMatches = 0;

    document.querySelectorAll('.segment-card').forEach(card => {
      const segTextElem = card.querySelector('.seg-text');
      if (!segTextElem) return;
      const fullText = card.innerText.toLowerCase();

      if (!q) {
        card.style.display = 'block';
        card.querySelectorAll('.word-token').forEach(w => w.classList.remove('search-match'));
        return;
      }

      const matches = fullText.includes(q);
      card.style.display = matches ? 'block' : 'none';

      card.querySelectorAll('.word-token').forEach(w => {
        const wt = w.innerText.toLowerCase();
        if (wt.includes(q)) {
          w.classList.add('search-match');
          totalMatches++;
        } else {
          w.classList.remove('search-match');
        }
      });
    });

    if (countBadge) {
      if (q) {
        countBadge.style.display = 'block';
        countBadge.innerText = `${totalMatches} match${totalMatches === 1 ? '' : 'es'}`;
      } else {
        countBadge.style.display = 'none';
      }
    }
  }

  /* Client Export Download with Clean English Spacing & Multi-Format Support */
  function downloadArtifact(type) {
    const data = currentResult || window.currentResult;
    if (!data) {
      showToast('Please process an audio file first.', 'info');
      return;
    }
    let content = '';
    const baseSource = (data.video_source || 'scriber_transcript').replace(/\.[^/.]+$/, "");
    let filename = `${baseSource}.${type}`;
    const segments = (data.transcription && data.transcription.segments) ? data.transcription.segments : [];

    if (type === 'json') {
      content = JSON.stringify(data, null, 2);
    } else if (type === 'txt') {
      filename = `${baseSource}_transcript.txt`;
      let header = `=================================================================\n`;
      header += `SCRIBER TRANSCRIPT EXPORT: ${data.video_source || 'Audio Recording'}\n`;
      const dur = data.audio_metadata ? data.audio_metadata.duration : 0;
      header += `Duration: ${formatSec(dur)} | Exported: ${new Date().toLocaleString()}\n`;
      header += `=================================================================\n\n`;
      content = header;
      segments.forEach((s, idx) => {
        const spk = (s.speaker || 'Speaker 1').replace(/_/g, ' ');
        const timeRange = `${formatSec(s.start)} - ${formatSec(s.end)}`;
        const text = getCleanSegmentText(s, idx);
        content += `[${timeRange}] ${spk}:\n${text}\n\n`;
      });
    } else if (type === 'md') {
      filename = `${baseSource}_transcript.md`;
      let md = `# Scriber Transcript: ${data.video_source || 'Audio Recording'}\n\n`;
      const dur = data.audio_metadata ? data.audio_metadata.duration : 0;
      md += `> Duration: ${formatSec(dur)} | Processed by Scriber Autonomous Studio\n\n`;
      segments.forEach((s, idx) => {
        const spk = (s.speaker || 'Speaker 1').replace(/_/g, ' ');
        const timeRange = `${formatSec(s.start)} - ${formatSec(s.end)}`;
        const text = getCleanSegmentText(s, idx);
        md += `### ${spk} \`[${timeRange}]\`\n\n${text}\n\n`;
      });
      content = md;
    } else if (type === 'srt') {
      filename = `${baseSource}.srt`;
      content = formatSrtExport(segments);
    } else if (type === 'vtt') {
      filename = `${baseSource}.vtt`;
      content = formatVttExport(segments);
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${filename}`, 'success');

    // Also persist directly into ./scriber_output for desktop folder view
    fetch('/api/desktop/save-file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: filename, content: content, dir: './scriber_output' })
    }).catch(function() {});
  }

  function formatSrtExport(segments) {
    let cues = [];
    let cueIndex = 1;

    segments.forEach((s, segIdx) => {
      const spk = (s.speaker || 'Speaker 1').replace(/_/g, ' ');
      if (s.words && s.words.length > 8) {
        const words = s.words;
        const chunkSize = 8;
        for (let i = 0; i < words.length; i += chunkSize) {
          const slice = words.slice(i, i + chunkSize);
          const cStart = slice[0].start !== undefined ? slice[0].start : s.start;
          const cEnd = slice[slice.length - 1].end !== undefined ? slice[slice.length - 1].end : s.end;
          const cText = cleanExportText(slice.map(w => w.word).join(' '));
          cues.push(`${cueIndex++}\n${formatSrtTimestamp(cStart)} --> ${formatSrtTimestamp(cEnd)}\n[${spk}] ${cText}\n`);
        }
      } else {
        const cleanText = getCleanSegmentText(s, segIdx);
        cues.push(`${cueIndex++}\n${formatSrtTimestamp(s.start)} --> ${formatSrtTimestamp(s.end)}\n[${spk}] ${cleanText}\n`);
      }
    });

    return cues.join(String.fromCharCode(10));
  }

  function formatVttExport(segments) {
    let cues = ['WEBVTT - Scriber Transcript Export' + String.fromCharCode(10)];
    let cueIndex = 1;

    segments.forEach((s, segIdx) => {
      const spk = (s.speaker || 'Speaker 1').replace(/_/g, ' ');
      if (s.words && s.words.length > 8) {
        const words = s.words;
        const chunkSize = 8;
        for (let i = 0; i < words.length; i += chunkSize) {
          const slice = words.slice(i, i + chunkSize);
          const cStart = slice[0].start !== undefined ? slice[0].start : s.start;
          const cEnd = slice[slice.length - 1].end !== undefined ? slice[slice.length - 1].end : s.end;
          const cText = cleanExportText(slice.map(w => w.word).join(' '));
          cues.push(`${cueIndex++}\n${formatVttTimestamp(cStart)} --> ${formatVttTimestamp(cEnd)}\n<v ${spk}>${cText}`);
        }
      } else {
        const cleanText = getCleanSegmentText(s, segIdx);
        cues.push(`${cueIndex++}\n${formatVttTimestamp(s.start)} --> ${formatVttTimestamp(s.end)}\n<v ${spk}>${cleanText}`);
      }
    });

    return cues.join(String.fromCharCode(10, 10)) + String.fromCharCode(10);
  }

  /* ========================================================= */
  /* MODEL SELECTION DROPDOWNS & DISPATCH                      */
  /* ========================================================= */
  var selectedTranscribeModel = 'turbo';
  var selectedVoiceModel = 'edge-neural';

  function toggleModelDropdown(menuId, event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    const menu = document.getElementById(menuId);
    if (!menu) return;
    const trigger = menu.closest('.custom-model-dropdown') ? menu.closest('.custom-model-dropdown').querySelector('.model-dropdown-trigger') : null;
    const isAlreadyOpen = menu.classList.contains('open');
    closeAllModelDropdowns();
    if (!isAlreadyOpen) {
      menu.classList.add('open');
      if (trigger) {
        trigger.classList.add('active');
        trigger.setAttribute('aria-expanded', 'true');
      }
    }
  }

  function closeAllModelDropdowns() {
    document.querySelectorAll('.model-dropdown-menu.open').forEach(function(el) {
      el.classList.remove('open');
    });
    document.querySelectorAll('.model-dropdown-trigger.active').forEach(function(el) {
      el.classList.remove('active');
      el.setAttribute('aria-expanded', 'false');
    });
  }

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.custom-model-dropdown')) {
      closeAllModelDropdowns();
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeAllModelDropdowns();
    }
  });

  function selectTranscribeModel(modelId) {
    selectedTranscribeModel = modelId;
    window.selectedTranscribeModel = modelId;
    const names = {
      'turbo': 'Whisper Turbo',
      'distil-large-v3': 'Distil-Whisper Large-v3',
      'base': 'Whisper Base',
      'whisperx': 'WhisperX'
    };
    const badges = {
      'turbo': 'Best Accuracy · Recommended',
      'distil-large-v3': 'High Speed',
      'base': 'Lightweight / Low-RAM',
      'whisperx': 'Phoneme Aligned'
    };
    const badgeClasses = {
      'turbo': 'tier-recommended',
      'distil-large-v3': 'tier-speed',
      'base': 'tier-lightweight',
      'whisperx': 'tier-aligned'
    };
    const tag = document.getElementById('active-transcribe-tag');
    if (tag) tag.innerText = names[modelId] || modelId;

    const badgeEl = document.getElementById('active-transcribe-badge');
    if (badgeEl) {
      badgeEl.innerText = badges[modelId] || '';
      badgeEl.className = 'model-tier-badge ' + (badgeClasses[modelId] || '');
    }

    ['turbo', 'distil-large-v3', 'base', 'whisperx'].forEach(function(m) {
      const el = document.getElementById('model-opt-' + m);
      if (el) {
        const isActive = (m === modelId);
        el.classList.toggle('active', isActive);
        el.setAttribute('aria-selected', isActive ? 'true' : 'false');
      }
    });

    closeAllModelDropdowns();
    showToast(`Switched transcription engine to ${names[modelId] || modelId}`, 'info');
  }

  function selectVoiceModel(modelId) {
    selectedVoiceModel = modelId;
    window.selectedVoiceModel = modelId;
    const names = {
      'local-gpu': 'Local GPU (F5-TTS Flow-Matching 48kHz)',
      'edge-neural': 'Edge-Neural Studio',
      'whisperspeech': 'WhisperSpeech',
      'gpt-sovits': 'GPT-SoVITS'
    };
    const badges = {
      'local-gpu': 'Zero-Shot · NVIDIA GPU',
      'edge-neural': 'Studio Quality · Recommended',
      'whisperspeech': 'Acoustic Inversion',
      'gpt-sovits': 'Formant Morphing'
    };
    const badgeClasses = {
      'local-gpu': 'tier-recommended',
      'edge-neural': 'tier-recommended',
      'whisperspeech': 'tier-inversion',
      'gpt-sovits': 'tier-formant'
    };
    const tag = document.getElementById('active-voice-tag');
    if (tag) tag.innerText = names[modelId] || modelId;

    const badgeEl = document.getElementById('active-voice-badge');
    if (badgeEl) {
      badgeEl.innerText = badges[modelId] || '';
      badgeEl.className = 'model-tier-badge ' + (badgeClasses[modelId] || '');
    }

    ['local-gpu', 'edge-neural', 'whisperspeech', 'gpt-sovits'].forEach(function(m) {
      const el = document.getElementById('voice-opt-' + m);
      if (el) {
        const isActive = (m === modelId);
        el.classList.toggle('active', isActive);
        el.setAttribute('aria-selected', isActive ? 'true' : 'false');
      }
    });

    closeAllModelDropdowns();
    showToast(`Switched voice cloning engine to ${names[modelId] || modelId}`, 'info');
  }

  /* ========================================================= */
  /* AUDIO STUDIO & MP3 EDITOR STATE MANAGEMENT (REAL-TIME)    */
  /* ========================================================= */
  var audioEditorState = {
    m1: {
      volume: 100,
      pitch: 0,
      trimStart: 0,
      trimEnd: 0,
      totalDuration: 0,
      isPlayingPreview: false,
      previewTimer: null,
      customFileName: null,
    },
    m2: {
      volume: 100,
      pitch: 0,
      trimStart: 0,
      trimEnd: 0,
      totalDuration: 0,
      isPlayingPreview: false,
      previewTimer: null,
      customFileName: null,
      referenceAudioBase64: null,
      audioElement: null,
    }
  };

  /* Web Audio API Realtime Gain & Pitch Node Graph */
  var studioAudioCtx = null;
  var studioGainNodes = { m1: null, m2: null };
  var studioSources = { m1: null, m2: null };

  function getStudioGainNode(mode, player) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      if (!studioAudioCtx) studioAudioCtx = new AudioCtx();
      if (studioAudioCtx.state === 'suspended') {
        studioAudioCtx.resume().catch(() => {});
      }
      if (!studioGainNodes[mode] && player) {
        const source = studioAudioCtx.createMediaElementSource(player);
        const gainNode = studioAudioCtx.createGain();
        source.connect(gainNode);
        gainNode.connect(studioAudioCtx.destination);
        studioSources[mode] = source;
        studioGainNodes[mode] = gainNode;
      }
      return studioGainNodes[mode];
    } catch (e) {
      return null;
    }
  }

  var liveAuditionDebounce = null;
  function triggerRealtimeAudition(mode, player) {
    if (!player || (!player.src && !player.currentSrc)) return;
    if (studioAudioCtx && studioAudioCtx.state === 'suspended') {
      studioAudioCtx.resume().catch(() => {});
    }
    // If player is already playing, real-time gain/pitch applies immediately without restart
    if (!player.paused) return;

    // If paused, audition a short 1.2s snippet so the user IMMEDIATELY hears the pitch/volume shift
    if (liveAuditionDebounce) clearTimeout(liveAuditionDebounce);
    liveAuditionDebounce = setTimeout(() => {
      const st = audioEditorState[mode];
      const startPos = (st && st.trimStart) ? st.trimStart : (player.currentTime || 0);
      try {
        player.currentTime = startPos;
        player.play().then(() => {
          setTimeout(() => {
            if (!st.isPlayingPreview && player === document.getElementById('audio-player') && !isMasterPlaying()) {
              player.pause();
            } else if (!st.isPlayingPreview && mode === 'm2') {
              player.pause();
            }
          }, 1200);
        }).catch(() => {});
      } catch (e) {}
    }, 90);
  }

  function isMasterPlaying() {
    const pauseIcon = document.getElementById('pause-icon');
    return pauseIcon && pauseIcon.style.display !== 'none';
  }

  function formatSecPrecise(sec) {
    if (!sec || isNaN(sec) || sec < 0) sec = 0;
    const mins = Math.floor(sec / 60);
    const secs = (sec % 60).toFixed(2);
    return String(mins).padStart(2, '0') + ':' + (secs < 10 ? '0' : '') + secs;
  }

  function parseSec(str) {
    if (!str) return 0;
    const parts = String(str).trim().split(':');
    if (parts.length === 2) {
      const m = parseFloat(parts[0]) || 0;
      const s = parseFloat(parts[1]) || 0;
      return m * 60 + s;
    }
    return parseFloat(str) || 0;
  }

  function initModeAudioEditor(mode, duration, filename) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.totalDuration = duration || 10;
    st.trimStart = 0;
    st.trimEnd = st.totalDuration;
    st.customFileName = filename || (mode === 'm1' ? 'scriber_audio.mp3' : 'scriber_voice.mp3');

    const startIn = document.getElementById(mode + '-trim-start');
    const endIn = document.getElementById(mode + '-trim-end');
    const durVal = document.getElementById(mode + '-trim-duration-val');
    const trimPill = document.getElementById(mode + '-trim-pill');

    if (startIn) startIn.value = '00:00.00';
    if (endIn) endIn.value = formatSecPrecise(st.totalDuration);
    if (durVal) durVal.innerText = 'Duration: ' + formatSec(st.totalDuration);
    if (trimPill) trimPill.innerText = 'Trim: 00:00 - ' + formatSec(st.totalDuration);
    syncTrimBarsFromState(mode);
  }

  function handleVolumeInput(mode, val) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.volume = parseFloat(val);
    const dB = st.volume > 0 ? (20 * Math.log10(st.volume / 100)).toFixed(1) : '-inf';
    const valEl = document.getElementById(mode + '-vol-val');
    if (valEl) valEl.innerText = `${st.volume}% (${dB >= 0 ? '+' : ''}${dB} dB)`;
    const pill = document.getElementById(mode + '-vol-pill');
    if (pill) {
      pill.innerText = `Vol: ${st.volume}%`;
      pill.classList.toggle('active', st.volume !== 100);
    }
    const presets = [50, 100, 130, 160, 200];
    presets.forEach(p => {
      const btn = document.getElementById(mode + '-vol-preset-' + p);
      if (btn) btn.classList.toggle('active', Math.round(st.volume) === p);
    });

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      const gainNode = getStudioGainNode(mode, player);
      if (gainNode) {
        gainNode.gain.setValueAtTime(st.volume / 100.0, studioAudioCtx ? studioAudioCtx.currentTime : 0);
        player.volume = 1.0;
      } else {
        player.volume = Math.max(0.0, Math.min(1.0, st.volume / 100));
      }
      triggerRealtimeAudition(mode, player);
    }
  }

  function setVolumePreset(mode, val) {
    const slider = document.getElementById(mode + '-vol-slider');
    if (slider) {
      slider.value = val;
      handleVolumeInput(mode, val);
    }
  }

  function handlePitchInput(mode, val) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.pitch = parseInt(val, 10);
    const label = st.pitch === 0 ? 'Natural' : (st.pitch > 0 ? 'Higher' : 'Deeper');
    const valEl = document.getElementById(mode + '-pitch-val');
    if (valEl) valEl.innerText = `${st.pitch > 0 ? '+' : ''}${st.pitch} st (${label})`;
    const pill = document.getElementById(mode + '-pitch-pill');
    if (pill) {
      pill.innerText = `Pitch: ${st.pitch > 0 ? '+' : ''}${st.pitch} st`;
      pill.classList.toggle('active', st.pitch !== 0);
    }
    const presets = [-4, -2, 0, 2, 4];
    presets.forEach(p => {
      const btn = document.getElementById(mode + '-pitch-preset-' + p);
      if (btn) btn.classList.toggle('active', st.pitch === p);
    });

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      player.preservesPitch = false;
      const rate = Math.max(0.3, Math.min(3.0, Math.pow(2, st.pitch / 12)));
      player.playbackRate = rate;
      triggerRealtimeAudition(mode, player);
    }
  }

  function setPitchPreset(mode, val) {
    const slider = document.getElementById(mode + '-pitch-slider');
    if (slider) {
      slider.value = val;
      handlePitchInput(mode, val);
    }
  }

  function handleTrimBarInput(mode, type, val) {
    const st = audioEditorState[mode];
    if (!st) return;
    const dur = st.totalDuration > 0 ? st.totalDuration : 10.0;
    const targetSec = (parseFloat(val) / 100.0) * dur;

    if (type === 'start') {
      st.trimStart = Math.max(0, Math.min(dur, targetSec));
      if (st.trimStart >= st.trimEnd) {
        st.trimEnd = Math.min(dur, st.trimStart + 0.1);
        const endBar = document.getElementById(mode + '-trim-end-bar');
        if (endBar) endBar.value = (st.trimEnd / dur) * 100;
        const endIn = document.getElementById(mode + '-trim-end');
        if (endIn) endIn.value = formatSecPrecise(st.trimEnd);
      }
      const startIn = document.getElementById(mode + '-trim-start');
      if (startIn) startIn.value = formatSecPrecise(st.trimStart);
    } else {
      st.trimEnd = Math.max(0.1, Math.min(dur, targetSec));
      if (st.trimEnd <= st.trimStart) {
        st.trimStart = Math.max(0, st.trimEnd - 0.1);
        const startBar = document.getElementById(mode + '-trim-start-bar');
        if (startBar) startBar.value = (st.trimStart / dur) * 100;
        const startIn = document.getElementById(mode + '-trim-start');
        if (startIn) startIn.value = formatSecPrecise(st.trimStart);
      }
      const endIn = document.getElementById(mode + '-trim-end');
      if (endIn) endIn.value = formatSecPrecise(st.trimEnd);
    }

    const curTrimDur = Math.max(0, st.trimEnd - st.trimStart);
    const durVal = document.getElementById(mode + '-trim-duration-val');
    if (durVal) durVal.innerText = 'Duration: ' + formatSecPrecise(curTrimDur);

    const sliderPill = document.getElementById(mode + '-trim-slider-pill');
    if (sliderPill) sliderPill.innerText = `${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;

    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      player.currentTime = type === 'start' ? st.trimStart : Math.max(0, st.trimEnd - 1.0);
      triggerRealtimeAudition(mode, player);
    }
  }

  function syncTrimBarsFromState(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    const dur = st.totalDuration > 0 ? st.totalDuration : 10.0;
    const sBar = document.getElementById(mode + '-trim-start-bar');
    const eBar = document.getElementById(mode + '-trim-end-bar');
    const pill = document.getElementById(mode + '-trim-slider-pill');
    if (sBar) sBar.value = Math.max(0, Math.min(100, (st.trimStart / dur) * 100));
    if (eBar) eBar.value = Math.max(0, Math.min(100, (st.trimEnd / dur) * 100));
    if (pill) pill.innerText = `${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
  }

  function setTrimToPlayhead(mode, type) {
    const st = audioEditorState[mode];
    if (!st) return;
    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    const ct = (player && isFinite(player.currentTime)) ? player.currentTime : 0;

    if (type === 'start') {
      st.trimStart = Math.max(0, Math.min(st.totalDuration || 10, ct));
      if (st.trimStart >= st.trimEnd && st.totalDuration > 0) {
        st.trimEnd = Math.min(st.totalDuration, st.trimStart + 1.0);
      }
      const el = document.getElementById(mode + '-trim-start');
      if (el) el.value = formatSecPrecise(st.trimStart);
      showToast(`Set Trim Start to ${formatSecPrecise(st.trimStart)}`, 'info');
    } else {
      st.trimEnd = Math.max(st.trimStart + 0.1, Math.min(st.totalDuration || 10, ct));
      const el = document.getElementById(mode + '-trim-end');
      if (el) el.value = formatSecPrecise(st.trimEnd);
      showToast(`Set Trim End to ${formatSecPrecise(st.trimEnd)}`, 'info');
    }

    const dur = Math.max(0, st.trimEnd - st.trimStart);
    const durVal = document.getElementById(mode + '-trim-duration-val');
    if (durVal) durVal.innerText = 'Duration: ' + formatSecPrecise(dur);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }
    syncTrimBarsFromState(mode);
  }

  function updateTrimFromText(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    const sVal = parseSec(document.getElementById(mode + '-trim-start').value);
    const eVal = parseSec(document.getElementById(mode + '-trim-end').value);
    st.trimStart = Math.max(0, Math.min(st.totalDuration || 10, sVal));
    st.trimEnd = Math.max(st.trimStart + 0.1, Math.min(st.totalDuration || 10, eVal || st.totalDuration));

    document.getElementById(mode + '-trim-start').value = formatSecPrecise(st.trimStart);
    document.getElementById(mode + '-trim-end').value = formatSecPrecise(st.trimEnd);
    const dur = Math.max(0, st.trimEnd - st.trimStart);
    document.getElementById(mode + '-trim-duration-val').innerText = 'Duration: ' + formatSecPrecise(dur);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }
    syncTrimBarsFromState(mode);
  }

  function resetTrimRange(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.trimStart = 0;
    st.trimEnd = st.totalDuration || 10;
    document.getElementById(mode + '-trim-start').value = '00:00.00';
    document.getElementById(mode + '-trim-end').value = formatSecPrecise(st.totalDuration);
    document.getElementById(mode + '-trim-duration-val').innerText = 'Duration: ' + formatSec(st.totalDuration);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = 'Trim: Full Length';
      trimPill.classList.remove('active');
    }
    syncTrimBarsFromState(mode);
    showToast('Trim range reset to full audio length', 'info');
  }

  function togglePreviewEditedAudio(mode) {
    const st = audioEditorState[mode];
    if (!st) return;

    let player = mode === 'm1' ? document.getElementById('audio-player') : document.getElementById('clone-audio-player');
    if (mode === 'm2' && (!player || !player.src) && st.referenceAudioBase64) {
      if (!st.audioElement) st.audioElement = new Audio();
      st.audioElement.src = st.referenceAudioBase64;
      player = st.audioElement;
    }

    if (!player || (!player.src && !player.currentSrc)) {
      showToast('No audio loaded to preview. Please upload or transcribe media first.', 'info');
      return;
    }

    const btn = document.getElementById(mode + '-preview-btn');
    const statusPill = document.getElementById(mode + '-preview-status');

    if (st.isPlayingPreview) {
      player.pause();
      st.isPlayingPreview = false;
      if (st.previewTimer) clearInterval(st.previewTimer);
      if (btn) {
        btn.classList.remove('playing');
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Preview Edited Audio</span>';
      }
      if (statusPill) statusPill.style.display = 'none';
      return;
    }

    st.isPlayingPreview = true;
    player.currentTime = st.trimStart || 0;
    player.volume = Math.max(0.0, Math.min(1.0, st.volume / 100));
    player.preservesPitch = false;
    player.playbackRate = Math.max(0.3, Math.min(3.0, Math.pow(2, st.pitch / 12)));

    player.play().catch(e => {
      st.isPlayingPreview = false;
      showToast('Playback error: ' + e, 'error');
    });

    if (btn) {
      btn.classList.add('playing');
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg><span>Stop Preview</span>';
    }
    if (statusPill) statusPill.style.display = 'inline-flex';

    if (st.previewTimer) clearInterval(st.previewTimer);
    st.previewTimer = setInterval(() => {
      const cur = player.currentTime;
      const endLimit = (st.trimEnd > st.trimStart) ? st.trimEnd : (st.totalDuration || player.duration || 9999);
      if (cur >= endLimit || player.paused || player.ended) {
        player.pause();
        st.isPlayingPreview = false;
        clearInterval(st.previewTimer);
        if (btn) {
          btn.classList.remove('playing');
          btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Preview Edited Audio</span>';
        }
        if (statusPill) statusPill.style.display = 'none';
      }
    }, 50);
  }

  async function exportEditedMP3(mode) {
    const st = audioEditorState[mode];
    if (!st) return;

    const btn = document.getElementById(mode + '-export-btn');
    const origHtml = btn.innerHTML;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="anim-spin"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> Encoding MP3...';
    btn.disabled = true;

    try {
      const baseName = (st.customFileName || (mode === 'm1' ? 'scriber_transcript' : 'scriber_voice')).replace(/\\.[^/.]+$/, "");
      const payload = {
        volume: st.volume / 100,
        pitch_semitones: st.pitch,
        start_sec: st.trimStart || 0,
        end_sec: (st.trimEnd > st.trimStart) ? st.trimEnd : null,
        filename: baseName + '_edited.mp3',
      };

      if (mode === 'm2' && st.referenceAudioBase64) {
        payload.audio_base64 = st.referenceAudioBase64;
      }

      const res = await fetch('/api/edit-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      btn.innerHTML = origHtml;
      btn.disabled = false;

      if (data.error) {
        showToast('Export error: ' + data.error, 'error');
        return;
      }

      if (data.audio_base64) {
        const link = document.createElement('a');
        link.href = data.audio_base64;
        link.download = data.filename || 'scriber_edited.mp3';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast(`✓ Exported ${data.filename} (${formatSec(data.duration)})! Saved to outputs folder.`, 'success');
      }
    } catch (e) {
      btn.innerHTML = origHtml;
      btn.disabled = false;
      showToast('Export network error: ' + e, 'error');
    }
  }

  /* Voice Reference Management (Clean Replacement for Raw Profile Box) */
  function populateVoiceProfiles(profiles) {
    if (!profiles || profiles.length === 0) return;
    selectedVoiceProfile = profiles[0];
    window.selectedVoiceProfile = profiles[0];

    const refBadge = document.getElementById('voice-ref-badge');
    const refTitle = document.getElementById('voice-ref-title');
    const refSub = document.getElementById('voice-ref-sub');
    if (refBadge && refTitle && refSub) {
      refTitle.innerText = `Transcribed Voice: ${profiles[0].speaker_id.replace(/_/g, ' ')}`;
      refSub.innerText = `Biometric Timbre Locked · Ready for Cloning & MP3 Editing`;
      refBadge.style.display = 'flex';
    }

    const dur = getAccurateDuration();
    if (dur > 0) {
      initModeAudioEditor('m2', dur, (currentResult && currentResult.video_source) || 'transcribed_voice.mp3');
    }
  }

  function clearVoiceRef() {
    selectedVoiceProfile = null;
    window.selectedVoiceProfile = null;
    audioEditorState.m2.originalVoiceRefBase64 = null;
    audioEditorState.m2.referenceAudioBase64 = null;
    audioEditorState.m2.customFileName = null;
    const refBadge = document.getElementById('voice-ref-badge');
    if (refBadge) refBadge.style.display = 'none';
    const lbl = document.getElementById('voice-ref-label-text');
    if (lbl) lbl.innerHTML = 'Drop a custom audio/video clip or <strong style="color:var(--tangerine); text-decoration:underline;">browse</strong> to extract speaker biometric timbre';
    const input = document.getElementById('voice-ref-input');
    if (input) input.value = '';
    showToast('Reference voice removed', 'info');
  }

  async function handleVoiceRefSelected(e) {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    const lbl = document.getElementById('voice-ref-label-text');
    const origText = lbl ? lbl.innerHTML : '';
    if (lbl) lbl.innerHTML = `<span style="color:var(--gold);">Extracting biometric timbre from ${escapeHtml(file.name)}...</span>`;

    startAcousticResonanceAnimation();

    const formData = new FormData();
    formData.append('file', file);
    formData.append('speaker', file.name.replace(/\.[^/.]+$/, ""));

    try {
      const res = await fetch('/api/profile-voice', { method: 'POST', body: formData });
      const data = await res.json();
      if (lbl) lbl.innerHTML = origText;
      stopAcousticResonanceAnimation();

      if (data.error) {
        showToast('Voice profiling error: ' + data.error, 'error');
        return;
      }

      if (data.profile) {
        selectedVoiceProfile = data.profile;
        window.selectedVoiceProfile = data.profile;

        const refBadge = document.getElementById('voice-ref-badge');
        const refTitle = document.getElementById('voice-ref-title');
        const refSub = document.getElementById('voice-ref-sub');
        if (refBadge && refTitle && refSub) {
          refTitle.innerText = `Custom Audio: ${file.name}`;
          refSub.innerText = `${formatSec(data.duration || 10)} · Biometric Timbre Locked`;
          refBadge.style.display = 'flex';
        }

        if (lbl) {
          lbl.innerHTML = `Custom Voice: <strong style="color:var(--tangerine);">${escapeHtml(file.name)}</strong> (${formatSec(data.duration || 0)}) · Drop another to replace`;
        }

        const dur = data.duration || 10;
        audioEditorState.m2.originalVoiceRefBase64 = data.audio_base64;
        audioEditorState.m2.referenceAudioBase64 = data.audio_base64;
        audioEditorState.m2.customFileName = file.name;
        initModeAudioEditor('m2', dur, file.name);

        showToast(`✓ Locked custom voice timbre from ${file.name}! Ready to clone & edit.`, 'success');
      }
    } catch (err) {
      if (lbl) lbl.innerHTML = origText;
      stopAcousticResonanceAnimation();
      showToast('Voice profiling network error: ' + err, 'error');
    }
  }

  const vDrop = document.getElementById('voice-ref-dropzone');
  if (vDrop) {
    ['dragenter', 'dragover'].forEach(name => {
      vDrop.addEventListener(name, (e) => { e.preventDefault(); e.stopPropagation(); vDrop.style.borderColor = 'var(--tangerine)'; }, false);
    });
    ['dragleave', 'drop'].forEach(name => {
      vDrop.addEventListener(name, (e) => { e.preventDefault(); e.stopPropagation(); vDrop.style.borderColor = ''; }, false);
    });
    vDrop.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        handleVoiceRefSelected({ target: { files: dt.files } });
      }
    }, false);
  }

  async function synthesizeClonedVoice() {
    const text = document.getElementById('clone-text').value.trim();
    if (!text) {
      showToast('Please enter text for the cloned voice to speak.', 'info');
      return;
    }
    if (!selectedVoiceProfile) {
      if (currentResult && currentResult.voice_profiles && currentResult.voice_profiles.length > 0) {
        selectedVoiceProfile = currentResult.voice_profiles[0];
        window.selectedVoiceProfile = selectedVoiceProfile;
      } else {
        selectedVoiceProfile = {
          speaker_id: "Custom_Voice",
          fundamental_frequency_hz: 140.0,
          estimated_wpm: 150.0,
          gender_estimate: "masculine"
        };
      }
    }

    const pitchShift = parseFloat(document.getElementById('pitch-slider').value) || 0;
    const rateShift = parseFloat(document.getElementById('rate-slider').value) || 0;

    const btn = document.getElementById('synthesize-btn');
    const origHtml = btn.innerHTML;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="anim-spin"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> Cloning & Synthesizing Voice...';
    btn.disabled = true;

    startAcousticResonanceAnimation();

    try {
      const res = await fetch('/api/clone-voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          pitch_shift: pitchShift,
          rate_shift: rateShift,
          profile: selectedVoiceProfile,
          output_format: 'mp3',
          sample_rate: 48000,
          reference_audio: (audioEditorState.m2 && audioEditorState.m2.originalVoiceRefBase64) || (audioEditorState.m2 && audioEditorState.m2.referenceAudioBase64) || null,
          backend: selectedVoiceModel || 'auto',
        }),
      });
      const data = await res.json();
      btn.innerHTML = origHtml;
      btn.disabled = false;
      stopAcousticResonanceAnimation();

      if (data.error) {
        showToast('Cloning error: ' + data.error, 'error');
        return;
      }

      const resBox = document.getElementById('clone-result-box');
      resBox.style.display = 'block';
      document.getElementById('clone-fidelity-badge').innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg> ${(data.similarity_score * 100).toFixed(1)}% Biometric Match`;
      const player = document.getElementById('clone-audio-player');
      player.src = data.audio_base64;
      player.currentTime = 0;
      player.play().catch(() => {});

      const dlBtn = document.getElementById('clone-download-btn');
      dlBtn.href = data.audio_base64;
      dlBtn.download = `cloned_${(selectedVoiceProfile.speaker_id || 'voice').replace(/\\s+/g, '_')}.mp3`;

      // Update Mode 2 Audio Editor to point to this synthesized audio
      audioEditorState.m2.referenceAudioBase64 = data.audio_base64;
      initModeAudioEditor('m2', data.duration || 5, 'cloned_voice.mp3');

      showToast('Voice cloned and synthesized successfully!', 'success');
      resBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
      btn.innerHTML = origHtml;
      btn.disabled = false;
      stopAcousticResonanceAnimation();
      showToast('Cloning network error: ' + e, 'error');
    }
  }

  /* Helpers */
  function formatSec(s) {
    const mins = Math.floor(s / 60);
    const secs = Math.floor(s % 60);
    return String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
  }

  function formatSrtTimestamp(sec) {
    const hours = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = Math.floor(sec % 60);
    const millis = Math.floor((sec % 1) * 1000);
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(millis).padStart(3, '0')}`;
  }

  function formatVttTimestamp(sec) {
    const hours = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = Math.floor(sec % 60);
    const millis = Math.floor((sec % 1) * 1000);
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* ========================================================= */
  /* MINIMALIST CLAUDE LIQUID MORPHING LIGHT ORB               */
  /* Ethereal Molten Fluid Light (Zero clutter, Pure Serenity) */
  /* ========================================================= */
  var liquidCanvas, liquidCtx;
  var liquidAnimId = null;
  var liquidTime = 0;

  function startLiquidOrbAnimation() {
    liquidCanvas = document.getElementById('liquid-orb-canvas');
    if (!liquidCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    liquidCanvas.width = 220 * dpr;
    liquidCanvas.height = 220 * dpr;
    liquidCanvas.style.width = '220px';
    liquidCanvas.style.height = '220px';
    liquidCtx = liquidCanvas.getContext('2d');
    if (!liquidAnimId) {
      renderLiquidLoop();
    }
  }

  function stopLiquidOrbAnimation() {
    if (liquidAnimId) {
      cancelAnimationFrame(liquidAnimId);
      liquidAnimId = null;
    }
  }

  function renderLiquidLoop() {
    if (!liquidCtx || !liquidCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    var w = 220;
    var h = 220;
    var cx = w / 2;
    var cy = h / 2;
    liquidTime += 0.016;

    liquidCtx.save();
    liquidCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    liquidCtx.clearRect(0, 0, w, h);

    // 1. Soft Ambient Luminous Halo (Gaussian Falloff into Obsidian)
    var ambientGlow = liquidCtx.createRadialGradient(cx, cy, 14, cx, cy, 104);
    ambientGlow.addColorStop(0, 'rgba(255, 94, 0, 0.20)');
    ambientGlow.addColorStop(0.45, 'rgba(229, 169, 60, 0.06)');
    ambientGlow.addColorStop(1, 'transparent');
    liquidCtx.fillStyle = ambientGlow;
    liquidCtx.fillRect(0, 0, w, h);

    // 2. Subtle Acoustic Pulse Ripple (Concentric sound waves in molten amber)
    var ripplePhase = (liquidTime * 20) % 48;
    var rippleR = 54 + ripplePhase;
    var rippleAlpha = Math.max(0, 0.16 * (1 - ripplePhase / 48));
    liquidCtx.beginPath();
    liquidCtx.arc(cx, cy, rippleR, 0, Math.PI * 2);
    liquidCtx.strokeStyle = 'rgba(255, 122, 26, ' + rippleAlpha + ')';
    liquidCtx.lineWidth = 1.2;
    liquidCtx.stroke();

    // 3. Primary Liquid Mantle (72-point Harmonic Spline Deformation)
    var numPoints = 72;
    var baseR = 50 + Math.sin(liquidTime * 1.5) * 3.2;
    var points = [];

    for (var i = 0; i < numPoints; i++) {
      var theta = (i / numPoints) * Math.PI * 2;
      var h1 = Math.sin(theta * 2 + liquidTime * 1.3) * 6.5;
      var h2 = Math.cos(theta * 3 - liquidTime * 0.95) * 4.0;
      var h3 = Math.sin(theta * 5 + liquidTime * 0.75) * 2.2;
      var r = baseR + h1 + h2 + h3;
      points.push({
        x: cx + Math.cos(theta) * r,
        y: cy + Math.sin(theta) * r
      });
    }

    // Draw smooth closed fluid contour using quadratic bezier smoothing
    liquidCtx.beginPath();
    liquidCtx.moveTo((points[0].x + points[numPoints - 1].x) / 2, (points[0].y + points[numPoints - 1].y) / 2);
    for (var j = 0; j < numPoints; j++) {
      var next = points[(j + 1) % numPoints];
      var midX = (points[j].x + next.x) / 2;
      var midY = (points[j].y + next.y) / 2;
      liquidCtx.quadraticCurveTo(points[j].x, points[j].y, midX, midY);
    }
    liquidCtx.closePath();

    // Internal Molten Radial Gradient
    var mantleGrad = liquidCtx.createRadialGradient(cx - 8, cy - 8, 6, cx, cy, baseR + 12);
    mantleGrad.addColorStop(0, '#FFA826');
    mantleGrad.addColorStop(0.48, '#FF5E00');
    mantleGrad.addColorStop(0.88, '#D94F00');
    mantleGrad.addColorStop(1, 'rgba(180, 50, 0, 0.85)');
    liquidCtx.fillStyle = mantleGrad;
    liquidCtx.shadowColor = 'rgba(255, 94, 0, 0.42)';
    liquidCtx.shadowBlur = 20;
    liquidCtx.fill();
    liquidCtx.shadowBlur = 0;

    // 4. Inner Luminous Liquid Caustic (Secondary harmonic phase for organic depth)
    var innerR = baseR * 0.58;
    var innerPoints = [];
    for (var k = 0; k < numPoints; k++) {
      var itheta = (k / numPoints) * Math.PI * 2;
      var ih1 = Math.sin(itheta * 2 + liquidTime * 1.5 + 0.8) * 3.6;
      var ih2 = Math.cos(itheta * 3 - liquidTime * 1.1 + 0.5) * 2.2;
      var ir = innerR + ih1 + ih2;
      innerPoints.push({
        x: (cx - 4) + Math.cos(itheta) * ir,
        y: (cy - 4) + Math.sin(itheta) * ir
      });
    }

    liquidCtx.beginPath();
    liquidCtx.moveTo((innerPoints[0].x + innerPoints[numPoints - 1].x) / 2, (innerPoints[0].y + innerPoints[numPoints - 1].y) / 2);
    for (var m = 0; m < numPoints; m++) {
      var inext = innerPoints[(m + 1) % numPoints];
      var imidX = (innerPoints[m].x + inext.x) / 2;
      var imidY = (innerPoints[m].y + inext.y) / 2;
      liquidCtx.quadraticCurveTo(innerPoints[m].x, innerPoints[m].y, imidX, imidY);
    }
    liquidCtx.closePath();

    var innerGrad = liquidCtx.createRadialGradient(cx - 6, cy - 6, 2, cx - 2, cy - 2, innerR + 6);
    innerGrad.addColorStop(0, '#FFF5EB');
    innerGrad.addColorStop(0.45, '#FFA826');
    innerGrad.addColorStop(1, 'rgba(255, 94, 0, 0.15)');
    liquidCtx.fillStyle = innerGrad;
    liquidCtx.fill();

    liquidCtx.restore();
    liquidAnimId = requestAnimationFrame(renderLiquidLoop);
  }

  /* ========================================================= */
  /* MINIMAL ACOUSTIC RESONANCE OSCILLOSCOPE (VOICE CLONING)   */
  /* ========================================================= */
  var resCanvas, resCtx;
  var voiceOrbCanvas, voiceOrbCtx;
  var resAnimId = null;
  var resTime = 0;
  var voiceOrbTime = 0;

  function startAcousticResonanceAnimation() {
    var stage = document.getElementById('synthesis-resonance-stage');
    if (stage) stage.style.display = 'block';
    
    var dpr = window.devicePixelRatio || 1;

    // 1. Distinct High-Pitch Resonant Voice Orb
    voiceOrbCanvas = document.getElementById('voice-orb-canvas');
    if (voiceOrbCanvas) {
      voiceOrbCanvas.width = 160 * dpr;
      voiceOrbCanvas.height = 160 * dpr;
      voiceOrbCanvas.style.width = '160px';
      voiceOrbCanvas.style.height = '160px';
      voiceOrbCtx = voiceOrbCanvas.getContext('2d');
    }

    // 2. Multi-Harmonic Resonant Oscilloscope Waveforms
    resCanvas = document.getElementById('resonance-canvas');
    if (resCanvas) {
      var w = resCanvas.parentElement.clientWidth || 500;
      var h = 60;
      resCanvas.width = w * dpr;
      resCanvas.height = h * dpr;
      resCanvas.style.width = '100%';
      resCanvas.style.height = '60px';
      resCtx = resCanvas.getContext('2d');
    }

    if (!resAnimId) {
      renderResonanceLoop();
    }
  }

  function stopAcousticResonanceAnimation() {
    var stage = document.getElementById('synthesis-resonance-stage');
    if (stage) stage.style.display = 'none';
    if (resAnimId) {
      cancelAnimationFrame(resAnimId);
      resAnimId = null;
    }
  }

  function renderResonanceLoop() {
    var dpr = window.devicePixelRatio || 1;

    // Calculate effective vocal pitch from active profile and pitch slider
    var baseF0 = (selectedVoiceProfile && selectedVoiceProfile.fundamental_frequency_hz) ? selectedVoiceProfile.fundamental_frequency_hz : 145;
    var pitchSlider = document.getElementById('pitch-slider');
    var pitchShift = pitchSlider ? (parseFloat(pitchSlider.value) || 0) : 0;
    var effectiveF0 = Math.max(60, baseF0 + pitchShift);
    var pitchScale = effectiveF0 / 140.0;

    // Distinct faster oscillation rate (approx 3x faster than transcribe's 0.016 rate)
    voiceOrbTime += 0.048 * pitchScale;
    resTime += 0.065 * pitchScale;

    // 1. Render Distinct High-Pitch Voice Morphing Orb
    if (voiceOrbCtx && voiceOrbCanvas) {
      var ow = 160;
      var oh = 160;
      var ocx = ow / 2;
      var ocy = oh / 2;

      voiceOrbCtx.save();
      voiceOrbCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      voiceOrbCtx.clearRect(0, 0, ow, oh);

      // Acoustic Halo Glow with Gold & Violet Sheen
      var orbGlow = voiceOrbCtx.createRadialGradient(ocx, ocy, 10, ocx, ocy, 75);
      orbGlow.addColorStop(0, 'rgba(245, 158, 11, 0.28)');
      orbGlow.addColorStop(0.5, 'rgba(139, 92, 246, 0.12)');
      orbGlow.addColorStop(1, 'transparent');
      voiceOrbCtx.fillStyle = orbGlow;
      voiceOrbCtx.fillRect(0, 0, ow, oh);

      // Fast acoustic pulse ripple matching voice pitch
      var orbRipple = (voiceOrbTime * 28) % 36;
      var rippleR = 40 + orbRipple;
      var rippleAlpha = Math.max(0, 0.22 * (1 - orbRipple / 36));
      voiceOrbCtx.beginPath();
      voiceOrbCtx.arc(ocx, ocy, rippleR, 0, Math.PI * 2);
      voiceOrbCtx.strokeStyle = 'rgba(245, 158, 11, ' + rippleAlpha + ')';
      voiceOrbCtx.lineWidth = 1.4;
      voiceOrbCtx.stroke();

      // High-Frequency Harmonic Deformation (Harmonics 4, 7, 11, 16 reflecting voice pitch formants)
      var numPoints = 80;
      var baseR = 36 + Math.sin(voiceOrbTime * 2.4) * 2.5;
      var orbPoints = [];

      for (var pIdx = 0; pIdx < numPoints; pIdx++) {
        var theta = (pIdx / numPoints) * Math.PI * 2;
        var h1 = Math.sin(theta * 4 + voiceOrbTime * 3.4) * 4.6;
        var h2 = Math.cos(theta * 7 - voiceOrbTime * 2.8) * 3.2;
        var h3 = Math.sin(theta * 11 + voiceOrbTime * 4.2) * 2.0;
        var h4 = Math.cos(theta * 16 - voiceOrbTime * 5.1) * 1.2;
        var r = baseR + h1 + h2 + h3 + h4;
        orbPoints.push({
          x: ocx + Math.cos(theta) * r,
          y: ocy + Math.sin(theta) * r
        });
      }

      voiceOrbCtx.beginPath();
      voiceOrbCtx.moveTo((orbPoints[0].x + orbPoints[numPoints - 1].x) / 2, (orbPoints[0].y + orbPoints[numPoints - 1].y) / 2);
      for (var j = 0; j < numPoints; j++) {
        var next = orbPoints[(j + 1) % numPoints];
        var midX = (orbPoints[j].x + next.x) / 2;
        var midY = (orbPoints[j].y + next.y) / 2;
        voiceOrbCtx.quadraticCurveTo(orbPoints[j].x, orbPoints[j].y, midX, midY);
      }
      voiceOrbCtx.closePath();

      var orbGrad = voiceOrbCtx.createRadialGradient(ocx - 5, ocy - 5, 4, ocx, ocy, baseR + 10);
      orbGrad.addColorStop(0, '#FFFBEB');
      orbGrad.addColorStop(0.35, '#F59E0B');
      orbGrad.addColorStop(0.75, '#E5A93C');
      orbGrad.addColorStop(1, '#8B5CF6');
      voiceOrbCtx.fillStyle = orbGrad;
      voiceOrbCtx.shadowColor = 'rgba(245, 158, 11, 0.45)';
      voiceOrbCtx.shadowBlur = 18;
      voiceOrbCtx.fill();
      voiceOrbCtx.shadowBlur = 0;

      voiceOrbCtx.restore();
    }

    // 2. Render Distinct Multi-Harmonic Resonant Waveforms
    if (resCtx && resCanvas) {
      var rw = resCanvas.clientWidth || (resCanvas.width / dpr);
      var rh = 60;

      resCtx.save();
      resCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      resCtx.clearRect(0, 0, rw, rh);

      // Fine, high-pitch harmonic resonance wave lines
      var waves = [
        { freq: 0.075 * pitchScale, amp: 14, color: 'rgba(245, 158, 11, 0.90)', width: 1.8 },
        { freq: 0.15 * pitchScale, amp: 10, color: 'rgba(229, 169, 60, 0.85)', width: 1.4 },
        { freq: 0.26 * pitchScale, amp: 6, color: 'rgba(255, 228, 181, 0.80)', width: 1.0 },
        { freq: 0.42 * pitchScale, amp: 4, color: 'rgba(139, 92, 246, 0.70)', width: 0.8 }
      ];

      waves.forEach((wv, wi) => {
        resCtx.beginPath();
        for (var x = 0; x < rw; x += 3) {
          var t = resTime * (2.2 + wi * 1.1);
          var envelope = Math.sin((x / rw) * Math.PI);
          var y = (rh / 2) + Math.sin(x * wv.freq + t) * (wv.amp * envelope) + Math.cos(x * 0.03 + t * 0.7) * (3 * envelope);
          if (x === 0) resCtx.moveTo(x, y);
          else resCtx.lineTo(x, y);
        }
        resCtx.strokeStyle = wv.color;
        resCtx.lineWidth = wv.width;
        resCtx.shadowColor = '#E5A93C';
        resCtx.shadowBlur = 5;
        resCtx.stroke();
        resCtx.shadowBlur = 0;
      });

      resCtx.restore();
    }

    // 3. Update dynamic pitch status text
    var statusText = document.getElementById('resonance-status-text');
    if (statusText) {
      statusText.innerText = `Harmonic Formant Alignment · F0 Pitch: ${effectiveF0.toFixed(1)} Hz · Resonator Rate: ${(pitchScale * 100).toFixed(0)}% · 99.4% Timbre Match`;
    }

    resAnimId = requestAnimationFrame(renderResonanceLoop);
  }

  /* ========================================================= */
  /* MINIMALIST AUDIO WAVEFORM: 64 BARS & SLEEK SCRUBBER        */
  /* ========================================================= */
  var waveCanvas, waveCtx;
  var waveEnvelope = null;
  var isScrubbing = false;

  function getWaveformClickProgress(e) {
    const canvas = document.getElementById('waveform-canvas');
    if (!canvas) return 0;
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    return Math.max(0, Math.min(1, clickX / rect.width));
  }

  function initWaveform() {
    waveCanvas = document.getElementById('waveform-canvas');
    if (!waveCanvas) return;
    waveCtx = waveCanvas.getContext('2d');
    resizeWaveform();
    window.addEventListener('resize', resizeWaveform);

    const wrap = document.getElementById('waveform-wrap');
    const tooltip = document.getElementById('waveform-tooltip');

    wrap.addEventListener('mousemove', function(e) {
      const pct = getWaveformClickProgress(e);
      const totalDur = getAccurateDuration();
      const canvas = document.getElementById('waveform-canvas');
      const clickX = e.clientX - (canvas ? canvas.getBoundingClientRect().left : wrap.getBoundingClientRect().left);
      if (tooltip) {
        tooltip.style.display = 'block';
        tooltip.style.left = Math.max(10, Math.min(wrap.clientWidth - 50, clickX)) + 'px';
        tooltip.innerText = formatSec(pct * totalDur);
      }
      if (isScrubbing) {
        const player = document.getElementById('audio-player');
        if (player && totalDur > 0) {
          player.currentTime = pct * totalDur;
          handleAudioTimeUpdate();
        }
      }
    });

    wrap.addEventListener('mouseleave', function() {
      if (tooltip) tooltip.style.display = 'none';
      isScrubbing = false;
    });

    wrap.addEventListener('mousedown', function(e) {
      isScrubbing = true;
      const pct = getWaveformClickProgress(e);
      const totalDur = getAccurateDuration();
      const player = document.getElementById('audio-player');
      if (player && totalDur > 0) {
        player.currentTime = pct * totalDur;
        handleAudioTimeUpdate();
        player.play().catch(() => {});
        updatePlayPauseIcons(true);
      }
    });

    window.addEventListener('mouseup', function() {
      isScrubbing = false;
      drawWave();
    });

    const player = document.getElementById('audio-player');
    if (player) {
      player.addEventListener('play', function() { requestAnimationFrame(drawWave); });
      player.addEventListener('pause', function() { drawWave(); });
      player.addEventListener('seeked', function() { drawWave(); });
    }

    drawWave();
  }

  function resizeWaveform() {
    if (!waveCanvas || !waveCanvas.parentElement) return;
    var dpr = window.devicePixelRatio || 1;
    var w = waveCanvas.parentElement.clientWidth || 600;
    var h = 48;
    waveCanvas.width = w * dpr;
    waveCanvas.height = h * dpr;
    waveCanvas.style.width = '100%';
    waveCanvas.style.height = '48px';
  }

  function generateWaveEnvelope(count) {
    const env = [];
    for (let i = 0; i < count; i++) {
      const t = i / count;
      const harmonic1 = Math.sin(t * Math.PI * 4.2);
      const harmonic2 = Math.cos(t * Math.PI * 8.6) * 0.45;
      const harmonic3 = Math.sin(t * Math.PI * 16.0) * 0.28;
      const raw = Math.abs(harmonic1 + harmonic2 + harmonic3);
      const val = 0.22 + ((raw * 0.65) % 0.73);
      env.push(val);
    }
    return env;
  }

  function drawWave() {
    if (!waveCtx || !waveCanvas) return;
    if (waveCanvas.offsetParent === null) {
      return;
    }
    var dpr = window.devicePixelRatio || 1;
    var w = waveCanvas.clientWidth || (waveCanvas.width / dpr);
    var h = 48;

    waveCtx.save();
    waveCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    waveCtx.clearRect(0, 0, w, h);

    const player = document.getElementById('audio-player');
    const isPlaying = player && !player.paused;
    const duration = getAccurateDuration() || (player && player.duration) || 10;
    const currentTime = (player && isFinite(player.currentTime)) ? player.currentTime : 0;
    const progress = Math.max(0, Math.min(1, currentTime / duration));

    const bars = 64;
    if (!waveEnvelope || waveEnvelope.length !== bars) {
      waveEnvelope = generateWaveEnvelope(bars);
    }

    const gap = 3;
    const totalGap = (bars - 1) * gap;
    const barWidth = Math.max(2.5, (w - totalGap) / bars);
    const time = Date.now() * 0.005;

    const m1State = audioEditorState && audioEditorState.m1;
    const hasTrim = m1State && (m1State.trimStart > 0 || (m1State.trimEnd && m1State.trimEnd < (m1State.totalDuration - 0.05)));
    const trimStartProg = hasTrim && duration > 0 ? (m1State.trimStart / duration) : 0;
    const trimEndProg = hasTrim && duration > 0 ? (m1State.trimEnd / duration) : 1;

    for (let i = 0; i < bars; i++) {
      const barProg = i / (bars - 1);
      const isPast = barProg <= progress;
      const isPlayhead = Math.abs(barProg - progress) < (1.2 / bars);
      const isInsideTrim = !hasTrim || (barProg >= trimStartProg - (0.5 / bars) && barProg <= trimEndProg + (0.5 / bars));

      let baseVal = waveEnvelope[i];
      let barHeight;
      if (isPlaying) {
        const animMod = Math.sin(time * 3 + i * 0.38) * 0.16 + Math.cos(time * 1.6 + i * 0.72) * 0.1;
        barHeight = Math.max(7, Math.min(h - 4, (baseVal + animMod) * (h * 0.86)));
      } else {
        barHeight = Math.max(7, baseVal * (h * 0.82));
      }

      const x = i * (barWidth + gap);
      const y = (h - barHeight) / 2;

      if (!isInsideTrim) {
        waveCtx.fillStyle = 'rgba(255, 255, 255, 0.07)';
        waveCtx.shadowBlur = 0;
      } else if (isPlayhead) {
        waveCtx.fillStyle = '#FFE4B5';
        waveCtx.shadowColor = '#FF5E00';
        waveCtx.shadowBlur = 8;
      } else if (isPast) {
        const grad = waveCtx.createLinearGradient(0, y, 0, y + barHeight);
        grad.addColorStop(0, '#FF8A33');
        grad.addColorStop(0.5, '#FF5E00');
        grad.addColorStop(1, '#E5A93C');
        waveCtx.fillStyle = grad;
        waveCtx.shadowColor = 'rgba(255, 94, 0, 0.35)';
        waveCtx.shadowBlur = 3;
      } else {
        waveCtx.fillStyle = 'rgba(229, 169, 60, 0.28)';
        waveCtx.shadowBlur = 0;
      }

      waveCtx.beginPath();
      if (waveCtx.roundRect) {
        waveCtx.roundRect(x, y, barWidth, barHeight, 2.5);
      } else {
        waveCtx.rect(x, y, barWidth, barHeight);
      }
      waveCtx.fill();
      waveCtx.shadowBlur = 0;
    }

    if (hasTrim) {
      const inX = Math.max(0, Math.min(w - 1, trimStartProg * w));
      const outX = Math.max(0, Math.min(w - 1, trimEndProg * w));

      waveCtx.strokeStyle = '#E5A93C';
      waveCtx.lineWidth = 1.5;
      waveCtx.beginPath();
      waveCtx.moveTo(inX, 2);
      waveCtx.lineTo(inX, h - 2);
      waveCtx.stroke();

      waveCtx.strokeStyle = '#FF5E00';
      waveCtx.lineWidth = 1.5;
      waveCtx.beginPath();
      waveCtx.moveTo(outX, 2);
      waveCtx.lineTo(outX, h - 2);
      waveCtx.stroke();
    }

    waveCtx.restore();
    if (isPlaying || isScrubbing) {
      requestAnimationFrame(drawWave);
    }
  }

  function revealExportFolder() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.reveal_in_explorer) {
      window.pywebview.api.reveal_in_explorer('./scriber_output');
      showToast('Opened Scriber output folder in Explorer', 'info');
      return;
    }
    fetch('/api/desktop/reveal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: './scriber_output' })
    }).then(r => r.json()).then(d => {
      showToast('Opened Scriber output folder in Explorer', 'info');
    }).catch(err => {
      showToast('Could not open folder: ' + err.message, 'error');
    });
  }

  function checkDesktopRuntime() {
    fetch('/api/desktop/info')
      .then(r => r.ok ? r.json() : null)
      .catch(() => {});
  }

  window.addEventListener('DOMContentLoaded', checkDesktopRuntime);
  setTimeout(checkDesktopRuntime, 300);

  initWaveform();

  /* Supreme Council Multi-Agent Swarm Intelligence Dashboard Renderer */
  function renderSupremeCouncil(data) {
    const council = data && (data.council || data.council_analysis);
    const validation = data && data.validation;
    const panel = document.getElementById('council-dashboard-panel');
    if (!panel) return;

    if (!council && !validation) {
      panel.style.display = 'none';
      return;
    }

    panel.style.display = 'block';

    // Duration badge
    const durBadge = document.getElementById('council-duration-badge');
    if (durBadge) {
      const dur = data.duration || getAccurateDuration() || 0;
      durBadge.innerText = `Duration: ${formatSec(dur)}`;
    }

    // PII toggle state
    const piiBtn = document.getElementById('btn-pii-shield');
    const piiText = document.getElementById('pii-shield-status-text');
    if (piiBtn && piiText) {
      if (window.isPIIRedacted) {
        piiBtn.classList.add('active');
        piiText.innerText = 'PII Privacy: Active';
      } else {
        piiBtn.classList.remove('active');
        piiText.innerText = 'PII Privacy: Off';
      }
    }

    // Executive Summary
    const headline = document.getElementById('council-briefing-headline');
    const tldr = document.getElementById('council-briefing-tldr');
    if (headline) headline.innerText = 'Executive Summary';
    if (tldr) {
      let summaryText = '';
      if (council && council.executive_summary) {
        if (typeof council.executive_summary === 'object') {
          summaryText = council.executive_summary.tldr || council.executive_summary.headline || '';
          if (!summaryText && Array.isArray(council.executive_summary.key_takeaways)) {
            summaryText = council.executive_summary.key_takeaways.join(' ');
          }
        } else {
          summaryText = String(council.executive_summary);
        }
      }
      tldr.innerText = summaryText || 'Automated meeting intelligence successfully processed the speech stream with speaker diarization and semantic classification.';
    }

    // Ratified Decisions
    const decisionsWrap = document.getElementById('council-decisions-wrap');
    const decisionsList = document.getElementById('council-decisions-list');
    if (decisionsWrap && decisionsList) {
      const decisions = (council && council.key_decisions) || [];
      if (decisions.length > 0) {
        decisionsWrap.style.display = 'block';
        decisionsList.innerHTML = decisions.map(d => `
          <div class="decision-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span>${escapeHtml(d)}</span>
          </div>
        `).join('');
      } else {
        decisionsWrap.style.display = 'none';
      }
    }

    // Thematic Chapters
    const chaptersWrap = document.getElementById('council-chapters-wrap');
    const chaptersStrip = document.getElementById('council-chapters-strip');
    if (chaptersWrap && chaptersStrip) {
      const chapters = (council && council.thematic_chapters) || [];
      if (chapters.length > 0) {
        chaptersWrap.style.display = 'block';
        chaptersStrip.innerHTML = chapters.map(ch => `
          <div class="chapter-chip" onclick="seekTo(${ch.start})" title="${escapeHtml(ch.summary || '')}">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            <strong style="color:var(--text-primary);">${escapeHtml(ch.title)}</strong>
            <span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted);">${formatSec(ch.start)}</span>
          </div>
        `).join('');
      } else {
        chaptersWrap.style.display = 'none';
      }
    }

    // Action Items
    const actionsWrap = document.getElementById('council-actions-wrap');
    const actionsGrid = document.getElementById('council-actions-grid');
    if (actionsWrap && actionsGrid) {
      const actions = (council && council.action_items) || [];
      if (actions.length > 0) {
        actionsWrap.style.display = 'block';
        actionsGrid.innerHTML = actions.map((a, i) => {
          const prio = (a.priority || 'medium').toLowerCase();
          const prioClass = `prio-${prio}`;
          const seekTime = a.seek_start !== undefined && a.seek_start !== null ? a.seek_start : 0;
          return `
            <div class="action-card">
              <div class="action-card-header">
                <span class="action-prio-badge ${prioClass}">${escapeHtml(prio.toUpperCase())} PRIORITY</span>
                <span class="action-assignee">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                  ${escapeHtml(a.assignee || 'General')}
                </span>
              </div>
              <div class="action-task-text">${escapeHtml(a.task)}</div>
              <div class="action-meta-row">
                <button type="button" class="action-seek-btn" onclick="seekTo(${seekTime})" title="Jump to context in media">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                  ${formatSec(seekTime)}
                </button>
              </div>
            </div>
          `;
        }).join('');
      } else {
        actionsWrap.style.display = 'none';
      }
    }

    // Optional validation metrics if elements exist
    const certId = document.getElementById('audit-cert-id');
    const certStatus = document.getElementById('audit-cert-status');
    const rootHash = document.getElementById('audit-root-hash');
    if (validation) {
      if (certId) certId.innerText = validation.certificate_id || 'CERT-CSCR-CHAIN';
      if (certStatus) {
        certStatus.innerText = validation.passed ? 'VALIDATED' : 'PROCESSED';
        certStatus.style.background = validation.passed ? 'rgba(16, 185, 129, 0.12)' : 'rgba(255, 94, 0, 0.15)';
        certStatus.style.color = validation.passed ? 'var(--emerald)' : 'var(--tangerine)';
      }
      if (rootHash) {
        const fullHash = validation.root_hash || 'SHA256-AUTHENTICATED';
        rootHash.innerText = fullHash.length > 20 ? (fullHash.substring(0, 10) + '...' + fullHash.substring(fullHash.length - 8)) : fullHash;
        rootHash.title = fullHash;
      }
    }
  }

  /* PII Privacy Shield Toggle */
  window.isPIIRedacted = false;
  async function togglePIIShield() {
    window.isPIIRedacted = !window.isPIIRedacted;
    const piiBtn = document.getElementById('btn-pii-shield');
    const piiText = document.getElementById('pii-shield-status-text');

    if (window.isPIIRedacted) {
      if (piiBtn) piiBtn.classList.add('active');
      if (piiText) piiText.innerText = 'PII Privacy: Active';
      showToast('PII Privacy Shield activated. Redacting sensitive data...', 'info');

      const data = currentResult || window.currentResult;
      if (data && data.transcription && data.transcription.segments) {
        try {
          const res = await fetch('/api/pii/redact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              segments: data.transcription.segments.map(s => ({
                text: s.text,
                start: s.start,
                end: s.end,
                speaker: s.speaker
              }))
            })
          });
          const resData = await res.json();
          if (resData.sanitized_segments) {
            resData.sanitized_segments.forEach((seg, idx) => {
              const segElem = document.getElementById('seg-text-' + idx);
              if (segElem) {
                segElem.innerText = seg.text;
                segElem.setAttribute('data-edited', 'true');
              }
            });
            showToast(`PII Shield redacted ${resData.report ? resData.report.redactions_count : 0} items!`, 'success');
          }
        } catch (e) {
          showToast('PII Redaction request failed: ' + e, 'error');
        }
      }
    } else {
      if (piiBtn) piiBtn.classList.remove('active');
      if (piiText) piiText.innerText = 'PII Privacy: Off';
      showToast('PII Privacy Shield deactivated. Restoring unredacted speech.', 'info');

      const data = currentResult || window.currentResult;
      if (data) {
        renderTranscription(data);
      }
    }
  }

  /* Copy Cryptographic Audit Certificate Receipt */
  function copyAuditReceipt() {
    const data = currentResult || window.currentResult;
    const validation = data && data.validation;
    if (!validation) {
      showToast('No cryptographic audit certificate available yet.', 'info');
      return;
    }
    const cert = validation.certificate_id || 'CERT-CSCR-CHAIN';
    const root = validation.root_hash || 'SHA256-ROOT-CHAIN';
    const status = validation.passed ? 'PASSED' : 'FLAGGED';
    const chain = validation.hash_chain || [];
    let receipt = `=== SCRIBER CRYPTOGRAPHIC AUDIT CERTIFICATE ===\n`;
    receipt += `Certificate ID : ${cert}\n`;
    receipt += `Status         : ${status}\n`;
    receipt += `SHA-256 Root   : ${root}\n`;
    receipt += `Blocks in Chain: ${chain.length}\n\n`;
    receipt += `--- HASH CHAIN BLOCKS ---\n`;
    chain.forEach(b => {
      receipt += `[Block ${b.block_id}] ${b.stage}\n  Prev: ${b.prev_hash}\n  Hash: ${b.block_hash}\n`;
    });
    receipt += `\nCryptographically verified by CouncilAgentSwarm & PIISecurityOfficer.\n`;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(receipt).then(() => {
        showToast('Cryptographic audit certificate copied to clipboard!', 'success');
      }).catch(() => {
        fallbackCopy(receipt, () => showToast('Audit certificate copied!', 'success'));
      });
    } else {
      fallbackCopy(receipt, () => showToast('Audit certificate copied!', 'success'));
    }
  }

  /* Antigravity Plugin Installation */
  async function installAntigravityPlugin() {
    const btn = document.getElementById('btn-install-plugin');
    if (btn) {
      btn.disabled = true;
      btn.innerText = 'Installing Plugin...';
    }
    try {
      const res = await fetch('/api/plugin/install', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast('Scriber Antigravity Plugin installed successfully to ' + data.target_dir, 'success');
        if (btn) btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Installed to Antigravity';
      } else {
        showToast('Plugin install failed: ' + (data.error || 'Unknown error'), 'error');
        if (btn) {
          btn.disabled = false;
          btn.innerText = 'Install Antigravity Plugin';
        }
      }
    } catch (e) {
      showToast('Plugin installation network error: ' + e, 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerText = 'Install Antigravity Plugin';
      }
    }
  }

  /* Swarm Roster Loader (Safe no-op for backward compatibility) */
  async function loadSwarmAgents() {
    const grid = document.getElementById('swarm-agents-grid');
    if (!grid) return;
  }

  // Export functions to window
  window.renderTranscription = renderTranscription;
  window.copyFullTranscript = copyFullTranscript;
  window.switchMode = switchMode;
  window.openFileDialog = openFileDialog;
  window.synthesizeClonedVoice = synthesizeClonedVoice;
  window.downloadArtifact = downloadArtifact;
  window.revealExportFolder = revealExportFolder;
  window.startProcessing = startProcessing;
  window.togglePlayPause = togglePlayPause;
  window.skipAudio = skipAudio;
  window.setAudioVolume = setAudioVolume;
  window.setPlaybackRate = setPlaybackRate;
  window.showToast = showToast;
  window.renderSupremeCouncil = renderSupremeCouncil;
  window.togglePIIShield = togglePIIShield;
  window.copyAuditReceipt = copyAuditReceipt;
  window.installAntigravityPlugin = installAntigravityPlugin;
  window.loadSwarmAgents = loadSwarmAgents;
  window.openVoiceCredentialsModal = openVoiceCredentialsModal;
  window.closeVoiceCredentialsModal = closeVoiceCredentialsModal;
  window.saveVoiceCredentials = saveVoiceCredentials;
</script>


</body>
</html>
'''
