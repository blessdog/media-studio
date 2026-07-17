# Lane B — research briefs for handoff to another agent

*Written 2026-07-17. Self-contained: everything needed is in this file — no
access to prior sessions required. Execute briefs in the order given; each is
independently valuable if tokens run out.*

## Context (read first)

**Project:** media-studio Lane B — authored/synthesized educational video.
First build: a **Monero explainer** (the piece that started the project).
Producer/creative owner: Ryan. Machine: M1 Pro/16GB Mac (no CUDA — local
video diffusion out of scope; hosted APIs are the generation lane). Proven
stack: DaVinci Resolve Studio 21 + Fusion, Blender 5.1.2 headless, HyperFrames
(HTML→video), Story IR→OTIO→Resolve assembly, Replicate for hosted diffusion.

**Direction already decided (do not relitigate):**

- Gate 1 ANSWERED: the Monero build is a **linear video PLUS an explorable
  interactive companion** — both, not either.
- Gate 6 ANCHORED: the first micro-test moment comes from the original Monero
  explainer concept.
- Gate 2 (visual references) is OPEN and is what Brief 1 serves: Ryan needs
  concrete examples in front of his eyes before choosing a visual treatment.

**Prior research (already done — do NOT re-cover):** 3Blue1Brown/manim
lineage, Animagraffs' solo Blender pipeline and tooling, Jared Owen, Branch
Education, Kurzgesagt effort figures, the AE motion-design school (van Dijk,
Marriott, Ordinary Folk, Giant Ant, Colombo, Hassenfratz), Holmedal/Houdini,
CodeParade, Amit Patel, Quilez, Vercidium, Drago, ThinMatrix, blender-mcp,
bpy/headless Blender, ComfyUI LTX-2.3 + IC-LoRA control, MolecularNodes,
ChimeraX, Mickmumpitz's Blender→ComfyUI workflows, Trillo/Bozesan. Full
findings live in `docs/LANE-B-REPORT.md`, `docs/LANE-B-RESEARCH.md`,
`docs/LANE-B-CREATOR-METHODS.md` in the media-studio repo.

## Research standards (apply to every brief)

Hard rules learned from a verification pass that caught real fabrications:

1. **Never state a number without a fetchable text source.** If a figure
   exists only in podcast/video audio, label it **[audio]** and cite a
   timestamp if possible.
2. Prefer first-person sources (creator's own site, talk, repo, interview)
   over aggregators. Label each claim's evidence tier: first-person /
   secondary / inference.
3. Fetch every URL you cite; if it 404s, find a mirror or drop the claim.
4. Distinguish what a creator *says* from what you *infer* — inferences must
   be labeled as yours.
5. Deliverable format: one markdown report per brief, claims with inline
   citations, a "refuted/unfound" section listing what you looked for and
   could not support. No padding; the natural amount of material sets length.

---

## Brief 1 — Visual-reference gallery for the Monero explainer (PRIORITY: gates Ryan's decision 2)

**Objective:** put candidate visual treatments in front of Ryan's eyes so he
can choose the desired quality bar and name unwanted traits.

**Deliverable:** a gallery document: 6-8 candidate visual "schools," each with
3-5 specific reference works (exact video URLs + timestamps of representative
moments, or interactive-page URLs), one paragraph on what defines the look,
what it costs to produce (from prior research where known), and what it would
imply for a Monero piece. End with a blank scorecard Ryan can mark up:
desired / acceptable / explicitly unwanted per school.

**Schools to cover (at minimum):**

1. Geometric math animation (3Blue1Brown; Bitcoin video especially —
   3blue1brown.com/lessons/bitcoin — since it's the closest existing artifact
   to the Monero goal)
2. Technical 3D x-ray/cutaway (Animagraffs, Jared Owen, Branch Education)
3. Flat-illustration studio 2D (Kurzgesagt, Ordinary Folk-style explainer
   motion design)
4. Documentary-3D mixed media (fern, Melodysheep)
5. Interactive-first explainers (Anders Brownworth's blockchain demo at
   andersbrownworth.com/blockchain/hash; curves.xargs.org; Red Blob Games) —
   these double as references for the explorable companion
6. Live-coded/procedural aesthetic (Quilez/Shadertoy, The Art of Code)
7. Sim-first devlog aesthetic (Sebastian Lague, Primer) — overlaps Brief 3
8. Diffusion-hybrid looks (Mickmumpitz, Corridor, Trillo) — include only
   strong examples; note continuity/rejection labor

**Also collect:** any existing high-quality Monero/privacy-tech/cryptography
explainer videos (search: Monero explained, ring signatures visualization,
stealth addresses animation, zero-knowledge proof visualization, elliptic
curve animation). Note which visual school each uses and whether it succeeds.

---

## Brief 2 — Verify the 25 unverified gap-sweep claims (cheap, high value)

**Objective:** these claims were extracted with direct quotes but their
verification panels all failed on infrastructure. Several are load-bearing for
the Monero build. For each: fetch the source, confirm or refute, assign
[confirmed]/[refuted]/[unverifiable], note corrections.

**The claims (source in parentheses):**

*fern (join.com posting mirror: join.com/companies/electrify/14178235… and the
de.linkedin 3d-generalist posting, now dead — use mirrors):*
1. fern's 3D production is Blender-based; UE5 optional; no C4D/Maya/Houdini
   named for the 3D role.
2. fern runs a full traditional 3D pipeline in-house (modeling → compositing),
   composited into mixed-asset edits rather than fully-3D videos.
3. fern is multi-role: producers, editors, motion designers, creative leads +
   remote freelance 3D.
4. The fern/Simplicissimus shared 3D role requires professional Blender.
5. fern separates 3D from 2D/motion roles; 3D Generalist composites into
   final edits.

*Branch Education (blenderartists.org/t/worlds-smallest-devices-blender-project/1389553):*
6. "World's Smallest Devices" was produced entirely in Blender.
7. The post is authored by a Branch team member (Mike Radjabov / hanni5bal) —
   primary evidence, not fan speculation.

*Melodysheep (blendernation.com/2021/12/22/life-beyond-3-melodysheep…):*
8. Life Beyond 3 included a 54-second shot by external collaborator
   "UnknownDino" — Boswell commissions outside artists.
9. That shot was built almost entirely in a single Blender 2.93 file.

*Posy (michieldb.nl/info/):*
10. Posy edits and grades in DaVinci Resolve Studio.

*3B1B Bitcoin lesson (3blue1brown.com/lessons/bitcoin):*
11. Teaches via invent-it-yourself scaffolding (communal ledger → signatures →
    distribution → proof-of-work), not top-down description.
12. Digital-signature visual: consistent handwritten signature vs
    message-dependent bit string.
13. Proof-of-work visualized as "find leading zeros in the hash" game with
    probability framing.

*Brownworth demo (andersbrownworth.com/blockchain/hash):*
14. Six-stage scaffold: Hash → Block → Blockchain → Distributed → Tokens →
    Coinbase.
15. Core device: live paired input/output widget (free text → real-time
    SHA-256) demonstrating determinism and avalanche behavior.
16. Extended to public-key crypto (keys, signatures) in a second installment.

*Animated elliptic curves (curves.xargs.org; github.com/syncsynchalt/animated-curves):*
17. Built solo in plain JavaScript + Canvas 2D + requestAnimationFrame, no
    engine; source fully open.
18. Visual vocabulary: chord lines for point addition, tangents for doubling,
    grid over F61, animated double-and-add, Alice/Bob exchange.

*Kurzgesagt (youtube.com/watch?v=uFk0mgljtns — their own video):*
19. Pipeline is AE-based; C4D only a recent experiment (as of ~Feb 2020).
20. ~200 illustrated panels per average video, made in Illustrator.
21. ≥1,200 person-hours per video across all stages.

*Programmatic-web lane:*
22. Remotion's official docs state videos can be created purely by prompting
    an AI coding agent (remotion.dev/docs/ai/coding-agents).
23. Canvas Commons is an explicit fork of motion-canvas/motion-canvas
    (github.com/canvas-commons/canvas-commons).
24. Canvas Commons is actively maintained (commits late June 2026).
25. The Canvas Commons repo itself makes NO claim that Motion Canvas is
    unmaintained — that half needs upstream corroboration (check the
    motion-canvas repo's activity and maintainer statements directly).

---

## Brief 3 — Methodology profiles: the sim-first school

**Objective:** the "write a real simulation, then film it" school is the
closest model to Ryan's rabbit-hole-driven educational content and is
currently discovery-only. Produce citation-checked methodology profiles in the
style of `LANE-B-CREATOR-METHODS.md`: documented tools, what is
scripted/procedural vs hand-crafted (in the creator's own words where
possible), production timelines, and an "agent fit" inference clearly labeled
as inference.

**Subjects (discovery notes from the prior sweep):**

- **Sebastian Lague** — Unity/C#/HLSL "Coding Adventures"; narrated build
  logs; fluid sim, ray tracing, atmosphere, ecosystem videos show every failed
  attempt and fix on screen. Find: his stated workflow, how much video
  production (editing, narration) rides on top of the code, timelines per
  video, any published project source.
- **Primer (Justin Helps)** — Unity/C# agent simulations (evolution, game
  theory) with blob characters; ex-Khan Academy. Find: his simulation-to-video
  pipeline, the blob rig/tooling (he has discussed open-sourcing parts),
  production cadence, team size.
- **Ten Minute Physics (Matthias Müller-Fischer)** — NVIDIA principal
  researcher, PBD/XPBD co-inventor; browser-JS physics explainers with code
  on-screen. Find: his stated production method, how the browser demos are
  built/published (they are open on his site), and what a ~10-minute video
  costs him in time.
- **Optional if budget allows: Martijn Steinrucken (The Art of Code)** —
  live-coded Shadertoy tutorials; the teachable version of the Quilez school.

**Key question for all four:** what does the *video layer* add on top of the
artifact (sim/demo), and how automatable is each layer separately? This
directly informs the video-plus-companion architecture Ryan chose.

---

## Brief 4 — Explorable-companion substrate survey

**Objective:** gate 1 decided the Monero build ships an interactive companion.
Survey how the best interactive explainers are actually built and maintained,
so the studio can choose a companion substrate.

**Cover:**

1. The three verified-adjacent exemplars: Brownworth's blockchain demo,
   curves.xargs.org (source open — read it and describe its architecture),
   Red Blob Games (Amit Patel documents his diagram architecture at
   redblobgames.com/making-of/diagram-structure/ — summarize his
   controls → input → algorithm → output → visualization pattern).
2. Distill/explorabl.es lineage: is there a current community, standard
   tooling, or is everything hand-rolled?
3. Vanilla JS + Canvas vs framework (Svelte/Vue) vs notebook (Observable) —
   what do working solo authors actually use; maintenance cost over years.
4. Code-sharing potential: can one codebase drive both the video (via
   HyperFrames, which renders HTML/JS to video) and the interactive page?
   This is the studio's unique angle — assess seriously: same scene code,
   two outputs (deterministic render + live widget).
5. Crypto-specific interaction patterns: live hash widgets, key-pair
   playgrounds, ring-signature visualizers — find any existing open-source
   Monero-specific interactive teaching material (search: Monero ring
   signature demo, RingCT visualization, stealth address interactive).

**Deliverable:** substrate comparison + a recommendation of 2 candidates for
the micro-test, with the video/companion code-sharing question answered
concretely.

---

## Brief 5 — Matteo Spinelli (Latent Vision / cubiq) + IPAdapter Plus deep-dive

**Objective:** lowest priority. Spinelli authored the IPAdapter Plus ComfyUI
nodes that identity/style-conditioning pipelines depend on — directly relevant
to the studio's existing Scene Forge identity-conditioning lane. Profile: his
documented teaching/workflow method, the current state and maintenance of
IPAdapter Plus (repo activity, compatibility with current ComfyUI), what
identity conditioning can and cannot hold across shots per his own material,
and any stated best practices for style consistency in generated sequences.

---

## Explicitly deferred (do not research yet)

- **fern frame-study** — waits until Ryan answers gate 2 with references in
  hand; frame decomposition only makes sense against a chosen quality bar.
- **Two-substrate micro-test** — in-studio build work, not research; happens
  after gates 2 and 6 produce a chosen moment and references.
- Gates 3-5 (hand-vs-agent split, recurring illustration craft, diffusion in
  the treatment) — Ryan decides these when there are concrete artifacts to
  decide between.
