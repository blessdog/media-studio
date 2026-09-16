---
id: a-4k-clip-on-a-1080p-timeline-thins-per-pixel-grain
kind: verdict
conflict-key: why-is-film-grain-weaker-on-4k-footage-on-a-1080p-timeline
status: live
supersedes: []
verified-on: 2026-09-16
scope: Resolve Studio 21.1, utility-dctls Film Grain (400 grains per pixel) in a clip's Fusion comp, a 3840x2160 Osmo Action 5 Pro clip on a 1920x1080 timeline, compared with the 1920x1080 iPhone clip IMG_0006 the look was approved on
evidence: grain = mean 5x5 high-pass std in the flattest 10% of 16 px blocks (luma 40 to 220), approved still minus its no-grain twin. IMG_0006 at 100 / 400 / 1600 grains per pixel 7.16 / 3.60 / 1.83 (clean 0.27). Osmo at 400, 5 s: 1.60 (clean 0.68); 300 s: 1.88 (clean 0.54, 12 blocks). Resolve estimated 11,449 s to render the 5 min 12 s Osmo clip at 1080p on the mini
asked-as:
  - why is the film grain weaker on my 4K footage
  - does Fusion process a clip at timeline resolution or source resolution
  - grain looks different on Osmo footage than on the iPhone clip
---

**On a 1080p timeline, the 4K Osmo clip came out with less than half the grain of
the approved 1080p look at the same setting: 1.60 against 3.60. Mechanism, inferred
and not yet confirmed: the clip's Fusion comp runs at source resolution, so Film
Grain is drawn on 4K pixels and averaged four-to-one by the downscale.
Averaging four independent samples halves the noise, which predicts 1.8.**

The same cause explains the render estimate: 11,449 s for 312 s of footage,
against 265 s for IMG_0006's 114 s at 1080p.

Two fixes were considered:

- **Scale to the timeline size before any stage.** This is what
  `jobs/film-look-mini/dctl_film_mini.py` now does (`resize_first`, a Fusion
  BetterResize). Every source then gets the grain grid the look was approved on,
  and the work drops to a quarter. **Unverified:** the check that it restores
  about 3.6 has not run yet.
- Lowering grains per pixel by (1080/2160)^2 to 100 would also restore the
  strength, but the grain would still be drawn at 4K, so it keeps the render cost
  and a different grain size.

A 4K delivery is a separate verdict. At 4K, 400 grains per pixel gives the
approved per-pixel strength, but each grain is half the size on screen.

Related: [[ryan-approved-the-utility-dctls-film-look-with-400-grain]],
[[utility-dctls-film-chain-in-resolve-matches-its-published-math]].
