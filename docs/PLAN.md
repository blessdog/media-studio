# PLAN — full project scope + current position

*Approved by Ryan 2026-07-11 (plan-mode). Promoted to repo 2026-07-12 for
session continuity. Read CLAUDE.md and STATUS.md first; this file is the map.*

## The end state

**Copilot, not autopilot** (Ryan's alignment correction, 2026-07-12 — this
overrides any earlier "brief in → finished video out" framing). Ryan MAKES the
videos: live OBS sessions driven from the Stream Deck (zoom-ins, cut scenes,
screen shares), iPhone footage, found media, his own script. The system is his
co-editor in the loop: scene-by-scene, conversational — place a meme image at
a moment, build a motion graphic for a beat, time an overlay to the music,
tighten a cut — Claude talking to Resolve at the software-to-software level,
every visual change returned to Ryan's eyes as a rendered artifact. He is the
creative input all the way through, not just at the ends. Agents do the
precision and the tedium: transcription, IR mutation, compile, template
population, grade application, render, delivery, verification. Tactile control
via Stream Deck; zero GUI scavenger hunts. Bongpot and cutwork are consumers,
never absorbed. Everything verified against ground truth at every stage.

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
| 3 Assembly Loop v0 + Registry v0 | conversational co-editing: transcript find + cutaway/retime/remove verbs, versioned timelines shown live in Resolve; SQLite registry | ✅ 2026-07-12 — exit test passed on real-scale sample (14-min iPhone recording); OBS Hybrid-MP4 verified machine-to-machine via websocket |
| 4 Template Library v0 | format packages (news-desk/podcast/documentary/retro), forge+place graphics pipeline, captions, ScreenSage ingest | news-desk ✅ APPROVED + exit test PASSED 2026-07-12; packages 2–4 + OGraf timebox remain |
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

## Blessed decisions 2026-07-12 (planning dialogue rounds 1–2)

- **Machine-first, GUI pass last.** Co-edit the IR via conversation; every
  machine change = fresh versioned timeline; Ryan's hands-on GUI edit is the
  final step and that timeline is never scripted again. No round-trip re-import.
- **Intake: drag into chat** → agent files it to `<workspace>/media/` +
  registers it (`studio/intake.py`). Nothing uploads anywhere; a drag hands
  the agent a disk path.
- **Recordings stay in `/Users/SSDrive/Movies`** (OBS output; semi-permanent,
  timelines link there). **OBS switched to Hybrid MP4** 2026-07-12 (Resolve
  cannot import MKV; backup at basic.ini.bak-premp4) — verify on Ryan's next
  real recording.
- **Verdicts live in Resolve**: each compile switches the open project to the
  new timeline; render only for final/motion-critical checks.
- **Meme house style: full-frame cutaway**, 3.5s default, voice under. PiP
  later behind a transform smoke test.
- **Workspaces: `outputs/projects/<name>/`.** Music overlay: later round
  (audio-track schema bump). Name: placeholder stays.
- **Portability doctrine**: AGENTS.md is the harness-neutral operating manual
  (any agent CLI can run the studio); repo is the memory; cold-start test is
  a recurring gate.

## Phase 3 drill-down — Assembly Loop v0 + Registry v0 (built 2026-07-12)

*Reframed 2026-07-12 per Ryan's alignment correction. The earlier "Cut Brain
v0" (one-shot OpenRouter brief→IR) is DEAD as a centerpiece — a one-shot
brief→video generator is not this project. Claude Code in session IS the
brain; what Phase 3 builds is the fast deterministic loop it drives while
Ryan and Claude work scene-by-scene.*

1. **Registry v0** (SQLite, `studio/registry.py` + `registry.db` gitignored —
   scope BLESSED 2026-07-12: this repo only): tables assets / transcripts /
   irs / renders / decisions; every tool writes through it; the cross-session
   memory the research called the hardest problem.
2. **IR verbs** (`studio/edit_ir.py`): safe programmatic IR mutations Claude
   drives conversationally — insert/remove/retime edits, shift a scene,
   place an asset at a record frame, add markers. Output is always a full IR
   that goes back through lint (nothing bypasses the gates).
3. **Scene previews** (`tools/preview.py` or verb in compile CLI): render just
   a frame range / working scene, not the whole timeline — seconds-fast
   feedback, artifact `open`ed on Ryan's screen. His eyes are the verdict.
4. (Demoted, optional later) an OpenRouter batch pass for cheap mechanical
   subtasks (e.g. candidate silence-cut suggestions) — never the author of
   the video.
5. Exit: a working session where Ryan says "put X at moment Y" style
   directions and gets a verified, rendered scene preview back within the
   conversation, with every change linted, compiled, and recorded in the
   registry. Test: speech.mp4 + a live co-editing exchange.

## Phase 4 drill-down — Template Library v0

Full doctrine in `docs/MOTION-GRAPHICS.md` (three tiers, formats, anti-slop).
Deliverables: 3–5 `.setting` templates (caption style, lower third, callout,
chapter card) authored as text, Anim-Curves duration-adaptive, each entering
the library ONLY via render-preview → Ryan's eyes; `studio/templates.py`
(populate installed template via fusionscript `SetInput`, or write
per-instance .setting); template linter; IR schema bump to carry a `graphics`
entity (version 0.2 — additive). Insertion via
`InsertFusionTitleIntoTimeline` (proven). OGraf investigation time-boxed.

## Phase 5 drill-down — Studio Daemon + Deck

Daemon (Python, localhost HTTP): owns Resolve lifecycle — the proven
`scripts/restart_resolve.py` sequence (save → AppleScript quit → poll exit →
+5s settle → launch; NEVER pkill, libggml crash) becomes its restart verb.
Verbs v0: `arm-capture` (Audio Hijack `.ahcommand` — requires its
Settings > Advanced "Allow execution of external scripts"), `ingest-last`
(newest file in OBS output dir → tools/ingest-recording.py), `rough-cut`,
`queue-render`, `status`. Deck wiring: **Companion first** (4.3.4, 700+
modules incl. OBS, generic HTTP button → daemon; no Resolve module needed) —
custom Node plugin (SDK WebSocket: keyDown/dialRotate/touchTap in, per-key
images/state OUT) only later if live key-state displays earn it. Farrago:
official first-party plugin (Settings > Controllers; six action types; works
backgrounded) — zero glue. MCP posture rec: gursky server for
exploration/conversational control; the daemon's verbs stay deterministic.

## Phase 6 drill-down — Finishing lane

**Grade Library** (author-once, apply-forever — verified API surface):
Ryan builds a look by hand in the color page → saved as DRX still (+ LUT
export via `ExportLUT`, 17/33/65pt CUBE) → versioned in repo → agent applies
per-clip via `ApplyGradeFromDRX(path, gradeMode)` / `Graph.SetLUT(nodeIdx,
path)` / `CopyGrades`. NOT scriptable (confirmed v21 README): wheels, curves,
qualifiers — grades are appliable, never authorable, by script. `SetCDL`
(slope/offset/power/sat) for coarse scripted correction.
**Delivery fan-out**: named presets → YouTube master / vertical / podcast
audio (loudness via ffmpeg — Fairlight is essentially unscriptable). Render
quirk: first `AddRenderJob` in a fresh project can no-op → retry guard.
**Bongpot adapter** (one-way): `video-plan.json` `cut.shots`
{id, covers, start/end float-seconds, speaker} → Story IR
(covers→`evidence[]`, seconds×fps→frames, one shot→one edit) → finishing
timeline with approved Wan clips on V1 + untouched call audio on A1 + shot
IDs/verdicts as markers. FFmpeg lane stays the deterministic default;
nothing writes back to bongpot.

## Phase 7 drill-down — Scene Forge

**Stills-first economics** (verified pricing 2026-07-11): stills ~$0.039
(Nano Banana) vs video $0.05/s (Veo 3.1 Lite 720p) / $0.10–0.12 (Fast) /
$0.40 (Standard 1080p) — generate MANY stills, curate hard, animate winners
only. Veo 3/2 are DEAD (shutdown 2026-06-30) — 3.1 model ids only.
**Character consistency**: native reference-identity FIRST (Veo/Sora identity
anchors; open-weights Wan 2.2 Animate holds identity from a single reference
image via DWPose+SAM2, FP8 14B checkpoint), train a LoRA only for a recurring
character reused across many videos. Kling v3 tops the blind-vote arena
(small sample); Hailuo/Seedance cited strongest at I2V; open-weights on GPU
rental wins above ~5K videos/mo (blog-grade heuristic).
**Blender bpy headless**: deterministic camera work (the mountain-road car
shot), repeatable scenes, alpha overlays; hybrid worth testing =
Blender-rendered motion → Wan Animate restyle (its video-driving mode).
Everything lands in Registry with provenance (model, prompt version,
license). Curation surface = files on disk + Ryan's eyes, not a bespoke UI.

## Deferred / explicitly out of scope until revisited

- Audio-only IR tracks, transitions, retimes (schema bumps when needed).
- Multicam sync producer (Phase 2 extension when a real shoot needs it).
- Beat-grid producer for music videos (small; lands with Phase 2/3 code).
- Watch-folder auto-ingest (end of Phase 2 scope, optional).
- Selling any of this (market research in RESEARCH.md Part 5: capped/niche/
  productized or nothing; service-first if ever).

## Session pickup checklist (after reboot)

1. Open Claude Code anywhere under `/Users/SSDrive/projects` (memory loads) or
   in `media-studio/` (CLAUDE.md loads).
2. Resolve running + external scripting Local (else `scripts/restart_resolve.py`).
3. Sanity: `.venv/bin/python tools/compile-ir.py tests/fixtures/golden-ir.json`
   → COMPILE OK (reused cached timeline).
4. Continue at Phase 3 (above) — registry gate is blessed; build per drill-down.

## Key doctrine (hard-won 2026-07-11, full list in STATUS.md)

- Absolute paths to every Resolve API call — relative fails silently.
- Project fps immutable once a timeline exists → project-per-IR, stamp fps first.
- Never pkill Resolve (libggml crash); graceful quit + wait.
- Verify artifacts, never self-reports; lint before spend; one-way flow
  (nothing scripted overwrites a human-touched timeline).
- Deepgram always, never Whisper. Templates/grades: agent applies, Ryan authors.
