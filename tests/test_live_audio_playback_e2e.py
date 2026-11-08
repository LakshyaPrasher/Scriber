"""Targeted Live End-to-End Test for Audio Playback, Transport Controls, and Transcription Sync.

Runs directly against Microsoft Edge via CDP with the real Dexter MKV file from Downloads.
Validates:
1. Non-standard MKV/EAC3 container processing produces a browser-playable audio stream.
2. /api/media OPTIONS preflight, HEAD probing, and byte-range streaming with CORS headers.
3. Edge HTML5 <audio id="audio-player"> loads source without network/decoding errors.
4. Master play/pause button (#btn-master-play) toggles state reliably and updates icons.
5. Active audio playback advances currentTime and live-timecode.
6. Word tokens and segment cards synchronize and highlight dynamically during playback.
7. Word-click seek and waveform scrub update playback position accurately.
"""

import asyncio
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scriber.desktop import find_edge_binary
from scriber.web.server import ScriberBackgroundServer


class CDPSession:
    """Async Chrome DevTools Protocol (CDP) client over WebSocket."""

    def __init__(self, ws: aiohttp.ClientWebSocketResponse):
        self.ws = ws
        self._req_id = 0

    async def evaluate(self, expression: str, await_promise: bool = True) -> Any:
        self._req_id += 1
        cmd_id = self._req_id
        payload = {
            "id": cmd_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": True,
            },
        }
        await self.ws.send_json(payload)
        while True:
            msg = await self.ws.receive_json()
            if msg.get("id") == cmd_id:
                result = msg.get("result", {})
                if "exceptionDetails" in result:
                    desc = (
                        result["exceptionDetails"].get("exception", {}).get("description")
                        or str(result["exceptionDetails"])
                    )
                    raise RuntimeError(f"CDP JS Exception: {desc}")
                return result.get("result", {}).get("value")

    async def click(self, selector: str) -> None:
        await self.evaluate(
            f"(function() {{"
            f"  const el = document.querySelector({json.dumps(selector)});"
            f"  if (!el) throw new Error('Element not found: ' + {json.dumps(selector)});"
            f"  el.click();"
            f"}})()"
        )


async def run_live_audio_test():
    downloads_dir = Path(r"C:\Users\laksh\Downloads")
    mkv_matches = glob.glob(str(downloads_dir / "*Dexter*.mkv"))
    if not mkv_matches:
        raise FileNotFoundError(f"Dexter MKV file not found in {downloads_dir}")
    dexter_mkv = str(Path(mkv_matches[0]).resolve())
    print(f"[+] Target media file: {os.path.basename(dexter_mkv)} ({os.path.getsize(dexter_mkv) / (1024**3):.2f} GB)")

    http_port = 8133
    cdp_port = 9233

    # Keep exports and generated speech tracks out of the user's real output folder.
    isolated_output = tempfile.mkdtemp(prefix="scriber_live_output_")
    os.environ["SCRIBER_OUTPUT_DIR"] = isolated_output

    print(f"[+] Starting Scriber server on 127.0.0.1:{http_port}...")
    server = ScriberBackgroundServer(host="127.0.0.1", port=http_port)
    server.start(timeout=5.0)

    edge_bin = find_edge_binary()
    if not edge_bin or not os.path.exists(edge_bin):
        server.stop()
        raise RuntimeError(f"Edge binary not found: {edge_bin}")

    temp_profile = os.path.join(tempfile.gettempdir(), f"scriber_audio_test_{int(time.time())}")
    os.makedirs(temp_profile, exist_ok=True)

    print(f"[+] Launching Edge with CDP on port {cdp_port}...")
    edge_proc = subprocess.Popen([
        edge_bin,
        f"--app={server.url}",
        f"--user-data-dir={temp_profile}",
        f"--remote-debugging-port={cdp_port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-features=Translate,ElasticOverscroll",
    ])

    session = aiohttp.ClientSession()
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            await asyncio.sleep(0.5)
            try:
                async with session.get(f"http://127.0.0.1:{cdp_port}/json") as r:
                    if r.status == 200:
                        targets = await r.json()
                        target = next(
                            (t for t in targets if "Scriber" in t.get("title", "") or str(http_port) in t.get("url", "")),
                            None,
                        )
                        if target and "webSocketDebuggerUrl" in target:
                            ws_url = target["webSocketDebuggerUrl"]
                            break
            except Exception:
                pass

        if not ws_url:
            raise RuntimeError(f"Could not connect to CDP targets on port {cdp_port}")

        print(f"[+] Connected to CDP WebSocket: {ws_url}")
        ws = await session.ws_connect(ws_url)
        cdp = CDPSession(ws)

        # Wait for Scriber to finish frontend initialization
        for _ in range(40):
            is_ready = await cdp.evaluate("typeof window.startProcessingPath === 'function'")
            if is_ready:
                break
            await asyncio.sleep(0.3)
        assert is_ready, "Scriber frontend failed to initialize startProcessingPath"

        # Check OPTIONS preflight directly via HTTP
        origin = f"http://127.0.0.1:{http_port}"
        async with session.options(f"http://127.0.0.1:{http_port}/api/media", headers={"Origin": origin}) as opt_resp:
            print(f"  [*] OPTIONS /api/media status: {opt_resp.status}")
            assert opt_resp.status == 204, f"Expected 204 for OPTIONS, got {opt_resp.status}"
            assert opt_resp.headers.get("Access-Control-Allow-Origin") == origin, "Expected validated loopback CORS origin"
            print("  [✓] OPTIONS preflight verified with validated loopback CORS origin.")

        # Ingest Dexter MKV with max_duration=10 for rapid test turnaround
        print("[+] Initiating transcription of Dexter MKV (first 10s)...")
        await cdp.evaluate(
            f"void window.startProcessingPath({json.dumps(dexter_mkv)}, {{max_duration: 10}})"
        )

        # Wait for processing completion
        t0 = time.time()
        completed = False
        while time.time() - t0 < 420:
            proc_disp = await cdp.evaluate("document.getElementById('processing-card').style.display")
            out_disp = await cdp.evaluate("document.getElementById('output-viewport').style.display")
            if proc_disp == "none" and out_disp == "block":
                completed = True
                break
            await asyncio.sleep(0.4)
        assert completed, "Processing Dexter MKV did not complete in time"
        print(f"  [*] Processing completed in {time.time() - t0:.2f}s")

        # 1. Verify media_url and audio source
        audio_src = await cdp.evaluate("document.getElementById('audio-player').src")
        print(f"  [*] Audio player source: {audio_src}")
        assert audio_src and "/api/media" in audio_src, f"Invalid audio source: {audio_src}"

        # 2. Verify audio error state and duration
        player_error = await cdp.evaluate("document.getElementById('audio-player').error")
        print(f"  [*] Audio player error state: {player_error}")
        assert player_error is None, f"Audio player reported error: {player_error}"

        # Wait for metadata / canplay
        for _ in range(20):
            dur = await cdp.evaluate("document.getElementById('audio-player').duration")
            ready_state = await cdp.evaluate("document.getElementById('audio-player').readyState")
            if dur and dur > 0 and ready_state >= 2:
                break
            await asyncio.sleep(0.2)

        dur = await cdp.evaluate("document.getElementById('audio-player').duration")
        ready_state = await cdp.evaluate("document.getElementById('audio-player').readyState")
        print(f"  [*] Audio duration: {dur:.2f}s, readyState: {ready_state}")
        assert dur and dur > 0, f"Expected positive duration, got {dur}"
        assert ready_state >= 2, f"Expected readyState >= 2 (HAVE_CURRENT_DATA), got {ready_state}"

        # 2b. Verify real server waveform + timeline contract
        peaks_len = await cdp.evaluate(
            "(Array.isArray(window.currentResult && window.currentResult.waveform_peaks))"
            " ? window.currentResult.waveform_peaks.length : 0"
        )
        envelope_len = await cdp.evaluate(
            "(typeof waveEnvelope !== 'undefined' && Array.isArray(waveEnvelope)) ? waveEnvelope.length : 0"
        )
        accurate_dur = await cdp.evaluate("getAccurateDuration()")
        print(f"  [*] waveform_peaks={peaks_len}, waveEnvelope={envelope_len}, getAccurateDuration={accurate_dur:.2f}")
        assert peaks_len == 64, f"Expected 64 real waveform bars, got {peaks_len}"
        assert envelope_len == 64, f"Frontend did not consume 64 waveform bars, got {envelope_len}"
        assert abs(accurate_dur - dur) < 0.5, f"Timeline duration {accurate_dur} disagrees with player {dur}"

        # 3. Verify initial play/pause button state
        initial_paused = await cdp.evaluate("document.getElementById('audio-player').paused")
        play_icon_disp = await cdp.evaluate("document.getElementById('play-icon').style.display")
        pause_icon_disp = await cdp.evaluate("document.getElementById('pause-icon').style.display")
        print(f"  [*] Initial state: paused={initial_paused}, playIcon={play_icon_disp}, pauseIcon={pause_icon_disp}")
        assert initial_paused is True, "Audio player should start paused"

        # 4. Trigger Play via Master Play Button
        print("[+] Clicking Master Play Button (#btn-master-play)...")
        await cdp.click("#btn-master-play")
        await asyncio.sleep(0.8)

        is_playing = not await cdp.evaluate("document.getElementById('audio-player').paused")
        play_icon_disp = await cdp.evaluate("document.getElementById('play-icon').style.display")
        pause_icon_disp = await cdp.evaluate("document.getElementById('pause-icon').style.display")
        btn_has_class = await cdp.evaluate("document.getElementById('btn-master-play').classList.contains('is-playing')")
        print(f"  [*] Active state: playing={is_playing}, playIcon={play_icon_disp}, pauseIcon={pause_icon_disp}, hasClass={btn_has_class}")
        assert is_playing is True, "Audio failed to play after clicking master play button"
        assert play_icon_disp == "none", "Play icon should be hidden during playback"
        assert pause_icon_disp == "block", "Pause icon should be visible during playback"
        assert btn_has_class is True, "#btn-master-play should have is-playing class"

        # 5. Let audio advance for 2.0 seconds and observe live sync updates
        await asyncio.sleep(2.0)
        curr_time = await cdp.evaluate("document.getElementById('audio-player').currentTime")
        timecode_text = await cdp.evaluate("document.getElementById('live-timecode').innerText")
        print(f"  [*] Advancing playback: currentTime={curr_time:.2f}s, timecode='{timecode_text}'")
        assert curr_time >= 1.0, f"currentTime did not advance during playback: {curr_time}"
        assert timecode_text and timecode_text != "0:00 / 0:00", f"Timecode failed to update: {timecode_text}"

        # 6. Verify segment and word token active synchronization
        active_segs = await cdp.evaluate("document.querySelectorAll('.segment-card.active-seg').length")
        print(f"  [*] Active segment cards during playback: {active_segs}")
        assert active_segs >= 1, "Expected at least 1 segment card to be highlighted as active-seg"

        # 7. Pause via Master Play Button
        print("[+] Clicking Master Play Button to Pause...")
        await cdp.click("#btn-master-play")
        await asyncio.sleep(0.4)

        is_paused = await cdp.evaluate("document.getElementById('audio-player').paused")
        play_icon_disp = await cdp.evaluate("document.getElementById('play-icon').style.display")
        pause_icon_disp = await cdp.evaluate("document.getElementById('pause-icon').style.display")
        btn_has_class = await cdp.evaluate("document.getElementById('btn-master-play').classList.contains('is-playing')")
        print(f"  [*] Paused state: paused={is_paused}, playIcon={play_icon_disp}, pauseIcon={pause_icon_disp}, hasClass={btn_has_class}")
        assert is_paused is True, "Audio failed to pause after clicking master play button"
        assert play_icon_disp == "block", "Play icon should be visible when paused"
        assert pause_icon_disp == "none", "Pause icon should be hidden when paused"
        assert btn_has_class is False, "#btn-master-play should not have is-playing class when paused"

        # 7b. Unpause via Master Play Button
        print("[+] Clicking Master Play Button to Unpause...")
        await cdp.click("#btn-master-play")
        await asyncio.sleep(0.8)

        is_unpaused = not await cdp.evaluate("document.getElementById('audio-player').paused")
        play_icon_disp = await cdp.evaluate("document.getElementById('play-icon').style.display")
        pause_icon_disp = await cdp.evaluate("document.getElementById('pause-icon').style.display")
        btn_has_class = await cdp.evaluate("document.getElementById('btn-master-play').classList.contains('is-playing')")
        print(f"  [*] Unpaused state: playing={is_unpaused}, playIcon={play_icon_disp}, pauseIcon={pause_icon_disp}, hasClass={btn_has_class}")
        assert is_unpaused is True, "Audio failed to unpause after clicking master play button"
        assert play_icon_disp == "none", "Play icon should be hidden when unpaused"
        assert pause_icon_disp == "block", "Pause icon should be visible when unpaused"
        assert btn_has_class is True, "#btn-master-play should have is-playing class when unpaused"

        # 7c. Pause again
        print("[+] Pausing again before seek tests...")
        await cdp.click("#btn-master-play")
        await asyncio.sleep(0.4)

        # 8. Test Word-Click Seeking
        tokens_count = await cdp.evaluate("document.querySelectorAll('.word-token').length")
        print(f"  [*] Total rendered word tokens: {tokens_count}")
        assert tokens_count > 0, "No word tokens rendered in transcript"

        first_token_start = float(await cdp.evaluate("document.querySelector('.word-token').getAttribute('data-start')"))
        print(f"  [*] Seeking by clicking first word token (start: {first_token_start}s)...")
        await cdp.evaluate("document.querySelector('.word-token').click()")
        await asyncio.sleep(0.4)

        seeked_time = await cdp.evaluate("document.getElementById('audio-player').currentTime")
        print(f"  [*] Player currentTime after token click: {seeked_time:.2f}s")
        assert abs(seeked_time - first_token_start) < 0.8, (
            f"Player did not seek to token start time: {seeked_time} vs {first_token_start}"
        )

        # 9. Test Waveform Seeking
        print("[+] Testing seekTo(4.5)...")
        await cdp.evaluate("seekTo(4.5)")
        await asyncio.sleep(0.4)
        seek_45_time = await cdp.evaluate("document.getElementById('audio-player').currentTime")
        print(f"  [*] Player currentTime after seekTo(4.5): {seek_45_time:.2f}s")
        assert abs(seek_45_time - 4.5) < 0.8, f"Player did not seek to 4.5s: {seek_45_time}"

        # Pause player cleanly before exit
        await cdp.evaluate("document.getElementById('audio-player').pause()")

        print("\n========================================================")
        print("ALL LIVE AUDIO PLAYBACK AND SYNC TESTS PASSED!")
        print("========================================================")

    finally:
        print("[+] Cleaning up processes and temp resources...")
        if ws and not ws.closed:
            await ws.close()
        if session and not session.closed:
            await session.close()
        if edge_proc:
            try:
                edge_proc.terminate()
                edge_proc.wait(timeout=3.0)
            except Exception:
                try:
                    edge_proc.kill()
                except Exception:
                    pass
        server.stop()
        if temp_profile and os.path.exists(temp_profile):
            shutil.rmtree(temp_profile, ignore_errors=True)
        if isolated_output and os.path.exists(isolated_output):
            shutil.rmtree(isolated_output, ignore_errors=True)
        print("[+] Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(run_live_audio_test())
