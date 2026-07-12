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

## Open issue (top of next session)

**Cold-start import flake.** `ImportTimelineFromFile` into a project *created in
the current session* fails silently (~half the time, non-deterministic) even
after the save/close/reload recipe. Same call succeeds when the project is
warm/pre-existing — the test suite passes, but a truly cold CLI first-build can
fail and need a retry. Evidence: ~4 inline/manual repros succeeded, ~4 CLI cold
runs failed, no single reliable differentiator found. This is the "silent
failure is the API's house style" reality the research warned about.

Candidate fixes to try next session (do NOT thrash live — pick one, test clean):
1. Create+configure the project in a **separate process**, exit, then compile
   in a fresh process (the create/import split — matches the "warm project
   imports fine" evidence).
2. Drive import through the **gursky MCP server** instead of raw scripting —
   it may sequence project ops more robustly (also the planned MCP-install task).
3. A warm-up: import a throwaway 1-clip timeline first, delete it, then import
   the real one.

Current `compile.py` retries 6× / 2s, which covers warm-session flakiness but
not a truly cold first build.

## Known Resolve quirks (doctrine, learned the hard way 2026-07-11)

- Project frame rate is immutable once a timeline exists → set fps on a fresh
  project before its first timeline (project-per-IR).
- OTIO inherits the *project's* fps on import, not the file's → stamp project fps.
- First `AddRenderJob()` in a fresh project can silently no-op → retry.
- Never `pkill` Resolve + relaunch → crashes libggml. Graceful quit + wait
  (`scripts/restart_resolve.py`).
- Renders inherit project-default fps unless set explicitly (the 24-vs-30 bug).

## Next

1. Harden cold-start (above) — small, isolated.
2. MCP server install (parallel track).
3. **Phase 2** — ingest lane: recording → Deepgram + auto-editor → IR → rough cut.
