---
id: edit-ir-find-does-not-work-on-a-multi-recording-
kind: open
conflict-key: should-we-edit-ir-find-does-not-work-on-a-multi-recording-
status: live
supersedes: []
proven: false
verified-on: 2026-09-07
asked-as:
  - edit-ir find does not work on a multi-recording session workspace
  - edit ir find does not work on a multi recording 
  - why is edit-ir.py find like this
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## edit-ir find does not work on a multi-recording session workspace

**Why it matters:** moments.spans_from_ir raises 'need asset_id' when track 1 references more than one asset, so a session workspace built by tools/ingest-session.py cannot be searched by phrase and the assembly dialogue (insert where I say X) is unavailable on exactly the timeline that needs it most

**Where it lands:** `studio/moments.py spans_from_ir, tools/edit-ir.py find`

**First step:** read <ws>/sources.json, search every source transcript, map each hit through that source's own spans plus its record offset from the session IR

Bookmarked 2026-09-07 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
