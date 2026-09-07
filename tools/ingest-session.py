#!/usr/bin/env python3
"""Several ingested recordings -> ONE session timeline, in the order given.

    .venv/bin/python tools/ingest-session.py <ws-or-story.json>... --name N
        [--cuts cuts.json] [--gap-frames 0] [--no-compile] [--render]

Each input is a workspace already produced by ingest-recording.py (its
story.json is silence-stripped and transcript-anchored). This verb does not
re-analyse anything: it concatenates the per-recording IRs onto one spine,
offsetting every edit and marker by a running record frame, and drops a Cyan
marker at the head of each recording so the sources are navigable in Resolve.
Output workspace: outputs/projects/<name>/ with story.json and sources.json
(asset id -> the workspace, recording and transcript it came from).

`--cuts` is the rough cut: a JSON list of {"source": <ws>, "start": s,
"end": s, "note": ...} in cut order, times in SOURCE seconds (what the
transcript prints). Each cut keeps only the source's silence-stripped spans
that fall inside [start, end) and lands them back to back, so the cut list is
the film's edit decisions in a form a person can read and diff. Without
--cuts every source lands whole, in the order given.

Refuses recordings that disagree on fps or resolution — project fps is
immutable once a timeline exists (AGENTS.md hard doctrine), so a mixed rate
cannot be concatenated, only conformed first.

PRIOR ART (searched 2026-09-07): RoughCut by DrRave (Resolve Workflow
Integration: transcribes, matches a script, assembles a hero cut), Cutsio
(silence removal + transcript selects -> XML for Resolve), Selects (multi-track
sync + diarize + chapters -> rough cut), and Resolve 19+'s own text-based
editing. All of them own the timeline, which breaks this studio's locked
one-way flow (Story IR is the ONLY source of truth for an edit; scripts never
touch a human-edited timeline). auto-editor's multi-input mode was measured
the same day: its v3 export dropped the first of two inputs (16 clips came
back, all from the second file). So the concat is done at the IR level, where
the studio already has lint, schema validation and idempotent compile.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ir as irmod
from studio import lint as lintmod
from studio import registry as regmod

ROOT = Path(__file__).resolve().parent.parent
SOURCE_MARKER_COLOR = "Cyan"


def _story_path(arg):
    p = Path(arg)
    if p.is_file():
        return p.resolve()
    if p.is_dir() and (p / "story.json").is_file():
        return (p / "story.json").resolve()
    ws = ROOT / "outputs" / "projects" / arg / "story.json"
    if ws.is_file():
        return ws.resolve()
    raise FileNotFoundError(f"no story.json for {arg!r}")


def _window(src, start_f, end_f):
    """Trim a source IR to the track-1 spans inside [start_f, end_f) source
    frames and re-pack them from record 0. Other tracks and markers outside
    the window are dropped; markers inside are remapped."""
    kept = []
    for e in sorted(src["edits"], key=lambda e: e["record"]):
        if e.get("track", 1) != 1:
            continue
        a, b = max(e["srcIn"], start_f), min(e["srcOut"], end_f)
        if a < b:
            kept.append((e, a, b))
    if not kept:
        raise ValueError(f"window {start_f}-{end_f} keeps no frames")
    out = dict(src)
    out["edits"], out["markers"], rec = [], [], 0
    for e, a, b in kept:
        ne = dict(e)
        ne.update(srcIn=a, srcOut=b, record=rec)
        out["edits"].append(ne)
        for m in src.get("markers", []):
            old = e["record"] + (a - e["srcIn"])
            if old <= m["frame"] < old + (b - a):
                nm = dict(m)
                nm["frame"] = rec + (m["frame"] - old)
                out["markers"].append(nm)
        rec += b - a
    return out


def build_session_ir(name, sources, gap_frames=0, created_by="ingest-session"):
    """sources: [(label, ir_dict, base_dir)] or [(label, ir, base, (start_f, end_f))].
    Returns (session_ir, sources_map)."""
    if not sources:
        raise ValueError("no sources")
    first = sources[0][1]
    fps, res = first["timebase"]["fps"], first["resolution"]
    assets, edits, markers, smap = [], [], [], {}
    offset = 0
    seen_assets = {}
    for i, entry in enumerate(sources):
        label, src, base = entry[:3]
        if len(entry) > 3 and entry[3] is not None:
            src = _window(src, *entry[3])
        if src["timebase"]["fps"] != fps:
            raise ValueError(f"{label}: fps {src['timebase']['fps']} != {fps}")
        if src["resolution"] != res:
            raise ValueError(f"{label}: resolution {src['resolution']} != {res}")
        amap = {}
        for a in src["assets"]:
            path = str(irmod.asset_path(a, base))
            if path in seen_assets:
                amap[a["id"]] = seen_assets[path]
                continue
            aid = f"r{i}-{a['id']}"[:32]
            amap[a["id"]] = seen_assets[path] = aid
            assets.append({"id": aid, "kind": a["kind"], "path": path})
            smap[aid] = {"source": label, "workspace": str(base),
                         "recording": path,
                         "transcript": str(base / "transcript.json")
                         if (base / "transcript.json").is_file() else None,
                         "record": offset}
        markers.append({"frame": offset, "color": SOURCE_MARKER_COLOR,
                        "name": f"SRC {i} {label} {entry[4] if len(entry) > 4 else ''}".strip(),
                        "note": str(irmod.asset_path(src["assets"][0], base))})
        for e in src["edits"]:
            ne = dict(e)
            ne["id"] = f"s{i}-{e['id']}"[:32]
            ne["asset"] = amap[e["asset"]]
            ne["record"] = e["record"] + offset
            edits.append(ne)
        for m in src.get("markers", []):
            nm = dict(m)
            nm["frame"] = m["frame"] + offset
            markers.append(nm)
        offset += irmod.extent_frames(src) + gap_frames
    session = {
        "irVersion": "0.2",
        "name": name,
        "timebase": {"fps": fps},
        "resolution": dict(res),
        "assets": assets,
        "edits": edits,
        "markers": markers,
        "provenance": {"generator": "ingest-session-v0", "createdBy": created_by},
    }
    return session, smap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="*",
                    help="workspace names, dirs, or story.json paths, in cut order")
    ap.add_argument("--name", required=True, help="session workspace name")
    ap.add_argument("--cuts", help="JSON cut list: [{source, start, end, note}] "
                    "in SOURCE seconds; overrides positional order")
    ap.add_argument("--gap-frames", type=int, default=0,
                    help="black between recordings, in frames")
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()

    plan = [{"source": s} for s in args.sources]
    if args.cuts:
        plan = json.loads(Path(args.cuts).read_text(encoding="utf-8"))

    loaded, cache = [], {}
    for c in plan:
        try:
            p = _story_path(c["source"])
        except FileNotFoundError as e:
            print(f"FAIL: {e}")
            return 1
        if p not in cache:
            cache[p] = irmod.load(p)      # schema-validated, not just linted
        ir, base = cache[p]
        window = None
        if "start" in c or "end" in c:
            fps = irmod.fps(ir)
            window = (int(round(float(c.get("start", 0)) * fps)),
                      int(round(float(c["end"]) * fps)) if "end" in c
                      else max(e["srcOut"] for e in ir["edits"]))
        loaded.append((p.parent.name, ir, base, window, c.get("note", "")))
        print(f"source: {p.parent.name}  "
              f"{'whole' if window is None else str(c.get('start', 0)) + '-' + str(c.get('end', 'end')) + 's'}"
              f"  {c.get('note', '')}")

    try:
        session, smap = build_session_ir(args.name, loaded, args.gap_frames)
    except ValueError as e:
        print(f"FAIL: {e}")
        return 1

    ws = ROOT / "outputs" / "projects" / args.name
    ws.mkdir(parents=True, exist_ok=True)
    ir_path = ws / "story.json"
    ir_path.write_text(json.dumps(session, indent=1), encoding="utf-8")
    (ws / "sources.json").write_text(json.dumps(smap, indent=1), encoding="utf-8")
    fps = float(irmod.fps(session))
    total = irmod.extent_frames(session)
    print(f"session IR: {len(loaded)} cuts from {len(session['assets'])} recordings, {len(session['edits'])} edits, "
          f"{total} frames = {total / fps / 60:.1f} min -> {ir_path}")

    reg = regmod.connect()
    regmod.record_ir(reg, session, ir_path)

    errors, warnings = lintmod.lint(session, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("lint: green")

    if args.no_compile:
        print("SESSION OK (compile skipped)")
        return 0

    from studio import compile as compmod
    from studio import verify as verifymod
    proj, tl, cached = compmod.compile_ir(session, ws, ws / "story.otio")
    print(f"{'reused' if cached else 'compiled'} timeline '{tl.GetName()}'")
    verrs = verifymod.verify_timeline(session, proj, tl)
    if verrs:
        print("VERIFY FAIL:")
        for e in verrs:
            print(f"  {e}")
        return 1
    print("verify (structure): green")
    proj.SetCurrentTimeline(tl)
    if args.render:
        rerrs, out = verifymod.verify_render(session, proj, tl, ws / "render")
        if rerrs:
            print("VERIFY FAIL (render):")
            for e in rerrs:
                print(f"  {e}")
            return 1
        regmod.record_render(reg, session, out, verified=True)
        print(f"verify (render): green | output: {out}")
    print("SESSION OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
