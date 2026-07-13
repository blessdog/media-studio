"""Find moments in a recording via its transcript, and map source time onto
the cut timeline an IR describes.

This is how "insert it where I say X" becomes a frame number: word-level
Deepgram timestamps -> source seconds -> source frame -> record frame through
the IR's kept spans.
"""
import re
from fractions import Fraction

_PUNCT = re.compile(r"[^\w']+")


def _norm(word):
    return _PUNCT.sub("", word).lower()


def find(transcript, phrase):
    """All occurrences of `phrase` in the word stream.

    Returns [{"start": sec, "end": sec, "text": matched-words}] in source
    time. Match is case/punctuation-insensitive on the word sequence.
    """
    words = transcript.get("words", [])
    tokens = [t for t in (_norm(w) for w in phrase.split()) if t]
    if not tokens or not words:
        return []
    normed = [_norm(w.get("word", "")) for w in words]
    hits = []
    for i in range(len(normed) - len(tokens) + 1):
        if normed[i:i + len(tokens)] == tokens:
            span = words[i:i + len(tokens)]
            hits.append({
                "start": span[0]["start"],
                "end": span[-1]["end"],
                "text": " ".join(w.get("punctuated_word", w["word"]) for w in span),
            })
    return hits


def src_to_record(src_frame, spans):
    """Map a source frame to its timeline frame via kept spans (None if cut)."""
    for s in spans:
        if s["srcIn"] <= src_frame < s["srcOut"]:
            return s["record"] + (src_frame - s["srcIn"])
    return None


def spans_from_ir(ir, asset_id=None):
    """The kept-span map implied by the IR's track-1 edits of the recording."""
    if asset_id is None:
        t1 = {e["asset"] for e in ir["edits"] if e.get("track", 1) == 1}
        if len(t1) != 1:
            raise ValueError(
                f"need asset_id: track 1 references {len(t1)} assets, not 1")
        asset_id = t1.pop()
    spans = [{"srcIn": e["srcIn"], "srcOut": e["srcOut"], "record": e["record"]}
             for e in ir["edits"]
             if e["asset"] == asset_id and e.get("track", 1) == 1]
    return sorted(spans, key=lambda s: s["record"])


def record_frame(ir, src_seconds, asset_id=None):
    """Source seconds -> record frame on the cut timeline (None if cut away)."""
    fps = Fraction(ir["timebase"]["fps"])
    src_frame = int(round(src_seconds * fps))
    return src_to_record(src_frame, spans_from_ir(ir, asset_id))


def timecode(frames, fps):
    """Frames -> m:ss.s display string (for humans reading CLI output)."""
    secs = frames / float(fps)
    return f"{int(secs // 60)}:{secs % 60:04.1f}"
