# AGENTS.md — operating manual (harness-neutral)

This file is the single source of truth for HOW to operate this project.
It is written for ANY agent harness (Claude Code, Codex CLI, Gemini CLI,
Cursor, ...): if you can run shell commands and edit files, you can run this
studio. Ryan-specific collaboration rules live in CLAUDE.md; architecture in
ARCHITECTURE.md; verified research in RESEARCH.md; live state in STATUS.md
and docs/PLAN.md.

## What this is

The agentic instrument layer between Ryan and DaVinci Resolve Studio.
**Copilot, not autopilot**: Ryan makes his videos (OBS + Stream Deck screen
recordings, iPhone footage, found media, his script); the agent is the
in-loop co-editor — scene by scene, conversationally. NO one-shot
brief→finished-video generation, ever.

## Installed toolchain (owned + licensed — check here before proposing tools)

Software Ryan already owns. **An agent must check this list before proposing
any third-party app, DIY script, or OS-level workaround.** Suggesting BlackHole,
a macOS Multi-Output Device, or a bespoke ffmpeg routing hack when a licensed
app on this list already does the job is a bug.

- **DaVinci Resolve Studio** (licensed) — the NLE. External scripting = Local.
- **OBS Studio** — capture. Hybrid MP4 → `/Users/SSDrive/Movies`.
- **Blender 5.2 LTS** + **Molecular Nodes** — headless deterministic camera
  work and structural-biology visuals (`blender/`). The add-on is enabled by
  `--addons` in `studio/blender.py`, NOT by dropping `--factory-startup`:
  renders stay a pure function of the scene script and the enabled set is
  versioned rather than inherited from someone's UI preferences.
- **Elgato Stream Deck** + `~/projects/obs-control-room` (Ryan's own OBS plugin).
- **The complete Rogue Amoeba suite** — the audio layer of this studio, all
  apps owned. Not an optional extra; audio capture, routing, and playback
  questions start here:
  | App | Role in this studio |
  |---|---|
  | **Audio Hijack** | capture/route audio from any app or device; agent-scriptable via `.ahcommand` (`open -b com.rogueamoeba.audiohijack X.ahcommand`; requires Settings → Advanced → "Allow execution of external scripts"). Has a **Transcribe** block (out of beta as of AH 4.5) — a local alternative to the Deepgram leg |
  | **Loopback** | virtual audio devices; aggregate app audio + hardware inputs into one device. **The correct answer to any "route audio into/out of X" question** |
  | **SoundSource** | per-app output routing, volume, EQ, effects (6.1, July 2026) |
  | **Farrago** | soundboard; **first-party Stream Deck plugin** (Settings → Controllers), six action types, works backgrounded — zero glue code |
  | **Fission** | lossless audio trim/split/export — no re-encode |
  | **Airfoil** | audio to network/remote output devices |
  | **Piezo** | simple one-shot recording |

  Deeper verified detail: `RESEARCH.md` §Rogue Amoeba, `research-raw-claims.md`.

Hardware incoming: **Roland SP-404MK2** (ordered 2026-08-02) — sampler /
music-production lane; see docs/PLAN.md music-video worked example.

## The working loop (all decisions blessed 2026-07-12)

1. Ryan records in OBS (Hybrid MP4 → `/Users/SSDrive/Movies`; recordings STAY
   there — never move/clean that folder casually, timelines link to it).
2. Ingest: one command → silence-stripped, transcript-anchored timeline in
   the open Resolve, workspace at `outputs/projects/<name>/`.
3. Assembly dialogue: Ryan directs ("insert this meme where I say X"); agent
   finds the moment via word-level transcript timestamps, mutates the
   workspace's `story.json` (the Story IR — the ONLY source of truth for the
   edit), lints, recompiles to a NEW versioned timeline `{name}@{hash8}`,
   and switches Resolve to it. Ryan scrubs and verdicts live in Resolve.
4. Media intake: Ryan drags a file into the chat (= hands the agent a disk
   path; nothing uploads) → agent files it into `<workspace>/media/` via
   `studio.intake.file_media` and registers it.
5. Ryan's hands-on GUI pass is the FINAL step. After he touches a timeline,
   scripts never modify it again (one-way flow). Machine changes always
   produce a fresh timeline from the IR.
6. House style: memes default to full-frame cutaway, 3.5s, voice under.

## The verbs (CLI — the whole agent interface)

All run as `.venv/bin/python <tool> ...` from the repo root. Nonzero exit =
gate failure. Every path handed to Resolve must be ABSOLUTE (doctrine).

| Verb | Does |
|---|---|
| `tools/ingest-recording.py <file> [--name N] [--margin 0.2s,0.2s] [--no-transcribe] [--no-compile] [--render]` | recording → probe → silence spans → Deepgram transcript → Story IR → compiled timeline, shown in Resolve. Workspace: `outputs/projects/<name>/`. `--margin` is auto-editor's keep-margin around loud sections; `--no-transcribe` skips the PAID Deepgram call |
| `tools/ingest-session.py [<ws-or-story.json>...] --name N [--cuts cuts.json] [--gap-frames 0] [--no-compile] [--render]` | several ingested recordings -> ONE session timeline in the order given. Inputs are workspaces already made by `ingest-recording.py` (silence-stripped, transcript-anchored); this concatenates their IRs onto one spine with a running record offset, a Cyan `SRC n` marker at the head of each recording, and `<ws>/sources.json` mapping asset id -> source workspace/recording/transcript. Refuses mixed fps or resolution (project fps is immutable). `--cuts` is the rough cut: a JSON list of `{source, start, end, note}` in cut order, times in SOURCE seconds as the transcript prints them; each cut keeps only that source's silence-stripped spans inside the window, so the film's edit decisions live in a readable, diffable file (`jobs/<film>/cuts.json`). `--gap-frames` puts black between recordings. Measured 2026-09-07: auto-editor's own multi-input mode dropped the first input from its v3 export, so the concat is IR-level. `edit-ir find` on a session workspace is a bookmarked gap (track 1 has many assets) |
| `tools/ingest-song.py <audio> [--name N] [--fps 30/1] [--size WxH] [--stems f...] [--bpm B] [--first-beat S] [--every 4] [--no-grid] [--no-compile]` | **the song front door** — a song has no speech, so silence detection and diarization mean nothing. Audio spine on A1 untouched, `--stems` onto A2,A3,A4… one per lane, beat grid unless `--no-grid`. `--bpm` skips librosa entirely when the Ableton/SP tempo is known |
| `tools/edit-ir.py <ws> find "phrase" [--hit N]` | locate spoken words → timeline frame + timecode. `--hit` picks which occurrence (default first) |
| `tools/edit-ir.py <ws> insert-image <img> --where "phrase" \| --at M:SS \| --record F [--dur s]` | file image into media/, cutaway edit, lint, recompile, show |
| `tools/edit-ir.py <ws> insert-clip <video> --where\|--at\|--record [--src-in s] [--dur s]` | found-b-roll video cutaway on the overlay track |
| `tools/edit-ir.py <ws> insert-graphic <template> --where\|--at\|--record [--dur s] [--input K=V ...]` | APPROVED library template instance (forged alpha master, placed exactly) |
| `tools/edit-ir.py <ws> add-music <audio> [--where\|--at\|--record] [--src-in s] [--dur s] [--track N]` | music/sfx bed on its own audio lane (default A2); voice on A1 is sacred |
| `tools/edit-ir.py <ws> add-stems <audio>... [--first-track N] [--record F] [--dur s]` | N stems onto CONSECUTIVE lanes A2,A3,A4… one per lane — so a single element can be ducked under narration instead of the whole bed, and beat-grid can analyse the drum stem alone. Refuses to write over A1 |
| `tools/edit-ir.py <ws> retime <edit-id> [--record F] [--dur s]` | move/stretch an edit, recompile |
| *(any `edit-ir.py` mutation)* `[--no-compile]` | mutate + lint only, skip Resolve. The fast path when batching several edits before one recompile |
| `tools/edit-ir.py <ws> remove <edit-id>` / `remove-graphic <id>` | remove edit/graphic (+ orphaned asset), recompile |
| `tools/compile-ir.py <ir.json> [--render] [--show]` | lint → compile → verify (structure; `--render` closes the loop to pixels) |
| `tools/preview-template.py <name> [--input K=V] [--bg footage] [--open]` | render a template preview over real footage — the library approval gate (Ryan's eyes). `--bg` is the clip composited under the graphic |
| `tools/make-captions.py <ws> [--native]` | transcript → SRT remapped to the cut timeline; `--native` = Resolve AI subtitles |
| `tools/ingest-screensage.py <bundle> [--name N] [--no-transcribe] [--render]` | ScreenSage bundle → multitrack timeline (voice by loudness, VFR→CFR, camera cut-in asset, click/zoom markers) |
| `tools/render-ir.py <ws> [--on mini] [--out PATH] [--no-open]` | render a workspace's Story IR with ffmpeg alone — track-1 edits as trims + concat — without Resolve open. `--on mini` offloads to the Mac mini: stages keyframe-padded stream copies of only the windows the cut uses (`-copyts`, so seeks land on the same frames), pipes each one over ssh straight into ffmpeg at nice 10 so nothing staged lands on the mini's disk, refuses when the mini lacks room for the encoded runs, concats there, pulls the mp4 back and removes `~/render/<name>/`. The MacBook must stay awake to feed the pipe. Output probed for duration and loudness against the IR, then opened. Resolve's own Remote Rendering was measured out: it needs Studio on both machines and identical media paths, and the mini (8 GB, 7 GB disk free) has no Resolve |
| `tools/deliver.py <ws> [--presets vertical,podcast-audio] [--open]` | fan-out: ONE Resolve master render → ffmpeg-derived platform formats, all probe+loudness verified, in <ws>/delivery/. `--open` reveals the folder when done |
| `tools/ingest-bongpot.py <call-dir> [--partial] [--clips D] [--audio MP3] [--name N] [--fps 30] [--size WxH] [--no-compile] [--render]` | bongpot video-plan → finishing timeline: shots conformed to V1 (scale/crop/fps/last-frame-pad to the exact window), untouched call audio on A1, shot ids/speakers/verdicts as colored markers (Red=missing/reject, Yellow=rework, Green=approved, Sky=unreviewed). ONE-WAY read of the bongpot repo; fails closed on missing clips unless `--partial` |
| `tools/forge-stills.py <ws> "<prompt>" [--n 8] [--model qwen-fast\|flux-2] [--ref img] [--size 1920x1080] [--no-open] [--pick 2,7,11] [--batch NAME] [--approve]` | genAI stills batch → `<ws>/forge/batch-NN/` + numbered contact sheet opened in Preview; Ryan answers with winner numbers (`--pick 2,7,11`). **SPEND GATE: never pass `--approve` without Ryan approving that batch's printed cost in conversation** |
| `tools/forge-motion.py <ws> <still> "<motion prompt>" [--model wan-480p\|wan-720p] [--no-open] [--approve]` | animate a curated still (I2V) → `<ws>/forge/motion/<still>-mNN.mp4` + provenance sidecar, probed + opened. Same SPEND GATE as forge-stills ($0.45/clip 480p, $1.25 720p). Motion prompt = Ryan's per-moment direction (prompt-brain doctrine) |
| `tools/forge-blender.py <ws> <scene\|name> [--frames 48] [--fps 24] [--size 960x540] [--no-open]` | deterministic camera work: headless Blender renders a scene script — a bare name resolves in repo `blender/`, or pass a path (e.g. `jobs/caffeine/scenes/tetramer.py`) → PNG seq → ffmpeg mux → `<ws>/forge/blender/`. FREE/local, no spend gate. Blender 5 has no video export — scenes emit PNG sequences |
| `tools/beat-grid.py <ws> <audio> [--every 4] [--offset-frames 0] [--bpm B] [--first-beat S] [--no-compile]` | music → librosa beat analysis → ALL beats in `<ws>/beats.json` (candidate cut grid) + Purple marker every Nth beat, recompiled + shown. Which cut lands on which beat stays Ryan's call. **`--bpm` is a KNOWN tempo and skips librosa entirely** — measured, librosa returns 117.45 on a synthesised perfect 120 BPM click and finds 22 of 24 beats; `--first-beat` is where beat 1 lands in seconds |
| `tools/als-trigger-map.py <project.als> [-o out.json] [--include-session] [--no-hash] [--summary]` | pipeline G2 — Ableton `.als` (gzip XML) → one entry per sample FIRING (`sample_hash`, `track_start_secs`, `duration_secs`), so the video a sample was cut from can land in sync. Arrangement clips only unless `--include-session`; `sample_hash` joins to blessdog's `phase8_sp404` ledger. Free/local, no hardware |
| `tools/ingest-osmo.py <clip.MP4>... --name N [--no-compile] [--force]` | **the Osmo Action 5 Pro front door** (spec `docs/CINEMATIC-PIPELINE.md` §3-4): originals copied read-only into `outputs/projects/<date>-<name>/media/`, each ffprobed and ASSERTED (hevc, 10-bit, 3840×2160, 24 or 23.976); a failing clip is FLAGGED in `manifest.json` and kept out of the timeline, never imported silently; passing clips become one full-length edit each on V1 of a Story IR, compiled through the normal IR → OTIO → Resolve path, project stamped DaVinci YRGB + Rec.709 / Gamma 2.4 and read back. Exit 2 = BLOCKED on a 23.976 file (lint refuses 1001-denominator rates, VERIFY 12). `--force` imports flagged clips anyway (status `forced`, reasons kept) for testing the lane on non-Osmo footage such as iPhone Apple Log ProRes. Writes `report.md`. Applies no grade |
| `tools/apply-grade.py <ws> --drx <look.drx> [--timeline-drx <tl.drx>] [--mode 0] [--suffix NAME]` | apply Ryan's base grade to every V1 clip of a DUPLICATE of the workspace timeline (`<name>+grade-<sha8>`), never the one he may have touched; success is read back per clip via `GetNumNodes`/`GetLUT`, not the call's boolean; refuses if the duplicate name exists. `--timeline-drx` does the same on the timeline node. Writes `grade-report.md`. Never says "graded": the per-shot pass is human |
| `tools/render-preset.py <name> [--size 3840x2160] [--format mp4] [--codec auto] [--bitrate-kbps 80000] [--color-space-tag Rec.709] [--gamma-tag "Gamma 2.4"]` | save or update a named Resolve render preset from the CLI (spec §8): `--size` (default 3840×2160; 1920x1080 for iPhone tests), H.265 Main10 picked from `GetRenderCodecs` when `--codec auto`, bit-rate limit, colour/gamma tags; frame rate follows the timeline. `--gamma-tag` is the one knob the §8 upload test flips. Needs Resolve open with any project current |
| `tools/deliver.py <ws> [--timeline NAME] [--resolve-preset NAME]` | (flags on the verb below) `--resolve-preset` renders the master through a named Resolve preset instead of the v0 H264 default; `--timeline` renders a named, human-finished timeline in the workspace's project (the apply-grade duplicate after the per-shot pass) as-is, skipping the IR structure verify; combine with `--presets ""` to skip the ffmpeg derivatives |
| `tools/grade-library.py fetch\|install\|verify\|validate [--manifest PATH] [--record] [--lut-root DIR]` | the Grade Library's third-party assets, from `grades/film-look/manifest.json` (SSOT: URL, upstream commit/date, sha256, license). `fetch` downloads into `grades/film-look/assets/` and refuses a hash mismatch; `--record` pins an unpinned asset's hash and zip contents. `install` copies/unzips into Resolve's LUT folder `film-look/` (`--lut-root` overrides the folder). `verify` re-hashes repo AND installed copies and lists human-only downloads still missing. `validate` needs Resolve open and asks it to compile every installed DCTL. Free, already-tuned assets only, nothing hand-rolled; the node recipe is `grades/film-look/README.md` |
| `python -m studio.registry [table]` | inspect the cross-session registry (assets/transcripts/irs/renders/decisions) |
| `python -m studio.daemon` | studio daemon on 127.0.0.1:8873 — GET /status /verbs /jobs; POST /verb/<name> (record-start, stop-and-ingest, ingest-last, ingest-screensage, compile, restart-resolve). Long verbs = background jobs, logs in outputs/daemon/ |
| `scripts/restart_resolve.py` | ONLY sanctioned way to restart Resolve (graceful save→quit→wait; pkill crashes it) |

Python modules under `studio/` back these verbs; tests under `tests/` are
plain scripts (`test_compile.py`, `test_registry.py`, `test_assembly.py`).

## Jobs vs. the studio (added 2026-09-02)

**This repo is the studio, not the films.** A capability that any future video
could use belongs to the studio; everything specific to one film belongs to that
film's job folder. Ryan, on finding the caffeine work scattered across the repo
root: *"it should have its own subfolder, don't you think?"*

    jobs/<job>/          TRACKED. One film. README.md is its brief — what it is,
                         the narration, the shot list, what works and what does
                         not. Plus its own scenes/, source assets, evidence/,
                         and any spec module only it needs.
    outputs/projects/<n>/ GITIGNORED. Render workspace: story.json, media/,
                         forge/ intermediates. Bulk pixels, regenerable.

The split test is **"would a second film want this?"** For the molecular lane it
put `blender/lib_membrane.py` (membrane orientation, interface faces, Kabsch
superposition — no molecule knows its name) and `blender/prep-opm.py` /
`blender/prep-alphafold.py` in the studio, while the A2A/D2/AC5 helix tables,
the arrangement and the scaffolds to hide went to `jobs/caffeine/complex.py`.

Why it matters beyond tidiness: before the split, `blender/tetramer.py` sat
beside `blender/orbit-cube.py`, a generic fixture. A second molecular video had
nowhere to go and would have copied half a library to get started.

**Never blanket-gitignore `jobs/`.** Text, scripts, JSON, source structures and
curated evidence are tracked by default; only bulk pixel intermediates are
ignored, and those live in `outputs/`.

## Hard doctrine (violations fail silently — learned the hard way)

- **Absolute paths to every Resolve API call.** Relative fails silently.
- **A modal dialog open in Resolve silently breaks scripting.** Cost a long
  investigation 2026-08-02. With the Preferences window open,
  `ImportTimelineFromFile` returns failure and Resolve logs only
  `Import Log (Info) - Operation canceled.` Results become erratic and
  path-dependent in ways that look like a real filesystem bug — the same file
  passes, then fails, minutes apart. **Before trusting ANY scripting result,
  check `app.GetCurrentPage()`: it returns a page name ("edit", "color", …)
  when Resolve is usable and `None` when a modal has the UI.** Treat `None` as
  "all measurements from this session are void", not as a minor detail.
  With no dialog open: `tests/test_compile.py` 7/7 and the full song lane
  compiles. Nothing was wrong with the code.
- **Resolve needs Full Disk Access, and the settings pane cannot tell you
  whether it has it.** It was genuinely denied on this machine (`auth_value=0`)
  and had to be granted. An app is LISTED under Privacy & Security merely for
  having *requested* a permission, and the row looks identical either way.
  Verify from the database, never the GUI:
  ```
  sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
    "select service,client,auth_value from access where client like '%esolve%';"
  ```
  `auth_value`: 0 = denied, 1 = prompt, **2 = allowed**. Granting it did NOT by
  itself fix the import failures above — the modal dialog did.
- **[U] Unresolved residue:** with no dialog open, an interchange file in
  `/private/tmp` referencing media under `/Users` still fails, while the same
  media with the `.otio` beside it in the workspace succeeds. No tool produces
  that split (compile writes `<ws>/story.otio` next to `<ws>/media/`), so it
  blocks nothing. Do not build a workaround for it without re-measuring first.
- **NO SPACES in media paths handed to OTIO import** — Resolve fails/HANGS on
  percent-encoded URLs (confirmed 2026-07-13). `studio.intake.resolve_safe()`
  hardlinks a safe name; lint refuses spaced paths on used assets; OBS
  filename format switched to space-free (websocket-settable).
- **One fusionscript client at a time.** A long-lived in-process connection
  concurrent with other clients wedges the scripting service (restart is the
  only cure). The daemon probes Resolve via short-lived subprocesses behind
  its job lock; scripts must not linger.
- **Lint before Resolve, verify artifacts after** — never trust API return
  values or your own reasoning; ffprobe and timeline inspection are truth.
- Project fps is immutable once a timeline exists → project-per-IR, fps
  stamped before the first timeline (compile.py owns this).
- Never `pkill` Resolve. First `AddRenderJob` may silently no-op → retry.
- Resolve's API is append-only: mid-timeline edits are impossible; the IR +
  full recompile IS the edit mechanism.
- Deepgram for transcription, never Whisper. Templates/grades: agents apply,
  Ryan authors.
- **Audio spine (epoch 2)**: track-1 video edits mirror their audio onto A1;
  video cutaways (V2+) are silent by design; audio assets get audio lanes
  (A2+ music). Renders are loudness-checked when the IR implies sound —
  every timeline before 2026-07-13 was silently MUTE; the verifier now has
  ears. `ir.py COMPILER_EPOCH` must be bumped whenever identical IR would
  compile differently.
- Requirements pinned in `requirements.txt`; venv at `.venv/`. Deepgram key
  in `.env` (never commit).

## Version control — a local commit is not a backup

| Repo | Remote | Owns |
|---|---|---|
| `media-studio` (this one) | `git@github.com:blessdog/media-studio.git` — **private**, default branch `master` | video: capture → ingest → Story IR → Resolve → delivery |
| `~/projects/blessdog` | `git@github.com:blessdog/blessdog.git` | music: Ableton control + `phase8_sp404` SP-404MK2 sample lane |

- **Committing is not finishing. Push.** This repo existed for weeks with no
  remote at all — every commit was one disk failure from gone. When a commit is
  made, push it; never end a session with a branch ahead of `origin`. Verify by
  reading the remote (`git log origin/<branch>`), not the local ref.
- **Check the pushed tree for secrets, not the working directory.**
  `git ls-tree -r --name-only origin/<branch> | grep -iE '\.env|registry\.db'`
  is the check that matters. `.gitignore` covers `.env`, `registry.db*`,
  `outputs/`, `vendor/`, `.venv/` — confirm, don't assume.
- **Cross-repo work means two pushes.** The music lanes live in `blessdog`
  (MUSIC-LANE.md decision 1: the boundary is the WAV file). Work that spans
  both is not shipped until both remotes have it.
- **The repos never import each other.** They join by **content hash** —
  `phase8_sp404`'s `LedgerEntry.source_clip_hash` references an asset in this
  repo's `registry.db`. Keep it that way; a code dependency between them would
  collapse the boundary.
- media-studio is **private** — it carries absolute paths, machine layout and
  business context. Do not make it public without Ryan saying so.

## Which document wins (truth hierarchy)

This repo holds design proposals, chronological logs, and current code. They do
not describe the same moment. When two disagree, use this precedence — do NOT
average conflicting claims:

1. **Observed behaviour, artifacts, code, and tests** — what the software does.
2. **AGENTS.md** — operating doctrine and safety rules.
3. **STATUS.md** — current state and pickup point. Capped at 150 lines.
4. **docs/ENGINEERING-AUDIT-2026-08-03.md** — architecture + risk synthesis,
   frozen at commit `fbeaf06`. A dated snapshot, not a live document.
5. **docs/PLAN.md** — phase map and decision history.
6. **docs/JOURNAL.md** — dated history. Archive; never read in full.
7. **ARCHITECTURE.md** — a 2026-07-11 *proposal*, not the implementation map.
8. **RESEARCH.md** and the Lane B reports — research inputs, not runtime truth.
   Preserve their `[V]/[R]/[U]` confidence labels.

When code and a document disagree: verify the behaviour, fix whichever is
wrong, and record the correction.

## Concurrent sessions — use a worktree, never share `master`

Two agents editing one checkout is the failure this project keeps hitting. Code
conflicts announce themselves; **documentation conflicts do not** — both
sessions write plausible prose and the file quietly disagrees with itself
(STATUS.md said pipeline G2 was both done and to-do, 776 lines apart).

```
make worktree NAME=music        # ../media-studio-music on branch lane/music
cd ../media-studio-music        # open the second Claude session HERE
make hooks                      # the gate is per-checkout
...
git push -u origin lane/music   # merge to master when the lane is done
make worktree-list / worktree-rm NAME=music
```

One session per checkout, one branch per lane. `git worktree` shares the object
store, so this costs disk for the working files only — not a second clone.

## Cold-start test (portability gate)

A fresh agent with zero conversation history must be able to run the whole
loop from this file alone: Resolve open (external scripting = Local), then
`ingest-recording.py` a clip, `edit-ir.py find/insert-image`, verify green.
If any step needs knowledge not written here or in docs/, that's a bug —
fix the docs.
