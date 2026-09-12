#!/usr/bin/env python3
"""ingest-osmo — Osmo Action 5 Pro clips -> asserted manifest -> Story IR -> Resolve timeline.

    .venv/bin/python tools/ingest-osmo.py <clip.MP4>... --name N [--no-compile]

Spec: docs/CINEMATIC-PIPELINE.md §3-4. Originals are copied read-only into a
dated workspace, every clip is ffprobed and asserted (hevc, 10-bit, 3840x2160,
24 or 23.976). A failing clip is FLAGGED in manifest.json and left out of the
timeline, never imported silently. Passing clips become one full-length edit
each on V1, compiled through the studio's own Story IR -> OTIO -> Resolve path
and stamped DaVinci YRGB, Rec.709 / Gamma 2.4.

Nothing here grades anything. The base grade is applied by tools/apply-grade.py;
the per-shot pass is human by design (§7).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from studio import intake as intakemod       # noqa: E402
from studio import lint as lintmod           # noqa: E402
from studio import osmo                      # noqa: E402
from studio import probe as probemod         # noqa: E402
from studio import registry as regmod        # noqa: E402

# Measured 2026-09-12 on 21.1: with separateColorSpaceAndGamma = '0' (the
# default) the timeline space is ONE combined value and the split keys the
# API stub shows as examples ('Rec.709' + 'Gamma 2.4') are rejected. A fresh
# project defaults to 'Rec.709 (Scene)', so stamping this is not optional.
PROJECT_COLOUR = {"colorScienceMode": "davinciYRGB",
                  "colorSpaceTimeline": "Rec.709 Gamma 2.4"}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _frames(meta):
    return int(meta["duration"] * Fraction(meta["fps"]))


def write_report(ws, manifest, compiled):
    ok = [c for c in manifest["clips"] if c["status"] == "ok"]
    bad = [c for c in manifest["clips"] if c["status"] == "flagged"]
    lines = [f"# {manifest['name']} — ingest report", "",
             f"Created {manifest['created']}. Workspace `{ws}`.", "",
             f"## Imported ({len(ok)})", ""]
    lines += [f"- `{c['file']}` {c['width']}x{c['height']} @ {c['fps']} {c['codec']} {c['pix_fmt']}"
              f" {c['duration']:.1f}s  ISO {c['iso'] or 'not in tags'}" for c in ok] or ["- none"]
    lines += ["", f"## Flagged, not imported ({len(bad)})", ""]
    lines += [f"- `{c['file']}`: " + "; ".join(c["reasons"]) for c in bad] or ["- none"]
    lines += ["", "## Awaiting the human pass (all imported clips, by design)", ""]
    lines += [f"- `{c['file']}`: balance, CineFocus focus point and aperture, per-shot review" for c in ok] or ["- none"]
    lines += ["", f"Timeline: {'compiled in Resolve' if compiled else 'NOT compiled'}.",
              "Base grade: not applied by this tool; run tools/apply-grade.py."]
    (ws / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--name", required=True, help="workspace name; the folder is <date>-<name>")
    ap.add_argument("--no-compile", action="store_true", help="manifest + IR + lint only, skip Resolve")
    args = ap.parse_args()

    today = dt.date.today().isoformat()
    name = f"{today}-{args.name}".lower().replace("_", "-").replace(" ", "-")
    ws = ROOT / "outputs" / "projects" / name
    ws.mkdir(parents=True, exist_ok=True)
    reg = regmod.connect()

    manifest = {"name": name, "created": dt.datetime.now().isoformat(timespec="seconds"),
                "spec": "docs/CINEMATIC-PIPELINE.md", "clips": []}
    passing = []
    for i, src in enumerate(args.clips):
        src = Path(src).expanduser().resolve()
        if not src.is_file():
            print(f"FAIL: no such file {src}")
            return 1
        dest = intakemod.file_media(src, ws)
        os.chmod(dest, 0o444)
        meta = probemod.probe(dest)
        ok, reasons = osmo.assess(meta)
        digest = _sha256(dest)
        regmod.record_asset(reg, dest, kind="video", sha256=digest, probe=meta)
        entry = {"source": str(src), "file": dest.name, "sha256": digest,
                 "duration": meta["duration"], "fps": meta["fps"], "codec": meta["codec"],
                 "pix_fmt": meta["pix_fmt"], "bits": meta["bits"],
                 "width": meta["width"], "height": meta["height"],
                 "iso": osmo.iso_from_tags(meta), "tags": {**meta["format_tags"], **meta["stream_tags"]},
                 "status": "ok" if ok else "flagged", "reasons": reasons}
        manifest["clips"].append(entry)
        tag = "ok     " if ok else "FLAGGED"
        print(f"{tag} {dest.name}: {meta['width']}x{meta['height']} @ {meta['fps']} {meta['codec']} {meta['pix_fmt']} {meta['duration']:.1f}s"
              + ("" if ok else "  <- " + "; ".join(reasons)))
        if ok:
            passing.append({"id": f"c{i:02d}", "path": str(dest), "frames": _frames(meta),
                            "fps": meta["fps"], "width": meta["width"], "height": meta["height"]})

    (ws / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"manifest: {ws / 'manifest.json'}  ({len(passing)} ok, {len(manifest['clips']) - len(passing)} flagged)")

    if not passing:
        write_report(ws, manifest, compiled=False)
        print("INGEST: nothing to compile, every clip was flagged")
        return 1
    mixed = {(c["fps"], c["width"], c["height"]) for c in passing}
    if len(mixed) > 1:
        write_report(ws, manifest, compiled=False)
        print(f"INGEST FAIL: passing clips disagree on fps/size {sorted(mixed)}; project fps is immutable")
        return 1

    ir = osmo.build_ir(name, passing)
    ir_path = ws / "story.json"
    ir_path.write_text(json.dumps(ir, indent=1), encoding="utf-8")
    regmod.record_ir(reg, ir, ir_path)
    print(f"IR written: {ir_path}")

    if osmo.is_ntsc_rate(passing[0]["fps"]):
        write_report(ws, manifest, compiled=False)
        print(f"BLOCKED: the camera wrote {passing[0]['fps']} (23.976). studio.lint refuses 1001-denominator rates "
              "until NDF handling is decided — VERIFY 12 in docs/CINEMATIC-PIPELINE-VERIFY.md")
        return 2

    errors, warnings = lintmod.lint(ir, ws)
    for w in warnings:
        print(f"  {w}")
    if errors:
        write_report(ws, manifest, compiled=False)
        print("LINT FAIL:")
        for e in errors:
            print(f"  {e}")
        return 1
    print("lint: green")

    if args.no_compile:
        write_report(ws, manifest, compiled=False)
        print("INGEST OK (compile skipped)")
        return 0

    from studio import compile as compmod
    from studio import verify as verifymod
    proj, tl, cached = compmod.compile_ir(ir, ws, ws / "story.otio")
    print(f"{'reused' if cached else 'compiled'} timeline '{tl.GetName()}'")
    verrs = verifymod.verify_timeline(ir, proj, tl)
    if verrs:
        print("VERIFY FAIL:")
        for e in verrs:
            print(f"  {e}")
        return 1
    print("verify (structure): green")
    if not proj.SetSettings(PROJECT_COLOUR):
        write_report(ws, manifest, compiled=True)
        print(f"FAIL: SetSettings({PROJECT_COLOUR}) returned False")
        return 1
    got = proj.GetSettings()
    drift = {k: got.get(k) for k, v in PROJECT_COLOUR.items() if str(got.get(k)) != v}
    if drift:
        write_report(ws, manifest, compiled=True)
        print(f"FAIL: project colour settings did not stick: {drift}")
        return 1
    print("project: DaVinci YRGB, Rec.709 / Gamma 2.4 (read back)")
    proj.SetCurrentTimeline(tl)
    write_report(ws, manifest, compiled=True)
    print(f"report: {ws / 'report.md'}")
    print("INGEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
