# Architecture — media-studio

*Status: PROPOSAL, 2026-07-11. Grounded in RESEARCH.md (verified claims) and
reconciled against the second-opinion report (RESEARCH.md Part 8). Decisions
marked **[RYAN]** are open and his to make; nothing below builds until the
[RYAN] items in "Open decisions" are blessed.*

## What this is

An agentic instrument layer over DaVinci Resolve Studio. Precedent: BlessDog
(Ableton). Consumers: bongpot (LPC film pipeline — uses this layer for the
"manual finishing via real external editor" slot its doctrine reserved),
cutwork (general lane — **doctrine change required there before Resolve enters
that lane; do not drift into it**), and Ryan's script/research → video work
directly.

**Division of labor (locked by the research, both reports converged):**
Ryan owns the brief, the creative cut, taste, and final grade authorship.
The agent owns ingest, transcription, rough assembly, template instantiation,
grade *application*, render, and delivery. The live Resolve timeline is never
the source of truth; one-way flow — compiled timelines go IN, humans finish,
nothing scripted writes over a human-touched timeline.

## Hard constraints (verified — see RESEARCH.md Part 1)

1. External scripting requires **Studio**; it's a Preferences toggle (Local).
2. Timelines are **append-only** via API — no move/trim/razor/effects/keyframes.
   All edit construction happens externally → FCPXML/OTIO → `ImportTimelineFromFile`.
3. Color: grades are **appliable, not authorable** by script (`ApplyGradeFromDRX`,
   `SetLUT`, `SetCDL`, `CopyGrades`). Wheels/curves/qualifiers: no API.
4. Silent failure is normal (Studio-only calls return `False`; first
   `AddRenderJob` in a fresh project can silently no-op → retry). Every stage
   verifies its own output artifact (ffprobe, counts, durations).
5. `-nogui` headless works; Resolve runs as a pre-launched daemon.

## Components

| # | Component | What it is | Contract in / out |
|---|-----------|-----------|-------------------|
| 1 | **Registry** | SQLite SSOT: assets, transcripts, cut decisions, grades, templates, renders, provenance | everything reads/writes here |
| 2 | **Resolve Op** | Adopted `samuelgursky/davinci-resolve-mcp` + thin wrappers; headless daemon lifecycle | MCP tools / Python calls |
| 3 | **Timeline Compiler** | Deterministic: Story IR → FCPXML/OTIO → imported editable timeline with markers | Story IR JSON in, timeline + verification report out |
| 4 | **Cut Brain** | LLM stages: transcript + script/brief → proposed Story IR (evidence-linked, frame-integer) | transcript+brief in, Story IR out, **linted before compile** |
| 5 | **Template Library** | Curated Fusion `.setting` macros (8–15, Ryan-approved motion), Anim-Curves-based; agent instantiates/populates only | structured content in, Inspector-editable timeline objects out |
| 6 | **Grade Library** | Ryan-authored DRX stills / LUTs, versioned; agent applies via node graph API | look name in, graded clips out |
| 7 | **Scene Forge** | GenAI stills → curate → I2V (Veo tiers / Kling / Wan) + Blender `bpy` for deterministic 3D; alpha renders for overlays | brief in, baked media + provenance out |
| 8 | **Studio Daemon + Deck** | Local Python HTTP daemon exposing pipeline verbs; Stream Deck via Companion or custom Node plugin; Farrago/OBS already native | key press in, verb execution + key-state feedback out |
| 9 | **Verifier** | Cross-cutting: artifact probes gate every stage transition | artifact in, pass/fail + diagnostics out |

## The central contract: Story IR

Versioned JSON, Resolve-independent (adopted from second report, Part 8):
frame-integer edits (`{asset, src:[in,out], dst, track, beat, evidence[]}`),
assets with hashes, beats with intent, graphics/captions/music as first-class
entities, provenance (model, prompt version). The Cut Brain **proposes** IR;
a deterministic linter gates it (bongpot's lint-plan pattern); the Compiler
**applies** it. Same shape as bongpot's video-plan.json → convergence
opportunity later, not a day-one merge.

## Anti-slop doctrine (locked by Ryan's standing rules)

- **Curated libraries over generated variety**: templates and grades enter the
  library only through a render-preview → Ryan's-eyes gate. Agent instantiates;
  it does not freestyle aesthetics onto timelines.
- **No bespoke editing surfaces** (bongpot rule generalizes): Resolve is the
  editor; code is burners + glue; the review desk pattern is for gating.
- **Lint before spend**: every LLM-authored artifact (Story IR, .setting) passes
  a deterministic linter before it costs GPU time or touches Resolve.
- **Verify against ground truth**: stage N+1 trusts only stage N's probed
  artifact, never its self-report.

## Build order (each phase independently useful; exit conditions per bible)

| Phase | Deliverable | Exit condition |
|---|---|---|
| 0 ✅ | Studio purchased + installed; `docs/INSTALL-DAY.md` executed; BMD Edit/Fusion training started | External scripting Local works; bundled Developer README diffed vs mirror |
| 1 ✅ | Story IR v0.1 + deterministic compiler (`studio/`, `tools/compile-ir.py`) → editable timeline + render, ffprobe-verified; test 9/9 | MET (steady state); cold-start import flake open — see STATUS.md |
| 2 | auto-editor handoff: real recording → silence-stripped editable timeline | Timeline opens with cuts as clips, relinked media |
| 3 | Cut Brain v0 + IR linter: script + transcript → Story IR → compiled rough cut | Every cut carries evidence; lint gate holds |
| 4 | Template Library v0: 3–5 Ryan-approved `.setting` templates + agent population | Templates appear in Effects Library; agent fills text/params; motion approved by eye |
| 5 | Daemon + Deck: 3 daily verbs on physical keys | Key → verb → state feedback round-trip |
| 6 | Grade Library + delivery presets; bongpot plan→timeline compiler | Bongpot film finishes in Resolve without touching its FFmpeg lane |
| 7 | Scene Forge integration | Brief → curated stills → animated clips in Registry with provenance |

## Open decisions **[RYAN]**

1. **Project name** (media-studio is a placeholder).
2. **Deck middleware**: Bitfocus Companion (fast, generic HTTP) vs custom Node
   plugin (live key-state displays). Recommendation: Companion first.
3. **MCP posture**: adopt gursky's server as-is for exploration + wrap our own
   deterministic verbs in the daemon (recommendation), or granular-tools-only.
4. ~~**Registry scope**~~ BLESSED 2026-07-12: **this repo only** (widen later
   only if the split lesson says otherwise).
5. **Veo/Kling/Wan provider mix and budget** for Scene Forge (deferred to Phase 7).
6. **Whether cutwork ever routes through Resolve** (its doctrine currently says
   hyperframes; a change is Ryan's call, made there, not here).
