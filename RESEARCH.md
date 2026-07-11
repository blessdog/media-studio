# AI-Driven Media Studio: Research Report & Architecture Plan

**Date:** 2026-07-11
**Method:** Deep-research workflow — 5 search angles, 23 sources fetched, 112 claims extracted, 25 adversarially verified (3 independent votes each) before the session usage limit cut verification short. Claims below are tagged **[VERIFIED]** (survived 2-3/3 adversarial votes, often with live code/API checks), **[REFUTED]** (killed by verifiers — listed because the correction matters), or **[UNVERIFIED]** (single-source, verification agents died on the usage limit; source quality noted).
**Raw evidence:** `research-raw-claims.md` in this directory (per bible §5.2: read source, not summary).

---

## Part 1 — DaVinci Resolve scripting: ground truth

### What's true

- **[VERIFIED]** External scripting (any process outside Resolve — including every MCP server's default mode) requires **Resolve Studio** ($295 one-time). The free edition restricts scripting to the in-app Console/Scripts menu. Verified against the BMD API README v21.0 (updated May 2026), forum threads, and three MCP repos. Since 19.1 the restriction has *tightened* (UIManager script GUIs are Studio-only too).
- **[REFUTED — important nuance]** "Therefore any MCP-driven pipeline requires Studio" is **false**. `hiteshK03/davinci-resolve-mcp` runs a bridge script *inside* free Resolve (Scripts menu, available to everyone) exposing a localhost HTTP endpoint; 155 of 162 tools work on Free (the 7 missing are Neural Engine features, mostly replaced with local Whisper/Demucs/rembg). So: **Studio is the clean unlock; free + in-app bridge is a workable-but-fragile fallback.**
- **[VERIFIED]** Headless mode works: `-nogui` launch flag, scripting API fully functional. Caveats: Resolve must be pre-launched as a daemon (no one-shot CLI render), and external scripting is a **Preferences toggle** (System > General > "External scripting using": None/Local/Network — Studio only).
- **[VERIFIED]** Rendering is fully scriptable: `AddRenderJob`, `StartRendering`, `GetRenderJobStatus`, render presets, `SetRenderSettings` (TargetDir, format, codec, MarkIn/Out, etc.). Known quirk: **the first `AddRenderJob()` in a fresh project can fail silently — always retry** (BMD forum t=183315).
- **[VERIFIED]** Free/Studio share a common API superset; Studio-only functions **return `False`** from Free rather than erroring loudly. Resolve 21 AI features (IntelliSearch, transcription models, AI Speech Generator) additionally require "Extras" downloads.
- **[VERIFIED — kills folklore]** Fusion is *partially* scriptable externally. `TimelineItem.GetFusionCompByIndex()` returns a full fusionscript comp object (`comp.AddTool("TextPlus")`, `tool.SetInput(...)`, port inspection). Verifiers confirmed this against BMD's own docs and live tests against Studio 20.3.2. Deep but poorly documented; keyframe/spline-level control remains thin.

### The hard limits (design around these)

Sources: Wild Lion Media's practitioner guide (the most honest writeup found), BMD forum first-hand reports. High-relevance search results; itemized claims mostly [UNVERIFIED] but multiply-sourced:

- The API covers an estimated **~30–40% of Resolve's feature set**.
- **No in-place timeline editing.** You cannot cut/split/razor, trim in/out of placed clips, move/reorder clips, add transitions/fades, or retime. The only primitives: append (`MediaPool.AppendToTimeline` with `{mediaPoolItem, startFrame, endFrame, trackIndex, recordFrame}`) and delete. One 2024 forum report found startFrame/endFrame partially non-functional with stills.
- **No clip effects or keyframes** via API (so delete-and-re-append loses effects). Transform properties (ZoomX/Y, crop) *are* settable via `TimelineItem.SetProperty`.
- **Color page node graphs, wheels, curves, qualifiers: not scriptable.** Fairlight mixing/EQ/automation: mostly not scriptable.
- **Resolve's own AI features are mostly closed to the API** — transcription can be triggered but the text can't be retrieved; Scene Cut Detection can't be parameterized.
- **The escape hatch that makes all of this OK:** `ImportTimelineFromFile()` accepts **OTIO, EDL, XML, AAF, FCPXML, DRT** with auto-conform. Compute the edit *outside* Resolve; hand it a finished timeline. **[UNVERIFIED but corroborated by every practitioner project surveyed]**

### The MCP server landscape (adopt, don't build — bible §5.6)

| Server | Status | Notes |
|---|---|---|
| `samuelgursky/davinci-resolve-mcp` | **[VERIFIED live against GitHub API 2026-07-11]** 1,578 ★, v2.60.0 (Jul 6, 2026), actively maintained | 34 compound / 341 granular tools; self-reported 336/336 API methods, 331 live-tested. Editing, media pool, render, markers, grading, Fusion, Fairlight helpers. Needs Studio 18.5+, Python 3.10–3.12, macOS OK. **The default choice.** |
| `DigitalWorkflowCompany/resolve-mcp` | **[VERIFIED by code count]** 88 tools + 20 resources, targets Resolve 21 | Counts real (verifier downloaded the tarball and counted decorators), but ~2 ★, 2 commits — unproven. Has an arbitrary-Python `execute` escape hatch. |
| `hiteshK03/davinci-resolve-mcp` | Cited by verifiers | The free-edition bridge (155/162 tools on Free). |
| `lordhoell/davinci-resolve-mcp` | Cited in passing | Claims 440+ tools incl. Fusion node wiring. Unassessed. |

---

## Part 2 — Prior art: how script-driven edit pipelines actually work

**The converged pattern across every practitioner project surveyed: analyze outside the NLE → emit an interchange timeline → import into Resolve as an *editable* timeline (never a baked render).**

- **[VERIFIED]** `auto-editor` (4.5k ★, v31.2.0 released 2026-07-10, now written in Nim, public domain): silence detection via loudness (default `audio:threshold=0.04`, dB syntax supported) or motion; **`--export resolve` emits an FCPXML timeline Resolve imports directly**. Verifiers confirmed users doing exactly this workflow, with one historical Sony-timecode import bug fixed upstream.
- Reference implementations of the same handoff: `YourAverageMo/auto-silence-cut`, `cobanov/autocut` (FCPXML with source timecode preserved). The OTIO-adapter route (`eric-with-a-c/resolve-otio`) is stale — **[REFUTED]** its "API can't place clips" premise was wrong even in 2022 (AppendToTimeline existed); OTIO *import* via `ImportTimelineFromFile` is the modern path anyway.
- **Crayotter** (arXiv 2606.07636, May 2026, open source) — the strongest evidence on agentic-editing architecture **[UNVERIFIED — verification died on limit, but peer-reviewed primary source]**:
  - Three phases: material preparation → editing research ("blueprint") → tool-grounded timeline execution.
  - **Every phase writes inspectable on-disk artifacts** (coverage reports, timeline plans, tool logs, intermediate renders) so failed segments are diagnosed and *selectively* re-run.
  - Core guardrail: **"environment-grounded reflection"** — after every tool call, a verifier computes diagnostics from *observable artifacts* (timestamp accuracy, narration alignment, render quality), never trusting the LLM's own account. This is your bible's §4.2.5 "trust but verify" formalized.
  - Reusable trick: **burn human-readable timecodes onto sampled frames** so a frozen multimodal LLM can bind what it sees to absolute timeline coordinates.
  - Honest ceiling: best system scores **3.40/5** in human eval. Scenery/music-rhythm content automates cleanly; fine-action continuity (food, pets) is weakest.
- Adoption pattern: the agentic tools winning users are **human-in-the-loop with transparent intermediate outputs** (storyboards, rough cuts), not zero-touch automation. **Persistent memory across sessions (which clips used, aesthetic choices, brand rules) is named the hardest unsolved problem** — i.e., your asset registry is a first-class component, not plumbing.

---

## Part 3 — GenAI video, mid-2026 state of the art

### Your stills → I2V → LoRA plan: still valid, needs one update

- **[UNVERIFIED, multi-source]** Image-to-video is the **most-used generation mode in real production** as of 2026 — your stills-first instinct is the consensus. Hailuo 02 and Seedance cited strongest at I2V specifically.
- **The update:** character consistency is increasingly **native** in the big closed models (reference-image "identity blocks" in Sora 2 / Veo 3.1 holding 60s+), and open-weights **Wan 2.2 Animate 14B** preserves identity from a **single reference image** (DWPose motion extraction + SAM2 segmentation, FP8 checkpoint for consumer GPUs) *while also supporting LoRA injection*. So: **try native reference-identity first; train a LoRA only for a recurring character you'll reuse across many videos.** The LoRA route isn't dead — it coexists — but it's no longer step one.
- Model field (mid-2026): Veo 3.1 (native audio, 4K, scene extension), Sora 2 (physics, ~25s cap), Kling 2.6/3.0 (motion/human performance — **Kling v3 tops the blind human-vote arena**, TrueSkill 2040, though on only ~1,134 votes), Hailuo 02/2.3, Seedance 1.5/2.0 (multi-shot consistency), Runway Gen-4/4.5 (editing maturity). Open: Wan 2.5/2.6, HunyuanVideo 1.5, LTX-Video 2 (realtime on consumer GPUs).

### Costs [VERIFIED live against Google's pricing page 2026-07-11]

| Tier | 720p | 1080p | 4K |
|---|---|---|---|
| Veo 3.1 Standard | $0.40/s | $0.40/s | $0.60/s |
| Veo 3.1 Fast | $0.10/s | $0.12/s | $0.30/s |
| Veo 3.1 Lite | $0.05/s | $0.08/s | — |

- 8s Lite clip ≈ **$0.40**; 8s Standard 1080p ≈ **$3.20**. Veo 3/2 shut down 2026-06-30 — target 3.1 model IDs only.
- **Stills are ~100× cheaper than video**: Nano Banana $0.039/image — generate *many* stills, curate hard, animate only winners. This is the economic core of your pipeline.
- Break-even folklore (blog-grade): paid APIs win under ~5K videos/month; GPU rental + open-weights Wan wins at volume. Your vast.ai RTX 3090 is on the wrong side for video gen (Wan 14B wants more VRAM headroom than a 3090 comfortably gives at speed) — treat local open-weights as a later optimization, not v0.

### Blender headless vs genAI (the mountain-road car shot)

`bpy` headless (`blender -b -P script.py`) remains fully scriptable — your prior automation work carries over. Division of labor the research supports:
- **GenAI**: mood shots, short cinematic beats (8–25s clip ceilings), stylized sequences, anything where "close enough" is fine. Cheap, fast, non-deterministic.
- **Blender**: exact camera choreography (the car-follow shot), anything that must be *repeatable* or *revisited* (same scene, new angle next month), long continuous moves beyond clip caps, and shots that composite with real footage. Deterministic, slow, yours forever.
- Hybrid worth testing: Blender renders the motion skeleton → genAI restyles (Wan Animate's video-driving mode is literally built for this).

---

## Part 4 — Control surface (Stream Deck as the tactile spine)

All [UNVERIFIED] — the verification agents for this angle died on the session limit — but every source is first-party vendor documentation, the strongest class of unverified:

- **Farrago: official Stream Deck plugin ships from Rogue Amoeba** (Settings > Controllers). Six action types: per-tile playback, selected-tile controls, set switching, global playback, master volume, bring-frontmost. Works while Farrago is backgrounded. **Zero glue code needed.**
- **Audio Hijack: fully agent-scriptable.** JavaScript automation; save scripts as `.ahcommand` files and any external process can run them (`open -b com.rogueamoeba.audiohijack Script.ahcommand`). Rogue Amoeba *explicitly documents Stream Deck's "Open" action as a supported trigger*. Gate: enable Settings > Advanced > "Allow execution of external scripts". Also has native Apple Shortcuts actions.
- **Stream Deck SDK: local WebSocket, Node.js recommended** (Elgato discourages native plugins). Full event surface (keyDown/keyUp, dialDown/dialRotate, touchTap) and — key for you — **push feedback to the hardware**: per-key images, titles, states, alerts. Your deck keys can display live pipeline state (render %, capture armed, queue depth).
- **Resolve has no official Stream Deck plugin.** Practitioner reality: keyboard-shortcut mapping, or SideshowFX's $44.99 mouse-coordinate plugin (resolution-dependent, brittle). **The right move for you: skip both — route deck → your local daemon → Resolve's scripting API.**
- **Bitfocus Companion** (open source, 4.3.4 May 2026, 2.2k ★, 700+ modules incl. OBS, generic HTTP/OSC/WebSocket): the buy-not-build middleware option. No confirmed Resolve module — you'd use its generic HTTP trigger against your daemon, which is the same daemon the custom-plugin route needs. Start with Companion; write a custom plugin only if you want the live-state key displays.

---

## Part 5 — Market: how editing services sell in 2026

- **Productized subscription editing is proven but labor-heavy**: Video Husky hit 7 figures in ~4 years at $495–$749/mo — with **40–50 human editors**, thin margins, and 70% of revenue from a handful of clients. **[VERIFIED-adjacent: case-study source, claims consistent]**
- **Capped/fractional positioning beats "unlimited"**: Vidpros sells a "fractional video editor" at $1,000–$4,000/mo, hard-capped at 4 clients/editor. Source's operational claim: uncapped recurring offers over-deliver relative to price within ~60 days.
- **AI-assisted agency model**: Lemonlight claims 40%+ production speedup from AI assist — AI as margin, humans as product. Academic research they cite: AI's real adoption footprint in pro editing is still small; outputs need specialist correction; revision cycles multiply.
- **Implication for you:** nobody is successfully selling "an AI edits your video." What sells is a **narrow, capped, niche-positioned outcome** (e.g., "podcast → 10 platform-ready clips, 48h turnaround") where your pipeline silently compresses the cost of the mundane 80%. The pipeline is your margin and moat, not your pitch. This also aligns with your belief-gate: you'd be selling turnaround and taste, both real.

---

## Part 6 — Pushback: where this breaks (you asked)

1. **The Resolve API is a delivery/assembly API, not an editing API.** ~30–40% coverage, append-only timelines, no effects/keyframes/color scripting. Any plan where "Claude does the whole edit inside Resolve" dies here. The architecture below routes around it (external cut brain → interchange import), but understand: **the creative timeline surface you'll touch by hand in the GUI is invisible to scripts.** Don't let an agent re-import over a timeline you've hand-polished — one-way flow, rough-cut in, human finishes.
2. **Fully-automated editing quality ceiling is 3.40/5** (best published system, human-evaluated). Automation is for the rough cut and the mundane; the cut that makes it *good* stays yours. Content-type matters: your talking-head/screen-capture material is on the *easy* end; fine-action continuity is where agents fall apart.
3. **Silent failure is the house style of this API.** Studio-only calls return `False` from Free; first `AddRenderJob` silently no-ops; documented AppendToTimeline params have partially failed in the wild. Every pipeline stage needs artifact-level verification (does the timeline exist, does clip count match the cut list, does the render probe clean under ffprobe) — never trust the return value alone. This is Crayotter's environment-grounded reflection and your bible's §5.2 saying the same thing.
4. **Dependency fragility**: the best MCP server is one maintainer; Veo versions die on ~9-month cycles (3→3.1 shutdown already happened); Resolve API docs officially target Python 3.6 while the MCP needs 3.10–3.12. Pin versions, wrap vendors behind your own thin interface (SSOT for provider IDs/model names — bible §2.2), expect churn.
5. **Persistent pipeline memory is the hardest unsolved problem** per the field — which clips were used, what aesthetic rules apply, what's been tried. Your asset registry needs to be designed on day 0, not bolted on.
6. **Vibe-coding limit**: this system is ~6 subsystems × external APIs × a GUI app with mood swings. It only stays sane as **small modules with typed contracts and single-stage evals** — exactly the harness discipline you already named. The failure mode to fear isn't a bad module; it's letting an agent iterate across module boundaries on shared code (your JobHard lesson generalizes).

---

## Part 7 — The architecture (generalized plan)

**Precedent:** BlessDog drives Ableton via MCP. Same shape: Claude Code + MCP + local daemons around a pro app. Division of labor: **Ryan = script, taste, creative cut, final grade. Claude = everything mundane and verifiable.**

```
                 ┌─────────────────────────────────────────────┐
                 │  CONDUCTOR — Claude Code harness             │
                 │  (plans, calls tools, never trusts itself)   │
                 └──────┬───────────────────────────┬──────────┘
   tactile              │                           │
 ┌─────────┐   ┌────────▼────────┐        ┌─────────▼─────────┐
 │  DECK   │──▶│  STUDIO DAEMON  │        │   SCENE FORGE     │
 │ Stream  │   │ (Python, local  │        │ stills (Nano B.)  │
 │ Deck +  │   │  HTTP; pipeline │        │  → curate →       │
 │ Farrago │   │  verbs + state) │        │ I2V (Veo/Kling/   │
 │ + OBS   │   └──┬────┬────┬────┘        │ Wan) / Blender bpy│
 └─────────┘      │    │    │             └─────────┬─────────┘
                  │    │    │                       │
        ┌─────────▼┐ ┌─▼────▼─────┐  ┌──────────────▼──┐
        │ REGISTRY │ │ CUT BRAIN  │  │ TIMELINE        │
        │ SQLite   │ │ transcript │  │ COMPILER        │
        │ SSOT:    │ │ (Whisper)+ │  │ cut list →      │
        │ media,   │ │ auto-editor│  │ FCPXML/OTIO →   │
        │ txns,    │ │ + LLM cut  │  │ ImportTimeline  │
        │ decisions│ │ list (EDL) │  │ FromFile        │
        └──────────┘ └────────────┘  └───────┬─────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │ RESOLVE OP (adopt gursky MCP)│
                              │ Studio, -nogui daemon,       │
                              │ media pool, markers, render  │
                              └──────────────┬──────────────┘
                                             │
                       human creative cut ◀──┤ (GUI, hands, taste)
                                             │
                              ┌──────────────▼──────────────┐
                              │ VERIFIER (every stage):      │
                              │ ffprobe, clip-count vs cut   │
                              │ list, duration, black-frame  │
                              └─────────────────────────────┘
```

### Components (each is a later deep-dive session)

1. **Registry** — SQLite SSOT: every asset, transcript, cut decision, render. The "hardest unsolved problem" solved the boring way. Build first; everything else reads/writes it.
2. **Resolve Op** — buy Studio ($295), adopt `samuelgursky/davinci-resolve-mcp`, enable external scripting (Local), smoke-test headless render round-trip.
3. **Cut Brain** — Whisper transcript + auto-editor silence pass + LLM cut-list generation against *your script*. Output: EDL/OTIO cut list, an artifact you can read before it touches Resolve.
4. **Timeline Compiler** — cut list → FCPXML/OTIO → `ImportTimelineFromFile`. The append-only API limits never bite because the timeline arrives whole.
5. **Scene Forge** — stills-first economics (100× cheaper), curate, animate winners via Veo Fast/Lite (or Kling/Hailuo via aggregator); native reference-identity before LoRA; Blender `bpy` headless for deterministic camera work; consider Blender-motion → Wan-restyle hybrid.
6. **Studio Daemon + Deck** — small Python HTTP daemon exposing pipeline verbs (arm capture, rough-cut last recording, queue render, play SFX). Farrago's official plugin handles the soundboard directly; Bitfocus Companion (or a custom Node plugin later, for live key-state displays) maps deck keys to daemon endpoints. OBS integration you already have.
7. **Verifier** — cross-cutting: every stage emits an artifact, every artifact gets probed (ffprobe, counts, durations) before the next stage runs. No stage trusts the previous stage's self-report.

### Build order (each step independently useful)

0. **Buy Resolve Studio.** Everything gates on it; $295 one-time, no subscription.
1. **Resolve Op smoke test** (a weekend): MCP installed, headless daemon, scripted import → timeline → render → ffprobe green.
2. **auto-editor handoff** on a real OBS recording → editable Resolve timeline. Immediate daily value: silence-stripped rough cuts for free.
3. **Cut Brain v0**: transcript + script → cut list → Compiler. Now "rough assembly from my script" is one command.
4. **Daemon + Deck**: wire the three verbs you use daily to physical keys. Farrago plugin: 10 minutes, do it today.
5. **Scene Forge v0**: stills → curation board → Veo Lite animation of winners → Registry.
6. **Iterate per-component** with single-stage evals (test-before-batch, as ever).

### What NOT to build

- A custom Resolve MCP server (gursky's is 1.6k ★ and live-tested — bible §5.6).
- API-driven clip-by-clip timeline surgery (fights the API's deepest limit).
- A LoRA training pipeline on day one (native reference-identity may cover you).
- "Unlimited AI editing" as a product (the market data says capped/fractional/niche or nothing).

---

## Part 8 — Second-opinion reconciliation (2026-07-11, later same day)

Ryan brought in an independent second research report (ChatGPT-sourced, commercial-product framing). Reconciliation against this report's verified corpus:

### Independent convergence (treat as settled)
Both reports, from different sources, landed on: Studio required (don't build on free); **compute the edit outside Resolve and deterministically compile it in** (interchange import / append API); the live timeline is never the source of truth; human keeps the creative cut; every AI proposal validated before mutation; don't send hours of raw footage into a multimodal context — funnel evidence (transcripts, keyframes, candidate segments) instead; and step 1 in both plans is the same no-AI spike: **JSON cut decisions → editable Resolve timeline → render, rerunnable without corruption.**

### Genuinely new from the second report (adopted)
- **Story IR** — a versioned, Resolve-independent intermediate representation (frame-integer edits, evidence links per decision, provenance, human-readable diffs, duplicate-before-apply). This *upgrades* the "cut list" contract between Cut Brain and Timeline Compiler. Adopt from day one; it's SSOT + types-as-contracts applied to editorial.
- **Workflow Integration plugins** — Resolve hosts JS/Electron panels (Electron 36.3.2 runtime since 20.1 per BMD notes). A later UI surface this research missed entirely.
- **Fusion templates/macros (`.setting`)** as the brand motion system — parameterized, *editable-in-Fusion* titles/lower-thirds/diagrams driven from structured data. Complements the fusionscript finding in Part 1.
- **Competitive landscape** (unverified, vendor-described): Eddie AI (proxy+log+chat rough cut, bridges to Resolve — same daemon topology as Part 7), StoryToolkitAI (local transcription + semantic search + Resolve), AutoCut, Cutback Selects. Consequence: generic "chat with footage → rough cut" is occupied; Part 5's niche/capped conclusion stands.
- **"Don't rebuild what Resolve commoditizes"** — captions, silence removal, scene detection, reframing are absorption-risk features, weak as standalone products. Sharpens Part 7's "what NOT to build."
- **Phase 0: learn the craft** — BMD's free official training (Edit/Fairlight/Fusion/color) before automating. Correct ordering; you can't encode editorial rules you don't have.
- **Open licensing question** (correctly flagged as NOT VERIFIED there either): no confirmed blanket SDK redistribution license for commercial products. If/when selling: customer-owned Studio, no BMD binaries redistributed, confirm with BMD Developer Support.

### Where the second report corrects THIS one
- **Color scripting — RESOLVED 2026-07-11 by direct read of the v21.0 API README** (X-Raym mirror). Both prior claims were half right. What IS scriptable: the node graph (`Timeline​Item.GetNodeGraph()` → Graph object: `GetNumNodes`, `SetLUT`/`GetLUT` per node, `SetNodeEnabled`, node labels/cache), **`ApplyGradeFromDRX(path, gradeMode)`**, `SetCDL` (slope/offset/power/saturation per node), `CopyGrades` across clips, color groups (incl. pre/post-clip group graphs), `ExportLUT` (CUBE 17/33/65pt, VLUT), stills grabbing, keyframe-mode switching. What is NOT scriptable: **color wheel values (lift/gamma/gain), curves, qualifiers, and any direct node parameter access beyond LUT/enable/label/cache.**
  **Practical consequence (the pattern that matters):** you cannot *author* a grade by script, but you can **apply** one — build the look by hand once, save as DRX still or LUT, then script `ApplyGradeFromDRX`/`SetLUT`/`CopyGrades` across every clip. Grading becomes a reusable, scriptable finishing pass with a human-authored look at its core. CDL gives coarse scripted correction on top.

### Where this report holds against the second one
- **MCP timing**: the second report says "do not start with MCP." That's right *for a sellable product* (deterministic domain commands first, MCP as transport later) — but for the personal studio, adopting gursky's MCP immediately is still correct: it's the exploration/dev harness Claude Code uses while the deterministic command layer is being built. Both are true at different layers; the Studio Daemon's verbs ARE the deterministic command layer.
- The second report's "VERIFIED" tags are its own (not adversarially voted); its BMD-first-party citations are strong, its competitor capabilities are vendor marketing.

### Net change to the plan
Build order unchanged except: **Story IR becomes the explicit contract at step 3** (Cut Brain emits Story IR, not a bare EDL), **Phase 0 adds BMD training coursework**, and **Fusion template system** is added alongside Scene Forge. Commercial path (if ever): service-first in interview-led narrative work, per both reports and the Part 5 market data.

---

## Source index

Primary: BMD Scripting API README v21.0 (X-Raym mirror, May 2026) · github.com/samuelgursky/davinci-resolve-mcp · github.com/DigitalWorkflowCompany/resolve-mcp · github.com/wyattblue/auto-editor · ai.google.dev/gemini-api/docs/pricing · rogueamoeba.com (Farrago Stream Deck manual; Audio Hijack scripting KB) · docs.elgato.com (SDK WebSocket) · bitfocus.io/companion · comfy.org (Wan 2.2 Animate workflow) · arxiv.org/pdf/2606.07636 (Crayotter)
Secondary/practitioner: wildlion.media Resolve API guide · forum.blackmagicdesign.com (t=197481, t=113252, t=183315) · jonnyelwyn.co.uk (Stream Deck × Resolve) · resolvedevdoc.readthedocs.io · llm-stats.com video arena · wavespeed.ai 2026 model guide · sidehustlenation.com (Video Husky) · hausadvisors.com (Vidpros) · lemonlight.com · htek.dev · loopdesk.ai
