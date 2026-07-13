#!/usr/bin/env python3
"""Delivery fan-out: workspace -> platform-ready files, one command.

    .venv/bin/python tools/deliver.py <workspace> [--presets vertical,podcast-audio]
        [--open]

Compiles the workspace's story.json (cached if unchanged), renders ONE
master via Resolve, derives the requested presets via ffmpeg, verifies
every output (probe + loudness), records them in the registry, and prints
every artifact path. Files land in <workspace>/delivery/.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import compile as compmod
from studio import delivery as delmod
from studio import ir as irmod
from studio import lint as lintmod
from studio import registry as regmod
from studio import verify as verifymod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("--presets", default=",".join(delmod.PRESETS),
                    help=f"comma list of: {', '.join(delmod.PRESETS)} (default all)")
    ap.add_argument("--open", action="store_true",
                    help="reveal the delivery folder when done")
    args = ap.parse_args()

    ws = (ROOT / "outputs" / "projects" / args.workspace) \
        if not Path(args.workspace).is_dir() else Path(args.workspace).resolve()
    ir, base = irmod.load(ws / "story.json")
    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1

    presets = [p.strip() for p in args.presets.split(",") if p.strip()]
    unknown = [p for p in presets if p not in delmod.PRESETS]
    if unknown:
        print(f"FAIL: unknown presets {unknown} (have: {sorted(delmod.PRESETS)})")
        return 1

    proj, tl, cached = compmod.compile_ir(ir, ws, ws / "story.otio")
    verrs = verifymod.verify_timeline(ir, proj, tl)
    if verrs:
        print("VERIFY FAIL (structure):")
        for e in verrs:
            print(f"  {e}")
        return 1
    print(f"timeline: {tl.GetName()} ({'cached' if cached else 'compiled'})")

    out_dir = ws / "delivery"
    expect_audio = verifymod.expects_audio(ir)
    reg = regmod.connect()

    master = delmod.render_master(proj, tl, out_dir)
    errs = delmod.probe_output(master, expect_audio)
    if errs:
        print("DELIVERY FAIL (master):")
        for e in errs:
            print(f"  {e}")
        return 1
    regmod.record_render(reg, ir, master, verified=True)
    print(f"master:        {master}")

    for preset in presets:
        out = delmod.PRESETS[preset](master, out_dir)
        errs = delmod.probe_output(out, expect_audio,
                                   expect_video=(preset != "podcast-audio"))
        if errs:
            print(f"DELIVERY FAIL ({preset}):")
            for e in errs:
                print(f"  {e}")
            return 1
        regmod.record_render(reg, ir, out, verified=True)
        print(f"{preset + ':':14} {out}")

    if args.open:
        import subprocess
        subprocess.run(["open", str(out_dir)])
    print("DELIVERY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
