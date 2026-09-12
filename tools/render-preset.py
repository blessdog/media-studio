#!/usr/bin/env python3
"""render-preset — save (or update) a named Resolve render preset from the CLI.

    .venv/bin/python tools/render-preset.py osmo-4k-h265 [--format mp4] [--codec auto] [--bitrate-kbps 80000] [--color-space-tag Rec.709] [--gamma-tag "Gamma 2.4"]

Spec: docs/CINEMATIC-PIPELINE.md §8. Needs Resolve open with a project loaded
(the preset is stored per user, not per project). `--codec auto` picks the
first codec whose name mentions H265 or HEVC for the chosen format; the flag
`--gamma-tag` exists so the §8 upload test can flip Rec.709 to Rec.709-A once.
Resolution is pinned to 3840x2160; frame rate is left to follow the timeline.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from studio.resolve import connect, ResolveUnavailable  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("--format", default="mp4")
    ap.add_argument("--codec", default="auto", help="exact codec key from GetRenderCodecs, or auto (H265/HEVC)")
    ap.add_argument("--bitrate-kbps", type=int, default=80000, help="VideoQuality bit-rate limit; err high, YouTube re-encodes")
    ap.add_argument("--color-space-tag", default="Rec.709")
    ap.add_argument("--gamma-tag", default="Gamma 2.4", help="flip to 'Rec.709-A' style tag only if the §8 upload test says so")
    args = ap.parse_args()

    try:
        app = connect()
    except ResolveUnavailable as e:
        print(f"RESOLVE   {e}")
        return 1
    if app.GetCurrentPage() is None:
        print("RESOLVE   a modal dialog has the UI; results would be void")
        return 1
    proj = app.GetProjectManager().GetCurrentProject()
    if not proj:
        print("FAIL: no current project; open or create one first")
        return 1

    # GetRenderCodecs returns {display name: internal id}, e.g. {'H.265': 'H265'};
    # SetCurrentRenderFormatAndCodec wants the internal id (measured 2026-09-12).
    codecs = proj.GetRenderCodecs(args.format) or {}
    if args.codec == "auto":
        pick = [v for k, v in codecs.items() if "265" in f"{k}{v}".upper() or "HEVC" in f"{k}{v}".upper()]
        if not pick:
            print(f"FAIL: no H.265 codec for format {args.format!r}; have {codecs}")
            return 1
        codec = pick[0]
    else:
        codec = codecs.get(args.codec, args.codec)
    if not proj.SetCurrentRenderFormatAndCodec(args.format, codec):
        print(f"FAIL: SetCurrentRenderFormatAndCodec({args.format!r}, {codec!r}); have {sorted(codecs)}")
        return 1
    settings = {"FormatWidth": 3840, "FormatHeight": 2160, "VideoQuality": args.bitrate_kbps,
                "EncodingProfile": "Main10", "ColorSpaceTag": args.color_space_tag,
                "GammaTag": args.gamma_tag, "ExportVideo": True, "ExportAudio": True}
    if not proj.SetRenderSettings(settings):
        print(f"FAIL: SetRenderSettings({settings})")
        return 1
    existing = proj.GetRenderPresetList() or []
    saved = proj.UpdateRenderPreset(args.name) if args.name in existing else proj.SaveAsNewRenderPreset(args.name)
    if not saved:
        print(f"FAIL: could not {'update' if args.name in existing else 'save'} preset {args.name!r}")
        return 1
    if not proj.LoadRenderPreset(args.name):
        print(f"FAIL: preset {args.name!r} saved but LoadRenderPreset returned False")
        return 1
    fc = proj.GetCurrentRenderFormatAndCodec()
    print(f"preset {args.name!r} {'updated' if args.name in existing else 'saved'}: {fc}  {settings}")
    print(f"presets now: {proj.GetRenderPresetList()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
