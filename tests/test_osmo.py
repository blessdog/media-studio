#!/usr/bin/env python3
"""Osmo lane rules (studio/osmo.py) — pure, no ffmpeg, no footage.

    .venv/bin/python tests/test_osmo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ir as irmod
from studio import osmo

passed = 0


def check(label, cond):
    global passed
    if not cond:
        print(f"FAIL: {label}")
        sys.exit(1)
    passed += 1
    print(f"  ok  {label}")


GOOD = {"fps": "24/1", "duration": 2.0, "width": 3840, "height": 2160,
        "codec": "hevc", "pix_fmt": "yuv420p10le", "bits": 10,
        "format_tags": {}, "stream_tags": {}}

ok, why = osmo.assess(GOOD)
check("to-spec clip passes", ok and why == [])

ok, why = osmo.assess({**GOOD, "fps": "24000/1001"})
check("23.976 passes assess (lint decides later)", ok)
check("24/1 stamps as Resolve '24'", irmod.resolve_rate({"timebase": {"fps": "24/1"}}) == "24")
check("24000/1001 stamps as Resolve '23.976'", irmod.resolve_rate({"timebase": {"fps": "24000/1001"}}) == "23.976")
check("30000/1001 stamps as Resolve '29.97'", irmod.resolve_rate({"timebase": {"fps": "30000/1001"}}) == "29.97")

ok, why = osmo.assess({**GOOD, "codec": "h264", "pix_fmt": "yuv420p", "bits": 8})
check("8-bit H.264 is flagged with both reasons", (not ok) and len(why) == 2)

ok, why = osmo.assess({**GOOD, "width": 1920, "height": 1080})
check("1080p is flagged", (not ok) and "1920x1080" in why[0])

ok, why = osmo.assess({**GOOD, "fps": "60/1"})
check("60p is flagged", (not ok) and "60/1" in why[0])

ok, why = osmo.assess({**GOOD, "bits": None, "pix_fmt": "yuv420p10le"})
check("10-bit by pix_fmt alone passes", ok)

check("ISO read from stream tags", osmo.iso_from_tags({**GOOD, "stream_tags": {"ISO": "100"}}) == "100")
check("no ISO tag is None", osmo.iso_from_tags(GOOD) is None)

clips = [{"id": "c1", "path": "/x/a.mp4", "frames": 48, "fps": "24/1", "width": 3840, "height": 2160},
         {"id": "c2", "path": "/x/b.mp4", "frames": 24, "fps": "24/1", "width": 3840, "height": 2160}]
ir = osmo.build_ir("t", clips)
check("IR has one edit per clip on V1", [e["track"] for e in ir["edits"]] == [1, 1])
check("edits are full length and butt-joined", ir["edits"][1]["record"] == 48 and ir["edits"][1]["srcOut"] == 24)
check("IR carries fps and resolution from the clips", ir["timebase"]["fps"] == "24/1" and ir["resolution"]["width"] == 3840)
check("one awaiting-human marker per edit", len(ir["markers"]) == 2)

print(f"\ntest_osmo: {passed} checks green")
