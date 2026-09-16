---
id: a-4k-clip-on-a-1080p-timeline-thins-per-pixel-grain
kind: verdict
conflict-key: why-is-film-grain-weaker-on-4k-footage-on-a-1080p-timeline
status: live
supersedes: []
verified-on: 2026-09-16
scope: Resolve Studio 21.1, utility-dctls Film Grain (400 grains per pixel) in a clip's Fusion comp, a 3840x2160 Osmo Action 5 Pro clip on a 1920x1080 timeline, compared with the 1920x1080 iPhone clip IMG_0006 the look was approved on
evidence: jobs/film-look-mini/evidence/2026-09-16-osmo-dji-0001-dlogm-approved-look-sheet.jpg (before) and -scaled-first.jpg (after). grain = mean 5x5 high-pass std in the flattest 10% of 16 px blocks (luma 40 to 220), approved still minus its no-grain twin. IMG_0006 at 100 / 400 / 1600 grains per pixel 7.16 / 3.60 / 1.83 (clean 0.27). Osmo at 400, 5 s: 1.60 (clean 0.68) unscaled, 3.28 (clean 0.59) scaled first; 300 s: 1.88 (clean 0.54, 12 blocks) unscaled. Resolve estimated 11,449 s to render the 5 min 12 s Osmo clip at 1080p on the mini
asked-as:
  - why is the film grain weaker on my 4K footage
  - does Fusion process a clip at timeline resolution or source resolution
  - grain looks different on Osmo footage than on the iPhone clip
---

**On a 1080p timeline, the 4K Osmo clip came out with less than half the grain of
the approved 1080p look at the same setting: 1.60 against 3.60. The clip's Fusion
comp runs at source resolution, so Film Grain is drawn on 4K pixels and averaged
four-to-one by the downscale. Averaging four independent samples halves the
noise, which predicts 1.8. Scaling the frame to 1080p before any stage brought it
back to 3.28 at the same 5 s frame.**

The same cause explains the render estimate: 11,449 s for 312 s of footage,
against 265 s for IMG_0006's 114 s at 1080p.

Two fixes were considered:

- **Scale to the timeline size before any stage. This is the route.**
  `jobs/film-look-mini/dctl_film_mini.py` does it (`resize_first`, a Fusion
  BetterResize). Measured 2026-09-16 at 5 s: grain 3.28 (clean 0.59), against
  1.60 before and 3.60 approved. The converted frame moved 0.5 to 2.5 codes on
  average against the unscaled one (resampling on foliage), so framing and tone
  held. The full 1080p render estimate dropped from 11,449 s on the mini to
  about 550 s on the MacBook. Two things changed at once there, the machine
  and the scaling, so the estimate does not isolate the scaling.
- Lowering grains per pixel by (1080/2160)^2 to 100 would also restore the
  strength, but the grain would still be drawn at 4K, so it keeps the render cost
  and a different grain size.

A 4K delivery is a separate verdict. At 4K, 400 grains per pixel gives the
approved per-pixel strength, but each grain is half the size on screen.

Related: [[ryan-approved-the-utility-dctls-film-look-with-400-grain]],
[[utility-dctls-film-chain-in-resolve-matches-its-published-math]].
