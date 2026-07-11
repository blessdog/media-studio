#!/usr/bin/env python3.12
"""Title-template smoke, zero-GUI edition: insert the agent-authored Fusion
title onto a fresh timeline via API, render it, leave an mp4 for human eyes.
"""
import sys
import time
from pathlib import Path

import DaVinciResolveScript as dvr

ROOT = Path(__file__).resolve().parent.parent
RENDER_DIR = ROOT / "outputs" / "smoke" / "render"
TITLE = "Media Studio Smoke"

def die(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

resolve = dvr.scriptapp("Resolve")
if resolve is None:
    die("no connection")
pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject() or pm.LoadProject("media-studio-smoke")
if not proj:
    die("no project")
mp = proj.GetMediaPool()

tl = mp.CreateEmptyTimeline(f"smoke-title-{int(time.time())}")
if not tl:
    die("CreateEmptyTimeline failed")
proj.SetCurrentTimeline(tl)

item = tl.InsertFusionTitleIntoTimeline(TITLE)
if not item:
    die(f"InsertFusionTitleIntoTimeline({TITLE!r}) returned None — template not in library?")
print(f"VERIFY inserted: {item.GetName()!r} dur={item.GetDuration()} frames")

proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
proj.SetRenderSettings({"TargetDir": str(RENDER_DIR), "CustomName": "smoke-title"})
job = proj.AddRenderJob() or proj.AddRenderJob()
if not job:
    die("AddRenderJob failed twice")
if not proj.StartRendering([job], isInteractiveMode=False):
    die("StartRendering failed")
t0 = time.time()
while proj.IsRenderingInProgress():
    if time.time() - t0 > 180:
        die("render timeout")
    time.sleep(2)
status = proj.GetRenderJobStatus(job)
if status.get("JobStatus") != "Complete":
    die(f"render incomplete: {status}")
outs = sorted(RENDER_DIR.glob("smoke-title*"))
if not outs:
    die("no output file")
print(f"OUTPUT: {outs[-1]}")
print("TITLE PASS — open the file; human eyes are the verdict")
