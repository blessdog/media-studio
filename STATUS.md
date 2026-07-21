# STATUS — where media-studio stands

*Updated 2026-07-20. If this file and the code disagree, the code wins — then
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

## Scene Forge slice 1 ✅ — stills engine (2026-07-13)

Phase-7 round-1 dialogue BLESSED (Ryan): build ALL slices in succession
(1 stills → 2 I2V animate → 3 reference-identity → 4 Blender/beat-grid);
**hosted APIs only** (Replicate; GPU lane can join later without rework);
**per-batch cost approval** — `tools/forge-stills.py` prints the estimate
and exits 2 unless `--approve`, which an agent may pass ONLY after Ryan's
go in chat; **curation = contact sheet** (numbered grid jpg, opened in
Preview, winners named in chat, recorded via `--pick`).

`studio/forge.py` + `tools/forge-stills.py` (tests/test_forge.py 13/13):
model SSOT cribbed from bongpot's proven config (qwen-image-fast
$0.0017/img exploration; flux-2-dev $0.04/img, native `input_images`
identity conditioning — slice 3 rides that). Replicate facts: community
models 404 on the model-path predictions endpoint — POST /predictions with
the version id (fetched+cached from the model record); 202 Accepted is a
valid creation status. Batches → `<ws>/forge/batch-NN/` with manifest.json
(prompt/model/cost/picks provenance) + registry rows. Live-proven: 8-still
batch on Ryan's studio aesthetic, $0.01, sheet verified by eye (both of us).

## Scene Forge slice 2 ✅ LIVE-PROVEN (2026-07-13, later)

Full loop closed on real material: Ryan picked still #08 + gave the motion
direction → `forge-motion.py` clip (hailuo-2.3-fast, 1378x768@24fps, 5.9s,
$0.48 ceiling approved) → `insert-clip` cutaway at frame 240 of his real
morning recording → compiled `2026-07-13-09-43-20@1d525f2c`, ground-truthed
(V2 item start=240 dur=210 exactly). **Mixed-fps SETTLED: Resolve conforms
24fps media by time through our OTIO path — no conform step needed.**
Hard-won same hour:
- **wan family on Replicate is DEAD upstream** (wavespeedai wan-2.1 AND
  wan-video wan-2.5 both fail E002 on every run, data-URI and file-URL
  alike; flux-schnell official ran fine → account healthy). Default is now
  minimax/hailuo-2.3-fast (768p 6s). Do not re-add wan without a live retest.
- Replicate rejects **data URIs >~256KB** (that E002 red herring cost a
  round) — `_image_input()` uploads >200KB stills via the files API.
- Video pricing is unpublished across providers → estimates are CEILINGS,
  flagged `estimated`, Ryan approves the ceiling; correct the table from
  real bills.
- **CONFESSION: every edit-ir mutation had been broken since the UTF-8
  sweep** (`encoding=` kwarg inside json.dumps instead of write_text —
  TypeError on write). The sweep was never re-exercised through the CLI.
  Fixed + proven by this insert. Lesson: a "mechanical" sweep still needs
  one end-to-end run per touched tool.
- PROMPT BRAIN doctrine (Ryan): prompts are the creative authorship layer —
  its own deferred planning area (docs/PLAN.md); agent prompts = fixture
  material. Also: one-prompt-x-N batches give seed-level variety only —
  same-y sheets; real batches want per-image prompt variation (backlog).

## Scene Forge slice 2 — I2V engine built, awaiting first live clip (2026-07-13)

`tools/forge-motion.py <ws> <still> "<motion prompt>"` + forge.animate():
same spend gate as stills. Model SSOT holds ONLY verifiably-priced models
(replicate.com/pricing 2026-07-13): wavespeedai/wan-2.1-i2v-480p $0.09/s
and -720p $0.25/s, fixed ~5s output (no duration input) → deterministic
$0.45 / $1.25 per clip. Kling/Seedance/Veo/Hailuo prices don't render
anywhere fetchable — parked until verifiable (or measured empirically).
wan-2.1 takes `lora_weights` — on-ramp for the identity slice. PROMPT
BRAIN doctrine (Ryan, 2026-07-13, docs/PLAN.md): the prompt is the
creative authorship layer — agent-written prompts are fixture material;
real generation takes Ryan's per-moment direction. CAVEAT: inserting a
16fps/480p forge clip via insert-clip is UNVERIFIED against the OTIO
path (Resolve should conform by time) — first live clip proves or
disproves; conform step gets added if needed.

## Regrounding (Ryan, 2026-07-13, after slice 2)

Course correction: I proposed filling clown-motel's missing s27 as a forge
test — WRONG. That lane is abandoned slop (Ryan stopped it deliberately);
resurrecting it as a test fixture would import bad architecture at the
foundation. Bongpot integration hard-stops at the adapter; the real
integration is its own future project (docs/PLAN.md "Bongpot posture").
Directive: stay regrounded in THIS project's own foundation — finish the
remaining phase-map items with content-agnostic mechanics and fixture
material only.

## Scene Forge slices 3 + 4 ✅ (2026-07-13, after regrounding)

**Slice 3 identity — LIVE-PROVEN ($0.16, Ryan-approved):** neutral fixture
character (wooden marionette, chipped blue hat, red scarf — deliberately
NOT his studio, NOT LPC). flux-2 `input_images` conditioning held identity
across marketplace/rowboat/snowy-street scenes — hat chips, scarf, wood
grain, even the strings persisted. Composite proof:
outputs/projects/forge-demo/forge/identity-sheet.jpg. This is the
recurring-character mechanics; WHAT any character is = Prompt Brain, his.

**Slice 4a Blender lane:** `studio/blender.py` + repo `blender/` scene
scripts + `tools/forge-blender.py`. Blender 5.1.2 facts: `Action.fcurves`
GONE (layered actions — set
`preferences.edit.keyframe_new_interpolation_type` BEFORE keying);
**built-in video export REMOVED** (image_settings enum is stills-only) →
scenes render PNG sequences, harness muxes with ffmpeg. Fixture
`orbit-cube` (Track-To constraint = the reusable aim idiom) renders 48f
headless in seconds, probe-exact 2.00s.

**Slice 4b beat grid:** `studio/beatgrid.py` + `tools/beat-grid.py`:
librosa beats → ALL frames in beats.json + every-Nth Purple markers →
recompile. Oracle-tested on a synthesized 120 BPM click (±2 frames);
live-run on loop-demo (its 5s ambient bed = 1 beat — real-music
validation awaits Ryan's track). Quantize-to-grid edit verbs come when a
real music video wants them.

## Course correction closing the session (Ryan, 2026-07-13)

Creation and editing are SEPARATE CONCERNS — the instant record→edit loop
was testing only. Next session (fresh start): the Stream Deck becomes a
full production dashboard (scene cuts, takes, live key feedback — REC
silently no-oped against a crashed OBS today, unacceptable) and material
accumulates as a CORPUS; ingest is deliberate/batch; editing is its own
later activity. Full agenda at docs/PLAN.md "NEXT SESSION AGENDA". Also
today: OBS crashed once mid-session (relaunched clean); the 1.9s
accidental take lives at outputs/projects/2026-07-13-14-37-50.

## Scope reel-in + state-of-instrument demo (2026-07-20)

**Ryan's decision: the studio focuses on THREE instruments — OBS, DaVinci
Resolve, and Blender — with the Stream Deck as the tactile layer over all
three.** Hosted-diffusion Scene Forge and other lanes are parked, not
deleted. (PLAN.md alignment pass pending the next planning dialogue.)

**Demo on real material** (his 2:38 un-ingested 07-13 recording →
`outputs/projects/state-demo/`, judgment pending his eyes): fresh ingest
(27 spans, 10 utterances) → three approved news-desk graphics placed by
spoken phrase → headless Blender orbit-cube cutaway at "Let's bless it" →
15s music bed on A2 → captions 10/10 cues remapped →
`state-demo@ea1f0c5a` rendered, all gates green. Hard-won en route:

- **A 24fps Blender mux misconforms on a 60fps timeline via OTIO**: landed
  rec=286 dur=144, wanted rec=250 dur=180 — the END frame matched exactly,
  so the conform shortened and right-shifted it. The 24fps hailuo clip had
  conformed fine on a 60fps timeline (slice 2), so the blender ffmpeg mux
  is the suspect (timebase?), not mixed-fps generally. Workaround proven:
  render Blender scenes at timeline fps (`--fps 60`). Root cause unowned.
- **Verifier false-fail: container duration includes AAC encoder padding**
  (~70ms past the video stream — 2390 AAC frames × 1024 / 48000). The
  video stream was frame-exact (3055) all along. verify.py now checks the
  VIDEO stream duration, the actual frame contract.
- Gates that held: add-music without --dur lint-failed correctly (15s bed
  can't span a 51s cut — story.json never written); the alpha-master
  150-frame cap (2.5s) bit all three graphics (headline wanted 4s, ticker
  5s — the ticker cuts mid-scroll). That v0 limit is now visible in real
  use → backlog candidate.

## Deck/corpus planning session (2026-07-20) — scope blessed, then ECOSYSTEM PIVOT

Planning dialogue held (per the 7/13 agenda). **Blessed by Ryan:** STOP splits
from ingest; corpus = automatic FREE indexing (ffprobe metadata → registry
rows) of every new recording in ~/Movies, with expensive processing (Deepgram
transcribe + compile) LAZY at edit time; one MARK key (daemon verb records
recording-file + offset-seconds → becomes timeline markers at processing
time); honest OBS state on keys; a dead REC key launches OBS instead of
silently no-oping.

**PIVOT (Ryan, hard correction, same session):** the bespoke Companion
text-tile approach is REJECTED — flat labeled rectangles are not a deck
design; the keys are mini LCD screens. Deck layer goes **Elgato-native
first**: official plugins (OBS), Marketplace profiles + icon packs, real key
artwork; Companion/bespoke survives ONLY where the ecosystem can't reach
(studio-daemon verbs like MARK/ingest) and must still look native. This is
the same adopt-don't-hand-roll doctrine as the MCP-server decision —
applied late to the deck, at Ryan's cost. Communication corrections from
the same session live in harness memory (precise app naming, full-paragraph
planning, questions must carry stakes).

Three web-research briefs dispatched (official OBS plugin + live key state;
Resolve deck plugins + what editors actually use; icon/artwork practice +
shell-command bridges + Elgato SDK ceiling). **Findings land in
docs/DECK-ECOSYSTEM.md — REPORT BEFORE BUILD; nothing gets wired until Ryan
reads it.**

## Deck reel-in + discovery (2026-07-21)

**Ryan's directive:** the deck does ONE thing well — OBS Studio. Resolve
profiles, daemon-verb keys, multi-surface dashboard: all dropped. Build,
don't buy: take the official OBS plugin as reference and build our own
sophistication for his workflow.

**Recon findings (verified on disk):**
- Official Elgato OBS plugin v3 is installed BUT its files are an
  encrypted `ELGATO\x01` container — not readable, and we do NOT attempt
  to crack it (DRM circumvention; also unnecessary: its full action
  surface is publicly documented and its transport — obs-websocket — is
  an open protocol this project already speaks).
- **DISCOVERY: `~/projects/obs-control-room/` is the real foundation.**
  Ryan's own custom Stream Deck SDK plugin
  (`com.blessdog.obs-control-room`, TypeScript/Node 24, built Jul 5,
  live through Jul 13 — logs prove OBS connect/launch cycles). Already
  does: per-scene keys WITH on-air highlight (6 of his 7 scenes; Cam
  Cutout missing), Status key (OFFLINE/READY/REC/LIVE + elapsed +
  dropped-frame %, press-when-dead = cold start), Show Flow state
  machine (countdown → live → hold-to-end), Screen Picker, Meeting Mode
  (virtual cam), scripted scene-collection builder, cold-start
  infrastructure, and documented OBS 32.1.x gotchas (GetSourceScreenshot
  broken, display-enum hang, NodeJS-dir install gotcha). Known bug in
  log: `show-flow: end-show failed` (2026-07-13 01:46).
- media-studio docs never referenced this project (parallel deck efforts,
  mutually blind — the Companion page rebuilt a worse subset of it).
  Elgato app 7.4.2, OBS 32.1.2, plugin loads on XL + SD+ + Mobile.

**Proposed build (bless gate — [RYAN]):** revive & extend
obs-control-room as THE deck surface: add Cam Cutout scene key; add
record start/stop for corpus creation (Status key already shows REC
truthfully); add MARK as an OBS chapter-marker action (FIRST verify
CreateRecordChapter exists on OBS 32.1.2's websocket and chapters
survive Hybrid MP4 → ffprobe); fix the end-show bug; retire the
Companion MEDIA STUDIO page. Corpus lane (auto-index + lazy processing)
unchanged, lands in the daemon as blessed.

**Vision addendum (Ryan, 2026-07-21, revival plan BLESSED):** the deck is
a launcher-based operating surface. A HOME profile with app tiles (OBS
now; Ableton + soundboard + future apps later); a house-GLYPH key on the
same corner of every surface (proposed: bottom-right) always returns
home. Mechanics: Stream Deck profiles + built-in Switch Profile action
(+ optionally Smart Profiles for focus-follow). Key grammar is
ICON-FIRST — media-transport glyphs, pictures, per-app color families,
animation where meaningful (144×144 PNG/GIF/WEBP); text only when
appropriate. Emoji-rendered PNGs acceptable as v1 art; authored set
after layouts stabilize. The keys are mini screens — use them.

## Next

1. **Deck lane (BLESSED, in progress):** ~~chapter-marker verification~~
   **PASSED 2026-07-21** (`scripts/verify_record_chapters.py`: OBS 32.1.2
   ws 5.7.3, CreateRecordChapter → titled chapters in Hybrid MP4 →
   ffprobe, ~0.2s press latency; OBS auto-adds a 'Start' chapter at 0 —
   ingest must skip it; test clip: ~/Movies/2026-07-21_10-37-22.mp4).
   MARK = plugin chapter action, ZERO pipeline code at record time;
   ingest later reads chapters → Story IR markers. NEXT: build in
   ~/projects/obs-control-room — Cam Cutout key, record start/stop
   action, MARK action, end-show bug, HOME/profile nav shell +
   icon-first art pass → then retire the Companion MEDIA STUDIO page.
2. **Authored lane / Monero visualization** (was missing from this file —
   2026-07-17/18 sessions): Lane B research DONE + verified, read
   docs/LANE-B-REPORT.md first; gate 2 (visual references) is the open
   blocker — Ryan-gated, creative decisions made live; briefs at
   docs/LANE-B-RESEARCH-BRIEFS.md. Scope reel-in 2026-07-20: OBS + Resolve
   + Blender only; other lanes parked.
2. Ryan-gated: Grade Library (author a look first), Prompt Brain dialogue,
   bongpot×studio project, project name, aesthetics passes.
3. Backlog: per-image prompt variation in batches; empirical cost
   correction from Replicate bills; launchd daemon; LAN/auth control
   page; captions --native exercise; quantize-to-beat edit verbs.
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
