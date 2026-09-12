# Cinematic pipeline — VERIFY ledger

Writer: the agent, at the moment each item is measured. Reader: whoever builds
or runs the lane, and Ryan deciding what is still an assumption. Fails when
wrong: a VERIFY in `docs/CINEMATIC-PIPELINE.md` gets treated as a fact.

Status words: **MEASURED** (checked on this machine, command given),
**REPORTED** (a review or forum says so, not checked here), **NEEDS CAMERA**
(only real footage or the camera menu can answer it).

| # | Spec item | Status | What was found, and how |
|---|---|---|---|
| 1 | §4 API README path is `Developer/Scripting/README.txt` | MEASURED, wrong path | On this install (21.1.0) the folder holds `README.md` (628 lines: setup, deprecations, unsupported calls) and **`DaVinciResolveScript.pyi`**, a 2,765-line typed stub with every method and docstring. The stub is the source of truth. `ls "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"` |
| 2 | §4 every named method exists | MEASURED, yes | In the stub: `LoadProject` 1633, `CreateProject` 1636, `ImportMedia` 1945, `CreateTimelineFromClips` 1897, `ApplyGradeFromDRX(path, gradeMode)` 2719, `SetRenderSettings` 1801, `LoadRenderPreset` 1768, `AddRenderJob` 1792, `StartRendering` 1783, `GetCurrentPage` 1516 |
| 3 | §4 `project.SetSetting` | MEASURED, deprecated | README.md line 595: `SetSetting`/`GetSetting` are deprecated for `SetSettings({...})`/`GetSettings()`. Still works; `studio/compile.py` uses the old form. Bookmark: migrate when compile is next touched |
| 4 | §4 a real D-Log M input in 21.1's CST | MEASURED, no | `strings` on the Resolve binary lists `DJI D-Gamut/D-Log` and `DJI D-Gamut2/D-Log2` and no `D-Log M`. The LUT stays the transform. Scope: binary strings, not a click through the CST menu |
| 5 | §5 `Resolve FX AI CineFocus` exists | MEASURED, yes | Binary carries `AI CineFocus` and plugin id `com.blackmagicdesign.resolvefx.cinefocus`. Not yet exercised on footage |
| 6 | §3 proxy generation by API | MEASURED, no | Stub has `LinkProxyMedia(path)` / `UnlinkProxyMedia()` and the `perfProxyMediaMode` setting only. No generate call. Proxies stay a Media Pool click, per the spec's own preference for not building an FFmpeg proxy lane |
| 7 | §4 letterbox via output blanking | MEASURED, yes | `Timeline.SetOutputBlanking({'Top','Bottom','Left','Right'})` in pixels, new in 21.1 (stub 2290) |
| 8 | §8 render preset by name | MEASURED, yes | `GetRenderPresetList`, `SaveAsNewRenderPreset`, `UpdateRenderPreset`, `LoadRenderPreset` all in the stub. `RenderSettings` carries `ColorSpaceTag` / `GammaTag`, which is where the Rec.709 vs Rec.709-A decision from §8 lands |
| 9 | §5 the base grade cannot be authored by API | MEASURED, confirmed | Graph exposes `SetLUT`, `SetCDL`, `SetNodeEnabled`, `ApplyGradeFromDRX`, `GetToolsInNode`; nothing creates nodes or sets OFX parameters. Also `ValidateDCTL(source)` takes source text and returns None on success (measured 2026-09-12, all seven film-look DCTLs compile) |
| 10 | §2 in-camera sharpness and NR controls exist | REPORTED | CineD's review mentions NR sliders; cinem8's settings guide says sharpness and NR both go to -2. Confirm in the camera menu |
| 11 | §2 exact name of the narrow/dewarped FOV mode | NEEDS CAMERA | |
| 12 | §3 does the camera write 24.000 or 23.976 | NEEDS CAMERA | The ingest tool asserts either and records which; the project fps is stamped from the file, not from the spec |
| 13 | §8 Rec.709 vs Rec.709-A on upload | NEEDS CAMERA | First delivery decides it, once |
| 14 | §9 CineFocus aperture ladder | NEEDS CAMERA | |
| 15 | ApplyGradeFromDRX crash on macOS after the next graph call | REPORTED | Blackmagic forum t=214698 (v19). Measure on 21.1 with the first .drx; if it reproduces, apply the grade as the last call per clip |
