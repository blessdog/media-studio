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
evidence: jobs/film-look-mini/scratch-dctl run2 grey stills, measured against film_chain.py; mini log /Volumes/BleSSD/media-studio/img-0006/dctl/run2.log
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

The grey frame reached the chain as gamma-2.4-decoded values, not 0.18, hence 99
rather than 125; see [[resolve-scripting-cannot-set-input-gamma-on-a-still]].
Clamp's default also clamps at 1.0, so recipes switch `Clamp Max` off.

Related: [[film-look-creator-renders-on-the-mini-through-a-fusion-comp]].
