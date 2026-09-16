---
id: resolve-scripting-sets-a-clip-input-only-with-the-split-off
kind: verdict
conflict-key: how-to-set-a-clip-input-colour-space-by-script
status: live
supersedes: []
verified-on: 2026-09-16
scope: Resolve Studio 21.1 on the MacBook, davinciYRGBColorManagedv2, timeline Rec.709 / Linear, output Rec.709 / Gamma 2.4; one DJI Osmo Action 5 Pro HEVC clip (DJI_20260916114233_0001_D.MP4, tagged bt709) imported by script. Not tried on a PNG still
evidence: probe output in the 2026-09-16 session; jobs/film-look-mini/dctl_film_mini.py set_clip_input; pass-through control 0.56 / 0.68 / 0.80 display codes mean difference at 5 / 60 / 300 s (99th percentile 1.8 / 2.8 / 3.3)
asked-as:
  - SetClipProperty Input Color Space Bypass returns False
  - how do I stop Resolve colour management converting a log clip it has no input for
  - D-Log M clip auto detected as Rec.709 Scene in a colour managed project
---

**Resolve 21.1 scripting sets a clip's Input Color Space only while the project's
`separateColorSpaceAndGamma` is `'0'`, and only with the combined names. Set it
to `'0'`, call `SetClipProperty('Input Color Space', 'Linear')`, set it back to
`'1'`. The clip then reads `Rec.709 (Scene)` / `Linear`, which equals a
Rec.709 / Linear timeline, so the code values reach the Fusion comp unchanged.**

What was refused and what was accepted, on one clip:

| split | value | result |
|---|---|---|
| on | `Bypass`, `Rec.709 Gamma 2.4`, `Linear`, `Rec.709 Linear` | False |
| on | `Rec.709`, `Rec.2020`, `DaVinci WG` | True (gamut only; gamma stays `Rec.709`) |
| on | Input Gamma `Linear`, `Gamma 2.4`, `Rec.709`, `Bypass` | False |
| off | `Rec.709 Gamma 2.4`, `Linear` | True |
| off | `Bypass` | False |

Why it matters: the clip is tagged bt709, so Resolve auto-assigns
`Rec.709 (Scene)` and would linearise D-Log M as if it were Rec.709. The project
default (`colorSpaceInput`) does not override the tag.

The control: a timeline with no stages exported stills that equal the file's own
decoded values raised to 1/2.4 (the output encoding), within 0.56 to 0.80
display codes on average.

Not tested: whether the same split-off route sets a PNG still's input, which
[[resolve-scripting-cannot-set-input-gamma-on-a-still]] found impossible with
the split on.

Related: [[osmo-d-log-m-into-resolve-goes-through-the-idt-dctl]].
