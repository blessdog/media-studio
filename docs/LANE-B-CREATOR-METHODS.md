# Lane B creator-methodology field map

*Recovery continuation, 2026-07-17. Companion to
[`LANE-B-RESEARCH.md`](LANE-B-RESEARCH.md). This is production-method
research, not a visual concept, script, analogy, or creative direction for the
Monero build.*

## What survived the failed run

The failed session was recoverable. Its creator-discovery stage found 31
people or studios with some public process evidence. The 3D-explainer search
then hit the session quota mid-query, and all 14 queued methodology profiles
plus the synthesis failed before doing work. Two earlier research streams also
left their source journals and extracted claims intact.

This continuation resumes from those artifacts rather than treating the first
memo as the final answer. It also corrects that memo's main sampling error.

> **Citation audit, 2026-07-17 (evening):** every cited section of this memo
> was adversarially re-checked against its sources by a 22-agent verification
> pass — the verification stage that the quota failure killed in every earlier
> run. Outcome: 2 sections fully sound, 14 with minor detail corrections, 4
> with unsupported numbers; one claim refuted outright (a "weeks vs. one
> second" Houdini comparison that the source states as *20 minutes* vs. one
> second). All corrections are applied inline. Numbers that exist only in
> unpublished podcast/video audio are now labeled as such rather than stated
> as text-verifiable facts. The machine-state section was re-verified against
> this Mac on the same date: all claims confirmed.

## The correction: code is one kind of leverage, not the whole field

The earlier headline — "the winners drive their tools with code, and the code
is the asset" — was too broad. It accurately describes 3Blue1Brown,
Animagraffs, Houdini proceduralists, shader artists, interactive-web authors,
and custom-engine creators. It does **not** accurately describe the whole
field.

High-end explainer and motion-design work has at least two successful
production economies:

1. **Code/procedure as medium.** The scene is a Python program, shader,
   Geometry Nodes/Houdini graph, browser application, or game-engine system.
   Iteration happens by changing rules and parameters.
2. **Designed and performed motion.** The work passes through message,
   references, styleframes, storyboard, animatic, blocking, hand-tuned
   keyframes or drawings, compositing, sound, and repeated critique. Scripts,
   expressions, rigs, and plugins remove repetition, but do not author the
   movement.

Across this sample, many successful workflows are hybrid. Scripts, rigs, and
procedural systems may generate or transform motion, but human authors still
set communicative intent, constraints, timing targets, and acceptance
criteria. The more useful generalization is:

> **The repeatable system is an asset.** It may be code, a rig, a template, a
> scene graph, a disciplined project structure, a review process, or a practiced
> manual technique. Automation should remove repetition so more time reaches
> the decisions; it should not erase the decisions that constitute authorship.

The practical question is not "code versus human touch." It is which
operations are repeatable enough to specify and verify, which judgments Ryan
wants to make directly, and which work an agent or collaborator can execute
without obscuring explanatory or aesthetic accountability.

## Evidence policy

- **High confidence:** creator-authored breakdown, official process page,
  public source/project file, or detailed first-person interview.
- **Medium confidence:** role posting, collaborator breakdown, or case study
  that proves part of a pipeline but not the whole pipeline.
- **Discovery only:** the work is relevant, but public process evidence is too
  thin to carry an architecture decision.
- "Agent fit" below is an inference from the documented method, not a claim
  made by the creator.

## Field map

| School | Representative practitioners | Primary substrate | Where leverage lives | Where craft remains |
|---|---|---|---|---|
| Programmatic animation | 3Blue1Brown, Inigo Quilez | Python/Manim, GLSL/Shadertoy | Reusable abstractions, live code, deterministic render | Explanatory decomposition, composition, pacing, visual selection |
| 2D/mixed motion design | Sander van Dijk, Ben Marriott, Ordinary Folk, Giant Ant, Emanuele Colombo | After Effects, Illustrator/Photoshop, occasional C4D/Maya | Expressions, rigs, plugins, palettes, precomps, templates | Message, styleframes, keyframe curves, transitions, character performance, polish |
| 3D technical explanation | Animagraffs, Jared Owen, Branch Education; fern (medium-confidence role evidence) | Blender; sometimes CAD and compositing tools | Python, Geometry Nodes, asset libraries, headless render, reusable labels | Research, modeling choices, camera, lighting, keyframes, legibility, review |
| Procedural/simulation motion | Simon Holmedal, Vercidium | Houdini, C#/OpenGL, custom engines | Node graphs, simulations, data-driven systems, benchmarks | Choosing the system, parameter tuning, framing, edit, explanation |
| Interactive/real-time explanation | Amit Patel, CodeParade, Lorenzo Drago, ThinMatrix | Browser JS/Canvas/WebGL, Unity, Unreal | Direct manipulation, hot reload, custom render/tooling, real-time iteration | Interaction design, level/scene design, camera performance, teaching sequence |
| Generative hybrid | Paul Trillo; Mickmumpitz and Albert Bozesan (discovery only) | ComfyUI/video models plus Blender/AE/editing | Batch generation, control graphs, structural conditioning | Prompt authorship, curation, continuity, shot direction, compositing, rejection |

## What motion-design practitioners actually do

The common pipeline is not "prompt to finished animation." It is:

**message/brief → references and concept variants → storyboard/styleframes →
animatic → blocking/base motion → timing and performance refinement →
compositing/texture → audio integration → delivery/versioning**

### Sander van Dijk — tools accelerate iteration

After Effects remains central, with Illustrator and occasional Cinema 4D.
Van Dijk's own tools link palettes, recall textures/effects/keyframes, and
stack multiple strokes on a single path. His project method moves from references and
styleframes into an animatic/boardamatic, an intentionally rough foundation,
sequence and transition tests, approval, then polish. The tools make thinking
and iteration faster; they do not choose the story pulse or final transition.
([first-person interview](https://schoolofmotion.com/blog/sander-van-dijk-podcast),
[official tools](https://www.sandervandijk.tv/tools),
[official case study](https://www.sandervandijk.tv/material-design))

### Ben Marriott — fundamentals survive the plugins

Marriott's published workflow uses After Effects, Illustrator, Ease-Copy, and
Duik. It starts from the intended result, works backward through many ideas and
approved boards, organizes assets, blocks movement and arcs, refines graph-
editor timing, then adds transitions, rigs, texture, and polish. He attributes
a major skill improvement to temporarily dropping plugins and learning manual
timing; automation without animation literacy had created a ceiling.
([official course](https://www.benmarriott.com/mastermotiondesign),
[first-person profile](https://elements.envato.com/learn/ben-marriott))

### Ordinary Folk / JR Canest — message before medium

Ordinary Folk publishes a four-stage process: **Message → Design → Animation
→ Audio**. The design stage chooses among 2D, 3D, vector, cut-out, and
hand-drawn treatments and produces sketches/storyboards. Animation then adds
nuance, personality, and pixel-level refinement; sound is considered from the
start and composers enter once an animatic exists. JR's documented toolchain
includes Animate, Audition, After Effects, Illustrator, and Photoshop, with
deliberate hand keyframing; the limited-scripts caution comes from an
interview where he weighs hand-animating against "fumbling through
expressions."
([official process](https://www.ordinaryfolk.co/process),
[official team](https://www.ordinaryfolk.co/about),
[course curriculum](https://www.learnsquared.com/courses/motion-design),
[tips interview](https://lesterbanks.com/2017/07/jr-canest-shares-amazing-tips-effects/))

### Giant Ant — technique follows the intended feeling

Giant Ant has mixed After Effects, cel/frame-by-frame animation, and what
Grandin calls a "bizarre and messy mix of techniques" across projects. The
studio starts from the intended look and feeling, then works backward to the
technique. Its leverage is a team of dedicated specialists — real illustrators
and classical animators, not generalist animators designing as they go — not
one universal automation layer. In the School of Motion interview Jay Grandin
says the work they value required enough time to get it wrong more than once.
([team](https://www.giantant.ca/about),
[first-person interview](https://medium.com/thenextgag-interviews/jay-grandin-partner-creative-director-giant-ant-5da2818b330b),
[process interview](https://schoolofmotion.com/blog/jay-grandin-podcast-podcast))

### Emanuele Colombo — constrained systems plus trial and error

Colombo builds simple-shape characters in Illustrator, prepares them for
After Effects, and plans transitions as morphs or match cuts that can be
decomposed into manageable steps. Handy shapes, expressions, and few-keyframe
constructions create leverage. Palette, character appeal, transition
readability, and extensive trial and error remain manual. A published raw
recording preserved roughly 1.5 hours of unplanned experimentation for one
small animation — useful evidence that the discarded tests are part of the
craft.
([course](https://motiondesign.school/courses/motion-secrets-with-emanuele-colombo/),
[process description](https://lesterbanks.com/2019/09/watch-emanuele-colombo-animate-a-character-in-ae/))

### EJ Hassenfratz — automate setup, not the teaching decision

Hassenfratz's Cinema 4D/Redshift workflow uses naming conventions, reusable
assets, non-destructive animation, Takes, render tokens, and batch output.
School of Motion's free Node Ninja plugin, which he demos, can build Redshift
materials from PBR texture folders, assign the correct color spaces and normal
handling, and organize the node graph. The time saved is operational. His
documented creative loop still starts from a real design problem, develops a
polished visual application, and teaches why the technique matters rather than
merely reproducing an effect. Cinema 4D Insider is a six-module professional
course — reusable teaching assets are themselves substantial authored work.
([first-person interview](https://schoolofmotion.com/blog/ej-hassenfratz-eyedesyn-podcast),
[workflow course](https://schoolofmotion.com/courses/cinema-4d-insider),
[Node Ninja](https://www.schoolofmotion.com/node-ninja))

## What 3D technical explainers actually do

### Jared Owen — a direct automation-versus-craft answer

Owen's documented sequence is research → 3D modeling → script/voice →
animation → narration sync → music → rough render → family-and-friends
critique → final render (subject experts are consulted during research, not at
render review). Historically a render took 20–100 hours; one Apollo series
took six months. His current pace is roughly two months per video, now
supported by contractors, purchased models, subject experts, and several
render machines. Python and Animation Nodes automate repeated operations, and
he has begun asking AI to write Blender scripts, with mixed results. He
identifies research, story, and making the 3D explanation self-evident as the
hard part — and found ChatGPT as likely to get important facts wrong as right,
calling it a no-go for research for now.
([creator-authored breakdown](https://www.blendernation.com/2018/11/19/meet-the-artist-jared-owen/),
[vidIQ podcast interview](https://www.youtube.com/watch?v=R1U6rpw7B9k),
[written interview](https://diginomica.com/telling-3d-stories-about-things-learnings-jared-owen-provide-digital-twins-and-industrial-metaverse))

This is the closest public answer to Lane B's question: automate operations,
not the comprehension test or the creator's recognizable point of view.

### Branch Education — procedural assets inside a laborious build

A Branch artist's breakdown says *World's Smallest Devices* was fully modeled,
rigged, and animated in Blender. It used about 45 models, extensive Geometry
Nodes, a purchased-then-modified PCB generator, a procedural ruler, manual
scene rescaling across orders of magnitude, and careful collection management
to survive render-memory limits. Founder Theodore Tablante describes a much
larger labor system than the finished procedural look suggests: a small team
of animator/modeler contributors plus a separate professional narrator, with
multi-stage review across storyboard, model, animation, accuracy, aesthetics,
and clarity; one complex video (transistors) was "in the works for over a year
and a half." (Precise team counts and per-stage timelines heard in the podcast
audio have no published transcript, so they are not stated here as
text-verifiable facts.) Automation makes the geometry manageable; it does not
collapse the production into one click.
([artist breakdown](https://blenderartists.org/t/worlds-smallest-devices-blender-project/1389553),
[founder interview, audio-only](https://www.inspiringcomputing.com/2107763/episodes/15238107-animating-engineering-with-teddy-the-mind-behind-branch-education),
[hiring goals](https://www.patreon.com/brancheducation/about))

### Animagraffs — private tooling as the solo-studio multiplier

Jacob O'Neal's Blender add-on suite (built over roughly two years) covers
specialized modeling tools, blend-file management, a transparency system,
efficient rendering workflows, and a custom label system; the finer-grained
pieces named in his workflow talk (data-driven labels, collection fades,
headless multi-GPU rendering) live in the video itself. That is unusually
agent-friendly operational glue. His actual sequence still starts with deep
research across patent drawings, engineer/pilot/mechanic forums, and library
books, more than a month on some base models, then substantial manual
animation and review work across long-form productions spanning tens of
thousands of frames. This is the strongest evidence for the original "code is the asset"
thesis, but even here the code supports explanation rather than replacing it.
The strategic lesson is not "automate the video." It is "capture each repeated
production pain as a reusable studio tool."
([first-person production interview](https://technicalillustrators.org/2019/08/animagraffs-by-jacob-oneal/),
[first-person workflow talk](https://www.youtube.com/watch?v=OkadsUTl1Pw),
[official about page](https://animagraffs.com/about/))

### Simon Holmedal / Panoply — proceduralism begins after the metaphor

Holmedal works as procedurally as possible in Houdini, Redshift, and Nuke,
using attributes, Python, PDG, and reusable solvers. A variation that had
required about 20 minutes of manual relinking per new mesh in Cinema 4D could
be reapplied in Houdini in about a second; an ESPN package used a PDG network
to manage information, respond to feedback, and adapt its "Shimmer" look to
shapes like the trophy and team logos. But the pipeline begins with the
product or client problem, a visual metaphor, and several days of small
R&D/styleframe tests.
Composition, lighting, hierarchy, edit, and the judgment that a solver is
saying the right thing remain handmade.
([first-person interview](https://schoolofmotion.com/blog/simon-holmedal-houdini-podcast),
[Panoply PDG case study](https://www.sidefx.com/community/nba-finals-panoply/),
[process interview](https://motionographer.com/2016/05/02/interview-man-vs-machines-simon-holmedal/),
[studio profile for Redshift/Nuke](https://www.maxon.net/en/article/on-the-edge-of-worlds))

### fern — medium-confidence role evidence, not a blueprint

Public evidence remains thinner. A 2025 fern/Simplicissimus 3D-generalist
posting required Blender and treated Unreal Engine 5 as optional; it described
modeling, texturing, rigging, lighting, animation, and compositing, with the
artist collaborating with producers, editors, and motion designers. The
Electrify partnership places fern inside a larger production network but does
not disclose its per-video method. Combined, the evidence supports only a
partial Blender-centered, multi-role picture. Treat fern as a quality
reference, not as a recovered solo blueprint.
([official studio site](https://www.watchfern.com/jobs),
[Electrify announcement](https://www.electrify.video/news/electrify-expands-into-investigative-journalism-with-partnership-in-leading-documentary-channels),
[archived role, posting mirror](https://join.com/companies/electrify/14251023-3d-generalist-youtube-channel-fern-and-simplicissimus))

### Mustard — a useful handcrafted counterexample

Mustard's 2020 first-person account describes a two-person pipeline built
around research, SketchUp aircraft models, Lumion renders, After Effects, and
licensed media. Research, writing, modeling, and music occupied roughly the
first four weeks; voice, rendering, motion graphics, assembly, and revision
filled roughly weeks four through six alongside full-time jobs. They said a
two-week cadence was possible only by accepting a quality loss. Public
evidence of custom scripting is thin. The case matters because polished
technical explanation can come from disciplined linear craft rather than a
code-native asset system.
([first-person AMA](https://www.reddit.com/r/watchnebula/comments/g7vsi5/hey_its_mustard_im_doing_an_ama/),
[production description](https://www.patreon.com/MustardChannel/about))

## What real-time and interactive creators add

The game-engine research does not say "install Unreal and animation becomes
easy." It says real-time tools are valuable when the teaching experience
depends on exploration, immediate feedback, spatial performance, or a world
whose rules must run continuously.

### CodeParade — engine leverage comes with engine work

*Hyperbolica* was solo-led but used specialist contributors for 3D art
(João Kalva) and music/sound (Phil K.). Its stack combined Unity, Blender
(plus add-ons for existing editors), editor scripts, custom shaders/rendering
and physics, and a custom dialogue scripting language for its ~1000 NPCs. The method was: prove the geometry, choose an existing
engine, customize only where non-Euclidean invariants demand it, then use tile
reuse and procedural fill to contain content cost. Level design often happened
inside the running game because a flat editor could not display the world
correctly. Geometry transforms, repeated tiles, lesser regions, and dialogue
execution were automated; level design, minigames, character writing, art,
mathematical compromises, and feel were not. Public devlogs to release span
roughly 21 months.
([first-person Q&A](https://www.gamedeveloper.com/design/q-a-the-mind-bending-geometry-of-non-euclidean-experiment-hyperbolica-),
[modeling breakdown](https://www.youtube.com/watch?v=spDA3hPJf6E),
[Unity/tooling breakdown](https://www.youtube.com/watch?v=rBr-0bHQfxc),
[dialogue-system devlog](https://www.youtube.com/watch?v=DlL_20x0QH8))

### Amit Patel / Red Blob Games — interactivity is the explanation

Patel's solo interactive explainers combine prose, direct manipulation, and
live diagrams built with browser technologies from D3/Vue to SVG, Canvas, and
WebGL. His useful abstraction is **controls → input → algorithm → output →
visualization**. He sketches the teaching sequence, builds disposable diagrams
with full redraw/recomputation, and only adds dependencies, caching, or shared
abstractions when measurements justify them. A major tutorial can take one to
five months; his small /x/ experiments are loosely timeboxed to about a week
(pages numbered by year and week on [his blog](https://simblob.blogspot.com/)). For procedural generation he first makes representative output by
hand, defines what must always happen, must never happen, and may vary, then
encodes those constraints. Automation produces state and interaction; the
teaching order, examples, hierarchy, and scope remain editorial work.
([official method index](https://www.redblobgames.com/),
[diagram architecture](https://www.redblobgames.com/making-of/diagram-structure/),
[A* making-of](https://www.redblobgames.com/pathfinding/a-star/making-of.html),
[first-person interview](https://www.randroll.com/interview_amit_patel/))

### Inigo Quilez — procedural pixels still require a painter

Quilez's shader method begins with an intended image and a simple analytic
surface, then layers noise/FBM, lighting, atmosphere, composition, modeled
details, color, highlights, and clouds while tuning in real time. Nearly every
pixel is procedural, yet the equations, placement, parameters, composition,
and stopping point are hand-authored — effectively painting with mathematics.
In the recorded build session he presents the landscape shader ("Rainforest",
originally built in 2016); the time figures attached to it — days for the
shader, months for the explanatory videos — exist only in video/interview
audio, not in any text source, so treat them as sourced-from-audio. The
asymmetry they describe still matters if it holds: deterministic image
generation may be fast while articulation, edit, and pedagogy remain slow.
([complete build](https://www.youtube.com/watch?v=BFld4EBO2RE),
[editable shader](https://www.shadertoy.com/view/4ttSWf),
[first-person 2025 interview](https://www.youtube.com/watch?v=F1ax1iJTHFs))

### Vercidium — benchmark the representation, handcraft the threshold

The two-brother *Sector's Edge* team split a custom C#/OpenGL engine from the
models, animation, and painted content. Their published method states a
measurable goal, isolates a representative benchmark, changes one structural
issue at a time, then remeasures. A voxel-meshing pass fell from 5.15 ms to
0.89 ms and then 0.48 ms through algorithm, layout, allocation, and buffer
changes. Particle work likewise compared realistic operation/storage
combinations and accepted lower precision only when the visual difference was
imperceptible. The reusable engine and profiler are automation assets; a human
still chooses the performance budget, visual threshold, weapon feel, UX, and
art. The team spent about four years creating the game; extracting the
reusable engine later took three weeks and was verified by reinserting it.
([voxel optimization](https://vercidium.com/blog/voxel-world-optimisations/),
[further optimization](https://vercidium.com/blog/further-voxel-world-optimisations/),
[particle-system breakdown](https://vercidium.com/blog/opengl-particle-systems/),
[team interview](https://gamerant.com/sectors-edge-interview-fps-building-game-design-family-engine-innovations/),
[engine extraction](https://www.patreon.com/vercidium/posts/engine-89442793))

### Lorenzo Drago — real-time rendering enables performed camera work

Drago's solo UE5 station project used references and camera matching, Blender
scale and modular modeling, Substance Painter, Lumen, Blueprints, VR camera
tracking, Take Recorder, image-sequence rendering, and Adobe finishing. He
manually performed camera takes while seeing the finished world in real time,
then recreated the motion in physical space to record matching audio. Lumen,
modular snapping, bakes, masks, and reusable materials accelerated feedback;
proportions, grime, lighting balance, composition, camera performance, and
sound remained authored. The build took a little over one month despite
learning several parts of the stack during production.
([first-person project breakdown](https://gamesartist.co.uk/etchu-daimon-station/),
[Unreal case study](https://www.unrealengine.com/tech-blog/environment-artist-explains-how-he-created-near-photo-realistic-train-station-using-ue5))

### ThinMatrix — build the minimum system, then add feel

Karl Wimble publishes filmed, every-step feature walkthroughs — the cited one
covers his current game *Homegrown*, not *Equilinox*: spec → minimal
implementation → Blender assets → effects and sound → polish → playtest. Read
the split below as this memo's synthesis of those videos, not his stated
taxonomy: engine systems and procedural layers are automated, while models,
system purpose, feel, balance, and acceptance thresholds are crafted.
*Equilinox* took roughly three years from first devlog to release. The
engine lesson is an inference from his trajectory, not his stated advice —
he still built a custom engine for *Homegrown* — but for Lane B it reads:
custom-engine authorship earns its cost only when it is itself part of the
creative purpose.
([feature-development breakdown](https://www.youtube.com/watch?v=c18rZoi46kc),
[ten-year retrospective](https://www.youtube.com/watch?v=FStOT4pP2tc),
[official press kit](https://www.equilinox.com/presskit/))

## What diffusion-hybrid creators add

Diffusion is a stochastic asset generator inside a production system, not a
production system by itself.

The first two practitioners below are discovery leads from the recovered
sweep, not load-bearing methodology profiles; their original source packets
did not receive the same post-failure verification as the profiles above.

- Mickmumpitz publishes downloadable ComfyUI graphs for controllable character
  and video workflows. The reusable node graph is automatable; source
  selection, control inputs, prompting, curation, and edit remain authored.
- Albert Bozesan has documented two-person work (*TARMAC*, with Robert
  Sladeczek) combining Stable Diffusion with substantial Blender work, plus
  Magnific and DaVinci Resolve in the published toolkit
  ([bio](https://albertbozesan.com/), [toolkit](https://tarmacshow.com/)).
  "AI-made" still contains traditional layout, compositing, and sound labor.
- Paul Trillo reportedly generated roughly 700 Sora clips for *The Hardest
  Part* and selected about 55; the whole project — prompting, generating, and
  editing — took roughly six weeks. The labor moved
  from rendering each frame to directing prompts, generating coverage,
  rejecting most output, and constructing continuity.
  ([first-person process interview](https://nofilmschool.com/ai-music-video),
  [production report](https://www.latimes.com/entertainment-arts/business/story/2024-05-02/first-major-music-artist-uses-openai-sora-to-create-music-video))

For this studio, Prompt Brain remains a human-authorship gate. An agent may run
the graph, preserve parameters/provenance, and prepare comparisons; Ryan owns
what is asked for and which result means anything.

## Discovered but unprofiled

The discovery sweep found 31 creators; the profiles above cover about half.
The rest are named here so the field map is honest about its coverage. Each is
a legitimate profile candidate if their school becomes load-bearing for a
chosen treatment (discovery notes only — none of these were methodology-
researched):

- **Sebastian Lague** — Unity/C#/HLSL "Coding Adventures"; narrated build logs
  where every failed attempt and fix is shown on screen.
- **Primer (Justin Helps)** — Unity/C# agent simulations (evolution, game
  theory); the closest model for "write a real sim, then film it."
- **Captain Disillusion (Alan Melikdjanian)** — AE/Blender VFX-literacy
  explainers; his pipeline (~2 weeks scripting, ~4h footage per 2-min video)
  is unusually well documented.
- **Corridor Digital (Niko Pueringer / Wren Weichman)** — live-action + Unreal
  + Stable Diffusion vid2vid hybrids; publishes its own behind-the-scenes for
  everything.
- **Entagma (Schwind & Casasola Merkle)** — the reference Houdini educator
  channel; every video a from-scratch procedural build.
- **Steven Knipping (Applied Houdini)** — ILM destruction TD; film-VFX
  simulation process made teachable.
- **Ten Minute Physics (Matthias Müller-Fischer)** — NVIDIA physics researcher
  (PBD/XPBD co-inventor) doing browser-JS simulation explainers.
- **Martijn Steinrucken (The Art of Code)** — live-coded GLSL/Shadertoy
  tutorials; the teachable version of the Quilez school.
- **Andrew Kramer (Video Copilot)** — 160+ free AE tutorials plus plugin
  authorship (Element 3D, Optical Flares).
- **Matteo Spinelli (Latent Vision / cubiq)** — author of the IPAdapter Plus
  ComfyUI nodes most identity-conditioning pipelines depend on; directly
  relevant to this studio's identity-conditioning lane.
- **Purz (Purz Beats)** — ComfyUI/AnimateDiff motion-graphics educator;
  publishes workflow templates on comfy.org.
- **Martin Nebelong** — VR/3D sculpting driving real-time diffusion (Krea);
  a strong process model for 3D-plus-generative work.
- **Dave Clark (Promise Studios)** — AI narrative shorts with fully documented
  toolchains, scaled into a hybrid AI/VFX studio.
- **Clinton Jones (pwnisher)** — Unreal/C4D cinematic renders and community
  render challenges; process-forward by format.
- **Mickmumpitz and Albert Bozesan** appear above as diffusion-hybrid leads.

(3Blue1Brown appears in the field map on the strength of the companion memo's
verified pass-1 claims — see `LANE-B-RESEARCH.md`, which cites
github.com/3b1b/videos — not this document's own citations.)

## The automation-versus-craft boundary

The fit ratings below are planning hypotheses inferred from practitioner
workflows, not demonstrated capability on this studio's stack. Hard-surface
assembly, camera/lighting variants, and keyframe mechanics must earn their
ratings in the micro-test before being treated as proven.

| Production activity | Agent/system fit | Required human gate |
|---|---|---|
| Source search, transcript extraction, claim cross-checking | High, with citations and contradiction checks | What the piece is trying to teach; final factual accountability |
| File naming, asset intake, project setup, versioning | High | None beyond exceptions |
| Repeated Blender/AE operations, conversions, render orchestration | High | Approve the reusable rule once |
| Parametric geometry, labels, graphs, simulations | High when the rule is explicit | Decide whether the rule communicates the idea |
| Rough layout, boards, animatic variants | Medium-high and reversible | Select the visual language and sequence |
| Hard-surface/diagram scene assembly | Medium-high with constraints | Accuracy, silhouette, staging, camera, legibility |
| Hero modeling, organic form, character appeal | Medium-low | Direct modeling/sculpting or specialist craft |
| Keyframe mechanics and inbetweening | Medium | Timing, weight, acting, rhythm, transition logic |
| Camera and lighting setup | Medium-high for variants | Taste; sometimes a performed camera take |
| Diffusion generation | High-volume | Prompt authorship, curation, continuity, rejection |
| Structural/pixel/audio QA | High | Human visual and listening verdict |
| Compositing, encoding, delivery, provenance | High | Final creative approval |

Candidate review gates for Ryan's approval are:

1. **Truth/message lock** — Ryan decides what must be understood.
2. **Visual-language lock** — Ryan chooses the treatment and references.
3. **Styleframe lock** — no costly motion before representative frames pass.
4. **Animatic lock** — timing, sequence, and audio relationship pass in rough
   form.
5. **Motion/performance review** — the human-touch pass occurs before final
   render.
6. **Final visual/audio verdict** — mechanical verification is necessary but
   not sufficient.

## Translation assessment against the actual machine

Machine state rechecked 2026-07-17:

- Blender 5.1.2 is installed and the repo's headless PNG-sequence lane is
  already proven.
- Resolve Studio 21.0.2 and the Story IR → OTIO → Resolve assembly spine are
  proven.
- Fusion templates are proven as reusable graphics/compositing assets.
- HyperFrames is available as the existing code-native HTML/SVG/video lane.
- ComfyUI is installed but its model directories contain configs and
  placeholders, not usable model weights. The local M1 Pro/16 GB machine is an
  authoring/orchestration host; heavy video diffusion belongs on a hosted API
  or rented GPU.
- No Unreal, Unity, or Godot installation was found. Manim, MolecularNodes,
  and `bpy` are not installed in the repo virtual environment.

### Already-proven options to test first

- **HyperFrames/SVG/Canvas for deterministic 2D motion** when code-native
  layout, text, paths, or interactive-web idioms fit the scene.
- **Blender/bpy for spatial truth**: geometry, cameras, occlusion, depth,
  material/light passes, and repeatable 3D scenes.
- **Fusion for reusable overlays and compositing**, not as the assumed primary
  authoring surface for every scene.
- **Resolve/Story IR for assembly, sound, review, and delivery.** The existing
  spine is the current default hypothesis; change it only if the micro-build
  exposes a concrete incompatibility.
- **Hosted diffusion only when Ryan's chosen treatment needs it**, with
  deterministic passes retained separately.

### Do not adopt yet

- **A game engine.** CodeParade and Drago justify one when the artifact needs a
  continuously running world, direct interaction, or performed real-time
  camera. A linear explainer alone does not justify the new toolchain. The
  studio can borrow game-development methods without installing Unreal.
- **Manim.** It is valuable for specialized mathematical primitives and access
  to public 3Blue1Brown scene code (note: the 3b1b/videos repo is CC BY-NC-SA
  — scene code can inform but not be commercially reused verbatim), but
  overlaps with the existing HTML/SVG lane. Install only if a chosen scene proves the math primitives save more
  work than another substrate.
- **blender-mcp.** Direct repo-owned `bpy` scripts already satisfy the
  deterministic pipeline. MCP could be an exploration surface, but it executes
  arbitrary Blender Python by design (per its README) and is a trust-boundary
  decision, not a default dependency.
  ([project](https://github.com/ahujasid/blender-mcp),
  [reported RCE issue, since closed](https://github.com/ahujasid/blender-mcp/issues/201))
- **MolecularNodes for the Monero build.** It remains a strong future adoption
  for the ochem lane, not a reason to expand the first build's dependency
  surface.

### Candidate seam, still unproven and Ryan-gated

ComfyUI's official LTX-2.3 workflow supports structural control from depth,
pose, and edges. A Blender-to-LTX handoff is therefore plausible, but neither
the handoff nor its output quality has been tested locally. It does **not**
decide that the Monero piece should use diffusion or establish a production
seam.
([official ComfyUI workflow](https://docs.comfy.org/tutorials/video/ltx/ltx-2-3))

## Gap analysis: adopt, adapt, improvise, overcome

### Adopt only after a scene proves the need

- A maintained math-animation library if the chosen visual grammar depends on
  its primitives.
- A real-time engine if an explorable or performed world becomes a deliverable,
  not merely an inspiration.
- MolecularNodes when the molecular-visualization project opens.
- Specialist human craft when a selected treatment requires sustained
  illustration, character animation, or hero modeling that cannot be encoded
  economically.

### Potential adaptations after the first scene exposes repeated pain

- When a repeated production pain appears in the first scene, capture it as a
  narrowly scoped repo-owned helper rather than prebuilding a general system.
- Treat HyperFrames compositions, Fusion templates, Blender scenes, control
  graphs, and their source as first-class registry assets with provenance.
- Preserve the existing spend gate and human visual verdict for generative
  work.

### Improvise after the first micro-build

- A small substrate-neutral scene manifest only after one real scene exposes
  the common inputs and outputs. Do not design a universal animation IR in the
  abstract.
- Automated contact sheets, representative-frame review, and A/B render
  comparisons so visual critique is fast and concrete.
- A render-pass handoff from Blender to the selected compositing/generative
  lane, frozen to disk with parameters and source hashes.

### Overcome through process, not another tool

- The missing creative grammar: references, density, pacing, camera language,
  typography, material/texture policy, and acceptable hand-crafted touch.
- The accuracy burden: every truth-bearing element needs a source and a visual
  comprehension check.
- The critique deficit of a solo shop: scheduled styleframe, animatic, motion,
  and final reviews replace the studio room that Giant Ant and Ordinary Folk
  have by default.
- The temptation to generalize too early. Animagraffs and Jared Owen built
  leverage in response to repeated pain across real projects.

## Pickup plan for the Monero first build

This is a planning sequence, not a preselected visual concept.

1. **Ryan dialogue: define the artifact.** Decide linear video only versus an
   explorable companion; choose reference work; name the desired and rejected
   qualities; decide where Ryan wants direct hand work; choose one bounded
   truth-bearing moment for a test.
2. **Frame-study the chosen references.** Decompose representative shots into
   substrate, camera, layout, motion, transition, sound, likely manual work,
   and likely reusable system. fern can be one reference, not the only one.
3. **Run a two-substrate micro-test.** Build the same Ryan-selected moment in
   the two most plausible existing substrates using placeholder styling. Judge
   iteration speed, precision, editability, render cost, and how directly Ryan
   can art-direct it.
4. **Lock a minimal Lane B scene contract.** Only after the test: source files,
   declared inputs, fps/size/duration, deterministic seed or parameters,
   render passes, audio assumptions, provenance, and the artifact handed to
   Story IR.
5. **Complete one production scene.** Take it through styleframe, animatic,
   motion, compositing, Resolve assembly, and visual/audio verdict. Capture
   repeated pain as tools; leave one-off craft as one-off craft.
6. **Generalize after evidence.** Decide whether Manim, a game engine,
   blender-mcp, cloud ComfyUI, or specialist collaborators actually earned a
   place. Then write the Lane A/Lane B split into `ARCHITECTURE.md` with Ryan's
   approval.

## Decision gates still open

- Linear video only, or video plus an explorable learning artifact?
- Which visual references define Lane B's desired quality — and which traits
  are explicitly unwanted?
- Which animation decisions does Ryan want to perform directly, and which
  should an agent execute from Ryan's conversational direction?
- How much recurring 2D illustration/character craft belongs in this studio,
  if any?
- Is diffusion part of the selected Monero treatment or merely an available
  substrate?
- What single bounded moment is the first micro-test?

No architecture, tool installation, paid generation, or Monero visual concept
should be locked before those questions are answered in dialogue.
