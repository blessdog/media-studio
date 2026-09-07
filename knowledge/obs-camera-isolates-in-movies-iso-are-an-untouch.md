---
id: obs-camera-isolates-in-movies-iso-are-an-untouch
kind: open
conflict-key: should-we-obs-camera-isolates-in-movies-iso-are-an-untouch
status: live
supersedes: []
proven: false
verified-on: 2026-09-07
asked-as:
  - OBS camera isolates in movies/iso are an untouched multicam B-roll lane
  - obs camera isolates in movies iso are an untouch
  - why is ingest.py like this
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## OBS camera isolates in movies/iso are an untouched multicam B-roll lane

**Why it matters:** Six *-cam.mp4 isolates (Sept 5 and 7 sessions, one 15GB with no matching program recording) exist beside the program recordings and no ingest lane reads them; a cut-in to the camera is the cheapest visual variety in a screen-recording video and currently impossible

**Where it lands:** `/Users/SSDrive/movies/iso/, studio/ingest.py`

**First step:** probe the -cam files, confirm they share a start with the program recording (OBS starts both on one press), then add them as a second video asset on V2 in build_ir with a cut-in verb

Bookmarked 2026-09-07 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
