"""Themes: the look, as data.

A theme is a flat dict of tokens. Components read tokens; they never contain a
hardcoded look value. That is the whole theming layer — there is no theme
engine, no style transfer, no render matrix, and adding one would be the mistake
this design exists to avoid.

**The boundary is aesthetic values, not all constants.** Components keep their
structural constants, normalised coordinates, indices, cell counts and animation
maths in code, because those are mechanism. Pushing them in here is exactly how
"no literals" turns into the theme engine we refused to build.

`load()` returns a `Theme` that RECORDS every token read. That recording is what
makes the contract enforceable rather than aspirational: a component declares
`consumes`, and `tests/test_theme_binding.py` compiles it and compares what it
actually touched against what it claimed. A component cannot quietly depend on a
token it did not declare, and cannot declare one it ignores.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES_DIR = ROOT / "themes"


class ThemeError(ValueError):
    pass


class Themed:
    """Marker: this value came out of a theme rather than out of a component.

    The binding test can only prove a component's `consumes` declaration
    matches its behaviour. It cannot see a look decision that is hardcoded AND
    undeclared — that combination is self-consistent and passes every
    assertion. (Verified 2026-08-06 by planting exactly that component.)

    Tagging closes it structurally instead: values leave a theme wearing this
    marker, and `studio/comp.py:check_look_binding()` refuses any look-bearing
    Fusion input whose value is not wearing it. A hardcoded blend mode then
    cannot compile, declared or not.
    """


class ThemedFloat(float, Themed):
    pass


class ThemedInt(int, Themed):
    pass


class ThemedStr(str, Themed):
    pass


class ThemedList(list, Themed):
    pass


def tag(value):
    """Wrap a theme value so its origin travels with it.

    bool is checked before int deliberately — bool subclasses int, and a
    ThemedInt(True) would silently become 1.
    """
    if isinstance(value, Themed):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return ThemedFloat(value)
    if isinstance(value, int):
        return ThemedInt(value)
    if isinstance(value, str):
        return ThemedStr(value)
    if isinstance(value, (list, tuple)):
        return ThemedList(tag(v) for v in value)
    return value


class Theme:
    """A theme with read-tracking.

    Access is by attribute or item — `theme.ink` and `theme["ink"]` are the same
    lookup and both record. An unknown token raises rather than returning a
    default: a silent default is how a component ends up looking correct under
    the theme it was written against and wrong under every other one.
    """

    def __init__(self, name, tokens, version=1, path=None):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "_tokens", dict(tokens))
        object.__setattr__(self, "_read", set())

    def __getitem__(self, token):
        if token not in self._tokens:
            raise ThemeError(
                f"theme {self.name!r} has no token {token!r} — "
                f"known: {', '.join(sorted(self._tokens))}")
        self._read.add(token)
        return tag(self._tokens[token])

    def __getattr__(self, token):
        if token.startswith("_"):
            raise AttributeError(token)
        return self[token]

    def __setattr__(self, k, v):
        raise ThemeError("themes are read-only at compile time")

    def __contains__(self, token):
        return token in self._tokens

    @property
    def tokens(self):
        return dict(self._tokens)

    @property
    def read(self):
        """Tokens actually looked up since this Theme was constructed."""
        return set(self._read)

    def reset_reads(self):
        self._read.clear()

    def hash(self):
        blob = json.dumps(self._tokens, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def replacing(self, token, value):
        """A copy with one token changed — the primitive the binding test is
        built on. Changing a CONSUMED token must change the compiled graph;
        changing a non-consumed one must not."""
        if token not in self._tokens:
            raise ThemeError(f"theme {self.name!r} has no token {token!r}")
        tokens = dict(self._tokens)
        tokens[token] = value
        return Theme(f"{self.name}+{token}", tokens, self.version, self.path)


def load(source):
    """Load a theme from a path, or by name from `themes/`."""
    path = Path(source)
    if not path.suffix:
        path = THEMES_DIR / f"{source}.json"
    if not path.is_file():
        raise ThemeError(f"no theme at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for required in ("name", "version", "tokens"):
        if required not in data:
            raise ThemeError(f"{path.name}: missing {required!r}")
    return Theme(data["name"], data["tokens"], data["version"], path)


def available():
    if not THEMES_DIR.is_dir():
        return []
    return sorted(p.stem for p in THEMES_DIR.glob("*.json"))
