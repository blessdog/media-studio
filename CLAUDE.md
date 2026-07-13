# CLAUDE.md — media-studio

**Read `AGENTS.md` first** — it is the harness-neutral operating manual (what
this project is, the working loop, the CLI verbs, hard doctrine). This file
only adds what is specific to working with Ryan. Then `STATUS.md` +
`docs/PLAN.md` for live state and the phase map. The bible lives at
`../bible/README.md`; judge all architecture against it.

## Locked decisions (full detail in AGENTS.md + docs/PLAN.md)

- **Copilot, not autopilot** (Ryan, 2026-07-12). He makes the videos; the
  system co-edits in the loop. No one-shot brief→video, ever.
- Resolve Studio only; edits computed OUTSIDE Resolve (Story IR → OTIO →
  import); one-way flow — scripts never touch a human-edited timeline.
- Grades/templates: agents apply, Ryan authors. Curated libraries, his eyes
  gate entry.
- Adopt `samuelgursky/davinci-resolve-mcp`; no bespoke editing surfaces;
  no rival servers.
- Portability doctrine: the AI is a replaceable component. Anything
  load-bearing lives in the repo, never only in harness memory. AGENTS.md
  must stay sufficient for a cold-start agent (that's a recurring test).

## How to work with me (Ryan)

- **Pressure-test before agreeing**; argue the "we don't need this" side first.
- **Verify before you assume**: `ls` / `git ls-files` before any claim about
  what exists. (This project exists because an unverified assumption about
  bongpot burned a session.)
- **Trust but verify**: read actual files/diffs/outputs, never summaries.
  Report WHERE work landed by exact path so verification takes seconds.
- **Mentor mode**: name principles and industry terms while working.
- **Architecture and trust boundaries are Ryan's calls.** Propose options.
  Do not build past a blocked [RYAN] decision (open ones: ARCHITECTURE.md
  §Open decisions).
- **Small commits**, one concern each, search-bait subjects. Tags before pivots.
- **His eyes are the verdict on anything visual** — render it and `open` it;
  never declare motion or a grade good unseen. Zero GUI scavenger hunts.
- **Plan through dialogue.** Before each phase's build, run a real
  question-round with him (AskUserQuestion) covering how HE will use it;
  he approves plans top-down: full scope first, then drill-in.
