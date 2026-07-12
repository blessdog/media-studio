#!/usr/bin/env python3
"""Emitter spike: does Resolve 21 faithfully import an opentimelineio-built .otio?

Builds a 2-clip timeline with a gap (record offsets), 30fps, from talky.mp4,
imports it, probes count/positions/fps. Verdict decides emit.py's primary path.
Run with the repo venv: .venv/bin/python scripts/spike_otio.py
"""
import sys
from pathlib import Path

import opentimelineio as otio

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from studio.resolve import connect, current_or_named_project

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "outputs" / "smoke" / "talky.mp4"
OUT = ROOT / "outputs" / "smoke" / "spike.otio"
FPS = 30.0

def rt(frames):
    return otio.opentime.RationalTime(frames, FPS)

tl = otio.schema.Timeline(name="spike-otio", global_start_time=rt(0))
track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
tl.tracks.append(track)

media = otio.schema.ExternalReference(
    target_url=MEDIA.as_uri(),
    available_range=otio.opentime.TimeRange(rt(0), rt(600)),
)
# clip A: src 60..150 (90f) at record 0
track.append(otio.schema.Clip(name="clipA", media_reference=media,
             source_range=otio.opentime.TimeRange(rt(60), rt(90))))
# gap of 30 frames, then clip B: src 300..360 (60f) at record 120
track.append(otio.schema.Gap(source_range=otio.opentime.TimeRange(rt(0), rt(30))))
track.append(otio.schema.Clip(name="clipB", media_reference=media.deepcopy(),
             source_range=otio.opentime.TimeRange(rt(300), rt(60))))

otio.adapters.write_to_file(tl, str(OUT))
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")

app = connect()
proj = current_or_named_project(app, "media-studio-smoke")
proj.SetSetting("timelineFrameRate", "30")
mp = proj.GetMediaPool()
timeline = mp.ImportTimelineFromFile(str(OUT), {"timelineName": "spike-otio-import"})
if not timeline:
    print("VERDICT: FAIL — ImportTimelineFromFile returned None for .otio")
    sys.exit(1)

items = timeline.GetItemListInTrack("video", 1) or []
tl_fps = timeline.GetSetting("timelineFrameRate")
start = timeline.GetStartFrame()
print(f"imported: {timeline.GetName()} fps={tl_fps} startFrame={start} items={len(items)}")
expect = [(0, 90), (120, 60)]  # (record, duration)
ok = len(items) == 2
for it, (rec, dur) in zip(items, expect):
    got_rec, got_dur = it.GetStart() - start, it.GetDuration()
    match = (got_rec, got_dur) == (rec, dur)
    ok &= match
    print(f"  {it.GetName()}: record={got_rec} dur={got_dur} expected=({rec},{dur}) {'OK' if match else 'MISMATCH'}")
ok &= str(tl_fps) in ("30", "30.0")
print(f"VERDICT: {'OTIO FAITHFUL — primary emitter' if ok else 'OTIO UNFAITHFUL — fall back to FCPXML'}")
sys.exit(0 if ok else 2)
