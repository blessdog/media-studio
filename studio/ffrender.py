"""Story IR -> mp4 with ffmpeg alone, locally or on the Mac mini.

Resolve is the editor; it is not the only thing that can render a spine of
straight cuts. For a timeline that is only track-1 edits (every ingest and
session workspace is), the render is trims + concat, which ffmpeg does with
bounded memory on any machine. That is what lets the render leave the
MacBook: the mini (8 GB, no Resolve, ffmpeg 8) can do it, Resolve cannot go
there (docs/journal 2026-09-07).

Shape of the job:

  plan     track-1 edits, in record order, grouped into RUNS of consecutive
           edits from the same asset. One run = one staged file = one encode.
  stage    per run, a keyframe-padded stream copy of the source window with
           timestamps preserved (-copyts), so a seek on the staged file lands
           on the same frame as on the original (measured 2026-09-07: same
           frame within one frame, offset = staged format start_time).
  encode   per run, one ffmpeg: split/trim/concat of that run's edits ->
           runNNN.mp4 (x264, aac). Runs are monotonic in source time, so the
           filter graph never buffers more than a few frames.
  concat   the concat demuxer over the run files, stream copy.

Remote mode ships stage/ + a shell script to the mini with rsync, runs it
under tmux at nice 10 with a disk-space precondition, polls, and pulls the
result back. Nothing on the mini is touched except ~/render/<name>/, which
is removed afterwards.
"""
import json
import shlex
import subprocess
import time
from pathlib import Path

from . import ir as irmod

PAD_SECONDS = 2.5           # > one OBS GOP (measured 1.97 s), so the keyframe before the window is inside the copy
REMOTE_ROOT = "render"      # under $HOME on the mini
DISK_MARGIN_GB = 2.0
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-r", "30", "-video_track_timescale", "30000"]
AAC = ["-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]


class RenderError(RuntimeError):
    pass


def _run(cmd, **kw):
    res = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if res.returncode != 0:
        raise RenderError(f"{cmd[0]} failed: {res.stderr[-400:]}")
    return res


def _probe(path, entry):
    res = _run(["ffprobe", "-v", "error", "-show_entries", entry, "-of", "json", str(path)])
    return json.loads(res.stdout)


def plan(ir, base_dir):
    """Track-1 edits in record order -> runs of (asset path, [(start_s, dur_s)])."""
    fps = irmod.fps(ir)
    assets = {a["id"]: irmod.asset_path(a, base_dir) for a in ir["assets"]}
    edits = sorted((e for e in ir["edits"] if e.get("track", 1) == 1),
                   key=lambda e: e["record"])
    if not edits:
        raise RenderError("no track-1 edits to render")
    runs = []
    for e in edits:
        seg = (e["srcIn"] / fps, (e["srcOut"] - e["srcIn"]) / fps)
        if runs and runs[-1]["asset"] == e["asset"] and e["srcIn"] >= runs[-1]["last_out"]:
            runs[-1]["segs"].append(seg)
        else:
            runs.append({"asset": e["asset"], "path": str(assets[e["asset"]]), "segs": [seg]})
        runs[-1]["last_out"] = e["srcOut"]
    for r in runs:
        r.pop("last_out")
        r["window"] = (max(0.0, float(r["segs"][0][0]) - PAD_SECONDS),
                       float(r["segs"][-1][0] + r["segs"][-1][1]) + PAD_SECONDS)
    return runs


def stage(runs, stage_dir):
    """Stream-copy each run's padded window, timestamps preserved. Fills in
    run['file'] and run['origin'] (the staged file's start_time). Cheap: no
    decode, no encode, one video + one audio stream."""
    stage_dir = Path(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(runs):
        out = stage_dir / f"run{i:03d}.mp4"
        w0, w1 = r["window"]
        if not out.is_file() or out.stat().st_size < 4096:
            # -to, never -t: with -copyts the clock is the SOURCE clock, so a
            # -t shorter than the window's start stops before the first packet
            # (measured: a 262-byte file for a window at 1605 s).
            _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{w0:.3f}", "-i", r["path"],
                  "-to", f"{w1:.3f}", "-map", "0:v:0", "-map", "0:a:0",
                  "-c", "copy", "-copyts", str(out)])
        fmt = _probe(out, "format=start_time,duration")["format"]
        if "start_time" not in fmt or out.stat().st_size < 4096:
            raise RenderError(f"staging {out.name} produced no media for window {w0:.1f}-{w1:.1f}s of {r['path']}")
        r["file"] = out.name
        r["origin"] = float(fmt["start_time"])
    return runs


def _encode_cmd(run, in_path, out_path, origin):
    """One ffmpeg for one run: trims relative to `origin`, concat, encode."""
    n = len(run["segs"])
    parts = [f"[0:v]split={n}" + "".join(f"[v{k}]" for k in range(n)),
             f"[0:a]asplit={n}" + "".join(f"[a{k}]" for k in range(n))]
    for k, (s, d) in enumerate(run["segs"]):
        # start/end at 6 decimals, never duration at 4: 0.966667 rounded to
        # 0.9667 lands past the frame at 29000/30000 and trim keeps it, one
        # extra frame per segment (measured: 21 frames over 56 segments).
        ss, ee = float(s) - origin, float(s + d) - origin
        parts.append(f"[v{k}]trim=start={ss:.6f}:end={ee:.6f},setpts=PTS-STARTPTS[tv{k}]")
        parts.append(f"[a{k}]atrim=start={ss:.6f}:end={ee:.6f},asetpts=PTS-STARTPTS[ta{k}]")
    parts.append("".join(f"[tv{k}][ta{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
    return (["ffmpeg", "-y", "-v", "error", "-i", str(in_path), "-filter_complex",
             ";".join(parts), "-map", "[v]", "-map", "[a]"] + X264 + AAC + [str(out_path)])


def write_script(runs, work_dir, out_name, staged=True):
    """A self-contained zsh script that encodes every run then concats.
    `staged`: inputs are the staged files in ./stage (origin-relative);
    otherwise the original assets (origin 0)."""
    lines = ["#!/bin/zsh", "set -e", f"cd {shlex.quote(str(work_dir))}" if work_dir else "",
             "mkdir -p enc", ": > concat.txt"]
    for i, r in enumerate(runs):
        src = f"stage/{r['file']}" if staged else r["path"]
        origin = r["origin"] if staged else 0.0
        cmd = _encode_cmd(r, src, f"enc/run{i:03d}.mp4", origin)
        lines.append(f"echo run {i}/{len(runs)} >&2")
        lines.append(" ".join(shlex.quote(c) for c in cmd))
        lines.append(f"echo \"file 'enc/run{i:03d}.mp4'\" >> concat.txt")
        if staged:
            lines.append(f"rm -f stage/{r['file']}")   # peak disk = stage + enc, not stage + enc + final
    lines.append(f"ffmpeg -y -v error -f concat -safe 0 -i concat.txt -c copy {shlex.quote(out_name)}")
    lines.append("echo DONE >&2")
    return "\n".join(lines) + "\n"


def verify(ir, out_path):
    """Duration against the IR extent, and ears if the IR implies sound."""
    errors = []
    meta = _probe(out_path, "format=duration:stream=width,height,codec_type")
    fps = float(irmod.fps(ir))
    want = irmod.extent_frames(ir) / fps
    got = float(meta["format"]["duration"])
    if abs(got - want) > 1.0 / fps + 0.25:
        errors.append(f"render duration {got:.3f}s != IR extent {want:.3f}s")
    v = next((s for s in meta["streams"] if s.get("width")), {})
    if (v.get("width"), v.get("height")) != (ir["resolution"]["width"], ir["resolution"]["height"]):
        errors.append(f"render {v.get('width')}x{v.get('height')} != IR {ir['resolution']}")
    vol = subprocess.run(["ffmpeg", "-i", str(out_path), "-map", "0:a?", "-af", "volumedetect",
                          "-f", "null", "-"], capture_output=True, text=True)
    import re
    m = re.search(r"max_volume:\s*(-?[\d.]+)", vol.stderr)
    if m is None:
        errors.append("render has no audio stream")
    elif float(m.group(1)) < -70:
        errors.append(f"render audio is silence (max {m.group(1)} dB)")
    return errors


def render_local(ir, base_dir, work_dir, out_path):
    runs = plan(ir, base_dir)
    for r in runs:
        r["origin"] = 0.0
    script = Path(work_dir) / "render-local.sh"
    script.write_text(write_script(runs, work_dir, str(out_path), staged=False))
    _run(["zsh", str(script)])
    return runs


# ---------------------------------------------------------------- remote ---

def _ssh(host, cmd, timeout=120):
    return _run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host,
                 f"zsh -lc {shlex.quote(cmd)}"], timeout=timeout)


def remote_free_gb(host):
    out = _ssh(host, "df -k $HOME | tail -1").stdout.split()
    return int(out[3]) / (1024 * 1024)


def render_remote(ir, base_dir, work_dir, out_path, host="mini", name=None, log=print):
    work_dir = Path(work_dir)
    name = name or ir["name"]
    runs = stage(plan(ir, base_dir), work_dir / "stage")
    stage_bytes = sum((work_dir / "stage" / r["file"]).stat().st_size for r in runs)
    # staged files are removed as each run encodes, so the peak is the stage
    # itself plus the encoded runs (~0.3x at crf 20) plus the concat copy
    need_gb = stage_bytes / 1e9 * 1.6 + DISK_MARGIN_GB
    free_gb = remote_free_gb(host)
    log(f"stage: {len(runs)} runs, {stage_bytes / 1e9:.2f} GB; {host} has {free_gb:.1f} GB free, "
        f"needs {need_gb:.1f}")
    if free_gb < need_gb:
        raise RenderError(f"{host} has {free_gb:.1f} GB free, render needs ~{need_gb:.1f} GB — refusing")

    remote_dir = f"{REMOTE_ROOT}/{name}"
    script = work_dir / "render-remote.sh"
    script.write_text(write_script(runs, None, f"{name}.mp4", staged=True))
    _ssh(host, f"mkdir -p ~/{remote_dir}")
    t0 = time.time()
    _run(["rsync", "-a", "--partial", str(work_dir / "stage"), str(script),
          f"{host}:{remote_dir}/"], timeout=3600)
    log(f"shipped in {time.time() - t0:.0f}s")

    _ssh(host, f"cd ~/{remote_dir} && rm -f DONE FAILED && tmux new-session -d -s render-{name} "
               f"'(nice -n 10 zsh render-remote.sh > render.log 2>&1 && touch DONE) || touch FAILED'")
    t0 = time.time()
    while True:
        time.sleep(15)
        state = _ssh(host, f"cd ~/{remote_dir} && ls DONE FAILED 2>/dev/null; tail -1 render.log").stdout
        if "DONE" in state.split():
            break
        if "FAILED" in state.split():
            tail = _ssh(host, f"tail -20 ~/{remote_dir}/render.log").stdout
            raise RenderError(f"remote render failed:\n{tail}")
        log(f"  {host}: {state.strip().splitlines()[-1] if state.strip() else '...'}  ({time.time() - t0:.0f}s)")
    log(f"encoded on {host} in {time.time() - t0:.0f}s")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    _run(["rsync", "-a", "--partial", f"{host}:{remote_dir}/{name}.mp4", str(out_path)], timeout=3600)
    _ssh(host, f"rm -rf ~/{remote_dir}")     # only the directory this call created
    return runs
