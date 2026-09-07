# 2026-09-07 — thirteen recordings, one timeline

Ryan: *"I have a ton of movie clips I've made while I'm building in public in
SSDrive/movies. Let's test the Media Studio's ability to edit together a
coherent single video — is that even possible?"*

## Tried

Read the studio before touching it. The Story IR schema has `assets` as a
list and `edits` keyed by asset id; the emitter places every track-1 edit by
record frame and mirrors it onto A1; lint only refuses overlaps and missing
files. So several recordings on one spine were always legal. What did not
exist was a way in: `ingest-recording.py` takes exactly one file.

Searched before building (LAW #0). RoughCut, Cutsio, Selects and Resolve's
own text-based editing all assemble rough cuts from transcripts. Every one
owns the timeline, which is the thing this studio's one-way flow forbids.
Then tried the closest existing tool in the repo: auto-editor accepts several
inputs.

## Happened

auto-editor's multi-input v3 export dropped the first file. Two inputs with 4
and 16 kept spans came back as 16 clips, all from the second file. Recorded
as a refuted claim with the mechanism (the first input is read as the
`templateFile`, not as content).

Ingested all thirteen recordings one at a time — 87 minutes raw, Deepgram
returned real utterances on eleven, the two silent ones are B-roll. Wrote
`tools/ingest-session.py`: concatenates per-recording IRs with a running
record offset, a Cyan marker at each source head, `sources.json` for
provenance. First run: 976 edits, 39.5 minutes, compiled and verified in
Resolve 21.0.4.5. A three-recording subset rendered end to end with the
loudness check green.

That is a concat, not a video. Read the thirteen transcripts, mapped the
story, and added `--cuts`: a JSON list of source windows in seconds, in
order, each with a note. Nineteen cuts became a 9.5-minute rough cut,
rendered and opened. One cut failed because its window fell entirely inside
stripped silence; the tool refuses rather than emitting an empty cut.

## Then the machine ran out

Ryan, mid-session, with Activity Monitor open: 13.5 of 16 GB used, Resolve
at 2.4 GB, swap in use. *"It's stressing out this machine. There's a project
one directory up called OneMachine that allows you to offload work to my
Mac Mini… so we can render everything there. That thing is just sitting
idle."* OneMachine turned out to be research, not code: a 2026-08-08 report
whose worked example is literally a Media Studio render, and whose verdict
is that the mini is a job runner, not more compute.

Measured the mini before building: M1, 8 GB with ~60 MB free, 7.3 GB of
disk, no Resolve, ffmpeg 8.1.2 and tmux, a Monero node and the JobHard
gateway resident. Resolve's Remote Rendering needs Studio on both machines,
a shared Postgres project library and identical media paths. Out by
measurement. What the mini can do is ffmpeg, and a straight-cut timeline is
trims plus concat.

Four mechanisms surfaced on the way, each now in the code or the store:
`-t` under `-copyts` measures against the source clock (a 262-byte staged
file); four-decimal trim durations keep an extra frame on half the segments
(21 frames over 56); runs that merge across gaps in one recording stage
16 GB from a 33-minute clip; and an mp4 without faststart cannot be piped.
The shape that survived: stage locally, pipe each run over ssh into ffmpeg
on the mini, concat there, pull back. Nothing staged touches the mini's
disk. Proof cut: 25 s on the mini, frame-identical to the local control.

## Mechanism

The IR was designed as a tagged list of edits over a list of assets rather
than "one recording plus overlays", so multi-source was free. The front door
was single-file because every earlier film had one recording. The cut list
is readable and diffable because the film's decisions belong in the job
folder, not in a Resolve project nobody can grep.

## Verdict

- **Works:** many recordings on one spine; a cut list as the film's edit.
- **Open, Ryan's:** which moments stay (Huberman rant, power washer, music
  bleed in recording 10), and the length.
- **Refuted:** one auto-editor call over several inputs.
- **Bookmarked:** transcript search on a session workspace, camera isolates
  in `movies/iso`, the missing `docs/STORY-IR.md`.

Evidence: `jobs/build-in-public/evidence/contact-sheet-13-recordings.png`.
Renders live in `outputs/projects/build-in-public-cut/render/` (gitignored,
regenerable from `cuts.json`).
