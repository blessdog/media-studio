# Motion graphics doctrine (feeds Phase 4)

Distilled from the 2026-07-11 design conversation + verified findings. This is
the full detail; PLAN.md only summarizes it.

## Definitions
**Animation** = the umbrella craft (characters, scenes, performances — bongpot's
lane). **Motion graphics** = graphic design in motion: type, shapes, charts,
diagrams, callouts, transitions. Script/research → video needs both: genAI/Wan
for animation, Fusion templates for motion graphics.

## What a Fusion motion graphic IS
A procedural node graph evaluated at render time on the GPU — live math, not
baked pixels. Stays editable and re-parameterizable until final render. This is
the fundamental contrast with Blender/genAI assets (frozen pixels in files).

## The template format (all verified locally 2026-07-11)
- A template is a **`.setting` file: plain-text Lua table** of the node graph.
  Agents can write, patch, lint, diff them offline — templates are CODE.
- Simplest possible Title: a **bare `TextPlus` tool named `Template`** (see
  Resolve's own "Candy" title — no macro wrapper needed; Inspector controls
  auto-exposed). Richer templates: `MacroOperator`/`GroupOperator` with
  published `InstanceInput`s (only published inputs appear in the Inspector).
- Install path (user-level, verified):
  `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/{Titles,Effects,Generators,Transitions}/`
  — the subfolder determines the kind.
- **Resolve rescans templates LIVE** — our file was scanned within 1s of
  writing (429→430 templates, logged), no restart needed.
- Official reference examples ship at
  `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Fusion Templates/`
  and inside `.../Resources/Fusion/Templates/Templates.drfx` (a zip of
  .setting files — unzip to study any built-in).
- API insertion without GUI: `Timeline.InsertFusionTitleIntoTimeline(name)`
  (proven: `scripts/smoke_title.py` → 120-frame item → rendered mp4).

## Animation inside a template — three mechanisms
1. **Keyframes** — `BezierSpline` modifier on an input (fixed timing).
2. **Expressions** — inputs computed from other inputs/time (procedural).
3. **Anim Curves modifier** — REQUIRED DOCTRINE for Edit-page templates:
   animation keyed to % of clip duration so trims stretch/squish the motion
   instead of clipping it (verified against the official manual).

## The three tiers of agent outsourceability
1. **Template instantiation — ~100% outsourceable. The workhorse.** Human
   authors/approves the template once (motion frozen in the file); agent
   populates content (text, colors, timecodes) per video. Data-driven motion
   graphics, broadcast-design-department style.
2. **Programmatic comp building — substantial but rough.** fusionscript via
   `GetFusionCompByIndex()`: `comp.AddTool("TextPlus")`, `SetInput`, node
   wiring (verified 3-0 in research incl. live tests). Caveats: badly
   documented, keyframe/spline authoring is the thinnest surface, and the
   agent animates BLIND — must run build → render preview → eyes loop.
3. **Design language & timing feel — NOT outsourceable.** Ryan's seat.

## The library grows by FORMAT PACKAGES (Round 3, 2026-07-12)

Not isolated widgets — themed sets sharing one look, matching Ryan's actual
reference space (Fern, Lemonhead/Lemon Clips, Red Bar, Channel 5, Plunder
Biscuit — never over-index on any two): 1) **news-desk** (ticker, headline,
bug, LIVE tag — authored, awaiting Ryan's verdicts) 2) podcast/clips (incl.
captions) 3) documentary 4) broadcast-retro/pirate radio. **Per-package
looks** — no global brand constraint.

**Rant visuals are a per-video artistic choice, never a system default**:
kinetic typography / ambient loops / Ryan's found b-roll (insert-clip) /
Phase 7 generated imagery — the system supplies one-liner verbs, Ryan picks
per moment.

## Graphics pipeline doctrine (settled by smokes, 2026-07-12)

- `InsertFusionTitleIntoTimeline` into an occupied timeline is a RIPPLE
  edit (razors V1, shifts everything) — dead path for overlays.
- Resolve's OTIO importer refuses ProRes4444 file references — graphics
  never travel through the interchange file.
- THE pipeline: **forge** (scratch fps-stamped project, insert title on an
  empty timeline, populate via comp `SetInput` — roundtrip-verified — render
  ProRes4444 + ExportAlpha, cached by hash of template+version+inputs+fps+res)
  → **place** (ImportMedia → AddTrack → `AppendToTimeline` with
  recordFrame/trackIndex; endFrame EXCLUSIVE) → multi-track verify.
- Masters are 150 frames (user still-duration pref, not scriptable); longer
  graphics via subrange today, seamless-loop extension later. No timeline-
  item retime API exists (only SetProperty is callable).
- Graphics live on one dedicated track above all edit tracks.
- Preview gate: `tools/preview-template.py` composites the populated master
  over real footage; approval flips ONLY on Ryan's verdict (manifest
  `approved` + registry).

## Anti-slop architecture (locked)
- **Curated library of 8–15 templates whose motion Ryan approved by eye.**
  Agent-authored candidates go through render-preview → Ryan's verdict BEFORE
  entering the library; never straight to a timeline. Infinite generated
  variety is the slop path.
- LLM-authored timing/easing is exactly what an LLM confidently gets wrong —
  syntactically perfect PowerPoint-feeling motion. The library gate exists
  for this.
- Template linter (schema/structure checks on .setting files) before any
  install — lint-before-spend generalized.

## Division of labor across substrates
- **Fusion templates**: recurring, text-bearing, brand elements that live ON
  the Resolve timeline and stay Inspector-editable (captions, lower thirds,
  callouts, chapter cards).
- **Blender (bpy headless)**: bespoke dimensional showpieces, exact camera
  choreography, anything repeatable/revisited; renders WITH ALPHA (ProRes
  4444 / EXR / PNG seq) and composites as a clip. Frozen pixels — change one
  word, re-render.
- **hyperframes (HTML)**: cutwork's locked compositor; agent authors
  end-to-end deterministically; import renders as clips. NOT wired into this
  repo unless Ryan changes doctrine.
- **OGraf HTML Templates** (`Developer/OGraf HTML Templates/` discovered on
  install): EBU standard for HTML overlay graphics, possibly native in
  Resolve 21 — POTENTIAL hyperframes↔Resolve bridge. Investigate during
  Phase 4 before building anything on it.
