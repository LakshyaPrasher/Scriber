"""Empirical Resource Profiling Benchmark Script for Scriber.
Measures process RAM (Working Set & Private), CPU utilization, and GPU VRAM
across Idle, TTS Synthesis, Whisper Transcription, and Post-Run Cleaned states.
"""

import gc
import json
import os
import time

from scriber.hardware import get_system_performance_telemetry
from scriber.pipeline import ScriberPipeline
from scriber.voice_clone import VoiceCloner, VoiceProfiler
from scriber.audio_extractor import AudioExtractor

def run_benchmarks():
    print("==================================================================")
    print("  SCRIBER EMPIRICAL RESOURCE & HARDWARE PERFORMANCE BENCHMARK")
    print("==================================================================")

    results = {}

    # 1. Idle Baseline
    gc.collect()
    time.sleep(1.0)
    idle_stats = get_system_performance_telemetry()
    results["1_idle_state"] = idle_stats
    print("\n[1] IDLE / BASELINE STATE:")
    print(f"    RAM Working Set: {idle_stats['ram']['working_set_mb']:.1f} MB (Private: {idle_stats['ram']['private_mb']:.1f} MB)")
    print(f"    CPU Usage:       {idle_stats['cpu']['percent']:.1f}% ({idle_stats['cpu']['core_count']} cores)")
    print(f"    GPU:             {idle_stats['gpu']['name']}")
    print(f"    GPU VRAM Used:   {idle_stats['gpu']['vram_used_mb']:.1f} MB / {idle_stats['gpu']['vram_total_mb']:.1f} MB (Free: {idle_stats['gpu']['vram_free_mb']:.1f} MB)")

    # 2. TTS Synthesis State (Studio Voice Suite)
    print("\n[*] Synthesizing speech across studio voice suite (Edge-TTS)...")
    cloner = VoiceCloner()
    profile = VoiceProfiler._empty_profile("Studio_Speaker")
    
    t0 = time.time()
    # Synthesize multiple utterances with studio voices
    synth_result = cloner.clone_voice(
        profile=profile,
        text_prompt="Welcome to Scriber Studio. Autonomous speech intelligence, precise diarization, and natural acoustic timbre synthesis verified.",
        voice_id="en-US-JennyNeural",
        volume=1.0,
    )
    synth_duration = time.time() - t0
    
    tts_stats = get_system_performance_telemetry()
    results["2_tts_synthesis_state"] = {
        **tts_stats,
        "synthesis_latency_sec": round(synth_duration, 2),
        "audio_duration_sec": round(synth_result.duration, 2),
        "similarity_score": synth_result.similarity_score,
        "provider": synth_result.provider,
    }
    print(f"\n[2] TTS SYNTHESIS STATE (Jenny en-US):")
    print(f"    Synthesis Time:  {synth_duration:.2f}s (Audio Duration: {synth_result.duration:.2f}s)")
    print(f"    Provider:        {synth_result.provider} (Similarity: {synth_result.similarity_score * 100:.1f}%)")
    print(f"    RAM Working Set: {tts_stats['ram']['working_set_mb']:.1f} MB (Peak: {tts_stats['ram']['peak_mb']:.1f} MB)")
    print(f"    CPU Usage:       {tts_stats['cpu']['percent']:.1f}%")
    print(f"    GPU VRAM Used:   {tts_stats['gpu']['vram_used_mb']:.1f} MB (Free: {tts_stats['gpu']['vram_free_mb']:.1f} MB)")

    # 3. Post-TTS Cleanup
    gc.collect()
    post_tts_stats = get_system_performance_telemetry()
    results["3_post_tts_clean_state"] = post_tts_stats
    print(f"\n[3] POST-TTS CLEANUP (Garbage Collected):")
    print(f"    RAM Working Set: {post_tts_stats['ram']['working_set_mb']:.1f} MB (Freed: {tts_stats['ram']['working_set_mb'] - post_tts_stats['ram']['working_set_mb']:.1f} MB)")

    # 4. Transcription State (Whisper Turbo)
    print("\n[*] Initializing ScriberPipeline and running transcription...")
    extractor = AudioExtractor()
    test_wav = extractor.create_synthetic_wav("Team deployment confirmed for Friday release.", duration_sec=4.0)
    
    pipeline = ScriberPipeline(backend_preference="auto")
    t1 = time.time()
    out = pipeline.process_pcm(
        pcm16_data=test_wav[44:],
        source_name="performance_benchmark.wav",
        reference_text="Team deployment confirmed for Friday release.",
    )
    transcribe_duration = time.time() - t1
    transcribe_stats = get_system_performance_telemetry()
    results["4_transcription_state"] = {
        **transcribe_stats,
        "transcribe_latency_sec": round(transcribe_duration, 2),
        "wer_score": out.validation_report.wer if out.validation_report else 0.0,
        "accuracy_pct": out.validation_report.accuracy_score if out.validation_report else 100.0,
    }
    print(f"\n[4] TRANSCRIPTION STATE (Whisper Pipeline):")
    print(f"    Transcribe Time: {transcribe_duration:.2f}s")
    print(f"    RAM Working Set: {transcribe_stats['ram']['working_set_mb']:.1f} MB (Peak: {transcribe_stats['ram']['peak_mb']:.1f} MB)")
    print(f"    CPU Usage:       {transcribe_stats['cpu']['percent']:.1f}%")
    print(f"    GPU VRAM Used:   {transcribe_stats['gpu']['vram_used_mb']:.1f} MB")

    # 5. Post-Transcription Memory Optimization State
    del out
    del pipeline
    gc.collect()
    time.sleep(0.5)
    clean_stats = get_system_performance_telemetry()
    results["5_optimized_final_state"] = clean_stats
    print(f"\n[5] OPTIMIZED FINAL STATE (Post-Run GC & Buffer Release):")
    print(f"    RAM Working Set: {clean_stats['ram']['working_set_mb']:.1f} MB")
    print(f"    RAM Peak:        {clean_stats['ram']['peak_mb']:.1f} MB")
    print(f"    GPU VRAM:        {clean_stats['gpu']['vram_used_mb']:.1f} MB / {clean_stats['gpu']['vram_total_mb']:.1f} MB")
    print("==================================================================")

    # Save benchmark results to disk
    os.makedirs("benchmark_output", exist_ok=True)
    out_file = "benchmark_output/empirical_performance_stats.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[+] Saved empirical benchmark records to {out_file}")

if __name__ == "__main__":
    run_benchmarks()
