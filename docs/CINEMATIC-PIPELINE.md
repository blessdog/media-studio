# Cinematic pipeline spec — DJI Osmo Action 5 Pro → DaVinci Resolve Studio 21

Ryan's spec, received 2026-09-12, verbatim below the line. LOCKED items are
his decisions. VERIFY items are checked in `docs/CINEMATIC-PIPELINE-VERIFY.md`
as they are measured; a VERIFY item is not a fact until that file says so.
The grade assets it relies on live in `grades/film-look/` (fetched, hashed,
installed, DCTLs compiled in 21.1 on 2026-09-12).

---

Audience: the agent that will build and run the ingest/grade/render tooling.
Status: locked decisions are marked LOCKED. Items marked VERIFY must be confirmed
against the real camera, the real footage, or Resolve's own docs before being
treated as fact — do not assume them.

## 0. Target look

- Reference: a 16:9 frame with a subject 1–3 m from camera, background
  gently soft (buildings still legible), muted/desaturated palette, warm
  skin, soft highlight rolloff, fine grain, natural 24 fps motion blur.
- Depth of field target: what a 35–50 mm-equivalent lens at f/2.8–f/4 does.
  Not f/1.4. Not creamy bokeh. Subtle falloff is what sells synthetic DOF;
  heavy blur is what exposes it.
- Non-goals: ultra-wide action-cam FOV, electronic horizon lock, crushed
  blacks, crunchy high-shutter motion, oversharpened edges.

## 1. Camera facts that constrain everything

- Fixed aperture (f/2.8), fixed focus (roughly 0.4 m to infinity), small
  (1/1.3") sensor. Optical background blur is not achievable in camera at any
  distance. All depth of field is synthetic, added in Resolve.
- 10-bit requires D-Log M (or HLG) with H.265. Any clip that arrives as
  8-bit or H.264 was shot with the wrong settings — flag it, don't grade it.
- Exposure has only three controls: shutter (locked for motion blur), ISO
  (keep at base), and ND filters. ND is therefore mandatory in daylight.

## 2. Camera settings (human sets; agent verifies on ingest via ffprobe)

LOCKED:
- Pro/manual mode
- 3840×2160, 24 fps
- Shutter 1/48 (180°). Indoors under artificial light, if flicker appears,
  use 1/60 — never auto.
- ISO at base; never let it float. Bring exposure in with ND (carry ND8
  through ND64).
- White balance locked per scene, not auto.
- Color profile D-Log M, 10-bit, H.265, highest bitrate offered.
- Field of view: the narrowest / dewarped mode available (VERIFY exact menu
  name — on this camera it is the "Standard"-type option, not Wide or
  Ultra-Wide). The wide look is the strongest action-cam tell and makes
  synthetic blur look wrong, since no real ultra-wide lens blurs a
  background at these distances.
- Stabilization: RockSteady on for handheld (accept the crop); off on a
  tripod or gimbal. HorizonSteady / HorizonBalancing off.
- If the camera exposes in-camera sharpness or noise reduction, set both to
  minimum (VERIFY availability). Sharpen and denoise in post, not in camera.
- Expose to protect highlights. D-Log M is a flat Rec.709-style profile,
  not a true log curve — highlight recovery is limited. Don't underexpose
  either; the small sensor gets noisy fast.

Shooting notes that make CineFocus work later: subject 1–3 m from camera,
background as far away as possible, avoid subject against a same-distance
wall. Shots with no depth structure (flat walls, water, sky) will not get
synthetic DOF — they stay sharp, and that's fine.

## 3. Ingest (agent, FFmpeg/ffprobe)

- Never transcode or modify originals. Copy into a dated project folder;
  originals are read-only.
- Per file, ffprobe and assert: codec `hevc`, `pix_fmt` is 10-bit
  (`yuv420p10le` or equivalent), 3840×2160, 24 fps (allow 23.976 — VERIFY
  which the camera actually writes; the Resolve timeline must match it).
  Write a manifest (filename, duration, fps, bit depth, resolution, ISO if
  present in metadata). Flag anything that fails; do not import failures
  silently.
- Proxies: let Resolve generate them (Media Pool → Generate Proxy) rather
  than building a parallel FFmpeg proxy pipeline. VERIFY whether the proxy
  API call exists in the installed version before automating it.

## 4. Resolve project setup (agent, via the Resolve scripting API)

LOCKED:
- Color science: DaVinci YRGB (not color managed). Reason: Resolve ships no
  dedicated transform for D-Log M. The "DJI D-Log" entry in Color Space
  Transform is for the older D-Log profile and produces oversaturated,
  over-contrasty results on D-Log M footage. The correct technical
  transform is DJI's official D-Log M → Rec.709 LUT for the Osmo Action 5
  Pro, applied on a node. (VERIFY once in Resolve 21 whether a real D-Log M
  input option has appeared; if it has and it's actually DJI-derived,
  revisit. Until then, the LUT is the transform.)
- Timeline: 3840×2160, frame rate matching the footage, Rec.709 Gamma 2.4.
- Aspect ratio: 16:9 (matches the reference). If a letterbox is ever
  wanted, do it with timeline output blanking, not by cropping media.

API mechanics (VERIFY every method name against the README that ships with
the install — that file is the source of truth, not memory):
- macOS: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/README.txt`
- Windows: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt`
- Enable Preferences → System → General → External scripting = Local.
  Resolve must be running; scripts attach to it. Studio is required for
  external scripting (satisfied).
- Expected calls: `GetProjectManager` → `CreateProject`/`LoadProject`;
  `project.SetSetting` for frame rate, resolution, color science;
  `mediaPool.ImportMedia([...])`; `mediaPool.CreateTimelineFromClips`;
  `timelineItem.ApplyGradeFromDRX(path, mode)` to apply the base grade;
  `project.SetRenderSettings` / `LoadRenderPreset` / `AddRenderJob` /
  `StartRendering`.

## 5. The base grade (human builds once; agent applies to every clip)

The scripting API cannot create ResolveFX nodes or set their parameters. So:
the human builds the node tree once on a hero shot, saves it as a PowerGrade
and exports it as a `.drx`, and the agent applies that `.drx` to every clip
with `ApplyGradeFromDRX`. Per-shot adjustments are then human work on top.

LOCKED node order (left to right). The ordering principle: fix the image,
then lens effects, then film-stock effects, grain dead last.

1. **Noise reduction** — temporal NR, only when the shot needs it (ISO above
   base or visibly noisy shadows). Applied first so blur and grain don't
   bake noise in. Bypassed by default in the PowerGrade.
2. **Technical transform** — DJI D-Log M → Rec.709 LUT. Nothing else on this
   node. Do not use a creative LUT here.
3. **Balance** — exposure, white balance, contrast. Primaries only. This is
   the per-shot node the human touches most.
4. **CineFocus** — `Resolve FX AI CineFocus` (Color page, OpenFX). Sits here
   so the depth model sees a normalized image and so blur happens before
   halation/grain (lens before film stock). Bypassed by default in the
   PowerGrade; the human enables and sets it per shot (section 6).
5. **Film emulation** — whichever tool is chosen (Film Look Creator, or a
   third-party emulation). If it has an input-colorspace setting, set it to
   Rec.709 Gamma 2.4 because we are already in 709 after node 2. Halation
   and bloom live here. If the tool splits these into separate nodes, order
   them: halation/bloom → look/tone → grain.
6. **Grain** — last. Nothing after this node except the timeline-level output.

Optional lens vignette goes on node 4 or 5, never after grain.

## 6. CineFocus rules (human, per shot)

- Click the focus point on the subject's face/eyes. Set focal range wide
  enough to hold the whole subject (both people in a two-shot), then adjust
  aperture until the background reads as "soft but legible." When in doubt,
  less.
- Aperture shape: circular. Bokeh/optical extras: off or minimal for a
  natural lens; the reference has no visible bokeh balls.
- Keyframe only for a deliberate rack focus; otherwise leave it static.
- Judge in playback, not on a paused frame. Depth estimates can shimmer
  frame to frame. If a shot shimmers, reduce aperture strength before
  anything else.
- If edges halo (hair, straps, thin objects): for that shot, switch to
  Magic Mask on the subject feeding Defocus Background, instead of
  CineFocus.
- Shots with no depth structure: leave CineFocus bypassed.

## 7. Division of labor

Agent owns: ingest validation and manifest, project/timeline creation,
media import, applying the base `.drx` to every clip, render presets and
render jobs, and a per-project report (clips imported, clips flagged, clips
that still need the human pass).

Human owns: shooting, building/updating the base grade, per-shot balance,
CineFocus focus point and aperture, final review.

The agent must not claim it has "graded" footage. It applies the base grade;
the per-shot pass is unautomated by design.

## 8. Render

LOCKED:
- 3840×2160, frame rate = timeline, H.265 (or H.264 if a target rejects
  HEVC), high bitrate — err high; YouTube re-encodes anyway.
- Rec.709 Gamma 2.4. On first delivery, check for the Mac QuickTime gamma
  shift on the uploaded result; if the upload looks washed out compared to
  Resolve, switch the output tag to Rec.709-A and re-test once, then lock
  whichever matched.
- Save as a render preset; the agent loads it by name.

## 9. First-footage validation (do once when the camera arrives)

1. Shoot a 20-second test: subject at 1.5 m, background 15+ m, daylight
   with ND, 24 fps / 1/48, D-Log M 10-bit, narrow FOV.
2. Ingest through the agent; confirm the manifest reports 10-bit HEVC at
   the expected fps.
3. Build the base grade on that shot; confirm the D-Log M LUT gives neutral
   skin before any creative work.
4. Run a CineFocus aperture ladder (three strengths) on the same shot and
   watch each in playback. Pick the mildest one that reads as cinematic;
   that becomes the default in the PowerGrade.
5. Export via the render preset, upload unlisted, compare to Resolve on the
   same display. Resolve the gamma question here, once.
6. Lock the PowerGrade `.drx`, the render preset, and the ffprobe assertions.
   Everything after this is per-shot work, not pipeline work.
