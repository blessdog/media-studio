# HANDOFF — 2026-08-06

Written for whoever picks this up next: a different AI agent, a different tool,
or a person. **It assumes no prior conversation and no particular assistant.**
Everything load-bearing is a file path you can open and a command you can run.

Facts below marked **[V]** were measured on this machine. **[U]** means
unverified — do not build on it without measuring first. That distinction is
the most valuable thing in this document; several days were lost to claims that
sounded verified and weren't.

---

## 1. Where you are, in one paragraph

Ryan is making explainer films for a YouTube channel. The first is a ~9½-minute
film about how Monero prevents double-spending. The visual approach is
**generated ink-wash stills carrying the look, plus code-compiled animation
carrying the explanation**, composited in DaVinci Resolve's Fusion. A working
picture cut of the whole film already exists. What does not exist is a finished
film.

**A 9:18 assembled cut of the entire film is at
`../BLENDER/monero/renders/film/monero-picture-v1.mp4`** (558 seconds, 100 MB).
It is animatic-grade — stills with camera moves — but it is the whole film, in
order, at length. Watch it first. It is the single best orientation available
and it will tell you more than this document.

---

## 2. Read this before you decide what to do

**The most useful next step is probably not the one the plan says.**

There is an approved plan at `~/.claude/plans/serene-popping-raven.md` (a
previous session's; read it for context, not as orders) whose Part B is "build
ten reusable Fusion components." Two of ten exist. Finishing the other eight is
weeks of work that produces no film.

Meanwhile the film already has a full picture cut. The distance from that to
something publishable is: **narration recorded over it, and the dozen weakest
shots replaced.** Ryan records his own narration; there is no TTS in this
pipeline and an earlier attempt to add one was rejected outright.

The compiler built on 2026-08-06 earns its keep on the four or five shots that
must be *provably exact* — where the film claims "the same coin always leaves
the same mark" and a diffusion model cannot guarantee that. The rest of the film
does not need it. **Ryan's stated preference at handoff time was to stop the
component library and finish the film shot by shot.**

---

## 3. Hard-won traps. Read all six; each one cost hours.

**1. Run DaVinci Resolve headless. [V]**
With the GUI up and the Project Manager showing, *every mutating API call
returns `None` while reads keep working* — `CreateProject`, `LoadProject`,
`OpenPage`, `CreateEmptyTimeline`. A script gets a plausible Project object and
silently does nothing.

```
"/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve" -nogui
```

API up in ~9–12 s, `GetCurrentPage()` returns a real page, mutations work.

**2. `ImportFusionComp()` REPLACES the whole composition. [V]**
`AddFusionComp()` creates `MediaIn1`/`MediaOut1`; importing a comp file discards
them. A generated comp that merely *references* `MediaIn1` imports with all its
tools present, correct names, correct types — and renders **nothing**, because
the input dangles and there is no output node. A node-count check passes this.
Comps must emit `MediaIn1`/`MediaOut1` themselves; `studio/components/__init__.py`
now does it centrally so no component can forget.

**3. `osascript` is denied by TCC on this machine. [V]**
So is `screencapture` and System Events. `scripts/restart_resolve.py` quits via
`osascript` and, when denied, produces *no log entry at all* and reports
`FAIL: ... (dialog blocking?)` — a misdiagnosis that sends you hunting a dialog
that isn't there. `kill -TERM <pid>` exits Resolve gracefully in ~10 s and needs
no permission. **That script's error message should be fixed.**

**4. `pip install pysion` installs the WRONG package. [V]**
PyPI's `pysion` is "EasyVision inferencing API" — unrelated. The Fusion library
of that name has no PyPI release and no git tags. It is vendored at a pinned
commit in `vendor/pysion/`; see `vendor/pysion/PROVENANCE.md`. **Never add
`pysion` to `requirements.txt`.**

**5. `vendor/` was in `.gitignore`.** The vendored dependency would not have been
committed and a fresh clone would not have compiled. Now `vendor/*` is excluded
and `!vendor/pysion/` re-included. If you vendor anything else, check this.

**6. Verify pixels, not files.** This project has been burned repeatedly by
"verified" that meant the file existed, the exit code was 0, or the filename
looked right. A render can exit 0 and be blank. A comp can import perfectly and
draw nothing. 81 images named `...-monero-ink-...` include several that are
photographs. **Open the artifact and look at it.**

---

## 4. What was built on 2026-08-06, and how to run it

A Python compiler that emits Fusion node graphs, with the visual style isolated
as swappable data. All under `media-studio/`.

| Path | What it is |
|---|---|
| `studio/comp.py` | The emitter. Python structures → `.comp` text. Also the graph manifest + hash used for verification. Knows nodes; knows nothing about looks. |
| `studio/theme.py` | Themes as data, with read-tracking. Values leave tagged so hardcoded looks can be refused. |
| `studio/components/__init__.py` | Registry: discovery, spec validation, compilation, and the composition boundary (`MediaIn1`/`MediaOut1`). |
| `studio/components/grid.py` | Seeded cell grid. Carries the film's determinism argument. |
| `studio/components/reveal.py` | Plate emerges from under a wash. |
| `schema/component.schema.json` | The durable component contract. **This, not the `.comp` file, is the interface.** |
| `themes/ink-wash.json` | The only shipping theme. |
| `tests/fixtures/themes/contrast-probe.json` | Permanent test fixture. Not a throwaway — deleting it destroys the proof. |
| `tests/test_theme_binding.py` | Proves components read the theme instead of hardcoding. |
| `vendor/pysion/` | Vendored Fusion serialization library, pinned. |
| `docs/FUSION-LANE.md` | **The verified ground-truth file for this lane. Read it.** |

**Run the offline gate — this must be green before you commit anything:**

```bash
cd media-studio
make check          # docs contract + unit tests, no Resolve needed
```

**Compile a component and render it through Resolve:**

```bash
# 1. start Resolve headless (see trap 1)
# 2. then, roughly what tools/forge-comp.py should automate:
.venv/bin/python -c "
import sys; sys.path.insert(0,'.')
from studio.theme import load
from studio import components as R
from studio import comp as C
r = R.compile('grid', load('ink-wash'), {'seed': 4471}, frames=48, fps=24, instance='mark_a1')
print(C.write_comp(r['comp'], 'outputs/comps/grid.comp', 48, 24))
"
```

Then in Resolve: import a plate, make a timeline from it,
`timelineItem.ImportFusionComp(path)`, render via the Deliver API. A worked
example of every step is in `docs/FUSION-LANE.md` §6.

**Verified end to end [V]:** compile → import → render produced a real frame with
the plate visible, the mark animating, and ink multiplying into the paper.
48 frames rendered in 3.8 s on this machine (~12.5 fps).

---

## 5. What is NOT done

- **`tools/forge-comp.py` does not exist.** The three verification gates are
  designed and specified in `docs/FUSION-LANE.md` and the plan file, and the
  hard parts are proven by hand, but nothing wraps them in one command. This is
  the highest-value small piece of work remaining.
- **8 of 10 components unbuilt** — see §2 before starting them.
- **No component consumes `texture_strength` / `texture_scale`.** Those tokens
  exist in the theme but nothing reads them, so ink edges render as soft
  rectangles rather than broken ink. This is the next *look* pass and it is why
  the current render still reads slightly synthetic.
- **The film is not assembled in Resolve.** The 9:18 cut was made with ffmpeg.
- **No narration.** Ryan records it himself.

---

## 6. Assets, and their real condition

- **`../BLENDER/monero/film.json`** — the 80-beat source of truth for the film.
  ⚠️ **`BLENDER/` is not inside any git repository. This file is not version
  controlled anywhere.** It is the single most valuable and least protected
  artifact in the project. Giving it a home is the highest-priority piece of
  housekeeping. Note that `BLENDER/` no longer holds a live Blender pipeline —
  that was retired 2026-08-06 in favour of Fusion — but the script and beats are
  live. Scripts also live there: `SCRIPT-v6-voice.md` is the current draft.
- **`../cutwork/footage/monero/keyframes-v1/`** — 81 generated ink plates. About
  70 are genuinely good. Two failure modes found by inspecting all 81:
  - *photograph of the artwork* rather than the artwork: `S1-A-010`, `S1-A-040`,
    `S1-A-050`, `S1-B-030` — one of them shows a human hand holding a sheet.
  - *Chinese characters / red seal stamps*: `S2-B-010`, `S6-B-040`, `S6-B-050`,
    `S1-A-100`. The generation prompt says "no Chinese characters, no red seal
    stamp" and produced exactly that — **negation does not work on this image
    model; describe what you want positively instead.**
  - Also off-world on subject: `S1-B-010`, `S6-A-030` (photographic billboards),
    `S6-B-030` (a smartphone).
- **`../cutwork/footage/monero/style-ref/`** — 12 reference stills from a
  different show. Dead reference; the style direction settled on ink wash.

---

## 7. How generation actually works (this was misunderstood once — don't repeat it)

Image and video generation live in **`../cutwork/`**, not here. Every visual
recipe in `cutwork/config/creative.js` names its own `provider`:

- `replicate` — hosted per-image API. The `monero-ink` recipe uses this
  (flux-2-dev). This is how the 81 plates were made.
- `runcomfy` — hosted ComfyUI.
- `comfy` — **Ryan's own GPU, rented by the hour from Vast.ai**, running ComfyUI,
  reached over an SSH tunnel. This is the motion lane: Wan 2.2 i2v, LongCat
  Avatar, LTX.

Tooling: `cutwork/tools/vast.mjs` (rent/status/destroy; dry-run by default,
`--max-price` cap, destroy stops billing), `cutwork/tools/_fleet.mjs` (rent N
boxes, one tunnel each, shard work across them).

**Cost is hourly compute, not per-asset.** Any per-film dollar figure quoted
without a re-roll multiplier is a floor, not an estimate — and that multiplier
is currently not instrumented anywhere. `media-studio/studio/forge.py` records
model/prompt/cost per batch; `cutwork/tools/generate-stills.mjs` does not. Adding
that ledger to the cutwork path is a small job that would make the economics
knowable.

---

## 8. Non-negotiables (Ryan's, stated repeatedly)

- **The full-length film is the deliverable. Shorts are cut from it afterwards,
  never instead of it.**
- **Every second must be a picture.** No text cards, no slates, no "silent
  transcription" over a still. An earlier attempt at this was rejected in the
  strongest terms.
- **Pedagogy over beauty.** A shot that looks gorgeous and teaches nothing is a
  failed shot. The test for the key-image shot is whether a viewer can compare
  two marks by eye and see they match.
- **His eyes are the verdict on anything visual.** Render it, open it, let him
  judge. Never call motion or a grade good unseen.
- **No shortcuts.** Do not quietly narrow scope; say what you are not doing.
- **Report where work landed by exact path**, so verification takes seconds.

---

## 9. Suggested order of work

1. Watch `monero-picture-v1.mp4`. Nothing else makes sense before that.
2. Give `BLENDER/monero/film.json` a version-controlled home. It is unprotected.
3. Ask Ryan whether to finish the film or continue the component library. §2 is
   the argument for finishing the film; the decision is his.
4. If finishing the film: put the picture cut on a Resolve timeline, and go shot
   by shot — replace the ~10 bad plates, use the Fusion compiler only where
   exactness is the point.
5. If continuing the library: write `tools/forge-comp.py` first so components
   have a verification harness, then build components against it.
6. Either way: `make check` green before every commit. Nothing is committed as of
   this handoff — `git status` in `media-studio/` shows the day's work untracked.

---

## 10. Repo layout

`~/projects/mediaStudio/` is a **workspace, not a project** — see its `README.md`.
It holds five independent git repos side by side. Open an agent *inside* the
project you're working on, never at the workspace root.

For this work that is **`media-studio/`**, whose `AGENTS.md` is the
harness-neutral operating manual and is meant to be sufficient on its own.
`STATUS.md` is current state. `docs/JOURNAL.md` is dated history.
