---
id: render-4k-footage-at-4k
kind: verdict
conflict-key: what-resolution-should-a-graded-render-be
status: live
supersedes: []
verified-on: 2026-09-16
scope: renders made for Ryan to watch from 4K camera footage (DJI Osmo Action 5 Pro, 3840x2160), through jobs/film-look-mini/dctl_film_mini.py on the MacBook with Resolve Studio 21.1; delivery spec tools/render-preset.py osmo-4k-h265
evidence: Ryan, 2026-09-16, on the 1080p render and 2x-enlarged crops of clip 0004, "they all look terrible. very pixulated. like an old vhs camera. why are you not rendering in 4k?" 4K windows of the first 30 s on the MacBook, H.265 Main 10 at about 80 Mbps: camera conversion alone 26 s; conversion plus rich-halation-grain-400 493 s (about 96 min for the 350 s clip). The 1080p full render of the look took 547 s
asked-as:
  - why are you not rendering in 4k
  - what resolution should the film look render at
  - the render looks pixelated like an old VHS camera
---

**Render 4K footage at 4K. `dctl_film_mini.py` now takes the clip's own
resolution unless `--size` is given (commit 8eec86b).**

The 1080p default came from the grain work on clip 0001
([[a-4k-clip-on-a-1080p-timeline-thins-per-pixel-grain]]): the look was approved
on a 1080p iPhone clip, so the 4K Osmo frame was scaled down to match. Nobody
asked Ryan whether 1080p was acceptable, and the project's own delivery preset
(`tools/render-preset.py`, osmo-4k-h265) was already 3840x2160. Shown on a
Retina screen, 1080p is enlarged 2x and read as "pixulated". The agent made it
look worse by enlarging 1080p crops 2x with nearest-neighbour scaling for a
side-by-side.

Cost at 4K on the MacBook: the camera conversion alone runs faster than real
time (26 s per 30 s). The utility-dctls look is about 16x slower (493 s per
30 s), mostly Film Grain drawn on 4x the pixels. So render a short window first
(`--window 0,30`) before committing to a full look render.

Related: [[the-approved-film-look-fails-on-osmo-clip-0004]],
[[osmo-clip-0004-was-shot-at-about-iso-3200]].
