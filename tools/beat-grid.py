#!/usr/bin/env python3
"""Scene Forge slice 4b: draw the beat grid on a timeline.

    .venv/bin/python tools/beat-grid.py <ws> <audio> [--every 4]
        [--offset-frames 0] [--no-compile]

Analyzes the music (librosa), writes ALL beat frames to <ws>/beats.json
(the candidate cut grid), adds a marker every Nth beat (Purple), and
recompiles so the grid is visible in Resolve. --offset-frames = where
the music starts on the timeline (0 if it plays from the top).
Free/local. Which cut lands on which beat stays Ryan's call.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import beatgrid as bgmod
from studio import ir as irmod
from studio import lint as lintmod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("audio")
    ap.add_argument("--every", type=int, default=4,
                    help="marker every Nth beat (all beats go to beats.json)")
    ap.add_argument("--offset-frames", type=int, default=0)
    ap.add_argument("--no-compile", action="store_true")
    args = ap.parse_args()

    ws = (ROOT / "outputs" / "projects" / args.workspace) \
        if not Path(args.workspace).is_dir() else Path(args.workspace).resolve()
    ir_path = ws / "story.json"
    if not ir_path.is_file():
        print(f"FAIL: no story.json in {ws}")
        return 1
    ir, _ = irmod.load(ir_path)

    try:
        grid = bgmod.analyze(args.audio, ir["timebase"]["fps"])
    except bgmod.BeatError as e:
        print(f"FAIL: {e}")
        return 1
    extent = irmod.extent_frames(ir)
    (ws / "beats.json").write_text(json.dumps({
        "audio": str(Path(args.audio).resolve()), "bpm": grid["bpm"],
        "offsetFrames": args.offset_frames, "beats": grid["beats"],
    }, indent=1), encoding="utf-8")
    markers = bgmod.beat_markers(grid["beats"], every=args.every,
                                 offset=args.offset_frames, extent=extent)
    ir.setdefault("markers", [])
    ir["markers"] = [m for m in ir["markers"]
                     if not m["name"].startswith("beat ")] + markers
    print(f"bpm {grid['bpm']} | {len(grid['beats'])} beats -> beats.json | "
          f"{len(markers)} markers (every {args.every})")

    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL (story.json NOT written):")
        for e in errors:
            print(f"  {e}")
        return 1
    ir_path.write_text(json.dumps(irmod._strip_internal(ir), indent=1),
                       encoding="utf-8")
    print("lint: green | story.json updated")

    if args.no_compile:
        return 0
    from studio import compile as compmod
    from studio import verify as verifymod
    proj, tl, cached = compmod.compile_ir(ir, ws, ws / "story.otio")
    verrs = verifymod.verify_timeline(ir, proj, tl)
    if verrs:
        print("VERIFY FAIL:")
        for e in verrs:
            print(f"  {e}")
        return 1
    proj.SetCurrentTimeline(tl)
    print(f"{'reused' if cached else 'compiled'} + showing '{tl.GetName()}'")
    print("BEAT GRID OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
