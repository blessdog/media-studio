"""grid — a cell pattern that is a PURE FUNCTION of a seed.

The film's whole security argument lives in one property: the same coin always
makes the same mark, and a different coin makes a different one. That is not a
promise here, it is arithmetic — `mark_pattern(seed)` is deterministic, so two
instances given the same seed produce byte-identical geometry and two instances
given different seeds cannot be made to agree.

This is why the shot cannot be a diffusion shot: a model that re-imagines every
frame cannot guarantee two marks are THE SAME MARK, and that guarantee is the
only thing the shot exists to demonstrate.

`_mix` and `mark_pattern` are ported BY COPY from the retired Blender shot
`BLENDER/monero/shots/s5-key-image-teach.py` (nothing here may import from
BLENDER/). They were never Blender's — they are pure Python, which is exactly
why the substrate could change without the argument changing.
"""
from __future__ import annotations

from studio import comp as C

SPEC = {
    "name": "grid",
    "version": 1,
    "route": 2,
    "description": "Seeded cell grid stained into the plate. Same seed, same "
                   "pattern, always — the security property, as arithmetic.",
    "consumes": ["ink", "ink_opacity", "merge_mode", "edge_softness", "bleed"],
    "params": {
        "seed": {"type": "seed", "required": True,
                 "description": "the coin. Same seed => same mark, always."},
        "cells": {"type": "integer", "default": 5, "minimum": 2, "maximum": 12,
                  "description": "grid is cells x cells. 5 stays countable by eye."},
        "center": {"type": "point", "default": [0.5, 0.5]},
        "cell_size": {"type": "number", "default": 0.028, "minimum": 0.002,
                      "maximum": 0.2},
        "gap": {"type": "number", "default": 0.006, "minimum": 0.0,
                "maximum": 0.1},
        "pop_start": {"type": "integer", "default": 6, "minimum": 0},
        "pop_frames": {"type": "integer", "default": 9, "minimum": 2},
    },
    "duration": {"mode": "fixed", "minFrames": 12},
    "motion": [
        {"label": "pop", "from": 6, "to": 15, "region": [0.30, 0.30, 0.70, 0.70],
         "minAreaFraction": 0.0004, "maxAreaFraction": 0.30},
    ],
}


def _mix(x):
    """Murmur-style finalizer. A plain LCG was tried first and two different
    seeds produced patterns that both opened `#...#` — its early output bits are
    dominated by the seed's low bits, so the marks LOOKED alike even though they
    differed by 58%. In a shot whose only job is letting a viewer compare two
    marks by eye, 'looks similar' is the same as broken."""
    x &= 0xFFFFFFFF
    x = ((x ^ (x >> 16)) * 0x45D9F3B) & 0xFFFFFFFF
    x = ((x ^ (x >> 16)) * 0x45D9F3B) & 0xFFFFFFFF
    return x ^ (x >> 16)


def mark_pattern(seed, cells=5):
    """The key image. Pure function of the coin — same seed, same mark."""
    n = cells * cells
    return [i for i in range(n) if _mix(seed * 2654435761 + i) & 1]


def build(ctx):
    t, p = ctx.theme, ctx.params
    cells = p["cells"]
    cx, cy = p["center"]
    step = p["cell_size"] + p["gap"]
    half = (cells - 1) / 2.0

    # `bleed` widens each cell so ink spreads past its geometric edge, the way
    # a wet brush does. It is a look, so it comes from the theme; the grid
    # arithmetic around it is structure, so it stays here.
    size = p["cell_size"] + t.bleed
    soft = t.edge_softness

    filled = mark_pattern(p["seed"], cells)
    if not filled:
        raise ValueError(f"seed {p['seed']} produced an empty pattern")

    # Masks chain through EffectMask and combine with their PaintMode, whose
    # default is Add — so an unset PaintMode is the union we want, and we avoid
    # encoding Fusion's FuID enum for no gain.
    previous = None
    for idx in filled:
        row, col = divmod(idx, cells)
        mask = C.Tool.mask(ctx.name(f"cell_{idx:02d}"), "Rectangle",
                           position=ctx.flow.stack())
        mask.add_inputs(
            Width=size, Height=size, SoftEdge=soft,
            Center=(round(cx + (col - half) * step, 6),
                    round(cy + (half - row) * step, 6)),
        )
        if previous is not None:
            mask.add_source_input("EffectMask", previous.name, "Mask")
        ctx.comp.add_tools(mask)
        previous = mask

    ink = C.Tool.background(ctx.name("ink"), C.themed_color(t.ink),
                            position=ctx.flow.next_col())
    ink.add_source_input("EffectMask", previous.name, "Mask")
    ctx.comp.add_tools(ink)

    # Pivot at the grid's own centre: without it the pop scales about frame
    # centre and the mark slides in from off-axis instead of blooming in place.
    pop = C.Tool("Transform", ctx.name("pop"), ctx.flow.next_col())
    pop.add_source_input("Input", ink.name, "Output")
    pop.add_inputs(Pivot=(cx, cy))
    ctx.comp.add_tools(pop)

    a = p["pop_start"]
    b = a + p["pop_frames"]
    ctx.comp.animate(pop, "Size", C.Curve.ease_out(), [
        (a, 0.001),
        (a + max(1, p["pop_frames"] // 2), 1.12),   # overshoot, then settle
        (b, 1.0),
    ])

    # Multiply against the plate is the whole reason this is Fusion and not a
    # 3D render composited Over: ink has to let the paper's grain read through
    # it. An Over merge of opaque geometry is what made the Blender pass look
    # like grey cut-outs sitting on a painting.
    stain = C.Tool("Merge", ctx.name("stain"), ctx.flow.next_col())
    stain.add_source_input("Background", "MediaIn1", "Output")
    stain.add_source_input("Foreground", pop.name, "Output")
    stain.add_inputs(ApplyMode=t.merge_mode, Blend=t.ink_opacity)
    ctx.comp.add_tools(stain)

    return stain
