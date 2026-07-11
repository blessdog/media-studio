#!/usr/bin/env python3.12
"""Headless smoke: poll for API readiness of a -nogui Resolve, then render.

Proves unattended operation: connect, load the smoke project, queue a render
of the existing timeline, verify completion. Run while Resolve runs -nogui.
"""
import sys
import time
from pathlib import Path

import DaVinciResolveScript as dvr

ROOT = Path(__file__).resolve().parent.parent
RENDER_DIR = ROOT / "outputs" / "smoke" / "render"

def die(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

# -- wait for the daemon to answer (fresh -nogui boot takes a moment) ---------
resolve = None
t0 = time.time()
while time.time() - t0 < 120:
    resolve = dvr.scriptapp("Resolve")
    if resolve is not None:
        break
    time.sleep(3)
if resolve is None:
    die("headless Resolve never answered within 120s")
print(f"connected headless after {time.time()-t0:.0f}s: {resolve.GetProductName()} {resolve.GetVersionString()}")

pm = resolve.GetProjectManager()
proj = pm.LoadProject("media-studio-smoke")
if not proj:
    die("could not load smoke project headless")
print(f"project loaded: {proj.GetName()}")

tls = [proj.GetTimelineByIndex(i + 1) for i in range(proj.GetTimelineCount())]
target = next((t for t in tls if t.GetName() == "smoke-interchange"), None)
if not target:
    die("smoke-interchange timeline not found")
proj.SetCurrentTimeline(target)

proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
proj.SetRenderSettings({"TargetDir": str(RENDER_DIR), "CustomName": "smoke-headless"})
job = proj.AddRenderJob() or proj.AddRenderJob()
if not job:
    die("AddRenderJob failed twice (headless)")
if not proj.StartRendering([job], isInteractiveMode=False):
    die("StartRendering returned False (headless)")
t0 = time.time()
while proj.IsRenderingInProgress():
    if time.time() - t0 > 300:
        die("headless render timeout")
    time.sleep(2)
status = proj.GetRenderJobStatus(job)
print(f"render status: {status}")
if status.get("JobStatus") != "Complete":
    die(f"headless job not complete: {status}")
outs = sorted(RENDER_DIR.glob("smoke-headless*"))
print(f"OUTPUT: {outs[-1] if outs else 'MISSING'}")
if not outs:
    die("no headless render output")
print("HEADLESS PASS")
