"""ffprobe ground truth for media files."""
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path):
    """Return {'fps': 'N/D', 'duration': float_secs, 'width': int, 'height': int}."""
    path = Path(path).resolve()
    res = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration:stream=codec_type,r_frame_rate,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {res.stderr.strip()}")
    meta = json.loads(res.stdout)
    v = next((s for s in meta.get("streams", []) if s.get("codec_type") == "video"), None)
    fps = None
    if v and v.get("r_frame_rate") not in (None, "0/0"):
        fr = Fraction(v["r_frame_rate"])
        fps = f"{fr.numerator}/{fr.denominator}"
    return {
        "fps": fps,
        "duration": float(meta.get("format", {}).get("duration", 0) or 0),
        "width": v.get("width") if v else None,
        "height": v.get("height") if v else None,
    }
