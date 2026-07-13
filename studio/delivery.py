"""Delivery fan-out: one timeline -> platform-ready files (Phase 6).

Resolve renders ONE master; everything else derives from it via ffmpeg —
deterministic, fast, and independent of Resolve's render queue quirks.
Fairlight is essentially unscriptable, so loudness lives in ffmpeg too.

Presets (v0):
  master         Resolve H264 mp4 render of the timeline (the source of truth)
  vertical       1080x1920 center-crop of the master (reframing is a human
                 pass later; center-crop is the honest default)
  podcast-audio  m4a, loudnorm to -16 LUFS / -1.5 dBTP (podcast standard)

Every output is verified (ffprobe + loudness when sound is expected) and
recorded in the registry.
"""
import json
import re
import subprocess
import time
from pathlib import Path


class DeliveryError(RuntimeError):
    pass


def _run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise DeliveryError(f"{cmd[0]} failed: {res.stderr[-300:]}")
    return res


def render_master(proj, timeline, out_dir, timeout=600):
    """Render the timeline to <out_dir>/<timeline>-master.mp4 via Resolve."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"{timeline.GetName().replace('@', '-')}-master"
    existing = out_dir / f"{name}.mp4"
    if existing.is_file():
        return existing                       # renders are content-addressed
                                              # via the timeline hash in name
    proj.SetCurrentTimeline(timeline)
    proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
    proj.SetRenderSettings({"TargetDir": str(out_dir), "CustomName": name})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    if not job:
        raise DeliveryError("AddRenderJob failed twice")
    if not proj.StartRendering([job], isInteractiveMode=False):
        raise DeliveryError("StartRendering returned False")
    t0 = time.time()
    while proj.IsRenderingInProgress():
        if time.time() - t0 > timeout:
            raise DeliveryError(f"master render timeout ({timeout}s)")
        time.sleep(2)
    if proj.GetRenderJobStatus(job).get("JobStatus") != "Complete":
        raise DeliveryError(f"master render: {proj.GetRenderJobStatus(job)}")
    outs = sorted(out_dir.glob(name + "*"))
    if not outs:
        raise DeliveryError("master render produced no file")
    return outs[-1]


def derive_vertical(master, out_dir):
    out = Path(out_dir) / (Path(master).stem.replace("-master", "") + "-vertical.mp4")
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(master),
          "-vf", "crop=ih*9/16:ih,scale=1080:1920",
          "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


def derive_podcast_audio(master, out_dir):
    out = Path(out_dir) / (Path(master).stem.replace("-master", "") + "-podcast.m4a")
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(master), "-vn",
          "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
          "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


PRESETS = {
    "vertical": derive_vertical,
    "podcast-audio": derive_podcast_audio,
}


def probe_output(path, expect_audio, expect_video=True):
    """ffprobe + loudness gates. Returns error list."""
    errors = []
    res = _run(["ffprobe", "-v", "error", "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of", "json", str(path)])
    meta = json.loads(res.stdout)
    kinds = {s.get("codec_type") for s in meta.get("streams", [])}
    if expect_video and "video" not in kinds:
        errors.append(f"{Path(path).name}: no video stream")
    if float(meta.get("format", {}).get("duration", 0) or 0) < 0.2:
        errors.append(f"{Path(path).name}: zero-length output")
    if expect_audio:
        if "audio" not in kinds:
            errors.append(f"{Path(path).name}: no audio stream")
        else:
            vol = subprocess.run(
                ["ffmpeg", "-i", str(path), "-map", "0:a", "-af",
                 "volumedetect", "-f", "null", "-"],
                capture_output=True, text=True)
            m = re.search(r"max_volume:\s*(-?[\d.]+)", vol.stderr)
            if m and float(m.group(1)) < -70:
                errors.append(f"{Path(path).name}: audio is silence")
    return errors
