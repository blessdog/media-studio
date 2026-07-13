"""Scene Forge: hosted genAI stills, cost-gated, curated by Ryan's eyes.

Blessed (Ryan, 2026-07-13): hosted APIs only (Replicate; model ids + costs
cribbed from bongpot's proven SSOT); PER-BATCH cost approval — nothing
spends without the printed estimate being approved first (lint-before-
spend); curation = contact sheet (one numbered grid image, opened in
Preview), winners named in chat. Stills-first economics: stills are ~100x
cheaper than video-seconds, so the funnel is wide here and narrow at
animation.

Every batch is recorded in the registry with full provenance
(model, prompt, cost) — the research called generation without provenance
unaccountable spend.
"""
import json
import os
import time
from pathlib import Path

# Model SSOT for THIS repo (ids + verified $/image from bongpot's config.js,
# 2026-07-13). ref_images = native multi-reference conditioning (the
# human-directed identity workflow — slice 3 rides this).
MODELS = {
    "qwen-fast": {"id": "prunaai/qwen-image-fast", "cost": 0.0017,
                  "ref_images": False,
                  "note": "cheap wide-funnel exploration"},
    "flux-2": {"id": "black-forest-labs/flux-2-dev", "cost": 0.04,
               "ref_images": True,
               "note": "strong prompt-following, legible text, "
                       "input_images identity conditioning"},
}
DEFAULT_MODEL = "qwen-fast"

# I2V models (slice 2). Pricing reality (2026-07-13): Replicate publishes
# NO fetchable per-model video prices; the only two on /pricing
# (wavespeedai/wan-2.1-i2v-*) have a DEAD backend (every prediction fails
# E002, data-URI and file-URL alike — do not re-add). So estimates carry an
# `estimated` flag: the gate prints a CEILING and Ryan approves that
# ceiling; real cost gets measured from the bill and the table corrected.
# wan-2.5-i2v-fast: duration input (default 5s), resolution 480p/720p/1080p,
# optional audio-sync input. fal.ai lists wan-2.5 at $0.05/s; ceiling 2x.
VIDEO_MODELS = {
    "hailuo-fast": {"id": "minimax/hailuo-2.3-fast", "cost_per_s": 0.08,
                    "estimated": True, "clip_s": 6.0,
                    "inputs": {"duration": 6, "resolution": "768p"},
                    "image_key": "first_frame_image",
                    "note": "default motion tier (768p 6s)"},
    "wan-fast": {"id": "wan-video/wan-2.5-i2v-fast", "cost_per_s": 0.10,
                 "estimated": True, "clip_s": 5.0,
                 "inputs": {"duration": 5, "resolution": "720p"},
                 "note": "BROKEN 2026-07-13: upstream E002 on every run "
                         "(shared wan backend; wavespeedai wan-2.1 same) — "
                         "retest before relying on it"},
}
DEFAULT_VIDEO_MODEL = "hailuo-fast"
BASE = "https://api.replicate.com/v1"


class ForgeError(RuntimeError):
    pass


def _token():
    tok = os.environ.get("REPLICATE_API_TOKEN")
    if not tok:
        env = Path(__file__).resolve().parent.parent / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("REPLICATE_API_TOKEN="):
                    tok = line.split("=", 1)[1].strip()
    if not tok:
        raise ForgeError("REPLICATE_API_TOKEN missing (repo .env)")
    return tok


def estimate(model_key, n):
    """Dollars for a batch, from the SSOT cost table."""
    return MODELS[model_key]["cost"] * n


def next_batch_dir(ws):
    forge = Path(ws) / "forge"
    forge.mkdir(parents=True, exist_ok=True)
    nums = [int(d.name.split("-")[1]) for d in forge.glob("batch-*")
            if d.is_dir() and d.name.split("-")[1].isdigit()]
    return forge / f"batch-{max(nums, default=0) + 1:02d}"


_VERSIONS = {}


def _version(session, model_id):
    """Latest version id for a model (community models require version-based
    predictions — the model-path endpoint 404s; bongpot-proven pattern)."""
    if model_id not in _VERSIONS:
        r = session.get(f"{BASE}/models/{model_id}", timeout=30)
        if not r.ok:
            raise ForgeError(f"{model_id}: HTTP {r.status_code} {r.text[:150]}")
        _VERSIONS[model_id] = r.json()["latest_version"]["id"]
    return _VERSIONS[model_id]


def _predict(session, model_id, inputs, timeout=300):
    """One Replicate prediction, sync-preferred then polled."""
    r = session.post(
        f"{BASE}/predictions",
        json={"version": _version(session, model_id), "input": inputs},
        headers={"Prefer": "wait=60"}, timeout=90)
    if r.status_code not in (200, 201, 202):
        raise ForgeError(f"{model_id}: HTTP {r.status_code} {r.text[:200]}")
    pred = r.json()
    t0 = time.time()
    while pred["status"] in ("starting", "processing"):
        if time.time() - t0 > timeout:
            raise ForgeError(f"{model_id}: prediction timeout ({timeout}s)")
        time.sleep(2)
        pred = session.get(f"{BASE}/predictions/{pred['id']}", timeout=30).json()
    if pred["status"] != "succeeded":
        raise ForgeError(f"{model_id}: {pred['status']} — "
                         f"{str(pred.get('error'))[:200]}")
    out = pred["output"]
    return out if isinstance(out, list) else [out]


def generate_batch(prompt, n, out_dir, model_key=DEFAULT_MODEL,
                   width=1920, height=1080, ref_images=None):
    """Generate n stills -> out_dir/01.png..NN.png + manifest.json.
    Returns (paths, manifest). ref_images only on models that support it."""
    import requests
    model = MODELS[model_key]
    if ref_images and not model["ref_images"]:
        raise ForgeError(f"{model_key} has no reference-image conditioning "
                         f"(use one of: "
                         f"{[k for k, m in MODELS.items() if m['ref_images']]})")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {_token()}"

    inputs = {"prompt": prompt, "aspect_ratio": _aspect(width, height)}
    if ref_images:
        inputs["input_images"] = [_image_input(session, p) for p in ref_images]

    paths = []
    for i in range(1, n + 1):
        inputs["seed"] = None  # let the provider vary; index varies the run
        urls = _predict(session, model["id"],
                        {k: v for k, v in inputs.items() if v is not None})
        img = session.get(urls[0], timeout=120)
        img.raise_for_status()
        ext = ".webp" if urls[0].endswith(".webp") else \
              ".jpg" if urls[0].endswith((".jpg", ".jpeg")) else ".png"
        p = out_dir / f"{i:02d}{ext}"
        p.write_bytes(img.content)
        paths.append(p)

    manifest = {
        "prompt": prompt, "model": model["id"], "modelKey": model_key,
        "count": n, "costUSD": round(estimate(model_key, n), 4),
        "refImages": [str(p) for p in (ref_images or [])],
        "picks": [],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    return paths, manifest


def _aspect(width, height):
    from fractions import Fraction
    f = Fraction(width, height)
    known = {(16, 9): "16:9", (9, 16): "9:16", (1, 1): "1:1",
             (4, 3): "4:3", (3, 4): "3:4", (21, 9): "21:9"}
    return known.get((f.numerator, f.denominator), "16:9")


def _data_uri(path):
    import base64
    p = Path(path)
    mime = {"png": "image/png", "webp": "image/webp"}.get(
        p.suffix.lstrip(".").lower(), "image/jpeg")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _image_input(session, path):
    """Image as prediction input. Replicate rejects data URIs over ~256KB
    (E002) — larger files go through the files API and pass as a URL."""
    p = Path(path)
    if p.stat().st_size <= 200_000:
        return _data_uri(p)
    with open(p, "rb") as f:
        r = session.post(f"{BASE}/files", files={"content": (p.name, f)},
                         timeout=120)
    if r.status_code not in (200, 201):
        raise ForgeError(f"file upload: HTTP {r.status_code} {r.text[:150]}")
    return r.json()["urls"]["get"]


def contact_sheet(batch_dir, cols=4, thumb_w=480):
    """Tile the batch into ONE numbered grid image -> <batch>/sheet.jpg.
    The curation surface: Ryan glances, answers with numbers."""
    from PIL import Image, ImageDraw
    batch_dir = Path(batch_dir)
    imgs = sorted(p for p in batch_dir.iterdir()
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
                  and p.stem != "sheet")
    if not imgs:
        raise ForgeError(f"no images in {batch_dir}")
    thumbs = []
    for p in imgs:
        im = Image.open(p).convert("RGB")
        h = int(im.height * thumb_w / im.width)
        thumbs.append((p.stem, im.resize((thumb_w, h))))
    rows = -(-len(thumbs) // cols)
    cell_h = max(t.height for _, t in thumbs) + 36
    sheet = Image.new("RGB", (cols * thumb_w, rows * cell_h), "#101010")
    draw = ImageDraw.Draw(sheet)
    for i, (label, t) in enumerate(thumbs):
        x, y = (i % cols) * thumb_w, (i // cols) * cell_h
        sheet.paste(t, (x, y))
        draw.text((x + 8, y + t.height + 8), label, fill="#f0f0f0")
    out = batch_dir / "sheet.jpg"
    sheet.save(out, quality=88)
    return out


def estimate_video(model_key):
    """Dollars per clip (fixed output length -> deterministic)."""
    m = VIDEO_MODELS[model_key]
    return m["cost_per_s"] * m["clip_s"]


def animate(still, prompt, out_dir, model_key=DEFAULT_VIDEO_MODEL):
    """Animate one still (I2V) -> <out_dir>/<stem>-mNN.mp4 + sidecar
    provenance json. The still is the initial frame; the prompt directs
    the MOTION (Ryan's per-moment creative call, never a default)."""
    import requests
    still = Path(still)
    if not still.is_file():
        raise ForgeError(f"still missing: {still}")
    model = VIDEO_MODELS[model_key]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 1 + sum(1 for _ in out_dir.glob(f"{still.stem}-m*.mp4"))
    out = out_dir / f"{still.stem}-m{n:02d}.mp4"

    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {_token()}"
    inputs = dict(model.get("inputs", {}))
    inputs[model.get("image_key", "image")] = _image_input(session, still)
    inputs["prompt"] = prompt
    urls = _predict(session, model["id"], inputs, timeout=900)
    clip = session.get(urls[0], timeout=300)
    clip.raise_for_status()
    out.write_bytes(clip.content)
    out.with_suffix(".json").write_text(json.dumps({
        "still": str(still), "prompt": prompt, "model": model["id"],
        "modelKey": model_key, "costUSD": round(estimate_video(model_key), 2),
    }, indent=1), encoding="utf-8")
    return out


def record_picks(batch_dir, picks):
    """Persist winner numbers into the batch manifest."""
    mpath = Path(batch_dir) / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    manifest["picks"] = sorted(set(manifest.get("picks", []) + list(picks)))
    mpath.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest
