"""File dragged/pasted media into a video workspace and register it.

The intake contract (blessed 2026-07-12): Ryan drags a file into the chat
(which hands the agent a disk path — nothing uploads anywhere); the agent
calls file_media() to copy it into the workspace's media/ folder and record
it in the registry. media/ is the video's one canonical bin.
"""
import filecmp
import mimetypes
import re
import shutil
from pathlib import Path

from . import registry


class IntakeError(ValueError):
    pass


def _kind(path):
    ctype = mimetypes.guess_type(str(path))[0] or ""
    for k in ("image", "video", "audio"):
        if ctype.startswith(k):
            return k
    raise IntakeError(f"unsupported media type {ctype or 'unknown'!r}: {path}")


def _safe_name(path):
    stem = re.sub(r"[^a-z0-9-]+", "-", path.stem.lower()).strip("-") or "media"
    return f"{stem}{path.suffix.lower()}"


def file_media(src, workspace, name=None):
    """Copy `src` into <workspace>/media/, register it. Returns the new Path."""
    src = Path(src).expanduser().resolve()
    if not src.is_file():
        raise IntakeError(f"no such file: {src}")
    kind = _kind(src)

    media_dir = Path(workspace) / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    dest = media_dir / (name or _safe_name(src))
    base = dest.stem
    n = 2
    while dest.exists() and not filecmp.cmp(src, dest, shallow=False):
        dest = dest.with_stem(f"{base}-{n}")   # name taken by different content
        n += 1
    if not dest.exists():
        shutil.copy2(src, dest)

    con = registry.connect()
    registry.record_asset(con, dest, kind=kind)
    return dest
