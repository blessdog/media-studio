"""ffprobe ground truth for media files."""
import json
import subprocess
from fractions import Fraction
from pathlib import Path


def probe(path):
    """Return {'fps': 'N/D', 'duration': float_secs, 'width': int, 'height': int,
    'codec': str, 'pix_fmt': str, 'bits': int|None, 'format_tags': {}, 'stream_tags': {}}.

    The first four keys are the original contract every lane reads. The rest
    were added 2026-09-12 for the Osmo lane's shot-settings assertions; tags
    are dumped raw because where DJI writes ISO is unverified (VERIFY 12 in
    docs/CINEMATIC-PIPELINE-VERIFY.md).
    """
    path = Path(path).resolve()
    res = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries",
         "format=duration:format_tags:stream=codec_type,codec_name,pix_fmt,"
         "bits_per_raw_sample,r_frame_rate,width,height:stream_tags",
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
    bits = None
    if v and str(v.get("bits_per_raw_sample", "")).isdigit():
        bits = int(v["bits_per_raw_sample"])
    return {
        "fps": fps,
        "duration": float(meta.get("format", {}).get("duration", 0) or 0),
        "width": v.get("width") if v else None,
        "height": v.get("height") if v else None,
        "codec": v.get("codec_name") if v else None,
        "pix_fmt": v.get("pix_fmt") if v else None,
        "bits": bits,
        "format_tags": meta.get("format", {}).get("tags", {}) or {},
        "stream_tags": (v.get("tags", {}) if v else {}) or {},
    }
