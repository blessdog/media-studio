# STATUS — where media-studio stands

*Updated 2026-07-11. If this file and the code disagree, the code wins — then
fix this file.*

## Done

- **Phase 0** ✅ — Studio 21.0.2.4 licensed, external scripting Local, e2e /
  headless / interchange / template smokes all pass. `scripts/smoke_*.py`.
- **Phase 1 — Story IR + Timeline Compiler** ✅ built & verified in steady state.
  - `schema/story-ir.schema.json` — IR v0.1 contract.
  - `studio/` — resolve (connection), ir (load/validate/hash), lint (ffprobe
    gates), emit (OTIO), compile (recipe), verify (structure + render/ffprobe).
  - `tools/compile-ir.py` — CLI: lint → compile → verify [--render].
  - `tests/test_compile.py` — passes 9/9 with `--render`, 7/7 without.
  - Exit condition MET: same IR → same timeline (idempotent), corrupted IR
    refused by lint, rendered output ffprobe-matches IR.
  - Emitter decision: **OTIO** (reliable/faithful; FCPXML regressed to silent
    no-op). Recorded in `docs/STORY-IR.md`.

## ~~Open issue~~ SOLVED (2026-07-11, next session)

**The "cold-start import flake" was never a flake.** Root cause:
`ImportTimelineFromFile` silently fails on **relative paths** — Resolve is a
separate process with its own CWD. Every historical failure had a relative
path; every success an absolute one. Proven back-to-back in one project:
relative → False, absolute → True. Fix: `compile.py` resolves the interchange
path absolute; retry loop removed (it was noise). True cold CLI build + render
now passes end-to-end.

**Doctrine: every path handed to any Resolve API call is absolute. No exceptions.**

## Known Resolve quirks (doctrine, learned the hard way 2026-07-11)

- Project frame rate is immutable once a timeline exists → set fps on a fresh
  project before its first timeline (project-per-IR).
- OTIO inherits the *project's* fps on import, not the file's → stamp project fps.
- First `AddRenderJob()` in a fresh project can silently no-op → retry.
- Never `pkill` Resolve + relaunch → crashes libggml. Graceful quit + wait
  (`scripts/restart_resolve.py`).
- Renders inherit project-default fps unless set explicitly (the 24-vs-30 bug).

## Phase 2 — Ingest lane ✅ (2026-07-11, same evening)

`tools/ingest-recording.py <recording> [--render]` — one command: probe →
auto-editor loudness spans (v3 export, maps losslessly to IR) → Deepgram
nova-3 diarized transcription (key in repo .env, gitignored) → Story IR with
per-edit utterance evidence + speaker-colored transcript markers mapped onto
the CUT timeline → lint → compile → verify [→ render+ffprobe].
Proven on a real spoken recording (say-generated): 3 speech spans kept, 3
utterances as evidence/markers, all gates green, rendered output verified.
Modules: `studio/{probe,transcribe,silence,ingest}.py`.
Transcribe degrades gracefully (missing key → silence-only ingest, warns).

## Phase 3 — Assembly Loop v0 + Registry v0 ✅ built (2026-07-12)

Reframed per Ryan's alignment correction (**copilot, not autopilot** — see
docs/PLAN.md blessed decisions; one-shot Cut Brain is dead). Shipped:

- **Registry v0**: `studio/registry.py`, SQLite `registry.db` (gitignored,
  this-repo scope blessed) — assets/transcripts/irs/renders/decisions; both
  tools write through it. `python -m studio.registry` to inspect. 8/8 tests.
- **Assembly verbs**: `studio/{moments,edit_ir,intake}.py` +
  `tools/edit-ir.py` (find/insert-image/retime/remove) — phrase →
  word-timestamp → record frame; pure IR mutations gated by lint; media
  filed into `<ws>/media/`; every change recompiles a fresh versioned
  timeline and SetCurrentTimeline's Resolve to it. 18/18 tests.
- **Schema v0.2** (additive): image assets as cutaway edits (srcIn=0,
  srcOut=duration). Verifier now checks EVERY video track (was V1-only).
- **Smokes**: still PNG rides OTIO import onto V2 natively (no ffmpeg
  fallback needed); SetCurrentTimeline works (`scripts/smoke_image_overlay.py`).
- **Proven end-to-end on speech.mp4**: find "key architectural decision" →
  frame 196 → insert meme 2.5s → render → extracted frames confirm meme
  pixels at the phrase moment.
- **AGENTS.md** added (harness-neutral operating manual, portability
  doctrine); CLAUDE.md slimmed to Ryan-specifics + pointer.
- **OBS switched to Hybrid MP4** (was MKV — Resolve can't import MKV;
  backup: basic.ini.bak-premp4). Verify on next real recording.
- Workspaces moved: `outputs/ingest/` → `outputs/projects/`.

**Exit test PASSED (2026-07-12)** on a real-scale sample (Ryan's 14.3-min
895MB iPhone recording, `outputs/projects/img-1700/`): ingest → 160-utterance
diarized transcript (audio-sidecar upload, not video bytes) → compiled
timeline → `find "been lopsided this whole time"` → frame 921 →
`insert-image` → lint green → recompiled versioned timeline
`img-1700@04675423` shown in Resolve, multi-track verify green. The sample is
FIXTURE MATERIAL — infrastructure and video-making are separate concerns;
Ryan's creative sessions are usage, not build.
**OBS Hybrid-MP4 VERIFIED (2026-07-12)** machine-to-machine: OBS is drivable
via its websocket (port/password read from its own plugin config — see
`scripts/verify_obs_recording.py`; obsws-python pinned). Test recording
rolled and ffprobed: mp4 container, h264+aac, Resolve-ingestable. This is
also the Phase 5 daemon's OBS control channel, proven early.
Incident note: an OBS stream output can WEDGE if stopped mid-reconnect
(ignores StopStream/StartRecord over websocket, ignores SIGTERM) — SIGKILL +
relaunch is the remedy; OBS shows a safe-mode prompt after (choose Normal
Mode; Safe Mode disables websockets).

## Next

1. MCP server install (parallel track, small).
2. R3 dialogue before Phase 4 (templates, incl. rant-visuals), per docs/PLAN.md.
3. Music overlay round (audio-track schema bump).
4. Ryan gates still open: project name, deck middleware, MCP posture.
