#!/usr/bin/env python3
"""Documentation-decay + gate-integrity test. Plain script, run via the gate:

    make check                    (or: .venv/bin/python tests/test_docs.py)

AGENTS.md is the cold-start contract (AGENTS.md §Cold-start test): a fresh
agent with zero conversation history must run this studio from that file alone.
Nothing enforced it, so it silently went stale — on 2026-08-03 it was missing
two of fourteen tools and fourteen flags, and a session nearly rebuilt work
that already existed.

Every check here exists because an artifact in this repo had no writer, no
reader, or no failure mode. The rule being enforced: an artifact nobody writes,
nobody reads, and nothing fails over is dead on arrival.

  1. every tools/*.py appears in AGENTS.md          (writer: whoever adds a verb)
  2. every argparse flag appears in its row          (same)
  3. STATUS.md stays a REFERENCE, not a journal      (reader: next session)
  4. every tests/test_*.py is wired into the Makefile (else the gate skips it)
  5. .githooks/pre-commit exists and is executable    (else nothing runs the gate)
  6. CLAUDE.md points at the gate                     (else nobody installs it)
  7. docs/JOURNAL.md exists and STATUS.md links it    (else history is deleted,
                                                       not moved, at the cap)

Waivers are explicit and visible. Silently undocumented is the failure mode
being fixed; do not add a waiver to make a red test green without a reason.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "AGENTS.md"
STATUS = ROOT / "STATUS.md"
JOURNAL = ROOT / "docs" / "JOURNAL.md"
CLAUDE = ROOT / "CLAUDE.md"
MAKEFILE = ROOT / "Makefile"
HOOK = ROOT / ".githooks" / "pre-commit"

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
        f"{n - STATUS_MAX_LINES} lines over. MOVE dated history to "
        "docs/JOURNAL.md — do not delete it. STATUS.md holds current state "
        "only: what works, what is broken, what is next.",
    )

    # 4. the gate actually covers every test — a test left out of the Makefile
    #    is a test that never runs, which is how this repo got here
    mk = MAKEFILE.read_text(encoding="utf-8") if MAKEFILE.is_file() else ""
    ungated = [t.name for t in sorted(ROOT.glob("tests/test_*.py")) if t.name not in mk]
    check(
        "every test is wired into the Makefile gate",
        MAKEFILE.is_file() and not ungated,
        ("Makefile missing" if not MAKEFILE.is_file()
         else "not in OFFLINE or LIVE: " + ", ".join(ungated))
        + "\nan ungated test runs only when someone remembers — which is never",
    )

    # 5. something has to RUN the gate
    check(
        ".githooks/pre-commit exists and is executable",
        HOOK.is_file() and os.access(HOOK, os.X_OK),
        "the gate is theatre without a hook. chmod +x .githooks/pre-commit",
    )

    # 6. and a cold-start session has to learn the gate exists
    claude = CLAUDE.read_text(encoding="utf-8") if CLAUDE.is_file() else ""
    check(
        "CLAUDE.md points at `make check`",
        "make check" in claude,
        "a fresh session will never run the gate it was never told about",
    )

    # 7. the cap in check 3 sends history somewhere — that somewhere must exist,
    #    and STATUS.md must name it, or the next session deletes instead of moves
    check(
        "docs/JOURNAL.md exists and is non-empty",
        JOURNAL.is_file() and JOURNAL.stat().st_size > 0,
        "check 3 tells the next agent to move history here; if it does not "
        "exist, history gets deleted instead",
    )
    check(
        "STATUS.md links to docs/JOURNAL.md",
        "JOURNAL.md" in STATUS.read_text(encoding="utf-8"),
        "an archive nothing points at is unreachable, and dies",
    )

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
