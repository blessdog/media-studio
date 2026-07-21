# DECK — Stream Deck XL → Companion → daemon (wired 2026-07-13) — RETIRED

**RETIRED 2026-07-21.** The Companion chain below is historic: the deck
surface is now Ryan's own plugin at `~/projects/obs-control-room` (see its
README). The "Companion XL" Elgato profile is removed (backup:
`~/Library/Application Support/com.elgato.StreamDeck/ProfilesV3-retired-2026-07-21/`)
and the Companion app is quit — it had ONE job (deck bridge) and that job
moved into the plugin. Post-mortem worth remembering: after 7/13 the XL
sat on the half-blank Companion profile while every later session built
plugin keys onto the unselected Default Profile — logs said "verified",
Ryan's eyes saw a dead surface for a week. Ground-truth the INSTRUMENT,
not the logs. Companion-v5 config-by-database doctrine below kept for
reference.

The tactile chain, proven live by Ryan's fingers:
**XL key → Elgato app (Companion Button plugin) → Companion v5 →
internal `exec` action → curl → studio daemon verb → OBS/Resolve.**

## Layout (Companion page 1 — "MEDIA STUDIO")

| Key (row/col) | Label | Verb |
|---|---|---|
| 0/1 | ● REC (red) | record-start |
| 0/2 | ■ STOP + INGEST (blue) | stop-and-ingest |
| 1/1 | INGEST LAST | ingest-last |
| 1/2 | INGEST SSAGE | ingest-screensage |
| 3/7 | RESTART RESOLVE (amber) | restart-resolve |

Deck profiles: Ryan's OBS rig lives in his own Elgato profile (untouched);
the plugin's auto-created **"Companion XL" profile** mirrors Companion pages
1:1 — switching profiles = switching control surfaces. Individual Companion
Button tiles can be dragged into his main profile for permanent studio keys
(drill-down later, per Ryan: build all phases first, polish components after).

## Coexistence doctrine

The Elgato app OWNS the deck; Companion reaches it through the
`io.bitfocus.companion-plugin` (v3.3.1, installed from GitHub releases via
`open file.streamDeckPlugin`). Companion's log line "cannot open device"
is EXPECTED — it must not open the deck directly.

## Companion v5 config-by-database (no GUI, learned from bundled source)

Companion v5 has no config API; its state is
`~/Library/Application Support/companion/v5.0/db.sqlite` — every table is
(id, value-JSON). QUIT COMPANION before writing. Shapes that matter:

- `pages` row id "1": `{id, name, controls: {"<row>": {"<col>": "bank:<id>"}}}`
- `controls` row `bank:<nanoid>`: `{type: "button-layered", options:
  {stepProgression: "auto", rotaryActions: false, canModifyStyleInApis:
  false, notes: ""}, style: {layers: [canvas, box, text]}, feedbacks: [],
  localVariables: [], steps: {"0": {action_sets: {down: [ACTION], up: []},
  options: {runWhileHeld: []}}}}`
- Style layer + **action option values are `{value, isExpression}` objects**
  — plain values parse as EMPTY silently (textinputs) or error (numbers).
  This was the only failure mode in the whole wiring.
- ACTION: `{type: "action", id: "<nanoid>", definitionId: "exec",
  connectionId: "internal", options: {path: {value: "<shell cmd>",
  isExpression: false}, cwd: {...}, timeout: {value: 10000, ...},
  targetVariable: {value: "", ...}}}`
- The internal `exec` action needs `"enable_shell_command_support": true`
  in `~/Library/Application Support/companion/config.json` (launcher
  restart applies it).
- Backup exists at `v5.0/db.sqlite.pre-studio`.

## Also present (from the plugin handshake)

Ryan's Elgato app also registers a **Stream Deck +** (4x2 + dials) and
**Stream Deck Mobile** — future surfaces for the same Companion pages.
