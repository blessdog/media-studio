# MUSIC-LANE — SP-404MK2 → track → video

*Written 2026-08-02, planning round. Nothing here is built. Verification
status is marked on every claim: **[V]** verified this session against the
machine or vendor docs, **[R]** read from a repo file, **[U]** unverified /
assumption, **[RYAN]** blocked on a decision.*

Scope of this document: how the incoming Roland SP-404MK2 connects to tooling
Ryan already owns, and what media-studio would have to grow to turn his own
music into videos. It does NOT propose a build — it maps the ground and lists
the decisions that gate one.

---

## 1. Ground truth — what already exists

### Hardware
- **Roland SP-404MK2** — ordered 2026-08-02, **not yet on the desk**. Every
  claim about it below is from vendor documentation, not from exercising the
  device. **[U]** until it arrives and is exercised.
- M1 Max MacBook Pro (primary), MacBook Air (**genuinely idle**), Mac Mini
  (**NOT idle** — `INDEX.md:17` says it is prod / source of truth for
  jobhard-v2 at `/Users/homer/projects/jobhard-v2`) **[R]**.
- Focusrite Scarlett interface, unused. Push 2 **[V]** (Ableton MIDI Remote
  Scripts `Push`, `Push2`, `pushbase` present). fifine USB mic **[V]**.

### Software (all verified present on this machine **[V]**)
| Tool | Version | Relevance |
|---|---|---|
| Ableton Live 12 Suite | — | arrangement / finishing destination |
| Native Instruments Komplete | Maschine 2, Kontakt 8, Battery 4, Massive X, Reaktor 6, Guitar Rig 6 | instrument library |
| Rogue Amoeba suite (all) | AH 4.5.9, Loopback 2.4.8, SoundSource 5.9.0, Farrago 2.1.5, Fission 2.9.4 | audio capture/routing/trim |
| DaVinci Resolve Studio | 21.0.2.4 | video finishing |
| Blender | 5 | deterministic camera work |

### Existing pipelines in sibling repos
- **`~/projects/blessdog/`** — seven-phase AI music production system
  (`phase1_osc` … `phase7_sound`). `phase5_analyzer/download.py`,
  `separator.py`, `analyzer.py` are the URL→audio→stems chain **[V]**.
  `INDEX.md:15`: "AI music production / Ableton MCP system" **[R]**.
- **`~/projects/rave/`** — Internet Archive restoration rig: `extract_audio.sh`,
  `enhance_video.sh`, `master.sh`, `mux_audio.sh`, with `tools/ffmpeg-full`,
  `tools/realesrgan`, `tools/rnnoise-models` vendored **[V]**.
- **`~/projects/ableton-mcp-extended/`** — second Ableton MCP with skills **[V]**.
- **`~/projects/bongpot/tools/ear/stems.py`** **[V]**.

### Existing pipeline in media-studio
- `tools/beat-grid.py` → librosa beat analysis → `<ws>/beats.json` + Purple
  markers **[R]**. `studio/beatgrid.py:28` uses `librosa.beat.beat_track`.
- `tools/edit-ir.py <ws> add-music` → audio lane A2+; **voice on A1 is
  sacred** **[R]**.
- `studio/registry.py` → SQLite asset ledger with hashes **[R]**.
- `docs/PLAN.md:50` — "Worked example — a music video through the system"
  already describes song-as-spine → beat grid → Phase 7 visuals → compiler →
  Ryan's GUI pass **[R]**. **The music video is the plan's canonical example,
  not a new lane.**

### SP-404MK2 facts (vendor docs, **[V]** as documentation; **[U]** as behaviour)
- Imports 16-bit linear WAV/AIFF/MP3; **everything converted to 48 kHz/16-bit
  on import**; files read from an **`IMPORT` folder on the SD card**.
- Max sample length **16 minutes (~176 MB)** — full tracks fit easily.
- Records/resamples at 48 kHz/16-bit, fixed — no setting.
- **4 audio channels in over USB**, USB Audio Class 2.0, class-compliant, no
  driver. FX-on means the effected signal reaches the computer.
- Skip Back Sampling: 25 s default, **40 s** via UTILITY → SYSTEM → MARK
  Function → SBS Long. `ROUTING = ExtIn` samples only external input.
- **Multipad Export** (firmware 4.x) — pads of a pattern as individual stems.
- MIDI clock sync both directions, with adjustable output delay.
- DJ Mode: two decks, 8 pads/side, per-channel volume, tempo nudge, cue to
  headphones, BPM sync either direction; later firmware added quick loop/roll
  and a crossfader. **Not** a single hardware crossfader (three knobs = levels
  + cue); no jog wheels. Reviewers consistently criticise the crossfading.
  Firmware 5.0 adds Serato DJ controller integration (Serato **not installed**).

---

> **Extended 2026-08-02 by `docs/CLIP-LANE.md`** — pipeline F (screen-region
> clip capture, for meme/reel sources that cannot be downloaded) and pipeline G
> (trigger map: knowing where in the finished track each sample fires, so the
> source video can be placed in sync). Read this document first, that one second.

## 2. The five pipelines

Deliberately separated because they have different owners, different risk, and
different readiness. A–C are music. D is media-studio's actual job. E is optional.

### A — Library Builder  ✅ **BUILT 2026-08-02**
```
URL / Internet Archive / local file
  → download            (blessdog/phase5_analyzer/download.py)      EXISTED
  → stem separation     (blessdog/phase5_analyzer/separator.py)     EXISTED
  → restoration         (rave/master.sh, rnnoise, ffmpeg-full)      EXISTED
  → normalise 48k/16-bit WAV   (blessdog/phase8_sp404/convert.py)   BUILT
  → stage local library + ledger (build.py, ledger.py)              BUILT
  → file to <card>/IMPORT      (blessdog/phase8_sp404/card.py)      BUILT
```
Lives at **`~/projects/blessdog/phase8_sp404/`** per decision 1. Tests:
`~/projects/blessdog/tests/test_sp404.py`, **26 passing**.

```
python -m phase8_sp404 cards                     # detect inserted card
python -m phase8_sp404 add <file|url> --kind loop --bank rave
python -m phase8_sp404 stems <file> --bank rave  # Demucs → 4 staged stems
python -m phase8_sp404 list [--kind] [--bank]
python -m phase8_sp404 push [--kind] [--bank] [--card /Volumes/X]
```

Design notes worth keeping:
- **Two-step staging.** Everything lands in `blessdog/music/sp404/<kind>/`
  first, and only then gets copied to a card. The card is small and swappable;
  the local library is durable, so a card can always be rebuilt from the ledger
  without re-downloading.
- **Card path is detected, never assumed.** Roland documents the SD layout only
  as a diagram image, so the exact import path stayed [U]. `card.py` searches a
  real card for the folder instead, accepting both `<card>/IMPORT` and
  `<card>/ROLAND/SP-404MKII/IMPORT`, and refuses loudly with format-the-card
  instructions rather than writing somewhere the device will never read.
- **Dedupe on source content hash**, so converting the same source twice is
  recognised instead of producing a second near-identical sample.
- **`kind` ∈ oneshot/loop/track/stem** plus a free-text `bank` label — this is
  what keeps DJ material distinguishable from pad material (decision 3).
- **Conversion is up front, not left to the device.** The SP converts to
  48 kHz/16-bit on import anyway; doing it here means what sits on the card is
  exactly what the SP will play.

**Two bugs found by exercising, neither visible from reading the code:**
1. `__init__.py` exported a function named `convert`, shadowing the `convert`
   *module* — `phase8_sp404.convert.probe` resolved against the function.
   Renamed to `to_sp_format`; a comment in `__init__.py` records the trap.
2. Card detection matched **any** directory named `import`, so scanning
   `/Volumes` "found a card" at `/usr/share/vim/vim91/import` on the boot disk
   and would have pushed samples into it. Now requires the folder to sit at the
   card root or under a `ROLAND/` ancestor, and skips the boot volume outright.
   Regression test: `test_card_rejects_unrelated_import_folder`.

**Still unexercised against real hardware** — no SP-404MK2 on the desk yet. The
card layout, the on-device display-name limit (`MAX_NAME_LEN = 32`, deliberately
conservative), and whether the device reads subfolders inside IMPORT all remain
[U] until the unit arrives.

### B — Capture  *(live sound → sample)*
```
computer audio → SP-404 (USB) → Skip Back Sampling → SD card
  → Fission trim → library
```
Deliberately minimal. **No new Loopback device.** When the SP arrives, add it
as a monitor on the existing `Loopback Audio` device, or don't route at all and
use the SD card only. See §4 on why.

### C — Performance → Track  *(SP → Ableton → finished song)*
```
SP-404 loops, clock-slaved to Ableton (Ableton = MIDI clock master)
  → 4ch USB audio → Ableton SESSION VIEW clip slots
  → Push 2 arrangement
  → stems + master export
```
No code. This is a technique and configuration change, not a build. The single
biggest friction fix is Session View instead of Arrangement View.

### D — Track → Video  *(media-studio's actual job)*
```
finished track + stems
  → tools/beat-grid.py (--bpm override)                    NEEDS --bpm FLAG
  → song-shaped workspace (no transcript, no silence spans) MISSING
  → stems on separate audio lanes A2..An                    NEEDS SCHEMA BUMP
  → Scene Forge visuals (Phase 7)                           EXISTS
  → compile → Resolve → Ryan's GUI pass                     EXISTS
  → tools/deliver.py fan-out                                EXISTS
```
Three gaps, all small and all already anticipated: `docs/PLAN.md:77` parks the
audio-track schema bump; the `--bpm` flag bypasses librosa when the SP/Ableton
tempo is known exactly; and `tools/ingest-recording.py` assumes speech
(silence detection + Deepgram diarization), neither of which means anything for
a song — a song needs a different front door, not a new system.

### E — DJ set  *(IN SCOPE per Ryan 2026-08-02; sampling stays primary)*
Library → SP DJ Mode banks, and/or SP as a Serato controller. Honest verdict:
DJ Mode alone is fine for a **sampler-DJ hybrid** set (tracks plus live loops,
one-shots and MFX), poor for a **traditional** beatmatched set. Serato is the
answer for traditional DJing. **Do not let this gate pipeline A.**

#### Serato — verified 2026-08-02
- **Serato DJ Lite IS installed** — `/Applications/Serato DJ Lite.app`,
  `~/Music/_Serato_`, `~/Music/_Serato_Backup` **[V]**. (An earlier claim in
  this session that Serato was absent was wrong.)
- **Spotify IS supported** by Serato DJ Lite and Pro in 2026, alongside Apple
  Music, TIDAL, SoundCloud, Beatport, Beatsource **[V]**.
- The SP-404MK2 is a **Serato DJ Lite hardware-unlocked device** — connecting
  it unlocks Lite free. **Serato DJ Pro is a paid upgrade** **[V]**.
- Requires **Serato DJ Lite/Pro 3.3.1+** AND **SP firmware 5.00+** **[V]**.
- Connected, the SP is both a controller AND Serato's USB audio interface, so
  **Serato's audio runs through the SP's effects** **[V]**.
- ⛔ **Recording is BLOCKED whenever a streaming service is in use** — a
  licensing term between labels, streaming providers and DJ-software makers.
  Industry-wide, not Serato-specific **[V]**. **You cannot clip or sample
  Spotify material out of Serato.** Beyond the technical block, sampling
  streaming catalogue into published tracks and videos is a takedown /
  demonetisation problem. **This is why pipeline A matters more than the
  Serato route: sample from material you own or can clear.**

#### Effects architecture **[V]**
- **Four effect buses.** BUS 1 + BUS 2 = per-sample effects. BUS 3 + BUS 4 =
  master effects on the overall mix.
- Up to **4 effects per sample**; up to **5 effects on external input
  (EXT SOURCE)**. 37 effects total. Bus routing switchable serial ↔ parallel.
- **In DJ mode, playback runs through the effects.** So Serato output can run
  through up to five effects on the external-input bus while your own samples
  trigger with their own per-sample effects. That is the hybrid set.

#### Unresolved — verify by exercising
- **[U] Can you sample while IN DJ mode?** DJ mode remaps the pads to
  screen-printed DJ functions, so simultaneous pad-sampling may not be
  available. EXT SOURCE and resampling exist regardless. Not answerable from
  documentation — test on arrival.
- **[U] Shipping firmware version.** Unknown; v5.00+ is required for Serato.
  Firmware updates via SD card. **Day-one task: update firmware before
  anything else.**

---

## 3. What we need to consider

1. **Repo boundary.** Which repo owns A and B? `blessdog/` already owns music
   production. media-studio owns video. Putting a sampler library builder in
   media-studio risks breaching the three-software scope reel-in (2026-07-20).
   → **[RYAN] decision 1 below.**
2. **Don't break what works.** Ryan's stated history: elaborate Rogue Amoeba
   setups broke, current setup works. Every pipeline here must be **additive**.
   No edits to existing Loopback devices as part of a build.
3. **The SD card is the interface, not USB.** The boring path has zero routing
   complexity and cannot break anything currently working. USB audio is an
   optimisation to add *after* the SD path proves too slow.
4. **Verification is blocked on hardware.** The SP is not here. Per
   `verify-by-exercising` doctrine, nothing about the device can be marked
   verified until it is exercised. Build only what is verifiable now.
5. **Curation over volume.** 16 pads + 1 sub pad per bank. A library builder
   that dumps thousands of files onto an SD card produces an unusable
   instrument. Selection and naming matter more than throughput.
6. **Provenance and dedupe.** `studio/registry.py` already stores assets with
   hashes. Whatever builds the library should register what it made and where
   it came from, or the library becomes unattributable within a month.
7. **Source licensing.** Internet Archive material has clearer licensing and
   often better source quality than YouTube rips. Prefer it where possible.
8. **Portability.** Anything load-bearing goes in the repo, not harness memory.
   A new lane means AGENTS.md grows a section and the cold-start test covers it.
9. **What NOT to build.** No bespoke SP control surface. No MCP for the SP —
   its only remote surface is MIDI and wrapping it breaks the no-bespoke-surfaces
   doctrine. No god Loopback device. The SP is an instrument; Ryan plays it.

---

## 4. Why no new Loopback device

`Loopback Audio` currently references sixteen entries, of which nine are
hardware or virtual devices that come and go: AirPods Pro (Bluetooth),
External Headphones, Headphone, Realtek USB Audio, fifine Microphone,
BlackHole 2ch (a virtual driver nested inside a virtual device), Microsoft
Teams Audio, Computer Audio Input, MacBook Pro Speakers **[V, read from
`~/Library/Application Support/Loopback/Devices.plist`]**.

That is a god object: sixteen dependencies coupled through one channel map,
every one a failure surface. `Ableton OBS mix` (3 entries) and
`Ableton Virtual Out` (2) are small, single-purpose, and almost certainly have
never broken. **This is the likely explanation for "I set it up and shit would
break."** Adding the SP to that device would make it worse.

*(Honest limit: the plist read distinguishes device composition but not cleanly
sources vs monitors. The diagnosis holds either way.)*

Neither **Loopback** nor **SoundSource** exposes any automation surface — no
`.sdef`, no `NSAppleScriptEnabled`, no CLI **[V]**. They are GUI-only. **Audio
Hijack**, **Farrago** and **Airfoil** are all scriptable **[V]**.

---

## 5. Decisions

**Answered by Ryan 2026-08-02:**

1. ✅ **Repo boundary — `blessdog/` owns music.** The boundary is the WAV file.
   `blessdog/` grows the SP library builder; media-studio stays video-only and
   receives finished tracks + stems as registered assets. Preserves the
   2026-07-20 three-software reel-in.
2. ✅ **Library builder (pipeline A) first.** Needs no hardware to develop and
   pays off for sampling, video beds, and DJ sets independently.
3. ✅ **DJ lane IS in scope — but sampling is primary and must be strong.**
   "That is gonna be the main way I'm using it." DJ capability is additive and
   must never compromise the sampling path.

**What decision 3 actually changes in pipeline A** (less than expected):
- Library builder must handle **full-length tracks**, not only short one-shots
  (16 min / 176 MB per pad is ample).
- Needs **BPM + key metadata** — `blessdog/phase5_analyzer/analyzer.py`
  already exists for this.
- Needs **bank organisation** as a first-class concept (DJ sets vs sample kits).
- Source material must be **files Ryan owns or can clear**, never streaming —
  see the Serato recording block in §2E.
- It does **not** change the repo boundary or the build order.

**Still open:**

4. **Where the sample library is registered** — media-studio's `registry.db`,
   a separate ledger in `blessdog/`, or none. Leaning: `blessdog/`, following
   decision 1, with only finished tracks/stems crossing into media-studio.
5. **Whether Serato DJ Pro is worth the paid upgrade** over the free Lite
   unlock. Deferred until Ryan has actually used Lite with the device.
