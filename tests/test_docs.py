#!/usr/bin/env python3
"""Documentation-decay test. Plain script (no framework), run with repo venv:

    .venv/bin/python tests/test_docs.py

AGENTS.md is the cold-start contract (AGENTS.md §Cold-start test): a fresh
agent with zero conversation history must be able to run this studio from that
file alone. Nothing enforced that, so it silently went stale — on 2026-08-03
it was missing two of fourteen tools and three of beat-grid's five flags, and
a session nearly rebuilt work that already existed.

This makes that decay a test failure instead of a discovery. Checks:

  1. every tools/*.py appears in AGENTS.md
  2. every argparse flag appears in the AGENTS.md lines describing its tool
  3. STATUS.md stays a REFERENCE, not a journal — under STATUS_MAX_LINES

Waivers are explicit and visible. Silently undocumented is the failure mode
being fixed; do not add a waiver to make a red test green without a reason.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "AGENTS.md"
STATUS = ROOT / "STATUS.md"

# A reference is read top-to-bottom every session; a journal is appended to and
# never read in full. Past this, STATUS.md has stopped being the former.
# History belongs in docs/JOURNAL.md and in git log.
STATUS_MAX_LINES = 150

# Flags deliberately absent from AGENTS.md, with the reason. Debug/escape
# hatches a cold-start agent does not need are legitimate; creative verbs are
# not.
WAIVERS = {
    # "tool.py": {"--flag": "why"},
}

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    print(f"  {'PASS' if cond else 'FAIL'}: {name}")
    if detail and not cond:
        for line in detail.splitlines():
            print(f"        {line}")
    if cond:
        passed += 1
    else:
        failed += 1


def flags_in(path):
    """Every long option the tool's argparse actually accepts."""
    src = path.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'add_argument\(\s*"(--[a-z0-9-]+)"', src)))


def lines_mentioning(doc, name):
    """AGENTS.md lines that describe this tool — its row(s) in the verbs table.
    edit-ir.py gets one row per subcommand, so this is a list, not a line."""
    return [ln for ln in doc.splitlines() if name in ln]


def main():
    doc = AGENTS.read_text(encoding="utf-8")
    tools = sorted(ROOT.glob("tools/*.py"))

    check("tools/ exists and is non-empty", bool(tools))

    # 1. every tool is documented at all
    undocumented = [t.name for t in tools if t.name not in doc]
    check(
        f"all {len(tools)} tools appear in AGENTS.md",
        not undocumented,
        "missing: " + ", ".join(undocumented)
        + "\na cold-start agent cannot know these exist, and may rebuild them",
    )

    # 2. every flag appears in that tool's row(s)
    for tool in tools:
        if tool.name in undocumented:
            continue  # already reported; flag-checking it adds only noise
        rows = "\n".join(lines_mentioning(doc, tool.name))
        waived = WAIVERS.get(tool.name, {})
        missing = [f for f in flags_in(tool) if f not in rows and f not in waived]
        check(
            f"{tool.name} — all flags documented",
            not missing,
            "undocumented: " + " ".join(missing),
        )

    # 3. STATUS.md is a reference, not a journal
    n = len(STATUS.read_text(encoding="utf-8").splitlines())
    check(
        f"STATUS.md is a reference ({n} lines, cap {STATUS_MAX_LINES})",
        n <= STATUS_MAX_LINES,
        f"{n - STATUS_MAX_LINES} lines over. Move dated history to "
        "docs/JOURNAL.md; STATUS.md holds current state only — what works, "
        "what is broken, what is next.",
    )

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
