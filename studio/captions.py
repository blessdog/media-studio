"""Captions: Deepgram transcript -> SRT cues (pure), for platform delivery
and Resolve subtitle import. Native in-Resolve captioning also exists
(Timeline.CreateSubtitlesFromAudio, Studio AI) — that's the CLI's --native.

Cue policy: one cue per utterance; long utterances split on word timings so
no cue exceeds MAX_CHARS or MAX_SECONDS; text wrapped to two lines.
"""
import textwrap

MAX_CHARS = 84       # ~2 lines of 42
MAX_SECONDS = 6.0


def _split_utterance(u, words):
    """Yield (start, end, text) chunks within limits, on word boundaries."""
    uwords = [w for w in words if u["start"] <= w["start"] < u["end"]] or None
    if uwords is None:
        yield u["start"], u["end"], u["text"]
        return
    chunk, chunk_start = [], None
    for w in uwords:
        token = w.get("punctuated_word", w["word"])
        cand = " ".join(c[0] for c in chunk + [(token,)])
        start = chunk_start if chunk_start is not None else w["start"]
        if chunk and (len(cand) > MAX_CHARS or w["end"] - start > MAX_SECONDS):
            yield chunk_start, chunk[-1][1], " ".join(c[0] for c in chunk)
            chunk, chunk_start = [], None
        if not chunk:
            chunk_start = w["start"]
        chunk.append((token, w["end"]))
    if chunk:
        yield chunk_start, chunk[-1][1], " ".join(c[0] for c in chunk)


def to_cues(transcript):
    """[{start, end, text}] within the cue policy."""
    words = transcript.get("words", [])
    cues = []
    for u in transcript.get("utterances", []):
        for start, end, text in _split_utterance(u, words):
            cues.append({"start": start, "end": end, "text": text.strip()})
    return [c for c in cues if c["text"]]


def remap_to_timeline(cues, ir):
    """Source-time cues -> cut-timeline-time cues via the IR's kept spans.

    A cue is clipped to the span it overlaps; cues falling entirely in
    cut-away regions are dropped. Frame-accurate at the IR's fps.
    """
    from fractions import Fraction

    from .moments import spans_from_ir
    fps = Fraction(ir["timebase"]["fps"])
    spans = spans_from_ir(ir)
    out = []
    for c in cues:
        s_f = int(round(c["start"] * fps))
        e_f = int(round(c["end"] * fps))
        for sp in spans:
            lo, hi = max(s_f, sp["srcIn"]), min(e_f, sp["srcOut"])
            if hi <= lo:
                continue
            rec = sp["record"] + (lo - sp["srcIn"])
            out.append({"start": float(rec / fps),
                        "end": float((rec + (hi - lo)) / fps),
                        "text": c["text"]})
            break                      # first overlapping span wins in v0
    return out


def _ts(seconds):
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem2 = divmod(rem, 60_000)
    s, ms = divmod(rem2, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt(cues):
    blocks = []
    for i, c in enumerate(cues, 1):
        text = "\n".join(textwrap.wrap(c["text"], MAX_CHARS // 2 + 1)[:2]) \
            or c["text"]
        blocks.append(f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n{text}\n")
    return "\n".join(blocks)
