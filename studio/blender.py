"""Blender bpy headless lane (Scene Forge slice 4a).

Deterministic camera work — the shots genAI wanders on (orbits, dolly
moves, repeatable scenes) rendered locally for free. Scene scripts are
plain bpy Python living in repo `blender/`; each receives its render
parameters after the `--` separator and must write ONE video file to the
given output path. The harness runs Blender fully headless
(--background --factory-startup) so renders are reproducible — nothing
depends on user preferences or startup files.
"""
import subprocess
from pathlib import Path

BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")


class BlenderError(RuntimeError):
    pass


def binary():
    if not BLENDER.is_file():
        raise BlenderError(f"Blender binary missing: {BLENDER}")
    return BLENDER


def render_scene(scene_script, out_path, frames=48, fps=24,
                 width=960, height=540, timeout=1800, extra=()):
    """Run one scene script headless -> out_path (mp4). Returns out_path.

    Blender 5 removed built-in video encoding (image_settings has stills
    only), so scenes render a PNG sequence and ffmpeg muxes it here."""
    import shutil
    import tempfile
    scene_script = Path(scene_script)
    if not scene_script.is_file():
        raise BlenderError(f"scene script missing: {scene_script}")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="ms-blender-"))
    try:
        cmd = [str(binary()), "--background", "--factory-startup",
               "--python", str(scene_script), "--",
               str(tmp / "frame_"), str(frames), str(fps),
               str(width), str(height), *[str(a) for a in extra]]
        res = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=timeout)
        pngs = sorted(tmp.glob("frame_*.png"))
        if res.returncode != 0 or len(pngs) != frames:
            raise BlenderError(
                f"{scene_script.name}: exited {res.returncode}, "
                f"{len(pngs)}/{frames} frames\n"
                f"{(res.stderr or res.stdout)[-400:]}")
        mux = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-framerate", str(fps),
             "-pattern_type", "glob", "-i", str(tmp / "frame_*.png"),
             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
             str(out_path)], capture_output=True, text=True)
        if mux.returncode != 0 or not out_path.is_file():
            raise BlenderError(f"mux failed: {mux.stderr[-300:]}")
        return out_path
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
