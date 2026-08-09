"""The component registry: discovery, validation, and compilation.

A component is a Python module in this package exposing two names:

    SPEC   a dict validated against schema/component.schema.json
    build(ctx) -> Tool      adds nodes to ctx.comp, returns the output tool

`build` receives everything it needs on `ctx` and reaches for nothing global.
It knows structure — cell counts, normalised coordinates, indices, animation
maths — and it reads its look from `ctx.theme`. It contains no colour, no merge
mode, no font: `tests/test_theme_binding.py` proves that from the outside, and
`compile()` proves the declaration is honest from the inside.

The undeclared-token check runs HERE rather than only in tests, because a
component that quietly reads a token it did not declare would otherwise compile
fine, ship, and then break the day someone edits a theme believing the
declaration.
"""
from __future__ import annotations

import importlib
import json
import pkgutil
from pathlib import Path

import jsonschema

from studio import comp as C
from studio.theme import Theme

ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = ROOT / "schema" / "component.schema.json"
_SCHEMA = None


class ComponentError(ValueError):
    pass


class Context:
    """What a component's build() is handed. Everything it may use, and the
    only channel through which it may read the look."""

    def __init__(self, comp, flow, params, theme, frames, fps, instance):
        self.comp = comp
        self.flow = flow
        self.params = params
        self.theme = theme
        self.frames = frames
        self.fps = fps
        self.instance = instance

    def name(self, part):
        """Namespaced, Fusion-legal, readable tool name. Every tool a component
        creates goes through here, so two instances of the same component in one
        comp cannot collide and a human reading the flow can tell them apart."""
        return C.check_name(f"{self.instance}_{part}")


def schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA


def validate_spec(spec):
    try:
        jsonschema.Draft202012Validator(schema()).validate(spec)
    except jsonschema.ValidationError as e:
        where = "/".join(str(p) for p in e.absolute_path) or "(root)"
        raise ComponentError(f"{spec.get('name', '?')}: spec invalid at {where}: {e.message}")
    if spec["route"] == 1:
        mode = (spec.get("duration") or {}).get("mode")
        if mode != "anim-curves":
            raise ComponentError(
                f"{spec['name']}: route 1 components must declare "
                "duration.mode = 'anim-curves' so a trim stretches the motion "
                "instead of clipping it (docs/MOTION-GRAPHICS.md)")
    return spec


def discover():
    """{name: module} for every valid component in this package."""
    found = {}
    for info in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        if not hasattr(mod, "SPEC") or not hasattr(mod, "build"):
            continue
        spec = validate_spec(mod.SPEC)
        if spec["name"] in found:
            raise ComponentError(f"duplicate component name {spec['name']!r}")
        found[spec["name"]] = mod
    return found


def get(name):
    mods = discover()
    if name not in mods:
        raise ComponentError(
            f"unknown component {name!r} — have: {', '.join(sorted(mods))}")
    return mods[name]


def resolve_params(spec, given):
    """Fill defaults, reject unknowns, check required and range. A param the
    component never declared is a typo that would otherwise be silently
    ignored and produce a correct-looking wrong render."""
    declared = spec.get("params") or {}
    unknown = set(given or {}) - set(declared)
    if unknown:
        raise ComponentError(
            f"{spec['name']}: unknown param(s) {', '.join(sorted(unknown))} — "
            f"declared: {', '.join(sorted(declared)) or '(none)'}")
    out = {}
    for key, decl in declared.items():
        if given and key in given:
            out[key] = given[key]
        elif "default" in decl:
            out[key] = decl["default"]
        elif decl.get("required"):
            raise ComponentError(f"{spec['name']}: param {key!r} is required")
        else:
            continue
        v = out[key]
        if decl["type"] in ("number", "integer"):
            if "minimum" in decl and v < decl["minimum"]:
                raise ComponentError(f"{spec['name']}: {key}={v} below minimum {decl['minimum']}")
            if "maximum" in decl and v > decl["maximum"]:
                raise ComponentError(f"{spec['name']}: {key}={v} above maximum {decl['maximum']}")
    return out


def compile(name, theme, params=None, frames=48, fps=24, instance=None):
    """Build a component into a fresh comp under `theme`.

    Returns a dict with the comp, its manifest, the graph hash, and the set of
    theme tokens the build actually read. That last field is what makes the
    `consumes` declaration enforceable.
    """
    if not isinstance(theme, Theme):
        raise ComponentError("compile() needs a Theme, not a dict — "
                             "the read-tracking is the point")
    mod = get(name)
    spec = mod.SPEC
    resolved = resolve_params(spec, params)
    instance = C.check_name(instance or spec["name"].replace("-", "_"))

    theme.reset_reads()
    composition = C.Composition()
    ctx = Context(composition, C.Flow(), resolved, theme, frames, fps, instance)
    out = mod.build(ctx)
    if out is None:
        raise ComponentError(f"{name}: build() returned None, expected the output tool")

    # The composition boundary belongs to the registry, not to the component.
    # A component says what it draws; it should not have to know that
    # ImportFusionComp replaces the comp and therefore that MediaIn1/MediaOut1
    # have to travel inside it. Emitting them here means no component can
    # forget, and the plate connection cannot silently dangle.
    if any(inp.source_operator == C.MEDIA_IN
           for tool in (composition.tools or {}).values()
           if isinstance(tool, C.Tool)
           for inp in (tool.inputs or {}).values()
           if isinstance(inp, C.Input)):
        C.add_media_in(composition, ctx.flow.at(-1, 0))
    C.add_media_out(composition, out, ctx.flow.next_col())

    read = theme.read
    undeclared = read - set(spec["consumes"])
    if undeclared:
        raise ComponentError(
            f"{name}: read theme token(s) {', '.join(sorted(undeclared))} "
            f"without declaring them in `consumes`. Add them to SPEC, or stop "
            f"reading them — an undeclared token breaks the day a theme changes.")

    errors = C.lint_graph(composition)
    if errors:
        raise ComponentError(f"{name}: graph lint failed:\n" +
                             "\n".join(f"  {e}" for e in errors))

    # Hardcoded-AND-undeclared is the one hole the binding test cannot see, and
    # it fails here instead — see comp.check_look_binding.
    hardcoded = C.check_look_binding(composition)
    if hardcoded:
        raise ComponentError(f"{name}: hardcoded look value(s):\n" +
                             "\n".join(f"  {e}" for e in hardcoded))

    man = C.manifest(composition)
    return {"component": name, "version": spec["version"], "route": spec["route"],
            "comp": composition, "output": out, "manifest": man,
            "graph_hash": C.graph_hash(man), "read": read,
            "params": resolved, "frames": frames, "fps": fps}
