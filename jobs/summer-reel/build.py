#!/usr/bin/env python3
"""summer-reel: ten iPhone clips -> one widescreen reel on an 80 BPM grid.

    .venv/bin/python jobs/summer-reel/build.py [--no-compile] [--no-conform]

Reads jobs/summer-reel/cuts.json ({source, start, beats, note} in cut order,
start in SOURCE seconds, beats on the 80 BPM grid, even counts only so a beat
pair is an integer 45 frames at 30 fps), conforms every used source to one
widescreen 1280x720 30 fps H.264 stream with loudness-normalised audio, writes
the Story IR to outputs/projects/summer-reel/story.json and compiles it.

PRIOR ART: the conform is ffmpeg (scale/gblur/overlay/fps/loudnorm).
studio/bongpot.py normalize_clip crops to fill; this job must NOT crop.
Second film that wants whole-picture-in-widescreen: move it into studio/.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

JOB = Path(__file__).resolve().parent
SOURCES = REPO / "outputs" / "intake" / "summer-clips"
WS = REPO / "outputs" / "projects" / "summer-reel"
NAME = "summer-reel"
FPS = Fraction(30, 1)
BPM = 80
W, H = 1280, 720   # widescreen, the YouTube shape (Ryan, 2026-09-09)
FRAMES_PER_BEAT = FPS * 60 / BPM          # 22.5 at 30 fps, hence even beats only
TARGET_LUFS = -18.0


def conform(src, dst):
    """One 1280x720 widescreen stream showing the WHOLE source picture.
    Landscape sources are native. Portrait sources stand at full height in
    the middle, the sides filled with a blurred stretch of the same frame.
    Nothing is cropped (Ryan, 2026-09-09: "youre just cropping in the shots
    show the full video. start over with the full video"). Audio to -18 LUFS."""
    vf = (f"split[bg][fg];"
          f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},gblur=sigma=40[bgb];"
          f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
          f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,fps=30,setsar=1")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex", vf,
         "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-r", "30", "-video_track_timescale", "30000",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
         "-movflags", "+faststart", str(dst)], check=True)


def build_ir(cuts):
    assets, edits, markers = [], [], []
    seen = {}
    record = 0
    for i, c in enumerate(cuts):
        if c["beats"] % 2:
            raise SystemExit(f"cut {i}: beats must be even at {BPM} BPM / {FPS} fps")
        aid = seen.get(c["source"])
        if aid is None:
            aid = f"c{len(seen)}"
            seen[c["source"]] = aid
            rel = f"media/{c['source']}.mp4"
            # sha256 makes the conform part of the IR's identity: a reconformed
            # file at the same path is a NEW timeline, never a cached one.
            assets.append({"id": aid, "path": rel, "kind": "video",
                           "sha256": hashlib.sha256((WS / rel).read_bytes()).hexdigest()})
        frames = int(c["beats"] * FRAMES_PER_BEAT)
        src_in = int(round(c["start"] * FPS))
        edits.append({"id": f"e{i}", "asset": aid, "srcIn": src_in,
                      "srcOut": src_in + frames, "record": record, "track": 1})
        markers.append({"frame": record, "color": "Purple",
                        "name": f"cut {i}", "note": c["note"]})
        record += frames
    return {
        "irVersion": "0.1",
        "name": NAME,
        "timebase": {"fps": f"{FPS.numerator}/{FPS.denominator}"},
        "resolution": {"width": W, "height": H},
        "assets": assets,
        "edits": edits,
        "markers": markers,
        "provenance": {"generator": "summer-reel-build", "createdBy": "jobs/summer-reel/build.py"},
    }, record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--no-conform", action="store_true", help="media/ already conformed")
    args = ap.parse_args()

    cuts = json.loads((JOB / "cuts.json").read_text())
    (WS / "media").mkdir(parents=True, exist_ok=True)
    for src_name in dict.fromkeys(c["source"] for c in cuts):
        src = SOURCES / f"{src_name}.MOV"
        dst = WS / "media" / f"{src_name}.mp4"
        if args.no_conform and dst.exists():
            continue
        if not src.exists():
            raise SystemExit(f"missing source: {src}")
        print(f"conform {src.name} -> {dst.relative_to(REPO)}", file=sys.stderr)
        conform(src, dst)

    ir, total = build_ir(cuts)
    ir_path = WS / "story.json"
    ir_path.write_text(json.dumps(ir, indent=1))
    print(f"IR: {ir_path} | {len(ir['edits'])} edits, {total} frames = {total / FPS:.2f}s "
          f"= {total / FRAMES_PER_BEAT:.0f} beats at {BPM} BPM")
    if args.no_compile:
        return 0
    return subprocess.run([str(REPO / ".venv/bin/python"), str(REPO / "tools/compile-ir.py"),
                           str(ir_path), "--show"]).returncode


if __name__ == "__main__":
    sys.exit(main())
