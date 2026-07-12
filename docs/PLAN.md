# PLAN — full project scope + current position

*Approved by Ryan 2026-07-11 (plan-mode). Promoted to repo 2026-07-12 for
session continuity. Read CLAUDE.md and STATUS.md first; this file is the map.*

## The end state

Ryan hands the system a script/brief and raw material. Agents transcribe,
propose the cut, compile editable Resolve timelines, populate his approved
motion templates, apply his saved grades, render, and put finished files in
front of him. He does two things: creative brief at the front, verdicts on
rendered artifacts at the end. Tactile control via Stream Deck; zero GUI
scavenger hunts. Bongpot and cutwork are consumers, never absorbed.
Everything verified against ground truth at every stage.

## Division of labor (locked)

Ryan: briefs, scripts, taste, creative cut, template/grade approval, all
architecture + trust-boundary decisions.
Agents: ingest, transcription, rough assembly, template population, grade
application, render, delivery, verification.

## Phase map with live status

| Phase | Scope | Status |
|---|---|---|
| 0 Foundation | Studio license, scripting, smokes | ✅ 2026-07-11 |
| 1 Story IR + Compiler | schema/, studio/, tools/compile-ir.py, tests 9/9 | ✅ 2026-07-11 (path doctrine: ABSOLUTE paths to all Resolve calls) |
| 2 Ingest lane | tools/ingest-recording.py: recording → Deepgram + auto-editor → evidence-linked IR → verified timeline | ✅ 2026-07-11 |
| 3 Cut Brain v0 + Registry v0 | LLM (OpenRouter): transcript + brief → proposed IR, linted; SQLite registry | **NEXT** — [RYAN gate: registry scope; rec: this repo only] |
| 4 Template Library v0 | 3–5 Ryan-approved .setting templates; agent populates only; Anim-Curves doctrine; OGraf investigation | queued |
| 5 Studio Daemon + Deck | Python HTTP daemon owns Resolve lifecycle + verbs; Stream Deck keys | queued — [RYAN gates: Companion vs custom plugin (rec: Companion); MCP posture (rec: gursky for exploration + daemon verbs)] |
| 6 Finishing lane | Grade Library (DRX/LUT apply), delivery fan-out, bongpot adapter (video-plan.json seconds → IR frames) | queued |
| 7 Scene Forge | stills-first genAI (→I2V), native reference-identity before LoRA, Blender bpy, provenance | queued — [RYAN gate: provider mix + budget] |

Parallel tracks: MCP server install (cloned at vendor/davinci-resolve-mcp,
venv ready, run its install.py with Resolve up); BMD training (Ryan's craft
homework); **[RYAN gate: project name — "media-studio" is a placeholder]**;
cutwork×Resolve NOT planned unless Ryan changes cutwork doctrine there.

Dependency shape: 1 → 2 → 3 → (4, 5, 6 any order) → 7. Each phase
independently useful.

## Worked example — a music video through the system

Song (BlessDog or any track) = untouched audio spine (sacred-audio doctrine).
Beat-grid producer (small script, lands Phase 2/3): beat/section detection →
IR markers + candidate cut frames. Footage via Phase 2 ingest (waveform sync,
multicam prep). Visuals via Phase 7 (stills → curate → I2V winners + Blender
moves). Assembly via Phase 1 compiler (edits quantized to beat grid) → Ryan's
creative pass in the GUI. Look via Phase 6 grade + Phase 4 lyric/title
templates. Delivery fan-out via Phase 6. What stays Ryan's: which image lands
on which beat, and what the video means.

## Phase 3 drill-down (next up — needs Ryan's registry-scope blessing first)

1. **Registry v0** (SQLite, `studio/registry.py` + `registry.db` gitignored):
   tables assets / transcripts / irs / renders / decisions; every tool writes
   through it; the cross-session memory the research called the hardest problem.
2. **Cut Brain v0** (`studio/brain.py` + `tools/cut-brain.py`): OpenRouter call
   (model id in a config SSOT, per bible §2.2): transcript.json + Ryan's
   brief/script → proposed Story IR. Every edit MUST carry evidence; the
   deterministic linter gates before compile (bongpot lint-plan pattern).
   Key q for Ryan at design time: brief format (freeform text first).
3. Exit: script + recording in → approved rough cut out, every cut explainable
   via its evidence link. Test: speech.mp4 + a two-line brief.

## Session pickup checklist (after reboot)

1. Open Claude Code anywhere under `/Users/SSDrive/projects` (memory loads) or
   in `media-studio/` (CLAUDE.md loads).
2. Resolve running + external scripting Local (else `scripts/restart_resolve.py`).
3. Sanity: `.venv/bin/python tools/compile-ir.py tests/fixtures/golden-ir.json`
   → COMPILE OK (reused cached timeline).
4. Continue at Phase 3 (above) — ask Ryan the registry-scope gate first.

## Key doctrine (hard-won 2026-07-11, full list in STATUS.md)

- Absolute paths to every Resolve API call — relative fails silently.
- Project fps immutable once a timeline exists → project-per-IR, stamp fps first.
- Never pkill Resolve (libggml crash); graceful quit + wait.
- Verify artifacts, never self-reports; lint before spend; one-way flow
  (nothing scripted overwrites a human-touched timeline).
- Deepgram always, never Whisper. Templates/grades: agent applies, Ryan authors.
