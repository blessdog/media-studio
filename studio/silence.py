"""Silence analysis via auto-editor's v3 timeline export.

The v3 format maps losslessly onto Story IR: timebase is the same rational
string, `offset` = srcIn, `start` = record frame, `dur` = duration.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

AUTO_EDITOR = shutil.which("auto-editor") or str(Path.home() / ".local/bin/auto-editor")


def loud_spans(media_path, margin=None):
    """Run auto-editor loudness analysis. Returns (timebase, spans) where
    spans = [{'record': int, 'srcIn': int, 'srcOut': int}, ...]."""
    media_path = Path(media_path).resolve()
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "cuts.v3"
        cmd = [AUTO_EDITOR, str(media_path), "--export", "v3", "-o", str(out)]
        if margin:
            cmd += ["--margin", margin]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # auto-editor names the file with its own extension
        candidates = list(Path(td).glob("cuts*"))
        if res.returncode != 0 or not candidates:
            raise RuntimeError(f"auto-editor failed: {res.stderr[-400:]}")
        v3 = json.loads(candidates[0].read_text())
    video_track = (v3.get("v") or [[]])[0]
    spans = [
        {"record": c["start"], "srcIn": c["offset"], "srcOut": c["offset"] + c["dur"]}
        for c in video_track if c.get("name") == "video"
    ]
    return v3["timebase"], spans
