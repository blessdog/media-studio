"""Load, validate, and identity-hash Story IR documents."""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "story-ir.schema.json"


class IRError(ValueError):
    pass


def load(ir_path):
    """Read + schema-validate an IR file. Returns (ir_dict, base_dir)."""
    ir_path = Path(ir_path).resolve()
    try:
        ir = json.loads(ir_path.read_text())
    except json.JSONDecodeError as e:
        raise IRError(f"{ir_path.name}: not valid JSON — {e}") from e
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(ir), key=lambda e: list(e.absolute_path))
    if errors:
        msgs = [f"  at {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
                for e in errors]
        raise IRError(f"{ir_path.name}: schema violations\n" + "\n".join(msgs))
    return ir, ir_path.parent


def fps(ir):
    """timebase.fps as a Fraction."""
    num, den = ir["timebase"]["fps"].split("/")
    return Fraction(int(num), int(den))


def asset_path(asset, base_dir):
    p = Path(asset["path"])
    return p if p.is_absolute() else (base_dir / p).resolve()


def content_hash(ir):
    """Canonical hash of the IR content (identity for idempotence)."""
    canon = json.dumps(ir, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()


def timeline_name(ir):
    return f"{ir['name']}@{content_hash(ir)[:8]}"


def extent_frames(ir):
    """Total timeline length: the furthest record + duration."""
    return max(e["record"] + (e["srcOut"] - e["srcIn"]) for e in ir["edits"])
