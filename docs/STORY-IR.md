# Story IR — the central contract

Story IR is the versioned JSON document every edit-decision producer emits
(Cut Brain, ingest lane, beat-grid producer, bongpot adapter, or Ryan by hand)
and the ONLY thing the Timeline Compiler consumes. Schema:
`schema/story-ir.schema.json` (v0.1). Rules:

- **Frame integers everywhere.** No float seconds. Timing is meaningless
  without `timebase.fps` (rational string, e.g. `30/1`, `30000/1001`).
  Rationale: floats drift, frames are exact, NLEs think in frames.
- **`srcOut` is exclusive** (`duration = srcOut - srcIn`). Half-open ranges
  concatenate without off-by-ones.
- **Every edit may carry `evidence`** — opaque strings pointing at transcript
  utterances, beats, or brief items. The compiler doesn't interpret them; they
  exist so a human can ask "why this cut?" and get an answer.
- **The IR is the source of truth, never the timeline.** Humans edit timelines
  after compilation; nothing writes those changes back to IR (one-way flow,
  locked in CLAUDE.md).
- **Versioned schema.** Graphics, captions, audio-only tracks, transitions are
  deliberately absent from v0.1 and will arrive as version bumps, not silent
  shape changes.

## Identity & idempotence

`studio/ir.py` computes a canonical content hash (sorted-key JSON, whitespace
normalized). The compiled timeline is named `{name}@{hash8}`. Same IR → same
name → the compiler verifies instead of duplicating. Any content change →
new hash → new timeline. History accumulates in the project bin, harmless.

## Bongpot convergence

Bongpot's `video-plan.json` shots carry `id`, `covers` (evidence), `speaker`,
and float-second `start`/`end`. Field-name mapping for the Phase-6 adapter:
`covers` → `evidence[]`, seconds × fps → frames, one shot → one edit. The
adapter converts; neither format changes for the other.

## Emitter decision (recorded 2026-07-11, updated same day)

The compiler's interchange emitter is decided empirically by
`scripts/spike_otio.py` (kept in-repo): a minimal OTIO file built with the
`opentimelineio` library (v0.18.1) imported into Resolve 21.0.2 and probed for
clip count / fps fidelity.

### Spike result (2026-07-11) — OTIO is primary

Empirical findings on Resolve 21.0.2, verified with `scripts/spike_otio.py`,
`diag_import.py`, `diag_fps_recipe.py`:

1. **OTIO imports reliably and faithfully** — clip count, record offsets, and
   durations all exact (built with `opentimelineio` 0.18.1). **Primary emitter.**
2. **FCPXML regressed within-session** to returning `True` while silently
   creating no timeline (a lie worse than OTIO's honest behavior). Not used.
3. **OTIO inherits the PROJECT's timeline frame rate**, not the file's. This is
   controllable and is why the compiler stamps fps before import.
4. **Resolve locks project frame rate once any timeline exists.** So fps must
   be set on a fresh project before its first timeline.
5. **Imports into a just-created project fail silently** (`False`/no-op) until
   the project is saved, closed, and reloaded. This caused a confusing string
   of false failures during the spike; the reload clears it.

### The compiler recipe (proven)

Per IR, one project named `{name}@{hash8}`:
1. Create project (or load if it already exists → idempotence).
2. `SetSetting("timelineFrameRate", fps)` + resolution, **before any timeline**.
3. Save → close → **reload** (mandatory; clears fresh-project import flakiness).
4. `ImportTimelineFromFile(otio, {"timelineName": ...})`.
5. Add markers via API; verify.

Project-per-IR (not timeline-in-shared-project) because frame rate is
per-project-immutable and different IRs carry different rates.
