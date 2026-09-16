#!/usr/bin/env python3
"""How far a second audio recording sits from a reference track, by cross-correlation at several times.

    python3 audio_lag.py <reference> <other> [SECONDS,SECONDS,...]

Both files' first audio stream are decoded at 48 kHz. For each start time, 10 s of the reference is matched against
the other recording within +-1 s. A negative lag means the other recording LEADS (its sound arrives earlier), so it
must be delayed by that much to match: ffmpeg `-itsoffset <minus the lag, in s>` on it. r is the normalised correlation; its sign
is the polarity. Self-test: a synthetic copy shifted 122 ms and inverted comes back as +5856 samples, r=-1.000.

Written for the Osmo Action 5 Pro, whose WAV leads its MP4 audio by 116-121 ms (docs/CINEMATIC-PIPELINE-VERIFY.md
row 30), and kept as the independent check on whatever does the syncing.

PRIOR ART: Resolve's own waveform sync (MediaPool.AutoSyncAudio, AUDIO_SYNC_WAVEFORM) is the route for doing the sync;
bookmarked as knowledge/sync-the-osmo-wav-inside-resolve-with-autosyncau.md. This file only measures.
"""
import subprocess
import sys

import numpy as np

SR = 48000
SEARCH = SR
WINDOW = 10 * SR


def pcm(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


def lag_at(ref, other, start):
    x = ref[start:start + WINDOW].astype(np.float64)
    y = other[start - SEARCH:start + WINDOW + SEARCH].astype(np.float64)
    if start < SEARCH or len(x) < WINDOW or len(y) < WINDOW + 2 * SEARCH:
        return None
    n = 2 ** int(np.ceil(np.log2(len(y) + len(x))))
    c = np.fft.irfft(np.fft.rfft(y, n) * np.conj(np.fft.rfft(x, n)), n)[:2 * SEARCH + 1]
    csum = np.concatenate([[0], np.cumsum(y ** 2)])
    r = c / np.maximum(np.sqrt((csum[WINDOW:WINDOW + 2 * SEARCH + 1] - csum[:2 * SEARCH + 1]) * np.sum(x ** 2)), 1e-12)
    k = int(np.argmax(np.abs(r)))
    return k - SEARCH, r[k]


def main():
    ref, other = pcm(sys.argv[1]), pcm(sys.argv[2])
    starts = [float(v) for v in (sys.argv[3] if len(sys.argv) > 3 else "20,60,120,200,280").split(",")]
    print(f"samples {len(ref)} / {len(other)}; left-right correlation {np.corrcoef(ref.T)[0, 1]:.3f} / {np.corrcoef(other.T)[0, 1]:.3f}")
    lags = []
    for t in starts:
        got = lag_at(ref.mean(1), other.mean(1), int(t * SR))
        if got is None:
            print(f"t={t:g}s  outside the recording")
            continue
        lag, r = got
        lags.append(lag)
        print(f"t={t:g}s  lag {lag:+d} samples ({lag / SR * 1000:+.1f} ms)  r={r:+.3f}")
    if lags:
        print(f"median lag {np.median(lags) / SR * 1000:+.1f} ms")


if __name__ == "__main__":
    main()
