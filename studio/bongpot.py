"""Bongpot adapter: video-plan.json (LPC prank lane) -> Story IR (Phase 6).

ONE-WAY: reads a bongpot call workspace, never writes into it. Bongpot's
FFmpeg assembly (tools/sequence-video.mjs over there) stays the production
path; this builds the OPTIONAL Resolve finishing timeline its doctrine
reserved ("manual finishing via a real external editor").

Plan facts (verified against bongpot outputs/clown-motel, 2026-07-13):
- cut.shots: contiguous [start, end) SECONDS, id like "s01", speaker,
  function/device/intent, review verdicts {stage: {status, at}}.
- Clips are <shotId>.mp4 (Wan i2v, 832x480@16fps) and often run SHORT of
  their window (Wan rounds to its own frame grid) -> normalize like
  bongpot's own assembler: scale/crop to target, retime to timeline fps,
  clone-pad the last frame to the exact shot duration, STRIP audio.
- The call audio is sacred (speaker attribution doctrine): placed ONCE,
  untouched, on A1 for the whole window. Normalized clips carry no audio,
  so the emit A1 mirror never competes with it.
"""
import json
import subprocess
from fractions import Fraction
from pathlib import Path

VERDICT_COLORS = {"reject": "Red", "rework": "Yellow", "approved": "Green"}
NO_VERDICT_COLOR = "Sky"
MISSING_COLOR = "Red"


class BongpotError(RuntimeError):
    pass


def load_plan(plan_path):
    """Read a bongpot video-plan.json; return its cut.shots (validated)."""
    plan_path = Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    shots = (plan.get("cut") or {}).get("shots")
    if not shots:
        raise BongpotError(f"{plan_path.name}: no cut.shots — not a brain plan")
    for a, b in zip(shots, shots[1:]):
        if abs(a["end"] - b["start"]) > 1e-6:
            raise BongpotError(
                f"shots {a['id']}/{b['id']} not contiguous "
                f"({a['end']} != {b['start']}) — the timing contract is broken")
    return plan, shots


def find_audio(plan_path):
    """The call mp3 from ear.json in the same workspace (bongpot's own
    ground-truth record of what was transcribed/analyzed)."""
    ear = Path(plan_path).parent / "ear.json"
    if not ear.is_file():
        return None
    meta = json.loads(ear.read_text(encoding="utf-8")).get("meta", {})
    audio = meta.get("audio")
    return Path(audio) if audio and Path(audio).is_file() else None


def shot_grid(shots, fps):
    """Seconds -> frame grid. Boundaries are rounded ONCE (never per-shot
    durations) so rounding can't accumulate drift off the call audio.
    Returns [{'id', 'record', 'frames', 'shot'}]; record 0 = window start."""
    fps = Fraction(fps)
    w0 = shots[0]["start"]
    bounds = [int(round((s["start"] - w0) * fps)) for s in shots]
    bounds.append(int(round((shots[-1]["end"] - w0) * fps)))
    grid = []
    for i, s in enumerate(shots):
        frames = bounds[i + 1] - bounds[i]
        if frames <= 0:
            raise BongpotError(f"shot {s['id']}: zero frames at {fps} fps "
                               f"({s['start']}-{s['end']}s)")
        grid.append({"id": s["id"], "record": bounds[i],
                     "frames": frames, "shot": s})
    return grid


def normalize_clip(src, dst, frames, fps, width, height):
    """Conform one shot clip to the timeline grid (bongpot-assembler recipe):
    scale/crop to WxH, retime to fps, clone-pad the last frame past the shot
    window, cut at exactly `frames`, strip audio. Cached: skips when dst is
    newer than src."""
    src, dst = Path(src), Path(dst)
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    fps = Fraction(fps)
    pad_s = float(frames / fps) + 1.0  # always enough; -frames:v cuts exact
    vf = (f"scale={width}:{height}:force_original_aspect_ratio=increase,"
          f"crop={width}:{height},fps={fps.numerator}/{fps.denominator},"
          f"setsar=1,tpad=stop_mode=clone:stop_duration={pad_s:.3f}")
    res = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf,
         "-frames:v", str(frames), "-an",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(dst)],
        capture_output=True, text=True)
    if res.returncode != 0 or not dst.is_file():
        raise BongpotError(f"normalize {src.name}: {res.stderr[-300:]}")
    return True


def _verdicts(shot):
    return {k: v.get("status") for k, v in (shot.get("review") or {}).items()}


def _marker_color(verdicts):
    for status in ("reject", "rework", "approved"):
        if status in verdicts.values():
            return VERDICT_COLORS[status]
    return NO_VERDICT_COLOR


def _marker_note(shot, verdicts):
    bits = []
    if verdicts:
        bits.append(" ".join(f"{k}:{v}" for k, v in sorted(verdicts.items())))
    if shot.get("function"):
        bits.append(shot["function"])
    if shot.get("intent"):
        bits.append(shot["intent"])
    return " | ".join(bits)[:180]


def build_ir(name, grid, clip_rels, audio_rel, audio_src_in, audio_frames,
             timebase, width, height):
    """Assemble the finishing-timeline IR. grid from shot_grid(); clip_rels
    maps shot id -> IR-relative clip path (absent = missing clip -> V1 gap +
    red MISSING marker); the untouched call audio spans the window on A1."""
    assets = [{"id": "call", "path": str(audio_rel), "kind": "audio"}]
    edits = [{"id": "a-call", "asset": "call", "srcIn": audio_src_in,
              "srcOut": audio_src_in + audio_frames, "record": 0, "track": 1}]
    markers = []
    for g in grid:
        shot, verdicts = g["shot"], _verdicts(g["shot"])
        if g["id"] in clip_rels:
            assets.append({"id": g["id"], "path": str(clip_rels[g["id"]]),
                           "kind": "video"})
            edits.append({"id": f"e-{g['id']}", "asset": g["id"], "srcIn": 0,
                          "srcOut": g["frames"], "record": g["record"],
                          "track": 1})
            name_bits = [g["id"], shot.get("speaker") or ""]
            markers.append({"frame": g["record"],
                            "color": _marker_color(verdicts),
                            "name": " ".join(b for b in name_bits if b),
                            "note": _marker_note(shot, verdicts)})
        else:
            markers.append({"frame": g["record"], "color": MISSING_COLOR,
                            "name": f"MISSING {g['id']}",
                            "note": _marker_note(shot, verdicts)})
    return {
        "irVersion": "0.1",
        "name": name,
        "timebase": {"fps": timebase},
        "resolution": {"width": width, "height": height},
        "assets": assets,
        "edits": edits,
        "markers": markers,
        "provenance": {"generator": "bongpot-adapter-v0",
                       "createdBy": "ingest-bongpot"},
    }
