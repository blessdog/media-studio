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
    assets = {a["id"]: a for a in ir["assets"]}
    by_track = {}
    for e in ir["edits"]:
        if assets[e["asset"]]["kind"] == "audio":
            continue                      # audio lane is verified below
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

    # -- audio lanes: A1 mirrors track-1 video edits; audio assets by track --
    audio_by_track = {}
    for e in ir["edits"]:
        kind = assets[e["asset"]]["kind"]
        entry = {"id": e["id"], "record": e["record"],
                 "dur": e["srcOut"] - e["srcIn"]}
        if kind == "audio":
            audio_by_track.setdefault(e.get("track", 1), []).append(entry)
        elif kind == "video" and e.get("track", 1) == 1 and \
                assets[e["asset"]].get("_hasAudio", True):
            audio_by_track.setdefault(1, []).append(entry)
    for track, wants in sorted(audio_by_track.items()):
        items = timeline.GetItemListInTrack("audio", track) or []
        # graphics masters are video-only; nothing else should stray here
        if len(items) != len(wants):
            errors.append(
                f"A{track} clip count {len(items)} != IR entries {len(wants)}")
        for it, w in zip(items, sorted(wants, key=lambda w: w["record"])):
            rec = it.GetStart() - start
            if rec != w["record"]:
                errors.append(f"audio {w['id']}: record {rec} != IR {w['record']}")
            if it.GetDuration() != w["dur"]:
                errors.append(f"audio {w['id']}: duration {it.GetDuration()} "
                              f"!= IR {w['dur']}")
    got_fps = str(timeline.GetSetting("timelineFrameRate"))
    want_fps = float(irmod.fps(ir))
    if got_fps not in (str(want_fps), str(int(want_fps))):
        errors.append(f"timeline fps {got_fps} != IR {want_fps}")
    return errors


def expects_audio(ir):
    """Does this IR imply audible output?"""
    assets = {a["id"]: a for a in ir["assets"]}
    return any(
        assets[e["asset"]]["kind"] == "audio"
        or (assets[e["asset"]]["kind"] == "video" and e.get("track", 1) == 1
            and assets[e["asset"]].get("_hasAudio", True))
        for e in ir["edits"])


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

    # -- ears: if the IR implies sound, the render must not be silence -------
    if expects_audio(ir):
        vol = subprocess.run(
            ["ffmpeg", "-i", str(out), "-map", "0:a?", "-af", "volumedetect",
             "-f", "null", "-"], capture_output=True, text=True)
        import re
        m = re.search(r"max_volume:\s*(-?[\d.]+)", vol.stderr)
        if m is None:
            errors.append("render has NO audio stream but IR implies sound")
        elif float(m.group(1)) < -70:
            errors.append(
                f"render audio is silence (max {m.group(1)} dB) but IR "
                "implies sound — the mute-timeline bug")
    return errors, str(out)
