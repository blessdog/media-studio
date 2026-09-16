---
id: denoise-high-iso-osmo-footage-with-resolve-s-noi
kind: open
conflict-key: should-we-denoise-high-iso-osmo-footage-with-resolve-s-noi
status: live
supersedes: []
proven: false
verified-on: 2026-09-16
asked-as:
  - Denoise high-ISO Osmo footage with Resolve's Noise Reduction plugin
  - the 4K Osmo video is noisy and grainy, how do we clean it up
  - can a script apply noise reduction in DaVinci Resolve
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## Denoise high-ISO Osmo footage with Resolve's Noise Reduction plugin before DJI's LUT

**Why it matters:** At 4K the plain conversion of clip 0004 shows the camera's ISO 3200 speckle noise plainly, and no grade or emulator hides it; without a scripted denoise step every Osmo render shot indoors under auto exposure looks like Ryan's 16:44 screenshot

**Where it lands:** `a Chain A script beside jobs/film-look-mini/dctl_film_mini.py; project osmo-0004-chain-a-probe`

**First step:** With Resolve open: non-managed project (colorScienceMode davinciYRGB, 3840x2160, 29.97), clip input left as imported, Fusion comp tool ofx.com.blackmagicdesign.resolvefx.NoiseReduction (id found in the Resolve 21.1 binary, never added by script yet), list its inputs by name, then TimelineItem.GetNodeGraph().SetLUT(1, 'film-look/dji/DJI OSMO Action 5 Pro D-Log M to Rec.709 V1.cube'); render --window 0,30 at 4K and compare with the undenoised DJI-LUT still in jobs/film-look-mini/evidence/2026-09-16-osmo-dji-0004-dji-looks-4k-sheet.jpg

**Blocked on:** Resolve open (Ryan quit it at 16:44 on 2026-09-16)

Bookmarked 2026-09-16 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
