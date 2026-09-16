---
id: the-osmo-wav-leads-its-mp4-audio-by-about-120-ms
kind: verdict
conflict-key: is-the-osmo-action-5-pro-wav-in-sync-with-its-mp4
status: live
supersedes: []
verified-on: 2026-09-16
scope: DJI Osmo Action 5 Pro, two clips shot 2026-09-16 (DJI_20260916114233_0001_D, DJI_20260916154133_0004_D), each with a same-named 48 kHz stereo WAV exactly as long as the MP4's AAC track; the MP4 track is taken as the picture-sync reference, which is NOT checked against a visual event
evidence: jobs/film-look-mini/audio_lag.py, 10 s windows searched within +-1 s. Clip 0004 at 20/60/120/200/280/330 s, lag -115.0/-118.4/-117.2/-116.1/-104.5/-115.4 ms, r +0.23 to +0.51. Clip 0001 at 20/60/120/200/280 s, -120.9/-121.3/-120.6/-119.6/-117.6 ms, r +0.41 then -0.25 to -0.44. After delaying clip 0004's WAV 5,556 samples and muxing it onto the Resolve render, the same check against the render's audio (itself identical to the camera track, lag 0, r 1.000) gave median 0.0 ms, five windows within 3 ms, 280 s at +11 ms. docs/CINEMATIC-PIPELINE-VERIFY.md row 30
asked-as:
  - is the Osmo WAV file in sync with the video
  - how far off is the DJI WAV audio from the MP4
  - how much do I delay the Osmo Action 5 Pro WAV
---

**The WAV the Osmo Action 5 Pro writes beside each clip starts at the same
moment as the MP4, but its sound arrives about 116 to 121 ms earlier than the
same sound in the MP4's own audio track. Delay the WAV by the measured lead
before putting it under the picture.**

Measured on two clips: 116 ms on clip 0004 (median of six windows) and 118 to
121 ms on clip 0001. The two recordings match only weakly (r 0.23 to 0.51), and
on clip 0001 the sign of the match flips between windows. So the MP4 track is
processed differently from the WAV, not just a copy of it. Clip 0001's ledger
row 29 said "best match at 122 ms with inverted polarity". That was this lead,
and the polarity is not constant.

Route used on clip 0004: `ffmpeg -i <render>.mp4 -i <clip>.WAV -map 0:v:0
-map 1:a:0 -c:v copy -af adelay=5556S:all=1 -c:a aac_at -b:a 320k -t
<video duration> <out>.mp4`, then `audio_lag.py <render>.mp4 <out>.mp4` to
confirm about 0 ms. Measure each clip; the lead differed by 5 ms between the two.

NOT known: which of the two tracks matches the picture. The MP4 track is the
camera's own mux, so it is the reference here. Frame strips around the two
loudest onsets in clip 0004 showed singing, with no contact event sharp
enough to settle it. Also not known: the firmware version, and whether the lead
depends on the mic setup.

Related: [[sync-the-osmo-wav-inside-resolve-with-autosyncau]] (doing the sync in
Resolve by waveform instead), [[osmo-d-log-m-into-resolve-goes-through-the-idt-dctl]].
