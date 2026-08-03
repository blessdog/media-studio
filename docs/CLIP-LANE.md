# CLIP-LANE — screen clip → SP-404 pad → track → video, in sync

*Written 2026-08-02. Companion to `docs/MUSIC-LANE.md` (pipelines A–E); this
document adds **pipeline F (clip capture)** and **pipeline G (trigger map)**.
Nothing here is built. Verification status on every claim: **[V]** verified
this session by exercising the machine, **[R]** read from a repo file, **[D]**
read from vendor documentation but not exercised, **[U]** unverified,
**[RYAN]** blocked on a decision.*

Ryan's ask, 2026-08-02, in two halves:

1. Draw a box over an Instagram reel / TikTok / X video playing on screen, hit
   record, and capture **that region's video plus the Mac's audio** into a
   library — without screen-recording the whole display and trimming later.
2. After the samples are chopped into a beat on the SP-404MK2, know **where in
   the finished track each sample fires**, so the meme video it came from can
   be dropped onto the Resolve timeline in time with the music.

Half 2 is the interesting one and it is nearly free. Half 1 needs almost no
code. Read §6 before agreeing to any of it.

---

## 1. The one idea this lane rests on

> **A sample is not a file. It is a pointer into a video, at an offset.**

If every sample in the library remembers *which clip it was cut from* and
*where in that clip it starts*, then a list of "sample X fired at 00:42.15"
is already a video edit — and not a rough one. The video can be chopped on
exactly the same in-points as the audio, because they are the same in-points.
Chop the audio at 2.1 s–2.6 s of the meme, and 2.1 s–2.6 s of the *picture*
lands on the timeline with it.

Everything below exists to produce and consume one artifact:

```
trigger-map.json   # [{sample_hash, track_start_secs, duration_secs}, ...]
```

Three independent producers (§4), one consumer (§5). That is the whole design.

---

## 2. Ground truth verified this session

### Capture — the entire engine is a built-in macOS command **[V]**

```
screencapture -v -R <x,y,w,h> -G <audio-device-UID> out.mov
```

Exercised in the scratchpad. A 640×360 rect produced **H.264 1280×720**
(Retina 2×) + **AAC 48 kHz stereo** in a single file, A/V locked by the OS —
no second recorder, no mux, no drift. Relevant flags **[V]** from
`screencapture` usage output:

| Flag | Effect |
|---|---|
| `-v` | record video instead of a still |
| `-R<x,y,w,h>` | capture an exact screen rect — **no drawing needed** |
| `-J video` | start the interactive **drag-a-box** recorder (the Cmd-Shift-5 UI) **[D]** |
| `-G<id>` | record audio from a named device |
| `-V<secs>` | hard length cap |
| `-D<display>` | pick the monitor — matters on the triple-monitor rig |
| `-x` | no shutter sound (keeps the sound out of the capture) |

`-G` takes the **CoreAudio device UID, not the display name** **[V]** — every
name form was rejected (`Capture audio device ... not found`). UIDs enumerated
this session with a CoreAudio Swift probe **[V]**:

| Device | UID |
|---|---|
| Computer Audio Input | `~:AMS2_Aggregate:0` |
| BlackHole 2ch | `BlackHole2ch_UID` |
| fifine Microphone | `AppleUSBAudioEngine:Unknown Manufacturer:fifine Microphone:1140000:2` |

### Two failures found by exercising, both silent **[V]**

1. **`Computer Audio Input` records digital silence.** Captured with
   `afplay` deliberately playing through it: `mean_volume: -91.0 dB`,
   `max_volume: -91.0 dB`. The file *looks* perfect — correct codec, correct
   sample rate, stereo, right duration. It contains nothing. A machine check
   that only probed streams would have passed this. **Browser audio must be
   routed somewhere before this works; it is not routed today.**
2. **Video and audio durations disagree.** Same file: video 1.800 s, audio
   4.049 s. Screen capture is variable-frame-rate — a still screen emits
   almost no frames. `tools/ingest-screensage.py:is_vfr()` already calls VFR
   "poison for the frame-integer model" **[R]**. A region showing a *playing*
   video has constant motion so this is far less severe in practice, but
   **every captured clip must be normalised to CFR on ingest**, and that code
   already exists in this repo.

### The SP-404MK2 exports its own trigger map **[D]**

This is the finding that makes half 2 cheap. Pattern export offers three modes:

- **SMF** → a **`.mid` file of the pattern's note data**
- **MULTIPAD** → one `.wav` per pad
- **BOUNCE** → one `.wav` of the whole pattern

Pad-to-note numbers are **fixed and documented**, offsettable but not
remappable. Bank A pad 1 = note 48 (C3), contiguous upward to pad 16 = note 63.
Mode A assigns one MIDI channel per bank; Mode B packs banks A–E onto Ch 1 and
F–J onto Ch 2. *(The two Roland sources reviewed disagree in their channel
wording; the exact channel layout is **[U]** until a MIDI monitor is pointed at
the device. It does not change the design — only a lookup table.)*

Pattern export "only includes the note messages from within the same bank" —
so **a multi-bank performance needs one export per bank** **[D]**.

### Ableton is a second, already-present source of truth **[V]**

`~/Music/Ableton/Live Recordings/thunderdome Project/thunderdome.als` — Ryan's
own project — is **gzip-compressed XML**, Ableton Live 12.4, 314 KB
uncompressed, containing `<AudioClip>`, `<MidiClip>`, `<CurrentStart>`,
`<CurrentEnd>`, `<SampleRef>`, and 16 `<MidiNoteEvent>` elements **[V]**.
188 `.als` files on disk. Clip positions and note events are readable with
`gzip` + an XML parser and no Ableton automation whatsoever.

### What is already built **[R]**

- `~/projects/blessdog/phase8_sp404/` — the sample library lane **already
  exists**: `ledger.py` (SHA-256 provenance ledger, atomic writes, `KINDS =
  oneshot|loop|track|stem`), `card.py` (SD card detection, refuses to guess),
  `convert.py`, `build.py`, `cli.py` (`add`/`stems`/`list`/`push`/`cards`).
- `tools/ingest-screensage.py` — already muxes multitrack screen captures,
  detects VFR, registers side assets, maps events onto the timeline **[R]**.
- `studio/registry.py` — SQLite asset ledger with hashes **[R]**.
- `tools/beat-grid.py`, `tools/edit-ir.py`, `tools/compile-ir.py` — beat grid,
  IR editing, OTIO → Resolve **[R]**.

---

## 3. Pipeline F — the clipper

```
media playing on screen
  → named rect (drawn once, reused forever)          MISSING (small)
  → screencapture -v -R <rect> -G <uid>              EXISTS (built into macOS)
  → CFR normalise + probe                            EXISTS (ingest-screensage)
  → register clip as a video asset                   EXISTS (studio/registry.py)
  → extract audio → phase8 ledger + SD card          EXISTS (phase8_sp404)
```

**The only genuinely missing piece is a rect store.** Drawing a box every time
is the friction, not the recording. Ripping twenty reels from the same browser
window means drawing the same box twenty times. So:

```
clip rect save ig-reel        # draw once (-J video / -i), remember it
clip ig-reel                  # every capture after that: no drawing
clip ig-reel --for 12         # hard cap the length
```

Bound to a Stream Deck key — Ryan has the hardware and his own plugin at
`~/projects/obs-control-room` — "record the reel window" becomes one press with
zero on-screen UI. That is the actual optimisation he asked for.

**Audio routing is the one real prerequisite.** State established 2026-08-02,
from CoreAudio and from Ryan's screen **[V]**:

- Loopback is installed, **running**, and functional. `com.rogueamoeba.ARK.driver`
  13.0.3 is its backing driver (Rogue Amoeba's shared engine — Loopback ships no
  HAL plug-in of its own, so its absence means nothing).
- **All four Loopback devices are toggled Off**, which is why CoreAudio
  publishes none of them: no `Loopback Audio`, no `Ableton OBS mix`, no
  `Ableton Virtual Out`, no `Loopback Audio 2`.
- `Loopback Audio` is additionally **broken**: ⚠️ "Missing Monitor Device", with
  `External Headphones` and `Headphone` both reporting **Device Missing** — the
  exact god-object failure `MUSIC-LANE.md` §4 predicted.
- `Computer Audio Input` (`~:AMS2_Aggregate:0`) exists but records **digital
  silence** (−91 dB measured) because it is wired as a *monitor* of the Off
  `Loopback Audio` device, and nothing feeds it.

**The plan is therefore the original one: a new, small, single-purpose device.**

| | |
|---|---|
| **Name** | `Clip Capture` |
| **Source** | **Brave Browser** (Ryan's actual browser — note the god device sources *Google Chrome*, which he does not use) |
| **Monitor** | his current output, so he still hears what he is clipping |
| **Then** | toggle it **On**, and pass its UID to `screencapture -G` |

Two sources, one monitor — the same shape as `Ableton Virtual Out` (2 entries)
rather than `Loopback Audio` (16). Nothing existing is edited or switched on.

**Do not write `Devices.plist` directly.** Loopback is running and rewrites that
file on quit, so an external edit is silently clobbered; and the file being
stale since 2025-12-21 while four devices exist in the UI proves it is not a
reliable store to author. Loopback exposes no CLI, no `.sdef`, no AppleScript
**[V]** — this is four clicks in a GUI Ryan already has open, and that is the
correct way to do it.

### BUILT + VERIFIED 2026-08-02 ✅

Ryan created `Clip Capture` in Loopback: **Sources** = Brave Browser +
Pass-Thru → **Output Channels** 1 & 2 → **Monitor** = Realtek USB Audio (so he
still hears what he clips). Toggled On. `Loopback Audio` left Off and untouched.

- **Published to CoreAudio** **[V]**, 2 in / 2 out, and it is the *only*
  Loopback device present:
  `com.rogueamoeba.Loopback::020C0EB0-C6BC-4019-8DEA-FFD14CBB8A00`
- **Audio reaches the capture** **[V]**. Proven by bandpass, not by eyeballing a
  level: a 1 kHz tone played in Brave raised the 900–1100 Hz band from
  **−42.4 dB mean (silent control) to −29.1 dB** — a ~13 dB rise in exactly the
  tone's band. Both `screencapture -G <uid>` and `ffmpeg -f avfoundation` see it.
- **A/V durations now agree** **[V]** — 8.050 s video vs 8.045 s audio, against
  the 1.8 s / 4.0 s split on a *static* region. VFR only bites when nothing
  moves, which a playing video never does. Normalising to CFR on ingest stays
  correct, but this is not the hazard it first looked like.

**Gotcha, and it is a real one for sampling** **[V]**: the device captures
**everything Brave plays**, not just the tab being clipped. A control recording
with the tone tabs closed still measured **−17.2 dB mean** — other Brave audio,
flowing constantly. Music in a background tab will bleed into every sample and
will not be obvious until the chop is on a pad. **Pause other Brave audio before
clipping**, or give clipping its own browser. Worth a check in the CLIP key.

**Levels are not yet characterised** **[U]**. In-band arithmetic suggests
roughly +12 dB of gain through the chain, but it cannot be measured cleanly
while background Brave audio is present. Re-measure against a genuinely silent
Brave before trusting captured levels — a clipped sample is a ruined sample.

> **Retracted:** an earlier pass in this session claimed automatic gain control,
> on the evidence that sources 20 dB apart captured at identical levels. That
> was a **confound, not AGC** — the constant background signal above swamped
> both tests. The error was declaring a result before running the silent
> control. Same lesson as `verify-by-exercising`, one level up: **measuring
> carefully is not the same as measuring the right thing. Run the control.**

---

### Pipeline F — BUILT, then MOVED OUT to `~/projects/rectum` ✅

**This lane no longer lives in media-studio** (Ryan, 2026-08-02). It is its own
repo, `rectum`, named for `rect` — the unit it operates on. `tools/clip.py`,
`tools/pickrect.swift` and `tools/audiodevices.swift` were built here, proven
here, and then moved; **nothing of pipeline F remains in this repo.**

Boundary, following `MUSIC-LANE.md` decision 1: **rectum never imports
media-studio.** It carries its own probe and ledger; the three repos join on
`clip_hash`. media-studio registers a clip when it enters an edit, blessdog's
sample ledger points back with `source_clip_hash` + `source_in_secs`.

```
cd ~/projects/rectum
python3 -m rectum displays          # left/right derived from the real arrangement
python3 -m rectum toggle left       # <- what the Stream Deck key calls
python3 -m rectum crop <hash>       # propose the video's rectangle
python3 -m rectum list | search <term>
```

Deck: the plugin becomes **Control Room**, with an OBS page and a rectum page
(Ryan, 2026-08-02) — one surface, one layout SSOT, one tripwire. See §3c.

**Exercised end to end** **[V]**: `start` → `status` ("RECORDING rect 'reel' for
2s") → `stop` → `1280x720 @ 30/1, 5.9s (VFR → CFR 30)`, SHA-256 recorded, WAV
emitted as **pcm_s16le / 48000 / 2ch** — exactly what the SP-404 imports.
Ground-truthed rather than trusted: the asset is in `registry.db`, and a frame
pulled at t=2s shows the real region, not a black rectangle.

**Two bugs found by exercising, neither visible from reading the code:**

1. **`start` hung any caller that captures output.** `screencapture` inherited
   the parent's stdout, so the pipe stayed open after `clip.py` exited and
   `subprocess.run(capture_output=True)` blocked forever — it wedged a 120 s
   smoke test. **This would have frozen the Stream Deck key**, which shells out
   exactly that way. Fixed with `DEVNULL` on all three streams plus
   `start_new_session=True`, which also keeps a recording alive if its launcher
   dies.
2. **`-v error` silently suppresses `volumedetect`.** The loudness check printed
   nothing and read as "no audio". A comment in `mean_volume()` now records the
   trap, because this is the exact check that catches a silent capture.

**Not yet exercised** **[U]**: `pickrect` compiles but has never been *run* — it
needs a human to drag a box. Its coordinate maths is derived from verified
facts (global points, top-left origin, primary-screen flip) but derivation is
not verification. **First real use is a test: draw a box over a known window and
confirm the capture contains that window.**

**Named `rectum`** (Ryan, 2026-08-02) — `rect` being the unit the whole thing
operates on. It gets its own Stream Deck page. Repo boundary: see §3c.

**Test material** **[RYAN, 2026-08-02]**:
- Track for the end-to-end run once the SP arrives —
  `https://www.youtube.com/watch?v=Fp9xuYeJako`
- Sampling source, Tyson fight — `https://www.youtube.com/watch?v=nm0OjxUEaSk`.
  Intended as a **bed**, not a stab: bell, punches, announcer and crowd running
  under the beat, faded up at chosen moments to build atmosphere. This is the
  case that forces duration + level envelope into the trigger map (§3b).

---

## 3b. REVISION — record the monitor, find the video afterwards (Ryan, 2026-08-02)

Ryan's redesign, and it is better than the saved-rect model: **stop choosing a
box before the shot.** One key per monitor, record the whole screen, and let the
system find the video inside the recording afterwards. You cannot un-crop a
capture, so capturing everything and deciding later is strictly more optionable.
It also deletes the one untested component in §3 — the rect picker.

**Premise correction first.** Ryan believed bongpot's ffmpeg Ken Burns /
zoom-pan work could be reused. It cannot **[V]**: media-studio contains **zero**
occurrences of `zoompan`, `ken burns` or `cropdetect`; and in bongpot the path
is *legacy being deliberately retired* — `docs/MEDIA-SYSTEM-PLAN.md:65` "retire
Ken Burns", `docs/PIPELINE.md:189` "dead weight". It also operated on **still
images**, a different problem from cropping a screen recording. Nothing to reuse.

**Display mapping, verified by exercising** **[V]**:

| Flag | Display | Ryan's name |
|---|---|---|
| `-D 1` | 3456 x 2234 built-in Retina | **RIGHT** (MacBook Pro) |
| `-D 2` | 1920 x 1080 external | **LEFT** |

No `-D 3` today — the rig is two displays, not three. This matches the existing
`Screen L` / `Screen R` OBS scene keys, so the deck's mental model already
exists and the same left/right vocabulary carries over.

### Finding the video: the naive method fails, the right one is exact **[V]**

Tested against ground truth — a 640x360 video (1280x720 device px at 2x) played
in Brave, full screen recorded, position confirmed by eye from an extracted frame.

**What does NOT work — consecutive-frame differencing.**
`tblend=all_mode=difference,cropdetect` returned `w:350 h:-2232` — a negative
height, garbage. Reason: flat regions that do not change between adjacent frames
contribute nothing, so only the moving *parts* of the picture light up, not the
picture's extent. A talking head over a static background fails identically.
`cropdetect` alone is worse still — it finds **black borders**, and a video
embedded in a browser page has none, so it dutifully returns the whole screen.

**What works — accumulated temporal RANGE over the whole clip.** Sample ~40
frames, grayscale, quarter scale; per pixel take `max - min` across all frames;
threshold; keep rows/columns where >2% of pixels changed; bounding box.

```
DETECTED  x=1100 y=852 w=1280 h=720   aspect=1.778
EXPECTED  x~1102 y~845 w~1280 h~720   aspect=1.778
```

Width and height **exact**, origin within 7 px, in well under a second. Over a
few seconds nearly every pixel of a real video changes at least once, which is
why the range works where the frame-to-frame delta does not.

**Honest limits — all of these need a human confirm, not blind trust:**
- **Two moving things = one big box.** An autoplaying sidebar video, an animated
  ad, or a progress bar outside the player will stretch the bounding box to span
  both. Mitigation is largest-connected-region rather than raw bbox.
- **Scrolling during capture destroys it** — the whole page becomes "motion".
- **A near-static clip** (still image plus audio) has no motion to find.
- Snap the result to even dimensions (h264) and offer the nearest standard
  aspect (9:16, 1:1, 16:9), since reels are almost always one of those.

**Therefore the crop is PROPOSED, never silently applied.** It renders a frame
for Ryan's eyes and he confirms — `copilot, not autopilot`, and his eyes are the
verdict on anything visual. Auto-crop is mechanical and safe to compute;
**punch-ins and Ken Burns moves are creative and belong in Resolve with his
hands on them.** Do not automate the second one.

**Storage.** Full-screen Retina capture ran ~1 MB/s (7.78 MB for 8 s), about
3.5 GB/hour. Fine per clip, but the full-screen master should be discarded once
a crop is confirmed, or the library outgrows the disk within weeks.

### Searchable library — what is actually missing

Already there **[V]**: `studio/registry.py` records every clip with a SHA-256,
and `clip.py` writes a sidecar carrying rect, source URL, note, duration and
measured loudness. What is missing is not storage, it is **recall**:

- **Transcription on ingest is the whole feature.** Meme clips are mostly
  speech, so "find the one where he says…" is the only search anyone actually
  performs. The repo already has a Deepgram leg in `tools/ingest-recording.py`,
  and Audio Hijack ships a non-beta local **Transcribe** block — either gives
  full-text search over the library for free.
- Tags, and the `source_clip_hash` join that already exists on both sides.

### Samples are not all stabs — some are BEDS

From Ryan's Tyson concept: a fight ambience (bell, punches, announcer, crowd)
running *under* the track, faded up and down to shape atmosphere. That is not a
one-shot chop, and it changes pipeline G: a trigger map entry needs a
**duration and a level envelope**, not just an onset. A bed's matching video is
a long clip under the section, not a stab on a beat. Both kinds must round-trip.

---

## 3a. The Stream Deck is the surface (Ryan, 2026-08-02)

Ground-truthed against the instrument, not the logs, per the 2026-08-01
post-mortem in `~/projects/obs-control-room/README.md`.

**What the deck actually is today** **[V]**: the live surface is Ryan's own
plugin `com.blessdog.obs-control-room` (installed, 17 actions). Layout is data
in `scripts/deck-layout.mjs`, written onto the hardware by
`scripts/build-profile.mjs`, and policed by `scripts/check-deck.mjs`, which
fails if a key points at a missing action **or** a shipped action sits on no
key. Companion is dead and its plugin is retired.

**The XL is nearly full where it counts** **[V]**:

```
 c0        c1      c2      c3     c4      c5       c6      c7
 STATUS    ·       ·       ·     SOON    BRB     ENDING  RECORD    row 0 — far, pressed rarely
   ·       ·       ·       ·      ·       ·        ·       ·       row 1 — deliberate gutter
 LEFT    RIGHT   SCRN+ME   ·     CAM   CUTOUT   ME+FLOAT LAVA      row 2 — what's on screen
 MARK    MUTE    ZOOM      ·   CAMERA  MEETING    ??    (nav)      row 3 — NEAREST the hand
```

Row 1 and column 3 are gutters — tactile landmarks the hand finds without
looking — and must stay dark. Column 7 row 3 is left free so the app's
undeletable page-nav key lands somewhere harmless. **That leaves `3,6` as the
only free key in the row you actually press mid-flow.** Clipping is a
press-constantly action, so it belongs on row 3 by the layout's own
reach-not-category rule. One slot, so: **one key.**

### The key

**`CLIP` at `3,6`** — and every behaviour it needs is a pattern this plugin has
already shipped and proven:

| Behaviour | Precedent already in the plugin **[R]** |
|---|---|
| Press = start/stop, elapsed time on the face | `record.ts` (Record key, amber ⏺ + elapsed) |
| Long press = secondary mode | `zoom.ts` (long press toggles follow) |
| Face shows real state, re-read on use | `mute-mic.ts` follows OBS's own event, "never lies" |
| Cycle between named targets | `camera-picker.ts` (face shows which is live) |

- **Press** — record the saved rect plus audio. Press again to stop.
- **Long press** — redraw the box (`screencapture -J video`), save it as the
  current rect. Two seconds, and only when the source window moves.
- **Face** — red/record family per `key-face.ts`; elapsed seconds are the only
  text, because the grammar is *text only when it's a number that changes*.

No rect-picker key at first. If switching between an Instagram window and an X
window starts to chafe, add one later using the Camera Picker pattern — but a
second key is not justified before the friction is real.

### What one press actually does

This is the whole "simple and easy" claim, and it is the reason the deck is the
right surface rather than a nicety: a single press has to leave behind a
finished, filed, pad-ready sample with provenance intact, or Ryan is back in a
file manager and the deck bought nothing.

```
press  → screencapture -v -R <rect> -G <uid>          (macOS built-in)  [V]
press  → stop
       → normalise VFR → CFR                           tools/ingest-screensage.py  [R]
       → register the .mov as a video asset            studio/registry.py          [R]
       → extract audio → 48 kHz/16-bit WAV             phase8_sp404/convert.py     [R]
       → file with source_clip_hash + source_in_secs   NEEDS THE §7 FIELDS
       → push to the SD card IMPORT folder             phase8_sp404/build.py       [R]
```

Every step except the ledger fields already exists. The deck action is a thin
TypeScript wrapper that shells out to one media-studio verb — the plugin owns
the key and the face, media-studio owns the pipeline.

### Two things to verify by exercising before trusting any of it

1. **[U] Screen Recording permission attaches to the calling process.** When
   the Stream Deck app spawns `screencapture`, macOS may attribute the capture
   to the Stream Deck app rather than to Terminal — which is where it is
   currently granted. This is exactly the shape of the five silent failures of
   2026-08-01: it will either work or produce a black frame, and a black frame
   probes as a perfectly valid H.264 stream. **Measure the pixels, don't probe
   the container.**
2. **[U] Two screen recorders at once.** If OBS is recording a session and
   `CLIP` fires, two capture mechanisms run simultaneously. Probably fine —
   different APIs — but unverified, and the failure mode is losing the OBS take,
   which is unacceptable. Test before this ever runs during a real recording.

### Where the action lives — and the one honest wrinkle

It goes in `obs-control-room/plugin/src/`, because that repo's README declares
it **THE Stream Deck surface** and the no-rival-surfaces doctrine says there is
exactly one. The wrinkle: this action never touches OBS, so the repo's name
becomes slightly a lie. The alternative — a second plugin — is worse: it
splits the layout SSOT, and `check-deck.mjs` would no longer see the whole
deck. **Recommendation: keep one surface, treat the repo as "control room"
with OBS as one of its subjects.** [RYAN] to overrule if the name matters.

---

## 4. Pipeline G — the trigger map

Three producers, each valid on its own, all emitting the same JSON. Ranked by
how much they can be trusted:

**G1 — SMF export from the SP  ·  exact, device-native, no DSP** **[D]**
Export the pattern as `.mid`. Every note-on is a pad hit with a timestamp. Pad
number → note number is a fixed documented table; pad → sample comes from the
ledger. This is the primary path and it costs a MIDI file parse.

**G2 — Ableton `.als` parse  ·  exact, verifiable today, no hardware** **[V]**
Anything arranged, chopped, or re-triggered inside Live is recorded in the
project file with `<CurrentStart>` / `<CurrentEnd>` / `<SampleRef>`. Since the
locked workflow is SP loops → Live Session View → arrangement, the finished
`.als` describes the final track more completely than the SP pattern does.
**This is the only producer that can be built and tested right now**, with no
SP on the desk.

> ### ✅ BUILT 2026-08-03 — `studio/ableton.py`, `tools/als-trigger-map.py`
>
> ```
> .venv/bin/python tools/als-trigger-map.py <project.als> [-o map.json]
>     [--summary] [--include-session] [--no-hash]
> ```
> Emits one entry per **firing**, not per clip. `tests/test_ableton.py`, **38
> passing** — synthetic fixtures for each trap (a real `.als` is megabytes of
> licensed factory content), plus real-file gates that skip on a cold checkout.
>
> **Correction to the 2026-08-03 handoff.** It said the parse was "buildable now
> against your thunderdome project." The *parser* was; the *trigger map* was not.
> `thunderdome.als` is a **mastering set** — one audio clip (the 32:06
> Thunderdome VHS master) on a track named `Master Test` with EQ Eight +
> Multiband Dynamics, and **zero played MIDI**. Nothing in it says "sample X
> fires at 00:42.15." The claim was inferred from a filename and a commit
> message without opening the file.
>
> Real fixture found instead: **`Factory Packs/Chop and Swing/Demo Song/Clean
> Swing.als`** — 18 tracks, 120 arrangement clips, 82 BPM, **1375 firings over
> 2m57s**. That is the shape a real trigger map has.
>
> **Five traps, each of which produces a plausible-looking map that is silently
> wrong. All five were found by reading Ryan's own files, not the docs:**
>
> 1. **GroovePool clips are not music.** `thunderdome.als`'s only `<MidiClip>`
>    lives at `LiveSet/GroovePool/Grooves/Groove/Clip` — a swing-timing
>    template. A naive `root.iter("MidiClip")` emits **16 phantom triggers on
>    note 36** from a project containing no played MIDI. Only clips reachable
>    from `Tracks/` count.
> 2. **Looped clips fire their content more than once.** A 64-beat clip with a
>    32-beat loop plays its notes twice; the note list holds one copy.
>    Un-expanded, every repeat is lost.
> 3. **Values live in `Value=` attributes, not element text.** `findtext()`
>    returns `""` for every field — so either it raises, or a defaulted `0.0`
>    silently stacks every clip at the top of the timeline.
> 4. **Tempo automation breaks beats→seconds.** The conversion is linear
>    (`60/bpm`); a ramp makes it wrong everywhere downstream. The parser
>    **refuses** rather than emit a drifting map.
> 5. **The declared absolute `Path` is frequently fiction.** Factory content
>    carries Ableton's own build machine (`/Volumes/data/tmp/trunk/...`), and any
>    set that has moved between machines carries a stale one. Resolution falls
>    back to `RelativePath` against the project folder, then the Live Pack —
>    and **verifies `OriginalFileSize`**, because a same-named file of the wrong
>    size would join to the wrong sample and place the wrong video.
>
> **Trap 2 has an evil twin, and the first implementation walked into it.**
> Expanding loops with a bare modulo folds *every* note into the loop window —
> but the loop brace selects only the portion that repeats, and notes outside
> `[LoopStart, LoopEnd)` are silent. On Clean Swing that invented **189 phantom
> firings** (1564 → 1375 after the fix); on the one genuinely repeating clip,
> 63 of its 114 notes sit outside the brace. Under-reporting loses picture;
> this over-reporting places picture where there is no sound. Both directions
> are gated by tests now.
>
> **What is deliberately NOT resolved here.** MIDI firings carry a `note`, not a
> pad or a sample hash. Resolving a note to a pad needs the bank, and the
> per-bank channel layout is still **[U]** (§2) — so that join is left to the
> consumer holding the ledger rather than guessed. Audio firings carry
> `sample_hash`, the join key to `phase8_sp404`.
>
> **Found in passing:** thunderdome's source WAV
> (`~/Downloads/hardcore.-techno.-vhsri-p/.../..._mastered.wav`) **no longer
> exists on disk** — the set references a file that is gone. Reported as
> unresolved rather than silently hashed to nothing.

**G3 — MULTIPAD stems + onset detection  ·  fallback, still reliable** **[D]**
One `.wav` per pad, each silent except where that pad fires. Onset detection on
a per-pad stem is a near-trivial problem — unlike correlating a sample against
a full mix, which is the fragile approach this design avoids. Use when the
performance was played live and never captured as MIDI.

> Deliberately **not** doing audio fingerprinting against the final master.
> Effects, pitch shifting, time stretch and layering all defeat it. Every
> producer above reads a *declaration* of what was played, not a guess.

---

## 5. Pipeline H — into Resolve

```
finished track + stems + trigger-map.json
  → tools/beat-grid.py --bpm <exact>        NEEDS --bpm FLAG (MUSIC-LANE §D)
  → song-shaped workspace                   MISSING (MUSIC-LANE §D)
  → resolve sample_hash → source clip + in-point   NEEDS LEDGER FIELDS (§7)
  → emit video clips at trigger times       NEW, small
  → tools/compile-ir.py → OTIO → Resolve    EXISTS
  → Ryan's GUI pass                         EXISTS
```

Because the ledger knows the sample's in-point inside the source clip, the
emitter places **the matching frames of the meme**, trimmed to the chop, at the
beat where the chop fires. The picture stutters exactly like the audio does,
for free, because both are reading the same two numbers. No manual syncing.

Everything downstream of the emitter already exists and already works. This
does not become a new lane in the compiler — it becomes a new *front door* to
the existing one, exactly as `docs/PLAN.md:50` already anticipates the music
video as the canonical worked example **[R]**.

---

## 6. The argument against building any of this

Required by working agreement. Taken seriously:

1. **macOS already does half 1.** Cmd-Shift-5 draws a box and records with a
   chosen audio input, today, with no code. If Ryan clips a handful of videos a
   month, the honest answer is *use the built-in and skip pipeline F entirely*.
   The build earns its keep only through repeat-rect speed, automatic filing,
   and the provenance link that half 2 depends on. **If half 2 is not
   happening, do not build half 1.**
2. **Half 2 is worth more than half 1 and is cheaper.** G2 needs no hardware,
   no routing, no new device, no permissions — a gzip read and an XML parse
   against files already on disk. It is also the piece no off-the-shelf tool
   does. If only one thing gets built, build G2.
3. **Scope risk.** `three-software-scope.md` (2026-07-20) reeled this project
   in to OBS + Resolve + Blender. A screen-capture tool is a fourth surface. It
   is defensible only as a thin wrapper over a **built-in OS command** — the
   moment it wants a UI framework, a preview window, or a menu-bar app, it has
   become a product and should be dropped.
4. **Publishing risk, stated once.** This pipeline samples Instagram, TikTok,
   X and YouTube material into published tracks and videos. `MUSIC-LANE.md` §2E
   already documents that DJ software hard-blocks recording from streaming
   services over exactly this issue. Meme audio is frequently itself
   copyrighted, and provenance in the ledger cuts both ways — it is also a
   record of what was taken from where. Ryan's call, not the agent's; the
   ledger at least makes takedown response possible instead of guesswork.
5. **Do not build:** an SP control surface or MCP (its remote surface is MIDI;
   wrapping it breaks no-bespoke-surfaces), a god Loopback device, a
   fingerprinting matcher, or a second asset ledger.

---

## 7. The smallest change that unlocks everything

> ### ✅ BUILT 2026-08-02 — `blessdog@839a6c3`
>
> All three fields are in `phase8_sp404/ledger.py:LedgerEntry`, defaulted so old
> ledgers load unchanged. Pads are validated and canonicalised on construction
> (`a5` → `A5`); negative in-points are rejected; `build.stage_file` validates
> the pad *before* running ffmpeg so it fails soft and wastes no conversion.
>
> Query side for §5: `Ledger.from_clip(hash)` returns everything cut from one
> clip in in-point order, `Ledger.by_pad("A5")` returns what sits on a pad
> (later entries win — re-recording a pad replaces it). `pad_to_note` /
> `note_to_pad` implement the documented Bank A pad 1 = note 48 mapping.
>
> **The per-bank MIDI channel layout was deliberately NOT implemented** — the
> two Roland sources disagree, so `note_to_pad` requires the caller to supply
> the bank rather than inventing one. Still `[U]`; resolve it with a MIDI
> monitor on real hardware. Tests: 51 passing.

`phase8_sp404/ledger.py:LedgerEntry` **could not express this lane** **[R]**.
It had `source_url`, `source_path`, `derived_from`, `bank`, `bpm`, `key` — but
no way to say *which video this came from*, *where inside it*, or *which pad
it sits on*. Three fields:

| Field | Why it is load-bearing |
|---|---|
| `source_clip_hash` | joins the sample to the captured `.mov` in media-studio's `registry.db`. **The content hash is the join key — neither repo has to import the other.** |
| `source_in_secs` | the in-point inside that clip. Without it the video cannot be chopped in sync with the audio; this is the field that makes §5 work. |
| `pad` | e.g. `"A5"`. Without it a MIDI note number resolves to nothing and G1/G3 are dead. |

`bank` already exists but is documented as "organisational label, **not a
device bank index**" **[R]** — so it cannot double as the pad's bank. `pad`
is genuinely new.

This preserves `MUSIC-LANE.md` decision 1 (blessdog owns music, media-studio
owns video, the boundary is the file) by adding a hash reference rather than a
dependency.

---

## 8. Decisions blocking a build

1. **[RYAN] Is half 2 in scope at all?** Everything above is sized on the
   assumption that "which meme plays when" is the real goal. If the actual want
   is just faster clipping, the answer is Cmd-Shift-5 and this document ends.
2. **[RYAN] May a new single-purpose Loopback device be created?** Required for
   captured audio to be non-silent **[V]**. Nothing existing would be touched —
   but the stated history is that Rogue Amoeba setups broke before, so this is
   his call, not an implementation detail.
3. **[RYAN] Which repo owns the clipper?** It produces a file that is
   simultaneously a video asset (media-studio) and a sample source (blessdog).
   Recommendation: the clipper lives in **media-studio** because it captures
   video and video is this repo's job; the audio it yields crosses to blessdog
   through `phase8_sp404 add`, and the hash joins them.
4. **[RYAN] Build order.** Recommendation: **G2 first** (Ableton parse — no
   hardware, no routing, testable today), then the three ledger fields, then
   the rect store, then G1 when the SP is on the desk and its MIDI behaviour
   can be exercised rather than assumed.

---

## 9. Day-one verification list (when the SP arrives)

Per `verify-by-exercising`: nothing below is trusted until it is exercised.

- [ ] Update firmware **first** (SMF export needs v4+; Serato needs v5+) **[D]**
- [ ] Point a MIDI monitor at USB and press pad A1 — confirm note 48, confirm
      the channel-per-bank layout, resolve the **[U]** in §2
- [ ] Export one pattern in all three modes; confirm SMF timing against the
      BOUNCE render
- [ ] Confirm whether a multi-bank performance really needs one export per bank
- [ ] Confirm a captured clip's audio is **non-silent** after routing — measure
      `mean_volume`, never trust the container
