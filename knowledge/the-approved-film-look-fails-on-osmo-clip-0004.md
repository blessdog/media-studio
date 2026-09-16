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

Seen at 5 s, the plain D-Log M conversion next to the look, not measured:
whites turn cream-grey, skin moves toward orange-red, a milky haze spreads from
the bright door, and the frame reads flat. Measured on the same frame (darkest
1% / brightest 1% / luma std / mean max-min channel): converted 46/255/64.0/21.2,
look 28/240/69.8/24.1. So the whole-frame numbers say "more contrast" while the
picture reads flatter. Whole-frame statistics are not the verdict here, his eyes are.

The mechanism is NOT diagnosed. Candidates, none tested: the recipe was tuned on
one iPhone clip with a different exposure and scene; this clip is overexposed in
camera (1.06% of pixels at code 255 as shot, the door); the Osmo's own
sharpening and wide lens.

What his verdict does not say: whether the D-Log M conversion alone is
acceptable, and whether the look fails on clip 0001 too (no verdict was given
there).

Next, already asked for (2026-09-16, "there are loads of free, high quality
ways"): [[compare-other-free-film-emulators-on-osmo-d-log-]].
Related: [[ryan-approved-the-utility-dctls-film-look-with-400-grain]] (true on
IMG_0006 only), [[reshoot-the-osmo-test-with-nd-filters-arriving-2]].
