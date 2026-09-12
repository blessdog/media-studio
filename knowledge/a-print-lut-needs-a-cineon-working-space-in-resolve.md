---
id: a-print-lut-needs-a-cineon-working-space-in-resolve
kind: verdict
conflict-key: how-to-convert-iphone-apple-log-in-resolve-by-api
status: live
supersedes: [iphone-apple-log-2-converts-by-colour-management-not-a-node]
verified-on: 2026-09-12
scope: Resolve Studio 21.1.0, davinciYRGBColorManagedv2, a Kodak 2383 print emulation LUT (Juan Melara's, grey axis identical to Resolve's shipped one) on node 1; iPhone 17 Pro Camera-app ProRes Log (converted as Apple Log 2 by mistake; it is Apple Log, see iphone-camera-app-prores-log-is-apple-log-not-log-2) and iPhone SDR HEVC
evidence: grades/film-look/evidence/2026-09-12-kodak-2383-fed-rec709-vs-cineon.jpg; Melara's page ("PFE LUTs expect log film scans in Rec709 colour space as their input"); the 33-point grey-axis comparison of the two 2383 cubes
asked-as:
  - my iPhone log footage looks washed out in Resolve
  - the film print LUT looks too contrasty and saturated
  - what input does the Kodak 2383 LUT expect
  - apply a film LUT to iPhone footage automatically
---

**A print film emulation LUT expects LOG input (Cineon, Rec.709 primaries), not
display Rec.709. By script, give the project a colour-managed working space of
Rec.709 / Cineon Film Log for BOTH timeline and output, set each clip's input
colour space, and put the print LUT on node 1.**

    proj.SetSettings({"colorScienceMode": "davinciYRGBColorManagedv2"})
    proj.SetSettings({"separateColorSpaceAndGamma": "1"})
    proj.SetSettings({"colorSpaceTimeline": "Rec.709"})
    proj.SetSettings({"colorSpaceTimelineGamma": "Cineon Film Log"})
    proj.SetSettings({"colorSpaceOutput": "Rec.709"})
    proj.SetSettings({"colorSpaceOutputGamma": "Cineon Film Log"})
    # leave the clip input to Resolve's auto-detection (Camera-app ProRes Log is Apple Log)

Output equals timeline, so Resolve adds no second transform after the print; the
print itself turns log into display Rec.709. A clip WITHOUT the print therefore
looks like flat log in the viewer, by design. For an iPhone SDR clip Resolve
auto-assigns `Rec.709 (Scene)` / `Rec.709` and refuses `'Rec.709 Gamma 2.4'`
once the split toggle is on; the auto value is correct.

Measured on the 12 s frame of IMG_0883.MOV (Apple Log 2), 0 to 255 scale:

| node 1 fed | contrast | saturation |
|---|---|---|
| display Rec.709 (the superseded claim's route) | 85 | 78 |
| Cineon log, print on | 67 | 68 |
| Cineon log, print bypassed | 37 | 39 |

The superseded claim was right that Apple Log 2 converts by colour management
and wrong that a print LUT behaves on display Rec.709: that route pushed
contrast and saturation well past the print's intent.

Related: [[resolve-ntsc-rates-compile-as-non-drop-frame-strings]],
[[osmo-d-log-m-into-resolve-goes-through-the-idt-dctl]].
