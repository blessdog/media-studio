"""Deterministic IR gates. Nothing touches Resolve until this passes.

Returns a list of error strings (empty = green). ffprobe is the ground truth
for asset bounds — never trust the IR's own claims about its media.
"""
import hashlib
import json
import subprocess

from . import ir as irmod


def _ffprobe(path):
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,r_frame_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return None
    return json.loads(res.stdout)


def _sha256(path, limit_mb=512):
    if path.stat().st_size > limit_mb * 1024 * 1024:
        return None  # skip hashing huge media; presence+probe still gate it
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lint(ir, base_dir):
    errors = []
    fps = irmod.fps(ir)
    if fps <= 0:
        errors.append(f"timebase.fps {ir['timebase']['fps']} is not positive")
    if fps.denominator == 1001:
        errors.append(f"warning: drop-frame-ish rate {fps} — v0.1 has no NDF/DF handling; proceed knowingly")

    assets = {}
    for a in ir["assets"]:
        if a["id"] in assets:
            errors.append(f"asset id {a['id']!r} duplicated")
            continue
        assets[a["id"]] = a
        p = irmod.asset_path(a, base_dir)
        if not p.is_file():
            errors.append(f"asset {a['id']}: file missing: {p}")
            continue
        probe = _ffprobe(p)
        if probe is None:
            errors.append(f"asset {a['id']}: ffprobe cannot read {p}")
            continue
        dur = float(probe.get("format", {}).get("duration", 0) or 0)
        a["_frames"] = int(dur * fps) if a["kind"] != "image" else None
        a["_hasAudio"] = any(s.get("codec_type") == "audio"
                             for s in probe.get("streams", []))
        if a.get("sha256"):
            actual = _sha256(p)
            if actual and actual != a["sha256"]:
                errors.append(f"asset {a['id']}: sha256 mismatch (file changed since IR was written)")

    edit_ids = set()
    by_track = {}
    for e in ir["edits"]:
        eid = e["id"]
        if eid in edit_ids:
            errors.append(f"edit id {eid!r} duplicated")
        edit_ids.add(eid)
        if e["asset"] not in assets:
            errors.append(f"edit {eid}: references unknown asset {e['asset']!r}")
            continue
        if e["srcIn"] >= e["srcOut"]:
            errors.append(f"edit {eid}: srcIn {e['srcIn']} >= srcOut {e['srcOut']}")
            continue
        frames = assets[e["asset"]].get("_frames")
        if frames is not None and e["srcOut"] > frames:
            errors.append(
                f"edit {eid}: srcOut {e['srcOut']} beyond asset {e['asset']} "
                f"length (~{frames} frames @ {fps} fps)")
        lane = "audio" if assets[e["asset"]]["kind"] == "audio" else "video"
        track = e.get("track", 1)
        by_track.setdefault((lane, track), []).append(
            (e["record"], e["record"] + e["srcOut"] - e["srcIn"], eid))

    for (lane, track), spans in by_track.items():
        spans.sort()
        for (s1, e1, id1), (s2, e2, id2) in zip(spans, spans[1:]):
            if s2 < e1:
                errors.append(
                    f"{lane} track {track}: edits {id1} and {id2} overlap "
                    f"({s2} < {e1})")

    _lint_graphics(ir, errors)

    return [e for e in errors if not e.startswith("warning:")], \
           [e for e in errors if e.startswith("warning:")]


def _lint_graphics(ir, errors):
    """Graphics gates: approved templates only, known inputs, no overlaps."""
    graphics = ir.get("graphics", [])
    if not graphics:
        return
    from . import templates as tmplmod
    try:
        library = tmplmod.load_manifests()
    except Exception as e:
        errors.append(f"graphics: cannot load template library: {e}")
        return
    extent = irmod.extent_frames(ir)
    seen, spans = set(), []
    for g in graphics:
        if g["id"] in seen:
            errors.append(f"graphic id {g['id']!r} duplicated")
        seen.add(g["id"])
        entry = library.get(g["template"])
        if not entry:
            errors.append(f"graphic {g['id']}: unknown template {g['template']!r}")
            continue
        if not entry.get("approved"):
            errors.append(
                f"graphic {g['id']}: template {g['template']!r} is NOT "
                "approved — Ryan's eyes gate library entry")
        unknown = set(g.get("inputs", {})) - set(entry.get("inputs", {}))
        if unknown:
            errors.append(f"graphic {g['id']}: unknown inputs {sorted(unknown)} "
                          f"(published: {sorted(entry.get('inputs', {}))})")
        if g["record"] >= extent:
            errors.append(f"graphic {g['id']}: record {g['record']} beyond "
                          f"timeline extent {extent}")
        dur = min(g.get("duration", tmplmod.MASTER_FRAMES), tmplmod.MASTER_FRAMES)
        if g.get("duration", 0) > tmplmod.MASTER_FRAMES:
            errors.append(f"warning: graphic {g['id']}: duration "
                          f"{g['duration']} capped at {tmplmod.MASTER_FRAMES} "
                          "(alpha-master limit in v0)")
        spans.append((g["record"], g["record"] + dur, g["id"]))
    spans.sort()
    for (s1, e1, id1), (s2, e2, id2) in zip(spans, spans[1:]):
        if s2 < e1:
            errors.append(f"graphics track: {id1} and {id2} overlap ({s2} < {e1})")
