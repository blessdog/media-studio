# IPHONE-MULTICAM — can the iPhone 12 Pro and iPhone 14 Pro feed OBS Studio at the same time?

*Research report, 2026-07-21. Report-before-build: nothing here is wired up;
the "live test" at the bottom is the gate before any purchase or plugin
install. Verification tags: **VERIFIED** = checked on this machine or a
primary document; **REPORTED** = credible secondary source, cited;
**UNVERIFIED** = could not confirm, needs the live test.*

## Ground truth (this machine, checked today)

- MacBook Pro 18,1 (M1 Pro, 16 GB), macOS 26.5.2 build 25F84. **VERIFIED**
  (`sw_vers`, `system_profiler`).
- OBS Studio 32.1.2 (verified previously on disk). **VERIFIED**
- macOS currently exposes exactly one iPhone camera device via Continuity
  Camera: model identifier `iPhone13,4`. **VERIFIED** — note that
  `iPhone13,4` decodes to iPhone 12 Pro **Max** (the 12 Pro is `iPhone13,3`);
  worth a glance at the phone's Settings → General → About, but nothing in
  this report changes either way. No iPhone is on USB right now.
- The NDI plugin for OBS Studio (DistroAV) is NOT installed; Reincubate Camo
  is NOT installed. **VERIFIED** (OBS plugin dirs, /Applications).
- The OBS scene collection uses ONE shared `Camera` input reused across all
  seven scenes. A second phone means a second, separate OBS input; the
  existing scene keys in obs-control-room are per-scene, so they are
  unaffected until new scenes are built around the second input. **VERIFIED**
  (obs-control-room README).

## The core question: two Continuity Camera iPhones at once

Apple's Continuity Camera turns any iPhone XR-or-later (iOS 16+) into a Mac
webcam, wireless or over a USB cable; both the iPhone 12 Pro and 14 Pro
qualify, and Lightning vs USB-C makes no difference to eligibility.
**REPORTED** (Apple support ecosystem docs, OWC setup guide).

Whether TWO of them can stream into the same app simultaneously is the
crux, and the honest answer is: **the weight of evidence says no — one
Continuity Camera stream at a time — but no primary Apple document states
the limit, and none of the sources tested macOS 26.** Ecamm (whose Mac
product lives or dies by camera support) documents "Continuity Camera
supports one iPhone at a time" and points multi-phone users at NDI apps
instead; OBS forum threads on multi-iPhone setups describe the second
device as flaky or absent; older Ventura-era articles state the
single-device limit outright. **REPORTED** (Ecamm help center,
venturepodcasting, OBS forums). Whether macOS 26.5 has lifted this is
**UNVERIFIED** — and that is exactly what the free live test below settles.
A second phone can definitely be *paired* (it shows up as an available
camera); the question is only whether it will *stream* while the first one
is streaming.

One wrinkle that matters for a mounted studio phone: the *wireless*
Continuity Camera path requires the phone locked, roughly stationary, in
landscape, with Wi-Fi and Bluetooth on — fine for an occasional webcam,
annoying for an appliance. A wired Lightning-to-USB connection removes
those conditions and charges the phone continuously while it works.
**REPORTED** (OWC guide, Apple support).

## Path B — NDI over the LAN (the standard second-camera answer)

If native simultaneity fails, the industry-standard answer is NDI: an app
on the iPhone publishes the camera as a network video source, and OBS
Studio receives it through the DistroAV plugin (the successor to obs-ndi —
the old plugin is dead on OBS 30+). DistroAV 6.2.1 requires OBS Studio
31.1.1+ and NDI Runtime 6.3+, so it is compatible with OBS 32.1.2.
**REPORTED** (DistroAV GitHub releases + wiki).

iOS sender apps, both current in 2026: **NDI Camera** (Vizrt's official
app, $19.99, last updated March 2026) and **NDICam** (Sienna, $9.99, full
NDI + NDI HX3 modes). **REPORTED** (App Store listings, ProVideo Coalition
comparison). Either runs on the 14 Pro. Requirements: both devices on the
same LAN with solid Wi-Fi (or the phone on Ethernet via a powered
Lightning hub); real-world latency over Wi-Fi is **UNVERIFIED** here —
commonly quoted in the "a few frames to ~200 ms" range, which matters
because a laggy camera cut lands late when switching scenes live. Measure
it in the live test if this path is needed. Two-hour-session reliability
over Wi-Fi is also **UNVERIFIED** and rides entirely on the studio's
wireless environment; wired power is mandatory (NDI streaming eats
battery faster than a Lightning cable can be optional).

This path is plumbing that feeds OBS Studio, so it sits inside the
three-software scope. It does add one OBS plugin (DistroAV) and one $10–20
phone app.

## Path C — Reincubate Camo (fallback, not first choice)

Camo supports iPhones wired or wireless and integrates with OBS Studio by
presenting a virtual camera. What could NOT be confirmed is whether Camo
can present TWO independent virtual cameras to OBS at once — its
multi-camera features read as mixing/switching multiple devices into ONE
output, which solves a different problem (that's a production surface, and
scope doctrine says no). **UNVERIFIED** single-output limit; current 2026
pricing also not confirmed. Camo stays a fallback: useful mainly as "one
phone on Camo + one phone on Continuity Camera" if both native streams
refuse to coexist AND NDI disappoints. **REPORTED/UNVERIFIED** (Camo docs,
TechCrunch Camo 2 coverage).

## Path D — HDMI out + capture card (ruled out for Lightning phones)

The Lightning Digital AV Adapter is not a clean HDMI output: internally it
is an AirPlay-style receiver with its own ARM chip that decodes a
compressed mirror of the screen, effectively 1600×900 upscaled to 1080p,
with visible compression artifacts and added latency — and it mirrors the
UI, notifications included. **REPORTED** (Panic's teardown, 9to5Mac).
That makes it unsuitable as a dedicated-camera path for the 12 Pro or
14 Pro regardless of capture card quality. (The USB-C iPhone 17 Pro can do
genuinely clean HDMI/USB video out with apps like Blackmagic Camera, but
it is the on-the-go phone, not a studio resident — noted and parked.)

## Long-session practicalities for a dedicated, mounted 14 Pro

Wired is the posture: a Lightning cable to the Mac (Continuity Camera) or
to power (NDI path) keeps the phone charged through a two-hour session and
sidesteps the wireless lock/landscape conditions. Continuity Camera
manages the phone's wake state itself while streaming; an NDI sender app
requires Auto-Lock set to Never while in use. **REPORTED**. Heat is real
but manageable: continuous capture + charging makes the phone warm, so the
mount class to want is open-backed (no sealed case), out of direct sun/
lights; the 14 Pro's only battery-health lever is iOS Optimized Battery
Charging (the 80% hard cap arrived with later models), so a studio
appliance phone simply lives near full charge — accepted cost, or a smart
plug on a schedule if it bothers you. **REPORTED**. Mount class: any
cold-shoe/tripod phone clamp or MagSafe-style stand; nothing exotic.

## Recommended path + the live test that proves it

**Recommendation:** keep the 12 Pro exactly as it is (the working
Continuity Camera webcam). For the 14 Pro, run the free native test FIRST;
only if it fails, go NDI (DistroAV 6.2.1 + NDICam at $9.99 as the cheaper
of the two current apps), phone on wired power. Camo is the fallback
behind both; HDMI capture is ruled out.

**The live test ($0, ~10 minutes, settles it on this exact rig):**
1. Plug the 14 Pro into the Mac via Lightning once, tap Trust.
2. Open OBS Studio. The existing shared `Camera` input keeps streaming the
   12 Pro.
3. Add ONE new macOS Video Capture Device source in any scratch scene and
   point it at the 14 Pro.
4. Watch whether both feeds render live at the same time. Try all three
   combos worth knowing: both wired, 14 Pro wired + 12 Pro wireless, both
   wireless.

If both render: native Continuity Camera multicam works on macOS 26.5 and
the second-camera question is closed for free. If the second source stays
black or kills the first: the one-stream limit is confirmed on this rig,
and the NDI path is the build — as its own small report-then-wire step,
not an assumption.

## Sources

- Ecamm: Continuity Camera in Ecamm — https://support.ecamm.com/en/articles/6952085-how-to-use-continuity-camera-as-a-webcam-in-ecamm
- Ecamm: phone cameras with Ecamm Live (NDI apps, NDICam pricing) — https://support.ecamm.com/en/articles/3865715-using-your-iphone-ipad-or-android-phone-camera-with-ecamm-live
- OWC: Continuity Camera + OBS power-user setup — https://www.owc.com/blog/the-iphone-makes-for-a-great-pro-webcam-how-to-get-setup-on-mac-and-windows
- OBS forums: multiple iOS devices — https://obsproject.com/forum/threads/multiple-ios-devices-with-obs.108251/
- DistroAV releases (6.2.1, OBS 31.1.1+, NDI 6.3+) — https://github.com/DistroAV/DistroAV/releases
- DistroAV installation wiki — https://github.com/DistroAV/DistroAV/wiki/1.-Installation
- ProVideo Coalition: NDI HX Camera vs NDICam — https://www.provideocoalition.com/comparison-newtek-ndi-hx-camera-app-vs-ndicam-app-both-for-ios/
- NDI Camera app (Vizrt, $19.99) — https://www.appbrain.com/appstore/ndi-hx-camera/ios-1477266080
- Panic blog: Lightning Digital AV Adapter teardown (AirPlay decoder, ~900p) — https://blog.panic.com/the-lightning-digital-av-adapter-surprise/
- 9to5Mac on the same finding — https://9to5mac.com/2013/03/01/the-lightning-digital-av-adapter-doesnt-do-native-1080p-out-possibly-because-it-is-an-airplay-receiver/
- TechCrunch: Camo 2 launch — https://techcrunch.com/2023/03/16/camo-2-launches-with-support-for-any-camera-new-effects-and-more/
- Apple: Continuity Camera overview — https://support.apple.com/102546
