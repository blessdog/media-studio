"""Registry v0 — the pipeline's cross-session memory (SQLite, this repo only;
scope blessed by Ryan 2026-07-12).

Every tool writes through here: what assets were seen, what transcripts and
IRs were produced, what got rendered and verified, and what Ryan decided.
Rows are append-mostly facts, not state — the artifacts on disk stay the
source of truth; the registry is the index that survives sessions.

    from studio import registry
    con = registry.connect()          # repo-root registry.db (gitignored)
    registry.record_ir(con, ir, ir_path)

Inspect from the shell:

    .venv/bin/python -m studio.registry            # recent rows, all tables
    .venv/bin/python -m studio.registry decisions  # one table
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "registry.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    sha256 TEXT,
    kind TEXT NOT NULL,
    probe TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY,
    asset_path TEXT NOT NULL,
    model TEXT NOT NULL,
    path TEXT NOT NULL,
    utterances INTEGER,
    speakers INTEGER,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS irs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL,
    fps TEXT NOT NULL,
    edits INTEGER NOT NULL,
    extent_frames INTEGER NOT NULL,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS renders (
    id INTEGER PRIMARY KEY,
    ir_hash TEXT NOT NULL,
    timeline TEXT NOT NULL,
    path TEXT NOT NULL,
    verified INTEGER NOT NULL,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY,
    topic TEXT NOT NULL,
    decision TEXT NOT NULL,
    context TEXT,
    created TEXT NOT NULL
);
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path=None):
    con = sqlite3.connect(db_path or DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    return con


def record_asset(con, path, kind, sha256=None, probe=None):
    """Upsert by absolute path; refreshes last_seen on re-ingest."""
    path = str(Path(path).resolve())
    now = _now()
    con.execute(
        "INSERT INTO assets (path, sha256, kind, probe, first_seen, last_seen)"
        " VALUES (?,?,?,?,?,?)"
        " ON CONFLICT(path) DO UPDATE SET"
        "  sha256=COALESCE(excluded.sha256, sha256),"
        "  probe=COALESCE(excluded.probe, probe),"
        "  last_seen=excluded.last_seen",
        (path, sha256, kind, json.dumps(probe) if probe else None, now, now))
    con.commit()


def record_transcript(con, asset_path, transcript, transcript_path):
    speakers = len({u["speaker"] for u in transcript["utterances"]})
    con.execute(
        "INSERT INTO transcripts (asset_path, model, path, utterances, speakers, created)"
        " VALUES (?,?,?,?,?,?)",
        (str(Path(asset_path).resolve()), transcript["model"],
         str(Path(transcript_path).resolve()),
         len(transcript["utterances"]), speakers, _now()))
    con.commit()


def record_ir(con, ir, ir_path):
    """Upsert by content hash — recompiling the same IR is one fact, not two."""
    from . import ir as irmod
    con.execute(
        "INSERT INTO irs (name, content_hash, path, fps, edits, extent_frames, created)"
        " VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(content_hash) DO UPDATE SET path=excluded.path",
        (ir["name"], irmod.content_hash(ir), str(Path(ir_path).resolve()),
         ir["timebase"]["fps"], len(ir["edits"]), irmod.extent_frames(ir), _now()))
    con.commit()


def record_render(con, ir, out_path, verified):
    from . import ir as irmod
    con.execute(
        "INSERT INTO renders (ir_hash, timeline, path, verified, created)"
        " VALUES (?,?,?,?,?)",
        (irmod.content_hash(ir), irmod.timeline_name(ir),
         str(Path(out_path).resolve()), int(bool(verified)), _now()))
    con.commit()


def record_decision(con, topic, decision, context=None):
    con.execute(
        "INSERT INTO decisions (topic, decision, context, created) VALUES (?,?,?,?)",
        (topic, decision, context, _now()))
    con.commit()


def recent(con, table, limit=10):
    if table not in ("assets", "transcripts", "irs", "renders", "decisions"):
        raise ValueError(f"unknown table {table!r}")
    rows = con.execute(
        f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def _main(argv):
    tables = argv[1:] or ["assets", "transcripts", "irs", "renders", "decisions"]
    con = connect()
    for t in tables:
        rows = recent(con, t)
        print(f"== {t} ({len(rows)} recent) ==")
        for r in rows:
            print("  " + json.dumps(r, default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv))
