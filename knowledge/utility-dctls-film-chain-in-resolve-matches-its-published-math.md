---
id: utility-dctls-film-chain-in-resolve-matches-its-published-math
kind: procedure
conflict-key: how-to-run-the-utility-dctls-film-pipeline-by-script-in-resolve
status: live
supersedes: []
verified-on: 2026-09-12
applies-when: building a film emulation from Thatcher Freeman's utility-dctls (Film Curve, Film Grain, Halation, Clamp, Multiplication Function) on the Mac mini's Resolve Studio 21.1, by script
not-when: the look is Resolve's own Film Look Creator (see film-look-creator-renders-on-the-mini-through-a-fusion-comp) or a print LUT on a colour node (see a-print-lut-needs-a-cineon-working-space-in-resolve)
route: jobs/film-look-mini/dctl_film_mini.py with recipes in jobs/film-look-mini/dctl-film-recipes.json; film_chain.py solves the printer-lights gain
sibling: none
asked-as:
  - how do I apply Thatcher Freeman utility DCTLs by script
  - does the Film Curve DCTL chain hold mid grey in Resolve
  - DCTL settings in a Fusion comp have generic slot names
evidence: grey stills on the mini at /Volumes/BleSSD/media-studio/img-0006/dctl/, measured against film_chain.py; mini log /Volumes/BleSSD/media-studio/img-0006/dctl/run2.log
---

**Wire each DCTL as a `ofx.com.blackmagicdesign.resolvefx.DCTL` tool in the clip's
Fusion comp, in a colour-managed project whose timeline is Rec.709 / Linear and
output Rec.709 / Gamma 2.4 with no tone or gamut mapping. Resolve then runs the
chain exactly as the DCTL source reads: a plain-Python copy of the formulas
predicted every grey patch within 1 display code.**

How it works, measured 2026-09-12:

- The tool's `DCTLs` list is filled only when Resolve starts. DCTLs installed
  while it runs show `DCTL_LIST_EMPTY_NAME` until a graceful restart.
- Entries read like `film-look/thatcher/Film Curve.dctl`. After `SetInput("DCTLs", entry)`
  the numbered slots (`sliderFloatParam0`, `valueBoxParam3`, `checkBoxParam0`…)
  take the DCTL's own UI names in declaration order, so settings are set by name.
- `SetSettings` accepted `colorSpaceTimelineGamma = 'Linear'` with
  `separateColorSpaceAndGamma = '1'`.
- The README chain is Clamp 0+, Film Curve (negative), a gain for printer
  lights, and Film Curve (print). The gain that holds 0.18 is bisected in
  `film_chain.py`; the print offset makes no difference once the gain is solved.

Grey patches, measured display code (predicted):

| recipe | 0 | 0.045 | 0.18 in | 1.0 |
|---|---|---|---|---|
| readme-defaults | 23 (23) | 59 (59) | 111 (111) | 173 (173) |
| rich (neg γ0.6, print γ2.8, Dmax 3.2) | 13 (13) | 29 (29) | 99 (99) | 203 (203) |
| rich + Film Grain negative | 24 (25) | 28 (28) | 92 (92) | 226 (225) |

That table came from a frame whose values reached the chain gamma-2.4-decoded
(0.18 arrived as 0.1167), and the predictions above are at those delivered values;
see [[resolve-scripting-cannot-set-input-gamma-on-a-still]]. Re-run with the
gamma-2.4 fixture: the no-chain control put 0.18 at code 125 and every recipe held
0.18 at 125, all nine patches within 1 code of the model.

Two clamps matter:
- Clamp's default also clamps at 1.0, so recipes switch `Clamp Max` off.
- **Put a Clamp 0+ after Halation.** Its red-shift matrix pushed IMG_0006's
  saturated teal below zero, and the negative Film Curve logged that into white
  and black speckles: 872 speckle pixels on the bowl, 0 without Halation, 0 again
  with the second clamp. Film Grain clamps its own input, so its recipe showed 3.

Halation at `Reflection exposure lost` -5 (default -3) is invisible on IMG_0006:
against the same chain without it, mean difference 0.035 display codes and 129 of
2,073,600 pixels moved by more than 2 codes. A visible glow needs a value nearer the default.

What each knob did on IMG_0006 at 30 s, one setting changed from the look with Halation
and a 400-grain Film Grain negative (darkest 1% / brightest 1% / fine grain, display codes):

| knob | down | now | up |
|---|---|---|---|
| print gamma 2.2 / 2.8 / 3.4 | 35 / 199 | 26 / 211 | 20 / 220 |
| print D max 2.6 / 3.2 / 4.0 | 29 / 219 | 26 / 211 | 27 / 201 |
| Black Point 0 / 0.5 / 1.5 nits | 26 | 33 | 47 (whites unchanged) |
| Film Grain grains per pixel 100 / 400 / 1600 | grain 7.4 | 3.8 | 2.0 |

- **Print gamma moves both ends** and saturation with them (17.0 to 23.2).
- **Print D max barely touches blacks in this look**, because the grain negative sets the floor; it mostly dims the whites.
- **Grains per pixel is the grain strength.** Grain halves each time it is quadrupled and tone does not move, as the
  source's Normal(np, np(1-p)) sampling predicts.
- **Halation stays faint.** With grain blurred out, -3 stops added 0.6 codes of red in shadows beside bright areas and -1.5
  added 1.8. The default Base Blur Amount is 3 thousandths of frame width, about 6 px at 1080p.

Evidence: `jobs/film-look-mini/evidence/2026-09-12-img-0006-knob-ladder-sheet.jpg`.

Related: [[film-look-creator-renders-on-the-mini-through-a-fusion-comp]].
