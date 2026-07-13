#!/usr/bin/env python3
"""Scene Forge slice 4a: deterministic camera work via headless Blender.

    .venv/bin/python tools/forge-blender.py <ws> <scene.py|name>
        [--frames 48] [--fps 24] [--size 960x540] [--no-open]

Scene scripts live in repo blender/ (pass a bare name to use one, e.g.
`orbit-cube`). Renders locally — FREE, no spend gate. Output lands in
<ws>/forge/blender/<scene>-NN.mp4, ffprobe-verified, registry-recorded,
opened for Ryan's eyes. Place with edit-ir.py insert-clip.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import blender as blmod
from studio import probe as probemod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("scene", help="scene .py path, or a name in repo blender/")
    ap.add_argument("--frames", type=int, default=48)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--size", default="960x540")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    ws = (ROOT / "outputs" / "projects" / args.workspace) \
        if not Path(args.workspace).is_dir() else Path(args.workspace).resolve()
    scene = Path(args.scene)
    if not scene.is_file():
        scene = ROOT / "blender" / f"{Path(args.scene).stem}.py"
    if not scene.is_file():
        print(f"FAIL: no scene script {args.scene} (repo blender/ has: "
              f"{[p.stem for p in (ROOT / 'blender').glob('*.py')]})")
        return 1

    width, height = (int(v) for v in args.size.lower().split("x"))
    out_dir = ws / "forge" / "blender"
    n = 1 + sum(1 for _ in out_dir.glob(f"{scene.stem}-*.mp4")) \
        if out_dir.is_dir() else 1
    out = out_dir / f"{scene.stem}-{n:02d}.mp4"

    print(f"render: {scene.name} {args.frames}f @ {args.fps}fps {args.size} "
          "(local, free)")
    try:
        blmod.render_scene(scene, out, frames=args.frames, fps=args.fps,
                           width=width, height=height)
    except (blmod.BlenderError, subprocess.TimeoutExpired) as e:
        print(f"FAIL: {e}")
        return 1

    meta = probemod.probe(out)
    want = args.frames / args.fps
    if abs(meta["duration"] - want) > 0.5:
        print(f"FAIL: duration {meta['duration']:.2f}s != expected {want:.2f}s")
        return 1
    print(f"clip: {out}")
    print(f"probe: {meta['width']}x{meta['height']} @ {meta['fps']} fps, "
          f"{meta['duration']:.2f}s")

    reg = regmod.connect()
    regmod.record_asset(reg, out, kind="video", probe=meta)
    if not args.no_open:
        subprocess.run(["open", str(out)])
    print("BLENDER OK — place with: tools/edit-ir.py <ws> insert-clip "
          f"{out} --where ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
