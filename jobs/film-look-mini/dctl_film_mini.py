#!/usr/bin/env python3
"""Runs ON the Mac mini. Builds Thatcher Freeman's utility-dctls film pipeline in a clip's Fusion comp and exports stills or a render.

    python3 dctl_film_mini.py <clip> <out_dir> <tag> --recipes a,b [--grey PNG] [--at SECONDS] [--fps 24]
                              [--size 1920x1080] [--render RECIPE]

Project `<tag>-utility-dctls`, colour managed so every DCTL receives scene-linear light: timeline Rec.709 / Linear,
output Rec.709 / Gamma 2.4, no tone or gamut mapping (measured accepted on 21.1, 2026-09-12). The clip's input transform
is whatever Resolve auto-detects. One timeline per recipe (`<clip stem>-<recipe>`), rebuilt on every run, plus a
`-null` timeline with no chain as the control. Each DCTL tool is loaded by file name, and its settings are set by their
UI names (the numbered slots take the DCTL's names once it loads; measured on Film Curve) and read back.

--grey imports a 16-bit PNG encoded with gamma 1/2.4, which the default 'Rec.709 (Scene)' input of a still decodes back
to linear (test/grey-ramp-gamma24.png) and exports a still per recipe, so the 0.18 patch can be checked against film_chain.py's prediction. The printer-lights gain ("solve" in the recipe) comes from
film_chain.solve_gain.

PRIOR ART: the looks are the utility-dctls DCTLs (blessdog/utility-dctls @ 693bf81), unmodified; this file only wires them.
"""
import os
import sys
import time

import film_chain

API = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
os.environ.setdefault("RESOLVE_SCRIPT_API", API)
os.environ.setdefault("RESOLVE_SCRIPT_LIB",
                      "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so")
sys.path.append(os.path.join(API, "Modules"))
import DaVinciResolveScript as dvr  # noqa: E402

DCTL_ID = "ofx.com.blackmagicdesign.resolvefx.DCTL"
SLOT_PREFIXES = ("sliderFloatParam", "sliderIntParam", "valueBoxParam", "checkBoxParam", "comboBoxParam", "colorPicker")


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


CLIP, OUT, TAG = (os.path.abspath(a) if i < 2 else a for i, a in enumerate(sys.argv[1:4]))
RECIPE_NAMES = [r for r in (arg("--recipes") or "").split(",") if r]
GREY = arg("--grey")
AT = float(arg("--at", "10"))
FPS = arg("--fps", "24")
W, H = (int(v) for v in arg("--size", "1920x1080").split("x"))
RENDER = arg("--render")
RECIPES = film_chain.load(RECIPE_NAMES)
os.makedirs(OUT, exist_ok=True)

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
    sys.exit("Resolve stayed busy for 5 minutes (modal dialog up or a render still stopping)")

SETTINGS = [("timelineFrameRate", FPS), ("timelineResolutionWidth", str(W)), ("timelineResolutionHeight", str(H)),
            ("colorScienceMode", "davinciYRGBColorManagedv2"), ("separateColorSpaceAndGamma", "1"),
            ("colorSpaceTimeline", "Rec.709"), ("colorSpaceTimelineGamma", "Linear"),
            ("colorSpaceOutput", "Rec.709"), ("colorSpaceOutputGamma", "Gamma 2.4"),
            ("colorSpaceOutputToneMapping", "None"), ("colorSpaceOutputGamutMapping", "None")]
name = f"{TAG}-utility-dctls"
proj = pm.LoadProject(name)
if not proj:
    proj = pm.CreateProject(name)
    if not proj:
        sys.exit(f"CreateProject({name!r}) returned None: Resolve busy, or the name is taken")
for k, v in SETTINGS:
    if proj.GetSettings().get(k) != v and not proj.SetSettings({k: v}):
        sys.exit(f"project setting {k}={v!r} refused (reads {proj.GetSettings().get(k)!r})")
print("project", name, {k: proj.GetSettings().get(k) for k, _ in SETTINGS})
mp = proj.GetMediaPool()


def pool_item(path):
    for c in mp.GetRootFolder().GetClipList():
        if c.GetClipProperty("File Path") == path:
            return c
    got = mp.ImportMedia([path])
    if not got:
        sys.exit(f"ImportMedia refused {path}")
    return got[0]


def fresh_timeline(tl_name, item):
    for i in range(proj.GetTimelineCount(), 0, -1):
        t = proj.GetTimelineByIndex(i)
        if t.GetName() == tl_name:
            mp.DeleteTimelines([t])
    tl = mp.CreateTimelineFromClips(tl_name, [item])
    if not tl:
        sys.exit(f"CreateTimelineFromClips({tl_name!r}) failed")
    proj.SetCurrentTimeline(tl)
    return tl


def dctl_entry(tool, dctl):
    sel = next(i for i in tool.GetInputList().values() if i.GetAttrs("INPS_ID") == "DCTLs")
    entries = [str(v) for v in (sel.GetAttrs().get("INPIDT_ComboControl_ID") or {}).values()]
    hits = [e for e in entries if os.path.basename(e) == dctl + ".dctl"]
    if len(hits) != 1:
        sys.exit(f"DCTL {dctl!r}: {len(hits)} matches in Resolve's list ({len(entries)} entries). Restart Resolve after installing.")
    return hits[0]


def add_stage(comp, prev, stage, gain, index):
    tool = comp.AddTool(DCTL_ID)
    if not tool:
        sys.exit("Fusion refused the DCTL tool")
    entry = dctl_entry(tool, stage["dctl"])
    tool.SetInput("DCTLs", entry)
    tool.SetAttrs({"TOOLS_Name": f"s{index}_{stage.get('role', stage['dctl']).replace(' ', '_')}"})
    slots = {}
    for inp in tool.GetInputList().values():
        a = inp.GetAttrs()
        if str(a.get("INPS_ID")).startswith(SLOT_PREFIXES):
            slots.setdefault(str(a.get("INPS_Name")), str(a.get("INPS_ID")))
    wrote = {}
    for pname, value in stage.get("params", {}).items():
        if pname not in slots:
            sys.exit(f"{stage['dctl']}: no setting named {pname!r}; it exposes {sorted(n for n in slots if n not in ('Check box',))}")
        value = gain if value == film_chain.SOLVE else value
        tool.SetInput(slots[pname], float(value))
        back = tool.GetInput(slots[pname])
        if back is None or abs(float(back) - float(value)) > 1e-4 * max(1.0, abs(float(value))):
            sys.exit(f"{stage['dctl']}: {pname} set {value!r} but reads {back!r}")
        wrote[pname] = round(float(back), 6)
    image_in = next(i for i in tool.GetInputList().values() if i.GetAttrs("INPS_DataType") == "Image")
    tool.ConnectInput(image_in.GetAttrs("INPS_ID"), prev)
    if not image_in.GetConnectedOutput():
        sys.exit(f"{stage['dctl']}: image input did not connect")
    print(f"    {tool.GetAttrs('TOOLS_Name')}: {entry} {wrote}")
    return tool


def build(item, recipe):
    comp = item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else item.AddFusionComp()
    reg = {t.GetAttrs("TOOLS_RegID"): t for t in comp.GetToolList(False).values()}
    for t in comp.GetToolList(False).values():
        if t.GetAttrs("TOOLS_RegID") == DCTL_ID:
            t.Delete()
    prev = reg["MediaIn"]
    gain = film_chain.solve_gain(recipe) if recipe else None
    for i, stage in enumerate(recipe["stages"] if recipe else [], 1):
        prev = add_stage(comp, prev, stage, gain, i)
    reg["MediaOut"].ConnectInput("Input", prev)
    return gain


def still(tl, path, seconds):
    app.OpenPage("color")
    hh = tl.GetStartTimecode().split(":")[0]
    s = int(seconds)
    tl.SetCurrentTimecode(f"{hh}:{s // 60:02d}:{s % 60:02d}:00")
    time.sleep(4)
    ok = proj.ExportCurrentFrameAsStill(path)
    print(f"  STILL {path} -> {ok}")
    return ok


def render(tl, stem):
    proj.SetCurrentTimeline(tl)
    app.OpenPage("deliver")
    print("  format mp4/H265 ->", proj.SetCurrentRenderFormatAndCodec("mp4", "H265"))
    proj.SetRenderSettings({"TargetDir": OUT, "CustomName": stem, "SelectAllFrames": True, "FormatWidth": W,
                            "FormatHeight": H, "VideoQuality": 80000 if W >= 3840 else 40000,
                            "EncodingProfile": "Main10", "ExportVideo": True, "ExportAudio": True,
                            "ColorSpaceTag": "Same as Project", "GammaTag": "Same as Project"})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    t0 = time.time()
    proj.StartRendering([job], False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    print("  status", proj.GetRenderJobStatus(job), f"{time.time() - t0:.0f}s")
    print(f"  RENDERED {os.path.join(OUT, stem + '.mp4')}")


sources = []
if GREY:
    g = pool_item(os.path.abspath(GREY))
    # Scripting refuses every Input Gamma value on a PNG still (21.1, measured), so the frame is encoded to match
    # the default input instead; the -null timeline's 0.18 patch at code 125 is the check that the decode is exact.
    print("grey frame input as assigned:", repr(g.GetClipProperty("Input Color Space")), "/", repr(g.GetClipProperty("Input Gamma")))
    sources.append(("grey", g, 1))
clip = pool_item(CLIP)
print("clip input as auto-detected:", repr(clip.GetClipProperty("Input Color Space")), "/", repr(clip.GetClipProperty("Input Gamma")))
stem = os.path.splitext(os.path.basename(CLIP))[0].lower().replace("_", "-")
sources.append((stem, clip, AT))

render_tl = None
for label, item, seconds in sources:
    for rname in ["null"] + RECIPE_NAMES:
        recipe = RECIPES.get(rname)
        tl_name = f"{label}-{rname}"
        print(f"\n[{tl_name}]")
        tl = fresh_timeline(tl_name, item)
        gain = build(tl.GetItemListInTrack("video", 1)[0], recipe)
        if gain is not None:
            print(f"  printer-lights gain {gain:.6g}")
        still(tl, os.path.join(OUT, f"{tl_name}.png"), seconds)
        if label == stem and rname == RENDER:
            render_tl = (tl, f"{stem}-{rname}")
pm.SaveProject()
if RENDER:
    if not render_tl:
        sys.exit(f"--render {RENDER!r} is not among --recipes")
    print(f"\n[render {render_tl[1]}]")
    render(*render_tl)
    pm.SaveProject()
