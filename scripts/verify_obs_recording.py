#!/usr/bin/env python3
"""Machine-to-machine OBS check: stop any zombie stream, roll a short test
recording, and ffprobe the file OBS wrote (Hybrid MP4 verification).

    .venv/bin/python scripts/verify_obs_recording.py [seconds]

Credentials come from OBS's own obs-websocket config (local plugin config);
nothing is hardcoded here.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import obsws_python as obs

WS_CONFIG = Path.home() / ("Library/Application Support/obs-studio/"
                           "plugin_config/obs-websocket/config.json")


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    cfg = json.loads(WS_CONFIG.read_text(encoding="utf-8"))
    cl = obs.ReqClient(host="localhost", port=cfg["server_port"],
                       password=cfg["server_password"], timeout=10)

    ver = cl.get_version()
    print(f"connected: OBS {ver.obs_version} (ws {ver.obs_web_socket_version})")

    st = cl.get_stream_status()
    if st.output_active or st.output_reconnecting:
        state = "reconnecting" if st.output_reconnecting else "active"
        cl.stop_stream()
        print(f"stream was {state} -> stopped")
    else:
        print("stream: not active")

    rec = cl.get_record_status()
    if rec.output_active:
        print("recording already in progress — leaving it alone, aborting test")
        return 1

    cl.start_record()
    print(f"recording {seconds:.0f}s test clip...")
    time.sleep(seconds)
    out = cl.stop_record().output_path
    print(f"OBS wrote: {out}")

    for _ in range(20):                      # finalization can lag a beat
        if Path(out).is_file() and Path(out).stat().st_size > 0:
            break
        time.sleep(0.5)
    else:
        print("FAIL: recording file never appeared")
        return 1

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=format_name,duration:stream=codec_type,codec_name",
         "-of", "json", out], capture_output=True, text=True)
    meta = json.loads(probe.stdout)
    fmt = meta["format"]["format_name"]
    codecs = [f"{s['codec_type']}:{s.get('codec_name')}" for s in meta["streams"]]
    print(f"container: {fmt} | duration {float(meta['format']['duration']):.1f}s | {', '.join(codecs)}")

    if "mp4" not in fmt or not out.endswith(".mp4"):
        print(f"FAIL: expected mp4 container, got {fmt} ({out})")
        return 1
    print("HYBRID MP4 VERIFIED: OBS recordings are Resolve-ingestable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
