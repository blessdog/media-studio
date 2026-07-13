"""Story IR -> OTIO interchange file.

OTIO chosen empirically (docs/STORY-IR.md spike): reliable, faithful record
offsets and durations. fps is carried but Resolve applies the project rate on
import, so the compiler stamps the project rate to match.
"""
from pathlib import Path

import opentimelineio as otio

from . import ir as irmod


def emit(ir, base_dir, out_path):
    """Write an .otio for `ir`. Returns the written Path.

    Audio spine (epoch 2): track-1 video edits mirror onto audio lane A1
    (the recording's voice follows its picture); video cutaways on higher
    tracks stay silent by design; audio-asset edits land on audio lanes
    (their `track` = A-index, A2+ by convention for music).
    """
    fps = float(irmod.fps(ir))
    assets = {a["id"]: a for a in ir["assets"]}

    def rt(frames):
        return otio.opentime.RationalTime(frames, fps)

    timeline = otio.schema.Timeline(name=ir["name"], global_start_time=rt(0))

    def lane_of(e):
        kind = assets[e["asset"]]["kind"]
        return ("audio" if kind == "audio" else "video", e.get("track", 1))

    # place every edit into its lane; A1 additionally mirrors V1 video edits
    placements = []
    for e in ir["edits"]:
        placements.append((lane_of(e), e))
        lane, ti = lane_of(e)
        if lane == "video" and ti == 1 and \
                assets[e["asset"]].get("_hasAudio", True):
            placements.append((("audio", 1), e))

    tracks = {}
    order = sorted(placements, key=lambda p: (p[0][0] == "audio", p[0][1],
                                              p[1]["record"]))
    for (lane, ti), _ in order:
        if (lane, ti) not in tracks:
            kind = otio.schema.TrackKind.Audio if lane == "audio" \
                else otio.schema.TrackKind.Video
            t = otio.schema.Track(name=f"{'A' if lane == 'audio' else 'V'}{ti}",
                                  kind=kind)
            timeline.tracks.append(t)
            tracks[(lane, ti)] = {"track": t, "playhead": 0}

    for (lane, ti), e in order:
        slot = tracks[(lane, ti)]
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
