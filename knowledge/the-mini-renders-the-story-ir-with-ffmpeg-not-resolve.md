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
file lands on the same frame as the original, faststart so the file can be
piped), then pipes each staged run over ssh straight into ffmpeg on the mini
at nice 10, so nothing staged is written to the mini's disk; the disk gate
counts only the encoded runs plus the concat copy. It concats there, pulls
the mp4 back and removes its own directory. The MacBook stays awake to feed
the pipe. The proof cut: 5 runs, 1.28 GB staged, 25 s on the mini, frame
count and duration identical to the local control.

Four mechanisms that bit on the way and are now in the code:
- `-t` with `-copyts` measures against the SOURCE clock, so a window at
  1605 s stopped before its first packet (a 262-byte file). Use `-to`.
- `trim=duration=` at four decimals rounds 0.966667 up to 0.9667 and keeps
  one extra frame on half the segments (21 frames over 56). Use
  `start=`/`end=` at six decimals.
- Runs that merge across gaps in one recording stage the whole span: eight
  cuts from a 33-minute clip became one 31-minute window, 16 GB. Runs split
  at gaps over 5 s.
- An mp4 whose moov atom is at the end cannot be demuxed from a pipe. Stage
  with `-movflags +faststart`.

Not covered by this verdict: overlays (V2+), graphics, grades, music lanes.
Those still render through Resolve on this machine.
