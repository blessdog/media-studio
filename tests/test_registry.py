#!/usr/bin/env python3
"""Registry v0 gates — runs against a throwaway db, never registry.db.

    .venv/bin/python tests/test_registry.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import ir as irmod
from studio import registry as regmod

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "golden-ir.json"

passed = 0


def check(label, cond):
    global passed
    if not cond:
        print(f"FAIL: {label}")
        sys.exit(1)
    passed += 1
    print(f"  ok: {label}")


with tempfile.TemporaryDirectory() as td:
    db = Path(td) / "test.db"
    con = regmod.connect(db)

    ir, base = irmod.load(FIXTURE)

    regmod.record_asset(con, base / "clip.mp4", kind="video",
                        probe={"fps": "30/1", "duration": 20.0})
    regmod.record_asset(con, base / "clip.mp4", kind="video")  # re-ingest
    rows = regmod.recent(con, "assets")
    check("asset upsert: re-ingest is one row", len(rows) == 1)
    check("asset upsert: probe survives sparse re-ingest",
          json.loads(rows[0]["probe"])["fps"] == "30/1")

    regmod.record_transcript(
        con, base / "clip.mp4",
        {"model": "nova-3",
         "utterances": [{"speaker": 0}, {"speaker": 0}, {"speaker": 1}]},
        base / "transcript.json")
    rows = regmod.recent(con, "transcripts")
    check("transcript recorded with counts",
          rows[0]["utterances"] == 3 and rows[0]["speakers"] == 2)

    regmod.record_ir(con, ir, FIXTURE)
    regmod.record_ir(con, ir, FIXTURE)  # recompile, same content
    rows = regmod.recent(con, "irs")
    check("ir upsert: same content hash is one row", len(rows) == 1)
    check("ir row carries identity hash",
          rows[0]["content_hash"] == irmod.content_hash(ir))

    regmod.record_render(con, ir, base / "out.mp4", verified=True)
    rows = regmod.recent(con, "renders")
    check("render recorded against ir hash",
          rows[0]["ir_hash"] == irmod.content_hash(ir) and rows[0]["verified"] == 1)

    regmod.record_decision(con, "test-topic", "test-decision", "ctx")
    check("decision recorded",
          regmod.recent(con, "decisions")[0]["decision"] == "test-decision")

    try:
        regmod.recent(con, "assets; DROP TABLE irs")
        check("recent() rejects unknown table", False)
    except ValueError:
        check("recent() rejects unknown table", True)

print(f"REGISTRY OK ({passed}/{passed})")
