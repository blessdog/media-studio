# RESOLVE-21.1-AGENTIC — what Resolve 21.1 gives an agent, and what this studio should do with it

*Research report, 2026-09-09. Report-before-build: nothing here is wired up.
Verification tags: **VERIFIED** = measured on this machine or read from a
primary artefact in the installed app; **REPORTED** = credible secondary source,
cited; **UNVERIFIED** = not confirmed, needs the stated measurement.*

Raw evidence for every VERIFIED line lives in `docs/research-raw/resolve-21.1/`:
the native server's tool dump, the smoke-test script and its transcript, the
scripting changelog, and the Claude extension manifest.

## Ground truth (this machine, today)

- DaVinci Resolve Studio **21.1.0.14** is installed and was running during the
  measurements. **VERIFIED** (`Info.plist`, `resolve.GetVersionString()`).
- External scripting is set to Local: the vendored third-party MCP server
  reports Connected and the native server's `initialize` handshake said
  "Resolve Studio 21.1 is running". **VERIFIED**.
- The app bundle ships a native MCP server binary,
  `DaVinci Resolve.app/Contents/Applications/ResolveMCP` (universal Mach-O,
  430 KB), and a Claude Desktop extension bundle,
  `Contents/Resources/DaVinciResolve.mcpb`. **VERIFIED** (`file`, `ls`).
- The bundle ships its own Python: `Contents/Applications/ResolvePython` is
  Python 3.14.4 and `import DaVinciResolveScript` works with no environment
  variables. **VERIFIED** (ran it).
- The scripting SDK now ships a type stub (`DaVinciResolveScript.pyi`, 116 KB)
  and a `CHANGELOG.md`. Neither existed in earlier releases. **VERIFIED**.
- Claude Desktop is not installed here; no assistant setup has been run, so
  `~/.claude.json` and `~/.codex/config.toml` carry no Resolve entry. **VERIFIED**.

## What shipped (Resolve 21.1, released 2026-09-08)

### The native MCP server

The Studio edition includes a native MCP server. `File > Setup AI Assistants`
writes the server into the config of whichever assistants it finds on the
machine: strings in the Resolve binary name `~/.claude.json` (Claude Code),
`~/.codex/config.toml` under `[mcp_servers.davinci_resolve]` (Codex),
`~/.gemini/config/mcp_config.json`, `~/.grok/config.toml`, and the `.mcpb`
extension for Claude Desktop. **VERIFIED** (strings in the binary) for the
paths; the GUI action itself was not run. **UNVERIFIED** that the written
entry is exactly `command: <path to ResolveMCP>` with no args, though the
`.mcpb` wrapper spawns it that way.

Transport is stdio JSON-RPC, protocol `2024-11-05`. `ResolveMCP --dump-tools`
prints the tool list and the agent instructions without connecting. **VERIFIED**.

**It is 14 tools, not 88.** The press number "88 tools" matches the
third-party `DigitalWorkflowCompany/resolve-mcp` count already in RESEARCH.md
and does not describe the native server. **VERIFIED** against the dump:

| tool | what it does |
|---|---|
| `launch_resolve`, `get_resolve_status` | lifecycle |
| `get_whats_new` | the scripting changelog since a version, so an agent trained before 21.1 can catch up |
| `get_scripting_api`, `search_scripting_api` | the `.pyi` stub, whole or regex-searched |
| `get_scripting_docs` | the README, whole or by section |
| **`run_script`** | run a Python 3.14 script with `resolve` and `project` pre-injected; sandboxed, no `os`/`sys`/filesystem/network/subprocess; set `result` for structured return |
| `run_script_unsafe` | same, with full system access |
| `list_luts`, `list_dctls`, `update_dctl`, `delete_dctl`, `delete_lut`, `generate_lut` | LUT/DCTL authoring into `.../LUT/MCP` |

The design is "code as the tool": instead of one MCP tool per API method, the
agent reads the stub and writes Python. That is the opposite shape from the
vendored `samuelgursky` server (376 granular tools upstream).

Measured live over stdio while the third-party server was also connected
(about ten seconds of overlap): `initialize` OK, `get_resolve_status` returned
`running: true`, `run_script` returned the current page (`media`), project
(`Untitled Project`), timeline count (0) and version; `import os` inside
`run_script` raised `PermissionError: import not allowed`;
`search_scripting_api("GetTranscription")` found the method. **VERIFIED**
(`resolvemcp-smoke-transcript.txt`).

One caveat: `--dump-tools` reported "Resolve is not running" while the process
was up. **VERIFIED**. The `.mcpb` wrapper caches that dump at startup, so its
instructions could lie about state where the live handshake does not.
**Inferred from reading `server/index.js`**, not observed through Claude Desktop.

A second copilot channel, unchecked: 21.1 adds presentation markers with
annotations, replies and status. Whether `GetMarkers()` exposes the annotation
text and replies is not in the stub's marker type as read. **UNVERIFIED**;
check with `search_scripting_api("annotation|reply")` before assuming.

### Scripting changes (from the installed `CHANGELOG.md`)

- Python 2 dropped, and a built-in Python now serves the script menu and
  console. **VERIFIED** (changelog). The free edition lost Python scripting,
  including in-app. **REPORTED** (CineD, Newsshooter); the installed changelog
  does not say it. External scripting was already Studio-only (RESEARCH.md,
  verified July). This studio has Studio, so nothing changes here.
- "Overloaded function signatures are deprecated": the dict-returning forms
  (`GetItemsInTrack`, `GetClips`, `GetRenderJobs`, `GetRenderPresets`,
  `AddItemsToMediaPool`, `GetSubFolders`, `GetFlags`, ...) are deprecated in
  favour of the `*List` forms. `studio/`, `tools/`, `scripts/` and `tests/`
  use none of the deprecated names. **VERIFIED** (grep, zero hits). The
  vendored third-party server was not grepped. **UNVERIFIED** for it.
- Twenty new APIs. The ones that touch this studio's lanes, with stub
  signatures. **VERIFIED** (`.pyi`):

| API | Returns / takes |
|---|---|
| `MediaPoolItem.GetTranscription()` | `{language, segments:[{start, end, text, speaker, words:[{start, end, text}]}]}`, timecodes as strings, `(...)` marks silence |
| `MediaPool.CreateMulticamClip(clips, {angleSyncMode, channelConfig, splitAtGaps, ...})` | multicam clip from media pool items |
| `Timeline.AutoAlignClips(items, {SyncUsing: TIMECODE\|WAVEFORM, UseTrack})` | align items by waveform |
| `TimelineItem.PerformMulticamSmartSwitch({minEditDuration, editChangeDelay, wideAngleID, ...})`, `FlattenMulticam(grade)` | automatic angle switching |
| `TimelineItem.AddTransition({type, category, position, alignment, duration})` | e.g. `'Cross Dissolve'`, `'simple'`, `'start'` |
| `TimelineItem.GetFades()` / `SetFades({FadeIn, FadeOut})` | frames |
| `TimelineItem.GetSpeed()` / `SetSpeed({Percentage, PitchCorrection, RippleTimeline})` | retime |
| `Timeline.NormalizeAudioLevel(items, {normalizationMode, targetLevel, targetLoudness})` | modes from `GetNormalizeAudioModes()` |
| `Project.UpdateRenderPreset(name)`, `SetQuickExportEnabledForRenderPreset(name, bool)` | render presets are now writable |
| `Project.GetAudioRenderCodecs/Formats` | codec queries |
| Project settings presets: set/delete/import/export/update | fps-per-project setup could be a preset |
| `resolve.ValidateDCTL`, `EncryptDCTL` | DCTL development |
| `resolve.GetCurrentProject/CurrentTimeline/MediaPool/Gallery` | shortcuts |

- Already present since 21.0 and 21.0.4, and unused here: `Timeline.GetSelectedClips()`
  and `MediaPool.GetSelectedClips()` (read what Ryan has selected),
  `AnalyzeForIntellisearch`, `AnalyzeForSlate`, `PerformAudioClassification`,
  `GenerateSpeech`, `TranscribeAudio(useSpeakerDetection=True)`. **VERIFIED**
  (changelog + grep of `studio/`).

### Third-party server status

Upstream `samuelgursky/davinci-resolve-mcp` is at v2.223.0 and its release
notes already wrap the 21.1 APIs (`AddTransition` 2.218, `CreateMulticamClip`
2.219, output blanking 2.220, `NormalizeAudioLevel` 2.221, `AutoAlignClips`
2.222, `ValidateDCTL` 2.223). `GetTranscription` is not mentioned. **REPORTED**
(GitHub releases page; the fetch mis-dated the release year, the version
numbers are what matter). The copy vendored here is the 2026-07-11 checkout,
roughly 160 minor releases behind. **VERIFIED** (`git log` in `vendor/`).

## What this changes for the studio

The studio's architecture does not move. The deterministic command layer is
the CLI verbs and the Story IR (RESEARCH.md §MCP timing); MCP is the
exploration harness an agent uses while those verbs are being built. What
changes is which harness, and which new primitives the verbs can reach.

### 1. Copilot primitive: read Ryan's selection

`Timeline.GetSelectedClips()` turns "insert the meme on *these*" into a verb
that needs no `find "phrase"`. Ryan lasso-selects in the GUI, the agent reads
the selection, maps items back to IR edits by record frame, and mutates
`story.json`. This is the most copilot-shaped API in the release and it costs
nothing to try. **Completion criterion:** `tools/edit-ir.py <ws> selected`
prints the IR edit ids under the current Resolve selection; a test with two
selected clips returns exactly two ids.

### 2. The OBS camera isolates become a multicam, not a hand-built V2 lane

The open claim `obs-camera-isolates-in-movies-iso-are-an-untouch` planned a
cut-in verb that places the `-cam.mp4` isolate on V2 by hand. 21.1 supplies
`CreateMulticamClip` + `AutoAlignClips(WAVEFORM)` + `PerformMulticamSmartSwitch`
+ `FlattenMulticam`. The multicam is built by Resolve, aligned by waveform,
switched by Resolve's own model, and flattened to ordinary clips that the
IR can then describe. **Completion criterion:** one Sept-7 program recording
plus its isolate become a multicam clip; `AutoAlignClips` returns True;
measured offset between the two tracks after alignment is within 2 frames of
the OBS one-press start; the flattened result verifies GREEN through
`compile-ir.py`.

### 3. Transitions, fades and speed as a post-compile pass keyed from the IR

`docs/STORY-IR.md` reserves transitions for a schema bump. The append-only
doctrine ("mid-timeline edits are impossible") still holds, but a transition
is not a mid-timeline edit: it attaches to an existing item's edge. So the
compiler stays OTIO import, then walks `story.json` and applies
`AddTransition` / `SetFades` / `SetSpeed` to the items it just created. The IR
remains the source of truth and `COMPILER_EPOCH` bumps. **Completion
criterion:** an IR with one `transition: cross-dissolve, 12 frames` compiles
to a timeline whose `GetItemListInTrack` shows the transition item at the
declared edge with the declared duration; a rendered control with no
transition differs only in those 12 frames.

### 4. Loudness in the audio spine

`deliver.py` measures loudness after the render. `NormalizeAudioLevel` with
a `targetLoudness` moves that upstream, onto the voice track before render, so
the check becomes a confirmation rather than a diagnosis. **Completion
criterion:** a workspace whose voice measures outside the target before the
pass measures within 1 LU of `targetLoudness` after it, by ffmpeg `ebur128`.

These four are sequenced, not a fork: none excludes another, and each has its
own criterion. Order is 1, 2, 3, 4 by cost and by how much of the open
backlog each one retires.

### Measurement before any doctrine change: Resolve's transcript vs Deepgram

"Deepgram, never Whisper" is locked. Resolve's engine is neither; it is
Blackmagic's own model, and `GetTranscription` now exposes word-level
timecodes and speaker labels through the API. Word timing is what
`studio/moments.py` maps into record frames, so the only question that
matters is timing accuracy, and it is countable. **Measurement:** transcribe
one already-Deepgram'd recording with `TranscribeAudio(useSpeakerDetection=True)`,
read `GetTranscription()`, align words to the Deepgram JSON, and report the
median and 95th-percentile start-time delta in frames over N words. Nothing
changes until Ryan reads that table.

## Conflicts with locked decisions ([RYAN] block)

1. **Which MCP server Claude Code holds.** CLAUDE.md locks "Adopt
   `samuelgursky/davinci-resolve-mcp`; no rival servers." The native server
   is Blackmagic's own, ships inside the app, self-updates with it, and
   carries the current stub and changelog as tools. The vendored third-party
   copy is 160 releases stale and has to be re-vendored to see any new API.
   My recommendation is to replace, not add: the doctrine "one fusionscript
   client at a time" is the reason add-versus-replace is a real either/or,
   and it is not yet measured whether `ResolveMCP` holds a persistent
   connection. **Countable check before deciding:** both servers connected
   for one working session, 30 tool calls spread across both, and
   `app.GetCurrentPage()` still returns a page name at the end. If it wedges,
   the choice is forced. `.mcp.json` was not touched.
2. **`run_script_unsafe` is a trust-boundary change.** Adopting the native
   server hands the agent arbitrary Python with filesystem, network and
   subprocess access on this machine. Bible §4.6 makes that Ryan's call.
   Resolve's own preference "Automatic scripted actions: Allow safe" governs
   embedded scripts, not this tool. Options are to accept it, or to run the
   native server with `run_script_unsafe` denied in Claude Code's permission
   config.
3. **`generate_lut` / `update_dctl` sit on the wrong side of "agents apply,
   Ryan authors."** The native server's own pitch is "generate custom LUTs
   and DCTLs from a description." That is authoring. `ValidateDCTL` is fine;
   the generators should stay unused unless the grades doctrine changes.
4. **Transcription doctrine** is not being changed by this report; see the
   measurement above.

## Corrections made to RESEARCH.md alongside this report

- The BMD API README is now v21.1 (Sept 2026), not v21.0.
- The third-party landscape table gains the native BMD row and the
  `samuelgursky` row now reads v2.223.0 upstream, 2026-07-11 vendored.
- "Resolve API docs target Python 3.6 while the MCP needs 3.10–3.12" is
  replaced: Blackmagic ships Python 3.14 and dropped Python 2; the studio's
  venv is 3.12.

## Sources

Primary: the installed app bundle (`ResolveMCP --dump-tools`, the `.mcpb`
manifest and `server/index.js`, `Developer/Scripting/CHANGELOG.md`, `README.md`
and `DaVinciResolveScript.pyi`), and the live smoke test in
`docs/research-raw/resolve-21.1/`.

Secondary: [CineD](https://www.cined.com/davinci-resolve-21-1-released-ai-assistant-integration-via-mcp-individual-hdr-trims-and-python-scripting-moves-to-studio/),
[Newsshooter feature list](https://www.newsshooter.com/2026/09/07/blackmagic-design-davinci-resolve-21-1/),
[Y.M.Cinema](https://ymcinema.com/2026/09/09/davinci-resolve-21-1-chatgpt-claude-ai-assistants/),
[VP Land](https://www.vp-land.com/stories/davinci-resolve-21-1-introduces-claude-and-chatgpt-assistants-that-edit-across-post-throug),
[Sports Video Group, IBC 2026](https://www.sportsvideo.org/2026/09/09/ibc-2026-blackmagic-design-releases-davinci-resolve-21-1/),
[samuelgursky releases](https://github.com/samuelgursky/davinci-resolve-mcp/releases).
Discarded: [byteiota](https://byteiota.com/davinci-resolve-21-1-mcp-server/)
conflates the native server with a third-party npm package (its "88 tools"
and `npx davinci-resolve-mcp setup` are not Blackmagic's).
