#!/usr/bin/env python3
"""Runs ON the Mac mini. One iPhone log clip, two film emulations, rendered by Resolve Studio.

  print  colour managed; timeline AND output Rec.709 / Cineon Film Log; Resolve's
         shipped Kodak 2383 print LUT on node 1 (its grey axis measured identical to
         Juan Melara's), so the print receives the log input it was built for
  flc    colour managed; timeline DaVinci WG/Intermediate, output Rec.709 Gamma 2.4;
         Film Look Creator in the clip's Fusion comp (the colour-page API cannot add
         a ResolveFX), fed scene-referred log

The clip's input colour space is whatever Resolve auto-detects, printed so it can be
checked; it is only set by hand when Resolve detects nothing Apple Log shaped.

    python3 film_mini.py <clip> <out_dir> <tag> [print|flc ...]
"""
import glob
import os
import sys
import time

API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
os.environ.setdefault("RESOLVE_SCRIPT_API", API)
os.environ.setdefault("RESOLVE_SCRIPT_LIB",
                      "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so")
sys.path.append(os.path.join(API, "Modules"))
import DaVinciResolveScript as dvr  # noqa: E402

CLIP, OUT, TAG = sys.argv[1:4]
ROUTES = sys.argv[4:] or ["print", "flc"]
PRINT_LUT = "Film Looks/Rec709 Kodak 2383 D65.cube"
FLC_ID = "ofx.com.blackmagicdesign.resolvefx.FilmLook"
W, H = (int(x) for x in (sys.argv[sys.argv.index("--size") + 1] if "--size" in sys.argv else "1920x1080").split("x"))
KEYS = ("colorScienceMode", "separateColorSpaceAndGamma", "colorSpaceTimeline", "colorSpaceTimelineGamma",
        "colorSpaceOutput", "colorSpaceOutputGamma", "timelineFrameRate")

app = dvr.scriptapp("Resolve")
if not app:
    sys.exit("Resolve is not answering on the mini")
pm = app.GetProjectManager()
# StopRendering returns at once, but Resolve keeps stopping the render and holds a modal
# dialog until it is done; CreateProject returns None meanwhile (measured 2026-09-12).
for _ in range(150):
    _cur = pm.GetCurrentProject()
    if app.GetCurrentPage() is not None and not (_cur and _cur.IsRenderingInProgress()):
        break
    time.sleep(2)
else:
    sys.exit("Resolve stayed busy for 5 minutes (modal dialog up or a render still stopping)")


def setting(proj, key, *values):
    for v in values:
        ok = proj.SetSettings({key: v})
        print(f"  {key}={v!r} -> {ok}, reads {proj.GetSettings().get(key)!r}")
        if ok:
            return True
    return False


def open_project(name, fps):
    proj = pm.LoadProject(name)
    if proj:
        return proj, False
    proj = pm.CreateProject(name)
    if not proj:
        sys.exit(f"CreateProject({name!r}) returned None: Resolve busy, or the name is taken")
    setting(proj, "timelineFrameRate", fps)
    setting(proj, "timelineResolutionWidth", str(W))
    setting(proj, "timelineResolutionHeight", str(H))
    setting(proj, "colorScienceMode", "davinciYRGBColorManagedv2")
    return proj, True


def clip_on_timeline(proj, name):
    mp = proj.GetMediaPool()
    if proj.GetTimelineCount():
        tl = proj.GetTimelineByIndex(1)
    else:
        tl = mp.CreateTimelineFromClips(name, [mp.ImportMedia([CLIP])[0]])
    proj.SetCurrentTimeline(tl)
    item = tl.GetItemListInTrack("video", 1)[0]
    mpi = item.GetMediaPoolItem()
    space, gamma = mpi.GetClipProperty("Input Color Space"), mpi.GetClipProperty("Input Gamma")
    print(f"  Resolve auto-detected input: space {space!r}, gamma {gamma!r}")
    if "apple" not in f"{space} {gamma}".lower():
        print("  nothing Apple Log shaped detected; setting Apple Log by hand")
        for v in ("Apple Log", "Apple Log Rec.2020 - CSC"):
            if mpi.SetClipProperty("Input Color Space", v):
                break
        print(f"  now: space {mpi.GetClipProperty('Input Color Space')!r}, gamma {mpi.GetClipProperty('Input Gamma')!r}")
    return tl, item


def render(proj, name):
    print("  format mp4/H265 ->", proj.SetCurrentRenderFormatAndCodec("mp4", "H265"))
    rs = {"TargetDir": OUT, "CustomName": name, "SelectAllFrames": True, "FormatWidth": W, "FormatHeight": H,
          "VideoQuality": 80000 if W >= 3840 else 40000, "EncodingProfile": "Main10", "ExportVideo": True, "ExportAudio": True,
          "ColorSpaceTag": "Same as Project", "GammaTag": "Same as Project"}
    print("  render settings ->", proj.SetRenderSettings(rs))
    job = proj.AddRenderJob() or proj.AddRenderJob()
    t0 = time.time()
    proj.StartRendering([job], False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    print("  status", proj.GetRenderJobStatus(job), f"{time.time() - t0:.0f}s")
    pm.SaveProject()
    return sorted(glob.glob(os.path.join(OUT, name + "*.mp4")))


fps = sys.argv[sys.argv.index("--fps") + 1] if "--fps" in sys.argv else "30"
ROUTES = [r for r in ROUTES if r in ("print", "flc")]

if "print" in ROUTES:
    print(f"\n[print] {TAG}")
    proj, fresh = open_project(f"{TAG}-kodak-2383", fps)
    setting(proj, "separateColorSpaceAndGamma", "1")
    setting(proj, "colorSpaceTimeline", "Rec.709")
    setting(proj, "colorSpaceTimelineGamma", "Cineon Film Log")
    setting(proj, "colorSpaceOutput", "Rec.709")
    setting(proj, "colorSpaceOutputGamma", "Cineon Film Log")
    tl, item = clip_on_timeline(proj, f"{TAG}-kodak-2383")
    g = item.GetNodeGraph()
    print("  SetLUT print ->", g.SetLUT(1, PRINT_LUT), "reads", g.GetLUT(1))
    print("  rendered:", render(proj, f"{TAG}-kodak-2383"))

if "flc" in ROUTES:
    print(f"\n[flc] {TAG}")
    proj, fresh = open_project(f"{TAG}-film-look-creator", fps)
    setting(proj, "separateColorSpaceAndGamma", "0")
    setting(proj, "colorSpaceTimeline", "DaVinci WG/Intermediate", "DaVinci Wide Gamut Intermediate", "DaVinci WG")
    setting(proj, "colorSpaceOutput", "Rec.709 Gamma 2.4")
    tl, item = clip_on_timeline(proj, f"{TAG}-film-look-creator")
    comp = item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else item.AddFusionComp()
    by_reg = {t.GetAttrs("TOOLS_RegID"): t for t in comp.GetToolList(False).values()}
    flc = by_reg.get(FLC_ID) or comp.AddTool(FLC_ID)
    mi, mo = by_reg["MediaIn"], by_reg["MediaOut"]
    src = [i for i in flc.GetInputList().values() if i.GetAttrs("INPS_DataType") == "Image"][0]
    flc.ConnectInput(src.GetAttrs("INPS_ID"), mi)
    mo.ConnectInput("Input", flc)
    if not src.GetConnectedOutput():
        sys.exit("Film Look Creator input unconnected; not rendering a blank video")
    print("  FLC wired, input colour space", flc.GetInput("inputColorSpace"), "output", flc.GetInput("outputColorSpace"))
    print("  rendered:", render(proj, f"{TAG}-film-look-creator"))

s = proj.GetSettings()
print("\nlast project settings:", {k: s.get(k) for k in KEYS})
