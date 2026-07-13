"""Bongpot adapter: pure-function tests (no Resolve, no ffmpeg)."""
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import bongpot as bpmod

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def shots(*spans, **extra):
    out = []
    for i, (a, b) in enumerate(spans):
        s = {"id": f"s{i+1:02d}", "start": a, "end": b}
        s.update(extra)
        out.append(s)
    return out


# -- shot_grid: boundary rounding, no cumulative drift -----------------------
fps = Fraction(30)
g = bpmod.shot_grid(shots((0, 5.5), (5.5, 10.5), (10.5, 295.9)), fps)
check("grid records", [x["record"] for x in g] == [0, 165, 315])
check("grid gapless", all(a["record"] + a["frames"] == b["record"]
                          for a, b in zip(g, g[1:])))
check("grid total exact", g[-1]["record"] + g[-1]["frames"] == round(295.9 * 30))

# non-zero window start: records still begin at 0
g2 = bpmod.shot_grid(shots((10.0, 12.0), (12.0, 15.0)), fps)
check("windowed start at 0", g2[0]["record"] == 0 and g2[-1]["frames"] == 90)

# drift guard: 1000 shots of 1/3s each — per-shot rounding would drift 30s+
thirds = [(i / 3, (i + 1) / 3) for i in range(1000)]
g3 = bpmod.shot_grid(shots(*thirds), fps)
check("no cumulative drift",
      g3[-1]["record"] + g3[-1]["frames"] == round(1000 / 3 * 30))

# contiguity contract enforced
try:
    bpmod.load_plan.__wrapped__  # noqa — just documenting: load_plan checks it
except AttributeError:
    pass
try:
    bpmod.shot_grid(shots((0, 1), (1, 1)), fps)
    check("zero-frame shot rejected", False)
except bpmod.BongpotError:
    check("zero-frame shot rejected", True)

# -- verdict colors / notes ---------------------------------------------------
approved = {"review": {"keyframe": {"status": "approved"}}}
rework = {"review": {"keyframe": {"status": "approved"},
                     "clip": {"status": "rework"}}}
check("approved green", bpmod._marker_color(bpmod._verdicts(approved)) == "Green")
check("rework beats approved",
      bpmod._marker_color(bpmod._verdicts(rework)) == "Yellow")
check("no verdict sky", bpmod._marker_color({}) == "Sky")

# -- build_ir shapes -----------------------------------------------------------
grid = bpmod.shot_grid(shots((0, 2), (2, 4), speaker="luther"), fps)
ir = bpmod.build_ir("test-call", grid, {"s01": "media/s01.mp4"}, "media/call.mp3",
                    0, 120, "30/1", 1920, 1080)
check("audio asset first", ir["assets"][0] == {"id": "call",
                                               "path": "media/call.mp3",
                                               "kind": "audio"})
check("audio edit on A1", ir["edits"][0]["track"] == 1
      and ir["edits"][0]["srcOut"] == 120)
check("placed shot has edit", any(e["id"] == "e-s01" for e in ir["edits"]))
check("missing shot has NO edit",
      not any(e["id"] == "e-s02" for e in ir["edits"]))
missing_mk = [m for m in ir["markers"] if m["name"] == "MISSING s02"]
check("missing marker red", missing_mk and missing_mk[0]["color"] == "Red")
check("speaker in marker name",
      any(m["name"] == "s01 luther" for m in ir["markers"]))

# schema-valid?
import json
import jsonschema
schema = json.loads((Path(__file__).resolve().parent.parent /
                     "schema" / "story-ir.schema.json").read_text(encoding="utf-8"))
try:
    jsonschema.Draft202012Validator(schema).validate(ir)
    check("IR schema-valid", True)
except jsonschema.ValidationError as e:
    check("IR schema-valid", False, e.message)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
