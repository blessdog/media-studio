"""IR -> editable Resolve timeline, via the proven recipe (docs/STORY-IR.md).

Project-per-IR named {name}@{hash8}. Idempotent: an existing project+timeline
for the same content is reused, not rebuilt.
"""
from . import emit as emitmod
from . import ir as irmod
from .resolve import connect


def _find_timeline(proj, name):
    for i in range(proj.GetTimelineCount()):
        t = proj.GetTimelineByIndex(i + 1)
        if t and t.GetName() == name:
            return t
    return None


def graphics_track(ir):
    """Graphics live on one dedicated track above all edit tracks."""
    return max((e.get("track", 1) for e in ir["edits"]), default=1) + 1


def compile_ir(ir, base_dir, otio_path):
    """Compile `ir` to a timeline. Returns (project, timeline, was_cached)."""
    app = connect()
    pm = app.GetProjectManager()
    proj_name = irmod.timeline_name(ir)          # {name}@{hash8}
    tl_name = proj_name                          # project holds one same-named timeline
    fps = ir["timebase"]["fps"].split("/")[0] if ir["timebase"]["fps"].endswith("/1") \
        else str(float(irmod.fps(ir)))

    # -- idempotence: existing project with the timeline -> reuse -------------
    existing = pm.LoadProject(proj_name)
    if existing:
        tl = _find_timeline(existing, tl_name)
        if tl:
            existing.SetCurrentTimeline(tl)
            return existing, tl, True

    # -- graphics: forge alpha masters FIRST (switches current project) ------
    masters = {}
    if ir.get("graphics"):
        from pathlib import Path
        from . import templates as tmplmod
        library = tmplmod.load_manifests()
        cache = Path(base_dir) / "graphics-cache"
        for g in ir["graphics"]:
            masters[g["id"]] = tmplmod.render_master(
                app, g["template"], g.get("inputs"), float(irmod.fps(ir)),
                ir["resolution"], cache, library)

    # -- fresh project, stamp rate/resolution BEFORE any timeline ------------
    proj = existing or pm.CreateProject(proj_name)
    if not proj:
        raise RuntimeError(f"could not create project {proj_name!r}")
    proj.SetSetting("timelineFrameRate", fps)
    proj.SetSetting("timelineResolutionWidth", str(ir["resolution"]["width"]))
    proj.SetSetting("timelineResolutionHeight", str(ir["resolution"]["height"]))
    pm.SaveProject()

    # -- reload: clears fresh-project import flakiness (spike finding) --------
    pm.CloseProject(proj)
    proj = pm.LoadProject(proj_name)

    # Resolve is a separate process with its own CWD: relative paths in
    # ImportTimelineFromFile fail silently. Absolute, always.
    otio_path = emitmod.emit(ir, base_dir, otio_path).resolve()
    mp = proj.GetMediaPool()
    tl = mp.ImportTimelineFromFile(str(otio_path), {"timelineName": tl_name})
    if not tl:
        raise RuntimeError(
            f"ImportTimelineFromFile failed for {otio_path} "
            f"(project {proj_name}, fps {fps})")

    # -- markers via API (proven path; not carried in the interchange file) --
    start = tl.GetStartFrame()
    for m in ir.get("markers", []):
        tl.AddMarker(start + m["frame"], m["color"], m["name"],
                     m.get("note", ""), m.get("duration", 1))

    # -- graphics: place cached alpha masters as overlays (never via OTIO) ---
    if masters:
        from . import templates as tmplmod
        gtrack = graphics_track(ir)
        for g in sorted(ir["graphics"], key=lambda g: g["record"]):
            path, frames = masters[g["id"]]
            dur = min(g.get("duration", frames), frames)
            tmplmod.place_overlay(proj, tl, path, g["record"], 0, dur, gtrack)

    pm.SaveProject()
    return proj, tl, False
