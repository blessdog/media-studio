# DECK AUDIT — 2026-08-01 (why the XL looks like shit)

*Ground-truthed from disk and running processes today, not from logs or prior
session notes. Verification legend: **[V]** = read directly from the file or
process named; **[I]** = inference stated as such.*

Instrument: **Stream Deck XL**, 8×4 = 32 keys, device `20GAT9902`,
profile bundle `~/Library/Application Support/com.elgato.StreamDeck/ProfilesV3/81602404-2044-4504-A854-88C9173CA422.sdProfile`,
profile "Default Profile", **current page `4345e073`**. [V]

Contact sheets rendered from the live generator + the live profile:
`scratchpad/xl-now.png` (the deck as it is) and `scratchpad/compare.png`
(our faces vs Elgato's shipped artwork).

---

## Finding 1 — five keys are dead, and they render as yellow warning triangles [V]

Page `4345e073` assigns 16 plugin keys. The deployed plugin manifest
(`plugin/com.blessdog.obs-control-room.sdPlugin/manifest.json`, symlinked live
into the Stream Deck app) declares 14 actions. **Five assigned keys point at
action UUIDs that no longer exist:**

| Key (col,row) | Assigned UUID | Status |
|---|---|---|
| 1,0 | `…obs-control-room.show-flow` | **deleted from source** |
| 2,0 | `…obs-control-room.screen-picker` | **deleted** (superseded by Screen L/R, commit `6df9475`) |
| 5,0 | `…obs-control-room.pause-record` | **deleted from source** |
| 1,1 | `…obs-control-room.scene-screen` | **deleted** (superseded by Screen L/R) |
| 7,1 | `…obs-control-room.stream` | **deleted from source** |

That is 5 of 16 live keys showing the Stream Deck app's missing-action
placeholder. Top-left quadrant of the deck — the part your hand lands on first.

## Finding 2 — the newest feature is on no key at all [V]

The manifest declares `scene-screen-left` and `scene-screen-right`. **Neither
appears on any page of any profile.** The per-monitor screen share you built
(commit `6df9475`, "Screen L / Screen R") is unreachable from the deck.

## Finding 3 — 15 of 32 keys are dark [V]

Rows 2 and 3 hold nothing except a Next Page key at (7,3), and the page it
opens (`87920aed`) contains exactly one key: Previous Page. So the bottom half
of the XL is empty — and it is the half **nearest the hand**, while every live
key sits on the far rows. The layout was backwards.

> **CORRECTION (2026-08-01, after researching the platform):** this finding
> originally called the stray arrow key at (7,3) sloppiness. It is not. **The
> Stream Deck app places page-navigation keys automatically on a free key
> whenever a profile has more than one page, and they cannot be deleted or
> moved.** The app was working correctly; I was wrong. See
> `DECK-MARKET-2026-08-01.md` §5.

## Finding 4 — root cause: source was rebuilt, deck page was never updated [V]

`~/projects/obs-control-room` has uncommitted work in the tree:

```
 M plugin/src/key-face.ts, plugin.ts, actions/record.ts, manifest.json
 D plugin/src/actions/{show-flow,pause-record,stream}.ts   (+ their imgs/)
?? plugin/src/animator.ts
?? plugin/ARCHITECTURE.md
 M plugin/com.blessdog.obs-control-room.sdPlugin/bin/plugin.js   (rebuilt)
```

The actions were deleted, the bundle was rebuilt, the symlinked plugin picked
it up — and the profile page still referenced them. **This is the Companion
incident again in a new costume:** the code moved, the instrument didn't, and
nothing in the loop checks that every key on the deck resolves to an action
that exists. [V for the facts; [I] for the causal read, but the diff and the
page contents agree.]

## Finding 5 — plugin is alive, OBS is not [V]

A Node 24 process is running `bin/plugin.js` with `--inspect=127.0.0.1:56813`
— i.e. left in `streamdeck dev` mode. Newest log
`logs/com.blessdog.obs-control-room.0.log` ends at `2026-07-22T15:53:41Z` with
registration and **no** `Connected to OBS` line, because OBS is not running.
So every surviving key is drawing its dim `offline` face. The deck reads dead
even where it is correct.

## Finding 6 — the art gap, stated concretely [V, from `compare.png`]

Holding our faces against the official Elgato OBS plugin's shipped artwork at
the same 144×144:

- **Elgato lights the whole key.** State is a filled background tile that
  changes color (teal = active); the icon is white line-art on top. At arm's
  length the key reads as a lit lozenge.
- **Ours lights only the symbol.** Constant `#101527` navy background, glyph
  recolored (white ready / red live / dim offline). At arm's length it reads as
  a dark key with a small mark on it.
- **Our seven scene keys have no icon at all** — small grey Helvetica ("Starting
  Soon", "Screen + Cam", "Lava Lounge", "Cam Cutout"). Elgato's scene keys are
  pictorial with the name as a title.
- Our glyphs themselves (record dot, mark flag, mic, mic-muted, camera) are
  sound — the shapes are fine. The failure is background/state treatment and
  the text-only scene row, not the drawing.

No Elgato icon packs are installed (`IconPacks/` is empty). The **Key Creator**
plugin and the **official OBS Studio** plugin are both installed. [V]

---

## What is NOT wrong

- The plugin architecture is fine and current (`@elgato/streamdeck` 2.1,
  obs-websocket-js 5, Node 24, SDKVersion 3). [V]
- `obs-connection.ts` (reconnect loop, SSOT config read, cold-start) is a real
  asset — the official plugin has no cold-start.
- Chapter markers (`mark`) are verified end-to-end already
  (`scripts/verify_record_chapters.py`).
- `plugin/ARCHITECTURE.md` (uncommitted, 2026-07-22) is a thorough
  report-before-build for turning the plugin into a generic configurable
  product. That is a *different, larger* project than "make the deck good
  today" and should not be started to fix the above.

## Open fork for Ryan

Today's stated direction ("we're not reinventing it, we're going with Elgato's
premade templates and putting useful icons on the screen") sits against the
2026-07-21 reel-in ("build-not-buy; the deck surface is our own plugin").
Both are defensible; they produce different work. Decision recorded below once
made.
