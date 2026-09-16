---
id: the-approved-film-look-fails-on-osmo-clip-0004
kind: verdict
conflict-key: does-the-approved-film-look-work-on-osmo-d-log-m-footage
status: live
supersedes: []
verified-on: 2026-09-16
scope: recipe rich-halation-grain-400 (utility-dctls, 400 grains per pixel) after the D-Log M conversion (dctl_film_mini.py --input dji-action5-dlogm), on Osmo Action 5 Pro clip DJI_20260916154133_0004_D (indoor shed, open bright door, 4K 29.97 scaled to 1080p first), rendered by Resolve Studio 21.1 on the MacBook
evidence: Ryan, 2026-09-16, on dji-20260916154133-0004-d-rich-halation-grain-400-wav.mp4, "looks like shit". jobs/film-look-mini/evidence/2026-09-16-osmo-dji-0004-dlogm-approved-look-sheet.jpg (as shot, converted, look at 5 s). docs/CINEMATIC-PIPELINE-VERIFY.md row 30
asked-as:
  - does the approved film look work on Osmo footage
  - Ryan did not like the film look on the DJI clip
  - should I put rich-halation-grain-400 on D-Log M footage
---

**Ryan rejected the approved iPhone film look on the second Osmo clip: "looks
like shit." Do not apply `rich-halation-grain-400` to Osmo footage as a default.**

The agent's reading of the 5 s frame, not Ryan's words and not measured:
whites turn cream-grey, skin moves toward orange-red, a milky haze spreads from
the bright door, and the frame reads flat. Measured on the same frame (darkest
1% / brightest 1% / luma std / mean max-min channel): converted 46/255/64.0/21.2,
look 28/240/69.8/24.1. So the whole-frame numbers say "more contrast" while the
picture reads flatter. Whole-frame statistics are not the verdict here, his eyes are.

His follow-up: "it looks low light but its not actually that dark where the shot
came from". Measured cause of the low-light look, upstream of any grade: the
camera ran about ISO 3200 at 1/110 to 1/200 s
([[osmo-clip-0004-was-shot-at-about-iso-3200]]). The look made it worse by
darkening the surroundings (dark wall 84 to 62) and adding grain over the
camera's noise. Not tested: whether the recipe fails on well-exposed Osmo
footage too. The recipe was tuned on one iPhone clip, and 1.06% of this clip's
pixels are at code 255 as shot (the door).

Second message, on a frame of the render: "grainy as all hell", and "is this the actual quality or a low res
sample?" It is the actual render, but it is 1920x1080 at 40.3 Mbps: `dctl_film_mini.py` renders at the
timeline size (default 1920x1080), a quarter of the camera's 3840x2160 pixels, so a Retina screen shows it
enlarged 2x. Same-region crops at 5 s
(`jobs/film-look-mini/evidence/2026-09-16-osmo-dji-0004-where-the-grain-comes-from.jpg`): the 4K original
through DJI's own LUT is the sharpest and cleanest; the 1080p conversion is softer; the 1080p look adds visible
grain texture and pink skin. The agent's reading of that sheet, not Ryan's. The whole-frame grain measure used
in row 29 gave 1.26 converted and 1.63 look here, lower than clip 0001's 3.28, so that measure does not match
what the eye sees on this clip and is not evidence either way.

Third and fourth messages, after 4K windows of the plain conversion and of the look (30 s each):
"they all look terrible. very pixulated. like an old vhs camera", then "the film emulation is not working with
the video from the dji". So the failure is not only the 1080p output
([[render-4k-footage-at-4k]]). The look is retired for DJI footage. At the same 5 s frame, set side by side at
normal size, DJI's own D-Log M LUT gives natural contrast. The Thatcher conversion the look is built on is
displayed with no tone curve and reads flat with clipped whites, and the look reads milky and pastel. That is the
agent's reading, not measured.

What his verdict does not say: whether the D-Log M conversion alone is
acceptable, and whether the look fails on clip 0001 too (no verdict was given
there).

Next, already asked for (2026-09-16, "there are loads of free, high quality
ways"): [[compare-other-free-film-emulators-on-osmo-d-log-]].
Related: [[ryan-approved-the-utility-dctls-film-look-with-400-grain]] (true on
IMG_0006 only), [[reshoot-the-osmo-test-with-nd-filters-arriving-2]].
