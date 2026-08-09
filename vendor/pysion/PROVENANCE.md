# pysion — vendored, not installed

Upstream: <https://github.com/brunocbreis/pysion> · MIT (Bruno Reis, 2023)
Pinned at commit **`f811983d14ff64fd53209c3a632984d48cffa3a0`** (2023-09-18, the
tip of `main`).

## Why vendored rather than a dependency

**`pip install pysion` installs a different package.** PyPI's `pysion` is
"EasyVision inferencing API" v0.0.1 — unrelated to this project, different
author. Verified 2026-08-06 against the PyPI JSON API. Adding `pysion` to
`requirements.txt` would silently pull the wrong library.

Upstream has **no PyPI release and no git tags**, so there is no version to pin
in the ordinary way. It has been unmaintained since 2023-09-18. It is ~1500
lines of MIT-licensed pure Python with no runtime dependencies. Under those
conditions a pinned vendored copy is the only honest way to get a reproducible
build, and it removes the supply-chain risk of the name collision entirely.

## What it gives us

Evaluated against the three gates in the plan before adoption:

| Gate | Result |
|---|---|
| Keyframes / splines | **PASS** — `BezierSpline` with real bezier hand calculation, `Curve` presets, loop/ping-pong/step flags, and `XYPathModifier` for point inputs |
| Arbitrary connection wiring | **PASS** — `add_source_input()` / `Composition.connect()` emit `Input { SourceOp, Source }` between any two tools, not just masks |
| Round-trip into Resolve 21 | see `docs/FUSION-LANE.md` |

Also present and load-bearing for this project: `Polyline` with published points
and per-point expressions (the coin notches), `to_macro()` and `publish()` for
Route 1 Inspector-editable templates, and `add_instance()`.

## What it does NOT give us, and we add on top

`Composition.render()` emits the **`.setting`** shape — a bare
`{ Tools = ordered() {…}, ActiveTool = "…" }` table. `ImportFusionComp()` wants a
**`.comp`**: the same table wrapped in `Composition { CurrentTime, RenderRange,
GlobalRange, … }`. That wrapper, the naming/layout discipline, and the graph
manifest all live in `studio/comp.py`.

## Modifying this copy

Prefer adding to `studio/comp.py` over editing here — an untouched vendored tree
can be re-diffed against upstream. If a change here is unavoidable, record it in
this file with the reason.
