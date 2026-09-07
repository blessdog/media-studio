---
id: the-mini-renders-the-story-ir-with-ffmpeg-not-resolve
kind: verdict
conflict-key: how-does-a-render-leave-the-macbook
status: live
supersedes: []
verified-on: 2026-09-07
scope: straight-cut timelines (track-1 edits only) rendered from a workspace's story.json; the Mac mini as it was measured 2026-09-07 (M1, 8 GB, no Resolve, ffmpeg 8.1.2, ~7 GB disk free, JobHard and a Monero node resident)
evidence: outputs/projects/build-in-public-proof/render/build-in-public-proof-mini.mp4 (2139 frames, identical count and duration to the local ffmpeg control); docs/journal/2026-09-07-thirteen-recordings-one-timeline.md
asked-as:
  - how do I render on the Mac mini
  - can DaVinci Resolve remote rendering use the mini
  - why is rendering stressing the MacBook and what moves it
  - how does render-ir --on mini work
---

**A render leaves this MacBook as ffmpeg over the Story IR (`tools/render-ir.py
<ws> --on mini`), not as a Resolve render. Resolve's own Remote Rendering is
disqualified on this mini by measurement.**

Why Resolve cannot go there, measured 2026-09-07: Resolve Remote Rendering
needs Studio installed on both machines, a shared Postgres project library,
and the media at identical paths on both. The mini has no Resolve, 8 GB of
RAM with ~60 MB free at rest (a Monero node at 620 MB and the OpenClaw
gateway at 240 MB are resident), and 7.3 GB of disk. Resolve's floor is 8 GB
total.

What works instead: a straight-cut timeline is trims + concat, which ffmpeg
does with bounded memory. The tool stages keyframe-padded stream copies of
only the windows the cut uses (no decode, `-copyts` so a seek on the staged
file lands on the same frame as the original), ships them with rsync at
~100 MB/s, encodes one run at a time under tmux at nice 10, deletes each
staged file as it encodes, refuses when the mini lacks disk, pulls the mp4
back and removes its own directory. The proof cut: 0.92 GB shipped in 24 s,
encoded in 15 s, frame count and duration identical to the local control.

Two mechanisms that bit on the way and are now in the code:
- `-t` with `-copyts` measures against the SOURCE clock, so a window at
  1605 s stopped before its first packet (a 262-byte file). Use `-to`.
- `trim=duration=` at four decimals rounds 0.966667 up to 0.9667 and keeps
  one extra frame on half the segments (21 frames over 56). Use
  `start=`/`end=` at six decimals.

Not covered by this verdict: overlays (V2+), graphics, grades, music lanes.
Those still render through Resolve on this machine.
