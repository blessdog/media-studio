#!/usr/bin/env python3
"""Gate test for the MARK-as-chapter design: do OBS chapter markers, dropped
via obs-websocket during a Hybrid MP4 recording, survive into ffprobe?

    .venv/bin/python scripts/verify_record_chapters.py           # self-test
    .venv/bin/python scripts/verify_record_chapters.py <file>    # check a file

Self-test: launches OBS if needed, rolls ~9s, drops two chapters (~3s, ~6s),
stops, reads them back. File mode: just ffprobes an EXISTING recording (e.g.
one made from the deck's Mark key) and passes if it holds at least one real
chapter beyond OBS's automatic 'Start'. Credentials come from OBS's own
obs-websocket config; nothing hardcoded.
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


def read_chapters(path):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_chapters", path],
        capture_output=True, text=True, check=True)
    return json.loads(probe.stdout).get("chapters", [])


def check_file(path):
    if not Path(path).is_file():
        print(f"FAIL: no such file: {path}")
        return 1
    chapters = read_chapters(path)
    print(f"ffprobe chapters: {len(chapters)}")
    for c in chapters:
        print(f"  - start={float(c['start_time']):7.2f}s "
              f"title={c.get('tags', {}).get('title', '?')!r}")
    marks = [c for c in chapters
             if c.get("tags", {}).get("title") != "Start"]  # OBS auto-chapter
    print(f"PASS: {len(marks)} mark(s) beyond the auto 'Start' chapter"
          if marks else
          "FAIL: no chapters beyond the auto 'Start' (were any marks pressed?)")
    return 0 if marks else 1


def main():
    if len(sys.argv) > 1:
        return check_file(sys.argv[1])
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

    chapters = read_chapters(out)
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
