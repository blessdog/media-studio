# media-studio

> **NAME IS A PLACEHOLDER** — Ryan hasn't blessed a name yet. Renaming is one `mv`.

The content-agnostic **agentic instrument layer** between Ryan (and his AI
agents) and DaVinci Resolve Studio — the way BlessDog sits between him and
Ableton. Ryan writes scripts, research, and creative intent; the agent layer
turns intent into finished video by operating Resolve: compiling timelines
from structured edit decisions, populating a curated Fusion template library,
applying human-authored grades, and scripting delivery. Existing pipelines
(bongpot, cutwork) are consumers of this layer, not parts of it.

- `RESEARCH.md` — the verified ground-truth research this is built on (read first)
- `ARCHITECTURE.md` — components, contracts, build order, open decisions
- `docs/ENGINEERING-AUDIT-2026-08-03.md` — current-state architecture, health audit, risks, roadmap, and new-engineer onboarding
- `docs/INSTALL-DAY.md` — the checklist for the day Resolve Studio lands

## The journey

**Install day was a gauntlet, on purpose (2026-07-11).** Resolve
Studio landed and the same day produced five passing smokes:
scripted project→import→timeline→markers→render, FCPXML interchange
(auto-editor cuts arriving as an editable timeline), fully headless
`-nogui` render, and agent-authored Fusion title templates inserted by
API. The doctrine that survived contact: **graceful Resolve lifecycle
only** — `pkill` + instant relaunch crashes libggml, so the studio is
opened and closed like an instrument, not a process.

**The Story IR is the contract.** Edit decisions are a JSON-Schema
document, not API calls: intent compiles to OTIO, imports into
Resolve, and is verified back out (9/9 round-trip steady-state).
Deterministic lint gates run before anything touches the studio. The
day-one flake that justified all this ceremony:
`ImportTimelineFromFile` **silently fails on relative paths** — the
kind of bug you only catch by verifying the import, never by trusting
the call.

**The gate that made the tests real (2026-08-03).** An audit found
that nothing ran the test suite, so nothing enforced anything —
`make check` plus a pre-commit hook closed that. Same session's other
lessons: two agents on one master branch is how work gets eaten
(worktrees now), a "silent" Stream Deck failure was actually a DENIED
audio-capture permission, and crop math is verified against rendered
ground truth, not trusted.

## Status

Working plumbing, honest about being plumbing: the instrument layer
runs end-to-end against Resolve Studio; what's rendered so far is
smoke fixtures and verification clips, not showpieces. The consumers
(bongpot, cutwork) drive what gets built next. Name is a placeholder.
