---
id: studio-lint-refuses-a-1001-denominator-frame-rat
kind: open
conflict-key: should-we-studio-lint-refuses-a-1001-denominator-frame-rat
status: superseded
supersedes: []
proven: false
verified-on: 2026-09-12
asked-as:
  - studio.lint refuses a 1001-denominator frame rate (23.976) as an error; the Osmo may write 23.976
  - studio lint refuses a 1001 denominator frame rat
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## studio.lint refuses a 1001-denominator frame rate (23.976) as an error; the Osmo may write 23.976

**Why it matters:** lint.py line 40 appends 'drop-frame-ish rate' to errors, so a 23.976 clip cannot compile; decide NDF handling when the first Osmo clip shows its real rate (VERIFY 12 in docs/CINEMATIC-PIPELINE-VERIFY.md)

Bookmarked 2026-09-12 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
