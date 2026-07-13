"""Template Library: approved Fusion .setting templates, installed and
populated by agents — never authored onto a timeline unapproved.

Layout (repo, versioned):
    templates/<package>/manifest.json   package manifest
    templates/<package>/<file>.setting  template source (plain-text Lua)

Manifest entry: {"name": "MS ND Headline", "file": "headline.setting",
"version": 1, "approved": false, "inputs": {"StyledText": "headline text"}}.
`approved` flips ONLY after Ryan verdicts a rendered preview (the anti-slop
gate); lint refuses unapproved templates in IR graphics.

Install = copy to the user Fusion Titles folder (filename stem becomes the
library name; Resolve rescans live, ~1s).

Graphics doctrine (settled by smoke 2026-07-12): InsertFusionTitleIntoTimeline
into an occupied timeline RIPPLES V1 (razors + shifts — dead path), and
Resolve's OTIO importer refuses ProRes4444 references. The proven chain is:
**forge** (scratch fps-stamped project: empty timeline -> insert title ->
SetInput populate -> render ProRes4444 + ExportAlpha, cached by content key)
then **place** (ImportMedia -> AddTrack as needed -> AppendToTimeline with
recordFrame/trackIndex; endFrame is EXCLUSIVE). Alpha composites correctly
(verified to pixels). Masters are 150 frames (user still-duration default,
not scriptable) — longer graphics via subrange/loop extension later.
"""
import hashlib
import json
import re
import time
from pathlib import Path

MASTER_FRAMES = 150          # Resolve's default title insert length (5s @ 30)

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
USER_TITLES_DIR = (Path.home() / "Library" / "Application Support" /
                   "Blackmagic Design" / "DaVinci Resolve" / "Fusion" /
                   "Templates" / "Edit" / "Titles")


class TemplateError(ValueError):
    pass


def load_manifests(templates_dir=None):
    """All packages' templates keyed by library name."""
    templates_dir = Path(templates_dir or TEMPLATES_DIR)
    library = {}
    for mf in sorted(templates_dir.glob("*/manifest.json")):
        data = json.loads(mf.read_text(encoding="utf-8"))
        for t in data["templates"]:
            entry = dict(t)
            entry["package"] = data["package"]
            entry["path"] = mf.parent / t["file"]
            if t["name"] in library:
                raise TemplateError(f"duplicate template name {t['name']!r}")
            library[t["name"]] = entry
    return library


def lint_setting(path):
    """Structural gates on a .setting before it may be installed."""
    errors = []
    path = Path(path)
    if not path.is_file():
        return [f"{path}: file missing"]
    text = path.read_text(encoding="utf-8")
    if text.count("{") != text.count("}"):
        errors.append(f"{path.name}: unbalanced braces "
                      f"({text.count('{')} vs {text.count('}')})")
    if not re.search(r"^\s*\{", text):
        errors.append(f"{path.name}: does not open with a Lua table")
    if "Tools = " not in text:
        errors.append(f"{path.name}: no Tools table")
    if not re.search(r"\b(TextPlus|MacroOperator|GroupOperator|Background)\b", text):
        errors.append(f"{path.name}: no recognizable template tool")
    return errors


def install(name, library=None):
    """Lint + copy a template into the user Titles folder. Returns dest."""
    library = library or load_manifests()
    if name not in library:
        raise TemplateError(f"unknown template {name!r}")
    entry = library[name]
    errors = lint_setting(entry["path"])
    if errors:
        raise TemplateError("lint failed:\n" + "\n".join(f"  {e}" for e in errors))
    USER_TITLES_DIR.mkdir(parents=True, exist_ok=True)
    dest = USER_TITLES_DIR / f"{name}.setting"
    dest.write_text(entry["path"].read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def frames_to_tc(frames, fps):
    fps_i = int(round(float(fps)))
    h, rem = divmod(int(frames), 3600 * fps_i)
    m, rem2 = divmod(rem, 60 * fps_i)
    s, f = divmod(rem2, fps_i)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def _populate(item, name, inputs):
    comp = item.GetFusionCompByIndex(1)
    if not comp:
        raise TemplateError(f"graphic {name!r}: no Fusion comp handle")
    tools = comp.GetToolList(False, "TextPlus")
    tool = tools.get(1) if isinstance(tools, dict) else None
    for key, value in (inputs or {}).items():
        if tool is None:
            raise TemplateError(f"graphic {name!r}: no TextPlus to populate")
        tool.SetInput(key, value)
        back = tool.GetInput(key)
        if back != value:
            raise TemplateError(
                f"graphic {name!r}: SetInput({key!r}) readback {back!r}")


def master_key(name, inputs, fps, resolution, version=1):
    canon = json.dumps({"t": name, "i": inputs or {}, "fps": str(fps),
                        "res": [resolution["width"], resolution["height"]],
                        "v": version}, sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def _slug(name):
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")


def render_master(app, name, inputs, fps, resolution, cache_dir,
                  library=None, timeout=180):
    """Render a populated template to a cached ProRes4444+alpha master.

    Returns (path, frames). Idempotent: cache key covers template name +
    version + inputs + fps + resolution. Switches the current Resolve
    project to the forge — callers load their target project AFTER.
    """
    library = library or load_manifests()
    if name not in library:
        raise TemplateError(f"unknown template {name!r}")
    entry = library[name]
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = master_key(name, inputs, fps, resolution, entry.get("version", 1))
    out = cache_dir / f"{_slug(name)}@{key}.mov"
    if out.is_file():
        return out, MASTER_FRAMES

    install(name, library)                       # lint + copy; live rescan
    fps_s = str(int(fps)) if float(fps) == int(fps) else str(float(fps))
    forge_name = f"ms-gfx-forge-{fps_s}x{resolution['width']}"
    pm = app.GetProjectManager()
    proj = pm.LoadProject(forge_name)
    if not proj:
        proj = pm.CreateProject(forge_name)
        if not proj:
            raise TemplateError(f"cannot create forge project {forge_name!r}")
        proj.SetSetting("timelineFrameRate", fps_s)
        proj.SetSetting("timelineResolutionWidth", str(resolution["width"]))
        proj.SetSetting("timelineResolutionHeight", str(resolution["height"]))
        pm.SaveProject()
    mp = proj.GetMediaPool()

    tl = mp.CreateEmptyTimeline(f"g-{key}")
    if not tl:
        raise TemplateError("forge CreateEmptyTimeline failed")
    proj.SetCurrentTimeline(tl)
    deadline = time.time() + 3                   # allow the ~1s library rescan
    item = tl.InsertFusionTitleIntoTimeline(name)
    while not item and time.time() < deadline:
        time.sleep(0.5)
        item = tl.InsertFusionTitleIntoTimeline(name)
    if not item:
        raise TemplateError(f"forge could not insert {name!r} (not scanned?)")
    _populate(item, name, inputs)

    proj.SetCurrentRenderFormatAndCodec("mov", "ProRes4444")
    proj.SetRenderSettings({"TargetDir": str(cache_dir),
                            "CustomName": out.stem, "ExportAlpha": True})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    if not job:
        raise TemplateError("forge AddRenderJob failed twice")
    if not proj.StartRendering([job], isInteractiveMode=False):
        raise TemplateError("forge StartRendering failed")
    t0 = time.time()
    while proj.IsRenderingInProgress():
        if time.time() - t0 > timeout:
            raise TemplateError(f"forge render timeout ({timeout}s)")
        time.sleep(2)
    if proj.GetRenderJobStatus(job).get("JobStatus") != "Complete":
        raise TemplateError(f"forge render: {proj.GetRenderJobStatus(job)}")
    if not out.is_file():
        raise TemplateError(f"forge render produced no file at {out}")
    frames = int(item.GetDuration())
    mp.DeleteTimelines([tl])       # scratch timeline is residue once the
    pm.SaveProject()               # master .mov exists; keep the forge clean
    return out, frames


def place_overlay(proj, timeline, media_path, record, src_in, src_out, track):
    """ImportMedia + AppendToTimeline at exact record/track (endFrame is
    exclusive). Verifies landing. Returns the timeline item."""
    mp = proj.GetMediaPool()
    items = mp.ImportMedia([str(media_path)])
    if not items:
        raise TemplateError(f"media pool refused {media_path}")
    while timeline.GetTrackCount("video") < track:
        if not timeline.AddTrack("video"):
            raise TemplateError("AddTrack failed")
    start = timeline.GetStartFrame()
    placed = mp.AppendToTimeline([{
        "mediaPoolItem": items[0], "startFrame": src_in, "endFrame": src_out,
        "trackIndex": track, "recordFrame": start + record}])
    item = placed[0] if placed else None
    if not item:
        raise TemplateError(f"AppendToTimeline refused {media_path.name} "
                            f"at {record} on V{track}")
    got = item.GetStart() - start
    if got != record or item.GetDuration() != (src_out - src_in):
        raise TemplateError(
            f"overlay landed rec={got} dur={item.GetDuration()}, "
            f"wanted rec={record} dur={src_out - src_in}")
    return item
