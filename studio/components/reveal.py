"""reveal — the plate emerges from under a wash.

The frame starts covered. A soft-edged region opens and the plate shows through
it, so the picture arrives rather than cuts. Route 2, because the thing being
revealed IS the plate — there is nothing to reveal in an isolated alpha master.

Structurally this is one mask with `Invert` set: the wash is drawn everywhere the
mask is NOT, so growing the mask removes wash. Animating the wash's opacity
instead would fade the whole frame at once, which reads as a dissolve rather than
something opening.
"""
from __future__ import annotations

from studio import comp as C

SPEC = {
    "name": "reveal",
    "version": 1,
    "route": 2,
    "description": "A soft region opens and the plate shows through the wash.",
    "consumes": ["paper", "edge_softness", "bleed"],
    "params": {
        "center": {"type": "point", "default": [0.5, 0.5]},
        "shape": {"type": "string", "default": "Ellipse",
                  "description": "Ellipse or Rectangle"},
        "start": {"type": "integer", "default": 0, "minimum": 0},
        "frames": {"type": "integer", "default": 18, "minimum": 2},
        "extent": {"type": "number", "default": 1.35, "minimum": 0.1,
                   "maximum": 3.0,
                   "description": "final mask size; past 1.0 it clears the frame"},
    },
    "duration": {"mode": "fixed", "minFrames": 20},
    "motion": [
        {"label": "open", "from": 0, "to": 18, "region": [0.0, 0.0, 1.0, 1.0],
         "minAreaFraction": 0.02, "maxAreaFraction": 1.0},
    ],
}


def build(ctx):
    t, p = ctx.theme, ctx.params
    shape = p["shape"] if p["shape"] in ("Ellipse", "Rectangle") else "Ellipse"

    hole = C.Tool.mask(ctx.name("hole"), shape, position=ctx.flow.at(0, -1))
    hole.add_inputs(Center=tuple(p["center"]), Invert=1, SoftEdge=t.edge_softness)
    ctx.comp.add_tools(hole)

    # Width and Height are driven by one spline each so the region opens
    # circularly. Two splines rather than an XYPath because these are separate
    # scalar inputs, not a point.
    a, b = p["start"], p["start"] + p["frames"]
    extent = p["extent"] + t.bleed
    for axis in ("Width", "Height"):
        ctx.comp.animate(hole, axis, C.Curve.ease_out(),
                         [(a, 0.0), (b, round(float(extent), 6))])

    wash = C.Tool.background(ctx.name("wash"), C.themed_color(t.paper),
                             position=ctx.flow.next_col())
    wash.add_source_input("EffectMask", hole.name, "Mask")
    ctx.comp.add_tools(wash)

    over = C.Tool("Merge", ctx.name("over"), ctx.flow.next_col())
    over.add_source_input("Background", "MediaIn1", "Output")
    over.add_source_input("Foreground", wash.name, "Output")
    ctx.comp.add_tools(over)

    return over
