"""Beat grid: music -> beat/tempo analysis -> timeline frames (slice 4b).

The music-video worked example's producer (docs/PLAN.md): beats become
IR markers + candidate cut frames so edits can quantize to the grid.
librosa is the analyzer; frames are computed at the TIMELINE's fps.
Which image lands on which beat stays Ryan's call — this only draws
the grid.
"""
from fractions import Fraction
from pathlib import Path


class BeatError(RuntimeError):
    pass


def analyze(audio_path, fps, bpm=None, first_beat=0.0):
    """Return {'bpm', 'beats', 'source'} at `fps`.

    Two modes, and the difference matters:

    - `bpm=None` — librosa's tempo tracker ESTIMATES from the samples. Fine for
      found music, but it is a guess: a washy or reverb-heavy mix smears the
      onsets and the grid drifts.
    - `bpm` given — the tempo is KNOWN (the SP-404MK2 and Ableton both run at a
      fixed project tempo), so the grid is computed arithmetically and is exact
      by construction. No estimation, no drift, no analysis pass. This is
      always the better answer when the number is known.

    `first_beat` is where beat 1 sits in the audio, in seconds — 0.0 when the
    file starts on the downbeat, which is the normal case for a bounce.

    'source' records which mode produced the grid, because "bpm 174" measured
    is a different claim from "bpm 174" declared.
    """
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise BeatError(f"audio missing: {audio_path}")
    fps = Fraction(fps)

    if bpm is not None:
        return _declared_grid(audio_path, fps, float(bpm), float(first_beat))

    import librosa
    y, sr = librosa.load(str(audio_path), mono=True)
    if not len(y):
        raise BeatError(f"no samples in {audio_path}")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    times = librosa.frames_to_time(beat_frames, sr=sr)
    bpm = float(tempo if not hasattr(tempo, "__len__") else tempo[0])
    beats = [int(round(float(t) * fps)) for t in times]

    # librosa returns bpm 0.0 and an EMPTY beat list rather than failing when
    # it cannot track the material (sustained pads, ambience, a pure tone).
    # Writing that out produces an empty grid and a beats.json claiming
    # "bpm 0.0" — a silent failure. Refuse, and point at the way out.
    if not beats or bpm <= 0:
        raise BeatError(
            f"librosa found no beat in {audio_path.name} (bpm={bpm:.1f}, "
            f"{len(beats)} beats). Ambient or sustained material often has no "
            f"trackable onsets. If you know the tempo, pass --bpm to compute "
            f"an exact grid instead of estimating."
        )

    return {"bpm": round(bpm, 2), "beats": beats, "source": "librosa"}


def _declared_grid(audio_path, fps, bpm, first_beat):
    """Exact beat grid from a known tempo — arithmetic, not analysis."""
    if bpm <= 0:
        raise BeatError(f"bpm must be positive, got {bpm}")
    if first_beat < 0:
        raise BeatError(f"first-beat must be >= 0, got {first_beat}")

    import librosa
    duration = float(librosa.get_duration(path=str(audio_path)))
    if duration <= 0:
        raise BeatError(f"no audio duration in {audio_path}")
    if first_beat >= duration:
        raise BeatError(
            f"first-beat {first_beat}s is past the end of {duration:.2f}s audio"
        )

    interval = 60.0 / bpm
    beats, n = [], 0
    while True:
        t = first_beat + n * interval
        if t >= duration:
            break
        beats.append(int(round(t * fps)))
        n += 1

    return {"bpm": round(bpm, 2), "beats": beats, "source": "declared"}


def beat_markers(beats, every=4, offset=0, extent=None, color="Purple"):
    """Markers for every Nth beat (all beats stay in beats.json — markers
    are the visible subset so a 3-minute track doesn't paint 400 flags)."""
    markers = []
    for i, b in enumerate(beats):
        if i % every:
            continue
        frame = b + offset
        if frame < 0 or (extent is not None and frame >= extent):
            continue
        markers.append({"frame": frame, "color": color,
                        "name": f"beat {i + 1}"})
    return markers
