---
id: reshoot-the-osmo-test-with-nd-filters-arriving-2
kind: open
conflict-key: should-we-reshoot-the-osmo-test-with-nd-filters-arriving-2
status: live
supersedes: []
proven: false
verified-on: 2026-09-16
asked-as:
  - Reshoot the Osmo test with ND filters (arriving 2026-09-17), 24p at 1/48
  - reshoot the osmo test with nd filters arriving 2
  - why is CINEMATIC-PIPELINE-VERIFY.md row 29 for the baseline numbers like this
  - what is blocking Reshoot the Osmo test with ND filters (a
---

**This is a PLAN, not a finding. `proven: false`. Do not build against it.**

## Reshoot the Osmo test with ND filters (arriving 2026-09-17), 24p at 1/48

**Why it matters:** the first Osmo clip clipped the sky in camera: 1.9 to 3.2% of pixels at the maximum code in the 60 s and 300 s frames, which no grade recovers; it was also shot at 29.97, while grades/film-look/README.md calls for 24 or 25 at 1/48 or 1/50

**Where it lands:** `outputs/osmo/<date>-nd-test/, docs/CINEMATIC-PIPELINE-VERIFY.md row 29 for the baseline numbers`

**First step:** shoot D-Log M 10-bit 24p 1/48 with ND (sunny ND64, overcast ND8-16), same backyard walk; measure % of pixels at max code at matching moments against row 29, then run dctl_film_mini.py --input dji-action5-dlogm --fps 24

**Blocked on:** ND filters arrive 2026-09-17

Bookmarked 2026-09-16 at the moment of deferral, because the record of a deferral is what fails, not the decision to defer.
