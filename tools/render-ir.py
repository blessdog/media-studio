#!/usr/bin/env python3
"""Render a workspace's Story IR with ffmpeg — here, or on the Mac mini.

    .venv/bin/python tools/render-ir.py <ws> [--on mini] [--out PATH] [--no-open]

Resolve stays the editor; this is the render lane that does not need Resolve
open and can leave this machine. Track-1 edits only (every ingest and session
workspace). Output: <ws>/render/<name>-ffmpeg.mp4 (or -<host>.mp4), probed
for duration and loudness against the IR, then opened.

`--on mini` stages keyframe-padded stream copies of just the windows the cut
uses, ships them with rsync, encodes under tmux at nice 10 (refusing when the
mini lacks disk), pulls the file back, and removes ~/render/<name>/ there.
Only the ssh alias in ~/.ssh/config is assumed (`mini`, user homer).

PRIOR ART: Resolve's own Remote Rendering needs Studio on both machines, a
shared Postgres project library and identical media paths; the mini has 8 GB
with ~60 MB free and 7 GB of disk, and no Resolve. media-tools/stitch.mjs
concatenates whole clips with no per-clip in/out. OneMachine/RESEARCH.md
(2026-08-08) names exactly this shape — rsync in, tmux + nice, rsync out — as
the mini's correct use.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ffrender
from studio import ir as irmod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ws", help="workspace name or path (holds story.json)")
    ap.add_argument("--on", help="ssh host to render on (e.g. mini); default: this machine")
    ap.add_argument("--out", help="output mp4 (default <ws>/render/<name>-<where>.mp4)")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    ws = Path(args.ws)
    if not ws.is_dir():
        ws = ROOT / "outputs" / "projects" / args.ws
    ir_path = ws / "story.json"
    if not ir_path.is_file():
        print(f"FAIL: no story.json in {ws}")
        return 1
    ir, base = irmod.load(ir_path)
    where = args.on or "ffmpeg"
    out = Path(args.out) if args.out else ws / "render" / f"{ir['name']}-{where}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    work = ws / "ffrender"
    work.mkdir(exist_ok=True)

    try:
        if args.on:
            runs = ffrender.render_remote(ir, base, work, out, host=args.on, name=ir["name"])
        else:
            runs = ffrender.render_local(ir, base, work, out)
    except ffrender.RenderError as e:
        print(f"FAIL: {e}")
        return 1
    print(f"rendered {len(runs)} runs -> {out}")

    errors = ffrender.verify(ir, out)
    if errors:
        print("VERIFY FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("verify (render): green")
    reg = regmod.connect()
    regmod.record_render(reg, ir, str(out), verified=True)
    if not args.no_open:
        subprocess.run(["open", str(out)])
    print("RENDER OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
