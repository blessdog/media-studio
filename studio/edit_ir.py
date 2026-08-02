"""Deterministic Story IR mutations — the assembly loop's verbs.

Pure functions: dict in, new dict out (input is never mutated). Every result
MUST re-pass studio.lint before it is compiled; these verbs enforce shape,
the linter enforces truth (files exist, bounds hold, tracks don't collide).
"""
import copy
from fractions import Fraction
from pathlib import Path

CUTAWAY_DEFAULT_SECONDS = 3.5   # house style: full-frame meme, voice under
CUTAWAY_TRACK = 2


class EditError(ValueError):
    pass


def _fps(ir):
    return Fraction(ir["timebase"]["fps"])


def _next_id(ir, prefix):
    used = ({e["id"] for e in ir["edits"]} | {a["id"] for a in ir["assets"]}
            | {g["id"] for g in ir.get("graphics", [])})
    n = 0
    while f"{prefix}{n}" in used:
        n += 1
    return f"{prefix}{n}"


def _find_edit(ir, edit_id):
    for e in ir["edits"]:
        if e["id"] == edit_id:
            return e
    raise EditError(f"no edit {edit_id!r} in IR {ir['name']!r}")


def _add_asset(ir, path, kind, prefix):
    """Register an asset (idempotent by absolute path). Returns (ir, id)."""
    ir = copy.deepcopy(ir)
    path = str(Path(path).resolve())
    for a in ir["assets"]:
        if a["kind"] == kind and str(Path(a["path"])) == path:
            return ir, a["id"]
    aid = _next_id(ir, prefix)
    ir["assets"].append({"id": aid, "path": path, "kind": kind})
    if ir["irVersion"] == "0.1":
        ir["irVersion"] = "0.2"
    return ir, aid


def add_image_asset(ir, path):
    return _add_asset(ir, path, "image", "img")


def insert_cutaway(ir, image_path, record, duration_frames=None,
                   track=CUTAWAY_TRACK, evidence=None):
    """Place an image full-frame over the cut at `record` (timeline frames).

    Returns (ir, edit_id). Duration defaults to the house style
    (CUTAWAY_DEFAULT_SECONDS at the IR's fps).
    """
    if duration_frames is None:
        duration_frames = int(round(CUTAWAY_DEFAULT_SECONDS * _fps(ir)))
    if duration_frames < 1:
        raise EditError(f"duration {duration_frames} frames < 1")
    if record < 0:
        raise EditError(f"record {record} < 0")
    ir, aid = add_image_asset(ir, image_path)
    eid = _next_id(ir, "cut")
    edit = {"id": eid, "asset": aid, "srcIn": 0, "srcOut": duration_frames,
            "record": record, "track": track}
    if evidence:
        edit["evidence"] = list(evidence)
    ir["edits"].append(edit)
    return ir, eid


def insert_clip(ir, video_path, record, src_in=0, duration_frames=None,
                track=CUTAWAY_TRACK, evidence=None):
    """Place a video cutaway (found b-roll) over the cut at `record`.

    Returns (ir, edit_id). Duration defaults to the cutaway house style;
    srcIn/duration are frames in the b-roll's own timebase (lint checks
    bounds via ffprobe).
    """
    if duration_frames is None:
        duration_frames = int(round(CUTAWAY_DEFAULT_SECONDS * _fps(ir)))
    if duration_frames < 1:
        raise EditError(f"duration {duration_frames} frames < 1")
    if record < 0 or src_in < 0:
        raise EditError(f"record {record} / srcIn {src_in} must be >= 0")
    ir, aid = _add_asset(ir, video_path, "video", "broll")
    eid = _next_id(ir, "cut")
    edit = {"id": eid, "asset": aid, "srcIn": src_in,
            "srcOut": src_in + duration_frames, "record": record, "track": track}
    if evidence:
        edit["evidence"] = list(evidence)
    ir["edits"].append(edit)
    return ir, eid


MUSIC_TRACK = 2                 # A2 by convention; A1 belongs to the voice


def add_music(ir, audio_path, record=0, src_in=0, duration_frames=None,
              track=MUSIC_TRACK):
    """Lay an audio asset (music bed, sfx) on its own audio lane.

    Returns (ir, edit_id). Duration defaults to the remaining timeline
    extent from `record` (lint clamps against the file's real length).
    The recording's voice on A1 is untouched — sacred-audio doctrine.
    """
    if record < 0 or src_in < 0:
        raise EditError(f"record {record} / srcIn {src_in} must be >= 0")
    ir, aid = _add_asset(ir, audio_path, "audio", "music")
    if duration_frames is None:
        from . import ir as irmod
        duration_frames = max(irmod.extent_frames(ir) - record, 1)
    if duration_frames < 1:
        raise EditError(f"duration {duration_frames} frames < 1")
    eid = _next_id(ir, "mus")
    ir["edits"].append({"id": eid, "asset": aid, "srcIn": src_in,
                        "srcOut": src_in + duration_frames,
                        "record": record, "track": track})
    return ir, eid


def add_stems(ir, audio_paths, record=0, src_in=0, duration_frames=None,
              first_track=MUSIC_TRACK):
    """Lay a set of stems on CONSECUTIVE audio lanes, one stem per lane.

    Returns (ir, [edit_id, ...]) in the order given, landing on
    A{first_track}, A{first_track+1}, ... — so four Demucs stems or four
    SP-404MK2 Multipad exports become A2/A3/A4/A5.

    Why lanes and not a mixdown: with the parts separated you can duck or drop
    ONE element under narration instead of the whole bed, and beat analysis can
    run on the drum stem alone (far cleaner onsets than a reverb-heavy mix).
    A1 stays the voice — sacred-audio doctrine.

    No schema change was needed for this: `track` is already generic and
    studio/emit.py already routes audio-asset edits by lane index.
    """
    if not audio_paths:
        raise EditError("no stems given")
    if first_track < MUSIC_TRACK:
        raise EditError(
            f"first-track {first_track} would collide with the voice on A1; "
            f"stems start at A{MUSIC_TRACK}"
        )
    ids = []
    for offset, path in enumerate(audio_paths):
        ir, eid = add_music(ir, path, record=record, src_in=src_in,
                            duration_frames=duration_frames,
                            track=first_track + offset)
        ids.append(eid)
    return ir, ids


def insert_graphic(ir, template, record, duration_frames=None, inputs=None,
                   evidence=None):
    """Place an APPROVED library template instance at `record`.

    Returns (ir, graphic_id). The compiler forges/caches the alpha master
    and overlays it; lint refuses unapproved or unknown templates.
    """
    if record < 0:
        raise EditError(f"record {record} < 0")
    ir = copy.deepcopy(ir)
    gid = _next_id(ir, "gfx")
    g = {"id": gid, "template": template, "record": record}
    if duration_frames is not None:
        if duration_frames < 1:
            raise EditError(f"duration {duration_frames} frames < 1")
        g["duration"] = duration_frames
    if inputs:
        g["inputs"] = dict(inputs)
    if evidence:
        g["evidence"] = list(evidence)
    ir.setdefault("graphics", []).append(g)
    ir["irVersion"] = "0.3"
    return ir, gid


def remove_graphic(ir, graphic_id):
    ir = copy.deepcopy(ir)
    before = len(ir.get("graphics", []))
    ir["graphics"] = [g for g in ir.get("graphics", []) if g["id"] != graphic_id]
    if len(ir["graphics"]) == before:
        raise EditError(f"no graphic {graphic_id!r} in IR {ir['name']!r}")
    if not ir["graphics"]:
        del ir["graphics"]
    return ir


def remove_edit(ir, edit_id):
    ir = copy.deepcopy(ir)
    edit = _find_edit(ir, edit_id)
    ir["edits"].remove(edit)
    # drop the asset too if nothing else references it
    if not any(e["asset"] == edit["asset"] for e in ir["edits"]):
        ir["assets"] = [a for a in ir["assets"] if a["id"] != edit["asset"]]
    return ir


def retime_edit(ir, edit_id, record=None, duration_frames=None):
    """Move an edit and/or change its length (images stretch from srcIn=0)."""
    ir = copy.deepcopy(ir)
    edit = _find_edit(ir, edit_id)
    if record is not None:
        if record < 0:
            raise EditError(f"record {record} < 0")
        edit["record"] = record
    if duration_frames is not None:
        if duration_frames < 1:
            raise EditError(f"duration {duration_frames} frames < 1")
        edit["srcOut"] = edit["srcIn"] + duration_frames
    return ir


def add_marker(ir, frame, color, name, note=""):
    ir = copy.deepcopy(ir)
    marker = {"frame": frame, "color": color, "name": name}
    if note:
        marker["note"] = note
    ir.setdefault("markers", []).append(marker)
    return ir
