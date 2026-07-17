# Lane B master research report — how explainer animation is actually made, and what a solo creator + agents can reach

*Consolidated 2026-07-17 from four research streams (2026-07-16 → 07-17) plus a
22-agent citation-verification pass. This is the full-visibility report: every
finding, with its verification status, in one place. The companion working
docs are [`LANE-B-RESEARCH.md`](LANE-B-RESEARCH.md) (pass-1 memo) and
[`LANE-B-CREATOR-METHODS.md`](LANE-B-CREATOR-METHODS.md) (creator field map);
this report supersedes neither but contains everything in both plus the
gap-sweep material that never made it into either.*

**How to read confidence labels:**

| Label | Meaning |
|---|---|
| **[3-0] / [2-1]** | Confirmed by a 3-vote adversarial refutation panel (vote margin shown) |
| **[cite-checked]** | Claim's citation fetched and verified against source text, 2026-07-17 |
| **[audio]** | Stated only in podcast/video audio with no published transcript — plausible, not text-verifiable |
| **[unverified]** | Extracted from a source (often with a direct quote) but never panel-checked |
| **[REFUTED]** | A verification panel or fact-checker contradicted it — do not build on it |
| **[CONTESTED]** | Verification runs disagreed — treat as unresolved |

---

## 1. Executive summary

**The question:** how is top-tier educational/technical explainer animation
actually produced today, and which production approaches are within reach of a
solo creator augmented by AI agents?

**The answer, in five sentences.** The field has two successful production
economies: *code/procedure as the medium* (3Blue1Brown, Animagraffs, shader
artists, Houdini proceduralists, interactive-web authors) and *designed,
performed motion* (the After Effects motion-design school, the team studios),
with most strong workflows hybrid between them. In both economies, **the
repeatable system is an asset** — code, rig, template, checklist, or practiced
technique — and automation removes repetition without replacing the decisions
that constitute authorship: message, visual language, timing, taste, and
accuracy. The effort ceiling at the top is brutal (Kurzgesagt: 1,200+
person-hours per 10-minute video; Branch Education: months of research and
review per topic) — but Animagraffs and Jared Owen prove that *one person plus
private tooling* produces studio-tier technical explanation. Agent leverage is
real and specific: headless scripted Blender, data-driven labels/graphs,
programmatic animation lanes (manim/Remotion/HyperFrames), render
orchestration, and research support — while organic modeling, keyframe
performance, camera taste, and final verdicts remain human. For this studio,
every already-proven lane (Blender headless, HyperFrames, Fusion, Resolve/Story
IR, hosted diffusion) matches how the field actually works; nothing found
justifies adopting a game engine, manim, or blender-mcp before a chosen scene
proves the need.

**What the research also delivered that the working docs don't yet show:** a
verified crypto-visualization vocabulary for the Monero build (§8), a
31-creator field map (§6), and a trust ledger of what survived vs. failed
verification (§10).

---

## 2. How this research ran (provenance)

Four streams, all wounded by session-quota failures, then recovered:

1. **Pass 1** (07-16 evening): 5 search angles → 23 sources → 102 extracted
   claims → 25 panel-verified (20 confirmed, 3 refuted, 2 errored). Synthesis
   stage died.
2. **Pass-1 resume** (07-17 morning): re-ran the dead verifications — 12 more
   confirmed, 2 refuted, 11 unverified. Synthesis died again.
3. **Gap sweep** (07-17 morning): 21 sources → 95 claims targeting coverage
   holes (fern, Melodysheep, crypto visualization, real-time engines). **All
   25 verifier panels failed on quota — every claim is [unverified]**, though
   most carry direct quotes from their sources.
4. **Creator-methodology sweep** (07-17 morning): discovery found 31 creators;
   all 14 profile agents and synthesis died on quota. A recovery pass rebuilt
   the profiles into `LANE-B-CREATOR-METHODS.md`.
5. **Citation-verification pass** (07-17 evening, 22 agents): fetched all ~50
   cited sources in the creator doc and adversarially checked each claim.
   Result: 2 sections fully sound, 14 minor corrections, 4 with unsupported
   numbers, 1 claim refuted outright. All corrections applied. The
   machine-state section was re-verified against this Mac: all confirmed.

---

## 3. School: programmatic animation (code is the medium)

### 3Blue1Brown / manim — the fully-inspectable pipeline

- Videos are produced almost entirely as code with Sanderson's own fork
  (`manimgl`, **not** manim-community; functionality differs). **[3-0]**
- The full scene source for every video 2015–2026 is public
  (github.com/3b1b/videos, year-based directories) — you can read the actual
  production code behind any scene you admire. **[2-1]**
- His day-to-day loop is interactive/REPL-style, not batch: embedded-debugger
  entry at a source line + `checkpoint_paste()` iterating with scene state
  preserved, plus Sublime Text editor plugins. Directly automatable by a
  code-writing agent. **[3-0]**
- **[REFUTED 0-3]:** "all 3B1B animation is manim, therefore fully
  agent-automatable" — the workflow is editor-integrated and interactive;
  "it's 100% code" is an oversimplification.
- License split that matters commercially: the manim library is MIT, but the
  3b1b/videos scene code is **CC BY-NC-SA** — scene code can inform but not be
  commercially reused verbatim. **[unverified, direct quote]**

### Agent-driven manim — real but contested

- `manim-generator`: a two-role LLM loop (Code Writer + Code Reviewer), closes
  the loop on actual rendered frames fed to a multimodal reviewer; bounded
  iteration (default 5 cycles, 400s/scene timeout); model-agnostic via
  LiteLLM. Early-stage (~110 stars, no releases). **[3-0]** on architecture.
- **TheoremExplainAgent [CONTESTED]:** pass-1 panels refuted its headline
  claims 0-3; the resume's panels then confirmed the same claims. What both
  runs agree on: even "successful" agent-generated manim videos mostly ship
  visual-layout defects needing a human co-editor — the literature
  independently arriving at copilot-not-autopilot. Treat its benchmark numbers
  (93.8% o3-mini vs 2.1% Claude 3.5 Sonnet v1) as unresolved; treat its
  qualitative conclusion as corroborated.

### The web-stack lane (HyperFrames' niche)

- Motion Canvas is effectively unmaintained; the active continuation is the
  community fork **Canvas Commons** (verified active: commits through
  2026-06-27). The "Motion Canvas is unmaintained" half comes from the fork's
  tutorial framing, not an upstream statement. **[unverified]**
- Motion Canvas/Canvas Commons layout is flexbox-based — HTML/CSS-fluent
  agents transfer directly. **[unverified]**
- **Remotion officially documents AI-coding-agent authoring** as a supported
  entry path (first-party docs, remotion.dev/docs/ai/coding-agents) — the
  React→video lane is vendor-endorsed for agents, not community speculation.
  **[unverified, first-party source]**
- Our HyperFrames occupies this same niche and is already in-stack and proven
  (v0.7.61 via npx, machine-verified).

---

## 4. School: team studios (the effort ceiling)

All effort figures below are [unverified] but carry direct quotes from the
studios' own material.

- **Kurzgesagt:** pipeline is After Effects 2D layer animation over
  illustrated panels (Illustrator), with Cinema 4D only a recent experiment —
  NOT Blender, NOT programmatic. ~200 illustrated panels per average video;
  2-3 illustrators for 8-12 weeks; animation another 8-10 weeks with 2-3
  animators; **1,200+ person-hours per video**; research/scripting weeks to
  years. Their motion work leans on AE expressions (procedural layer) —
  confirmed **[2-1]**.
- **fern:** no complete first-person per-video breakdown exists publicly. Best
  evidence is the studio's own 2025 3D-Generalist posting: professional
  **Blender** proficiency required, UE5 optional; full traditional pipeline
  (modeling → compositing); distinct producer/editor/motion-designer roles; 3D
  staffed by remote freelancers. fern is a multi-role team and a quality
  reference, not a recoverable solo blueprint. **[cite-checked]**
- **Melodysheep:** commissions external artists for some shots — a 54-second
  Life Beyond 3 shot was built by a collaborator almost entirely in one
  Blender 2.93 file. Not strictly solo. **[unverified]**
- **Branch Education:** *World's Smallest Devices* fully modeled/rigged/
  animated in Blender (primary evidence: team artist's own forum breakdown —
  ~45 models, extensive Geometry Nodes, purchased-then-modified PCB generator,
  procedural ruler, collection management against render-memory limits).
  Multi-stage review; one complex video was "in the works for over a year and
  a half." Exact team counts/timelines exist only in podcast audio.
  **[cite-checked; numbers [audio]]**
- **Mustard:** two-person pipeline (research/writing/AE + 3D modeling/
  rendering split), SketchUp + Lumion + AE, ~6 weeks/video alongside full-time
  jobs, quality loss admitted at 2-week cadence. Polished technical
  explanation from disciplined linear craft, no code asset. **[cite-checked]**
- **Posy** (Michiel de Boer): edits and grades in **DaVinci Resolve Studio** —
  same NLE as this studio. **[unverified, first-party site]**

---

## 5. School: solo 3D technical explanation (the existence proofs)

### Animagraffs (Jacob O'Neal) — one person, studio-tier, entirely Blender

The strongest single data point for this studio's whole thesis. **[3-0]** on
all core claims:

- Produced entirely in Blender by a self-described non-programmer who built a
  custom Python add-on suite over ~2 years, writing tools ~a week at a time
  between projects.
- Renders headlessly via CLI: his "render job" button generates a .bat that
  launches multiple lightweight command-line Blender instances per GPU to
  saturate hardware (Eevee can't split across GPUs natively — he runs renamed
  per-GPU executables). Same idiom as our `studio/blender.py`.
- Signature x-ray/fade transparency system is custom Python (drivers on alpha
  linked to world properties + a render handler unloading zeroed collections)
  — impossible natively in Blender.
- Label pipeline is data-driven end-to-end: script lives in a table exported
  to CSV; a Python function generates numbered 3D label objects; labels render
  as separate passes with 0KB placeholder frames for the NLE. 121 labels in a
  35-minute video; ~180 for the SR-71. **[unverified, direct video quote]**
- Hour-long videos ≈ 100,000 frames on consumer GPUs (RTX 3080 + 2070).
  **[audio — video-only source]**
- His sequence still starts with deep research (patent drawings, engineer/
  pilot/mechanic forums, library books), a month+ on some base models, then
  substantial manual animation and review. **[cite-checked]**
- The strategic lesson: *capture each repeated production pain as a reusable
  studio tool* — not "automate the video."

### Jared Owen — the direct automation-vs-craft answer

- Sequence: research → modeling → script/voice → animation → narration sync →
  music → rough render → family-and-friends critique → final render (experts
  consulted during research). ~2 months per video with contractors, purchased
  models, and several render machines. Python + Animation Nodes automate
  repeated operations; AI-written Blender scripts tried with mixed results.
  **[cite-checked]**
- He identifies research, story, and making the 3D explanation self-evident as
  the hard part — and found ChatGPT as likely to get facts wrong as right,
  "a no-go for research for now." **[cite-checked]**

---

## 6. The creator field map (31 discovered)

Six schools; ~17 profiled with citation-checked methodology in
`LANE-B-CREATOR-METHODS.md`, the rest discovery-only leads.

| School | Profiled (cite-checked) | Discovery-only leads |
|---|---|---|
| Programmatic/shader | Inigo Quilez, Amit Patel | Martijn Steinrucken (Art of Code) |
| 2D/mixed motion design | Sander van Dijk, Ben Marriott, Ordinary Folk/JR Canest, Giant Ant, Emanuele Colombo, EJ Hassenfratz | Andrew Kramer (Video Copilot) |
| 3D technical explanation | Animagraffs, Jared Owen, Branch Education, fern (partial), Mustard | — |
| Procedural/simulation | Simon Holmedal, Vercidium | Entagma, Steven Knipping (Applied Houdini), Ten Minute Physics |
| Real-time/interactive/game | CodeParade, Lorenzo Drago, ThinMatrix | Sebastian Lague, Primer, Clinton Jones (pwnisher) |
| Diffusion-hybrid | Paul Trillo | Mickmumpitz, Albert Bozesan, Corridor Digital (Niko Pueringer, Wren Weichman), Matteo Spinelli (Latent Vision/IPAdapter Plus author), Purz, Martin Nebelong, Dave Clark, Captain Disillusion (VFX-literacy) |

Highest-value unprofiled leads for this studio specifically:

- **Sebastian Lague / Primer** — the "write a real sim, then film it" model;
  closest to rabbit-hole-driven educational content.
- **Matteo Spinelli (cubiq)** — author of the IPAdapter Plus nodes the
  identity-conditioning lane (Scene Forge) already depends on.
- **Ten Minute Physics** — NVIDIA researcher (PBD/XPBD co-inventor) doing
  browser-JS physics explainers: the purest research-to-lay pipeline.
- **Captain Disillusion** — documented pipeline: ~2 weeks scripting, ~4h
  footage per 2-minute video; the density benchmark for edited education.

The motion-design pipeline common to the AE school (van Dijk, Marriott,
Ordinary Folk, Giant Ant, Colombo): **message/brief → references → storyboard/
styleframes → animatic → blocking → timing/performance refinement →
compositing/texture → audio → delivery**, with sound considered from the start
(Ordinary Folk's stated Message → Design → Animation → Audio staging).
Plugins/rigs/expressions remove repetition; none of these creators lets
automation choose the message, style frames, or final timing. Marriott's
"plugin diet" datum: he attributes a major skill jump to *removing* automation
for 2-3 months to learn manual timing — automation without animation literacy
created a ceiling. **[cite-checked]**

---

## 7. School: agent-driven Blender + diffusion hybrid (the seam Ryan named)

### Agent-driven Blender

- **blender-mcp exists and is mature adoption-wise** (24.3k stars, MIT; socket
  server driving a live Blender session; Poly Haven/Sketchfab/Hyper3D asset
  integrations). An agent can run arbitrary Python, do object/material/scene
  CRUD, and inspect scenes. **[3-0]** It executes arbitrary code *by design* —
  a trust-boundary decision; the reported RCE issue is closed but the surface
  remains. Repo-owned `bpy` scripts stay the proven approach here.
- **Community performance profile [unverified]:** agents reliably succeed at
  hard-surface/geometric scene assembly, materials, arrangement, and utility
  scripting — exactly diagram-like explainer scenes — and reliably fail at
  organic shapes, animation curves/timing, Geometry Nodes (version-drift
  brittleness), rigging, and precise placement (needs rounds of correction).
  Prototyping-grade, not production-grade: a copilot shape.
- **`bpy` is pip-installable** for fully headless scripting; geometry nodes
  are constructible entirely from Python (`bpy.data.node_groups.new(...,
  'GeometryNodeTree')`), and scripted node setups are version-controllable
  code artifacts independent of .blend files. **[unverified, documented API]**
- Headless CLI (`-b`, `-P`, `-a/-f/-o/-E/-t/-F`) is sufficient for full
  render-pipeline automation; audio disabled in background mode; argument
  order matters. **[unverified, documented API]**

### Diffusion × 3D

- **LTX-2.3** (Lightricks, open-source audio-video model) is native in ComfyUI
  — six built-in workflows: T2V, I2V, first/last-frame interpolation,
  image+audio lip-sync, IC-LoRA union control, ID-LoRA personalization.
  **[3-0]**
- **The bridge primitive: IC-LoRA control conditions generation on depth,
  pose, edge, or motion-tracking inputs** — Blender's deterministic depth/edge
  passes can steer diffusion imagery with 3D-scene geometric precision.
  **[3-0, confirmed twice]**
- Hardware floor: CUDA 32GB+ VRAM, 100GB+ disk. Local Apple Silicon use is out
  of scope → hosted (Replicate, proven via Scene Forge) or rented GPU (bongpot
  Vast.ai playbook, `provision-ltx.sh`). **[3-0]**
- LTX-2 outputs HDR in **ARRI LogC3** — drops directly into Resolve
  color-managed grading. **[unverified, vendor docs]**
- **Mickmumpitz's two packaged Blender→ComfyUI workflows [unverified]:**
  (a) ControlNet variant — Blender exports depth/outline(Freestyle)/color-mask
  (emission shader) passes → ControlNet Depth/Canny + regional conditioning by
  mask + IPAdapter + AnimateDiff; the Blender half is fully scriptable
  headlessly. (b) Wan 2.1 VACE variant — Blender passes replace the control
  video directly (`WanVideoVACEStartToEndFrame`), frame count must follow the
  Wan 4n+1 rule; distributed as a JSON node graph with a serverless API
  option. Both are packaged for adoption, not custom engineering.
- **Practitioner reality check:** Trillo's *The Hardest Part* — ~700 Sora
  clips generated, ~55 used, whole project ~6 weeks; labor moved to prompt
  direction, coverage generation, rejection, and continuity construction.
  Bozesan's TARMAC (two-person): Stable Diffusion + substantial Blender +
  Magnific + Resolve. "AI-made" still contains traditional layout,
  compositing, and sound labor. **[cite-checked]**

### Scientific/molecular visualization (the ochem on-ramp)

- **MolecularNodes**: Blender add-on importing PDB/mmCIF + MD trajectories via
  Geometry Nodes (Blender 4.2+), built on Biotite + MDAnalysis; GPL-3.0,
  actively maintained (v4.5.12, 2026-03). Real molecules in the substrate we
  already drive headless. **[3-0]** (Documented as GUI tutorials; headless
  scripting path unproven.)
- **ChimeraX**: movie production via scriptable `movie` command + motion
  commands (coordset, crossfade, fly, morph, roll, perframe) driven by command
  files. The classic sci-viz lane is also code-driven. **[3-0]**

---

## 8. Crypto-visualization vocabulary (Monero-specific, from the gap sweep)

Never previously surfaced in any doc. All [unverified] with direct source
quotes; verify before load-bearing use, but all four sources are first-party
and stable:

- **3Blue1Brown's Bitcoin lesson** teaches by *invent-it-yourself scaffolding*:
  start from a communal ledger among friends, progressively add signatures,
  distribution, proof-of-work — never top-down description. Visual devices:
  handwritten signature vs message-dependent bit string (signatures vary per
  document); proof-of-work as a "find leading zeros in the hash" game with
  explicit probability framing.
- **Anders Brownworth's interactive blockchain demo** scaffolds six stages —
  Hash → Block → Blockchain → Distributed → Tokens → Coinbase — from one
  cryptographic primitive up to a full distributed ledger. Core device: a live
  paired input/output widget (free-text data → real-time SHA-256) that lets
  learners *experience* determinism and avalanche behavior. Extended to
  public-key crypto in a second installment.
- **curves.xargs.org (Animated Elliptic Curve)** — a solo-built, acclaimed
  interactive ECC explainer in plain JavaScript + Canvas 2D +
  requestAnimationFrame, complete source open (syncsynchalt/animated-curves).
  Visual vocabulary: chord lines for point addition, tangents for doubling, a
  numerical grid over F61, animated double-and-add, step-by-step Alice/Bob
  exchange. Direct proof a solo creator ships an interactive crypto explainer
  with no engine, and a reusable vocabulary for Monero's ECC primitives.
- Together these three define a candidate Monero visual grammar: *scaffold
  from primitives, make every cryptographic property something the viewer
  watches change live, keep the math geometric.* Treatment choice remains
  Ryan's (decision gate §11).

---

## 9. Machine ground truth (re-verified 2026-07-17 against this Mac)

All confirmed by direct local checks:

- Blender 5.1.2 at `/Applications/Blender.app` (headless PNG-sequence lane
  already proven in-repo)
- DaVinci Resolve 21.0.2 (Studio) + proven Story IR → OTIO → Resolve spine
- ComfyUI at `~/ComfyUI` — 28 model subdirs, zero real weights (48K total):
  authoring/orchestration host only; heavy diffusion is hosted/rented
- No Unreal, Unity, or Godot installed
- manim, MolecularNodes, bpy NOT in the media-studio venv
- HyperFrames 0.7.61 functional via npx
- M1 Pro / 16 GB: no CUDA — local video diffusion out of scope by hardware

---

## 10. Trust ledger — what verification changed

**Refuted or corrected during the 07-17 citation pass:**

| Claim as originally written | Reality per source |
|---|---|
| Holmedal: "weeks of manual relinking in Cinema 4D" vs 1s in Houdini | **20 minutes per mesh** vs 1s — inflated ~3 orders of magnitude |
| Jared Owen: "about 200 hours of his own labor per video" | In no fetchable source; only "roughly two months" is supported |
| Branch Education: "1 researcher, 5 animators, a modeler; 40 script revisions; 2 months review" | Exists only in untranscribed podcast audio; now labeled [audio] |
| Hassenfratz: "his Node Ninja tool," "9-month course build," "Python and plugins" | Node Ninja is School of Motion's (he demos it); no timeline in any source; no Python/plugin evidence |
| Animagraffs: "100,000 frames," fine-grained tool list | Video-audio only; softened to verifiable categories |
| Mustard: "two-brother pipeline" | Sources say two-person; no sibling evidence |
| Vercidium: "three years to release" | Team's own words: "past 4 years," still open beta Dec 2022 |
| Giant Ant: 7-tool enumeration (Maya, Flash, VR, etc.) | None in cited sources; replaced with Grandin's actual "bizarre and messy mix of techniques" |
| blender-mcp: "open security issue" | Issue closed; the by-design arbitrary-exec surface is the real argument |
| ThinMatrix: engine advice attributed as his stated conclusion | Author inference; he still builds custom engines (Homegrown) |
| Bozesan: "Stable Diffusion and Runway with … After Effects" | Documented toolkit: SD + Blender + Magnific + Resolve |
| Trillo: "edited for six weeks" | Six weeks was the *whole project* |

**From the earlier panel runs:** "3B1B is 100% manim/fully automatable"
[REFUTED 0-3]; TheoremExplainAgent benchmark claims [CONTESTED across runs];
Kurzgesagt effort figures re-confirmed from the studio's own video (panels
failed, but source quotes are verbatim).

**Still wholly unverified (panel failures, not refutations):** all 25
gap-sweep claims (§4 studio evidence, §8 crypto vocabulary, Remotion/Canvas
Commons, Posy) and the resume's 11 unverified items (mostly restatements of
already-confirmed LTX/blender-mcp facts from second sources).

---

## 11. Translation to this studio + open decisions

**Proven lanes that match how the field works** (no adoption needed):
HyperFrames/SVG for deterministic 2D motion · scripted headless Blender for
spatial truth · Fusion for reusable overlays · Resolve/Story IR for assembly ·
hosted diffusion only when the chosen treatment needs it.

**Adopt only after a scene proves the need:** manim (math primitives; note
NC license on 3b1b scene code) · a game engine (only if an explorable or
performed real-time artifact becomes a deliverable) · blender-mcp (trust
boundary; repo-owned bpy already covers deterministic work) · MolecularNodes
(waits for the ochem lane).

**Candidate seam, unproven and Ryan-gated:** Blender depth/edge passes →
LTX-2.3 IC-LoRA (or Wan VACE). Plausible, packaged, untested locally; does
not decide that Monero uses diffusion.

**The six decision gates (all Ryan's, none researchable):**

1. Linear video only, or video + an explorable companion? —
   **ANSWERED 2026-07-17: both.** The Monero build ships a linear video plus
   an explorable interactive companion.
2. Which visual references define desired quality — and which traits are
   explicitly unwanted? — **OPEN**; Ryan needs examples in front of his eyes
   first (see `LANE-B-RESEARCH-BRIEFS.md` Brief 1, the reference gallery).
3. Which animation decisions do you perform directly; which does an agent
   execute from your direction? — deferred until there are artifacts to
   decide between.
4. How much recurring 2D illustration/character craft belongs in this studio?
   — deferred, same condition.
5. Is diffusion part of the Monero treatment, or merely available? —
   deferred, same condition.
6. What single bounded moment is the first two-substrate micro-test? —
   **ANCHORED 2026-07-17** to the original Monero explainer concept that
   started the project; the specific moment gets chosen once gate 2 has
   references in hand.

**Optional further research (only if wanted, in value order):** (a) verify the
25 gap-sweep claims (cheap, high value — the Monero vocabulary rides on them);
(b) profile Sebastian Lague/Primer/Ten Minute Physics (the sim-first school is
closest to your rabbit-hole model and currently discovery-only); (c) deep-dive
Matteo Spinelli's IPAdapter Plus materials (direct Scene Forge relevance);
(d) frame-study of chosen references — but that starts after gate 2.

---

## Appendix: raw material locations

- Pass-1 claims dump (102, with quotes): session scratchpad `all-claims.md`
- Pass-1 / resume / gap-sweep full outputs: session task files
  `wjitli2cn` / `wt32yluid` / `wevj02z3r` (media-studio session
  `6fd46f1f`, 2026-07-16/17)
- Discovery journal (31 creators): workflow `wf_d1092b74-07d/journal.jsonl`
- Citation-verification results (20 sections, 22 agents): write-on session
  `0220e86b` task `wbtees887`
- Working docs: `docs/LANE-B-RESEARCH.md`, `docs/LANE-B-CREATOR-METHODS.md`
