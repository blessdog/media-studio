#!/usr/bin/env python3
"""Phase 4 smokes S1–S4. Decide-by-result; findings become doctrine.

    .venv/bin/python scripts/smoke_phase4.py

S1 population: after InsertFusionTitleIntoTimeline, can the item's Fusion
   comp be read and its TextPlus populated via SetInput, and read back?
S2 placement: does insert land at the playhead (SetCurrentTimecode first)?
   What retime surface does the item expose (SetStart/SetEnd/SetDuration)?
S3 captions: what subtitle-import surface exists (timeline + mediapool)?
S4 video overlay: does a video clip ride OTIO onto V2 like images did?
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import compile as compmod
from studio.resolve import connect

ROOT = Path(__file__).resolve().parent.parent
SMOKE = ROOT / "outputs" / "smoke"
TITLE = "Media Studio Smoke"


def main():
    app = connect()
    pm = app.GetProjectManager()
    proj = pm.GetCurrentProject() or pm.LoadProject("media-studio-smoke")
    if not proj:
        print("FAIL: no current project")
        return 1
    mp = proj.GetMediaPool()

    tl = mp.CreateEmptyTimeline(f"smoke-p4-{int(time.time())}")
    proj.SetCurrentTimeline(tl)
    fps = float(tl.GetSetting("timelineFrameRate") or 24)
    start = tl.GetStartFrame()

    # --- S2: placement via playhead -----------------------------------------
    target = 120
    tc_frames = start + target
    h, rem = divmod(int(tc_frames), int(3600 * fps))
    m, rem2 = divmod(rem, int(60 * fps))
    s, f = divmod(rem2, int(fps))
    tl.SetCurrentTimecode(f"{h:02d}:{m:02d}:{s:02d}:{f:02d}")
    item = tl.InsertFusionTitleIntoTimeline(TITLE)
    if not item:
        print(f"S1/S2 FAIL: could not insert {TITLE!r}")
        return 1
    got = item.GetStart() - start
    print(f"S2 insert-at-playhead: wanted record {target}, got {got} "
          f"-> {'PASS' if got == target else 'MISS'}")
    retime_surface = [m_ for m_ in ("SetStart", "SetEnd", "SetDuration",
                                    "SetLeftOffset", "SetRightOffset",
                                    "SetProperty")
                      if callable(getattr(item, m_, None))]
    print(f"S2 item retime surface (actually callable): {retime_surface or 'NONE'}")
    if "SetEnd" in retime_surface:
        try:
            ok = item.SetEnd(item.GetStart() + 60)
            print(f"S2 SetEnd(+60): returned {ok}, duration now {item.GetDuration()}")
        except TypeError as e:
            print(f"S2 SetEnd not usable: {e}")

    # --- S1: populate the comp ----------------------------------------------
    n = item.GetFusionCompCount()
    print(f"S1 fusion comps on item: {n}")
    comp = item.GetFusionCompByIndex(1) if n else None
    if not comp:
        print("S1 FAIL: no comp handle")
    else:
        tools = comp.GetToolList(False, "TextPlus")
        tool = tools.get(1) if isinstance(tools, dict) else (tools[0] if tools else None)
        if not tool:
            print("S1 FAIL: no TextPlus in comp")
        else:
            tool.SetInput("StyledText", "POPULATED BY SMOKE")
            back = tool.GetInput("StyledText")
            print(f"S1 SetInput/GetInput roundtrip: {back!r} "
                  f"-> {'PASS' if back == 'POPULATED BY SMOKE' else 'FAIL'}")

    # --- S3: subtitle surface ------------------------------------------------
    sub_tl = [m_ for m_ in dir(tl) if "ubtitle" in m_ or "SRT" in m_ or "rt" == m_.lower()]
    sub_mp = [m_ for m_ in dir(mp) if "ubtitle" in m_]
    print(f"S3 timeline subtitle methods: {sub_tl or 'NONE'}")
    print(f"S3 mediapool subtitle methods: {sub_mp or 'NONE'}")

    # --- S4: video clip overlay via OTIO ------------------------------------
    clip = SMOKE / "clip1-red.mp4"
    talky = SMOKE / "talky.mp4"
    if clip.is_file() and talky.is_file():
        ir = {
            "irVersion": "0.2",
            "name": "smoke-clip-overlay",
            "timebase": {"fps": "30/1"},
            "resolution": {"width": 1920, "height": 1080},
            "assets": [
                {"id": "base", "path": str(talky), "kind": "video", "_frames": 600},
                {"id": "b", "path": str(clip), "kind": "video", "_frames": 90},
            ],
            "edits": [
                {"id": "e1", "asset": "base", "srcIn": 0, "srcOut": 240,
                 "record": 0, "track": 1},
                {"id": "e2", "asset": "b", "srcIn": 10, "srcOut": 70,
                 "record": 60, "track": 2},
            ],
        }
        proj2, tl2, cached = compmod.compile_ir(ir, SMOKE, SMOKE / "smoke-clip-overlay.otio")
        items = tl2.GetItemListInTrack("video", 2) or []
        if len(items) == 1 and items[0].GetStart() - tl2.GetStartFrame() == 60 \
                and items[0].GetDuration() == 60:
            print("S4 PASS: video clip overlay rides OTIO onto V2 at exact frames")
        else:
            print(f"S4 FAIL: V2 items={len(items)}")
            return 1
    else:
        print("S4 SKIP: smoke media missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
