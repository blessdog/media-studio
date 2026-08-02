#!/usr/bin/env python3
"""Song front door: a track (+ optional stems) -> workspace -> beat grid.

    .venv/bin/python tools/ingest-song.py <audio> [--name N]
        [--fps 30/1] [--size 1920x1080] [--stems a.wav b.wav ...]
        [--bpm 174] [--first-beat 0.25] [--every 4] [--no-compile]

The talking-head lane (tools/ingest-recording.py) is wrong for music: it strips
silence, which would gut a track's rests and breakdowns, and anchors edits to
diarized speech, which a song does not have. So this is a separate front door.

The song lands whole and uncut on A1 — the untouched audio spine. Optional
stems land on A2,A3,A4... one per lane, so a single element can be ducked
later. Then the beat grid is drawn: pass --bpm when you know the tempo from the
SP-404MK2 or the Ableton project and the grid is exact instead of estimated.

Which image lands on which beat stays Ryan's call. This only sets the table.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import beatgrid as bgmod
from studio import edit_ir as editmod
from studio import ingest as ingestmod
from studio import intake as intakemod
from studio import ir as irmod
from studio import lint as lintmod
from studio import probe as probemod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="the song — the untouched spine on A1")
    ap.add_argument("--name", help="workspace name (default: audio stem)")
    ap.add_argument("--fps", default="30/1",
                    help="timeline rate; a song carries none of its own")
    ap.add_argument("--size", default="1920x1080", help="WxH")
    ap.add_argument("--stems", nargs="*", default=[],
                    help="stem files -> A2,A3,A4... one per lane")
    ap.add_argument("--bpm", type=float, default=None,
                    help="KNOWN tempo (SP-404MK2 / Ableton project tempo) — "
                         "exact grid instead of a librosa estimate")
    ap.add_argument("--first-beat", type=float, default=0.0)
    ap.add_argument("--every", type=int, default=4,
                    help="marker every Nth beat")
    ap.add_argument("--no-grid", action="store_true", help="skip the beat grid")
    ap.add_argument("--no-compile", action="store_true")
    args = ap.parse_args()

    song = Path(args.audio).expanduser().resolve()
    if not song.is_file():
        print(f"FAIL: no such file {song}")
        return 1
    safe = intakemod.resolve_safe(song)
    if safe != song:
        print(f"space-free hardlink: {safe.name}")
        song = safe

    try:
        width, height = (int(v) for v in args.size.lower().split("x"))
    except ValueError:
        print(f"FAIL: --size wants WxH, got {args.size!r}")
        return 1

    name = args.name or song.stem.lower().replace("_", "-").replace(" ", "-")
    ws = ROOT / "outputs" / "projects" / name
    ws.mkdir(parents=True, exist_ok=True)

    meta = probemod.probe(song)
    duration = float(meta["duration"])
    print(f"probe: {duration:.1f}s song -> {args.fps} fps, {width}x{height}")

    reg = regmod.connect()
    regmod.record_asset(reg, song, kind="audio", probe=meta)

    ir = ingestmod.build_song_ir(name, song, duration, fps=args.fps,
                                 width=width, height=height)
    print(f"spine: {song.name} whole and uncut on A1 (never overwritten)")

    if args.stems:
        stems = []
        for raw in args.stems:
            s = Path(raw).expanduser().resolve()
            if not s.is_file():
                print(f"FAIL: no such stem {s}")
                return 1
            if ws not in s.parents:
                s = intakemod.file_media(s, ws)
            stems.append(s)
        # Each stem gets ITS OWN length, not the song's. Stems bounced from one
        # session are usually identical in length, but forcing a short stem to
        # the song's extent makes lint refuse the whole ingest — and silently
        # stretching it would be worse.
        rate = irmod.fps(ir)
        for offset, s in enumerate(stems):
            smeta = probemod.probe(s)
            sframes = max(int(round(float(smeta["duration"]) * rate)), 1)
            ir, eid = editmod.add_music(
                ir, s, record=0, duration_frames=sframes,
                track=editmod.MUSIC_TRACK + offset)
            d = next(e for e in ir["edits"] if e["id"] == eid)
            note = "" if sframes >= irmod.extent_frames(ir) else \
                f"  (shorter than the song — {smeta['duration']:.1f}s)"
            print(f"  stem {eid}: {s.name} -> A{d['track']}{note}")

    if not args.no_grid:
        try:
            grid = bgmod.analyze(song, irmod.fps(ir), bpm=args.bpm,
                                 first_beat=args.first_beat)
        except bgmod.BeatError as e:
            print(f"FAIL: {e}")
            return 1
        (ws / "beats.json").write_text(json.dumps({
            "audio": str(song), "bpm": grid["bpm"], "bpmSource": grid["source"],
            "firstBeatSecs": args.first_beat, "offsetFrames": 0,
            "beats": grid["beats"],
        }, indent=1), encoding="utf-8")
        ir["markers"] = bgmod.beat_markers(
            grid["beats"], every=args.every, extent=irmod.extent_frames(ir))
        print(f"grid: bpm {grid['bpm']} ({grid['source']}) | "
              f"{len(grid['beats'])} beats -> beats.json | "
              f"{len(ir['markers'])} markers")

    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL (story.json NOT written):")
        for e in errors:
            print(f"  {e}")
        return 1
    (ws / "story.json").write_text(
        json.dumps(irmod._strip_internal(ir), indent=1), encoding="utf-8")
    print(f"lint: green | workspace {ws}")

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
    print("SONG OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
