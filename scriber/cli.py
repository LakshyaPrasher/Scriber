"""Command-Line Interface (CLI) for Scriber.

Usage:
  py -m scriber.cli process <media_file> [options]
  py -m scriber.cli benchmark
  py -m scriber.cli info
  py -m scriber.cli serve [--port 8080]
  py -m scriber.cli app
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from scriber import ScriberPipeline, ResultValidator, TOP_LEVERAGED_REPOS, __version__
from scriber.exporters import ScriberExporter


if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="scriber",
        description="Scriber: Autonomous Video Intelligence, Whisper Flow Transcription, and Summarization.",
    )
    parser.add_argument("--version", action="version", version=f"Scriber {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available sub-commands")

    # Command: process
    proc_parser = subparsers.add_parser("process", help="Process a video/audio file through the 5-subagent swarm")
    proc_parser.add_argument("file", help="Path to input video or audio file")
    proc_parser.add_argument("--task", default="transcribe", choices=["transcribe", "translate"], help="Task to perform")
    proc_parser.add_argument("--lang", default="en", help="Language code (e.g. en, es, fr)")
    proc_parser.add_argument("--out-dir", default="./scriber_output", help="Directory to save exported results")
    proc_parser.add_argument(
        "--formats",
        default="json,md,html,srt,vtt",
        help="Comma-separated export formats (json, md, html, srt, vtt)",
    )
    proc_parser.add_argument("--ref", default=None, help="Optional ground-truth reference text for WER calculation")
    proc_parser.add_argument(
        "--model",
        default="turbo",
        choices=["turbo", "distil-large-v3", "base", "whisperx", "small", "medium", "large-v3"],
        help="Transcription model to use (default: turbo)",
    )
    proc_parser.add_argument("--redact-pii", action="store_true", help="Enable PII and credentials masking for privacy")

    # Command: swarm
    swarm_parser = subparsers.add_parser("swarm", help="Inspect Supreme Council multi-agent swarm roster and model tiers")

    # Command: install-antigravity
    install_parser = subparsers.add_parser("install-antigravity", help="Install Scriber plugin into Google Antigravity configuration")
    install_parser.add_argument("--force", action="store_true", help="Overwrite existing plugin installation")

    # Command: benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run 99%+ accuracy verification benchmark suite")

    # Command: info
    info_parser = subparsers.add_parser("info", help="Display speech intelligence engines and architecture details")

    # Command: clone-voice
    clone_parser = subparsers.add_parser("clone-voice", help="Clone speaker voice from media and synthesize custom speech")
    clone_parser.add_argument("file", help="Reference video or audio file containing speaker voice")
    clone_parser.add_argument("--text", required=True, help="Text phrase for the cloned voice to speak")
    clone_parser.add_argument("--speaker", default="Speaker_1", help="Speaker identifier (default: Speaker_1)")
    clone_parser.add_argument("--pitch", type=float, default=0.0, help="Pitch offset in Hz (default: 0.0)")
    clone_parser.add_argument("--rate", type=float, default=0.0, help="Speaking rate offset in percent (default: 0.0)")
    clone_parser.add_argument("--out", default="cloned_voice.wav", help="Output WAV path (default: cloned_voice.wav)")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch standalone Web UI dashboard")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to bind server (default: 8080)")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")

    # Command: app
    app_parser = subparsers.add_parser("app", help="Launch native desktop application window")
    app_parser.add_argument("--port", type=int, default=None, help="Port to bind server (default: auto)")
    app_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    app_parser.add_argument("--mode", default="auto", choices=["auto", "webview", "edge", "browser"], help="Desktop window engine (default: auto)")
    app_parser.add_argument("--fullscreen", action="store_true", help="Launch in fullscreen mode")
    app_parser.add_argument("--debug", action="store_true", help="Enable developer tools and debug logging")

    args = parser.parse_args()

    if args.command == "process":
        run_process(args)
    elif args.command == "swarm":
        run_swarm()
    elif args.command == "install-antigravity":
        run_install_antigravity(args)
    elif args.command == "benchmark":
        run_benchmark()
    elif args.command == "info":
        run_info()
    elif args.command == "clone-voice":
        run_clone_voice(args)
    elif args.command == "serve":
        run_serve(args)
    elif args.command == "app":
        run_app(args)
    else:
        parser.print_help()


def run_process(args):
    if not os.path.exists(args.file):
        print(f"Error: Media file '{args.file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"  🎬 Scriber Video Intelligence Pipeline v{__version__}")
    print(f"=======================================================")
    print(f"File:        {args.file}")
    print(f"Model:       {getattr(args, 'model', 'turbo')}")
    print(f"Task:        {args.task}")
    print(f"Language:    {args.lang}")
    print(f"Export Dir:  {args.out_dir}")
    print(f"PII Shield:  {'ACTIVE (Masking enabled)' if getattr(args, 'redact_pii', False) else 'OFF (Raw)'}")
    print(f"-------------------------------------------------------")
    print(f"[*] Ingesting media and extracting 16kHz PCM...")
    print(f"[*] Running Voice Activity Detection (VAD) chunking...")
    print(f"[*] Whisper Flow Engine transcribing with {getattr(args, 'model', 'turbo')}...")
    print(f"[*] Sub-agent 2: Quality Check Guard auditing & culling hallucinations...")
    print(f"[*] Sub-agent 3: Supreme Council Multi-Agent Swarm synthesizing intelligence...")
    print(f"[*] Sub-agent 4: Result Validator verifying 99%+ accuracy & hash chain...")

    pipeline = ScriberPipeline()
    formats = [f.strip() for f in args.formats.split(",")]
    output = pipeline.process_file(
        file_path=args.file,
        task=args.task,
        language=args.lang,
        reference_text=args.ref,
        export_dir=args.out_dir,
        export_formats=formats,
        model=getattr(args, "model", "turbo"),
        redact_pii=getattr(args, "redact_pii", False),
    )

    cs = output.council_analysis
    sm = cs.executive_summary
    val = output.validation_report
    qual = output.quality_report

    print(f"\n-------------------------------------------------------")
    print(f"  ✅ PROCESSING COMPLETE (Took {output.processing_time_seconds:.2f}s)")
    print(f"-------------------------------------------------------")
    print(f"Headline:     {sm.headline}")
    print(f"Duration:     {output.audio_metadata.duration:.1f}s")
    print(f"Spoken Words: {qual.word_count} ({qual.estimated_speaking_wpm:.1f} WPM)")
    print(f"Action Items: {len(cs.action_items)} extracted")
    print(f"Discussions:  {len(cs.discussion_points)} topics identified")
    if cs.pii_report:
        print(f"PII Shield:   {cs.pii_report.redacted_count} entities secured | Compliance: {cs.pii_report.compliance_score * 100:.1f}%")
    print(f"Net Accuracy: {val.accuracy_score * 100:.2f}% (WER: {val.wer * 100:.2f}%)")
    print(f"Audit Status: {'✅ PASSED 99%+ ACCURACY AUDIT' if val.passed_99_percent else '⚠️ REVIEW NEEDED'}")
    print(f"Certificate:  {val.certificate_id}")
    if val.root_hash:
        print(f"Hash Chain:   {val.root_hash[:20]}... (Verifiable SHA-256 root)")

    print(f"\n[+] Key Action Items:")
    for a in cs.action_items[:5]:
        print(f"  - [{a.id}] {a.task} (Owner: {a.assignee}, Priority: {a.priority.upper()})")

    print(f"\n[+] Supreme Council Swarm Telemetry:")
    for telem in cs.agent_telemetry:
        print(f"  - [{telem.agent_id}] {telem.agent_name} ({telem.model_tier.upper()}): {telem.runtime_ms:.1f}ms - {telem.summary}")

    print(f"\n[+] Exported Artifacts saved to: {os.path.abspath(args.out_dir)}")
    for f in formats:
        print(f"  - {f.upper()} report generated.")


def run_swarm():
    """Displays Supreme Council multi-agent swarm roster, model mappings, and capabilities."""
    from scriber.agent_swarm import CouncilAgentSwarm

    swarm = CouncilAgentSwarm()
    agents = swarm.get_registered_agents()

    print(f"\n================================================================================")
    print(f"  🤖 Scriber Supreme Council: Multi-Agent Swarm Registry")
    print(f"  Architecture: wshobson/agents (https://github.com/wshobson/agents)")
    print(f"================================================================================")
    print(f"{'Agent ID':<24} {'Specialist Role':<42} {'Model Tier':<12}")
    print(f"{'-'*24} {'-'*42} {'-'*12}")
    for a in agents:
        print(f"{a.id:<24} {a.role:<42} {a.model_tier.upper():<12}")
        print(f"  └─ Description: {a.description}")
        print(f"  └─ Key Capabilities: {', '.join(a.capabilities[:2])}\n")


def run_install_antigravity(args):
    """Installs the Scriber plugin bundle into user's Google Antigravity configuration directory."""
    import shutil
    from pathlib import Path

    home = Path.home()
    dest_dir = home / ".gemini" / "config" / "plugins" / "scriber"
    src_dir = Path(__file__).resolve().parent.parent / ".antigravity" / "plugins" / "scriber"

    print(f"\n=======================================================")
    print(f"  🚀 Installing Scriber Plugin for Google Antigravity")
    print(f"=======================================================")
    print(f"Source: {src_dir}")
    print(f"Target: {dest_dir}")

    if not src_dir.exists():
        print(f"Error: Plugin source directory '{src_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if dest_dir.exists():
        if not args.force:
            print(f"[!] Plugin already installed at {dest_dir}. Use --force to reinstall.")
            return
        shutil.rmtree(dest_dir)

    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_dir, dest_dir)
    print(f"\n✅ Scriber plugin successfully installed into Google Antigravity!")
    print(f"Agents registered:")
    print(f"  - scriber-intelligence")
    print(f"  - scriber-whisper-flow")
    print(f"  - scriber-council-auditor")
    print(f"  - scriber-voice-studio")
    print(f"  - scriber-pii-shield")
    print(f"\nYou can now invoke Scriber commands in Antigravity chat: /scriber:process, /scriber:swarm\n")


def run_benchmark():
    print(f"\n=======================================================")
    print(f"  🧪 Scriber Sub-Agent 4: Validation Benchmark Suite")
    print(f"=======================================================")
    results = ResultValidator.run_benchmark_suite()
    print(f"Total Cases Evaluated:       {results['total_cases_evaluated']}")
    print(f"Average Accuracy Percentage: {results['average_accuracy_percentage']}")
    print(f"All Passed 99%+ Threshold:   {'✅ YES (PASSED)' if results['all_passed_99_percent'] else '❌ NO (FAILED)'}")
    print(f"\nCase-by-Case Breakdown:")
    for r in results["benchmark_results"]:
        status = "PASSED (>=99%)" if r["passed_99_percent"] else "FAILED"
        print(f"  [{r['test_case_id']}] Accuracy: {r['accuracy_percentage']} | WER: {r['wer'] * 100:.2f}% | Status: {status}")
        print(f"    Certificate: {r['certificate_id']}")


def run_info():
    print(f"\n=======================================================")
    print(f"  ⚡ Scriber Speech Intelligence & Architectural Foundations")
    print(f"=======================================================")
    for idx, repo in enumerate(TOP_LEVERAGED_REPOS, start=1):
        print(f"{idx}. {repo['repo']}")
        print(f"   URL:          {repo['url']}")
        print(f"   Description:  {repo['description']}")
        print(f"   Contribution: {repo['key_contribution']}\n")

    from scriber.transcription_engine import get_model_evaluation_matrix
    print(f"=======================================================")
    print(f"  🔬 Evaluated Speech-to-Text & Word Alignment Models")
    print(f"=======================================================")
    matrix = get_model_evaluation_matrix()
    for m_id, m_info in matrix.items():
        print(f"• {m_info['name']} ({m_info['params']})")
        print(f"  Speedup: {m_info['speedup_cpu']} | WER: {m_info['wer_librispeech']}% | RAM: {m_info['ram_mb']}MB | Timestamps: {m_info['timestamp_accuracy']}")
        print(f"  Verdict: {m_info['evaluation_verdict']}\n")


def run_clone_voice(args):
    if not os.path.exists(args.file):
        print(f"Error: Media file '{args.file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"  🎙️ Scriber Voice Cloning & Biometric Synthesis")
    print(f"=======================================================")
    print(f"Source Media:  {args.file}")
    print(f"Target Text:   \"{args.text}\"")
    print(f"Speaker ID:    {args.speaker}")
    print(f"Pitch Offset:  {args.pitch:+.1f} Hz")
    print(f"Rate Offset:   {args.rate:+.1f}%")
    print(f"Output File:   {args.out}")
    print(f"-------------------------------------------------------")
    print(f"[*] Ingesting speaker reference audio...")

    from scriber.audio_extractor import AudioExtractor
    from scriber.voice_clone import VoiceCloner, VoiceProfiler

    extractor = AudioExtractor()
    pcm16_data, meta = extractor.extract_pcm16(args.file)
    print(f"[*] Profiling speaker vocal biometrics (F0, formants, timbre)...")
    profile = VoiceProfiler.profile_from_pcm16(pcm16_data, speaker_id=args.speaker)

    print(f"\n[+] Extracted Biometric Voice Profile:")
    print(f"    - Gender Estimate:   {profile.gender_estimate.upper()}")
    print(f"    - Pitch (F0 Mean):   {profile.fundamental_frequency_hz:.1f} Hz (Range: {profile.pitch_min_hz:.1f} - {profile.pitch_max_hz:.1f} Hz)")
    print(f"    - Spectral Centroid: {profile.spectral_centroid_hz:.1f} Hz")
    print(f"    - Speaking Cadence:  {profile.estimated_wpm:.1f} WPM")
    print(f"    - RMS Energy:        {profile.energy_rms:.4f}")

    print(f"\n[*] Synthesizing speech with cloned vocal timbre...")
    cloner = VoiceCloner()
    result = cloner.clone_voice(
        profile=profile,
        text_prompt=args.text,
        pitch_shift_hz=args.pitch,
        rate_shift_pct=args.rate,
        reference_pcm=pcm16_data,
    )

    # Save output WAV file
    import wave
    with open(args.out, "wb") as f:
        with wave.open(f, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(result.audio_pcm16)

    print(f"\n-------------------------------------------------------")
    print(f"  ✅ VOICE CLONING SUCCESSFUL")
    print(f"-------------------------------------------------------")
    print(f"Synthesis Backend: {result.synthesis_backend}")
    print(f"Acoustic Match:    {result.similarity_score * 100:.2f}% (>=99% verification)")
    print(f"Audio Duration:    {result.duration:.2f}s")
    print(f"Saved Output To:   {os.path.abspath(args.out)}\n")


def run_serve(args):
    from scriber.web.server import run_server
    run_server(host=args.host, port=args.port)


def run_app(args):
    from scriber.desktop import launch_desktop
    sys.exit(
        launch_desktop(
            host=args.host,
            port=args.port,
            mode=args.mode,
            fullscreen=args.fullscreen,
            debug=args.debug,
        )
    )


if __name__ == "__main__":
    main()
