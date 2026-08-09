#!/usr/bin/env python3
"""The style-agnosticism regression test. Plain script, run via the gate:

    make check                (or: .venv/bin/python tests/test_theme_binding.py)

The pipeline must not be architected around one aesthetic. Ink-wash is a look
Ryan happens to like; it is data, and swapping it must be a one-file change.
The cheap way to check that is grepping for hex codes, and the cheap way is not
enough — it misses constants behind generic names, imported palettes, computed
values, and it passes cleanly when a component ignores the theme entirely.

So the enforcement surface is compiler-level BINDING, asserted both directions
against a permanent fixture theme:

  1. change a token a component DECLARES  -> its compiled graph MUST change.
     Impossible to pass while hardcoding: a hardcoded component compiles to the
     same graph under both themes, so the hashes match and the test fails.
  2. change a token it does NOT declare   -> its graph MUST NOT change.
     Catches coupling the declaration does not admit.
  3. every token read at compile time appears in `consumes`.
  4. the two themes must expose the SAME token set with DIFFERENT values, or
     rows 1 and 2 are vacuous and would pass by accident.

tests/fixtures/themes/contrast-probe.json is a FIXTURE, not a throwaway.
Generating it, running once and deleting it destroys the proof for every future
run — which is the whole reason it is checked in.

A literal lint stays as a supplemental smell test. It walks the AST rather than
grepping text, because a text grep flags `t.ink` (reading the theme — correct)
and `ctx.name("ink")` (naming a node — structural) alongside real hardcoding.
It is non-exhaustive by nature; the binding assertions are the gate.
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from studio import components as R          # noqa: E402
from studio.theme import load               # noqa: E402

PROBE = ROOT / "tests" / "fixtures" / "themes" / "contrast-probe.json"

# Params good enough to compile each component. Derived from the spec by type
# so a new component needs no entry here — hand-registering each one is a
# maintenance trap, and a component silently skipped is a component untested.
# SAMPLE_PARAMS overrides only where a generic value will not do.
SAMPLE_PARAMS = {}

BY_TYPE = {
    "seed": 4471,
    "integer": 3,
    "number": 0.25,
    "string": "sample",
    "boolean": True,
    "point": [0.5, 0.5],
    "region": [0.25, 0.25, 0.75, 0.75],
}


def sample_params(spec):
    """Every required param filled, declared defaults left alone."""
    out = {}
    for key, decl in (spec.get("params") or {}).items():
        if not decl.get("required"):
            continue
        value = BY_TYPE.get(decl["type"])
        if decl["type"] in ("number", "integer"):
            lo, hi = decl.get("minimum"), decl.get("maximum")
            if lo is not None and value < lo:
                value = lo
            if hi is not None and value > hi:
                value = hi
        out[key] = value
    out.update(SAMPLE_PARAMS.get(spec["name"], {}))
    return out

failures = []


def fail(msg):
    failures.append(msg)
    print(f"  FAIL {msg}")


def compile_hash(name, theme, params):
    return R.compile(name, theme, params, frames=48, fps=24)["graph_hash"]


# Blend modes and asset paths are unambiguous look decisions: appearing as a
# literal means the component chose one instead of reading it. Names are NOT
# evidence — `t.ink` reading the theme and `ctx.name("ink")` labelling a node
# are both correct, and a text grep flags them, which is why this walks the AST
# for literal VALUES in executable positions instead.
#
# Hardcoded colour numbers are deliberately NOT chased here. A tuple of four
# floats is indistinguishable from a region or a pair of coordinates, and the
# binding assertions above catch a hardcoded colour with certainty: the graph
# stops changing when the token changes, and `consumes` stops matching `read`.
BLEND_MODES = {"Multiply", "Screen", "Overlay", "SoftLight", "HardLight",
               "Darken", "Lighten", "ColorBurn", "ColorDodge", "Difference"}
ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".exr", ".tif", ".tiff", ".mov")
HEX_COLOUR = re.compile(r"^#?[0-9a-fA-F]{6}([0-9a-fA-F]{2})?$")


def lint_targets():
    return sorted((ROOT / "studio" / "components").glob("*.py")) + \
        [ROOT / "studio" / "comp.py"]


def aesthetic_literals(path):
    """String constants in executable positions that decide a look."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and \
                    isinstance(body[0].value, ast.Constant) and \
                    isinstance(body[0].value.value, str):
                docstrings.add(id(body[0].value))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or id(node) in docstrings:
            continue
        v = node.value
        if not isinstance(v, str):
            continue
        if v in BLEND_MODES:
            out.append((path, node.lineno, f"blend mode {v!r} — read it from the theme"))
        elif v.lower().endswith(ASSET_SUFFIXES):
            out.append((path, node.lineno, f"asset path {v!r}"))
        elif HEX_COLOUR.match(v) and v.startswith("#"):
            out.append((path, node.lineno, f"hex colour {v!r}"))
    return out


def main():
    base = load("ink-wash")
    probe = load(PROBE)

    # --- 4. fixture parity: without this the binding rows prove nothing ------
    print("=== fixture parity ===")
    if set(base.tokens) != set(probe.tokens):
        only_base = sorted(set(base.tokens) - set(probe.tokens))
        only_probe = sorted(set(probe.tokens) - set(base.tokens))
        fail(f"token sets differ — only in ink-wash: {only_base}, "
             f"only in contrast-probe: {only_probe}")
    else:
        same = [k for k in base.tokens if base.tokens[k] == probe.tokens[k]]
        if same:
            fail(f"contrast-probe shares values with ink-wash for {same} — "
                 "a shared value makes the binding assertion vacuous for it")
        else:
            print(f"  ok  {len(base.tokens)} tokens, all values differ")

    components = R.discover()
    if not components:
        fail("no components discovered — the whole test is vacuous")

    for name in sorted(components):
        spec = components[name].SPEC
        params = sample_params(spec)
        print(f"=== {name} v{spec['version']} ===")

        try:
            result = R.compile(name, base, params, frames=48, fps=24)
        except Exception as e:                       # noqa: BLE001
            fail(f"{name}: does not compile under ink-wash: {e}")
            continue
        baseline = result["graph_hash"]

        # --- 3. no undeclared reads -------------------------------------
        undeclared = result["read"] - set(spec["consumes"])
        if undeclared:
            fail(f"{name}: reads undeclared token(s) {sorted(undeclared)}")

        declared = set(spec["consumes"])
        unread = declared - result["read"]
        if unread:
            fail(f"{name}: declares {sorted(unread)} in `consumes` but never "
                 "reads them — a stale declaration misleads the next editor")

        # --- 1. consumed token changed => graph MUST change -------------
        for token in sorted(declared):
            altered = base.replacing(token, probe.tokens[token])
            try:
                got = compile_hash(name, altered, params)
            except Exception as e:                   # noqa: BLE001
                fail(f"{name}: fails to compile with {token!r} from the probe: {e}")
                continue
            if got == baseline:
                fail(f"{name}: declares `{token}` but changing it does not "
                     "change the graph — the value is hardcoded, or the "
                     "declaration is wrong")
            else:
                print(f"  ok  {token}: binds")

        # --- 2. non-consumed token changed => graph MUST NOT change -----
        for token in sorted(set(base.tokens) - declared):
            altered = base.replacing(token, probe.tokens[token])
            try:
                got = compile_hash(name, altered, params)
            except Exception as e:                   # noqa: BLE001
                fail(f"{name}: fails to compile with {token!r} from the probe: {e}")
                continue
            if got != baseline:
                fail(f"{name}: changing undeclared `{token}` changed the graph "
                     "— hidden coupling the spec does not admit")

        # --- and it must survive the probe theme wholesale ---------------
        try:
            whole = compile_hash(name, probe, params)
        except Exception as e:                       # noqa: BLE001
            fail(f"{name}: does not compile under contrast-probe: {e}")
        else:
            if whole == baseline:
                fail(f"{name}: identical graph under both themes — it ignores "
                     "the theme entirely")

    # --- supplemental lint ----------------------------------------------
    print("=== supplemental lint (non-exhaustive) ===")
    hits = []
    for path in lint_targets():
        hits.extend(aesthetic_literals(path))
    if hits:
        for path, lineno, what in hits:
            fail(f"aesthetic literal in the mechanism: "
                 f"{path.relative_to(ROOT)}:{lineno} {what}")
    else:
        print(f"  ok  no aesthetic literal in {len(lint_targets())} module(s)")

    print()
    if failures:
        print(f"THEME BINDING FAILED — {len(failures)} problem(s)")
        return 1
    print("THEME BINDING GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
