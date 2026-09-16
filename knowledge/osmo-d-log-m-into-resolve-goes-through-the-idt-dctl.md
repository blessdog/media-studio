---
id: osmo-d-log-m-into-resolve-goes-through-the-idt-dctl
kind: procedure
conflict-key: how-to-convert-osmo-action-5-pro-d-log-m-in-resolve
status: live
supersedes: []
verified-on: 2026-09-16
applies-when: a clip from the DJI Osmo Action 5 Pro (or any DJI D-Log M source) needs to become a usable image in Resolve, on either a colour-managed DaVinci Wide Gamut timeline or a plain Rec.709 one
not-when: the clip is older DJI D-Log (Mavic 2 era, Phantom, X7); that is the curve the CST's "DJI D-Log" entry actually implements, so the CST is right for those
route: approved film look (utility-dctls, Fusion comp): jobs/film-look-mini/dctl_film_mini.py --input dji-action5-dlogm, which sets the clip input to 'Linear' (pass-through on the Rec.709 / Linear timeline), then DJI Action 5 D-Log M to DWG.dctl with Output Transfer Function Linear, then Gamut Primaries Conversion.dctl DaVinci Wide Gamut to Rec.709, then the recipe. Colour node chains: scene-referred: node 1 = DCTL film-look/thatcher/DJI Action 5 D-Log M to DWG.dctl (thatcherfreeman/dwg-transforms @ 22f2134, fit to real Action 5 footage), output DaVinci Intermediate, then grade in DWG. Display-referred: node 1 = LUT film-look/dji/DJI OSMO Action 5 Pro D-Log M to Rec.709 V1.cube (DJI's official file). Both are installed by tools/grade-library.py install; recipe in grades/film-look/README.md
sibling: none
asked-as:
  - how do I convert D-Log M footage in DaVinci Resolve
  - what color space transform settings for the Osmo Action 5 Pro
  - the CST has DJI D-Log but not D-Log M, which one do I pick
  - D-Log M looks wrong after the color space transform
---

**D-Log M is not the curve Resolve's Color Space Transform calls "DJI D-Log".
Convert it with a transform built for D-Log M: Thatcher Freeman's Action 5
IDT DCTL for a DaVinci Wide Gamut timeline, or DJI's own LUT for a Rec.709 one.**

Why: DJI never published the D-Log M math. The CST's DJI entries implement the
older Mavic-era D-Log, and forum threads (Blackmagic forum t=186378, DJI forum
thread-290442, MavicPilots 141460) all report the same wrong-looking result from
feeding D-Log M through them. The DCTL in dwg-transforms is a curve fit to shot
Action 5 footage; DJI's cube is DJI's own answer, and its header says it is the
Mavic 3 Pro D-Log M LUT reused for this camera.

Measured 2026-09-12: both files downloaded, hashed (sha256 in
`grades/film-look/manifest.json`), installed under Resolve's LUT folder
`film-look/`, and re-hashed in place by `tools/grade-library.py verify`.
Measured 2026-09-16 on the first clip off the camera (DJI_20260916114233_0001_D,
4K 29.97 HEVC 10-bit, tagged bt709, which ffprobe cannot tell from Normal mode):
the conversion gives natural contrast with nothing crushed, which is the sign the
clip really is D-Log M. The pass-through that feeds it is checked in
[[resolve-scripting-sets-a-clip-input-only-with-the-split-off]]. Evidence:
`jobs/film-look-mini/evidence/2026-09-16-osmo-dji-0001-dlogm-approved-look-sheet.jpg`
(as shot, converted, approved look at 5 / 60 / 300 s). Resolve colour management
cannot do this step itself: 21.1 has no D-Log M input.
NOT measured: DJI's cube on real footage. Ryan's verdict on the look is pending.

Related: [[the-native-resolve-mcp-server-works-over-stdio]] (the API surface
that applies these files to nodes: SetLUT, ApplyGradeFromDRX, SetCDL).
