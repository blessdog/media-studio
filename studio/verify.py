"""Post-compile verification. Trust observed timeline state, never the
compiler's word. Optional render + ffprobe closes the loop to pixels."""
import json
import subprocess
import time
from pathlib import Path

from . import ir as irmod


def verify_timeline(ir, proj, timeline):
    """Structural checks against the imported timeline, every video track —
    edits AND graphics (which live on their own dedicated top track).
    Returns error list."""
    errors = []
    start = timeline.GetStartFrame()
    by_track = {}
    for e in ir["edits"]:
        by_track.setdefault(e.get("track", 1), []).append(
            {"id": e["id"], "record": e["record"],
             "dur": e["srcOut"] - e["srcIn"]})
    if ir.get("graphics"):
        from .compile import graphics_track
        from .templates import MASTER_FRAMES
        gt = graphics_track(ir)
        for g in ir["graphics"]:
            by_track.setdefault(gt, []).append(
                {"id": g["id"], "record": g["record"],
                 "dur": min(g.get("duration", MASTER_FRAMES), MASTER_FRAMES)})

    for track, wants in sorted(by_track.items()):
        items = timeline.GetItemListInTrack("video", track) or []
        if len(items) != len(wants):
            errors.append(
                f"V{track} clip count {len(items)} != IR entries {len(wants)}")
        for it, w in zip(items, sorted(wants, key=lambda w: w["record"])):
            rec = it.GetStart() - start
            dur = it.GetDuration()
            if rec != w["record"]:
                errors.append(f"{w['id']}: record {rec} != IR {w['record']}")
            if dur != w["dur"]:
                errors.append(f"{w['id']}: duration {dur} != IR {w['dur']}")

    got_fps = str(timeline.GetSetting("timelineFrameRate"))
    want_fps = float(irmod.fps(ir))
    if got_fps not in (str(want_fps), str(int(want_fps))):
        errors.append(f"timeline fps {got_fps} != IR {want_fps}")
    return errors


def verify_render(ir, proj, timeline, render_dir):
    """Render the timeline and ffprobe the output. Returns (errors, out_path)."""
    errors = []
    render_dir = Path(render_dir)
    render_dir.mkdir(parents=True, exist_ok=True)
    proj.SetCurrentTimeline(timeline)
    proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
    name = f"verify-{int(time.time())}"
    proj.SetRenderSettings({"TargetDir": str(render_dir), "CustomName": name})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    if not job:
        return ["AddRenderJob failed twice"], None
    if not proj.StartRendering([job], isInteractiveMode=False):
        return ["StartRendering returned False"], None
    t0 = time.time()
    while proj.IsRenderingInProgress():
        if time.time() - t0 > 300:
            return ["render timeout (300s)"], None
        time.sleep(2)
    if proj.GetRenderJobStatus(job).get("JobStatus") != "Complete":
        return [f"render not complete: {proj.GetRenderJobStatus(job)}"], None

    outs = sorted(render_dir.glob(name + "*"))
    if not outs:
        return ["render produced no file"], None
    out = outs[-1]

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height", "-of", "json", str(out)],
        capture_output=True, text=True)
    meta = json.loads(probe.stdout)
    fps = float(irmod.fps(ir))
    want_dur = irmod.extent_frames(ir) / fps
    got_dur = float(meta.get("format", {}).get("duration", 0) or 0)
    if abs(got_dur - want_dur) > 1.0 / fps + 0.05:
        errors.append(f"render duration {got_dur:.3f}s != IR extent {want_dur:.3f}s")
    vstream = next((s for s in meta.get("streams", []) if s.get("width")), {})
    if vstream.get("width") != ir["resolution"]["width"] or \
       vstream.get("height") != ir["resolution"]["height"]:
        errors.append(
            f"render {vstream.get('width')}x{vstream.get('height')} != IR "
            f"{ir['resolution']['width']}x{ir['resolution']['height']}")
    return errors, str(out)
