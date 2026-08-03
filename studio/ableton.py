"""Ableton .als parse -> trigger map (pipeline G2 of docs/CLIP-LANE.md).

G2 is the only trigger-map producer that needs no hardware: a `.als` is
gzip-compressed XML, and every clip in it declares where it sits on the
timeline. We read a DECLARATION of what was played, never a guess -- no
fingerprinting against the master (CLIP-LANE.md §4).

The output is CLIP-LANE.md §1's one artifact:

    [{sample_hash, track_start_secs, duration_secs}, ...]

`sample_hash` joins to blessdog's `phase8_sp404` ledger, which carries
`source_clip_hash` + `source_in_secs` -- so the meme's own frames can be
trimmed to the same in-point as the audio chop (§5). The .als never needs
to know the in-point INSIDE the sample; it only says when the sample
fires. Keeping that split is what lets neither repo import the other.

Four traps, all found by reading Ryan's own files rather than the docs.
Each one produces a plausible-looking map that is silently wrong:

1. GroovePool clips are not music. `thunderdome.als` has exactly one
   `<MidiClip>` and it lives at LiveSet/GroovePool/Grooves/Groove/Clip --
   a swing-timing template. A naive `root.iter("MidiClip")` emits 16
   phantom triggers on note 36 from a project with zero played MIDI.
   Only clips under Tracks/ count.
2. Looped clips fire their content more than once. A clip spanning 16
   beats with an 8-beat loop plays its notes TWICE; the note list holds
   one copy. Un-expanded, the map under-reports every repeat.
3. Values live in `Value=` attributes, not element text. `findtext()`
   returns "" for every field and float("") raises -- or worse, a
   defaulted 0.0 silently puts every clip at the top of the timeline.
4. Tempo automation breaks beats->seconds. The conversion here is
   linear (60/bpm); a tempo ramp makes it wrong everywhere after the
   first ramp. We refuse rather than emit a drifting map.
"""
import gzip
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

# Clips reachable from Tracks/ are music. Everything else -- GroovePool
# templates most of all -- is not, and must never reach a trigger map.
CLIP_TAGS = ("AudioClip", "MidiClip")


class AbletonError(RuntimeError):
    pass


def _val(elem, tag, default=None):
    """Read <Tag Value="x"/>. Trap 3: the payload is an attribute."""
    if elem is None:
        return default
    child = elem.find(tag)
    if child is None:
        return default
    v = child.get("Value")
    return default if v is None else v


def _num(elem, tag, default=0.0):
    v = _val(elem, tag)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _flag(elem, tag, default=False):
    v = _val(elem, tag)
    return default if v is None else v == "true"


def parse(als_path):
    """Read a .als. Returns a project dict; raises AbletonError on refusal.

    {'path', 'live_version', 'creator', 'tempo', 'time_signature',
     'tracks': [{'name', 'kind', 'clips': [...]}]}
    """
    als_path = Path(als_path)
    if not als_path.is_file():
        raise AbletonError(f"no such .als: {als_path}")

    try:
        with gzip.open(als_path, "rb") as fh:
            root = ET.parse(fh).getroot()
    except (OSError, EOFError) as exc:
        # An uncompressed .als is legal in principle; Live has always
        # written gzip, so this is far more likely a truncated file.
        raise AbletonError(f"{als_path.name} is not gzip XML: {exc}") from exc
    except ET.ParseError as exc:
        raise AbletonError(f"{als_path.name} is not valid XML: {exc}") from exc

    live_set = root.find("LiveSet")
    if live_set is None:
        raise AbletonError(f"{als_path.name} has no <LiveSet> — not an Ableton set")

    tempo = _project_tempo(live_set, als_path.name)

    tracks = []
    tracks_el = live_set.find("Tracks")
    for track_el in list(tracks_el) if tracks_el is not None else []:
        tracks.append(_read_track(track_el, tempo))

    return {
        "path": str(als_path),
        "live_version": root.get("MinorVersion"),
        "creator": root.get("Creator"),
        "tempo": tempo,
        "tracks": tracks,
    }


def _project_tempo(live_set, name):
    """Master-track tempo. Trap 4: refuse tempo automation.

    Live stores the tempo as a Manual value plus an automation envelope.
    A static project has the envelope present but holding a single event
    (or none). Two or more DISTINCT event values means the tempo moves,
    and every beats->seconds number after the first ramp would be wrong.
    """
    tempo_el = None
    for candidate in live_set.iter("Tempo"):
        if candidate.find("Manual") is not None:
            tempo_el = candidate
            break
    if tempo_el is None:
        raise AbletonError(f"{name}: no master tempo found")

    bpm = _num(tempo_el, "Manual", 0.0)
    if bpm <= 0:
        raise AbletonError(f"{name}: master tempo is {bpm}, expected > 0")

    values = set()
    for events in tempo_el.iter("Events"):
        for ev in events:
            v = ev.get("Value")
            if v is not None:
                values.add(round(float(v), 6))
    if len(values) > 1:
        raise AbletonError(
            f"{name}: tempo automation found ({sorted(values)} BPM). "
            f"beats->seconds here is linear (60/bpm) and would drift after "
            f"the first ramp, so the trigger map would be silently wrong. "
            f"Bounce at a fixed tempo, or the map needs a real tempo curve."
        )
    return bpm


def _read_track(track_el, tempo):
    kind = {"MidiTrack": "midi", "AudioTrack": "audio",
            "ReturnTrack": "return", "MasterTrack": "master"}.get(
                track_el.tag, track_el.tag)

    name_el = track_el.find("Name")
    name = _val(name_el, "EffectiveName") or _val(name_el, "UserName") or ""

    clips = []
    # Trap 1: scope the search to this TRACK. Reaching for clips from the
    # LiveSet root pulls in GroovePool templates, which are not music.
    for holder, view in _clip_holders(track_el):
        for clip_el in holder:
            if clip_el.tag in CLIP_TAGS:
                clips.append(_read_clip(clip_el, tempo, view))

    clips.sort(key=lambda c: (c["start_beats"], c["name"]))
    return {"name": name, "kind": kind, "clips": clips}


def _clip_holders(track_el):
    """Yield (container, view) for every place a track keeps clips.

    Arrangement: DeviceChain/MainSequencer/{Sample,ClipTimeable}/
                 ArrangerAutomation/Events
    Session:     MainSequencer/ClipSlotList/ClipSlot/ClipSlot/Value
    """
    for auto in track_el.iter("ArrangerAutomation"):
        events = auto.find("Events")
        if events is not None:
            yield events, "arrangement"
    for slot in track_el.iter("ClipSlot"):
        value = slot.find("Value")
        if value is not None:
            yield value, "session"


def _read_clip(clip_el, tempo, view):
    start = _num(clip_el, "CurrentStart")
    end = _num(clip_el, "CurrentEnd")
    span = max(0.0, end - start)

    loop_el = clip_el.find("Loop")
    loop_on = _flag(loop_el, "LoopOn")
    loop_start = _num(loop_el, "LoopStart")
    loop_end = _num(loop_el, "LoopEnd")
    start_relative = _num(loop_el, "StartRelative")
    loop_len = max(0.0, loop_end - loop_start)

    clip = {
        "kind": "audio" if clip_el.tag == "AudioClip" else "midi",
        "view": view,
        "name": _val(clip_el, "Name") or "",
        "disabled": _flag(clip_el, "Disabled"),
        "start_beats": start,
        "end_beats": end,
        "duration_beats": span,
        "start_secs": beats_to_secs(start, tempo),
        "duration_secs": beats_to_secs(span, tempo),
        "loop_on": loop_on,
        "loop_start_beats": loop_start,
        "loop_end_beats": loop_end,
        "loop_length_beats": loop_len,
        "start_relative_beats": start_relative,
        "passes": _passes(span, loop_len, start_relative, loop_on),
    }

    if clip["kind"] == "audio":
        clip["sample"] = _sample_ref(clip_el)
        clip["sample_path"] = (clip["sample"] or {}).get("path")
    else:
        clip["notes"] = _read_notes(clip_el)
    return clip


def _passes(span, loop_len, start_relative, loop_on):
    """Timeline offsets (beats, from clip start) where content restarts.

    Trap 2. Playback position inside a looped clip is
        content = loop_start + ((start_relative + d) mod loop_len)
    so the content wraps to loop_start at every d where that mod hits 0.
    An unlooped clip plays through exactly once: a single pass at 0.
    """
    if not loop_on or loop_len <= 0 or span <= 0:
        return [0.0]
    first = (-start_relative) % loop_len
    offsets = [0.0]
    d = first
    if d == 0.0:
        d = loop_len
    while d < span - 1e-9:
        offsets.append(d)
        d += loop_len
    return offsets


# Live Packs install here on this machine (verified against
# "Chop and Swing"). Used only to resolve a pack-relative RelativePath.
PACK_ROOTS = (
    Path.home() / "Music/Ableton/Factory Packs",
    Path.home() / "Music/Ableton/User Library",
)


def _sample_ref(clip_el):
    """The sample's declared location, plus what it takes to find it.

    The absolute `Path` is frequently FICTION: Ableton bakes its own build
    machine into factory content ("/Volumes/data/tmp/trunk/..."), and any
    set that has moved between machines carries a stale one. So the
    relative path, the pack name, and the original file size all matter —
    the size is what proves a resolved candidate is the SAME file rather
    than a different one with the same name, which would place the wrong
    video on the timeline.
    """
    ref = clip_el.find("SampleRef")
    file_ref = ref.find("FileRef") if ref is not None else None
    if file_ref is None:
        return None
    return {
        "path": _val(file_ref, "Path"),
        "relative_path": _val(file_ref, "RelativePath"),
        "relative_type": _val(file_ref, "RelativePathType"),
        "pack": _val(file_ref, "LivePackName") or None,
        "size": int(_num(file_ref, "OriginalFileSize", 0)),
    }


def resolve_sample(ref, als_path):
    """Find the sample on THIS disk, or None. Size-checked when known.

    Order: the declared absolute path, then the relative path against the
    project folder (and its parent — Live keeps the .als inside an
    "X Project" directory), then against an installed Live Pack.
    """
    if not ref:
        return None
    als_path = Path(als_path)
    candidates = []

    if ref["path"]:
        candidates.append(Path(ref["path"]))

    rel = ref["relative_path"]
    if rel:
        candidates.append(als_path.parent / rel)
        candidates.append(als_path.parent.parent / rel)
        if ref["pack"]:
            for root in PACK_ROOTS:
                candidates.append(root / ref["pack"] / rel)

    for cand in candidates:
        try:
            if not cand.is_file():
                continue
            # A size mismatch means we found a DIFFERENT file that merely
            # shares a name. Skipping it is right: a wrong hash joins to
            # the wrong sample and places the wrong picture.
            if ref["size"] and cand.stat().st_size != ref["size"]:
                continue
            return str(cand)
        except OSError:
            continue
    return None


def _read_notes(clip_el):
    """MIDI notes with their key. Note Time is CLIP-relative, in beats."""
    notes = []
    for key_track in clip_el.iter("KeyTrack"):
        key = _val(key_track, "MidiKey")
        if key is None:
            continue
        key = int(key)
        for note in key_track.iter("MidiNoteEvent"):
            if note.get("IsEnabled") == "false":
                continue
            notes.append({
                "note": key,
                "time_beats": float(note.get("Time", 0.0)),
                "duration_beats": float(note.get("Duration", 0.0)),
                "velocity": float(note.get("Velocity", 100.0)),
            })
    notes.sort(key=lambda n: (n["time_beats"], n["note"]))
    return notes


def beats_to_secs(beats, tempo):
    """Linear only — _project_tempo has already refused tempo automation."""
    return beats * 60.0 / tempo


def file_hash(path):
    """SHA-256, the join key to blessdog's ledger (CLIP-LANE.md §7)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def trigger_map(project, hash_samples=True, include_session=False):
    """CLIP-LANE.md §1: [{sample_hash, track_start_secs, duration_secs}, ...].

    One entry per FIRING, not per clip — a looped clip contributes one
    entry per pass (trap 2). Session clips are excluded by default: a clip
    sitting in a slot has no timeline position, so it has not fired.

    Audio clips carry `sample_hash` when the sample resolves on disk.
    MIDI notes carry `note` instead: resolving a note to a pad needs the
    bank, and the per-bank channel layout is still [U] (CLIP-LANE.md §2) —
    so that join is left to the consumer with the ledger in hand, rather
    than guessed here.
    """
    tempo = project["tempo"]
    hashes = {}
    entries = []

    for track in project["tracks"]:
        if track["kind"] in ("return", "master"):
            continue
        for clip in track["clips"]:
            if clip["disabled"]:
                continue
            if clip["view"] == "session" and not include_session:
                continue

            passes = clip["passes"]
            span = clip["duration_beats"]
            base = clip["start_beats"]

            if clip["kind"] == "audio":
                declared = clip.get("sample_path")
                found = resolve_sample(clip.get("sample"), project["path"])
                sample_hash = None
                if hash_samples and found:
                    if found not in hashes:
                        hashes[found] = file_hash(found)
                    sample_hash = hashes[found]

                for i, offset in enumerate(passes):
                    nxt = passes[i + 1] if i + 1 < len(passes) else span
                    entries.append({
                        "kind": "audio",
                        "track": track["name"],
                        "clip": clip["name"],
                        "sample_hash": sample_hash,
                        "sample_path": declared,
                        "sample_resolved": found,
                        "track_start_secs": beats_to_secs(base + offset, tempo),
                        "duration_secs": beats_to_secs(max(0.0, nxt - offset), tempo),
                        "track_start_beats": base + offset,
                        "pass": i,
                    })
            else:
                loop_len = clip["loop_length_beats"]
                loop_start = clip["loop_start_beats"]
                rel = clip["start_relative_beats"]
                for note in clip["notes"]:
                    for d in _note_offsets(note, clip, span, loop_len,
                                           loop_start, rel):
                        entries.append({
                            "kind": "midi",
                            "track": track["name"],
                            "clip": clip["name"],
                            "note": note["note"],
                            "velocity": note["velocity"],
                            "sample_hash": None,
                            "track_start_secs": beats_to_secs(base + d, tempo),
                            "duration_secs": beats_to_secs(
                                note["duration_beats"], tempo),
                            "track_start_beats": base + d,
                        })

    entries.sort(key=lambda e: (e["track_start_secs"], e["track"],
                                e.get("note") or 0))
    return entries


def _note_offsets(note, clip, span, loop_len, loop_start, rel):
    """Timeline offsets (beats from clip start) where this note fires.

    Solving  (rel + d) mod loop_len == time - loop_start  for d, then
    stepping by loop_len while still inside the clip (trap 2).

    The modulo alone is NOT enough, and getting this wrong is trap 2's
    evil twin. A clip's note list spans its whole content, but the loop
    brace selects only the portion that repeats — notes outside
    [LoopStart, LoopEnd) are silent. Folding every note into the loop
    window with a bare modulo invents triggers that never sounded: on
    Clean Swing's one repeating clip that is 63 of 114 notes, each
    doubled by the two passes. Under-reporting loses picture; this
    over-reporting would place picture where there is no sound.
    """
    t = note["time_beats"]
    if not clip["loop_on"] or loop_len <= 0:
        d = t - loop_start - rel
        return [d] if -1e-9 <= d < span - 1e-9 else []

    if not (loop_start - 1e-9 <= t < loop_start + loop_len - 1e-9):
        return []

    out = []
    d = (t - loop_start - rel) % loop_len
    while d < span - 1e-9:
        out.append(d)
        d += loop_len
    return out
