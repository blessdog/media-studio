#!/usr/bin/env python3
"""Generate captions for a video workspace.

    .venv/bin/python tools/make-captions.py <workspace> [--native]

Writes <workspace>/captions.srt from the Deepgram transcript (word-timed,
platform-ready — YouTube/Resolve both import SRT). --native additionally
runs Resolve's own AI captioning (CreateSubtitlesFromAudio) on the
workspace's CURRENT compiled timeline, creating a subtitle track in-place.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import captions as capmod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace")
    ap.add_argument("--native", action="store_true",
                    help="also run Resolve's CreateSubtitlesFromAudio on the "
                         "workspace's current timeline")
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    tp = ws / "transcript.json"
    if not tp.is_file():
        print(f"FAIL: no transcript.json in {ws}")
        return 1
    transcript = json.loads(tp.read_text())
    cues = capmod.to_cues(transcript)
    if not cues:
        print("FAIL: transcript has no cueable utterances")
        return 1
    ir_path = ws / "story.json"
    if ir_path.is_file():
        from studio import ir as irmod
        ir, _ = irmod.load(ir_path)
        n_src = len(cues)
        cues = capmod.remap_to_timeline(cues, ir)
        print(f"remapped to cut timeline: {len(cues)}/{n_src} cues survive the cuts")
    out = ws / "captions.srt"
    out.write_text(capmod.srt(cues), encoding="utf-8")
    print(f"captions: {len(cues)} cues -> {out}")

    if args.native:
        from studio import compile as compmod
        from studio import ir as irmod
        ir, base = irmod.load(ws / "story.json")
        proj, tl, _ = compmod.compile_ir(ir, base, ws / "story.otio")
        ok = tl.CreateSubtitlesFromAudio()
        print(f"native CreateSubtitlesFromAudio on '{tl.GetName()}': {ok}")
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
