---
id: ryan-approved-the-utility-dctls-film-look-with-400-grain
kind: verdict
conflict-key: which-film-look-is-approved-for-ryans-footage
status: live
supersedes: []
verified-on: 2026-09-12
scope: iPhone 17 Pro log clip IMG_0006 (Final Cut Camera HEVC, Resolve detected Apple Log 2), 1080p24, rendered by Resolve Studio 21.1 on the Mac mini; not yet seen on DJI Osmo Action 5 Pro D-Log M or on other scenes
evidence: Ryan, 2026-09-12, "img-0006-rich-halation-grain-400.mp4 looks good"; grades/film-look/evidence/2026-09-12-approved-look-img-0006-before-after.jpg; render at /Volumes/BleSSD/media-studio/img-0006/knobs/img-0006-rich-halation-grain-400.mp4
asked-as:
  - which film look did Ryan approve
  - what grade do I put on new footage
  - locked film emulation recipe for the studio
---

**Ryan's approved film look is the recipe `rich-halation-grain-400` in
`jobs/film-look-mini/dctl-film-recipes.json`, built only from Thatcher Freeman's
utility-dctls and rendered by `jobs/film-look-mini/dctl_film_mini.py` on the mini.
His words: "img-0006-rich-halation-grain-400.mp4 looks good."**

The chain, in a Rec.709 Linear colour-managed timeline:

1. Clamp 0+
2. Halation, reflection 5 stops down
3. Clamp 0+
4. Film Grain as the negative: D max 2.6, 400 grains per pixel
5. Printer-lights gain, solved so mid grey stays at 0.18
6. Film Curve as the print: gamma 2.8, D min 0.06, D max 3.2

Rejected on the way, with his words:

- **Kodak 2383 print LUT.** "bland and washed out".
- **Film Look Creator.** Its default clipped shadows and glowed. Hand-tuning it stopped at "No, this is not the way. There's already a full GitHub library of these."
- **100 grains per pixel.** "lower the grain strength".
- **1600 grains per pixel.** Rendered and shown, not picked.

Still open: he chose no panel from the knob ladder
(`jobs/film-look-mini/evidence/2026-09-12-img-0006-knob-ladder-sheet.jpg`), so print
contrast stays at 2.8 and the Black Point fade stays off. The look has not been
seen on Osmo footage.

Related: [[utility-dctls-film-chain-in-resolve-matches-its-published-math]].
