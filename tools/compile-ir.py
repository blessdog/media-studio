#!/usr/bin/env python3
"""Compile a Story IR file into an editable Resolve timeline.

    .venv/bin/python tools/compile-ir.py path/to/story.json [--render]

lint -> compile -> verify. Prints every artifact path. Nonzero on any failure.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ir as irmod
from studio import lint as lintmod
from studio import compile as compmod
from studio import registry as regmod
from studio import verify as verifymod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ir_file")
    ap.add_argument("--render", action="store_true",
                    help="also render and ffprobe-verify the output")
    ap.add_argument("--show", action="store_true",
                    help="switch the open Resolve to the compiled timeline")
    args = ap.parse_args()

    try:
        ir, base_dir = irmod.load(args.ir_file)
    except irmod.IRError as e:
        print(f"LOAD FAIL:\n{e}")
        return 1
    print(f"loaded IR '{ir['name']}' -> project {irmod.timeline_name(ir)}")

    errors, warnings = lintmod.lint(ir, base_dir)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("lint: green")

    otio_path = Path(args.ir_file).with_suffix(".otio")
    try:
        proj, timeline, cached = compmod.compile_ir(ir, base_dir, otio_path)
    except Exception as e:
        print(f"COMPILE FAIL: {e}")
        return 1
    print(f"{'reused cached' if cached else 'compiled'} timeline "
          f"'{timeline.GetName()}' | interchange: {otio_path}")

    verrors = verifymod.verify_timeline(ir, proj, timeline)
    if verrors:
        print("VERIFY FAIL (structure):")
        for e in verrors:
            print(f"  {e}")
        return 1
    print("verify (structure): green")

    reg = regmod.connect()
    regmod.record_ir(reg, ir, args.ir_file)

    if args.show:
        proj.SetCurrentTimeline(timeline)
        print(f"showing '{timeline.GetName()}' in Resolve")

    if args.render:
        rerrors, out = verifymod.verify_render(
            ir, proj, timeline, base_dir / "outputs" / "compiled")
        if rerrors:
            print("VERIFY FAIL (render):")
            for e in rerrors:
                print(f"  {e}")
            return 1
        regmod.record_render(reg, ir, out, verified=True)
        print(f"verify (render): green | output: {out}")

    print("COMPILE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
