"""The Osmo Action 5 Pro lane's shot-settings rules (docs/CINEMATIC-PIPELINE.md §2-3).

Pure functions over probe dicts so the rules run inside `make check` with no
ffmpeg and no footage. The tool (tools/ingest-osmo.py) does the I/O.
"""
from fractions import Fraction

EXPECT_CODEC = "hevc"
TEN_BIT_PIX_FMTS = {"yuv420p10le", "yuv420p10be", "yuv422p10le", "yuv422p10be",
                    "yuv444p10le", "yuv444p10be"}
EXPECT_SIZE = (3840, 2160)
ALLOWED_FPS = {Fraction(24, 1), Fraction(24000, 1001)}
GENERATOR = "ingest-osmo-v0"


def assess(meta):
    """(ok, reasons) for one probe() dict. Empty reasons means the clip was shot
    to spec: H.265, 10-bit, 3840x2160, 24 or 23.976 fps."""
    reasons = []
    if meta.get("codec") != EXPECT_CODEC:
        reasons.append(f"codec {meta.get('codec')!r}, expected {EXPECT_CODEC} (shot in H.264 or not on this camera)")
    pf = meta.get("pix_fmt")
    if pf not in TEN_BIT_PIX_FMTS and meta.get("bits") != 10:
        reasons.append(f"pix_fmt {pf!r} is not 10-bit (shot in a normal colour profile, not D-Log M 10-bit)")
    if (meta.get("width"), meta.get("height")) != EXPECT_SIZE:
        reasons.append(f"{meta.get('width')}x{meta.get('height')}, expected {EXPECT_SIZE[0]}x{EXPECT_SIZE[1]}")
    fps = meta.get("fps")
    try:
        fr = Fraction(fps)
    except (TypeError, ValueError, ZeroDivisionError):
        fr = None
    if fr not in ALLOWED_FPS:
        reasons.append(f"fps {fps!r}, expected 24 or 23.976")
    return (not reasons), reasons


def is_ntsc_rate(fps):
    """True for 24000/1001-style rates the lint refuses (VERIFY 12)."""
    try:
        return Fraction(fps).denominator == 1001
    except (TypeError, ValueError, ZeroDivisionError):
        return False


def iso_from_tags(meta):
    """Best-effort ISO from container/stream tags. Unverified where DJI puts it."""
    for tags in (meta.get("stream_tags") or {}, meta.get("format_tags") or {}):
        for k, v in tags.items():
            if "iso" in k.lower():
                return str(v)
    return None


def build_ir(name, clips, created_by="ingest-osmo"):
    """One full-length edit per passing clip, in order, on V1.

    clips: [{'id', 'path', 'frames'}], all already asserted to share fps/size.
    fps and resolution come from the first clip's probe (passed in by caller).
    """
    edits, record = [], 0
    for c in clips:
        edits.append({"id": f"e-{c['id']}", "asset": c["id"], "srcIn": 0,
                      "srcOut": c["frames"], "record": record, "track": 1})
        record += c["frames"]
    return {
        "irVersion": "0.2",
        "name": name,
        "timebase": {"fps": clips[0]["fps"]},
        "resolution": {"width": clips[0]["width"], "height": clips[0]["height"]},
        "assets": [{"id": c["id"], "path": c["path"], "kind": "video"} for c in clips],
        "edits": edits,
        "markers": [{"frame": e["record"], "color": "Sky", "name": e["asset"],
                     "note": "awaiting human pass: balance, CineFocus"} for e in edits],
        "provenance": {"generator": GENERATOR, "createdBy": created_by},
    }
