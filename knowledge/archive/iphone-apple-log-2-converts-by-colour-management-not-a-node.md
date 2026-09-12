---
id: iphone-apple-log-2-converts-by-colour-management-not-a-node
kind: verdict
conflict-key: how-to-convert-iphone-apple-log-in-resolve-by-api
status: superseded
supersedes: []
verified-on: 2026-09-12
scope: DaVinci Resolve Studio 21.1.0 on macOS, iPhone 17 Pro Apple Log 2 ProRes 422 HQ (IMG_0883.MOV, 1080p60); not re-measured for iPhone 15/16 Apple Log or for Osmo D-Log M, which Resolve has no built-in space for
evidence: grades/film-look/evidence/2026-09-12-iphone-apple-log-2-three-stages.jpg; outputs/projects/2026-09-12-iphone-log-test/delivery/ (gitignored renders)
asked-as:
  - my iPhone log footage looks washed out in Resolve
  - how do I convert Apple Log 2 without making a CST node
  - set a clip input color space from a script
  - apply a film LUT to iPhone footage automatically
---

**iPhone Apple Log 2 needs no node and no LUT to become normal-looking video.
Switch the project to colour management and set the clip's input colour space;
Resolve 21.1 has Apple Log 2 built in. A Rec.709 print LUT on node 1 then
behaves correctly because the node works in Rec.709.**

The calls, all returning True and reading back on 2026-09-12:

    proj.SetSettings({"colorScienceMode": "davinciYRGBColorManagedv2"})
    proj.SetSettings({"colorSpaceTimeline": "Rec.709 Gamma 2.4"})
    proj.SetSettings({"colorSpaceOutput": "Rec.709 Gamma 2.4"})
    mediaPoolItem.SetClipProperty("Input Color Space", "Apple Log 2")
    timelineItem.GetNodeGraph().SetLUT(1, "film-look/melara/Rec709_Kodak_2383_D65.cube")

Measured on the 12 s frame (luma contrast as standard deviation, saturation as
mean HSV S, both 0 to 255):

| stage | contrast | saturation |
|---|---|---|
| Apple Log 2 as shot, YRGB, no transform | 36 | 23 |
| colour managed, input Apple Log 2 | 59 | 49 |
| plus Kodak 2383 print | 85 | 78 |
| frame pulled from the H.265 render | 84 | 78 |

Why the clip looked washed out: `tools/ingest-osmo.py` stamps a plain DaVinci
YRGB project, which is right for Osmo D-Log M (the DJI LUT is the transform)
and wrong for any camera whose log Resolve can decode itself. A fresh managed
project's output defaults to `Rec.709 (Scene)`, so the output must be set too.

The 2383 print at full strength pushed saturation to 78, stronger than the
spec's muted palette; the node's key output gain is not scriptable, so easing
it is a GUI step.

Related: [[a-yrgb-project-timeline-colour-space-is-one-combined-key]],
[[osmo-d-log-m-into-resolve-goes-through-the-idt-dctl]].
