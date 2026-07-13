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
    used = {e["id"] for e in ir["edits"]} | {a["id"] for a in ir["assets"]}
    n = 0
    while f"{prefix}{n}" in used:
        n += 1
    return f"{prefix}{n}"


def _find_edit(ir, edit_id):
    for e in ir["edits"]:
        if e["id"] == edit_id:
            return e
    raise EditError(f"no edit {edit_id!r} in IR {ir['name']!r}")


def add_image_asset(ir, path):
    """Register an image asset (idempotent by absolute path). Returns (ir, id)."""
    ir = copy.deepcopy(ir)
    path = str(Path(path).resolve())
    for a in ir["assets"]:
        if a["kind"] == "image" and str(Path(a["path"])) == path:
            return ir, a["id"]
    aid = _next_id(ir, "img")
    ir["assets"].append({"id": aid, "path": path, "kind": "image"})
    ir["irVersion"] = "0.2"
    return ir, aid


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
