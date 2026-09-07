---
id: auto-editor-multi-input-drops-inputs-from-v3-export
kind: refuted
conflict-key: how-to-silence-strip-several-recordings-in-one-pass
status: live
supersedes: []
verified-on: 2026-09-07
mechanism: on the v3 export path the first input is consumed as the templateFile (stream rotation and attachment passthrough), not as content, so only the last input's kept spans reach the timeline
asked-as:
  - can auto-editor take multiple input files at once
  - how do I concatenate several recordings and strip silence in one pass
  - why does the v3 timeline only contain one of my input files
  - should ingest-recording accept more than one file
---

**Dead end: passing several recordings to one auto-editor call and reading its
v3 timeline export. The export came back with only the LAST input.**

Mechanism, measured 2026-09-07 with auto-editor 29.3.1:

    auto-editor A.mp4 B.mp4 --export v3 -o multi.v3

A alone yields 4 kept spans and B alone yields 16. The multi-input export held
16 clips, every one with `src` = B. A's spans were not present at all. The
docs say multiple inputs "concat horizontally" and that the first input becomes
the `templateFile` for stream rotation and attachment passthrough, so the
first file is being read as a template, not as content, on the v3 path.

So the studio does not analyse several recordings in one auto-editor call.
Each recording is ingested on its own (`tools/ingest-recording.py`, one
workspace each, one transcript each) and `tools/ingest-session.py` concatenates
the per-recording IRs at the IR level with a running record offset. That path
already has schema validation, lint and an idempotent compile, which a
single-call concat would have bypassed.

Retry only if the premise changes: a newer auto-editor whose changelog names
multi-input v3 export, re-measured with the same two files.
