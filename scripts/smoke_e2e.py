#!/usr/bin/env python3.12
"""Phase-0 end-to-end smoke: project -> import -> timeline -> markers -> render.

Run with Resolve open (GUI or -nogui):
  RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting" \
  RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so" \
  PYTHONPATH="$RESOLVE_SCRIPT_API/Modules" python3.12 scripts/smoke_e2e.py

Every stage prints VERIFY lines from observed state, never from return values
alone (this API returns False/None silently on failure).
"""
import os
import sys
import time
from pathlib import Path

import DaVinciResolveScript as dvr

ROOT = Path(__file__).resolve().parent.parent
MEDIA = sorted((ROOT / "outputs" / "smoke").glob("clip*.mp4"))
RENDER_DIR = ROOT / "outputs" / "smoke" / "render"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
PROJECT = "media-studio-smoke"

def die(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

resolve = dvr.scriptapp("Resolve")
if resolve is None:
    die("cannot connect — is Resolve running with external scripting = Local?")
print(f"connected: {resolve.GetProductName()} {resolve.GetVersionString()}")

pm = resolve.GetProjectManager()

# -- project (idempotent: reuse if it exists, else create) --------------------
proj = pm.LoadProject(PROJECT) or pm.CreateProject(PROJECT)
if not proj:
    die("could not create or load project")
print(f"project: {proj.GetName()}")

# -- import media --------------------------------------------------------------
mp = proj.GetMediaPool()
root_folder = mp.GetRootFolder()
existing = {c.GetClipProperty("File Path") for c in (root_folder.GetClipList() or [])}
to_import = [str(p) for p in MEDIA if str(p) not in existing]
if to_import:
    items = mp.ImportMedia(to_import)
    if not items:
        die("ImportMedia returned nothing")
clips = root_folder.GetClipList() or []
have = [c for c in clips if c.GetClipProperty("File Path") in {str(p) for p in MEDIA}]
print(f"VERIFY media pool: {len(have)}/{len(MEDIA)} smoke clips present")
if len(have) != len(MEDIA):
    die("media pool count mismatch")

# -- timeline (append-only, as the API demands) --------------------------------
tl_name = f"smoke-{int(time.time())}"
timeline = mp.CreateEmptyTimeline(tl_name)
if not timeline:
    die("CreateEmptyTimeline failed")
ok = mp.AppendToTimeline(have)
items = timeline.GetItemListInTrack("video", 1) or []
print(f"VERIFY timeline '{tl_name}': {len(items)} clips on V1 (expected {len(have)})")
if len(items) != len(have):
    die("timeline clip count mismatch")

# -- markers --------------------------------------------------------------------
start = timeline.GetStartFrame()
for i, color in enumerate(["Red", "Blue", "Green"]):
    added = timeline.AddMarker(i * 240 + 1, color, f"beat-{i+1}", f"smoke marker {i+1}", 1)
markers = timeline.GetMarkers() or {}
print(f"VERIFY markers: {len(markers)} on timeline (expected 3)")
if len(markers) != 3:
    die("marker count mismatch")

# -- render ---------------------------------------------------------------------
proj.SetCurrentTimeline(timeline)
fmt_ok = proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
print(f"format mp4/H264 accepted: {fmt_ok}")
proj.SetRenderSettings({
    "TargetDir": str(RENDER_DIR),
    "CustomName": "smoke-e2e",
})
job1 = proj.AddRenderJob()
print(f"AddRenderJob first call -> {job1!r}  (documenting the known silent-fail quirk)")
if not job1:
    job1 = proj.AddRenderJob()
    print(f"AddRenderJob retry -> {job1!r}")
if not job1:
    die("AddRenderJob failed twice")

if not proj.StartRendering([job1], isInteractiveMode=False):
    die("StartRendering returned False")
t0 = time.time()
while proj.IsRenderingInProgress():
    if time.time() - t0 > 300:
        die("render timeout (300s)")
    time.sleep(2)
status = proj.GetRenderJobStatus(job1)
print(f"render status: {status}")
if status.get("JobStatus") != "Complete":
    die(f"job not complete: {status}")

outs = sorted(RENDER_DIR.glob("smoke-e2e*"))
if not outs:
    die("no render output file found")
print(f"OUTPUT: {outs[-1]}")
print("SMOKE PASS — ffprobe verification is the caller's job (Verifier doctrine)")
