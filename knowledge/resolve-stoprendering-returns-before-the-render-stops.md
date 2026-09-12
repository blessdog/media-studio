---
id: resolve-stoprendering-returns-before-the-render-stops
kind: verdict
conflict-key: what-happens-after-stoprendering-in-resolve
status: live
supersedes: []
verified-on: 2026-09-12
scope: Resolve Studio 21.1.0 on the Mac mini, stopping a Fusion CineFocus render started through the scripting API
evidence: reorder job log (StopRendering -> None at 16:43:28, CreateProject -> None at 16:43:28 and 16:43:29); mini_state.py at 16:43:30 (page None, rendering True, job Cancelled) and 16:45:05 (page deliver, rendering False)
asked-as:
  - CreateProject returns None in Resolve
  - Resolve scripting fails right after stopping a render
  - how do I know when a Resolve render has really stopped
---

**`Project.StopRendering()` returns immediately, but Resolve keeps stopping the
render behind a modal dialog. Until that finishes, `GetCurrentPage()` is None,
`IsRenderingInProgress()` stays True, and `CreateProject` / `LoadProject`
return None. Poll for a readable page and no render before the next project
operation.**

Measured 2026-09-12 on the mini. `StopRendering` returned None at 16:43:28, and
two `CreateProject` calls in the next second both returned None. At 16:43:30
the page was None and a render was still in progress, though the job already
read Cancelled. By 16:45:05 the page was `deliver` and nothing was rendering.
A CineFocus render took about 90 seconds to wind down.

Both `jobs/film-look-mini/film_mini.py` and `stack_mini.py` now wait up to 5
minutes for that state before touching a project.

Related: [[film-look-creator-renders-on-the-mini-through-a-fusion-comp]].
