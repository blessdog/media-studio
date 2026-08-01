# DECK-MARKET — what exists, what people use, what we learned from it

*Research report, 2026-08-01. Verified against primary sources: the Elgato
Marketplace API (`mp-gateway.elgato.com`, all 3,681 products pulled), Elgato's
shipped plugin artwork measured off this machine, the OBS forum resource
directory, and vendor documentation.*

**Why this report exists.** Ryan's correction, 2026-08-01: *"build not buy"
never meant "don't look."* It meant study what has been built, learn what people
love, then build something excellent. Earlier sessions inverted it — skipped the
ecosystem, went straight to code — and shipped a deck with five dead keys, grey
text where the platform uses icons, and the newest feature reachable from
nothing. The survey comes first. Always.

**Stated limitation up front:** the Elgato Marketplace exposes **no ratings and
no reviews** — every field on the product records was checked. There is no
five-star metric to sort by; `download_count` is the only popularity signal it
publishes. The **OBS forum directory does publish both**, so OBS-side figures
below carry real star ratings.

---

## 1. The Stream Deck side — OBS plugins by real downloads

| Downloads | Product | Maker | Price | macOS? |
|---:|---|---|---|---|
| **1,223,298** | OBS Studio | Elgato (official) | free | yes |
| **282,364** | OBS Tools | BarRaider | free | **NO — Windows only** |
| 61,581 | SE.Live | StreamElements | free | yes |
| 52,538 | Multi OBS Controller | the_ca11 | free | yes |
| 1,112 | OBS Studio *icon pack* | Aetheon | $5.00 | n/a |
| 828 | OBS Studio *profile pack* | Aetheon | $8.50 | MK/Mobile/Neo — **not XL** |

Whole-platform leaders for scale: Volume Controller 1,738,100 · **OBS Studio
1,223,298** · Discord 1,045,184. **OBS is the second most-installed plugin on
the entire platform.**

*("Obsideck", 12,561 downloads, is for **Obsidian** the notes app. Name
collision — excluded.)*

## 2. The best OBS deck plugin does not run on macOS

**BarRaider's OBS Tools — 282,364 downloads — is Windows-only.** Of every plugin
over 100k downloads that Mac users cannot install, **eight of the top ten are
BarRaider's**. What those users get and we cannot buy at any price:

- **Smart Scene Switcher** — preview vs live with a coloured border on the key
- **Instant Replay** — press saves the last N seconds; long-press arms the buffer
- **Dropped Frames Alarm** — the key changes colour as the stream degrades
- **CPU Usage** — OBS's load, live, on a key
- **Source Animation** — multi-phase moves, recordable, import/export
- **Previous Scene** — jumps back, showing the scene's name

On macOS the entire OBS toolkit is Elgato's official plugin (fixed actions,
state icons, no telemetry) plus a multi-instance controller. **The whole "live
telemetry on a key" category is absent on our OS.** That is the evidence-backed
reason to own a plugin at all.

**But scope it honestly.** Ryan **records screen-shares and commentary; he does
not stream** (stated 2026-08-01). Dropped-frames alarms, bitrate health, instant
replay and preview/live tally are live-broadcast machinery. Building them would
be building the wrong instrument well. **Parked until he actually streams.** The
one item that does serve him — source animation — is better solved OBS-side (§4).

## 3. How the paid layouts are built — and why not to copy them

**SideshowFX**, the dominant commercial profile maker, in their own words and
products:

- **They prefer folders over pages** — a folder is a key opening 31 more keys on
  an XL, nested without limit; pages are linear.
- **Structure = a menu page of category tiles → one folder per category.**
- **Icons are drawn from the host software's own interface design**, never
  invented. (Independently confirms the rule Ryan set on 2026-07-21: the
  official plugin's artwork is the spec.)
- **Scale:** their Blender Pro pack is 79 XL pages / 927 programmed keys.

**The trap in copying them.** That structure exists because Blender, Photoshop
and Resolve have a thousand-plus keyboard commands and no live state — those
profiles are keystroke emulators, and nothing ever comes back. **OBS has ~20
verbs and rich live state.** A folder tree built for the opposite problem throws
away our only advantage.

**The market states it plainly: OBS profile packs get 828 downloads while the
OBS plugin gets 1.2 million.** For OBS nobody buys a layout — they want live
keys and arrange them themselves. So: **flat page, no navigation during a take.**

## 4. The OBS side — plugins that serve THIS workflow

| Downloads | Rating | Plugin | What it gives us |
|---:|:---:|---|---|
| 2,490,000 | 4.65★ | **Move** (Exeldro) v3.2.1, Feb 2026, macOS | Sources with matching names animate between scenes automatically — "camera pushes aside while the screen share pans in" becomes a scene switch. |
| — | — | **obs-zoom-to-mouse** (Lua, BlankSourceCode), macOS | Hotkey punches a display capture in on the cursor and follows it. Author wrote it *"to zoom into an IDE when highlighting sections of code."* Hotkey ⇒ deck key. |
| — | — | **obs-shaderfilter** | Rounded corners + drop shadow, so a floating screen share reads as floating. |
| installed ✓ | — | **Background Removal** | Already on this machine; what Cam Cutout and Lava Lounge ride on. |

**Architectural point: the motion belongs in OBS, not the deck.** With Move
installed, a scene key press animates the composition and we write no tweening
code. The deck stays a scene switcher.

*Retina caveat for zoom-to-mouse: needs Set Manual Source Position, Scale X/Y = 2,
and explicit monitor width/height, or it misbehaves on a Retina Mac.*

## 5. Platform mechanics (things we had wrong)

- **10 pages per profile** — 320 keys on an XL. Capacity is a non-issue; the
  limit is human memory.
- **Page-navigation keys are placed automatically by the app and cannot be
  deleted or moved.** `DECK-AUDIT-2026-08-01.md` flagged the arrow key at (7,3)
  as sloppiness; that was wrong, and is corrected there.
- **Folders nest without limit**, each with an auto-exit timer up to 60 s.
- **Profiles are unlimited**; Smart Profiles auto-switch on app focus.
- **The app owns the profile files while it runs** and rewrites them on exit, so
  edits made underneath a running app are silently discarded. It must be *quit*,
  not killed — a SIGTERM'd app skips its session checkpoint and the next launch
  offers to restore a stale backup, which reverts the layout. (Both learned the
  hard way this session; `scripts/build-profile.mjs` encodes the remedy.)

## 6. The visual grammar — verified three ways

1. **Elgato's shipped OBS artwork, measured off this machine:** inactive tile
   `#263838`, active tile `#5E8B8B` teal, inactive icon `#979797`, active icon
   `#EFEFEF`; record adds `#FF2B00`, stream adds `#04C84F`. **Full bleed — no
   corner radius in the artwork**; the app and the physical key do the rounding.
2. **Aetheon's paid OBS profile pack:** same language — teal-filled active tiles,
   dark inactive, white line icons.
3. **Elgato's own icon packs** (Entypo, 256,862 downloads) — line-art on flat fields.

> **The rule: state is the whole key's background colour. Identity is a centred
> glyph. Text appears only when it is a number that changes.**

This is the perception hierarchy, not a preference: colour across a whole key is
caught in peripheral vision; a glyph needs a glance; text needs a full second of
focus. Shipped in `obs-control-room/plugin/src/key-face.ts` (commit `85bf12e`).

## 7. Free icon packs worth using as source art

| Downloads | Pack | Maker |
|---:|---|---|
| 256,862 | Entypo | Elgato |
| 255,143 | Animated GIF Pack | VIVRE-MOTION |
| 144,178 | Hexaza | Piotezaza |
| 112,805 | Pure | Nerd Or Die |
| 95,876 | Duotone Essentials | Caleb Leigh |

All free; none installed (`IconPacks/` is empty). Note these drop art onto keys
configured by hand — our plugin *draws* its faces, so a pack is useful as
reference and source SVG, not as a drop-in.

## Sources

- Elgato Marketplace API — `https://mp-gateway.elgato.com/products?limit=200&offset=N`
- Official OBS plugin listing — marketplace.elgato.com/product/obs-studio-35615969-830f-45c9-ba0a-1a295bba7fec
- BarRaider OBS Tools actions — docs.barraider.com/faqs/obs-tools/actions/
- BarRaider macOS status — docs.barraider.com/faqs/general/compatibility/
- SideshowFX method — sideshowfx.net/news/2022/1/22/stream-deck-customization-part-1
- Move plugin — obsproject.com/forum/resources/move.913/ · github.com/exeldro/obs-move-transition
- obs-zoom-to-mouse — github.com/BlankSourceCode/obs-zoom-to-mouse
- Pages/folders — help.elgato.com/hc/en-us/articles/4410312027277-Elgato-Stream-Deck-Pages
- Elgato shipped artwork — `~/Library/Application Support/com.elgato.StreamDeck/Plugins/com.elgato.obsstudio.sdPlugin/resources/actions/`
