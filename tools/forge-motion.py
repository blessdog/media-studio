#!/usr/bin/env python3
"""Scene Forge slice 2: animate a curated still into a video clip (I2V).

    .venv/bin/python tools/forge-motion.py <ws> <still> "<motion prompt>"
        [--model wan-480p|wan-720p] [--approve] [--no-open]

SAME SPEND GATE as forge-stills: without --approve this prints the cost and
exits 2. An agent passes --approve ONLY after Ryan approved that clip's cost
in conversation. The motion prompt is Ryan's per-moment creative direction
(prompt-brain doctrine), never a system default.

Clips land in <ws>/forge/motion/<still>-mNN.mp4 (+ .json provenance
sidecar), verified by ffprobe, registry-recorded, and opened for Ryan's
eyes. Place with: tools/edit-ir.py <ws> insert-clip <clip> --where ...
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import forge as forgemod
from studio import probe as probemod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("still")
    ap.add_argument("prompt")
    ap.add_argument("--model", default=forgemod.DEFAULT_VIDEO_MODEL,
                    choices=sorted(forgemod.VIDEO_MODELS))
    ap.add_argument("--approve", action="store_true",
                    help="Ryan approved this clip's cost in conversation")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    ws = (ROOT / "outputs" / "projects" / args.workspace) \
        if not Path(args.workspace).is_dir() else Path(args.workspace).resolve()
    still = Path(args.still)
    if not still.is_absolute():
        still = (ws / still).resolve()
    if not still.is_file():
        print(f"FAIL: still missing: {still}")
        return 1

    model = forgemod.VIDEO_MODELS[args.model]
    cost = forgemod.estimate_video(args.model)
    tag = ("CEILING (provider publishes no price — approving the ceiling; "
           "real cost measured from the bill)" if model.get("estimated")
           else "verified")
    print(f"clip: ~{model['clip_s']:.0f}s x {model['id']} "
          f"-> estimated ${cost:.2f} {tag}")
    if not args.approve:
        print("AWAITING APPROVAL — nothing spent. Rerun with --approve "
              "after Ryan's go.")
        return 2

    try:
        out = forgemod.animate(still, args.prompt, ws / "forge" / "motion",
                               model_key=args.model)
    except forgemod.ForgeError as e:
        print(f"FAIL: {e}")
        return 1

    meta = probemod.probe(out)
    if meta["duration"] < 1.0:
        print(f"FAIL: output too short ({meta['duration']:.2f}s): {out}")
        return 1
    print(f"clip: {out}")
    print(f"probe: {meta['width']}x{meta['height']} @ {meta['fps']} fps, "
          f"{meta['duration']:.1f}s (${cost:.2f} spent)")

    reg = regmod.connect()
    regmod.record_asset(reg, out, kind="video", probe=meta)
    regmod.record_decision(
        reg, "forge-motion",
        f"{out.name}: {args.model} approved (${cost:.2f})",
        context=f"{still.name} | {args.prompt[:160]}")

    if not args.no_open:
        subprocess.run(["open", str(out)])
    print("MOTION OK — place it with: tools/edit-ir.py <ws> insert-clip "
          f"{out} --where ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
