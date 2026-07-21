#!/usr/bin/env python3
"""Gate test for the MARK-as-chapter design: do OBS chapter markers, dropped
via obs-websocket during a Hybrid MP4 recording, survive into ffprobe?

    .venv/bin/python scripts/verify_record_chapters.py

Launches OBS if it isn't running. Rolls ~9s, drops two chapters (~3s, ~6s),
stops, then reads chapters back with ffprobe. Exit 0 = both chapters
readable (MARK key can be a plugin chapter action; ingest reads chapters).
Credentials come from OBS's own obs-websocket config; nothing hardcoded.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import obsws_python as obs

WS_CONFIG = Path.home() / ("Library/Application Support/obs-studio/"
                           "plugin_config/obs-websocket/config.json")


def connect(timeout_s=60):
    """Poll until OBS is READY, not merely listening: the socket accepts
    connections before startup finishes, and requests return error 207
    ("not ready") in that window — poll through both phases."""
    cfg = json.loads(WS_CONFIG.read_text(encoding="utf-8"))
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        try:
            cl = obs.ReqClient(host="localhost", port=cfg["server_port"],
                               password=cfg["server_password"], timeout=10)
            cl.get_version()              # raises 207 until OBS is ready
            return cl
        except Exception as e:
            last = e
            time.sleep(2)
    raise RuntimeError(f"OBS never became ready: {last} "
                       "(a blocking dialog on screen, e.g. Safe Mode?)")


def main():
    if subprocess.run(["pgrep", "-x", "OBS"], capture_output=True).returncode:
        print("OBS not running -> launching")
        subprocess.run(["open", "-a", "OBS"], check=True)
    cl = connect()
    ver = cl.get_version()
    print(f"connected: OBS {ver.obs_version} (ws {ver.obs_web_socket_version})")

    if cl.get_record_status().output_active:
        print("recording already in progress — leaving it alone, aborting test")
        return 1

    cl.start_record()
    t0 = time.time()
    print("recording; dropping chapters at ~3s and ~6s...")
    time.sleep(3)
    cl.create_record_chapter("mark-test-1")
    time.sleep(3)
    cl.create_record_chapter("mark-test-2")
    time.sleep(3)
    out = cl.stop_record().output_path
    print(f"rolled {time.time() - t0:.1f}s; OBS wrote: {out}")

    for _ in range(20):                      # finalization can lag a beat
        if Path(out).is_file() and Path(out).stat().st_size > 0:
            break
        time.sleep(0.5)
    else:
        print("FAIL: recording file never appeared")
        return 1

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_chapters", out],
        capture_output=True, text=True, check=True)
    chapters = json.loads(probe.stdout).get("chapters", [])
    print(f"ffprobe chapters: {len(chapters)}")
    for c in chapters:
        print(f"  - start={float(c['start_time']):6.2f}s "
              f"title={c.get('tags', {}).get('title', '?')!r}")

    names = [c.get("tags", {}).get("title") for c in chapters]
    ok = "mark-test-1" in names and "mark-test-2" in names
    print("PASS: chapters survive Hybrid MP4 -> ffprobe" if ok else
          "FAIL: expected chapters missing from ffprobe output")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
