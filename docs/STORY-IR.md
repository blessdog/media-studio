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

**RESULT: see the Spike Result section appended by the spike run.**
