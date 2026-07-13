#!/usr/bin/env python3
"""Render a template preview for Ryan's verdict — THE library approval gate.

    .venv/bin/python tools/preview-template.py "MS ND Headline" \
        [--input "StyledText=THE FED BLINKS"] [--bg footage.mp4] [--open]

Forges the populated alpha master (cached), composites it over real footage
(default: the rig-demo recording if present, else dark gray), writes
outputs/previews/<slug>-preview.mp4 and optionally opens it. Approval is
NEVER flipped by this tool — Ryan's eyes verdict, then the manifest+registry
get updated explicitly.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import registry as regmod
from studio import templates as tmplmod
from studio.resolve import connect

ROOT = Path(__file__).resolve().parent.parent
PREVIEWS = ROOT / "outputs" / "previews"
DEFAULT_BG = ROOT / "outputs" / "projects" / "rig-demo" / "recording.mp4"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("--input", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--bg", help="footage to composite under the graphic")
    ap.add_argument("--open", action="store_true", help="open the preview")
    args = ap.parse_args()

    inputs = {}
    for kv in args.input:
        k, v = kv.split("=", 1)
        inputs[k] = v

    app = connect()
    master, frames = tmplmod.render_master(
        app, args.template, inputs, 30.0,
        {"width": 1920, "height": 1080}, PREVIEWS / "cache")
    print(f"alpha master: {master} ({frames} frames)")

    out = PREVIEWS / f"{master.stem.split('@')[0]}-preview.mp4"
    bg = Path(args.bg) if args.bg else DEFAULT_BG
    if bg.is_file():
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-i", str(bg), "-i", str(master),
               "-filter_complex",
               "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,"
               "crop=1920:1080[bg];[bg][1:v]overlay=shortest=1[v]",
               "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "20",
               "-pix_fmt", "yuv420p", str(out)]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-f", "lavfi", "-i", "color=c=0x333333:s=1920x1080:r=30:d=5",
               "-i", str(master), "-filter_complex",
               "[0:v][1:v]overlay=shortest=1[v]", "-map", "[v]", "-an",
               "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(cmd, check=True)
    print(f"PREVIEW: {out}")

    lib = tmplmod.load_manifests()
    entry = lib[args.template]
    reg = regmod.connect()
    regmod.record_template(reg, args.template, entry["package"],
                           entry.get("version", 1), entry.get("approved", False))
    if args.open:
        subprocess.run(["open", str(out)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
