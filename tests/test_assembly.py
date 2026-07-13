#!/usr/bin/env python3
"""Assembly-loop gates: moments (phrase -> frame) and edit_ir (IR mutations).

No Resolve required — pure functions + lint against real files.

    .venv/bin/python tests/test_assembly.py
"""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import edit_ir as editmod
from studio import ir as irmod
from studio import lint as lintmod
from studio import moments as momentsmod

FIXTURES = Path(__file__).resolve().parent / "fixtures"

passed = 0


def check(label, cond):
    global passed
    if not cond:
        print(f"FAIL: {label}")
        sys.exit(1)
    passed += 1
    print(f"  ok: {label}")


def w(word, start, punct=None):
    return {"word": word, "punctuated_word": punct or word,
            "start": start, "end": start + 0.3}


TRANSCRIPT = {"model": "test", "words": [
    w("the", 1.0), w("fed", 1.3, "Fed"), w("just", 1.6),
    w("blinked", 1.9, "blinked."), w("and", 3.0), w("markets", 3.3),
    w("noticed", 3.6), w("the", 8.0), w("fed", 8.3, "Fed"),
    w("just", 8.6), w("blinked", 8.9, "blinked!"),
], "utterances": []}

# --- moments.find ------------------------------------------------------------
hits = momentsmod.find(TRANSCRIPT, "Fed just BLINKED?!")
check("find: case/punctuation-insensitive, both occurrences",
      len(hits) == 2 and hits[0]["start"] == 1.3 and hits[1]["start"] == 8.3)
check("find: hit text uses punctuated words", "blinked." in hits[0]["text"])
check("find: miss returns empty", momentsmod.find(TRANSCRIPT, "quantitative easing") == [])

# --- moments mapping through the golden IR's spans ---------------------------
ir, base = irmod.load(FIXTURES / "golden-ir.json")
check("record_frame: inside first span (src 90 -> rec 30)",
      momentsmod.record_frame(ir, 90 / 30) == 30)
check("record_frame: inside second span (src 320 -> rec 140)",
      momentsmod.record_frame(ir, 320 / 30) == 140)
check("record_frame: cut region -> None",
      momentsmod.record_frame(ir, 200 / 30) is None)

# --- edit_ir mutations, gated by the real linter -----------------------------
with tempfile.TemporaryDirectory() as td:
    png = Path(td) / "meme.png"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "color=c=red:s=640x480:d=1", "-frames:v", "1", str(png)],
        check=True)

    before = copy.deepcopy(ir)
    ir2, eid = editmod.insert_cutaway(ir, png, record=30)
    check("insert_cutaway: input IR untouched (pure)", ir == before)
    edit = next(e for e in ir2["edits"] if e["id"] == eid)
    check("insert_cutaway: house default 3.5s @30fps = 105 frames",
          edit["srcOut"] == 105 and edit["track"] == 2 and edit["srcIn"] == 0)
    check("insert_cutaway: stamps irVersion 0.2", ir2["irVersion"] == "0.2")
    errors, _ = lintmod.lint(copy.deepcopy(ir2), base)
    check("insert_cutaway: lints green", errors == [])

    p = Path(td) / "round.json"
    p.write_text(json.dumps(ir2))
    irmod.load(p)
    check("mutated IR passes schema v0.2", True)

    ir3, eid2 = editmod.insert_cutaway(ir2, png, record=60)
    check("same image twice: one asset, two edits",
          sum(a["kind"] == "image" for a in ir3["assets"]) == 1)
    errors, _ = lintmod.lint(copy.deepcopy(ir3), base)
    check("overlapping cutaways (30+105 > 60): lint refuses",
          any("overlap" in e for e in errors))

    ir4 = editmod.retime_edit(ir3, eid2, record=150, duration_frames=60)
    e2 = next(e for e in ir4["edits"] if e["id"] == eid2)
    check("retime: record + duration applied",
          e2["record"] == 150 and e2["srcOut"] == 60)
    errors, _ = lintmod.lint(copy.deepcopy(ir4), base)
    check("retimed IR lints green", errors == [])

    ir5 = editmod.remove_edit(editmod.remove_edit(ir4, eid), eid2)
    check("remove: orphaned image asset dropped",
          not any(a["kind"] == "image" for a in ir5["assets"]))

    ir6, _ = editmod.insert_cutaway(ir2, Path(td) / "nope.png", record=200)
    errors, _ = lintmod.lint(copy.deepcopy(ir6), base)
    check("missing image file: lint refuses",
          any("missing" in e for e in errors))

    try:
        editmod.insert_cutaway(ir2, png, record=-5)
        check("negative record raises EditError", False)
    except editmod.EditError:
        check("negative record raises EditError", True)

    # --- b-roll clip cutaways -------------------------------------------------
    broll = Path(td) / "broll.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "color=c=blue:s=640x480:d=6:r=30", str(broll)], check=True)
    ir7, eid7 = editmod.insert_clip(ir, broll, record=30, src_in=15,
                                    duration_frames=60)
    e7 = next(e for e in ir7["edits"] if e["id"] == eid7)
    check("insert_clip: srcIn/srcOut honored",
          e7["srcIn"] == 15 and e7["srcOut"] == 75 and e7["track"] == 2)
    errors, _ = lintmod.lint(copy.deepcopy(ir7), base)
    check("b-roll cutaway lints green", errors == [])
    ir8, eid8 = editmod.insert_clip(ir, broll, record=30, src_in=150,
                                    duration_frames=60)
    errors, _ = lintmod.lint(copy.deepcopy(ir8), base)
    check("b-roll beyond asset length: lint refuses",
          any("beyond" in e for e in errors))

# --- audio spine ---------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    tone = Path(td) / "tone.m4a"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=220:duration=10", "-c:a", "aac", str(tone)],
        check=True)
    png = Path(td) / "meme.png"          # earlier block's tempdir is gone
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "color=c=red:s=640x480:d=1", "-frames:v", "1", str(png)],
        check=True)
    irA, mid = editmod.add_music(ir, tone, record=30, duration_frames=90)
    m = next(e for e in irA["edits"] if e["id"] == mid)
    check("add_music: lands on A2 with duration",
          m["track"] == 2 and m["srcOut"] - m["srcIn"] == 90)
    errors, _ = lintmod.lint(copy.deepcopy(irA), base)
    check("music bed lints green", errors == [])

    # audio track 2 and video track 2 are DIFFERENT lanes — no false overlap
    irB, _ = editmod.insert_cutaway(irA, png, record=40)
    errors, _ = lintmod.lint(copy.deepcopy(irB), base)
    check("audio A2 and video V2 don't false-overlap (lane separation)",
          errors == [])

    irC, _ = editmod.add_music(irA, tone, record=60, duration_frames=90)
    errors, _ = lintmod.lint(copy.deepcopy(irC), base)
    check("overlapping music beds on A2: lint refuses",
          any("audio track 2" in e and "overlap" in e for e in errors))

    irD, bad = editmod.add_music(ir, tone, record=0, src_in=200,
                                 duration_frames=200)
    errors, _ = lintmod.lint(copy.deepcopy(irD), base)
    check("music beyond file length: lint refuses",
          any("beyond" in e for e in errors))

    lintmod.lint(irA, base)     # enrich in place, as the CLI flow does
    rec_asset = next(a for a in irA["assets"] if a["id"] == "a1")
    check("lint enriches _hasAudio on the recording",
          rec_asset.get("_hasAudio") is True)

    from studio import verify as verifymod
    check("expects_audio: true with voice or music", verifymod.expects_audio(irA))
    silent = {**copy.deepcopy(ir),
              "assets": [{**a, "_hasAudio": False} for a in ir["assets"]]}
    check("expects_audio: false for silent sources",
          not verifymod.expects_audio(silent))

# --- graphics (uses the repo smoke package manifest) --------------------------
ir9, gid = editmod.insert_graphic(
    ir, "Media Studio Smoke", record=30, duration_frames=60,
    inputs={"StyledText": "HELLO"})
check("insert_graphic: stamps v0.3 and appends",
      ir9["irVersion"] == "0.3" and ir9["graphics"][0]["id"] == gid)
errors, _ = lintmod.lint(copy.deepcopy(ir9), FIXTURES)
check("approved graphic lints green", errors == [])

ir10, _ = editmod.insert_graphic(ir, "Smoke Unapproved", record=30)
errors, _ = lintmod.lint(copy.deepcopy(ir10), FIXTURES)
check("UNAPPROVED template: lint refuses", any("NOT approved" in e for e in errors))

ir11, _ = editmod.insert_graphic(ir, "No Such Template", record=30)
errors, _ = lintmod.lint(copy.deepcopy(ir11), FIXTURES)
check("unknown template: lint refuses", any("unknown template" in e for e in errors))

ir12, _ = editmod.insert_graphic(ir, "Media Studio Smoke", record=30,
                                 inputs={"NotAnInput": "x"})
errors, _ = lintmod.lint(copy.deepcopy(ir12), FIXTURES)
check("unknown input key: lint refuses", any("unknown inputs" in e for e in errors))

ir13, _ = editmod.insert_graphic(ir9, "Media Studio Smoke", record=60,
                                 inputs={"StyledText": "OVERLAP"})
errors, _ = lintmod.lint(copy.deepcopy(ir13), FIXTURES)
check("overlapping graphics: lint refuses", any("overlap" in e for e in errors))

ir14 = editmod.remove_graphic(ir9, gid)
check("remove_graphic drops the list when empty", "graphics" not in ir14)

# --- .setting linter ----------------------------------------------------------
from studio import templates as tmplmod
lib = tmplmod.load_manifests()
check("manifest loads with package tag",
      lib["Media Studio Smoke"]["package"] == "smoke")
check("good .setting lints clean",
      tmplmod.lint_setting(lib["Media Studio Smoke"]["path"]) == [])
with tempfile.TemporaryDirectory() as td2:
    bad = Path(td2) / "bad.setting"
    bad.write_text("{ Tools = ordered() { Template = TextPlus {")
    errs = tmplmod.lint_setting(bad)
    check(".setting linter catches unbalanced braces",
          any("unbalanced" in e for e in errs))

print(f"ASSEMBLY OK ({passed}/{passed})")
