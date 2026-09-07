---
id: docs-story-ir-md-is-cited-by-status-md-and-agent
kind: open
conflict-key: should-we-docs-story-ir-md-is-cited-by-status-md-and-agent
status: live
supersedes: []
proven: false
verified-on: 2026-09-07
asked-as:
  - docs/STORY-IR.md is cited by STATUS.md and AGENTS.md but does not exist
  - docs story ir md is cited by status md and agent
  - why is emit.py docstring like this
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## docs/STORY-IR.md is cited by STATUS.md and AGENTS.md but does not exist

**Why it matters:** the Story IR contract is documented only in schema/story-ir.schema.json and docstrings; a cold agent following the manual hits a dead link and the docs test does not catch a missing doc, only a missing tool

**Where it lands:** `STATUS.md 'Where things live', AGENTS.md, studio/emit.py docstring`

**First step:** git log --all --full-history -- docs/STORY-IR.md to see whether it was deleted or never written, then restore or write it and add a link check to tests/test_docs.py

Bookmarked 2026-09-07 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
