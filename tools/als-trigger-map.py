#!/usr/bin/env python3
"""Pipeline G2: Ableton .als -> trigger-map.json (docs/CLIP-LANE.md §4).

    .venv/bin/python tools/als-trigger-map.py <project.als> [-o out.json]
        [--include-session] [--no-hash] [--summary]

Reads a Live set and emits one entry per sample FIRING — where each clip
lands on the finished track's timeline, in seconds. That artifact is what
lets the meme a sample was cut from land on the Resolve timeline in time
with the music (§5): the ledger knows the sample's in-point inside its
source clip, this knows when the sample fires, and the two numbers
together place the picture without any manual syncing.

Needs no hardware and no SP-404 — a gzip read and an XML parse against
files already on disk. Free/local.

`sample_hash` is the join key to blessdog's phase8_sp404 ledger. MIDI
firings carry a `note` instead: resolving a note to a pad needs the bank,
and the per-bank channel layout is still unverified against real hardware
(CLIP-LANE.md §2), so that join belongs to the consumer, not a guess here.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ableton as abl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("als", help="path to the .als project file")
    ap.add_argument("-o", "--out", default=None,
                    help="write trigger-map.json here (default: stdout)")
    ap.add_argument("--include-session", action="store_true",
                    help="also emit Session-View clips. Off by default: a "
                         "clip sitting in a slot has no timeline position, "
                         "so it has not fired")
    ap.add_argument("--no-hash", action="store_true",
                    help="skip SHA-256 of referenced samples (faster; drops "
                         "the join key to the sample ledger)")
    ap.add_argument("--summary", action="store_true",
                    help="print what was found instead of the map")
    args = ap.parse_args()

    try:
        project = abl.parse(args.als)
    except abl.AbletonError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    entries = abl.trigger_map(project,
                              hash_samples=not args.no_hash,
                              include_session=args.include_session)

    if args.summary:
        return summarize(project, entries)

    payload = {
        "source_als": project["path"],
        "creator": project["creator"],
        "tempo": project["tempo"],
        "triggers": entries,
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n")
        print(f"{len(entries)} firings -> {args.out}")
    else:
        print(text)
    return 0


def summarize(project, entries):
    print(f"{Path(project['path']).name}  —  {project['creator']}")
    print(f"tempo {project['tempo']} BPM")

    arr = ses = 0
    for track in project["tracks"]:
        for clip in track["clips"]:
            if clip["view"] == "arrangement":
                arr += 1
            else:
                ses += 1
    print(f"tracks {len(project['tracks'])}  "
          f"clips {arr} arrangement / {ses} session")

    kinds = Counter(e["kind"] for e in entries)
    print(f"firings {len(entries)}  "
          f"({kinds['audio']} audio, {kinds['midi']} midi)")

    if entries:
        last = max(e["track_start_secs"] + e["duration_secs"] for e in entries)
        print(f"extent {last / 60:.0f}m{last % 60:04.1f}s")

    unresolved = {e["sample_path"] for e in entries
                  if e["kind"] == "audio" and e["sample_hash"] is None}
    if unresolved:
        # Worth saying out loud: an unresolvable sample still emits its
        # firing, but without the hash it cannot join to the ledger, so
        # its video will not be placed.
        print(f"unresolved samples {len(unresolved)} "
              f"(no hash -> no ledger join -> no picture)")

    per_track = Counter(e["track"] for e in entries)
    for name, n in per_track.most_common():
        print(f"  {n:5d}  {name or '(unnamed)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
