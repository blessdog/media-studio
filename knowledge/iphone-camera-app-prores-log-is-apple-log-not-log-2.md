---
id: iphone-camera-app-prores-log-is-apple-log-not-log-2
kind: verdict
conflict-key: which-log-does-the-iphone-camera-app-record
status: live
supersedes: [img-0883-built-in-camera-prores-log-is-likely-ap]
verified-on: 2026-09-12
scope: iPhone 17 Pro, iOS 26.6.2, built-in Camera app with ProRes Log (ProRes 422 HQ 1080p); Resolve Studio 21.1.0 auto-detection on the Mac mini
evidence: jobs/film-look-mini/film_mini.py run on IMG_0891.MOV (log at /Volumes/BleSSD/media-studio/img-0891/film_mini.log on the mini); ffprobe colour tags of IMG_0883 and IMG_0891
asked-as:
  - is iPhone ProRes Log Apple Log or Apple Log 2
  - which input color space for iPhone log footage in Resolve
  - Apple Log 2 in the regular camera app
  - why does my iPhone log footage look wrong after conversion
---

**The iPhone 17 Pro's built-in Camera app records ProRes Log as the ORIGINAL
Apple Log. Apple Log 2 comes only from Apple's Final Cut Camera app. Let
Resolve auto-detect the input space; do not type Apple Log 2 for Camera-app clips.**

Measured 2026-09-12 on IMG_0891.MOV, a Camera-app ProRes Log clip. Resolve
auto-detected `Apple Log` / `Apple Log` with the split colour-space toggle off,
and `Rec.2020 (Scene)` / `Apple Log` with it on. The file's colour tags read
primaries bt2020, matrix bt2020nc, which is Apple Log's gamut; Apple Log 2 uses
Apple Wide Gamut.

Final Cut Camera side, measured the same day on IMG_0004.MOV (metadata
`com.apple.proapps.appBundleID = com.apple.FinalCutApp.companion`): HEVC Rext 4:2:2
10-bit, 3840x2160, 30 fps, primaries tag `unknown`. Resolve auto-detected
`Apple Log 2` / `Apple Log`. Size 212,564,612 bytes for 57.3 s = about 223 MB a
minute, against about 3.1 GB a minute for the Camera app's 1080p60 ProRes Log.

Consequence: every IMG_0883 render this session set the input to Apple Log 2 by
hand, so that clip was converted with the wrong gamut. The measurements in
[[a-print-lut-needs-a-cineon-working-space-in-resolve]] still show the print
mechanism (display-fed vs Cineon-fed), but not a correct absolute look.

Related: [[film-look-creator-renders-on-the-mini-through-a-fusion-comp]].
