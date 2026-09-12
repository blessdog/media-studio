"""Scratch, runs ON the Mac mini: IMG_0888 through Resolve's Film Look Creator.

The colour-page API cannot add a ResolveFX to a node, so Film Look Creator goes
into the clip's Fusion comp (MediaIn -> FilmLook -> MediaOut), where tools can
be added and their inputs set by script. Usage:

    python3 flc_mini.py <clip> <out_dir> [--list] [Input=value ...]

--list prints every Film Look Creator input and renders nothing.
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

CLIP, OUT = sys.argv[1], sys.argv[2]
LIST = "--list" in sys.argv
OVERRIDES = [a.split("=", 1) for a in sys.argv[3:] if "=" in a]
FLC_ID = "ofx.com.blackmagicdesign.resolvefx.FilmLook"
NAME = "img-0888-film-look-creator"

app = dvr.scriptapp("Resolve")
if not app:
    sys.exit("Resolve is not answering: is it running, activated, with External scripting = Local?")
print("page", app.GetCurrentPage())
pm = app.GetProjectManager()
proj = pm.LoadProject(NAME)
fresh = not proj
if fresh:
    proj = pm.CreateProject(NAME)
    for k, v in (("timelineFrameRate", "29.97"), ("timelineResolutionWidth", "1920"),
                 ("timelineResolutionHeight", "1080"), ("colorScienceMode", "davinciYRGB"),
                 ("colorSpaceTimeline", "Rec.709 Gamma 2.4")):
        print(f"  {k}={v} ->", proj.SetSettings({k: v}))
mp = proj.GetMediaPool()
if proj.GetTimelineCount():
    tl = proj.GetTimelineByIndex(1)
else:
    clip = mp.ImportMedia([CLIP])[0]
    tl = mp.CreateTimelineFromClips("img-0888", [clip])
proj.SetCurrentTimeline(tl)
item = tl.GetItemListInTrack("video", 1)[0]
print("project", proj.GetName(), "timeline", tl.GetName(), "fps", tl.GetSetting("timelineFrameRate"))

comp = item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else item.AddFusionComp()
tools = list(comp.GetToolList(False).values())
by_reg = {t.GetAttrs("TOOLS_RegID"): t for t in tools}
flc = by_reg.get(FLC_ID) or comp.AddTool(FLC_ID)
if not flc:
    sys.exit(f"Fusion refused tool {FLC_ID}; Film Look Creator may be colour-page only")
mi, mo = by_reg.get("MediaIn"), by_reg.get("MediaOut")
print("tools", sorted(by_reg), "flc", flc.GetAttrs("TOOLS_Name"))
img_inputs = [i for i in flc.GetInputList().values() if i.GetAttrs("INPS_DataType") == "Image"]
print("FLC image inputs:", [i.GetAttrs("INPS_ID") for i in img_inputs])
src = img_inputs[0]
src_id = src.GetAttrs("INPS_ID")
print("wire MediaIn->FLC", src_id, flc.ConnectInput(src_id, mi))
if not src.GetConnectedOutput():
    print("  fallback SetInput ->", flc.SetInput(src_id, mi.FindMainOutput(1)))
print("  FLC input connected to:", src.GetConnectedOutput())
print("wire FLC->MediaOut", mo.ConnectInput("Input", flc))
if not src.GetConnectedOutput():
    sys.exit("FLC image input is still unconnected; not rendering a blank video")

if LIST:
    for inp in flc.GetInputList().values():
        a = inp.GetAttrs()
        print(f"  {a.get('INPS_ID')!s:40} {a.get('INPS_Name')!s:32} {a.get('INPS_DataType')!s:12} "
              f"now={inp[comp.CurrentTime]!r}")
    sys.exit(0)

for k, v in OVERRIDES:
    try:
        val = float(v)
    except ValueError:
        val = v
    flc.SetInput(k, val)
    print(f"  set {k}={val!r} reads {flc.GetInput(k)!r}")

print("format mp4/H265 ->", proj.SetCurrentRenderFormatAndCodec("mp4", "H265"))
rs = {"TargetDir": OUT, "CustomName": "img-0888-film-look-creator", "SelectAllFrames": True,
      "FormatWidth": 1920, "FormatHeight": 1080, "VideoQuality": 20000, "EncodingProfile": "Main10",
      "ExportVideo": True, "ExportAudio": True}
print("render settings ->", proj.SetRenderSettings(rs))
job = proj.AddRenderJob() or proj.AddRenderJob()
t0 = time.time()
print("start ->", proj.StartRendering([job], False))
while proj.IsRenderingInProgress():
    time.sleep(2)
print("status", proj.GetRenderJobStatus(job), f"{time.time() - t0:.0f}s")
print(sorted(glob.glob(os.path.join(OUT, "img-0888-film-look-creator*"))))
pm.SaveProject()
