---
id: film-look-creator-renders-on-the-mini-through-a-fusion-comp
kind: procedure
conflict-key: how-to-apply-film-look-creator-by-script
status: live
supersedes: []
verified-on: 2026-09-12
applies-when: a clip needs Resolve's Film Look Creator (Studio ResolveFX) applied and rendered without anyone clicking in the colour page, including on the Mac mini
not-when: the look is a LUT or CDL only; SetLUT / ApplyGradeFromDRX on the colour node graph is simpler
route: TimelineItem.AddFusionComp(); comp.AddTool("ofx.com.blackmagicdesign.resolvefx.FilmLook"); connect MediaIn to the tool's image input "Source" (found by INPS_DataType == "Image", verified with GetConnectedOutput()); connect MediaOut "Input" to the tool; set inputs by ID (colorContrast2, grainAmount, halationAmount, inputColorSpace ...); render mp4/H265. Script: jobs/film-look-mini/flc_mini.py
sibling: none
asked-as:
  - apply Film Look Creator with a script
  - render the film look on the Mac mini with Resolve
  - the Resolve API can't add ResolveFX to a node
  - Film Look Creator settings names for scripting
---

**The colour-page API cannot add a ResolveFX, but a Fusion comp can: Film Look
Creator is a Fusion OFX tool, `ofx.com.blackmagicdesign.resolvefx.FilmLook`,
and every one of its settings is scriptable by input ID.**

Measured 2026-09-12 on the Mac mini (M1, 8 GB, Resolve Studio 21.1.0 activated):
IMG_0888.mov, iPhone SDR HEVC 1080p 29.97, 33 s. Default look
(`globalPreset` GlobalPresetDefault65, Core Look Cinematic, contrast 1.25,
subtractive sat 1.2, halation, bloom, grain, flicker, gate weave on; input and
output colour space follow the timeline). Rendered to H.265 Main 10 in 49 s.

The one trap: the tool's image input is `Source`, not `Input`.
`ConnectInput("Input", mediaIn)` returns False and would render with no picture.

12 s frame, 0 to 255:

| | darkest 1% | brightest 1% | contrast | saturation |
|---|---|---|---|---|
| original | 47 | 241 | 42 | 116 |
| Kodak 2383 LUT chain on SDR | 36 | 219 | 45 | 100 |
| Film Look Creator default | 30 | 238 | 48 | 120 |

Film Look Creator keeps the whites and the colour that the print LUT lost on
regular video. Ryan's verdict on the look is still pending.

Other ResolveFX the mini's Fusion page registers (100 in total, `fusion.GetRegList(1)`,
2026-09-12) include CineFocus, DepthMap, LensBlur, NoiseReduction, Relight,
CinematicHaze, HalationPlugin, FilmGrain, SoftSharpenSkin and Vignette. Magic Mask is
NOT among them. Key input IDs read back from a live comp:

| tool | inputs that matter |
|---|---|
| CineFocus | `apertureEnhanced` 0.5, `focusDistance` 0.5, `focusLocationXY` point (0.5,0.5), `focusExtendRange`, `depthMapQuality` |
| NoiseReduction | `neighbourhoodWidth` frames either side, `temporalLumaThresh` 0 (a no-op until raised), `temporalMotionThresh` 50, `spatialLumaThresh` |
| LensBlur | `BlurStrength` 4, `ShapeType`, `Anamorphism` 1 |
| Relight | `lightSourceType` point, `reflBright` 1, `reflFallOff` 0.5, `lightPosXYZX` 0.25 |
| CinematicHaze | `inputColorSpace` timeline, `depthMapSource` internal, `scalingIsOn` 1 |

Mini prerequisites, done once: Studio activation and Preferences > System >
General > External scripting = Local, both in Resolve's GUI.

Related: [[resolve-21-1-installer-needs-14-gb-on-the-startup-disk]],
[[a-print-lut-needs-a-cineon-working-space-in-resolve]].
