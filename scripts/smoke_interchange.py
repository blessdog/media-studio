#!/usr/bin/env python3.12
"""Interchange smoke: auto-editor FCPXML -> editable Resolve timeline.

Proves the architecture's load-bearing beam: edits computed OUTSIDE Resolve
arrive as an editable timeline via ImportTimelineFromFile.
"""
import sys
from pathlib import Path

import DaVinciResolveScript as dvr

ROOT = Path(__file__).resolve().parent.parent
FCPXML = ROOT / "outputs" / "smoke" / "talky-cut.fcpxml"

def die(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

resolve = dvr.scriptapp("Resolve")
if resolve is None:
    die("no connection")
pm = resolve.GetProjectManager()
proj = pm.LoadProject("media-studio-smoke") or pm.GetCurrentProject()
if not proj:
    die("no project")
mp = proj.GetMediaPool()

timeline = mp.ImportTimelineFromFile(str(FCPXML), {"timelineName": "smoke-interchange"})
if not timeline:
    die("ImportTimelineFromFile returned None")

items = timeline.GetItemListInTrack("video", 1) or []
print(f"VERIFY imported timeline '{timeline.GetName()}': {len(items)} clips on V1")
for i, it in enumerate(items):
    print(f"  clip {i+1}: start={it.GetStart()} end={it.GetEnd()} dur={it.GetDuration()}")
if len(items) < 2:
    die("expected multiple clips from silence cuts, got fewer — interchange NOT proving cuts")
print("INTERCHANGE PASS: external cut decisions arrived as an editable timeline")
