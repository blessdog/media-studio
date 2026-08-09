# The Fusion lane — verified ground truth

*Started 2026-08-06. Everything marked **[V]** was measured on this machine, not
inferred. **[U]** is unverified and must not be built on until it is. When this
file and the code disagree, the code wins — then fix this file.*

The animation substrate moved from Blender to Fusion. Blender produced correct
geometry that composited as grey cut-outs on a painted plate, because an alpha
`Over` merge of opaque 3D geometry can only sit on paper, never soak into it.
Fusion merges in Multiply against the plate's own grain. Plan:
`~/.claude/plans/serene-popping-raven.md`.

---

## 1. Headless is the only sane way to drive Resolve **[V]**

**With the GUI running, an open Project Manager blocks every mutating API call
while leaving reads working.** This is the trap `STATUS.md` records as costing a
full session, and it is worse than documented — it is not just that
`GetCurrentPage()` returns `None` as a warning sign. Measured 2026-08-06 on
Resolve Studio 21.0.2.4 with the PM on screen:

| Call | Result |
|---|---|
| `GetCurrentProject()` | works — returns a live Project |
| `GetProjectListInCurrentFolder()` | works — 98 projects |
| `CreateProject(name)` | **`None`** |
| `LoadProject(name)` | **`None`** |
| `OpenPage('edit')` | **`None`** |
| `MediaPool.CreateEmptyTimeline()` | **`None`** |
| `GetCurrentPage()` | **`None`** |

Reads succeeding is what makes it dangerous: a script gets a plausible Project
object and then silently no-ops.

**Headless has none of this** — launch with:

```
"/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve" -nogui
```

API up in **9 seconds**, `GetCurrentPage()` returns `'media'` (a real page, not
`None`), and `CreateProject` works. There is no Project Manager to be modal.
**Automated compilation and rendering should always run headless.**

### The restart script misdiagnoses a TCC denial **[V]**

`scripts/restart_resolve.py` quits via `osascript -e 'quit app "DaVinci
Resolve"'`. On this machine that is denied by TCC (same family as the
`System Events`/`osascript is not allowed assistive access` and `screencapture`
denials), and the attempt produces **no Resolve log entry at all**. The script
reports `FAIL: Resolve did not exit within 60s (dialog blocking?)`, which points
at the wrong cause and sent one investigation down a dead end.

`kill -TERM <pid>` exits Resolve gracefully in ~10s and needs no permission.
`SIGKILL` was not required. **[U]** whether TERM is always safe mid-render.

---

## 2. Route 2 confirmed: the plate really does arrive as `MediaIn1` **[V]**

On a still imported into a timeline, `timelineItem.AddFusionComp()` returns a
Composition containing **exactly two tools**:

```
1  MediaIn   MediaIn1     <- the plate
2  MediaOut  MediaOut1
```

So a Route 2 component can wire `Background = MediaIn1/Output` and multiply into
the plate without importing it separately. This is the mechanism Blender could
not offer and the reason the key-image shot moved here.

Also measured: a PNG imports at **120 frames** at 24 fps (this project's still
duration = 5s), not the 150 that `studio/templates.py` records for the title
path.

### Read-back API shape **[V]**

```python
tools = comp.GetToolList(False)      # -> dict {1: Tool, 2: Tool, ...}
tool.ID                              # 'MediaIn'   (registry type)
tool.Name                            # 'MediaIn1'
tool.GetAttrs()['TOOLS_RegID']       # 'MediaIn'
tool.GetAttrs()['TOOLS_Name']        # 'MediaIn1'
```

`GetToolList` is keyed by integer index, so tool identity comes from `.Name`,
never from position.

---

## 3. pysion: adopted, vendored, pinned **[V]**

`vendor/pysion/`, upstream `brunocbreis/pysion` at `f811983` (2023-09-18), MIT.
Full reasoning in `vendor/pysion/PROVENANCE.md`. Two findings worth repeating:

- **`pip install pysion` installs a different package.** PyPI's `pysion` is
  "EasyVision inferencing API" v0.0.1 — different author, unrelated. Never add
  it to `requirements.txt`.
- **`vendor/` was in `.gitignore`**, so the vendored tree would not have been
  committed and a fresh clone would not have compiled. `.gitignore` now excludes
  `vendor/*` and re-includes `vendor/pysion/`.

Its README claims far less than the code does. Verified present and working:
`BezierSpline` with real bezier hand calculation, `XYPathModifier` for point
animation, arbitrary `SourceOp` wiring via `add_source_input`/`connect`,
`Polyline` with published points and per-point expressions, `to_macro()` and
`publish()` for Route 1 Inspector controls, and `add_instance()`.

What it does not do, and `studio/comp.py` adds: the `Composition { … }` wrapper
with `RenderRange`/`GlobalRange` that makes a `.comp` rather than a `.setting`,
readable node naming and flow layout, and the graph manifest.

`RGBA.__post_init__` premultiplies, and arithmetic on a tagged float returns a
plain float — which silently stripped theme provenance until `comp.themed_color()`
was added to reapply it.

---

## 4. The theme-binding test had a blind spot **[V]**

The binding assertions prove a component's `consumes` declaration matches its
behaviour. They **cannot** catch a value that is both hardcoded *and*
undeclared: that combination is self-consistent. Verified by planting a
component that hardcoded `ApplyMode="Multiply"` and removed `merge_mode` from
`consumes` — it passed every binding assertion. Only the supplemental lint
caught it, and lint was explicitly ruled out as the gate.

Closed structurally rather than by more linting: theme values leave `Theme`
wearing a `Themed` marker (`studio/theme.py`), and `comp.check_look_binding()`
refuses any look-bearing Fusion input holding an untagged literal. The plant now
fails at compile. `themed_color()` and `derive()` refuse untagged input, so the
tag cannot be laundered.

---

## 5. `ImportFusionComp` REPLACES the comp — emit MediaIn/MediaOut yourself **[V]**

The single most dangerous finding so far, and a textbook silent failure.

`AddFusionComp()` creates `MediaIn1` and `MediaOut1` for you. **`ImportFusionComp()`
discards them**, replacing the entire composition with the file's contents. A
generated comp that merely *references* `SourceOp = "MediaIn1"` therefore imports
into a comp where no such tool exists.

Measured on 21.0.4.5 with a comp that referenced but did not emit them:

```
tools back      : 19   (all 18 emitted tools + the spline, correct names + types)
MediaIn present : False
MediaOut present: False
mark_a1_stain.Background  value=None  connected_from=None     <- dangling
```

**Every name and type matched. A tool-count check passes this. The comp renders
nothing**, because there is no MediaOut at all and the plate never arrives.

Fixes, both landed:

- `studio/components/__init__.py:compile()` emits `MediaIn1` (when referenced)
  and always wires `MediaOut1` to the component's returned output. The
  composition boundary belongs to the registry, so no component can forget.
- `comp.lint_graph()` no longer whitelists those names — a reference without a
  matching tool is an error, and it now requires exactly one `MediaOut`.

After the fix: `Background <- MediaIn1`, `Foreground <- mark_a1_pop`,
`MediaOut1.Input <- mark_a1_stain`, `ApplyMode='Multiply'`, `Blend=0.88`.

## 6. Full round-trip and render **[V]** — 21.0.4.5

`grid` seed 4471 → generated `.comp` → `ImportFusionComp` → Deliver render
(3.8s for 48 frames, H.264). Confirmed **in pixels**, not just in the graph:

- the plate binds — the ink-wash coin is present, so `MediaIn1` resolves to the
  clip's media
- the mark is absent early, pops in, overshoots and settles — the `BezierSpline`
  survived the trip and drives the render
- `Multiply` genuinely stains: paper grain reads through the ink

Art direction needed one pass: at `cell_size` 0.028 with `edge_softness` 0.0035
the mark was sub-pixel-soft and unreadable, and centred at (0.5, 0.5) it sat
behind the coin. Theme now ships `edge_softness` 0.014 / `bleed` 0.010.
**Still missing:** `texture_strength` and `texture_scale` exist as tokens but no
component consumes them yet, so cell edges are soft rectangles rather than
broken ink. That is the next look pass.

The format did NOT drift across 21.0.2.4 → 21.0.4.5 — a comp authored under the
old version imported clean under the new one.

## 7. Open

- **[U] Gate 3 — full graph round-trip.** `AddFusionComp` and the read-back
  shape are verified; importing a *generated* `.comp` via `ImportFusionComp` and
  diffing the full manifest is not yet done. Interrupted by a Resolve update on
  2026-08-06.
- **Re-baseline after the update.** `resolveVersion` in every `approval.json`
  and the pinned version in verification gate 3 are keyed to **21.0.2.4**. The
  update is a free real-world test of the premise behind demoting `.setting` to
  a build artifact: if the serialization moved, one emitter changes and every
  component spec survives. Check whether a comp written under 21.0.2.4 still
  imports clean.
- **[U]** whether `-nogui` renders Fusion comps identically to the GUI. Assumed;
  unmeasured.
