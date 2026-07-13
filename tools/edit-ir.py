#!/usr/bin/env python3
"""Assembly-loop verbs: mutate a video's Story IR, gate through lint, compile.

Operates on a workspace dir containing story.json (+ transcript.json).

    tools/edit-ir.py <workspace> find "the fed just blinked"
    tools/edit-ir.py <workspace> insert-image meme.png --where "fed just blinked"
    tools/edit-ir.py <workspace> insert-image meme.png --record 10620 --dur 4
    tools/edit-ir.py <workspace> retime cut0 --record 10650 --dur 2.5
    tools/edit-ir.py <workspace> remove cut0

Every mutation: lint gates -> story.json rewritten -> compile to a fresh
versioned timeline and switch Resolve to it (skip with --no-compile).
Nonzero exit on any gate failure; story.json is never written on a red lint.
"""
import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import edit_ir as editmod
from studio import intake as intakemod
from studio import ir as irmod
from studio import lint as lintmod
from studio import moments as momentsmod
from studio import registry as regmod


def _load_ws(ws):
    ws = Path(ws).resolve()
    ir_path = ws / "story.json"
    if not ir_path.is_file():
        sys.exit(f"FAIL: no story.json in {ws}")
    ir, _ = irmod.load(ir_path)
    transcript = None
    tp = ws / "transcript.json"
    if tp.is_file():
        transcript = json.loads(tp.read_text(encoding="utf-8"))
    return ws, ir_path, ir, transcript


def _fps(ir):
    return Fraction(ir["timebase"]["fps"])


def _resolve_record(ir, transcript, args):
    """--where/--record/--at -> a timeline frame."""
    given = [x for x in (args.where, args.record, args.at) if x is not None]
    if len(given) != 1:
        sys.exit("FAIL: give exactly one of --where / --record / --at")
    if args.record is not None:
        return args.record
    if args.at is not None:
        parts = args.at.split(":")
        secs = float(parts[-1]) + 60 * int(parts[-2] or 0) if len(parts) > 1 \
            else float(parts[0])
        return int(round(secs * _fps(ir)))
    if not transcript:
        sys.exit("FAIL: --where needs transcript.json in the workspace")
    hits = momentsmod.find(transcript, args.where)
    if not hits:
        sys.exit(f"FAIL: phrase not found in transcript: {args.where!r}")
    if args.hit >= len(hits):
        sys.exit(f"FAIL: --hit {args.hit} but only {len(hits)} hit(s)")
    hit = hits[args.hit]
    rec = momentsmod.record_frame(ir, hit["start"])
    if rec is None:
        sys.exit(f"FAIL: hit at source {hit['start']:.1f}s was cut out of the "
                 "timeline (silence-stripped)")
    if len(hits) > 1:
        print(f"note: {len(hits)} hits; using #{args.hit} "
              f"({hit['text']!r} @ source {hit['start']:.1f}s) — pick others with --hit N")
    return rec


def _gate_write_compile(ws, ir_path, ir, args):
    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL (story.json NOT written):")
        for e in errors:
            print(f"  {e}")
        return 1
    ir_path.write_text(json.dumps(irmod._strip_internal(ir), indent=1, encoding="utf-8"))
    reg = regmod.connect()
    regmod.record_ir(reg, ir, ir_path)
    print(f"lint: green | story.json updated -> timeline {irmod.timeline_name(ir)}")

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
    print(f"{'reused' if cached else 'compiled'} + showing timeline '{tl.GetName()}'")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find", help="locate a spoken phrase; print source + timeline position")
    p.add_argument("phrase")

    for name in ("insert-image", "insert-clip", "insert-graphic", "add-music",
                 "retime", "remove", "remove-graphic"):
        p = sub.add_parser(name)
        if name == "insert-image":
            p.add_argument("image")
        elif name == "insert-clip":
            p.add_argument("video")
            p.add_argument("--src-in", type=float, default=0.0,
                           help="b-roll start point in seconds (default 0)")
        elif name == "add-music":
            p.add_argument("audio")
            p.add_argument("--src-in", type=float, default=0.0,
                           help="start point inside the track (seconds)")
        elif name == "insert-graphic":
            p.add_argument("template", help="APPROVED library template name")
            p.add_argument("--input", action="append", default=[],
                           metavar="KEY=VALUE",
                           help="published input, repeatable "
                                "(e.g. --input 'StyledText=THE FED BLINKS')")
        else:
            p.add_argument("edit_id")
        if name.startswith("insert") or name == "add-music":
            p.add_argument("--where", help="spoken phrase to anchor on")
            p.add_argument("--hit", type=int, default=0,
                           help="which phrase occurrence (default first)")
            p.add_argument("--at", help="timeline time M:SS or seconds")
        if name not in ("remove", "remove-graphic"):
            p.add_argument("--record", type=int, help="timeline frame")
            p.add_argument("--dur", type=float, help="duration in seconds")
        p.add_argument("--no-compile", action="store_true",
                       help="mutate + lint only; skip Resolve")

    args = ap.parse_args()
    ws, ir_path, ir, transcript = _load_ws(args.workspace)
    fps = _fps(ir)

    if args.cmd == "find":
        if not transcript:
            sys.exit("FAIL: no transcript.json in workspace")
        hits = momentsmod.find(transcript, args.phrase)
        if not hits:
            print(f"no hits for {args.phrase!r}")
            return 1
        for i, h in enumerate(hits):
            rec = momentsmod.record_frame(ir, h["start"])
            where = (f"timeline {rec} ({momentsmod.timecode(rec, fps)})"
                     if rec is not None else "CUT (silence-stripped)")
            print(f"hit {i}: source {h['start']:.1f}s {h['text']!r} -> {where}")
        return 0

    try:
        if args.cmd == "insert-image":
            record = _resolve_record(ir, transcript, args)
            img = Path(args.image).expanduser().resolve()
            if img.is_file() and ws not in img.parents:
                img = intakemod.file_media(img, ws)
                print(f"filed media: {img}")
            dur = int(round(args.dur * fps)) if args.dur else None
            ir, eid = editmod.insert_cutaway(ir, img, record, duration_frames=dur)
            d = next(e for e in ir["edits"] if e["id"] == eid)
            print(f"insert {eid}: {img.name} at {record} "
                  f"({momentsmod.timecode(record, fps)}) for "
                  f"{d['srcOut'] - d['srcIn']} frames")
        elif args.cmd == "insert-clip":
            record = _resolve_record(ir, transcript, args)
            vid = Path(args.video).expanduser().resolve()
            if vid.is_file() and ws not in vid.parents:
                vid = intakemod.file_media(vid, ws)
                print(f"filed media: {vid}")
            dur = int(round(args.dur * fps)) if args.dur else None
            src_in = int(round(args.src_in * fps))
            ir, eid = editmod.insert_clip(ir, vid, record, src_in=src_in,
                                          duration_frames=dur)
            d = next(e for e in ir["edits"] if e["id"] == eid)
            print(f"insert {eid}: {vid.name} at {record} "
                  f"({momentsmod.timecode(record, fps)}) for "
                  f"{d['srcOut'] - d['srcIn']} frames")
        elif args.cmd == "add-music":
            record = 0 if not (args.where or args.at or args.record is not None) \
                else _resolve_record(ir, transcript, args)
            aud = Path(args.audio).expanduser().resolve()
            if aud.is_file() and ws not in aud.parents:
                aud = intakemod.file_media(aud, ws)
                print(f"filed media: {aud}")
            dur = int(round(args.dur * fps)) if args.dur else None
            src_in = int(round(args.src_in * fps))
            ir, eid = editmod.add_music(ir, aud, record=record, src_in=src_in,
                                        duration_frames=dur)
            d = next(e for e in ir["edits"] if e["id"] == eid)
            print(f"music {eid}: {aud.name} at {record} on A{d['track']} "
                  f"for {d['srcOut'] - d['srcIn']} frames (voice on A1 untouched)")
        elif args.cmd == "insert-graphic":
            record = _resolve_record(ir, transcript, args)
            inputs = {}
            for kv in args.input:
                if "=" not in kv:
                    sys.exit(f"FAIL: --input needs KEY=VALUE, got {kv!r}")
                k, v = kv.split("=", 1)
                inputs[k] = v
            dur = int(round(args.dur * fps)) if args.dur else None
            ir, gid = editmod.insert_graphic(ir, args.template, record,
                                             duration_frames=dur, inputs=inputs)
            print(f"insert {gid}: graphic {args.template!r} at {record} "
                  f"({momentsmod.timecode(record, fps)})")
        elif args.cmd == "retime":
            dur = int(round(args.dur * fps)) if args.dur else None
            ir = editmod.retime_edit(ir, args.edit_id, record=args.record,
                                     duration_frames=dur)
            print(f"retimed {args.edit_id}")
        elif args.cmd == "remove":
            ir = editmod.remove_edit(ir, args.edit_id)
            print(f"removed {args.edit_id}")
        elif args.cmd == "remove-graphic":
            ir = editmod.remove_graphic(ir, args.edit_id)
            print(f"removed graphic {args.edit_id}")
    except (editmod.EditError, intakemod.IntakeError) as e:
        print(f"FAIL: {e}")
        return 1

    return _gate_write_compile(ws, ir_path, ir, args)


if __name__ == "__main__":
    sys.exit(main())
