#!/usr/bin/env python3
"""Runs ON the Mac mini. Ease Film Look Creator's contrast on an existing Film Look Creator project.

    python3 flc_ease.py <project> <out_dir> ladder <seconds> <contrast> [<contrast> ...]
        export one still of the same frame per contrast value, then restore the default 1.25
    python3 flc_ease.py <project> <out_dir> render <contrast> <name>
        render the whole timeline with that contrast, 10-bit H.265 at the timeline size
"""
import os
import sys
import time

API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
os.environ.setdefault("RESOLVE_SCRIPT_API", API)
os.environ.setdefault("RESOLVE_SCRIPT_LIB",
                      "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so")
sys.path.append(os.path.join(API, "Modules"))
import DaVinciResolveScript as dvr  # noqa: E402

PROJECT, OUT, MODE = sys.argv[1:4]
FLC_ID = "ofx.com.blackmagicdesign.resolvefx.FilmLook"
DEFAULT_CONTRAST = 1.25

app = dvr.scriptapp("Resolve")
if not app:
    sys.exit("Resolve is not answering on the mini")
pm = app.GetProjectManager()
for _ in range(150):
    _cur = pm.GetCurrentProject()
    if app.GetCurrentPage() is not None and not (_cur and _cur.IsRenderingInProgress()):
        break
    time.sleep(2)
else:
    sys.exit("Resolve stayed busy for 5 minutes")

cur = pm.GetCurrentProject()
proj = cur if cur and cur.GetName() == PROJECT else pm.LoadProject(PROJECT)
if not proj:
    sys.exit(f"could not load project {PROJECT!r}")
tl = proj.GetTimelineByIndex(1)
proj.SetCurrentTimeline(tl)
item = tl.GetItemListInTrack("video", 1)[0]
comp = item.GetFusionCompByIndex(1)
flc = next(t for t in comp.GetToolList(False).values() if t.GetAttrs("TOOLS_RegID") == FLC_ID)
print("project", proj.GetName(), "timeline", tl.GetName(), "contrast now", flc.GetInput("colorContrast2"))

if MODE == "ladder":
    secs = int(float(sys.argv[4]))
    app.OpenPage("color")
    hh = tl.GetStartTimecode().split(":")[0]
    tl.SetCurrentTimecode(f"{hh}:{secs // 60:02d}:{secs % 60:02d}:00")
    print("timecode", tl.GetCurrentTimecode())
    for c in sys.argv[5:]:
        flc.SetInput("colorContrast2", float(c))
        time.sleep(2)
        path = os.path.join(OUT, f"contrast-{c}.png")
        print(f"STILL {c} reads {flc.GetInput('colorContrast2')} -> {proj.ExportCurrentFrameAsStill(path)} {path}")
    flc.SetInput("colorContrast2", DEFAULT_CONTRAST)
elif MODE == "render":
    c, name = float(sys.argv[4]), sys.argv[5]
    flc.SetInput("colorContrast2", c)
    print("contrast set", flc.GetInput("colorContrast2"))
    s = proj.GetSettings()
    w, h = int(s["timelineResolutionWidth"]), int(s["timelineResolutionHeight"])
    proj.SetCurrentRenderFormatAndCodec("mp4", "H265")
    proj.SetRenderSettings({"TargetDir": OUT, "CustomName": name, "SelectAllFrames": True, "FormatWidth": w,
                            "FormatHeight": h, "VideoQuality": 80000 if w >= 3840 else 40000,
                            "EncodingProfile": "Main10", "ExportVideo": True, "ExportAudio": True,
                            "ColorSpaceTag": "Same as Project", "GammaTag": "Same as Project"})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    t0 = time.time()
    proj.StartRendering([job], False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    print("status", proj.GetRenderJobStatus(job), f"{time.time() - t0:.0f}s")
    print(f"RENDERED {os.path.join(OUT, name + '.mp4')}")
pm.SaveProject()
