#!/usr/bin/env python3
"""apply-grade — put the human-authored base grade (.drx) on every V1 clip of a
DUPLICATE of the workspace's timeline, and verify per clip by reading the node
graph back.

    .venv/bin/python tools/apply-grade.py <workspace> --drx <look.drx> [--timeline-drx <tl.drx>] [--mode 0] [--suffix NAME]

Spec: docs/CINEMATIC-PIPELINE.md §5, §7. The grade is APPLIED, never authored
here, and never onto the timeline Ryan may have touched: the tool duplicates
the compiled timeline as <name>+<suffix> and applies there (one-way flow,
AGENTS.md doctrine). Success is what GetNumNodes/GetLUT report afterwards,
not what ApplyGradeFromDRX returns. Writes <ws>/grade-report.md.
"""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from studio import ir as irmod          # noqa: E402
from studio import lint as lintmod      # noqa: E402


def _timelines(proj):
    return [proj.GetTimelineByIndex(i) for i in range(1, proj.GetTimelineCount() + 1)]


def _graph_state(graph):
    n = graph.GetNumNodes()
    return {"nodes": n, "luts": [graph.GetLUT(i) or "" for i in range(1, n + 1)]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace")
    ap.add_argument("--drx", required=True, help="clip-level base grade, exported from a PowerGrade / gallery still")
    ap.add_argument("--timeline-drx", help="optional timeline-level grade (grain, halation)")
    ap.add_argument("--mode", type=int, default=0, help="ApplyGradeFromDRX gradeMode: 0 no keyframes, 1 source TC aligned, 2 start frames aligned")
    ap.add_argument("--suffix", help="duplicate timeline suffix (default: drx sha256[:8])")
    args = ap.parse_args()

    drx = Path(args.drx).expanduser().resolve()
    tl_drx = Path(args.timeline_drx).expanduser().resolve() if args.timeline_drx else None
    for p in (drx, tl_drx):
        if p is not None and not p.is_file():
            print(f"FAIL: no such file {p}")
            return 1
    digest = hashlib.sha256(drx.read_bytes()).hexdigest()
    suffix = args.suffix or f"grade-{digest[:8]}"

    ws = (ROOT / "outputs" / "projects" / args.workspace) \
        if not Path(args.workspace).is_dir() else Path(args.workspace).resolve()
    ir, _ = irmod.load(ws / "story.json")
    errors, _ = lintmod.lint(ir, ws)
    if errors:
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1

    from studio import compile as compmod
    proj, tl, cached = compmod.compile_ir(ir, ws, ws / "story.otio")
    print(f"timeline: {tl.GetName()} ({'cached' if cached else 'compiled'})")
    dup_name = f"{tl.GetName()}+{suffix}"
    if any(t and t.GetName() == dup_name for t in _timelines(proj)):
        print(f"FAIL: timeline {dup_name!r} already exists; it may carry human work. Pass --suffix for a fresh one")
        return 1
    dup = tl.DuplicateTimeline(dup_name)
    if not dup:
        print("FAIL: DuplicateTimeline returned nothing")
        return 1
    proj.SetCurrentTimeline(dup)
    print(f"duplicate: {dup.GetName()}")

    rows, failed = [], 0
    for item in dup.GetItemListInTrack("video", 1):
        graph = item.GetNodeGraph()
        before = _graph_state(graph)
        ok = graph.ApplyGradeFromDRX(str(drx), args.mode)
        after = _graph_state(graph)        # the next graph call: VERIFY 15 (forum-reported crash)
        changed = after != before
        rows.append((item.GetName(), ok, before, after, changed))
        failed += 0 if (ok and changed) else 1
        print(f"{'applied' if ok and changed else 'FAILED '} {item.GetName()}: nodes {before['nodes']}->{after['nodes']}, "
              f"luts {after['luts']}")

    tl_row = None
    if tl_drx:
        g = dup.GetNodeGraph()
        before = _graph_state(g)
        ok = g.ApplyGradeFromDRX(str(tl_drx), args.mode)
        after = _graph_state(g)
        tl_row = (ok, before, after)
        print(f"{'applied' if ok else 'FAILED '} timeline node: nodes {before['nodes']}->{after['nodes']}, luts {after['luts']}")
        failed += 0 if ok else 1

    lines = [f"# {ir['name']} — base grade application", "",
             f"Timeline `{dup.GetName()}` (duplicate of `{tl.GetName()}`).",
             f"Clip grade `{drx}` sha256 {digest}, mode {args.mode}.", "",
             "| clip | applied | nodes before → after | LUTs after |", "|---|---|---|---|"]
    lines += [f"| {n} | {'yes' if ok and ch else 'NO'} | {b['nodes']} → {a['nodes']} | {', '.join(x for x in a['luts'] if x) or '-'} |"
              for n, ok, b, a, ch in rows]
    if tl_row:
        ok, b, a = tl_row
        lines += ["", f"Timeline node `{tl_drx}`: {'applied' if ok else 'FAILED'}, nodes {b['nodes']} → {a['nodes']}."]
    lines += ["", "The per-shot pass (balance, CineFocus, review) is human work and has not been done."]
    (ws / "grade-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report: {ws / 'grade-report.md'}")
    print("APPLY-GRADE " + ("OK" if not failed else f"FAILED on {failed}"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
