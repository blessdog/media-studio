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


def analyze(audio_path, fps):
    """Return {'bpm': float, 'beats': [frame,...]} at `fps`. Beat times
    come from librosa's tempo tracker on the audio's own samples."""
    import librosa
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise BeatError(f"audio missing: {audio_path}")
    fps = Fraction(fps)
    y, sr = librosa.load(str(audio_path), mono=True)
    if not len(y):
        raise BeatError(f"no samples in {audio_path}")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    times = librosa.frames_to_time(beat_frames, sr=sr)
    bpm = float(tempo if not hasattr(tempo, "__len__") else tempo[0])
    return {
        "bpm": round(bpm, 2),
        "beats": [int(round(float(t) * fps)) for t in times],
    }


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
