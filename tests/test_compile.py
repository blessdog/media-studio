#!/usr/bin/env python3
"""Phase-1 exit-condition test. Plain script (no framework), run with repo venv:

    .venv/bin/python tests/test_compile.py [--render]

Exercises: golden compile+verify, idempotent recompile, lint rejection of a
corrupted IR. Nonzero exit on any failure.
"""
import copy
import sys
import tempfile
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ir as irmod
from studio import lint as lintmod
from studio import compile as compmod
from studio import verify as verifymod

FIX = Path(__file__).resolve().parent / "fixtures" / "golden-ir.json"
passed = failed = 0


def check(name, cond):
    global passed, failed
    print(f"  {'PASS' if cond else 'FAIL'}: {name}")
    if cond:
        passed += 1
    else:
        failed += 1


def main():
    do_render = "--render" in sys.argv

    # 1. golden compiles + verifies green
    ir, base = irmod.load(FIX)
    errs, _ = lintmod.lint(ir, base)
    check("golden lint green", not errs)
    otio = FIX.with_suffix(".otio")
    proj, tl, cached = compmod.compile_ir(ir, base, otio)
    check("golden compiled (not cached first time OR reused)", tl is not None)
    check("interchange file written", otio.is_file())
    verrs = verifymod.verify_timeline(ir, proj, tl)
    check("golden structure verify green", not verrs)

    # 2. idempotent recompile -> reuse, no rebuild
    proj2, tl2, cached2 = compmod.compile_ir(ir, base, otio)
    check("recompile reuses timeline (cached=True)", cached2 is True)
    check("recompile verify green", not verifymod.verify_timeline(ir, proj2, tl2))

    # 3. corrupted IR rejected by lint (srcOut past asset length)
    bad = copy.deepcopy(ir)
    bad["edits"][0]["srcOut"] = 99999
    berrs, _ = lintmod.lint(bad, base)
    check("corrupted IR (srcOut beyond asset) fails lint", bool(berrs))

    # 4. optional render verify
    if do_render:
        rerrs, out = verifymod.verify_render(
            ir, proj, tl, base / "outputs" / "compiled")
        check("render verify green", not rerrs)
        check("render output exists", out and Path(out).is_file())

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
