"""Tone math of the utility-dctls film pipeline, in plain Python, so the printer-lights gain is solved before Resolve runs.

The README's pipeline is Clamp 0+ -> Film Curve (negative) -> Color Gain -> Film Curve (print) -> Gain -> Display
Encoding, where the Color Gain "should make it so that middle gray is preserved at 0.18". This file mirrors the published
DCTL formulas (SIGMOID Film Curve, and the expected value of Film Grain's layered-grain transmittance) and bisects that
gain for a recipe. Halation is treated as identity here: on a flat field it only adds its reflection, which the grey-ramp
render in dctl_film_mini.py measures instead of assuming.

Writer: this file. Readers: dctl_film_mini.py (on the Mac mini) and `python3 film_chain.py` (offline table).
Fails when wrong: the 0.18 patch of the grey-ramp still stops landing at display code 125.

PRIOR ART: github.com/thatcherfreeman/utility-dctls, pinned as Ryan's fork blessdog/utility-dctls @ 693bf81 in
grades/film-look/manifest.json. The looks run as those DCTLs, unmodified, inside Resolve; nothing here renders pixels.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPES = os.path.join(HERE, "dctl-film-recipes.json")
SOLVE = "solve"


def _film_curve(x, p):
    gamma, dmin, dmax = p.get("Red Gamma", 1.0), p.get("Red D_MIN", 0.01), p.get("Red D_MAX", 4.0)
    offset, mid, exposure = p.get("Red Offset", 0.0), p.get("Mid Gray", 0.18), p.get("Exposure Gain", 1.0)
    z = math.log10(max(x * exposure, 1e-12) / mid)
    coeff = gamma / (0.25 * (dmax - dmin))
    d = 1.0 / (1.0 + math.exp(-coeff * (z + offset))) * (dmax - dmin) + dmin
    return 10.0 ** (-d)


def _film_grain_mean(x, p):
    dmax, dmin = p.get("D Max", 4.0), p.get("D Min", 0.01)
    layers, thr, gain = p.get("Num Layers of Grains", 5), p.get("Activation Threshold", 0.18), p.get("Photon Gain", 0.5)
    lam = max(x * gain, 0.0)
    if lam <= 0.0:
        prob = 0.0
    else:
        k = math.sqrt(2.0 / math.pi)
        z = (thr - lam) / math.sqrt(lam)
        prob = 1.0 - 1.0 / (1.0 + math.exp(max(min(-2.0 * k * z, 700.0), -700.0)))
    layer_t = (10.0 ** -dmin) ** (1.0 / layers)
    absorb = 1.0 - (10.0 ** -dmax) ** (1.0 / layers)
    return min(max((layer_t - absorb * prob) ** layers, 0.0), 1.0)


def _stage(x, st, gain):
    name, p = st["dctl"], st.get("params", {})
    if name == "Clamp":
        return max(x, 0.0)
    if name == "Film Curve":
        return _film_curve(x, p)
    if name == "Film Grain":
        return _film_grain_mean(x, p)
    if name == "Multiplication Function":
        g = p.get("Global Gain", 1.0)
        return x * (gain if g == SOLVE else g)
    return x


def chain(x, recipe, gain=1.0):
    for st in recipe["stages"]:
        x = _stage(x, st, gain)
    return x


def solve_gain(recipe):
    lo, hi = -10.0, 10.0
    rising = chain(0.18, recipe, 10.0 ** 1) > chain(0.18, recipe, 10.0 ** -1)
    for _ in range(200):
        mid = (lo + hi) / 2
        above = chain(0.18, recipe, 10.0 ** mid) > 0.18
        if above == rising:
            hi = mid
        else:
            lo = mid
    return 10.0 ** ((lo + hi) / 2)


def display_code(v):
    return round(255 * min(max(v, 0.0), 1.0) ** (1 / 2.4))


def load(names=None):
    with open(RECIPES) as f:
        book = json.load(f)["recipes"]
    return {n: book[n] for n in (names or book)}


if __name__ == "__main__":
    xs = [0.0, 0.005, 0.0225, 0.045, 0.09, 0.18, 0.36, 0.72, 1.0, 4.0]
    print("scene-linear in:", xs)
    for name, r in load(sys.argv[1:] or None).items():
        g = solve_gain(r)
        e = 0.01
        slope = (math.log10(chain(0.18 * 10 ** e, r, g)) - math.log10(chain(0.18 * 10 ** -e, r, g))) / (2 * e)
        print(f"{name:26} gain {g:.5g}  grey {chain(0.18, r, g):.4f}  mid slope {slope:.2f}  "
              f"codes {[display_code(chain(x, r, g)) for x in xs]}")
    print(f"{'no chain (null)':26} codes {[display_code(x) for x in xs]}")
