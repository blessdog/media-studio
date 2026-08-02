"""Ingest lane: recording -> Story IR (silence-stripped, transcript-anchored).

build_ir() is pure assembly; transcription and silence analysis are injected
results so each piece stays testable and the network stays optional.
"""
from fractions import Fraction
from pathlib import Path

from .moments import src_to_record as _src_to_record

MARKER_COLORS = ["Sky", "Mint", "Lemon", "Rose", "Lavender", "Sand"]


def _to_frames(seconds, fps):
    return int(round(seconds * fps))


def build_ir(name, recording, meta, timebase, spans, transcript=None, created_by="ingest"):
    """Assemble a Story IR dict from analysis results.

    meta: studio.probe.probe() output. timebase: rational string from silence
    analysis (source-true). spans: loud_spans() output. transcript: optional
    {utterances: [...]} with float-second times.
    """
    recording = Path(recording).resolve()
    fps = Fraction(timebase)

    edits = []
    for i, s in enumerate(spans):
        edits.append({
            "id": f"e{i}",
            "asset": "rec",
            "srcIn": s["srcIn"],
            "srcOut": s["srcOut"],
            "record": s["record"],
            "track": 1,
        })

    markers = []
    if transcript:
        for u in transcript.get("utterances", []):
            src_f = _to_frames(u["start"], fps)
            rec_f = _src_to_record(src_f, spans)
            if rec_f is None:
                continue  # utterance starts inside a cut region
            markers.append({
                "frame": rec_f,
                "color": MARKER_COLORS[u.get("speaker", 0) % len(MARKER_COLORS)],
                "name": f"S{u.get('speaker', 0)} {u['id']}",
                "note": u["text"][:180],
            })
        # attach evidence: utterances overlapping each edit's source range
        for e in edits:
            ev = [u["id"] for u in transcript.get("utterances", [])
                  if _to_frames(u["end"], fps) > e["srcIn"]
                  and _to_frames(u["start"], fps) < e["srcOut"]]
            if ev:
                e["evidence"] = ev

    return {
        "irVersion": "0.1",
        "name": name,
        "timebase": {"fps": timebase},
        "resolution": {"width": meta["width"], "height": meta["height"]},
        "assets": [{"id": "rec", "path": str(recording), "kind": "video"}],
        "edits": edits,
        "markers": markers,
        "provenance": {"generator": "ingest-v0", "createdBy": created_by},
    }


def build_song_ir(name, song, duration_secs, fps="30/1", width=1920,
                  height=1080, created_by="ingest-song"):
    """Assemble a Story IR whose spine is a SONG, not a recording of speech.

    The talking-head front door (build_ir) does not fit music: it strips
    silence, which would gut a track's rests and breakdowns, and it anchors
    edits to diarized utterances, which a song does not have. So this is a
    separate front door rather than a flag on that one.

    The song lands whole and uncut on **A1** — the untouched audio spine
    (docs/PLAN.md:50). Nothing later may write A1; visuals go on V1+ and are
    expected to be silent, which Scene Forge output already is. Found footage
    carrying its own audio will collide on A1 and lint will refuse it — that
    is correct: in a music video the song owns the audio.
    """
    song = Path(song).resolve()
    rate = Fraction(fps)
    frames = max(int(round(float(duration_secs) * rate)), 1)

    return {
        "irVersion": "0.2",
        "name": name,
        # NOT str(rate): Fraction drops a denominator of 1, so "30/1" would
        # round-trip as "30" and studio.ir.fps() splits on "/" and blows up.
        "timebase": {"fps": f"{rate.numerator}/{rate.denominator}"},
        "resolution": {"width": int(width), "height": int(height)},
        "assets": [{"id": "song", "path": str(song), "kind": "audio"}],
        "edits": [{"id": "song0", "asset": "song", "srcIn": 0,
                   "srcOut": frames, "record": 0, "track": 1}],
        "markers": [],
        "provenance": {"generator": "ingest-song-v0", "createdBy": created_by},
    }
