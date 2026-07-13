#!/usr/bin/env python3
"""Phase-2 exit condition: one command, raw recording -> editable rough-cut
timeline (silence-stripped, transcript-anchored markers).

    .venv/bin/python tools/ingest-recording.py recording.mp4
        [--name my-video] [--no-transcribe] [--no-compile] [--render]
        [--margin 0.2s,0.2s]

Artifacts land in outputs/ingest/<name>/: transcript.json, story.json,
story.otio. Nonzero exit on any gate failure.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ingest as ingestmod
from studio import lint as lintmod
from studio import probe as probemod
from studio import registry as regmod
from studio import silence as silencemod

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--name", help="IR/workspace name (default: recording stem)")
    ap.add_argument("--margin", default="0.2s,0.2s",
                    help="auto-editor keep-margin around loud sections")
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    rec = Path(args.recording).resolve()
    if not rec.is_file():
        print(f"FAIL: no such file {rec}")
        return 1
    name = args.name or rec.stem.lower().replace("_", "-").replace(" ", "-")
    ws = ROOT / "outputs" / "projects" / name
    ws.mkdir(parents=True, exist_ok=True)

    meta = probemod.probe(rec)
    print(f"probe: {meta['width']}x{meta['height']} @ {meta['fps']} fps, {meta['duration']:.1f}s")
    reg = regmod.connect()
    regmod.record_asset(reg, rec, kind="video", probe=meta)

    timebase, spans = silencemod.loud_spans(rec, margin=args.margin)
    kept = sum(s["srcOut"] - s["srcIn"] for s in spans)
    num, den = timebase.split("/")
    total = meta["duration"] * int(num) / int(den)
    print(f"silence analysis: {len(spans)} kept spans, {kept} of ~{int(total)} frames")

    transcript = None
    if not args.no_transcribe:
        from studio import transcribe as tmod
        try:
            transcript = tmod.transcribe(rec, ws / "transcript.json")
            n_spk = len({u['speaker'] for u in transcript['utterances']})
            print(f"transcript: {len(transcript['utterances'])} utterances, "
                  f"{n_spk} speaker(s) -> {ws / 'transcript.json'}")
            regmod.record_transcript(reg, rec, transcript, ws / "transcript.json")
        except tmod.TranscribeError as e:
            print(f"transcribe skipped: {e}")

    ir = ingestmod.build_ir(name, rec, meta, timebase, spans, transcript)
    ir_path = ws / "story.json"
    ir_path.write_text(json.dumps(ir, indent=1))
    regmod.record_ir(reg, ir, ir_path)
    print(f"IR written: {ir_path}")

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
        print("INGEST OK (compile skipped)")
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
    print("INGEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
