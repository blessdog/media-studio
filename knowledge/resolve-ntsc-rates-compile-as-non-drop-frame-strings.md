---
id: resolve-ntsc-rates-compile-as-non-drop-frame-strings
kind: verdict
conflict-key: how-to-compile-a-2997-or-23976-timeline
status: live
supersedes: [studio-lint-refuses-a-1001-denominator-frame-rat]
verified-on: 2026-09-12
scope: Resolve Studio 21.1.0 through studio.compile (OTIO import); 30000/1001 measured on IMG_0888.mov, iPhone 17 Pro HEVC 1080p; 24000/1001 and 60000/1001 covered only by the unit test of the mapping
evidence: outputs/projects/2026-09-12-iphone-hevc-test/ ingest run (compiled 2026-09-12-iphone-hevc-test@834f402b, verify green); tests/test_osmo.py resolve_rate checks
asked-as:
  - can the studio compile 23.976 or 29.97 footage
  - timeline frame rate 29.97 fails to set
  - lint says drop-frame-ish rate
  - iPhone 30 fps clip won't compile in Resolve
---

**A 1001-denominator clip compiles once the project rate is stamped as the menu
string Resolve uses, `'23.976'`, `'29.97'` or `'59.94'`, non-drop-frame.
`studio.ir.resolve_rate()` is that mapping; compile and verify both use it.**

The bookmark this supersedes named the wrong blocker. `studio.lint` never
refused these rates: it appends a `warning:` string and `lint()` filters those
into warnings on return. The real faults were `compile.py` stamping
`str(float(30000/1001))` = `'29.97002997002997'`, which is not a frame rate
Resolve's menu offers, and `verify.py` comparing float strings. Plus the block
this session had put into `tools/ingest-osmo.py` on the bookmark's word.

Measured 2026-09-12: IMG_0888.mov (30000/1001) ingested, compiled and passed
structure verify with the lint warning `NTSC rate 30000/1001, stamped as
Resolve non-drop-frame '29.97'`.

`COMPILER_EPOCH` was not bumped: /1-rate IRs compile identically, and a stale
project made by the old code for a 1001 rate carries the wrong rate, which
verify now reports loudly rather than reusing silently.

Related: [[a-yrgb-project-timeline-colour-space-is-one-combined-key]].
