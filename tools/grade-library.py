#!/usr/bin/env python3
"""grade-library — fetch, install and verify the third-party grade assets
listed in grades/film-look/manifest.json (the SSOT for provenance).

  fetch    download every URL asset into grades/film-look/assets/, check sha256
  install  copy (and unzip) the assets into Resolve's LUT folder, film-look/
  verify   sha256 of the repo copies and the installed copies, human assets
  validate ask a RUNNING Resolve to compile every installed DCTL (ValidateDCTL)

Stdlib only. Nonzero exit = something is missing or does not match.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MANIFEST = os.path.join(ROOT, "grades", "film-look", "manifest.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/128 Safari/537.36"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(manifest_path):
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def save(manifest_path, m):
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
        f.write("\n")


def asset_path(m, a):
    return os.path.join(ROOT, m["assets_dir"], a["dest"])


def install_root(m, lut_root):
    return os.path.join(lut_root or m["lut_root"], m["install_dir"])


def fetchable(a):
    return a.get("kind") not in ("human", "reference") and a.get("url")


def cmd_fetch(m, manifest_path, record):
    bad = 0
    for a in m["assets"]:
        if not fetchable(a):
            continue
        dst = asset_path(m, a)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            req = urllib.request.Request(a["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f:
                shutil.copyfileobj(r, f)
            print(f"fetched   {a['id']}  ({os.path.getsize(dst)} bytes)")
        got = sha256(dst)
        want = a.get("sha256")
        if want is None:
            if record:
                a["sha256"] = got
                print(f"recorded  {a['id']}  {got}")
            else:
                print(f"UNPINNED  {a['id']}  {got}  (run with --record to pin)")
                bad += 1
        elif got != want:
            print(f"MISMATCH  {a['id']}\n  want {want}\n  got  {got}")
            bad += 1
        else:
            print(f"ok        {a['id']}")
        if a.get("kind") == "zip" and record and not a.get("contents"):
            with zipfile.ZipFile(dst) as z:
                a["contents"] = [n for n in z.namelist() if _is_lut(n)]
    if record:
        save(manifest_path, m)
    return bad


def _is_lut(name):
    base = os.path.basename(name)
    return (not base.startswith("._")) and base.lower().endswith((".cube", ".dctl"))


def _installed_files(m, a, lut_root):
    """(source_in_repo_or_zipmember, installed_path) pairs for one asset."""
    dst_dir = os.path.join(install_root(m, lut_root), a["install"])
    src = asset_path(m, a)
    if a.get("kind") == "zip":
        return [(n, os.path.join(dst_dir, os.path.basename(n))) for n in a.get("contents", [])]
    return [(src, os.path.join(dst_dir, os.path.basename(a["dest"])))]


def cmd_install(m, lut_root):
    bad = 0
    for a in m["assets"]:
        if not fetchable(a) or not a.get("install"):
            continue
        src = asset_path(m, a)
        if not os.path.exists(src):
            print(f"MISSING   {a['id']}  run fetch first")
            bad += 1
            continue
        dst_dir = os.path.join(install_root(m, lut_root), a["install"])
        os.makedirs(dst_dir, exist_ok=True)
        if a.get("kind") == "zip":
            with zipfile.ZipFile(src) as z:
                for member in a.get("contents", []):
                    out = os.path.join(dst_dir, os.path.basename(member))
                    with z.open(member) as r, open(out, "wb") as f:
                        shutil.copyfileobj(r, f)
                    print(f"installed {out}")
        else:
            out = os.path.join(dst_dir, os.path.basename(a["dest"]))
            shutil.copyfile(src, out)
            print(f"installed {out}")
    human = [a for a in m["assets"] if a.get("kind") == "human"]
    for a in human:
        src_dir = asset_path(m, a)
        files = [f for f in os.listdir(src_dir)] if os.path.isdir(src_dir) else []
        files = [f for f in files if _is_lut(f)]
        if files:
            dst_dir = os.path.join(install_root(m, lut_root), a["install"])
            os.makedirs(dst_dir, exist_ok=True)
            for f in files:
                shutil.copyfile(os.path.join(src_dir, f), os.path.join(dst_dir, f))
                print(f"installed {os.path.join(dst_dir, f)}")
        else:
            print(f"HUMAN     {a['id']}  download from {a['url']} into {src_dir}")
    print("Resolve sees new files after LUT browser > Update Lists, or a restart.")
    return bad


def cmd_verify(m, lut_root):
    bad = 0
    for a in m["assets"]:
        if a.get("kind") == "reference":
            ok = os.path.exists(a["path"])
            print(f"{'ok       ' if ok else 'MISSING  '} {a['id']}  {a['path']}")
            bad += 0 if ok else 1
            continue
        if a.get("kind") == "human":
            src_dir = asset_path(m, a)
            files = [f for f in os.listdir(src_dir) if _is_lut(f)] if os.path.isdir(src_dir) else []
            print(f"{'ok       ' if files else 'HUMAN    '} {a['id']}  {len(files)} file(s) in {src_dir}")
            continue
        src = asset_path(m, a)
        if not os.path.exists(src):
            print(f"MISSING   {a['id']}  {src}")
            bad += 1
            continue
        got = sha256(src)
        if got != a.get("sha256"):
            print(f"MISMATCH  {a['id']}  repo copy differs from manifest")
            bad += 1
            continue
        if not a.get("install"):
            print(f"ok        {a['id']}")
            continue
        for member, installed in _installed_files(m, a, lut_root):
            if not os.path.exists(installed):
                print(f"NOT-INST  {a['id']}  {installed}")
                bad += 1
                continue
            if a.get("kind") == "zip":
                with zipfile.ZipFile(src) as z:
                    want = hashlib.sha256(z.read(member)).hexdigest()
            else:
                want = got
            if sha256(installed) != want:
                print(f"DRIFT     {a['id']}  installed copy differs: {installed}")
                bad += 1
            else:
                print(f"ok        {a['id']}  {installed}")
    return bad


def cmd_validate(m, lut_root):
    sys.path.insert(0, ROOT)
    from studio.resolve import connect, ResolveUnavailable  # noqa: E402

    try:
        app = connect()
    except ResolveUnavailable as e:
        print(f"RESOLVE   {e}")
        return 1
    if app.GetCurrentPage() is None:
        print("RESOLVE   a modal dialog has the UI; results would be void (AGENTS.md doctrine)")
        return 1
    if not hasattr(app, "ValidateDCTL"):
        print("RESOLVE   this build's API has no ValidateDCTL (21.1 changelog lists it); "
              "fall back to LUT browser > Update Lists and apply each DCTL to a node by hand")
        return 1
    bad = 0
    for a in m["assets"]:
        if a.get("kind") != "dctl" or not a.get("install"):
            continue
        for _, installed in _installed_files(m, a, lut_root):
            res = app.ValidateDCTL(installed)
            ok = bool(res) if not isinstance(res, dict) else not res.get("error")
            print(f"{'compiles ' if ok else 'FAILS    '} {a['id']}  {installed}  -> {res!r}")
            bad += 0 if ok else 1
    return bad


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["fetch", "install", "verify", "validate"])
    p.add_argument("--manifest", default=DEFAULT_MANIFEST, help="manifest path (default grades/film-look/manifest.json)")
    p.add_argument("--record", action="store_true", help="fetch: pin sha256/contents of unpinned assets into the manifest")
    p.add_argument("--lut-root", default=None, help="override Resolve's LUT folder (default from the manifest)")
    args = p.parse_args()
    m = load(args.manifest)
    if args.command == "fetch":
        bad = cmd_fetch(m, args.manifest, args.record)
    elif args.command == "install":
        bad = cmd_install(m, args.lut_root)
    elif args.command == "verify":
        bad = cmd_verify(m, args.lut_root)
    else:
        bad = cmd_validate(m, args.lut_root)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
