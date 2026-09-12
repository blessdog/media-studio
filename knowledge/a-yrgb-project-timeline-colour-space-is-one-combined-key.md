---
id: a-yrgb-project-timeline-colour-space-is-one-combined-key
kind: verdict
conflict-key: how-to-set-a-resolve-project-colour-space-by-api
status: live
supersedes: []
verified-on: 2026-09-12
scope: DaVinci Resolve Studio 21.1.0 on macOS, colorScienceMode davinciYRGB with the default separateColorSpaceAndGamma = '0'; not re-measured for the colour-managed modes or with the split toggle on
evidence: docs/CINEMATIC-PIPELINE-VERIFY.md; tools/ingest-osmo.py PROJECT_COLOUR; the SetSettings probe run 2026-09-12 (values below)
asked-as:
  - how do I set the timeline color space through the scripting API
  - SetSettings colorSpaceTimeline returns False
  - what value does colorSpaceTimelineGamma take
  - new Resolve project defaults to Rec.709 Scene not Gamma 2.4
---

**In a DaVinci YRGB project the timeline colour space is ONE combined value,
`colorSpaceTimeline = 'Rec.709 Gamma 2.4'`. The split keys the API stub
documents as examples (`'Rec.709'` plus `colorSpaceTimelineGamma = 'Gamma 2.4'`)
are rejected, and a fresh project starts at `'Rec.709 (Scene)'`, so the stamp
is not optional.**

Measured 2026-09-12 on the smoke project `2026-09-12-osmo-smoke@4005f132`:

| call | result |
|---|---|
| `SetSettings({'colorScienceMode': 'davinciYRGB'})` | True |
| `SetSettings({'colorSpaceTimeline': 'Rec.709'})` | False |
| `SetSettings({'colorSpaceTimelineGamma': 'Gamma 2.4'})` | False |
| `SetSettings({'colorSpaceTimeline': 'Rec.709 Gamma 2.4'})` | True, reads back identically |
| `SetSettings({'colorSpaceOutput': 'Rec.709'})` | False |

Mechanism: `separateColorSpaceAndGamma` was `'0'`, so the gamma key is empty
and the space key carries both halves as one menu string. The stub's docstring
examples describe the split mode. Read `GetSettings()` first and match the
shape of the value you see there, then read it back after setting.

Related: [[osmo-d-log-m-into-resolve-goes-through-the-idt-dctl]],
[[compile-py-still-uses-project-setsetting-resolve]].
