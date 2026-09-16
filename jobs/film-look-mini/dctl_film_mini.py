#!/usr/bin/env python3
"""Runs where Resolve runs (the Mac mini for long renders, the MacBook for stills). Builds Thatcher Freeman's
utility-dctls film pipeline in a clip's Fusion comp and exports stills or a render.

    python3 dctl_film_mini.py <clip> <out_dir> <tag> [--recipes a,b] [--grey PNG] [--at S[,S...]] [--fps 24]
                              [--size WxH] [--render NAME[,NAME]] [--window START,END]
                              [--input NAME] [--recipe-file JSON]

Without --recipes it builds the recipe marked "approved" in the recipe file (Ryan's pick).

Project `<tag>-utility-dctls`, colour managed so every DCTL receives scene-linear light: timeline Rec.709 / Linear,
output Rec.709 / Gamma 2.4, no tone or gamut mapping (measured accepted on 21.1, 2026-09-12). The clip's input transform
is whatever Resolve auto-detects. One timeline per recipe (`<clip stem>-<recipe>`), rebuilt on every run, plus a
`-null` timeline with no chain as the control. Each DCTL tool is loaded by file name, and its settings are set by their
UI names (the numbered slots take the DCTL's names once it loads; measured on Film Curve) and read back.

--input NAME takes a camera conversion from the recipe file's "inputs" (e.g. dji-action5-dlogm, for footage Resolve
colour management cannot convert). The clip's input colour space is set to the entry's "clip_input" so Resolve passes the
code values through untouched, the entry's stages run ahead of every recipe, and an extra `-idt` timeline holds the
conversion alone: the "before" of a before/after. `-null` stays the no-stage control that proves the pass-through.

--size defaults to the clip's own resolution (4K Osmo footage renders at 4K). A source larger than --size is scaled to it
before any stage (Fusion otherwise runs the chain at source resolution, which thins per-pixel grain). --render takes
recipe names, and `idt` for the camera conversion alone. --at takes several times, one still each. --window START,END renders only that span (seconds).

--grey imports a 16-bit PNG encoded with gamma 1/2.4, which the default 'Rec.709 (Scene)' input of a still decodes back
to linear (test/grey-ramp-gamma24.png) and exports a still per recipe, so the 0.18 patch can be checked against film_chain.py's prediction. The printer-lights gain ("solve" in the recipe) comes from
film_chain.solve_gain.

PRIOR ART: the looks are the utility-dctls DCTLs (blessdog/utility-dctls @ 693bf81), unmodified; this file only wires them.
"""
import json
import os
import subprocess
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
RESIZE_ID = "BetterResize"
SLOT_PREFIXES = ("sliderFloatParam", "sliderIntParam", "valueBoxParam", "checkBoxParam", "comboBoxParam", "colorPicker")


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def source_size(path):
    # Ryan, 2026-09-16, on a 1080p render of a 4K Osmo clip: "very pixulated... why are you not rendering in 4k?"
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "json", path], capture_output=True, text=True, check=True)
    s = json.loads(probe.stdout)["streams"][0]
    return f"{s['width']}x{s['height']}"


CLIP, OUT, TAG = (os.path.abspath(a) if i < 2 else a for i, a in enumerate(sys.argv[1:4]))
RECIPE_NAMES = [r for r in (arg("--recipes") or "").split(",") if r] or [
    r for r in [film_chain.approved(arg("--recipe-file") or film_chain.RECIPES)] if r]
GREY = arg("--grey")
ATS = [float(t) for t in arg("--at", "10").split(",")]
FPS = arg("--fps", "24")
WINDOW = [float(t) for t in arg("--window").split(",")] if arg("--window") else None
W, H = (int(v) for v in (arg("--size") or source_size(CLIP)).split("x"))
RENDER = [r for r in (arg("--render") or "").split(",") if r]
RECIPES = film_chain.load(RECIPE_NAMES, arg("--recipe-file") or film_chain.RECIPES)
INPUT = film_chain.load_input(arg("--input"), arg("--recipe-file") or film_chain.RECIPES) if arg("--input") else None
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


def set_clip_input(item, value):
    # 21.1 scripting refuses every value while the project splits colour space and gamma, and accepts the combined
    # names with the split off (measured 2026-09-16 on the Osmo clip: 'Linear' accepted, 'Bypass' refused in both).
    proj.SetSettings({"separateColorSpaceAndGamma": "0"})
    ok = item.SetClipProperty("Input Color Space", value)
    proj.SetSettings({"separateColorSpaceAndGamma": "1"})
    got = (item.GetClipProperty("Input Color Space"), item.GetClipProperty("Input Gamma"))
    if not ok or proj.GetSettings().get("separateColorSpaceAndGamma") != "1":
        sys.exit(f"clip input {value!r} refused (reads {got!r})")
    drift = {k: proj.GetSettings().get(k) for k, v in SETTINGS if k.startswith("colorSpace") and proj.GetSettings().get(k) != v}
    if drift:
        sys.exit(f"toggling the colour space split changed project colour settings: {drift}")
    print(f"clip input set to {value!r}, reads {got!r}")


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


def resize_first(comp, prev, source):
    # Fusion runs a clip's comp at the SOURCE resolution. Film Grain is per pixel, so a 4K source graded for a 1080p
    # timeline got its grain averaged away in the downscale: 1.60 against the approved 3.60 (2026-09-16, Osmo clip).
    # Scaling first puts every source on the pixel grid the look was approved on, and quarters the work.
    tool = comp.AddTool(RESIZE_ID)
    tool.SetAttrs({"TOOLS_Name": "s0_resize_to_timeline"})
    tool.SetInput("Width", W)
    tool.SetInput("Height", H)
    tool.ConnectInput("Input", prev)
    got = (tool.GetInput("Width"), tool.GetInput("Height"))
    if tuple(int(v) for v in got) != (W, H) or not tool.Input.GetConnectedOutput():
        sys.exit(f"resize to {W}x{H} did not take (reads {got})")
    print(f"    s0_resize_to_timeline: {source[0]}x{source[1]} -> {W}x{H}")
    return tool


def build(item, recipe, pre=(), source=None):
    comp = item.GetFusionCompByIndex(1) if item.GetFusionCompCount() else item.AddFusionComp()
    reg = {t.GetAttrs("TOOLS_RegID"): t for t in comp.GetToolList(False).values()}
    for t in comp.GetToolList(False).values():
        if t.GetAttrs("TOOLS_RegID") in (DCTL_ID, RESIZE_ID):
            t.Delete()
    prev = reg["MediaIn"]
    if source and source != (W, H):
        prev = resize_first(comp, prev, source)
    gain = film_chain.solve_gain(recipe) if recipe else None
    for i, stage in enumerate(list(pre) + (recipe["stages"] if recipe else []), 1):
        prev = add_stage(comp, prev, stage, gain, i)
    reg["MediaOut"].ConnectInput("Input", prev)
    return gain


def timecode(tl, seconds):
    # Non-drop timecode counts whole frames at the nominal rate (30 for 29.97), so a frame index converts directly.
    nominal = round(float(FPS))
    f = tl.GetStartFrame() + round(seconds * float(FPS))
    return f"{f // (3600 * nominal):02d}:{f // (60 * nominal) % 60:02d}:{f // nominal % 60:02d}:{f % nominal:02d}"


def still(tl, path, seconds):
    app.OpenPage("color")
    tl.SetCurrentTimecode(timecode(tl, seconds))
    time.sleep(4)
    ok = proj.ExportCurrentFrameAsStill(path)
    print(f"  STILL {path} -> {ok}")
    return ok


def render(tl, stem):
    proj.SetCurrentTimeline(tl)
    app.OpenPage("deliver")
    print("  format mp4/H265 ->", proj.SetCurrentRenderFormatAndCodec("mp4", "H265"))
    span = {"SelectAllFrames": True}
    if WINDOW:
        span = {"SelectAllFrames": False, "MarkIn": tl.GetStartFrame() + round(WINDOW[0] * float(FPS)),
                "MarkOut": tl.GetStartFrame() + round(WINDOW[1] * float(FPS)) - 1}
    proj.SetRenderSettings({"TargetDir": OUT, "CustomName": stem, **span, "FormatWidth": W,
                            "FormatHeight": H, "VideoQuality": 80000 if W >= 3840 else 40000,
                            "EncodingProfile": "Main10", "ExportVideo": True, "ExportAudio": True,
                            "ColorSpaceTag": "Same as Project", "GammaTag": "Same as Project"})
    job = proj.AddRenderJob() or proj.AddRenderJob()
    t0 = time.time()
    proj.StartRendering([job], False)
    while proj.IsRenderingInProgress():
        time.sleep(2)
    status = proj.GetRenderJobStatus(job)
    print("  status", status, f"{time.time() - t0:.0f}s")
    if status.get("JobStatus") != "Complete":
        sys.exit(f"render {stem} ended {status.get('JobStatus')!r}, not Complete")
    print(f"  RENDERED {os.path.join(OUT, stem + '.mp4')}")


sources = []
if GREY:
    g = pool_item(os.path.abspath(GREY))
    # Scripting refuses every Input Gamma value on a PNG still (21.1, measured), so the frame is encoded to match
    # the default input instead; the -null timeline's 0.18 patch at code 125 is the check that the decode is exact.
    print("grey frame input as assigned:", repr(g.GetClipProperty("Input Color Space")), "/", repr(g.GetClipProperty("Input Gamma")))
    sources.append(("grey", g, [1], ()))
clip = pool_item(CLIP)
print("clip input as auto-detected:", repr(clip.GetClipProperty("Input Color Space")), "/", repr(clip.GetClipProperty("Input Gamma")))
if INPUT:
    set_clip_input(clip, INPUT["clip_input"])
stem = os.path.splitext(os.path.basename(CLIP))[0].lower().replace("_", "-")
sources.append((stem, clip, ATS, INPUT["stages"] if INPUT else ()))

render_tls = []
for label, item, times, pre in sources:
    size = tuple(int(v) for v in str(item.GetClipProperty("Resolution")).split("x")) if item.GetClipProperty("Resolution") else None
    for rname in ["null"] + (["idt"] if pre else []) + RECIPE_NAMES:
        recipe = RECIPES.get(rname)
        tl_name = f"{label}-{rname}"
        print(f"\n[{tl_name}]")
        tl = fresh_timeline(tl_name, item)
        gain = build(tl.GetItemListInTrack("video", 1)[0], recipe, () if rname == "null" else pre, size)
        if gain is not None:
            print(f"  printer-lights gain {gain:.6g}")
        for t in times:
            still(tl, os.path.join(OUT, f"{tl_name}.png" if len(times) == 1 else f"{tl_name}-t{t:g}.png"), t)
        if label == stem and rname in RENDER:
            window = f"-{WINDOW[0]:g}-{WINDOW[1]:g}s" if WINDOW else ""
            render_tls.append((tl, rname, f"{stem}-{rname}{window}"))
pm.SaveProject()
missing = set(RENDER) - {rname for _, rname, _ in render_tls}
if missing:
    sys.exit(f"--render {sorted(missing)} not among --recipes")
for tl, _, out_name in render_tls:
    print(f"\n[render {out_name}]")
    render(tl, out_name)
    pm.SaveProject()
