#!/usr/bin/env python3
"""Scene Forge slice 1: cost-gated stills batch + contact sheet.

    .venv/bin/python tools/forge-stills.py <ws> "<prompt>" [--n 8]
        [--model qwen-fast|flux-2] [--size 1920x1080] [--ref img ...]
        [--approve] [--no-open]
    .venv/bin/python tools/forge-stills.py <ws> --pick 2,7,11 [--batch NN]

PER-BATCH APPROVAL DOCTRINE (Ryan, 2026-07-13): without --approve this
prints the cost estimate and exits 2, spending NOTHING. An agent may pass
--approve ONLY after Ryan approved that specific batch in conversation.

Batches land in <ws>/forge/batch-NN/ (01.png.., manifest.json, sheet.jpg);
the sheet opens in Preview; winners are recorded with --pick and placed via
the existing verbs (edit-ir.py insert-image <ws>/forge/batch-NN/07.png ...).
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import forge as forgemod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--model", default=forgemod.DEFAULT_MODEL,
                    choices=sorted(forgemod.MODELS))
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--ref", action="append", default=[],
                    help="reference image(s) for identity conditioning")
    ap.add_argument("--approve", action="store_true",
                    help="Ryan approved this batch's cost in conversation")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--pick", help="record winners, e.g. --pick 2,7,11")
    ap.add_argument("--batch", help="batch name for --pick (default newest)")
    args = ap.parse_args()

    ws = (ROOT / "outputs" / "projects" / args.workspace) \
        if not Path(args.workspace).is_dir() else Path(args.workspace).resolve()

    if args.pick:
        batches = sorted((ws / "forge").glob("batch-*"))
        if not batches:
            print("FAIL: no batches to pick from")
            return 1
        batch = (ws / "forge" / args.batch) if args.batch else batches[-1]
        picks = [int(p) for p in args.pick.split(",") if p.strip()]
        manifest = forgemod.record_picks(batch, picks)
        print(f"picks {manifest['picks']} recorded in {batch / 'manifest.json'}")
        return 0

    if not args.prompt:
        print("FAIL: prompt required (or use --pick)")
        return 1
    for r in args.ref:
        if not Path(r).is_file():
            print(f"FAIL: ref image missing: {r}")
            return 1

    cost = forgemod.estimate(args.model, args.n)
    model_id = forgemod.MODELS[args.model]["id"]
    print(f"batch: {args.n} x {model_id} ({args.size}) "
          f"-> estimated ${cost:.2f}")
    if not args.approve:
        print("AWAITING APPROVAL — nothing spent. Rerun with --approve "
              "after Ryan's go.")
        return 2

    width, height = (int(v) for v in args.size.lower().split("x"))
    batch_dir = forgemod.next_batch_dir(ws)
    try:
        paths, manifest = forgemod.generate_batch(
            args.prompt, args.n, batch_dir, model_key=args.model,
            width=width, height=height, ref_images=args.ref or None)
    except forgemod.ForgeError as e:
        print(f"FAIL: {e}")
        return 1
    print(f"generated {len(paths)} stills -> {batch_dir} "
          f"(${manifest['costUSD']:.2f} spent)")

    reg = regmod.connect()
    for p in paths:
        regmod.record_asset(reg, p, kind="image")
    regmod.record_decision(
        reg, "forge-batch",
        f"{batch_dir.name}: {args.n} x {args.model} approved "
        f"(${manifest['costUSD']:.2f})",
        context=args.prompt[:200])

    sheet = forgemod.contact_sheet(batch_dir)
    print(f"contact sheet: {sheet}")
    if not args.no_open:
        subprocess.run(["open", str(sheet)])
    print("FORGE OK — name the winners (e.g. --pick 2,7,11), place them "
          "with edit-ir.py insert-image, or animate them (slice 2).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
