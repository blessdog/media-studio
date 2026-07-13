# AGENTS.md — operating manual (harness-neutral)

This file is the single source of truth for HOW to operate this project.
It is written for ANY agent harness (Claude Code, Codex CLI, Gemini CLI,
Cursor, ...): if you can run shell commands and edit files, you can run this
studio. Ryan-specific collaboration rules live in CLAUDE.md; architecture in
ARCHITECTURE.md; verified research in RESEARCH.md; live state in STATUS.md
and docs/PLAN.md.

## What this is

The agentic instrument layer between Ryan and DaVinci Resolve Studio.
**Copilot, not autopilot**: Ryan makes his videos (OBS + Stream Deck screen
recordings, iPhone footage, found media, his script); the agent is the
in-loop co-editor — scene by scene, conversationally. NO one-shot
brief→finished-video generation, ever.

## The working loop (all decisions blessed 2026-07-12)

1. Ryan records in OBS (Hybrid MP4 → `/Users/SSDrive/Movies`; recordings STAY
   there — never move/clean that folder casually, timelines link to it).
2. Ingest: one command → silence-stripped, transcript-anchored timeline in
   the open Resolve, workspace at `outputs/projects/<name>/`.
3. Assembly dialogue: Ryan directs ("insert this meme where I say X"); agent
   finds the moment via word-level transcript timestamps, mutates the
   workspace's `story.json` (the Story IR — the ONLY source of truth for the
   edit), lints, recompiles to a NEW versioned timeline `{name}@{hash8}`,
   and switches Resolve to it. Ryan scrubs and verdicts live in Resolve.
4. Media intake: Ryan drags a file into the chat (= hands the agent a disk
   path; nothing uploads) → agent files it into `<workspace>/media/` via
   `studio.intake.file_media` and registers it.
5. Ryan's hands-on GUI pass is the FINAL step. After he touches a timeline,
   scripts never modify it again (one-way flow). Machine changes always
   produce a fresh timeline from the IR.
6. House style: memes default to full-frame cutaway, 3.5s, voice under.

## The verbs (CLI — the whole agent interface)

All run as `.venv/bin/python <tool> ...` from the repo root. Nonzero exit =
gate failure. Every path handed to Resolve must be ABSOLUTE (doctrine).

| Verb | Does |
|---|---|
| `tools/ingest-recording.py <file> [--name N] [--render]` | recording → probe → silence spans → Deepgram transcript → Story IR → compiled timeline, shown in Resolve. Workspace: `outputs/projects/<name>/` |
| `tools/edit-ir.py <ws> find "phrase"` | locate spoken words → timeline frame + timecode |
| `tools/edit-ir.py <ws> insert-image <img> --where "phrase" \| --at M:SS \| --record F [--dur s]` | file image into media/, cutaway edit, lint, recompile, show |
| `tools/edit-ir.py <ws> retime <edit-id> [--record F] [--dur s]` | move/stretch an edit, recompile |
| `tools/edit-ir.py <ws> remove <edit-id>` | remove edit (+ orphaned asset), recompile |
| `tools/compile-ir.py <ir.json> [--render] [--show]` | lint → compile → verify (structure; `--render` closes the loop to pixels) |
| `python -m studio.registry [table]` | inspect the cross-session registry (assets/transcripts/irs/renders/decisions) |
| `scripts/restart_resolve.py` | ONLY sanctioned way to restart Resolve (graceful save→quit→wait; pkill crashes it) |

Python modules under `studio/` back these verbs; tests under `tests/` are
plain scripts (`test_compile.py`, `test_registry.py`, `test_assembly.py`).

## Hard doctrine (violations fail silently — learned the hard way)

- **Absolute paths to every Resolve API call.** Relative fails silently.
- **Lint before Resolve, verify artifacts after** — never trust API return
  values or your own reasoning; ffprobe and timeline inspection are truth.
- Project fps is immutable once a timeline exists → project-per-IR, fps
  stamped before the first timeline (compile.py owns this).
- Never `pkill` Resolve. First `AddRenderJob` may silently no-op → retry.
- Resolve's API is append-only: mid-timeline edits are impossible; the IR +
  full recompile IS the edit mechanism.
- Deepgram for transcription, never Whisper. Templates/grades: agents apply,
  Ryan authors.
- Requirements pinned in `requirements.txt`; venv at `.venv/`. Deepgram key
  in `.env` (never commit).

## Cold-start test (portability gate)

A fresh agent with zero conversation history must be able to run the whole
loop from this file alone: Resolve open (external scripting = Local), then
`ingest-recording.py` a clip, `edit-ir.py find/insert-image`, verify green.
If any step needs knowledge not written here or in docs/, that's a bug —
fix the docs.
