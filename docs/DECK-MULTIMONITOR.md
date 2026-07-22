# DECK-MULTIMONITOR — sharing left vs right screen (research + proposal, 2026-07-21)

*Report before build. Nothing wired until Ryan blesses. Verification legend:
**[V]** fetched from source · **[F]** OBS forum consensus · **[M]** measured on
Ryan's rig this session · **[T]** thin (single source).*

## Ryan's actual geometry (measured via CoreGraphics) [M]

| Side | Display | Resolution | Notes |
|---|---|---|---|
| **LEFT** | external monitor | 1920×1080 | native 16:9 — fills the canvas with no bars |
| **RIGHT** | built-in MacBook | 1728×1117 (logical) | main display; 16:10 → pillarboxed on a 16:9 canvas |

OBS canvas is 1920×1080. The external (left) is the clean full-frame share.

## How streamers solve multi-monitor sharing

Three patterns exist. Ranked for THIS rig:

1. **Scene-per-monitor** — one scene per display, each a full-frame Display
   Capture; switch with Stream Deck **Scene** keys. [F] The winning key lights
   up (on-air highlight), so you SEE which screen is live. Matches Ryan's
   existing deck grammar exactly (his scene keys already do this).
2. **One scene, two sources, Source Visibility toggle** — official Elgato OBS
   plugin has a Source Visibility action with live on/off key state. [V] Works,
   but no spatial "which screen" feedback and clutters one scene.
3. **[current] One Display source, swap `display_uuid`** — Ryan's "Screen
   Picker" key. One key toggles built-in↔external. Works, but it's a swap not
   a pick: no distinct left/right keys, labeled BUILT-IN/EXTERNAL not L/R,
   easy to miss. This is why Ryan "doesn't see" a way to change screens.

## macOS facts that matter [V/F]

- Multiple Display Captures use Apple's **ScreenCaptureKit** (macOS 12.3+),
  which handles Retina scaling natively — the same thing that made the
  fit-to-canvas fix work.
- **Only the active scene's sources render.** Scene-per-monitor does NOT pay a
  double capture cost — the off-air screen's capture is idle. [F]
- Primary gotcha is **Screen Recording permission**: black frame if not
  granted, and it can silently reset after OS updates → System Settings →
  Privacy & Security → Screen Recording. [V]
- No standard for spatial vs numeric key labels — user's call. [T] "SCREEN L /
  SCREEN R" is clear and unambiguous for a 2-monitor rig.

## BUILT 2026-07-21 (blessed + shipped, obs-control-room commit 6df9475)

Pattern 1 shipped. On Ryan's rig now: **Screen L** (external/left) and
**Screen R** (built-in/right) scenes, each a fit-to-canvas full capture;
two deck scene keys with on-air highlight at scene-row cols 2–3; Screen
Picker retired; Screen + Cam defaults to the left screen. Left/right
computed from CoreGraphics x-origin in both `display-uuids.py` and
`setup-scenes.mjs`. Machine-verified: scenes switch, displays map L=left
R=right. **Ryan's eyes still gate the actual picture** (press SCREEN L /
SCREEN R and confirm each shows the right monitor full-frame). One known
quirk: OBS reverted the live display_uuid to its last-saved collection
once mid-build — if L/R ever swap after an OBS restart, re-run
`node scripts/setup-scenes.mjs` (it's the SSOT) or just press through.

## Original proposal (adopted as-is)

**Adopt pattern 1, scene-per-monitor**, because it gives Ryan the exact
left/right keys he asked for AND rides his existing on-air-highlight grammar:

- Replace the single **Screen** scene with **Screen L** (external, full-frame)
  and **Screen R** (built-in, full-frame). Two full-screen Display Capture
  sources, each auto-fit to canvas (scale-inner, the fix from `16d209a`).
- Two deck **scene keys**: `SCREEN L` / `SCREEN R`, monitor glyph + L/R, native
  on-air highlight. Left/right derived from CoreGraphics x-origin (external is
  left today; the builder should compute it, not hard-code, so re-arranging
  monitors doesn't lie).
- **Screen + Cam**: keep as ONE scene defaulting to the share screen (proposed:
  external/left — the clean 16:9). Revisit L/R variants only if he wants them.
- **Retire the Screen Picker key** — superseded by the two explicit scene keys.
  (The CAMERA picker stays; that solved a real problem.)

**Cost:** +1 scene, +1 display source. Trivial. No perf hit (only-active-renders).

**Open [RYAN] decisions:** (a) bless scene-per-monitor; (b) Screen + Cam — one
scene on the left screen, or L/R variants too; (c) retire Screen Picker, or
keep it as a fallback.

## Sources [V]
- Elgato OBS plugin (Source Visibility live state): elgato.com/us/en/s/obs-studio-plugin-for-stream-deck
- OBS forum, scene-per-display: obsproject.com/forum/threads/different-scenes-different-screens.151991/
- macOS ScreenCaptureKit perf (GitHub #10636): github.com/obsproject/obs-studio/issues/10636
- Screen Recording permission reset: obsproject.com/forum/threads/screen-capture-permissions-not-working-heres-a-solution.159963/
