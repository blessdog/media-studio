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
