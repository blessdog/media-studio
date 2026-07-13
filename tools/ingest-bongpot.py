#!/usr/bin/env python3
"""Bongpot -> Resolve finishing timeline: the Phase-6 adapter, one command.

    .venv/bin/python tools/ingest-bongpot.py <call-dir | video-plan.json>
        [--clips DIR] [--audio MP3] [--name N] [--fps 30]
        [--size 1920x1080] [--partial] [--no-compile] [--render]

Reads a bongpot call workspace ONE-WAY (never writes into it): cut.shots
timing -> frame grid, per-shot Wan clips conformed into <ws>/media/, the
untouched call audio on A1, shot ids/speakers/verdicts as markers. Default
fails closed on missing clips (bongpot-assembler doctrine); --partial
places what exists and marks the holes red.
"""
import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import bongpot as bpmod
from studio import intake as intakemod
from studio import lint as lintmod
from studio import probe as probemod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent


def pick_plan(arg):
    p = Path(arg).resolve()
    if p.is_file():
        return p
    if p.is_dir():
        plans = sorted(p.glob("video-plan*.json"), key=lambda f: f.stat().st_mtime)
        if plans:
            return plans[-1]
    raise SystemExit(f"FAIL: no video-plan*.json at {p}")


def pick_clips(call_dir, override):
    if override:
        return Path(override).resolve()
    dirs = sorted([d for d in call_dir.glob("clips*") if d.is_dir()],
                  key=lambda d: d.stat().st_mtime)
    if not dirs:
        raise SystemExit(f"FAIL: no clips dir in {call_dir} (use --clips)")
    return dirs[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("call", help="bongpot call dir or a video-plan*.json")
    ap.add_argument("--clips", help="per-shot clips dir (default: newest clips* in call dir)")
    ap.add_argument("--audio", help="call mp3 (default: ear.json meta.audio)")
    ap.add_argument("--name", help="workspace name (default: call dir name)")
    ap.add_argument("--fps", default="30", help="timeline fps (bongpot OUT_FPS=30)")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--partial", action="store_true",
                    help="place available clips, mark missing shots red")
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    plan_path = pick_plan(args.call)
    call_dir = plan_path.parent
    clips_dir = pick_clips(call_dir, args.clips)
    print(f"plan:  {plan_path}")
    print(f"clips: {clips_dir}")

    audio = Path(args.audio).resolve() if args.audio else bpmod.find_audio(plan_path)
    if not audio or not audio.is_file():
        raise SystemExit("FAIL: call audio not found (ear.json has no usable "
                         "meta.audio; pass --audio)")
    print(f"audio: {audio}")

    try:
        _, shots = bpmod.load_plan(plan_path)
        fps = Fraction(args.fps)
        timebase = f"{fps.numerator}/{fps.denominator}"
        width, height = (int(v) for v in args.size.lower().split("x"))
        grid = bpmod.shot_grid(shots, fps)
    except bpmod.BongpotError as e:
        raise SystemExit(f"FAIL: {e}")

    missing = [g["id"] for g in grid if not (clips_dir / f"{g['id']}.mp4").is_file()]
    if missing and not args.partial:
        raise SystemExit(
            f"FAIL: missing {len(missing)}/{len(grid)} clips "
            f"({', '.join(missing[:8])}{'…' if len(missing) > 8 else ''}) — "
            "rerun with --partial to place what exists")
    if missing:
        print(f"partial: {len(grid) - len(missing)}/{len(grid)} clips placed, "
              f"{len(missing)} marked MISSING")

    name = args.name or f"{call_dir.name}-finish"
    ws = ROOT / "outputs" / "projects" / name
    media = ws / "media"
    media.mkdir(parents=True, exist_ok=True)

    clip_rels, encoded = {}, 0
    for g in grid:
        src = clips_dir / f"{g['id']}.mp4"
        if not src.is_file():
            continue
        dst = media / f"{g['id']}.mp4"
        try:
            if bpmod.normalize_clip(src, dst, g["frames"], fps, width, height):
                encoded += 1
        except bpmod.BongpotError as e:
            raise SystemExit(f"FAIL: {e}")
        clip_rels[g["id"]] = dst.relative_to(ws)
    print(f"conformed {len(clip_rels)} clips ({encoded} encoded, "
          f"{len(clip_rels) - encoded} cached) -> {media}")

    safe_audio = intakemod.resolve_safe(audio, safe_dir=media)
    if safe_audio != audio:
        print(f"space-free hardlink: {safe_audio.name}")
    audio_rel = safe_audio.relative_to(ws) if safe_audio.is_relative_to(ws) \
        else safe_audio

    audio_dur = probemod.probe(safe_audio)["duration"]
    win0 = shots[0]["start"]
    total = grid[-1]["record"] + grid[-1]["frames"]
    src_in = int(round(win0 * fps))
    avail = int(audio_dur * fps)
    audio_frames = min(total, avail - src_in)
    if audio_frames < total:
        print(f"warning: call audio ends {total - audio_frames} frames before "
              "the plan window — A1 runs short")

    ir = bpmod.build_ir(name, grid, clip_rels, audio_rel, src_in,
                        audio_frames, timebase, width, height)
    ir_path = ws / "story.json"
    ir_path.write_text(json.dumps(ir, indent=1), encoding="utf-8")
    reg = regmod.connect()
    regmod.record_asset(reg, safe_audio, kind="audio",
                        probe={"fps": None, "duration": audio_dur,
                               "width": None, "height": None})
    regmod.record_ir(reg, ir, ir_path)
    print(f"IR written: {ir_path} ({len(ir['edits'])} edits, "
          f"{len(ir['markers'])} markers)")

    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("lint: green")

    if args.no_compile:
        print("BONGPOT INGEST OK (compile skipped)")
        return 0

    from studio import compile as compmod
    from studio import verify as verifymod
    proj, tl, cached = compmod.compile_ir(ir, ws, ws / "story.otio")
    print(f"{'reused' if cached else 'compiled'} timeline '{tl.GetName()}'")
    verrs = verifymod.verify_timeline(ir, proj, tl)
    if verrs:
        print("VERIFY FAIL:")
        for e in verrs:
            print(f"  {e}")
        return 1
    print("verify (structure): green")
    proj.SetCurrentTimeline(tl)
    if args.render:
        rerrs, out = verifymod.verify_render(ir, proj, tl, ws / "render")
        if rerrs:
            print("VERIFY FAIL (render):")
            for e in rerrs:
                print(f"  {e}")
            return 1
        regmod.record_render(reg, ir, out, verified=True)
        print(f"verify (render): green | output: {out}")
    print("BONGPOT INGEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
