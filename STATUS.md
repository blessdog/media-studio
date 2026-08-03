# STATUS — where media-studio stands

*Current state only. Updated 2026-08-03. If this file and the code disagree,
the code wins — then fix this file.*

**This is a reference, not a journal.** `tests/test_docs.py` caps it at 150
lines. When it grows past that, dated history **moves** to
[`docs/JOURNAL.md`](docs/JOURNAL.md) — it does not get deleted. Operating
manual: `AGENTS.md`. Phase map: `docs/PLAN.md`.

## Before you touch anything

- **`make check` must be green before you commit.** `.githooks/pre-commit`
  enforces it; run `make hooks` once per clone to install. `make check-live`
  adds the two Resolve-driving tests.
- **Resolve: `app.GetCurrentPage()` must return a page name.** `None` means a
  modal dialog holds the UI and *every measurement from that session is void*.
  This cost a full session on 2026-08-02. AGENTS.md §Hard doctrine.
- **A local commit is not a backup. Push.** AGENTS.md §Version control.

## Remotes

| Repo | Remote | Owns |
|---|---|---|
| `media-studio` | `blessdog/media-studio` (private, `master`) | video: capture → Story IR → Resolve → delivery |
| `~/projects/blessdog` | `blessdog/blessdog` (`feat/sound-control`) | music: Ableton + `phase8_sp404` SP-404 lane |
| `~/projects/rectum` | `blessdog/rectum` (private, pushed 2026-08-03) | screen-region clipper |
| `~/projects/obs-control-room` | `blessdog/obs-control-room` (private, pushed 2026-08-03) | Stream Deck / OBS plugin |

## What works

- **Story IR → Resolve compiler.** Lint → OTIO → import → verify, idempotent
  on content hash (`{name}@{hash8}`). `schema/story-ir.schema.json`, `studio/`.
- **Ingest lanes** — recording (silence + Deepgram), song, ScreenSage, bongpot.
- **Conversational assembly** — `edit-ir.py` find / insert-image / insert-clip /
  insert-graphic / add-music / add-stems / retime / remove.
- **Audio spine** — voice mirrored to A1, stems onto A2+ one per lane. Proven
  against live Resolve 21.0.2.4: 4-stem IR → 5 audio tracks, verify GREEN.
- **Beat grid** with `--bpm` override (librosa reads 117.45 on a perfect 120
  BPM click, so declare the tempo when you know it).
- **Scene Forge** — stills, I2V motion, headless Blender. Spend-gated.
- **Delivery fan-out** — one master render → platform formats, probe+loudness
  verified.
- **Pipeline G2** — `.als` → trigger map. `studio/ableton.py`,
  `tools/als-trigger-map.py`, 38 tests. Write-up: `docs/CLIP-LANE.md` §4.
- **SP-404 library builder** (in `blessdog`) — 10 samples / 476 MB staged,
  provenance ledger, BPM/key detection. 55 tests.

## What is broken or unproven

**13 reproduced defects** from the 2026-08-03 audit are the real queue —
`docs/ENGINEERING-AUDIT-2026-08-03.md` §Findings. The four that bite hardest:

| P0 | |
|---|---|
| **Wrong media can enter an edit** | `intake.resolve_safe()` reuses an existing underscore-normalised filename without checking content matches. Reproduced. Every later path/duration check still looks plausible |
| **Mutated IR is not schema-validated** | producers build dicts and call `lint()` directly, skipping JSON Schema. `30/0` passes the fps pattern then divides by zero; an empty IR lints green; removing the last edit can overwrite `story.json` with an invalid one |
| **The edit source of truth is unbacked** | `outputs/` (~1.4 GB) and `registry.db` are gitignored with no replacement backup. Each mutation overwrites `story.json`; 33 IR rows across 16 paths means past edit decisions are already unreconstructable |
| **`GetCurrentPage()` is doctrine, not code** | the modal-dialog rule that cost a session is enforced nowhere in production code, and the daemon's single-client lock is not shared with CLIs, other agents, or the MCP server |

| Other | |
|---|---|
| Cold-start gaps (P0.7, partly closed) | `make check` exists now; still missing a complete `requirements.txt`, a `doctor` verb, CI, and fixtures that don't reference gitignored media |
| SP-404 `push` to a card | **never run** — no card, no device on the desk |
| `bpm`/`key` backfill | 9 ledger entries predate `--analyze`; dedupe refuses a re-add, so there is no route. Needs an `analyze` verb that updates rows in place |
| No `remove` verb (SP lane) | nothing can leave the library once staged |
| `add` won't take a directory | a stem folder is four invocations |
| Innerbloom 123.0 BPM | detected, **unconfirmed**. One number from Ableton settles it |
| Deck-initiated capture | audio-capture permission was **denied** 2026-08-03 and cleared with `tccutil`; needs one press + Allow. Only affects the *fallback* lane — `rectum fetch` needs no permission |
| `rectum crop` scrolling / static clips | verified against ground truth (±7 px, survives a second moving region); scrolling-during-capture and no-motion clips still **[U]** |
| **[U]** `.otio` in `/private/tmp` | referencing media under `/Users` still fails with no dialog open. No tool produces that split, so it blocks nothing — do not build a workaround without re-measuring |

## Next

1. **Pipeline H — the emitter** (`docs/CLIP-LANE.md` §5, "NEW, small"). The
   trigger map (G2) and the ledger fields (§7) both exist; what is missing is
   the step that turns `sample_hash + track_start_secs` into video clips on the
   timeline. Needs no hardware. This is the piece that makes the whole lane pay.
2. **Finish the SP lane's rough edges** — `analyze` (in-place backfill),
   `remove`, directory-accepting `add`. Small, mechanical, no decisions.
3. **`[RYAN]`** — confirm Innerbloom's tempo from Ableton.
4. **`[RYAN]`** — `docs/CLIP-LANE.md` has four open decisions; the load-bearing
   one is whether a new small, single-purpose Loopback device may be created
   (captured clip audio is silent without it). Nothing existing gets touched.
5. **G1 (SP-404 SMF export)** when the unit lands. Day-one list:
   `docs/CLIP-LANE.md` §9 — **firmware first** (v5.00+ for Serato), then format
   the card in the device, then MIDI-monitor pad A1.
6. **Deck leftovers** — read `~/projects/obs-control-room/README.md` first.
   Move plugin `.pkg` needs Ryan's admin password; character scenes await his
   images; the $0 iPhone multicam test (`docs/IPHONE-MULTICAM.md`) has still
   never been run.

**Blender is genuinely open.** Ryan 2026-08-01: "a whole planning stage." Do not
start it without a research-first round. It is `blender/orbit-cube.py` and
nothing else.

## Where things live

| What | Where |
|---|---|
| Operating manual, verbs, doctrine | `AGENTS.md` |
| Dated history | `docs/JOURNAL.md` |
| Phase map | `docs/PLAN.md` |
| Story IR contract | `schema/story-ir.schema.json`, `docs/STORY-IR.md` |
| Music lane (pipelines A–E) | `docs/MUSIC-LANE.md` |
| Clip lane (pipelines F–G) | `docs/CLIP-LANE.md` |
| Engineering audit (2026-08-03) | `docs/ENGINEERING-AUDIT-2026-08-03.md` |
| SP-404 code + ledger | `~/projects/blessdog/phase8_sp404/`, `music/sp404-library.json` |

## Standing caveat

The SP-404 library currently holds **commercial reference tracks**. Fine as
pipeline practice; **samples cut from them must not reach published videos.**
