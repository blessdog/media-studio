#!/usr/bin/env python3
"""Runs ON the Mac mini. Set Film Look Creator inputs on an existing project, then export a still or render.

    python3 flc_tune.py <project> <timeline|-> <out_dir> still|render <name> [--at SECONDS] [--create-combo] [input=value ...]

--create-combo builds <timeline> in <project> from its first media-pool clip: Resolve's Kodak 2383 print on
colour node 1, and Film Look Creator in the Fusion comp ahead of it (Resolve runs Fusion before the colour
page). The print sets tone and colour; Film Look Creator, with its own look blended out, adds texture.
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

PROJECT, TL_NAME, OUT, ACTION, NAME = sys.argv[1:6]
REST = sys.argv[6:]
AT = float(REST[REST.index("--at") + 1]) if "--at" in REST else 30.0
CREATE = "--create-combo" in REST
PAIRS = [a.split("=", 1) for a in REST if "=" in a]
PRINT_LUT = "Film Looks/Rec709 Kodak 2383 D65.cube"
FLC_ID = "ofx.com.blackmagicdesign.resolvefx.FilmLook"
SHOW = ("filmLookBlend", "colorContrast2", "halationIsEnable", "halationAmount", "bloomIsEnable", "bloomAmount",
        "grainIsEnable", "grainAmount")

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
timelines = [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)]
tl = timelines[0] if TL_NAME == "-" else next((t for t in timelines if t.GetName() == TL_NAME), None)
if tl is None:
    if not CREATE:
        sys.exit(f"no timeline {TL_NAME!r} in {PROJECT!r}")
    mp = proj.GetMediaPool()
    clip = next(c for c in mp.GetRootFolder().GetClipList() if "Timeline" not in str(c.GetClipProperty("Type")))
    tl = mp.CreateTimelineFromClips(TL_NAME, [clip])
    item = tl.GetItemListInTrack("video", 1)[0]
    item.GetNodeGraph().SetLUT(1, PRINT_LUT)
    comp = item.AddFusionComp()
    reg = {t.GetAttrs("TOOLS_RegID"): t for t in comp.GetToolList(False).values()}
    flc = comp.AddTool(FLC_ID)
    src = next(i for i in flc.GetInputList().values() if i.GetAttrs("INPS_DataType") == "Image")
    flc.ConnectInput(src.GetAttrs("INPS_ID"), reg["MediaIn"])
    reg["MediaOut"].ConnectInput("Input", flc)
    if not src.GetConnectedOutput():
        sys.exit("Film Look Creator input unconnected")
    print("created combo timeline", TL_NAME)
proj.SetCurrentTimeline(tl)
item = tl.GetItemListInTrack("video", 1)[0]
print("project", proj.GetName(), "timeline", tl.GetName(), "node1 LUT", repr(item.GetNodeGraph().GetLUT(1)))
flc = None
if item.GetFusionCompCount():
    comp = item.GetFusionCompByIndex(1)
    flc = next((t for t in comp.GetToolList(False).values() if t.GetAttrs("TOOLS_RegID") == FLC_ID), None)
for k, v in PAIRS:
    try:
        val = float(v)
    except ValueError:
        val = v
    if not flc:
        sys.exit(f"no Film Look Creator on {tl.GetName()!r} to set {k}")
    flc.SetInput(k, val)
if flc:
    print("FLC", {k: flc.GetInput(k) for k in SHOW})

if ACTION == "still":
    app.OpenPage("color")
    hh = tl.GetStartTimecode().split(":")[0]
    secs = int(AT)
    tl.SetCurrentTimecode(f"{hh}:{secs // 60:02d}:{secs % 60:02d}:00")
    time.sleep(3)
    path = os.path.join(OUT, NAME + ".png")
    print(f"STILL {path} -> {proj.ExportCurrentFrameAsStill(path)}")
else:
    s = proj.GetSettings()
    w, h = int(s["timelineResolutionWidth"]), int(s["timelineResolutionHeight"])
    proj.SetCurrentRenderFormatAndCodec("mp4", "H265")
    proj.SetRenderSettings({"TargetDir": OUT, "CustomName": NAME, "SelectAllFrames": True, "FormatWidth": w,
                            "FormatHeight": h, "VideoQuality": 80000 if w >= 3840 else 40000,
                            "EncodingProfile": "Main10", "ExportVideo": True, "ExportAudio": True,
                            "ColorSpaceTag": "Same as Project", "GammaTag": "Same as Project"})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    t0 = time.time()
    proj.StartRendering([job], False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    print("status", proj.GetRenderJobStatus(job), f"{time.time() - t0:.0f}s")
    print(f"RENDERED {os.path.join(OUT, NAME + '.mp4')}")
pm.SaveProject()
