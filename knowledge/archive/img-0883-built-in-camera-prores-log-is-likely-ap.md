---
id: img-0883-built-in-camera-prores-log-is-likely-ap
kind: open
conflict-key: should-we-img-0883-built-in-camera-prores-log-is-likely-ap
status: superseded
supersedes: []
proven: false
verified-on: 2026-09-12
asked-as:
  - IMG_0883 (built-in Camera ProRes Log) is likely Apple Log, not Apple Log 2: its colour primaries tag is bt2020, and Apple documents Log 2 only in Final Cut Camera. The Resolve renders set Input Color Space 'Apple Log 2', so re-verify with Resolve's own auto-detected input space and re-render with 'Apple Log'
  - img 0883 built in camera prores log is likely ap
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## IMG_0883 (built-in Camera ProRes Log) is likely Apple Log, not Apple Log 2: its colour primaries tag is bt2020, and Apple documents Log 2 only in Final Cut Camera. The Resolve renders set Input Color Space 'Apple Log 2', so re-verify with Resolve's own auto-detected input space and re-render with 'Apple Log'

**Why it matters:** The log render Ryan judged unimpressive may have used the wrong input transform; the claim a-print-lut-needs-a-cineon-working-space-in-resolve measured contrast and saturation on that mislabelled conversion

Bookmarked 2026-09-12 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
