# Lane B research — how top-tier explainer animation is actually made

*Deep-research sweep 2026-07-16/17 (105 agents, 23 sources, 102 extracted
claims, top 25 adversarially verified by 3-vote refutation panels: 20
confirmed, 3 refuted, 2 unverified-by-error). Confidence labels: **[3-0]** /
**[2-1]** = confirmed vote margins; **[unverified]** = extracted from a source
but never panel-checked. Verify unverified claims before load-bearing use.*

Context: this research serves the Lane B (authored/synthesized media) planning
step — see memory `authored-media-lane-vision` and the Monero first build.
Machine ground truth it must be read against: M1 Pro / 16 GB (no CUDA — local
video diffusion out of scope; hosted APIs / rented GPU boxes are the
generation lane), Resolve Studio 21.0.2 + Fusion, Blender 5.1.2 headless-
proven, ComfyUI installed but weightless (workflow editor only), Replicate
proven via Scene Forge, HyperFrames CLI functional via npx.

> **Continuation/correction, 2026-07-17:** the broader creator-methodology
> sweep refuted the universal version of the code-first headline below. Code
> is a primary medium for some schools and a leverage layer for others. Motion
> design and technical 3D retain substantial manual research, design, timing,
> modeling, performance, and critique. See
> [`LANE-B-CREATOR-METHODS.md`](LANE-B-CREATOR-METHODS.md) for the recovered
> continuation and production implications.

## Initial code-first finding — now narrowed

Within this memo's verified sample, a strong pattern recurred: **the creators
drive repeatable parts of their tools with code, and the reusable system is an
asset.** 3B1B is Python-centric; Animagraffs combines Blender craft with a
self-written add-on toolset; ChimeraX movies can be command scripts; LTX-2
control workflows are node graphs. The sample, however, overrepresented
programmatic schools. The follow-up found equally strong work built around
hand-tuned keyframes, modeling, performed cameras, visual development, and
team critique. The durable conclusion is that automation removes repetition;
it does not replace the decisions that constitute authorship.

## School 1 — Programmatic animation (manim lineage)

- 3B1B videos are produced almost entirely as code with Sanderson's own manim
  fork (`manimgl`, not manim-community). **[3-0]**
  (github.com/3b1b/videos)
- The full production source for every video 2015–2026 is public in that repo
  — you can read the actual code behind any scene you admire instead of
  guessing. **[2-1]**
- His authoring loop is interactive/REPL-style, not batch: embedded-debugger
  entry at a source line + `checkpoint_paste()` iterating with scene state
  preserved. Directly automatable by a code-writing agent. **[3-0]**
- But NOT purely code: the workflow leans on Sublime Text editor plugins — an
  editor-integrated interactive loop. **[3-0]** (The stronger claim "all 3B1B
  animation is manim, therefore fully agent-automatable" was **REFUTED 0-3**
  — treat "it's 100% code" as an oversimplification.)
- Agentic manim exists off the shelf: `manim-generator` runs a two-role LLM
  loop (Code Writer + Code Reviewer) **[3-0]** and closes the loop on actual
  rendered frames fed back to a multimodal reviewer. **[3-0]** Claims about
  TheoremExplainAgent's end-to-end automation and its model-dependent success
  rates were **REFUTED 0-3** — don't cite that benchmark.
- Adjacent web-stack lane [unverified]: Motion Canvas is effectively
  unmaintained (active fork: "Canvas Commons"); its flexbox layout means
  HTML/CSS-fluent agents transfer directly. Remotion + Claude Code is a
  documented agent-driven React→video path. (Our HyperFrames occupies this
  same niche and is already in-stack.)

## School 2 — Team studios (the effort ceiling)

All [unverified] (extracted, didn't make the verify cut):
- Kurzgesagt: After Effects 2D layer animation over ~200 custom illustrations
  per 10-min video; 2-3 illustrators 8-12 weeks; animation another 8-10 weeks
  with 2-3 animators; >1,200 person-hours per video; research/scripting can
  take weeks to years. NOT Blender, NOT programmatic.
- **No complete first-person fern per-video breakdown surfaced.** A role
  posting supplies partial Blender and multi-role evidence; frame study
  remains an inference exercise, not pipeline ground truth. See the companion
  memo for the bounded evidence.
- Counter-example that matters more than either: **Animagraffs is ONE person**
  producing studio-tier technical explainers entirely in Blender, with a
  custom Python add-on suite (modeling/file-hygiene/transparency/render/label
  tools) built ~a week at a time between projects, by a self-described
  non-programmer. **[3-0]** (youtube.com/watch?v=OkadsUTl1Pw)
- O'Neal (Animagraffs) renders production frames HEADLESS via CLI — his
  render button generates a .bat spawning multiple background Blender
  instances to saturate GPUs. **[3-0]** Same idiom as our
  `studio/blender.py`.
- His signature x-ray/fade transparency system is custom Python (drivers on
  alpha linked to world properties + a render handler unloading zeroed
  collections) — impossible natively. **[3-0]** For Animagraffs, private
  tooling is a major multiplier. For Lane B, repo-owned tooling is one
  possible leverage layer; the broader sample shows it is not the creative
  edge by itself.

## School 3 — Agent-driven Blender

- blender-mcp exists (ahujasid/blender-mcp): an MCP bridge letting Claude
  drive Blender directly **[3-0]**, including running arbitrary Python,
  object/material/scene CRUD, and scene inspection. **[3-0]** It is not
  adopted. It is a candidate exploration surface requiring an explicit
  arbitrary-code trust review; repo-owned `bpy` scripts remain the currently
  proven approach.
- [unverified] Community experience: agent-driven Blender succeeds
  consistently at hard-surface/geometric scene assembly and utility
  scripting — i.e., exactly the diagram-like structured scenes an explainer
  needs — and struggles with organic modeling.
- [unverified] `bpy` is pip-installable for GUI-less scripting; geometry
  nodes are fully constructible from Python.

## School 4 — Diffusion×3D hybrid (the seam Ryan named)

- LTX-2.3 (Lightricks, open-source audio-video model) is natively supported
  in ComfyUI — built-in workflows, no custom nodes. **[3-0]**
- ComfyUI ships six native LTX-2.3 workflows: T2V, I2V, first/last-frame
  interpolation, image+audio lip-sync, IC-LoRA union control, ID-LoRA
  personalization. **[3-0]**
- **The bridge primitive: IC-LoRA control conditions generation on depth,
  pose, or edge guidance** — i.e., Blender's deterministic depth/edge passes
  can steer diffusion imagery, giving generated pixels the geometric
  precision of a 3D scene. **[3-0 twice]** (docs.comfy.org LTX-2.3 tutorial;
  Lightricks/ComfyUI-LTXVideo)
- Hardware reality: recommended full-pipeline spec is CUDA 32GB+ VRAM, 100GB+
  disk. On Apple Silicon local use is effectively out of scope → hosted
  (Replicate) or rented GPU (the bongpot Vast.ai playbook,
  `~/projects/bongpot/tools/provision-ltx.sh`). **[3-0]**
- [unverified — verification errored, not refuted] RunComfy documents a
  Blender→ComfyUI workflow exporting depth/outline/color-mask passes into
  ControlNet Depth/Canny + regional-conditioning-by-mask + IPAdapter.
  Directionally consistent with the confirmed IC-LoRA facts; re-verify
  before building on the specifics.

## School 6 — Scientific/molecular visualization

- MolecularNodes (BradyAJohnston): Blender add-on importing structural
  biology data via Geometry Nodes (Blender 4.2+). **[3-0]** Supports
  PDB/mmCIF and MD trajectories, built on Biotite + MDAnalysis. **[3-0]**
  → real molecules, in the substrate we already drive headless. The ochem
  ambition has an existing, free, scriptable on-ramp.
- ChimeraX (UCSF) produces movies via a scriptable `movie` command driven by
  command files. **[3-0]** — the classic sci-viz lane is also code-driven.

## School 5 — Real-time/game engines: initial coverage hole

Nothing about Unreal/Unity/Godot/three.js explainer production survived to
the verified set; the scivis angle spent its budget on molecular viz. That gap
is filled in the continuation with first-person methods from CodeParade,
Lorenzo Drago, Inigo Quilez, Vercidium, Amit Patel, and ThinMatrix. The machine
note remains: no engines are installed, and the follow-up did not establish a
need to adopt one before a chosen artifact demonstrates a real-time
requirement.

## Draft translation assessment (for dialogue with Ryan, not decided)

What the field's practice maps onto this stack:

1. **Precision candidates** — scripted Blender and the existing
   HyperFrames/Fusion lanes are proven locally. Manim is an uninstalled option
   gated by a scene-specific need. Multiple substrates remain viable; the
   choice belongs to the scene and Ryan's selected visual language.
2. **World/texture layer** — diffusion via Replicate (proven) or rented GPU
   ComfyUI+LTX (playbook exists in bongpot).
3. **Candidate seam** — LTX IC-LoRA accepts depth, pose, and edge controls. A
   Blender-to-LTX handoff and its output quality remain untested locally; the
   recovered ControlNet workflow is still unverified. Validate both before
   treating this as a production seam.
4. **Molecules** — MolecularNodes drops real PDB data into the Blender lane.
5. **Assembly hypothesis** — emit Lane B media into the existing Story IR →
   OTIO → Resolve spine by default; change it only if the micro-build exposes
   a concrete incompatibility.

Gap-analysis state when this first memo ended: no fern ground truth;
game-engine lane unresearched; manim/MolecularNodes/blender-mcp all
uninstalled; ComfyUI local authoring-only; two hybrid-workflow claims awaiting
re-verification. The continuation narrows fern to partial role evidence, fills
the game/realtime lane, and converts the remaining items into explicit
adopt/adapt/improvise/overcome gates rather than default tool installs.
