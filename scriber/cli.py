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
import ctypes
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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

    # Command: shortcut
    shortcut_parser = subparsers.add_parser("shortcut", help="Create and manage Windows desktop and Start Menu shortcuts")
    shortcut_parser.add_argument("--install", action="store_true", help="Install or update desktop and Start Menu shortcuts")
    shortcut_parser.add_argument("--desktop-only", action="store_true", help="Install shortcut to Desktop only")
    shortcut_parser.add_argument("--target", default=None, help="Explicit target executable path")
    shortcut_parser.add_argument("--icon", default=None, help="Explicit icon path")

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
    elif args.command == "shortcut":
        run_shortcut(args)
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
    print(f"  Architecture: Scriber Local Intelligence Core")
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


def get_default_shortcut_destinations(desktop_only: bool = False) -> List[Path]:
    """Resolves standard Windows shortcut target destinations."""
    desktop = Path(os.path.expanduser("~/Desktop"))
    destinations = [desktop / "Scriber.lnk"]
    if not desktop_only:
        appdata = os.environ.get("APPDATA")
        if appdata:
            programs_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            destinations.append(programs_dir / "Scriber.lnk")
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            onedrive_desktop = Path(userprofile) / "OneDrive" / "Desktop"
            if onedrive_desktop.is_dir():
                destinations.append(onedrive_desktop / "Scriber.lnk")
    return destinations


def create_windows_shortcut(
    dest_path: Union[str, Path],
    target_path: Union[str, Path],
    working_dir: Union[str, Path],
    icon_path: Union[str, Path],
    description: str = "Scriber - Studio Intelligence and Voice Synthesis",
    arguments: str = "",
) -> Path:
    """Creates a Windows .lnk shortcut using Windows Script Host with icon binding."""
    dest = Path(dest_path).resolve()
    target = Path(target_path).resolve()
    workdir = Path(working_dir).resolve()
    icon = Path(icon_path).resolve()

    # Ensure parent destination directory exists
    parent_dir = dest.parent
    if not parent_dir.exists():
        os.makedirs(parent_dir, exist_ok=True)

    # Remove existing shortcut to prevent stale PropertyStore
    if dest.exists():
        try:
            dest.unlink()
        except Exception:
            pass

    dest_str = str(dest)
    target_str = str(target)
    workdir_str = str(workdir)
    icon_str = str(icon)
    args_str = str(arguments)

    vbs_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{dest_str}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_str}"
oLink.Arguments = "{args_str}"
oLink.WorkingDirectory = "{workdir_str}"
oLink.Description = "{description}"
oLink.IconLocation = "{icon_str},0"
oLink.WindowStyle = 1
oLink.Save
'''
    with tempfile.NamedTemporaryFile("w", suffix=".vbs", delete=False) as f:
        f.write(vbs_content)
        tmp_vbs = f.name

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform == "win32" else 0
    si = None
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0

    try:
        try:
            subprocess.run(["wscript", "//nologo", tmp_vbs], check=True, shell=False, creationflags=flags, startupinfo=si)
        except Exception:
            subprocess.run(["cscript", "//nologo", tmp_vbs], check=True, shell=False, creationflags=flags, startupinfo=si)
    finally:
        if os.path.exists(tmp_vbs):
            try:
                os.remove(tmp_vbs)
            except Exception:
                pass

    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)
        except Exception:
            pass

    return dest


def install_shortcuts(
    target_exe: Optional[Union[str, Path]] = None,
    icon_path: Optional[Union[str, Path]] = None,
    desktop_only: bool = False,
) -> List[Path]:
    """Installs or updates Scriber desktop and Start Menu shortcuts across Windows."""
    repo_root = Path(__file__).resolve().parent.parent

    target_args = ""
    # Resolve executable target
    if target_exe:
        resolved_exe = Path(target_exe).resolve()
    else:
        candidate_bundle = repo_root / "dist" / "Scriber" / "Scriber.exe"
        candidate_onefile = repo_root / "dist" / "Scriber.exe"
        pythonw_candidate = repo_root / ".venv" / "Scripts" / "pythonw.exe"
        if candidate_bundle.exists():
            resolved_exe = candidate_bundle.resolve()
        elif candidate_onefile.exists():
            resolved_exe = candidate_onefile.resolve()
        elif pythonw_candidate.exists():
            resolved_exe = pythonw_candidate.resolve()
            target_args = f'"{repo_root / "run_desktop.py"}"'
        else:
            resolved_exe = candidate_bundle.resolve()

    working_dir = resolved_exe.parent if resolved_exe.exists() else repo_root

    # Resolve icon
    if icon_path:
        resolved_icon = Path(icon_path).resolve()
    else:
        from scriber.assets import get_icon_path
        resolved_icon = Path(get_icon_path()).resolve()

    destinations = get_default_shortcut_destinations(desktop_only=desktop_only)
    created: List[Path] = []
    for dest in destinations:
        try:
            res = create_windows_shortcut(
                dest_path=dest,
                target_path=resolved_exe,
                working_dir=working_dir,
                icon_path=resolved_icon,
                arguments=target_args,
            )
            created.append(res)
            print(f"[+] Installed shortcut: {res} -> {resolved_exe}")
        except Exception as e:
            print(f"[-] Warning: Failed creating shortcut at {dest}: {e}", file=sys.stderr)

    return created


def create_desktop_shortcut(
    target_exe: Optional[Union[str, Path]] = None,
    icon_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Convenience helper to create or refresh the primary Desktop shortcut."""
    shortcuts = install_shortcuts(target_exe=target_exe, icon_path=icon_path, desktop_only=True)
    if shortcuts:
        return shortcuts[0]
    return Path(os.path.expanduser("~/Desktop")) / "Scriber.lnk"


def run_shortcut(args):
    desktop_only = getattr(args, "desktop_only", False)
    target = getattr(args, "target", None)
    icon = getattr(args, "icon", None)
    installed = install_shortcuts(target_exe=target, icon_path=icon, desktop_only=desktop_only)
    if not installed:
        print("[-] No shortcuts were created.")


if __name__ == "__main__":
    main()

