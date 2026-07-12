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

    pm.SaveProject()
    return proj, tl, False
