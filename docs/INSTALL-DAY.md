# Install-day checklist — Resolve Studio

## Progress 2026-07-11 (install day WAS today)
- ✅ Studio 21.0.2.4 installed, licensed, external scripting **Local** confirmed live
- ✅ E2E smoke PASSED (`scripts/smoke_e2e.py`): project → import → timeline →
  markers → render → ffprobe. Finding: render inherited project-default 24fps
  vs 30fps sources — **Compiler must always set timebase explicitly.**
  AddRenderJob first call returned a job id (quirk didn't manifest; guard kept).
- ✅ Interchange smoke PASSED (`scripts/smoke_interchange.py`): auto-editor
  FCPXML → `ImportTimelineFromFile` → 5 editable clips.
- ✅ `.setting` format verified against BMD's own shipped examples at
  `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Fusion Templates/`
  (MacroOperator + InstanceInput, plain-text Lua table — as designed for).
- ✅ Bundled docs located (`Developer/Scripting/README.txt`, 26 May 2026 — newer
  than the gist mirror, 8 May). CHANGELOG.txt: drift is ADDITIVE only. Resolve 21
  added: TranscribeAudio(useSpeakerDetection), PerformAudioClassification,
  AnalyzeForIntellisearch, AnalyzeForSlate, GenerateSpeech,
  DisableBackgroundTasksForCurrentResolveSession. → Check whether transcript
  TEXT is now retrievable via API (old folklore: trigger-only).
- 🔎 Found `Developer/OGraf HTML Templates/` — EBU OGraf HTML graphics support?
  Potential hyperframes↔Resolve bridge. INVESTIGATE.
- ⬜ Remaining: MCP `install.py` · headless `-nogui` probe · agent-authored
  `.setting` → Effects Library round-trip (needs one Resolve restart + Ryan's eyes)

Run top to bottom the day Studio lands. Each item is minutes; together they
convert RESEARCH.md's remaining [UNVERIFIED] claims into ground truth on THIS
machine before any building starts.

## Purchase & install
- [ ] Buy DaVinci Resolve Studio ($295 one-time) — blackmagicdesign.com or a
      license dongle from a reseller. Keep the activation key in the usual
      secrets place, not in this repo.
- [ ] Install Resolve Studio (macOS build). Launch once, activate, let it
      create its folder structure.

## Enable the scripting surface
- [ ] Preferences → System → General → **External scripting using: Local**.
- [ ] Confirm the API module exists:
      `/Library/Application Support/Blackmagic Design/Developer/Scripting/Modules/DaVinciResolveScript.py`
- [ ] Smoke: with Resolve running, from a Python 3.10–3.12 venv:
      `import DaVinciResolveScript as dvr; print(dvr.scriptapp("Resolve").GetVersionString())`
- [ ] Headless smoke: quit Resolve, relaunch with `-nogui`, rerun the same
      two-liner. Note: Resolve must be pre-launched; there is no one-shot CLI.

## Diff the docs we trusted
- [ ] Open `Help → Documentation → Developer`, find the bundled scripting
      README. Diff against the X-Raym gist mirror we verified from
      (RESEARCH.md sources). Flag any drift, esp. color/Fusion methods.

## Template mechanics (the .setting smoke)
- [ ] Confirm folder exists (create if not):
      `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/Titles/`
- [ ] Read one of Resolve's own shipped title `.setting` files to confirm the
      plain-text Lua-table format on v21.
- [ ] Build a trivial macro in Fusion (TextPlus → publish StyledText), save as
      `.setting` into Titles/, restart Resolve, confirm it appears in the
      Effects Library and its published input shows in the Inspector.
- [ ] Drop it on a timeline, stretch the clip, confirm Anim Curves behavior
      question: does OUR keyframed test stretch or clip? (Determines whether
      Anim Curves is mandatory in the template doctrine.)

## MCP smoke
- [ ] Install `samuelgursky/davinci-resolve-mcp` (needs Python 3.10–3.12).
- [ ] From Claude Code: connect, list projects, create a scratch project,
      import 3 clips, create a timeline, add markers, queue a render with a
      preset, `StartRendering`, poll status, ffprobe the output.
- [ ] Reproduce the known quirk: fresh project → first `AddRenderJob` — does it
      silently fail? Document retry behavior in CLAUDE.md if so.

## Interchange smoke (the architecture's load-bearing beam)
- [ ] Run auto-editor on any screen recording with `--export resolve`;
      import the FCPXML; confirm cuts arrive as editable clips with media
      relinked.
- [ ] Export that timeline back out as OTIO via the API
      (`timeline.Export`), confirm round-trip integrity.

## Exit condition
Phase 0 is done when every box above is checked and RESEARCH.md's Part 1
[UNVERIFIED] items are re-tagged VERIFIED-LOCAL or corrected.
