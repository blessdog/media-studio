#!/usr/bin/env python3
"""Smoke S1+S2 (Phase 3): can a still PNG ride an overlay track through the
OTIO->ImportTimelineFromFile path, and does SetCurrentTimeline switch the
visible timeline?

    .venv/bin/python scripts/smoke_image_overlay.py

S1: V1 = talky.mp4 frames 0-120, V2 = meme.png at record 30 for 60 frames.
Pass = 2 video tracks, 1 item on V2 at the right offset/duration.
S2: pass = GetCurrentTimeline() returns the imported timeline after switching.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import compile as compmod

ROOT = Path(__file__).resolve().parent.parent
SMOKE = ROOT / "outputs" / "smoke"
PNG = SMOKE / "smoke-meme.png"
TALKY = SMOKE / "talky.mp4"


def main():
    if not TALKY.is_file():
        print(f"FAIL: missing fixture {TALKY}")
        return 1
    if not PNG.is_file():
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
             "-i", "color=c=orange:s=1920x1080:d=1",
             "-frames:v", "1", str(PNG)], check=True)
        print(f"made test still: {PNG}")

    ir = {
        "irVersion": "0.2-smoke",
        "name": "smoke-image-overlay",
        "timebase": {"fps": "30/1"},
        "resolution": {"width": 1920, "height": 1080},
        "assets": [
            {"id": "v", "path": str(TALKY), "kind": "video", "_frames": 600},
            {"id": "img", "path": str(PNG), "kind": "image"},
        ],
        "edits": [
            {"id": "e1", "asset": "v", "srcIn": 0, "srcOut": 120,
             "record": 0, "track": 1},
            {"id": "e2", "asset": "img", "srcIn": 0, "srcOut": 60,
             "record": 30, "track": 2},
        ],
    }

    proj, tl, cached = compmod.compile_ir(ir, SMOKE, SMOKE / "smoke-image-overlay.otio")
    print(f"{'reused' if cached else 'compiled'} timeline {tl.GetName()!r}")

    vtracks = tl.GetTrackCount("video")
    print(f"video tracks: {vtracks}")
    if vtracks < 2:
        print("S1 FAIL: no overlay track — still images do NOT survive this path")
        return 1
    items = tl.GetItemListInTrack("video", 2)
    if not items or len(items) != 1:
        print(f"S1 FAIL: expected 1 item on V2, got {items and len(items)}")
        return 1
    it = items[0]
    tstart = tl.GetStartFrame()
    start = it.GetStart() - tstart
    dur = it.GetDuration()
    print(f"V2 item: record {start}, duration {dur} (want 30, 60)")
    if (start, dur) != (30, 60):
        print("S1 FAIL: wrong placement")
        return 1
    print("S1 PASS: still image lands on V2 at the right frames")

    ok = proj.SetCurrentTimeline(tl)
    cur = proj.GetCurrentTimeline()
    if not ok or not cur or cur.GetName() != tl.GetName():
        print(f"S2 FAIL: SetCurrentTimeline -> {ok}, current={cur and cur.GetName()}")
        return 1
    print("S2 PASS: SetCurrentTimeline switches the visible timeline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
