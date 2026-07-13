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
| `tools/edit-ir.py <ws> insert-clip <video> --where\|--at\|--record [--src-in s] [--dur s]` | found-b-roll video cutaway on the overlay track |
| `tools/edit-ir.py <ws> insert-graphic <template> --where\|--at\|--record [--dur s] [--input K=V ...]` | APPROVED library template instance (forged alpha master, placed exactly) |
| `tools/edit-ir.py <ws> add-music <audio> [--where\|--at\|--record] [--src-in s] [--dur s]` | music/sfx bed on its own audio lane (A2+); voice on A1 is sacred |
| `tools/edit-ir.py <ws> retime <edit-id> [--record F] [--dur s]` | move/stretch an edit, recompile |
| `tools/edit-ir.py <ws> remove <edit-id>` / `remove-graphic <id>` | remove edit/graphic (+ orphaned asset), recompile |
| `tools/compile-ir.py <ir.json> [--render] [--show]` | lint → compile → verify (structure; `--render` closes the loop to pixels) |
| `tools/preview-template.py <name> [--input K=V] [--open]` | render a template preview over real footage — the library approval gate (Ryan's eyes) |
| `tools/make-captions.py <ws> [--native]` | transcript → SRT remapped to the cut timeline; `--native` = Resolve AI subtitles |
| `tools/ingest-screensage.py <bundle> [--name N]` | ScreenSage bundle → multitrack timeline (voice by loudness, VFR→CFR, camera cut-in asset, click/zoom markers) |
| `tools/deliver.py <ws> [--presets vertical,podcast-audio]` | fan-out: ONE Resolve master render → ffmpeg-derived platform formats, all probe+loudness verified, in <ws>/delivery/ |
| `tools/ingest-bongpot.py <call-dir> [--partial] [--clips D] [--audio MP3]` | bongpot video-plan → finishing timeline: shots conformed to V1 (scale/crop/fps/last-frame-pad to the exact window), untouched call audio on A1, shot ids/speakers/verdicts as colored markers (Red=missing/reject, Yellow=rework, Green=approved, Sky=unreviewed). ONE-WAY read of the bongpot repo; fails closed on missing clips unless `--partial` |
| `tools/forge-stills.py <ws> "<prompt>" [--n 8] [--model qwen-fast\|flux-2] [--ref img] [--approve]` | genAI stills batch → `<ws>/forge/batch-NN/` + numbered contact sheet opened in Preview; Ryan answers with winner numbers (`--pick 2,7,11`). **SPEND GATE: never pass `--approve` without Ryan approving that batch's printed cost in conversation** |
| `python -m studio.registry [table]` | inspect the cross-session registry (assets/transcripts/irs/renders/decisions) |
| `python -m studio.daemon` | studio daemon on 127.0.0.1:8873 — GET /status /verbs /jobs; POST /verb/<name> (record-start, stop-and-ingest, ingest-last, ingest-screensage, compile, restart-resolve). Long verbs = background jobs, logs in outputs/daemon/ |
| `scripts/restart_resolve.py` | ONLY sanctioned way to restart Resolve (graceful save→quit→wait; pkill crashes it) |

Python modules under `studio/` back these verbs; tests under `tests/` are
plain scripts (`test_compile.py`, `test_registry.py`, `test_assembly.py`).

## Hard doctrine (violations fail silently — learned the hard way)

- **Absolute paths to every Resolve API call.** Relative fails silently.
- **NO SPACES in media paths handed to OTIO import** — Resolve fails/HANGS on
  percent-encoded URLs (confirmed 2026-07-13). `studio.intake.resolve_safe()`
  hardlinks a safe name; lint refuses spaced paths on used assets; OBS
  filename format switched to space-free (websocket-settable).
- **One fusionscript client at a time.** A long-lived in-process connection
  concurrent with other clients wedges the scripting service (restart is the
  only cure). The daemon probes Resolve via short-lived subprocesses behind
  its job lock; scripts must not linger.
- **Lint before Resolve, verify artifacts after** — never trust API return
  values or your own reasoning; ffprobe and timeline inspection are truth.
- Project fps is immutable once a timeline exists → project-per-IR, fps
  stamped before the first timeline (compile.py owns this).
- Never `pkill` Resolve. First `AddRenderJob` may silently no-op → retry.
- Resolve's API is append-only: mid-timeline edits are impossible; the IR +
  full recompile IS the edit mechanism.
- Deepgram for transcription, never Whisper. Templates/grades: agents apply,
  Ryan authors.
- **Audio spine (epoch 2)**: track-1 video edits mirror their audio onto A1;
  video cutaways (V2+) are silent by design; audio assets get audio lanes
  (A2+ music). Renders are loudness-checked when the IR implies sound —
  every timeline before 2026-07-13 was silently MUTE; the verifier now has
  ears. `ir.py COMPILER_EPOCH` must be bumped whenever identical IR would
  compile differently.
- Requirements pinned in `requirements.txt`; venv at `.venv/`. Deepgram key
  in `.env` (never commit).

## Cold-start test (portability gate)

A fresh agent with zero conversation history must be able to run the whole
loop from this file alone: Resolve open (external scripting = Local), then
`ingest-recording.py` a clip, `edit-ir.py find/insert-image`, verify green.
If any step needs knowledge not written here or in docs/, that's a bug —
fix the docs.
