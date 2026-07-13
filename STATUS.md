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

## Phase 4 — Template Library v0: infrastructure BUILT (2026-07-12)

Round 3 dialogue done (all four format packages blessed; per-package looks;
rant visuals = per-video choice, never a default; composite = OBS live +
post verb). Built & verified same day:

- **Graphics pipeline** (doctrine in docs/MOTION-GRAPHICS.md): forge cached
  ProRes4444+alpha masters → AppendToTimeline placement (title insert
  RIPPLES V1 — dead path; OTIO refuses ProRes4444 refs — smoked). Verified
  to pixels. IR v0.3 `graphics` entity; approved-only lint gate;
  `insert-graphic` / `insert-clip` / `remove-graphic` verbs; multi-track +
  graphics verifier. Tests 31/31.
- **Captions**: `tools/make-captions.py` — transcript → SRT remapped
  through kept spans to CUT-timeline time; `--native`
  CreateSubtitlesFromAudio exists (smoked, unexercised).
- **ScreenSage ingest**: `tools/ingest-screensage.py` — bundle →
  multitrack timeline; loudness-based voice pick (his mic often routes to
  OBS → near-silent sidecar), VFR→CFR normalization (screen captures are
  VFR — poison for frame integers), camera cut-in asset, click/zoom events
  as markers. Ryan's real 79s rig demo rebuilt: `rig-demo@48432052`.
- **News-desk package v1 authored** (templates/news-desk/): headline,
  ticker (scrolling expression), bug, LIVE tag — all `approved: false`,
  previews rendered over Ryan's own rig footage (outputs/previews/),
  self-checked, opened for HIS verdicts. Nothing enters the library
  without them.

**News-desk package APPROVED** (Ryan: "love it", all four on first
previews, 2026-07-12) — manifest + registry flipped.
**Phase-4 exit test PASSED** on the rig demo (`rig-demo@1f92f016`): one
conversation placed headline ("THE FEEDBACK LOOP IS REAL") + scrolling
ticker + his camera track as a 5s cut-in + remapped captions.srt; all gates
green, render verified, graphics confirmed in extracted frames. Honest
caveat: captions exist as the SRT deliverable; the --native subtitle-track
path is smoked but not yet exercised on a real timeline.
Fix landed en route: spans_from_ir now keys on the track-1 asset (multi-
video-asset IRs broke the old single-asset assumption).

## Audio spine ✅ (2026-07-13) — and a confession

**Every timeline compiled before today was MUTE.** emit built video tracks
only; the verifier had no ears; "verified to pixels" never listened. Caught
by ground-truthing A1 before building music support (render measured -91 dB).
Shipped: A1 mirrors track-1 voice frame-exact; cutaways silent by design;
audio assets on their own lanes (`add-music` verb, A2 beds); forge masters
render audio-free (cache key salted); verify checks audio lanes structurally
AND volume-detects renders (silence = red). COMPILER_EPOCH introduced in
ir.py — bump it whenever identical IR would compile differently, so stale
timelines can't satisfy idempotence. Proven: loop-demo voice+music render
at -1.8 dB max; suites 39/39 + 9/9 --render. Packages 2–4 provisionally
approved same day (aesthetics pass later).

## Studio Daemon v0 ✅ (2026-07-13) + two hard-won doctrines

`python -m studio.daemon` → 127.0.0.1:8873; verbs shell the same CLIs any
harness uses; background jobs, logs in outputs/daemon/. Money path PROVEN
end-to-end: POST record-start → OBS records → POST stop-and-ingest →
compiled verified timeline in Resolve, zero human clicks.
Found the hard way en route:
- **Spaces in media paths break/HANG Resolve's OTIO import** (discriminating
  test: same 60fps file, space-free hardlink imports perfectly). Fixes:
  resolve_safe() hardlinks, lint gate, OBS filename format now space-free
  (set via websocket). 60fps was innocent.
- **Concurrent fusionscript clients wedge the scripting service** (only a
  Resolve restart recovers). Daemon probes via short-lived subprocesses
  behind its job lock.
- Silent recordings (screen demos) now ingest as one full-length span
  instead of auto-editor refusing.
- UTF-8 encoding sweep: all read_text/write_text now explicit (ASCII-locale
  subprocesses crashed on em-dashes).
**Deck wiring DONE (2026-07-13, proven by Ryan's fingers)** — Companion
BLESSED + v5.0.0 installed; Stream Deck XL runs the studio page via the
Elgato Companion plugin (coexists with his OBS rig). Full doctrine incl.
Companion-v5 config-by-database in docs/DECK.md. Two full REC→STOP+INGEST
cycles from physical keys produced verified timelines; a third exposed the
Deepgram-network crash (now degrades to silence-only ingest). Daemon runs
manually (launchd later); control page at 127.0.0.1:8873 as backup surface.

## Delivery fan-out ✅ (2026-07-13)

`tools/deliver.py <ws>` (+ daemon verb `deliver`): ONE Resolve master render
→ ffmpeg derivations (vertical 1080x1920 center-crop — reframing is a human
pass; podcast m4a loudnormed to -16 LUFS) → every output probe+loudness
verified + registry-recorded. Proven on loop-demo (voice+music+meme+graphic):
master/vertical/podcast all green, vertical eyeballed.

## Bongpot adapter ✅ (2026-07-13)

`tools/ingest-bongpot.py <call-dir> [--partial]` (+ `studio/bongpot.py`,
tests/test_bongpot.py 16/16): bongpot video-plan.json → Resolve finishing
timeline, ONE-WAY. Facts verified against
`~/projects/bongpot/outputs/clown-motel`: cut.shots are contiguous
[start,end) SECONDS; Wan clips (`<shotId>.mp4`, 832x480@16fps) run SHORT of
their windows → conformed per bongpot's own assembler recipe (scale/crop
1920x1080, fps 30, last-frame clone-pad, cut at exact frame count, audio
stripped) into `<ws>/media/`, cached by mtime. The frame grid rounds
BOUNDARIES once — never per-shot durations — so rounding cannot drift off
the call audio. The untouched call mp3 (auto-discovered from ear.json
meta.audio; the spaced LPC-collection path → resolve_safe hardlink) spans
the whole window as ONE A1 item. Shot ids/speakers/verdicts = colored
markers (Red missing/reject, Yellow rework, Green approved, Sky
unreviewed). Fails closed on missing clips unless `--partial`. Proven:
clown-motel 27/47 clips → `clown-motel-finish@2c1c4bae`, ground-truthed in
Resolve (27 V1 items, 1 A1 item, 8877 frames exactly, 47 markers). Nothing
writes into bongpot; its FFmpeg lane stays production.

## Next

1. Phase 7 Scene Forge — planning dialogue FIRST
   ([RYAN gate: provider mix + budget]).
2. Packages 2–4: **podcast-clips v1 AUTHORED + previewed (autonomous loop,
   2026-07-12)** — outputs/previews/ms-pc-{caption,speaker,episode}-preview.mp4
   awaiting Ryan's verdicts. Documentary + broadcast-retro next, same rails.
2. ~~OGraf investigation~~ DONE 2026-07-12 (report in
   docs/MOTION-GRAPHICS.md): NATIVE in Resolve as CEF-rendered Titles,
   manifest-defined duration, deterministic goToTime — the hyperframes
   bridge confirmed + kinetic typography's natural substrate.
   Smoke 2026-07-13 CONCLUDED (Ryan's screenshot confirmed): OGraf loads
   fine — Effects→Titles→OGraf→Breaking-News IS in the GUI — but
   InsertFusionTitleIntoTimeline cannot reach OGraf entries (Fusion
   titles only) in 21.0.2. Verdict: GUI-usable today, script-unreachable;
   revisit when BMD extends the API. Fusion .setting stays the scripted
   graphics substrate. (Side note: a probe script segfaulted on
   interpreter exit after failed inserts — API teardown flake, Resolve
   unharmed.)
3. ~~MCP server install~~ DONE 2026-07-13: gursky davinci-resolve-mcp
   v2.60.0 installed (own venv in vendor/), verified connected to Studio
   21.0.2.4; config at repo-root `.mcp.json` (project-scoped) — tools load
   in the NEXT Claude Code session opened in this repo. Posture per plan
   rec: MCP for exploration/conversational control; our deterministic
   verbs stay the pipeline.
4. Ryan gates still open: project name, deck middleware, MCP posture.
