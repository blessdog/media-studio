"""The Fusion emitter: Python structures -> `.comp` text, plus the graph
manifest that proves what was emitted actually survived the trip.

This module knows NODES. It does not know what anything looks like and it does
not know what a component is. No colour, no aesthetic name, no theme lookup
belongs here — `tests/test_theme_binding.py` enforces that from the other side.

Serialization is vendored pysion (`vendor/pysion`, MIT, pinned — see its
PROVENANCE.md for why it is vendored rather than installed). Three things it
does not do, which are the reason this module exists:

  1. pysion renders the `.setting` shape — a bare `{ Tools = ordered() {…} }`
     table. `ImportFusionComp()` wants a `.comp`: that table wrapped in
     `Composition { CurrentTime, RenderRange, GlobalRange, … }`.
  2. Nothing upstream enforces readable node names or flow layout. A generated
     graph has to be openable in the Fusion page and takeable-apart by a human,
     so an unreadable graph is a failed output, not a cosmetic issue.
  3. There is no manifest. Counting tools proves nothing — a comp can import
     with the right number of tools and the wrong connections, values or
     keyframes. `manifest()` is one half of the equality that gate 1 asserts;
     `studio/fusion.py:live_manifest()` is the other half, and both round every
     float through `norm()` here so the two sides cannot disagree by precision.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_VENDOR = Path(__file__).resolve().parent.parent / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from pysion import Composition, Tool, RGBA  # noqa: E402,F401
from pysion.animation import BezierSpline, Curve  # noqa: E402,F401
from pysion.input import Input  # noqa: E402

# Floats arrive from three directions — our maths, pysion's bezier hand
# calculation, and Resolve's own round-trip — and they disagree in the last
# bits. Six places is far below anything visible and far above anything Resolve
# perturbs, so both manifest sides quantise here and nowhere else.
PRECISION = 6

# Flow spacing. Fusion's own grid step is what pysion's fusion_coords assumes;
# these are the column/row units the layout helper hands out.
COL = 1
ROW = 1


class CompError(ValueError):
    pass


def norm(value):
    """The single normalizer. Used by manifest() and by live_manifest()."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return round(value, PRECISION)
    if isinstance(value, int):
        return float(value) if abs(value) > 2**31 else value
    if isinstance(value, (list, tuple)):
        return [norm(v) for v in value]
    if isinstance(value, dict):
        return {str(k): norm(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if value is None:
        return None
    return str(value)


def check_name(name):
    """Fusion tool names must not carry spaces, dashes or a leading digit, and
    ours must additionally mean something. `Rectangle17` tells a reader nothing;
    `mark-a1-cell-07` tells them everything — but the dash is illegal, so the
    convention is underscores: `mark_a1_cell_07`."""
    if not name:
        raise CompError("tool name is empty")
    if name[0].isdigit():
        raise CompError(f"tool name {name!r} starts with a digit")
    bad = [c for c in name if not (c.isalnum() or c == "_")]
    if bad:
        raise CompError(
            f"tool name {name!r} contains {''.join(sorted(set(bad)))!r} — "
            "Fusion accepts only letters, digits and underscores")
    return name


class Flow:
    """Hands out grid positions so a generated comp opens as something legible.

    Left to itself every tool lands at (0,0) and the Fusion page shows one
    illegible pile. Columns advance along the signal path; rows stack the
    contributors feeding a single column.
    """

    def __init__(self):
        self._col = 0
        self._row = 0

    def next_col(self):
        self._col += COL
        self._row = 0
        return (self._col, 0)

    def stack(self):
        self._row -= ROW
        return (self._col, self._row)

    def at(self, col, row=0):
        return (col * COL, row * ROW)


def _tool_entry(tool):
    """One tool's contribution to the manifest: only what was explicitly set."""
    inputs, connections, expressions = {}, {}, {}
    for name, inp in (tool.inputs or {}).items():
        if not isinstance(inp, Input):
            continue
        if inp.source_operator is not None:
            connections[name] = [inp.source_operator, inp.source or "Output"]
        if inp.expression is not None:
            expressions[name] = str(inp.expression)
        if inp.value is not None:
            inputs[name] = norm(inp.value)
    return {
        "type": tool.id,
        "inputs": dict(sorted(inputs.items())),
        "connections": dict(sorted(connections.items())),
        "expressions": dict(sorted(expressions.items())),
    }


def _spline_entry(spline):
    keys = []
    for frame, kf in (spline.keyframes or {}).items():
        keys.append([norm(frame), norm(kf.value)])
    keys.sort(key=lambda p: p[0])
    return {"type": "BezierSpline", "keyframes": keys}


def manifest(comp):
    """The normalized graph, emitted side. Compared field-for-field against
    `studio/fusion.py:live_manifest()` after import — see gate 1.

    Only inputs we actually set appear. Fusion elides its own defaults, so
    asserting defaults would produce noise; asserting what we set produces
    signal, and every one of those is asserted exactly.
    """
    tools, modifiers = {}, {}
    for name, tool in (comp.tools or {}).items():
        if not isinstance(tool, Tool):
            continue
        tools[name] = _tool_entry(tool)
    for name, mod in (comp.modifiers or {}).items():
        if isinstance(mod, BezierSpline):
            modifiers[name] = _spline_entry(mod)
    return {"tools": dict(sorted(tools.items())),
            "modifiers": dict(sorted(modifiers.items()))}


def graph_hash(man):
    """Stable digest of a manifest. Goes into approval.json as `graphHash` so an
    approval stays attached to the graph it was actually given for."""
    blob = json.dumps(man, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def to_comp_text(comp, frames, fps=None, current_time=0):
    """Wrap pysion's `.setting` table into a real `.comp`.

    `ImportFusionComp()` reads a Composition, not a bare tool table, and the
    render range is what makes a comp more than one frame long — omit it and the
    import succeeds while every later render is a single still.
    """
    if frames < 1:
        raise CompError(f"frames must be >= 1, got {frames}")
    body = repr(comp.render())
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end <= start:
        raise CompError("pysion produced no table — is the comp empty?")
    inner = body[start + 1:end].strip().rstrip(",")
    last = frames - 1
    head = [
        "\tCurrentTime = %d," % current_time,
        "\tRenderRange = { 0, %d }," % last,
        "\tGlobalRange = { 0, %d }," % last,
        "\tHiQ = true,",
    ]
    if fps:
        head.append("\tFrameFormat = { Rate = %s }," % norm(float(fps)))
    return "Composition {\n%s\n\t%s\n}\n" % ("\n".join(head), inner)


def write_comp(comp, path, frames, fps=None):
    """Emit the `.comp` and return (path, manifest, graph_hash) together — the
    three things every caller needs and nobody should recompute separately."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = to_comp_text(comp, frames, fps)
    errors = lint_comp_text(text)
    if errors:
        raise CompError("refusing to write a comp that fails lint:\n" +
                        "\n".join(f"  {e}" for e in errors))
    path.write_text(text, encoding="utf-8")
    man = manifest(comp)
    return path, man, graph_hash(man)


def lint_comp_text(text):
    """Structural gates before anything reaches Resolve. Cheap, and it catches
    the failure that costs the most time: a comp that imports without error and
    silently drops the half of the graph whose sources do not resolve."""
    errors = []
    if text.count("{") != text.count("}"):
        errors.append(f"unbalanced braces ({text.count('{')} vs {text.count('}')})")
    if not text.lstrip().startswith("Composition {"):
        errors.append("does not open with `Composition {` — this is a .setting, not a .comp")
    if "Tools = " not in text:
        errors.append("no Tools table")
    if "RenderRange" not in text:
        errors.append("no RenderRange — the comp would render as a single still")
    return errors


def themed_color(value, premultiply=True):
    """RGBA from a theme colour token, with the origin tag surviving.

    pysion's RGBA premultiplies in `__post_init__`, and arithmetic on a tagged
    float returns a plain float — so the tag has to be reapplied afterwards.
    Refusing an untagged argument is what stops this from becoming a laundry
    for literals: you cannot get a themed colour out without putting a theme
    value in.
    """
    from studio.theme import Themed, tag
    if not isinstance(value, Themed):
        raise CompError(
            f"themed_color() got a literal {value!r} — colour must come from a "
            "theme token, or the component is deciding the look itself")
    if len(value) not in (3, 4):
        raise CompError(f"colour token must be 3 or 4 channels, got {len(value)}")
    c = RGBA(*value, premultiply=premultiply)
    c.red, c.green, c.blue = tag(c.red), tag(c.green), tag(c.blue)
    c.alpha = tag(c.alpha)
    return c


def derive(value, *from_tokens):
    """Re-tag a value computed FROM theme tokens.

    A component that needs `t.edge_softness * 2` on a look input would
    otherwise lose the tag and be rejected as hardcoded. Naming the tokens it
    was derived from keeps the audit trail honest — an untagged source still
    refuses, so this cannot be used to smuggle a constant through.
    """
    from studio.theme import Themed, tag
    if not from_tokens:
        raise CompError("derive() needs the theme value(s) it came from")
    for src in from_tokens:
        if not isinstance(src, Themed):
            raise CompError(f"derive() source {src!r} is not a theme value")
    return tag(value)


# Fusion inputs that decide how something LOOKS rather than where or how big it
# is. A literal on one of these is a component making an aesthetic choice in
# code, which is the thing the whole layer separation exists to prevent.
#
# Colour channels are matched by suffix because Fusion spreads one colour across
# four inputs and prefixes them per tool (`TopLeftRed`, `Red1`, `BottomRightAlpha`).
LOOK_INPUTS = {
    "ApplyMode", "ApplyOperator", "Font", "Style", "SoftEdge", "Softness",
    "BlurLevel", "Blend", "Opacity", "Gain", "Gamma", "Saturation",
}
LOOK_SUFFIXES = ("Red", "Green", "Blue", "Alpha")


def _is_look_input(name):
    return name in LOOK_INPUTS or name.rstrip("0123456789").endswith(LOOK_SUFFIXES)


def check_look_binding(comp):
    """Refuse a graph that decides a look in code instead of reading a theme.

    The theme-binding test proves a component's `consumes` matches what it
    reads. It cannot catch a value that is BOTH hardcoded AND undeclared —
    that is self-consistent and passes every assertion (verified by planting
    one, 2026-08-06). This is the structural half: values leave a theme tagged
    `Themed`, and a look-bearing input holding an untagged literal fails here.

    Numbers that happen to be structural (a Blend driven by a spline, a size)
    never reach this: connections and expressions carry no value at all.
    """
    from studio.theme import Themed
    problems = []
    for tool_name, tool in (comp.tools or {}).items():
        if not isinstance(tool, Tool):
            continue
        for input_name, inp in (tool.inputs or {}).items():
            if not isinstance(inp, Input) or inp.value is None:
                continue
            if not _is_look_input(input_name):
                continue
            if not isinstance(inp.value, Themed):
                problems.append(
                    f"{tool_name}.{input_name} = {inp.value!r} is a hardcoded "
                    "look value — read it from the theme")
    return problems


MEDIA_IN = "MediaIn1"
MEDIA_OUT = "MediaOut1"


def add_media_in(comp, position=(0, 0)):
    """The clip's own image, as an explicit tool.

    `AddFusionComp()` creates MediaIn1/MediaOut1 for you, but
    `ImportFusionComp()` REPLACES the whole composition and takes them with it.
    Measured 2026-08-06 on Resolve 21.0.4.5: an imported comp referencing
    `SourceOp = "MediaIn1"` came back with the connection reading
    `value=None, connected_from=None` — silently dangling — and with no
    MediaOut at all, so the comp rendered nothing while looking perfect. Every
    tool was present with the right name and type; a count check passes it.
    So the comp has to carry these itself.
    """
    tool = Tool("MediaIn", MEDIA_IN, position)
    comp.add_tools(tool)
    return tool


def add_media_out(comp, source, position=(0, 0)):
    tool = Tool("MediaOut", MEDIA_OUT, position)
    tool.add_source_input("Input", source.name, source.output or "Output")
    comp.add_tools(tool)
    return tool


def lint_graph(comp):
    """Semantic gates on the structure, where the names are still available.

    Nothing is whitelisted. A reference to a tool that does not exist in the
    comp is an error even when the name is `MediaIn1` — especially then, since
    that is the one that fails silently rather than loudly.
    """
    errors = []
    tools = comp.tools or {}
    mods = comp.modifiers or {}
    known = set(tools) | set(mods)
    for name, tool in tools.items():
        if not isinstance(tool, Tool):
            continue
        if not tool.id:
            errors.append(f"{name}: no tool type")
        for input_name, inp in (tool.inputs or {}).items():
            if isinstance(inp, Input) and inp.source_operator:
                if inp.source_operator not in known:
                    hint = (" — ImportFusionComp replaces the comp, so this tool "
                            "must be emitted, not assumed"
                            if inp.source_operator in (MEDIA_IN, MEDIA_OUT) else "")
                    errors.append(
                        f"{name}.{input_name} -> {inp.source_operator!r} "
                        f"which is not a tool in this comp{hint}")
    outs = [n for n, t in tools.items()
            if isinstance(t, Tool) and t.id == "MediaOut"]
    if len(outs) != 1:
        errors.append(f"expected exactly one MediaOut, found {len(outs)} "
                      f"({', '.join(outs) or 'none'}) — a comp with no MediaOut "
                      "imports cleanly and renders nothing")
    return errors
