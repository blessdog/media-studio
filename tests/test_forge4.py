"""Scene Forge slice 4: beat grid (synthesized oracle) + blender guards."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import beatgrid as bgmod
from studio import blender as blmod

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


tmp = Path(tempfile.mkdtemp(prefix="forge4-"))

# -- beat grid on a synthesized 120 BPM click track ---------------------------
import numpy as np
import soundfile as sf
sr, secs, bpm = 22050, 8.0, 120
y = np.zeros(int(sr * secs), dtype=np.float32)
step = int(sr * 60 / bpm)                      # 0.5s
for i in range(0, len(y) - 600, step):
    t = np.arange(600) / sr
    y[i:i + 600] += (np.sin(2 * np.pi * 1000 * t) *
                     np.exp(-t * 60)).astype(np.float32)
click = tmp / "click120.wav"
sf.write(click, y, sr)

grid = bgmod.analyze(click, "30/1")
check("bpm ~120", abs(grid["bpm"] - 120) < 6, f"got {grid['bpm']}")
beats = grid["beats"]
check("found most beats", len(beats) >= 12, f"got {len(beats)}")
gaps = [b - a for a, b in zip(beats, beats[1:])]
check("beat spacing ~15 frames @30fps",
      all(abs(g - 15) <= 2 for g in gaps), f"gaps {gaps[:6]}")

# markers: every Nth, offset, extent clamp
mk = bgmod.beat_markers(beats, every=4, offset=10, extent=200)
check("every-4th subset", len(mk) <= len(beats) // 4 + 1)
check("offset applied", mk[0]["frame"] == beats[0] + 10)
check("extent clamps", all(m["frame"] < 200 for m in mk))
check("names count beats", mk[0]["name"] == "beat 1")

# -- error paths ---------------------------------------------------------------
try:
    bgmod.analyze(tmp / "nope.wav", "30/1")
    check("missing audio rejected", False)
except bgmod.BeatError:
    check("missing audio rejected", True)
try:
    blmod.render_scene(tmp / "nope.py", tmp / "out.mp4")
    check("missing scene rejected", False)
except blmod.BlenderError:
    check("missing scene rejected", True)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
