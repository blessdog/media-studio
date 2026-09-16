---
id: osmo-clip-0004-was-shot-at-about-iso-3200
kind: verdict
conflict-key: why-does-the-osmo-indoor-clip-look-like-low-light
status: live
supersedes: []
verified-on: 2026-09-16
scope: DJI Osmo Action 5 Pro (firmware field 10.00.16.13), auto exposure, D-Log M, 4K 29.97, clip DJI_20260916154133_0004_D (inside the shed, door open to daylight); ISO read from an undecoded metadata field whose identity is inferred, not documented
evidence: exiftool 13.55 `-ee -u -G3` on the clip. ShutterSpeed (decoded) 1/200 on 3,989 of 10,489 frames, the rest 1/110 to 1/199. Undecoded field Dvtm_ac204_3-2-3-1 (float) is 3200 on 7,220 frames and 1,646 to 4,174 on the rest. It behaves like ISO on both clips: pinned at 3200 while the shutter moves from 1/199 to 1/115; on sunny clip 0001, 217 to 650 at 1/2000 and 6,400 to 9,937 at 1/89 to 1/55. ExifTool maps ISO to field 3-2-2-1 for the Action 4 (dvtm_ac203) and maps nothing for the Action 5. 5 s stills, median Rec.709 luma: face 183 as shot, 160 converted, 163 look; dark wall 134 / 84 / 62; whole frame 152 / 107 / 96
asked-as:
  - is it my camera settings
  - why does the Osmo footage look like low light when the room was not dark
  - what ISO did the Osmo Action 5 Pro shoot at
  - how do I read ISO and shutter speed from a DJI Osmo clip
---

**Clip 0004 was shot at about ISO 3200 with a 1/110 to 1/200 s shutter, picked
by auto exposure. That is why it looks like low-light footage: the small sensor
is working at high gain, and the camera's noise reduction smears the detail.**

Ryan, 2026-09-16: "it looks low light but its not actually that dark where the
shot came from". The numbers agree that the face is not dark: it sits at
luma 160 of 255 after conversion, a normal skin level. What reads as low light
is the texture. A 1:1 crop of the face shows waxy, smeared skin, which is the
signature of noise reduction at high ISO. The film look then darkens the
surroundings (dark wall 84 to 62) and adds grain on top of the camera's noise.

Why a room that looks fine to the eye makes the camera climb to ISO 3200: at
the Osmo's fixed f/2.8, 1/200 s and ISO 3200 is about EV 5.6, ordinary indoor
light. Eyes adapt; the sensor does not. DJI's auto exposure keeps the shutter
fast, which helps the stabiliser, and raises gain instead of slowing the
shutter. Sunny clip 0001 shows the same ladder: shutter first down to 1/200,
then gain.

How to count the fix before shooting: at 29.97 fps a 1/60 s shutter gathers
200/60 = 3.3 times the light of 1/200, so this room would need about ISO 960
instead of 3200. At 24 fps, 1/50 gives 4 times, about ISO 800. Set shutter and
an ISO ceiling by hand (Pro mode), add light on the subject, and use ND outside
([[reshoot-the-osmo-test-with-nd-filters-arriving-2]]).

To read the settings again: `exiftool -ee -u -G3 -s -n -ShutterSpeed
-Dvtm_ac204_3-2-3-1 <clip>`. The ISO field name is an inference from the
pattern above. Confirm it by filming a card at a known manual ISO before
trusting it as ISO.

Related: [[the-approved-film-look-fails-on-osmo-clip-0004]].
