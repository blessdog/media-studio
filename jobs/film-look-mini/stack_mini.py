#!/usr/bin/env python3
"""Runs ON the Mac mini. Pro-finish test variants on one iPhone log clip, rendered by Resolve Studio.

Each variant is its own timeline, so each has its own Fusion comp, node graph and output blanking.
Print variants share a project whose timeline AND output are Rec.709 / Cineon Film Log, so the
Kodak 2383 print on node 1 receives log. Resolve runs Fusion before the colour page, so lens-side
tools (noise reduction, CineFocus) sit in the Fusion comp ahead of the print: lens, then film stock.

    python3 stack_mini.py <clip> <out_dir> <tag> <variant> [--fps 30]
variants: print letterbox denoise cinefocus stack flc
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

CLIP, OUT, TAG, VARIANT = sys.argv[1:5]
FPS = sys.argv[sys.argv.index("--fps") + 1] if "--fps" in sys.argv else "30"
PRINT_LUT = "Film Looks/Rec709 Kodak 2383 D65.cube"
RFX = "ofx.com.blackmagicdesign.resolvefx."
W, H = 1920, 1080
# Resolve's timeline output blanking is a PERCENT of frame per edge, not pixels: measured
# 2026-09-12, Top/Bottom 138 blanked the whole frame. 2.39:1 in a 16:9 frame is 12.81%.
BARS = round((1 - (W / 2.39) / H) / 2 * 100, 2)
DENOISE = ("NoiseReduction", {"temporalLumaThresh": 12.0})
SPEC = {
    "print":     ("print", [], False),
    "letterbox": ("print", [], True),
    "denoise":   ("print", [DENOISE], False),
    "cinefocus": ("print", [("CineFocus", {})], False),
    "stack":     ("print", [DENOISE, ("CineFocus", {})], True),
    "flc":       ("flc", [("FilmLook", {})], False),
}
kind, tools, letterbox = SPEC[VARIANT]

app = dvr.scriptapp("Resolve")
if not app:
    sys.exit("Resolve is not answering on the mini")
pm = app.GetProjectManager()


def setting(proj, key, value):
    ok = proj.SetSettings({key: value})
    print(f"  {key}={value!r} -> {ok}, reads {proj.GetSettings().get(key)!r}")


name = f"{TAG}-finish-{kind}"
proj = pm.LoadProject(name)
if not proj:
    proj = pm.CreateProject(name)
    for k, v in (("timelineFrameRate", FPS), ("timelineResolutionWidth", str(W)),
                 ("timelineResolutionHeight", str(H)), ("colorScienceMode", "davinciYRGBColorManagedv2")):
        setting(proj, k, v)
    if kind == "print":
        for k, v in (("separateColorSpaceAndGamma", "1"), ("colorSpaceTimeline", "Rec.709"),
                     ("colorSpaceTimelineGamma", "Cineon Film Log"), ("colorSpaceOutput", "Rec.709"),
                     ("colorSpaceOutputGamma", "Cineon Film Log")):
            setting(proj, k, v)
    else:
        for k, v in (("separateColorSpaceAndGamma", "0"), ("colorSpaceTimeline", "DaVinci WG/Intermediate"),
                     ("colorSpaceOutput", "Rec.709 Gamma 2.4")):
            setting(proj, k, v)

mp = proj.GetMediaPool()
base = os.path.basename(CLIP)
clips = [c for c in (mp.GetRootFolder().GetClipList() or []) if c.GetName() == base]
clip = clips[0] if clips else mp.ImportMedia([CLIP])[0]
print(f"[{VARIANT}] project {name}; clip input {clip.GetClipProperty('Input Color Space')!r} / {clip.GetClipProperty('Input Gamma')!r}")

tl_name = f"{TAG}-{VARIANT}"
timelines = [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)]
tl = next((t for t in timelines if t and t.GetName() == tl_name), None)
fresh = tl is None
if fresh:
    tl = mp.CreateTimelineFromClips(tl_name, [clip])
proj.SetCurrentTimeline(tl)
item = tl.GetItemListInTrack("video", 1)[0]

if fresh and tools:
    comp = item.AddFusionComp()
    reg = {t.GetAttrs("TOOLS_RegID"): t for t in comp.GetToolList(False).values()}
    prev, mo = reg["MediaIn"], reg["MediaOut"]
    for tid, values in tools:
        t = comp.AddTool(RFX + tid)
        if not t:
            sys.exit(f"Fusion refused {tid}")
        images = [i for i in t.GetInputList().values() if i.GetAttrs("INPS_DataType") == "Image"]
        src = next((i for i in images if i.GetAttrs("INPS_ID") == "Source"), images[0])
        t.ConnectInput(src.GetAttrs("INPS_ID"), prev)
        if not src.GetConnectedOutput():
            sys.exit(f"{tid} image input unconnected; not rendering a blank video")
        for k, v in values.items():
            t.SetInput(k, v)
            print(f"  {tid}.{k} = {t.GetInput(k)!r}")
        print(f"  wired {tid}")
        prev = t
    mo.ConnectInput("Input", prev)

if kind == "print":
    g = item.GetNodeGraph()
    if g.GetLUT(1) != PRINT_LUT:
        g.SetLUT(1, PRINT_LUT)
    print("  print LUT on node 1:", g.GetLUT(1))
if letterbox:
    print("  output blanking ->", tl.SetOutputBlanking({"Top": BARS, "Bottom": BARS, "Left": 0, "Right": 0}),
          tl.GetOutputBlanking())

proj.SetCurrentRenderFormatAndCodec("mp4", "H265")
proj.SetRenderSettings({"TargetDir": OUT, "CustomName": tl_name, "SelectAllFrames": True, "FormatWidth": W,
                        "FormatHeight": H, "VideoQuality": 40000, "EncodingProfile": "Main10", "ExportVideo": True,
                        "ExportAudio": True, "ColorSpaceTag": "Same as Project", "GammaTag": "Same as Project"})
job = proj.AddRenderJob() or proj.AddRenderJob()
t0 = time.time()
proj.StartRendering([job], False)
while proj.IsRenderingInProgress():
    time.sleep(2)
status = proj.GetRenderJobStatus(job)
pm.SaveProject()
print(f"  status {status}")
print(f"RENDERED {os.path.join(OUT, tl_name + '.mp4')} {time.time() - t0:.0f}s")
