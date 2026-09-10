---
id: every-ingest-and-build-tool-should-write-sha256-
kind: open
conflict-key: should-we-every-ingest-and-build-tool-should-write-sha256-
status: live
supersedes: []
proven: false
verified-on: 2026-09-09
asked-as:
  - Every ingest and build tool should write sha256 into IR assets, so reconformed media at the same path compiles a NEW timeline instead of reusing the cached one
  - every ingest and build tool should write sha256 
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## Every ingest and build tool should write sha256 into IR assets, so reconformed media at the same path compiles a NEW timeline instead of reusing the cached one

**Why it matters:** measured 2026-09-09 on summer-reel: after reconforming three clips in place, compile-ir reported 'reused cached timeline' and Resolve kept pointing at stale media; only jobs/summer-reel/build.py hashes today. Where it lands: studio/ingest.py, ingest-session, ingest-song, ingest-bongpot, studio/intake.file_media. First step: add a helper in studio/ir.py that fills sha256 for every asset and call it from every producer

Bookmarked 2026-09-09 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
