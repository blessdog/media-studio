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
