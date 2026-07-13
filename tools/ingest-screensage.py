#!/usr/bin/env python3
"""Rebuild a ScreenSage Pro bundle as an editable multitrack timeline.

    .venv/bin/python tools/ingest-screensage.py <bundle.screensage>
        [--name N] [--no-transcribe] [--render]

A .screensage bundle records screen, camera, and mic as SEPARATE SYNCED
tracks plus interaction-event JSON. This verb:
  1. picks the voice source by measured loudness (mic is often silent —
     Ryan's mic usually routes to OBS),
  2. muxes screen video + voice into <ws>/recording.mp4 (stream copy),
  3. runs the standard ingest lane (silence spans -> Deepgram -> IR),
  4. registers the camera track as a cut-in asset (reference in place),
  5. maps ScreenSage's click events + auto-zoom ranges onto the CUT
     timeline as markers (machine-readable editing hints),
  6. lint -> compile -> verify -> shows the timeline in Resolve.
"""
import argparse
import json
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ingest as ingestmod
from studio import lint as lintmod
from studio import moments as momentsmod
from studio import probe as probemod
from studio import registry as regmod
from studio import silence as silencemod

ROOT = Path(__file__).resolve().parent.parent


def mean_volume(path, map_spec="0:a"):
    res = subprocess.run(
        ["ffmpeg", "-i", str(path), "-map", map_spec, "-af", "volumedetect",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"mean_volume:\s*(-?[\d.]+)", res.stderr)
    return float(m.group(1)) if m else None


def is_vfr(path):
    """Screen captures are usually variable-frame-rate — poison for the
    frame-integer model. Detect via avg vs nominal rate divergence."""
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=avg_frame_rate,r_frame_rate", "-of", "json", str(path)],
        capture_output=True, text=True)
    s = json.loads(res.stdout)["streams"][0]
    avg, nom = Fraction(s["avg_frame_rate"]), Fraction(s["r_frame_rate"])
    return abs(float(avg) - float(nom)) > 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--name")
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    bundle = Path(args.bundle).expanduser().resolve()
    rec_dir = bundle / "recording"
    display = rec_dir / "display-0.mov"
    camera = rec_dir / "camera-0.mov"
    mic = rec_dir / "microphone-0.m4a"
    if not display.is_file():
        print(f"FAIL: no display-0.mov in {bundle}")
        return 1

    name = args.name or bundle.stem.lower().replace(" ", "-").replace("_", "-")
    name = re.sub(r"[^a-z0-9-]", "", name)[:48].strip("-")
    ws = ROOT / "outputs" / "projects" / name
    ws.mkdir(parents=True, exist_ok=True)

    # -- voice pick by measured loudness (never assume routing) --------------
    vol_mic = mean_volume(mic) if mic.is_file() else None
    vol_disp = mean_volume(display)
    use_mic = vol_mic is not None and (vol_disp is None or vol_mic >= vol_disp)
    print(f"voice pick: mic={vol_mic} dB, display={vol_disp} dB "
          f"-> {'microphone' if use_mic else 'display audio'}")

    # -- mux screen video + chosen voice; normalize VFR captures to CFR ------
    muxed = ws / "recording.mp4"
    if not muxed.is_file():
        vfr = is_vfr(display)
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(display)]
        if use_mic:
            cmd += ["-i", str(mic), "-map", "0:v", "-map", "1:a"]
        else:
            cmd += ["-map", "0:v", "-map", "0:a"]
        if vfr:
            cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-r", "30", "-fps_mode", "cfr", "-pix_fmt", "yuv420p",
                    "-c:a", "copy"]
        else:
            cmd += ["-c", "copy"]
        cmd += [str(muxed)]
        subprocess.run(cmd, check=True)
        print(f"muxed: {muxed.name}{' (VFR -> CFR 30)' if vfr else ''}")

    # -- standard ingest lane -------------------------------------------------
    meta = probemod.probe(muxed)
    print(f"probe: {meta['width']}x{meta['height']} @ {meta['fps']} fps, "
          f"{meta['duration']:.1f}s")
    reg = regmod.connect()
    regmod.record_asset(reg, muxed, kind="video", probe=meta)

    timebase, spans = silencemod.loud_spans(muxed)
    print(f"silence analysis: {len(spans)} kept spans")

    transcript = None
    if not args.no_transcribe:
        from studio import transcribe as tmod
        try:
            transcript = tmod.transcribe(muxed, ws / "transcript.json")
            print(f"transcript: {len(transcript['utterances'])} utterances")
            regmod.record_transcript(reg, muxed, transcript, ws / "transcript.json")
        except tmod.TranscribeError as e:
            print(f"transcribe skipped: {e}")

    ir = ingestmod.build_ir(name, muxed, meta, timebase, spans, transcript,
                            created_by="ingest-screensage")

    # -- camera track: register as cut-in asset (space-free hardlink; the
    # bundle's own directories contain spaces, which break OTIO import) ------
    if camera.is_file():
        from studio import intake as intakemod
        cam_safe = intakemod.resolve_safe(camera, ws / "media")
        cam_meta = probemod.probe(cam_safe)
        regmod.record_asset(reg, cam_safe, kind="video", probe=cam_meta)
        ir["assets"].append({"id": "camera", "path": str(cam_safe), "kind": "video"})
        print(f"camera cut-in asset registered: {camera.name} "
              f"({cam_meta['width']}x{cam_meta['height']} @ {cam_meta['fps']})")

    # -- interaction events -> markers on the CUT timeline -------------------
    fps = Fraction(timebase)
    added = 0
    clicks = rec_dir / "click_events.json"
    if clicks.is_file():
        downs = [e for e in json.loads(clicks.read_text(encoding="utf-8"))
                 if e.get("type") == "leftMouseDown"]
        for e in downs:
            rec = momentsmod.src_to_record(
                int(round(e["timeOffset"] * fps)), spans)
            if rec is None:
                continue
            x, y = e.get("location", [0, 0])
            ir.setdefault("markers", []).append(
                {"frame": rec, "color": "Cyan", "name": "click",
                 "note": f"ScreenSage click at ({x:.2f}, {y:.2f})"})
            added += 1
    proj_json = bundle / "project.json"
    if proj_json.is_file():
        data = json.loads(proj_json.read_text(encoding="utf-8"))
        for sess in data.get("sessions", []):
            for z in sess.get("zoomRanges", []):
                rec = momentsmod.src_to_record(
                    int(round(z["startTime"] * fps)), spans)
                if rec is None:
                    continue
                ir.setdefault("markers", []).append(
                    {"frame": rec, "color": "Purple", "name": "ss-zoom",
                     "note": f"ScreenSage auto-zoom x{z.get('zoom')} until "
                             f"{z.get('endTime'):.1f}s (source)"})
                added += 1
    print(f"interaction markers: {added}")

    ir_path = ws / "story.json"
    ir_path.write_text(json.dumps(ir, indent=1), encoding="utf-8")
    regmod.record_ir(reg, ir, ir_path)
    print(f"IR written: {ir_path}")

    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("lint: green")

    from studio import compile as compmod
    from studio import verify as verifymod
    proj, tl, cached = compmod.compile_ir(ir, ws, ws / "story.otio")
    verrs = verifymod.verify_timeline(ir, proj, tl)
    if verrs:
        print("VERIFY FAIL:")
        for e in verrs:
            print(f"  {e}")
        return 1
    proj.SetCurrentTimeline(tl)
    print(f"{'reused' if cached else 'compiled'} + showing '{tl.GetName()}'")
    if args.render:
        rerrs, out = verifymod.verify_render(ir, proj, tl, ws / "render")
        if rerrs:
            print("VERIFY FAIL (render):")
            for e in rerrs:
                print(f"  {e}")
            return 1
        regmod.record_render(reg, ir, out, verified=True)
        print(f"verify (render): green | {out}")
    print("SCREENSAGE INGEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
