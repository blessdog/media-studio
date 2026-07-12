# CLAUDE.md — media-studio

## What this project is
The agentic instrument layer between Ryan and DaVinci Resolve Studio (the way
BlessDog is for Ableton). Ryan supplies scripts/research/intent; this layer
compiles structured edit decisions into editable Resolve timelines, populates
a curated Fusion template library, applies human-authored grades, and scripts
delivery. It is content-agnostic: bongpot and cutwork are CONSUMERS, not parts.
Read `RESEARCH.md` (verified ground truth) and `ARCHITECTURE.md` before
proposing anything.

## Locked decisions
- **Resolve Studio only.** No free-edition bridges in production.
- **Edits are computed OUTSIDE Resolve** (Story IR → FCPXML/OTIO →
  `ImportTimelineFromFile`). Never clip-by-clip API surgery; the API is
  append-only and that limit is permanent until proven otherwise.
- **One-way flow.** Compiled timelines go in; humans finish in the GUI;
  nothing scripted ever writes over a human-touched timeline.
- **Grades and templates are applied, not authored, by agents.** Curated
  libraries (Ryan's eyes gate entry); agents instantiate and populate only.
- **Adopt `samuelgursky/davinci-resolve-mcp`**; don't build a rival server.
- **No bespoke editing surfaces.** Resolve is the editor. Code is burners+glue.
- **Lint before spend; verify artifacts, not self-reports.** Silent failure is
  this API's house style (False returns, first-AddRenderJob no-op → retry).
- **Resolve lifecycle: quit gracefully, never pkill, and WAIT.** Save via API →
  AppleScript quit → poll until the process is actually gone (+ a few seconds)
  before any relaunch. A pkill + instant relaunch crashed Resolve 21.0.2 in
  libggml (its bundled ML runtime) on 2026-07-11. The Studio Daemon owns this
  sequence; nothing else starts/stops Resolve.
- **The bible** lives at `../bible/README.md`. Judge all architecture against it.

## Known state / active work
- **Read `STATUS.md` then `docs/PLAN.md` first** — live status + the full
  approved phase map with pickup checklist.
- 2026-07-11: Phases 0, 1, 2 ALL shipped on install day. Compiler + ingest
  lane work end-to-end, verified. Next: Phase 3 (Cut Brain + Registry) —
  blocked on Ryan's registry-scope gate. MCP install is a small parallel task
  (vendor/davinci-resolve-mcp cloned, venv ready).
- Open [RYAN] decisions in `ARCHITECTURE.md` §Open decisions (name, deck
  middleware, MCP posture, registry scope). Do not build past a blocked decision.

## How to work with me (Ryan)
- **Pressure-test before agreeing**; argue the "we don't need this" side first.
- **Verify before you assume**: `ls` / `git ls-files` before any claim about
  what exists. (This project exists because an unverified assumption about
  bongpot burned a session.)
- **Trust but verify**: read actual files/diffs/outputs, never summaries.
  Report WHERE work landed by exact path so verification takes seconds.
- **Mentor mode**: name principles and industry terms while working.
- **Architecture and trust boundaries are Ryan's calls.** Propose options.
- **Small commits**, one concern each, search-bait subjects. Tags before pivots.
- **His eyes are the verdict on anything visual** — render it and `open` it;
  never declare motion or a grade good unseen.
