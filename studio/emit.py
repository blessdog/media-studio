"""Story IR -> OTIO interchange file.

OTIO chosen empirically (docs/STORY-IR.md spike): reliable, faithful record
offsets and durations. fps is carried but Resolve applies the project rate on
import, so the compiler stamps the project rate to match.
"""
from pathlib import Path

import opentimelineio as otio

from . import ir as irmod


def emit(ir, base_dir, out_path):
    """Write an .otio for `ir`. Returns the written Path."""
    fps = float(irmod.fps(ir))

    def rt(frames):
        return otio.opentime.RationalTime(frames, fps)

    timeline = otio.schema.Timeline(name=ir["name"], global_start_time=rt(0))

    # one OTIO track per IR track index, in ascending order
    tracks = {}
    for e in sorted(ir["edits"], key=lambda e: (e.get("track", 1), e["record"])):
        ti = e.get("track", 1)
        if ti not in tracks:
            t = otio.schema.Track(name=f"V{ti}", kind=otio.schema.TrackKind.Video)
            timeline.tracks.append(t)
            tracks[ti] = {"track": t, "playhead": 0}

    assets = {a["id"]: a for a in ir["assets"]}
    for e in sorted(ir["edits"], key=lambda e: (e.get("track", 1), e["record"])):
        ti = e.get("track", 1)
        slot = tracks[ti]
        gap = e["record"] - slot["playhead"]
        if gap > 0:
            slot["track"].append(
                otio.schema.Gap(source_range=otio.opentime.TimeRange(rt(0), rt(gap))))
        asset = assets[e["asset"]]
        url = irmod.asset_path(asset, base_dir).as_uri()
        ref = otio.schema.ExternalReference(
            target_url=url,
            available_range=otio.opentime.TimeRange(
                rt(0), rt(asset.get("_frames") or e["srcOut"])),
        )
        dur = e["srcOut"] - e["srcIn"]
        slot["track"].append(otio.schema.Clip(
            name=e["id"], media_reference=ref,
            source_range=otio.opentime.TimeRange(rt(e["srcIn"]), rt(dur))))
        slot["playhead"] = e["record"] + dur

    out_path = Path(out_path)
    otio.adapters.write_to_file(timeline, str(out_path))
    return out_path
