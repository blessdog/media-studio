# Pipeline assessment — how should the explainer videos actually get made?

*2026-08-05. Written in response to: "what I wanted was to build out what we did
for LPC, but for this video… Is there a better way? What kind of technical debt
am I already in?"*

Everything below was verified by reading the repos and running the media. Where
something is a judgement call it says so.

---

## Verdict, up front

**You are not in much technical debt on the thing that matters, and you already
built the pipeline you're describing.** It's `cutwork`'s illustrate lane, and its
assembler is `cutwork/tools/splice-assemble.mjs`. Nothing new needs to be
written to do what you asked.

**Three things are actually true:**

1. **The architecture is right and proven.** Transcript → plan → stills → motion
   clips → ffmpeg assembly, with your audio never cutting. It exists, it runs,
   and it produced a 601 MB finished film.
2. **The quality bar has already been cleared once** — `bongpot-film-v10.mp4`
   looks genuinely good. That is the proof this approach doesn't have to be slop.
3. **The debt is duplication, not design.** Two repos hold 16 of the same tool
   files and 6 of them have silently diverged.

**The Blender ink lane I spent today on is the wrong default** and should be
demoted to ~8 shots. More on that in §6.

---

## 1. What actually exists

Verified with `ls` and file comparison, not memory.

| Repo | Role | State |
|---|---|---|
| `bongpot/` | LPC prank-call → film. 68 tools | **Proven.** Shipped `bongpot-film-v10.mp4` (601 MB, Jun 10) |
| `cutwork/` | Illustrate lane — *your own recordings → illustrated video*. 27 tools | Mechanics carried over proven; **end-to-end unproven in this repo** (its own STATUS says so) |
| `media-studio/` | Intended control plane — Story IR, OTIO, Resolve | Exists, **not wired to either lane** |
| `BLENDER/` | Today's work. 6 tools | New. Partly duplicates cutwork |

**`cutwork` is the correct home for this film.** It was split out of bongpot on
2026-07-03 for exactly this: your material, not prank calls.

---

## 2. The LPC pipeline, precisely

From `bongpot/STATUS.md`, confirmed against the files:

```
transcribe-local.mjs   call.mp3 → Deepgram nova-3 diarized → transcript.json
_ear.mjs / ear/        THE EAR — stems, prosody, voiceprint → delivery ground truth
author-video.mjs       5-pass brain: READ/CAST/SCOUT/CUT/DIRECT/EMIT → video-plan.json
lint-plan.mjs          deterministic doctrine gate — run after EVERY brain run
clay-stills.mjs        Pass 1: plates + keyframes (Replicate Flux 2)
wan-clips.mjs          Pass 2: motion (Wan i2v on a Vast GPU box)
studio.mjs             THE DESK — review server; gates and verdicts live in the plan
sequence-video.mjs     assembly — approved clips + untouched audio → film.mp4
```

`cutwork` carries the same shape with a **2-pass** brain instead of 5
(`author-inserts.mjs`: BEATS → EMIT-INSERT), because inserts over your own
footage need far less machinery than casting a whole cast of characters.

### The two assemblers are different tools — this is the fork in the road

| Tool | Model | Needs |
|---|---|---|
| `cutwork/tools/splice-assemble.mjs` | **Spine-first.** Your recording IS the timeline; clips replace the *picture* for `[start,end]` windows; your audio never cuts | Your footage to exist first |
| `bongpot/tools/sequence-video.mjs` | **Picture-first.** Tiles clips gaplessly to fill a timeline | A plan with durations |

You said *"stitch them together with ffmpeg and then I can narrate over it"* —
that's **picture-first**, and that assembler lives only in `bongpot`. The film as
scripted (`SCRIPT-v5.md`) is **spine-first**, because you on camera is the A plot.

**Both are correct at different stages**, and that's the actual answer to "is
there a better way":

- **Now**, to see something and react to it: picture-first. Generate the shots
  from the script, tile them, narrate over the top.
- **Later**, once you've shot the shed footage: spine-first. Your take becomes
  the spine and those same clips become inserts. The clips don't get rebuilt.

The plan file is the same object in both cases. Nothing is wasted.

---

## 3. The real creative surface

> *"It really strips me of all the creativity and thinking."*

That's a fair reaction to what I handed you, but it's not what this pipeline is.
The creative surface isn't the ffmpeg — it's **`video-plan.json`**. Here's a real
one from `cutwork/footage/write-on-app/`:

```json
{ "id": "b01", "start": 41.5, "end": 46.6, "function": "EXTEND", "medium": "world3d",
  "intent": "A large, dusty mechanical keyboard sits untouched under a thin layer
             of dust while a half-drunk coffee cup slowly steams next to it —
             nobody home.",
  "quote": "Now I don't type shit. It's so much faster just to talk.",
  "framing": "low angle, slightly off-center, keyboard filling the foreground…",
  "still_prompt": "A large mechanical keyboard sits on a desk, its keycaps coated
                   in a thin even layer of dust…" }
```

**Every one of those fields is yours to rewrite.** The brain's job is to produce
34 of these in one pass so you're editing instead of staring at a blank page.
Then you re-roll individual shots — one shot, not the film.

The slop risk isn't the pipeline. It's accepting the first output. That's why
`lint-plan.mjs` gates every brain run and `studio.mjs` exists as a review desk
with verdicts. Those tools are the anti-slop machinery and they're already built.

---

## 4. Technical debt — itemized

### 4.1 Duplicated tools across `bongpot` and `cutwork` — **the real debt**

16 files exist in both. **6 have diverged:**

```
DIVERGED  _replicate.mjs        generate-clips.mjs     generate-stills.mjs
          rebuild-transcript.mjs transcribe-local.mjs   wan-clips.mjs
same      _comfy _fleet _gates _lint _transcript _uso
          dispatch-render  render-monitor  runcomfy  vast
```

**Cost:** every render-substrate fix has to be made twice, and six of them are
already out of sync — so "the fix works in bongpot" no longer implies it works
in cutwork. This is textbook **shotgun surgery**.

**This was a deliberate trade.** The 2026-07-03 split says the repos
*deliberately* don't share a package, because separation was the point. That was
the right call for the *brains* (LPC's 5-pass has no business in the illustrate
lane). It's the wrong call for the *substrate* — Vast provisioning, Replicate
clients, Deepgram transcription and i2v have no lane-specific content.

**Fix (small, deferrable):** extract the 10 identical files into one shared
package both repos depend on. Leave the 6 diverged ones alone until you know
which version is right. This is a half-day and it is not urgent — but every
month you don't, the 6 becomes 8.

### 4.2 `cutwork`'s illustrate lane is unproven end-to-end

Its own STATUS: *"No video-use CUT has happened yet; the raw→trimmed→
illustrated→rendered loop is UNPROVEN end to end in this repo."*

The one workspace, `footage/write-on-app/`, has **exactly one authored insert**
(`b01`) across an 88-second video. `draft.mp4` and `draft-world3d.mp4` both
exist and are full length — so the assembler genuinely works — but this is a
smoke test, not a proof of the creative loop.

**Cost:** the first real run will hit bugs. Budget for that; don't be surprised.

### 4.3 State and archaeology are mixed together

`bongpot/outputs/` holds ~20 `video-plan.*.json` variants (`.v2`…`.v10`,
`.sonnet46`, `.slice90`, `.unscoped`) and 8 `clips-v*` directories. Nothing
marks which is current. `STATUS.md` calls `archive/` archaeology but the
outputs directory has the same problem and isn't labelled.

**Cost:** low day-to-day, high when you or an agent comes back cold in three
months. Cheap fix: move superseded runs under `outputs/_archive/`.

### 4.4 `media-studio` is a fourth thing that isn't connected

It has its own Story IR (TimelineSpec, OTIO, Resolve) and an
`ENGINEERING-AUDIT-2026-08-03.md`. It's the intended control plane. Neither
`bongpot` nor `cutwork` calls it. Its Resolve MCP path was broken until I fixed
it today.

**Cost:** none right now — but don't build a fifth thing before deciding whether
this is the one that survives.

### 4.5 Debt I added today

`BLENDER/monero/film.json` + `narrate.py` + `assemble.py` reimplement, badly and
narrowly, what `video-plan.json` + `splice-assemble.mjs` already do properly.

**What's worth keeping:**
- `film.json`'s **content** — 80 beats of the script, timed. That's real work and
  it converts to `video-plan.json` shape mechanically.
- `beats.py` — Deepgram transcript → frame markers.
- The two hard-won correctness rules now in the tools: **cut by frame count, not
  duration** (80 segments of duration-rounding drifted +0.186s), and **fail loud
  when a segment doesn't fill its slot** (a short clip silently truncates the
  narration tail and shifts every later cut onto the wrong word).

**What should go:** `narrate.py` (you don't want TTS), `assemble.py` (superseded
by `splice-assemble.mjs`), and the slate mechanism as a *deliverable* — though
slates as a *fallback for an unrendered shot* is a genuinely good idea that
`splice-assemble` already does better, by keeping the spine.

---

## 5. Where the quality actually is

This is the part that matters most, and the evidence is unambiguous.

**`bongpot-film-v10.mp4` @ 3:20** — a UPS driver in a truck cab. Painterly
rendering, ink-line edges on the interior, a stylised landscape through the
window, a real performance on the face. **This is not slop. This clears the bar.**

**`cutwork/footage/write-on-app/draft-world3d.mp4` @ 43s** — the `world3d`
medium (image → TRELLIS 3D → Blender → ink-wash). The keyboard is a melted
black blob. **This does not clear the bar**, and it's the same `world3d` route I
was walking down today.

**Both STATUS files carry the same 2026-07-02 verdict, unchanged:**
> *"mechanics proven, output quality below Ryan's bar (still recipe, i2v motion,
> washed-out treatment). Splitting repos didn't fix pixels."*

So the honest read: **the still/plate lane (Replicate Flux 2 / Kontext) is where
the quality is. The 3D lanes — `world3d`, and my Blender work today — are where
it isn't.**

---

## 6. Where Blender belongs

I argued yesterday that Blender was necessary because **diffusion cannot
guarantee *sameness***, and the film's argument requires it:

- sixteen envelopes that are *genuinely identical*
- a duplicate mark that is *literally the same mark*
- `SCRIPT-v5.md`'s own reject condition: *"if the animator can still point to
  the hero, the shot is rejected"*

**That argument still holds.** It's a real constraint and diffusion can't satisfy
it. What was wrong was the *scope*: I let it become the default medium for the
whole film. It shouldn't be.

**Blender's honest scorecard from today:**
- ~6 s/frame at 48 samples. 34 shots ≈ many hours per revision.
- Two shots built in a day. One of them shipped **blank** because I checked the
  file existed instead of looking at the pixels.
- The look that did render is washed out — faint speckle where ink marks should
  be. The palette spans 0.045–0.93 but the render lands everything in 0.10–0.82.

**Verdict:** Blender for the **~8 sameness shots** (the ring, the duplicate mark,
the envelopes). Diffusion for the other ~26. One treatment over both so they
live in one world. That's the split I already wrote in the handoff — I just
didn't follow it.

---

## 7. Recommended path

**Do not write new tooling.** In order:

1. **Convert `film.json` → `video-plan.json`.** The 80 beats already exist with
   text and shot directions; `cut.shots[]` and `emit.shots[]` want the same
   information in a different shape. Mechanical.
2. **Run `author-inserts` to fill `still_prompt` / `framing` per shot** — that's
   your first-draft art direction, 34 shots in one pass.
3. **`lint-inserts` gate**, then read the prompts. **This is where you direct.**
   Rewrite the ones that are wrong. Cheap — it's text.
4. **`generate-stills`** (Replicate Flux 2 — the lane whose output already
   cleared your bar). Review stills, re-roll individually.
5. **`wan-clips`** for motion on the ones that need it; hold on a still where
   motion adds nothing. Motion is the weakest link — use it deliberately.
6. **Assemble picture-first** with `sequence-video.mjs` → you have a rough film
   to react to, no narration needed.
7. **You narrate over it.** Then swap to `splice-assemble.mjs` with your shed
   footage as the spine when you shoot it. Same clips, no rebuild.
8. **Blender only for the sameness shots**, dropped in as `medium: "footage"`
   inserts.

**Debt payments, when convenient, in this order:** extract the 10 identical
substrate tools into a shared package (§4.1) · archive superseded `outputs/`
runs (§4.3) · decide whether `media-studio` is the control plane or gets folded
in (§4.4).

---

## 8. The one thing I'd push back on

The pipeline is not what strips the creativity — but **it will** if the brain's
first output gets accepted. The whole design assumes a human rejects things:
`lint-plan` gates, `studio.mjs` holds verdicts, assembly **fails closed** on
unresolved rejects.

Today I did the opposite of that. I shipped a blank shot and called it verified,
because I looked at a file instead of an image. That's the actual failure mode
to defend against, and it isn't a tooling problem.

**Your eyes on every still before it becomes a clip. That's the gate.**
