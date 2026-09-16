---
id: sync-the-osmo-wav-inside-resolve-with-autosyncau
kind: open
conflict-key: should-we-sync-the-osmo-wav-inside-resolve-with-autosyncau
status: live
supersedes: []
proven: false
verified-on: 2026-09-16
asked-as:
  - Sync the Osmo WAV inside Resolve with AutoSyncAudio
  - can Resolve line up the WAV with the video by waveform from a script
  - add the external audio file to the film look render automatically
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## Sync the Osmo WAV inside Resolve with AutoSyncAudio

**Why it matters:** The Osmo's WAV leads its MP4 audio by 116-121 ms (clips 0001 and 0004); today the fix is a hand-measured offset and an ffmpeg remux after the render, which a new clip can silently get wrong if its lead differs

**Where it lands:** `jobs/film-look-mini/dctl_film_mini.py (pool_item / fresh_timeline)`

**First step:** Add --audio WAV: import the WAV, call MediaPool.AutoSyncAudio([clip, wav], {resolve.AUDIO_SYNC_MODE: resolve.AUDIO_SYNC_WAVEFORM, resolve.AUDIO_SYNC_RETAIN_EMBEDDED_AUDIO: False}) (DaVinciResolveScript.pyi lines 18-22, 120-122, 1269-1273), build the timelines from the synced clip, then check the render's audio against the camera track with jobs/film-look-mini/audio_lag.py (expect about 0 ms; the remux on clip 0004 measured median 0.0 ms)

Bookmarked 2026-09-16 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
