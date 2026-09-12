---
id: resolve-scripting-cannot-set-input-gamma-on-a-still
kind: verdict
conflict-key: how-to-feed-a-known-linear-test-frame-into-resolve-colour-management
status: live
supersedes: []
verified-on: 2026-09-12
scope: Resolve Studio 21.1.0 on the Mac mini, davinciYRGBColorManagedv2 with separate colour space and gamma, timeline Rec.709 / Linear, output Rec.709 / Gamma 2.4, a 16-bit PNG still imported by script
evidence: /Volumes/BleSSD/media-studio/img-0006/grey_gamma_probe.py output; grey-null still codes 0 5 25 44 69 104 152 217 255 equal to the stored codes of jobs/film-look-mini/archive/grey-ramp-rec709-scene.png
asked-as:
  - SetClipProperty Input Gamma returns False
  - how do I import a linear test chart into Resolve colour management
  - what transfer does Resolve use for a PNG still's Rec.709 Scene input
---

**Scripting cannot set a still's Input Gamma, and the still's default input,
Rec.709 (Scene), decodes as gamma 2.4. To feed a known linear value, store it as
`linear ** (1/2.4)` in a 16-bit PNG.**

`SetClipProperty('Input Gamma', v)` returned False for `Linear`,
`Linear (Scene)`, `Gamma 2.4`, `Rec.709 Gamma 2.4`, and even the current value
`Rec.709`. The clip read Input Color Space `Rec.709 (Scene)` and Input Gamma
`Rec.709` throughout.

A frame encoded with the BT.709 camera curve went through a timeline with no
effects and came out with every stored code unchanged under Gamma 2.4 output.
So the decode was V**2.4, not the camera curve. Its 0.18 patch reached the
DCTLs as 0.1167. The fixture is now `jobs/film-look-mini/test/grey-ramp-gamma24.png`;
the camera-curve one is in `jobs/film-look-mini/archive/`.

Related: [[utility-dctls-film-chain-in-resolve-matches-its-published-math]].
