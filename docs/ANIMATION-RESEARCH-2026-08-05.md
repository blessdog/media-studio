# How to actually animate these films

*2026-08-05. Written after measuring Ryan's reference clip frame by frame and
researching how this problem is solved elsewhere. Everything in §1 is measured
from the file, not inferred.*

---

## The headline

**You have been trying to animate everything. The reference animates almost
nothing — and that is why it looks expensive.**

In the Adult Swim clip you sent, **68% of consecutive frames are identical to
the frame before them.** When a frame does change, **2.5–3.9% of the pixels
move.** That's one car on a painted road. The camera never moves; shot changes
are hard cuts.

That single fact reorganises the whole project. A 9-minute film is not 13,000
frames of animation. It is **a few hundred beautiful painted plates, each with
one thing moving on it.**

---

## 1. What the reference clip actually is (measured)

`/Volumes/BleSSD/clips/20260805-155708-hBXz3OaSaTk.mp4` — 4:18, 1920×1080,
23.976 fps, 6,192 frames.

Sampling 48 consecutive frames (2 seconds) from the middle of a scene:

| Measurement | Result | What it means |
|---|---|---|
| Frames identical to previous | **32 of 47 (68%)** | Held drawings — the norm, not the exception |
| Median inter-frame change | **0.27 / 255** | Even "moving" frames barely move |
| Change cadence | every **3–5 frames** | ≈ **5–8 drawings per second**, not 24 |
| Pixels changed when it changes | **2.5–3.9%** | One small element. Not the frame |
| Frame 29 | **95% changed** | A CUT. Not a camera move |

**The structure is:** a static painted background of real quality, a locked
camera, one small element moving on a sparse cadence, and hard cuts between
shots. The background carries 100% of the beauty and 0% of the motion.

The industry term is **limited animation** — reusing and holding frames to cut
production cost while keeping a distinctive look. It is Adult Swim's house
standard, and backgrounds in that tradition are hand-painted after layout while
character motion is deliberately minimal.

**Why this matters to us:** you already generate backgrounds of exactly this
quality with diffusion. You said you can hit a style accurately, and the ink
stills prove it. The expensive-looking half of this technique is *the half you
have already solved.* The other half is cheap by design.

---

## 2. Is scripting Blender the efficient way? Partly — and I picked wrong

**Honest answer: for the shot I wrote today, no.** `s5-key-image-teach.py` is
~200 lines constructing meshes vertex by vertex, hand-rolling keyframe
insertion, and computing an orthographic camera — to draw *squares appearing in
a grid*. That is a solved problem with a purpose-built tool.

### The landscape

| Tool | Language | Built for | Verdict here |
|---|---|---|---|
| **Manim** (ManimCE) | Python | Programmatic explainer animation — 3Blue1Brown's engine | **This is what I hand-rolled.** Grids, transforms, fades, highlight, morph-between-shapes are one-liners |
| **Motion Canvas** | TypeScript | Explanatory videos, animation-first API, real-time editor | Strong fit — matches bongpot/cutwork's stack |
| **Remotion** | React/TS | Programmatic video at scale (~60K weekly downloads vs Motion Canvas ~8K) | Best for volume/templating, heavier than needed for hand-crafted shots |
| **Blender + Python** | Python | 3D, and anything needing real geometry | Keep — but for the ~8 shots that need it |
| **Blender Grease Pencil** | — | 2D animation *inside* Blender, layered for parallax | The bridge if you want one tool |

Manim's own community guidance is explicit in the other direction too: for
genuinely complex 3D, **use Blender, not Manim.** So this isn't "replace
Blender." It's "stop using Blender for diagrams."

### The split that follows

- **Diagrams, comparisons, highlights, transforms** → Manim or Motion Canvas.
  The key-image shot is 15 lines there.
- **Anything requiring real geometry, real perspective, or provable sameness**
  → Blender. That is still ~8 shots and the argument for them is unchanged.
- **Everything beautiful** → diffusion stills, barely animated.

---

## 3. The architecture this points to

Four layers, each using the cheapest tool that can do its job:

```
1. PAINTED WORLD      diffusion stills (flux-2-dev, monero-ink recipe)
                      the entire visual identity lives here
                             │
2. LIMITED MOTION     one element moving, ~6-8 changes/sec, locked camera
                      2.5D parallax where depth helps; i2v ONLY where the
                      whole frame is the subject (ink blooming, fire, water)
                             │
3. DETERMINISTIC      Manim / Motion Canvas for diagrams,
   EXPLANATION        Blender for provable sameness
                             │
4. THE PERSON         LPC's transcript → talking-character system, already built
```

**Layer 2 is the piece that doesn't exist yet**, and it's the smallest one. The
reference proves it needs: a static plate, a cut-out element, a sparse
keyframe cadence, and a hold. That's a compositor, not an animator — and
`splice-assemble.mjs` is already 80% of it.

**A note on i2v:** today's seedance clips moved *every pixel of every frame* —
the opposite of the reference. That's why they read as "AI video" rather than
animation. i2v is right when the whole frame IS the event (ink blooming into
paper). It is wrong as a general motion strategy, and it's also the most
expensive and least controllable option. **Holding a still and moving one
cut-out is cheaper, more controllable, and closer to the look you want.**

---

## 4. What changes for the Monero film

- **Stop rendering 34 shots.** Render ~34 *plates* and animate one element on
  each. The plates already exist.
- **Rebuild the key-image shot in Manim.** Same logic, ~15 lines, and it gains
  the transform/highlight vocabulary that makes comparisons legible for free.
- **Keep Blender for provable sameness only** — the ring of sixteen, the
  duplicate mark. Diffusion demonstrably fails these (it returned eight
  visibly different envelopes when asked for sixteen identical ones).
- **Cut, don't move.** The reference changes shot by cutting. That's free, and
  it's the strongest tool for pacing a 9-minute explainer.
- **Target ~8 fps of change, not 24.** Holds are not a compromise here; they're
  the style.

---

## 5. Open questions worth answering before committing

1. **Does the ink-wash look survive limited animation?** The reference's
   painted style is designed for holds. Ink-wash might read as *stiff* rather
   than *composed* when held. One test scene answers it.
2. **Manim's aesthetic is opinionated** and vector-flat; it also handles raster
   images poorly, which matters because our backgrounds are diffusion rasters.
   The likely answer is Manim for the diagram *layer only*, composited over a
   painted plate — not Manim as the renderer of record.
3. **Motion Canvas vs Manim** is a real fork: TS matches the existing repos,
   Python matches media-studio and Blender. Worth a small bake-off rather than
   a guess.

---

## Sources

- [Limited animation — Wikipedia](https://en.wikipedia.org/wiki/Limited_animation)
- [Limited Animation — TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/Main/LimitedAnimation)
- [Manim — 3b1b/manim (GitHub)](https://github.com/3b1b/manim)
- [Manim Community docs](https://docs.manim.community/en/stable/examples.html)
- [What Is Manim? — Animo](https://animo.video/what-is-manim)
- [Remotion vs Motion Canvas vs Revideo (2026) — PkgPulse](https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026)
- [Remotion vs Motion Canvas — CamelEdge](https://cameledge.com/post/productivity/remotion-vs-motion-canvas)
- [Blender Grease Pencil — Story Artist](https://www.blender.org/features/story-artist/)
- [Anime-Style Hand-Drawn 3D with Grease Pencil — 80.lv](https://80.lv/articles/check-out-this-anime-style-hand-drawn-3d-setup-made-with-blender)
- [Animate Flat 2D Images in After Effects (2.5D Parallax) — Motion Array](https://motionarray.com/learn/after-effects/animate-flat-2d-images-after-effects/)
- [Adult Swim animation style — BAM Animation](https://brentandmax.com/project/adult-swim-style/)
