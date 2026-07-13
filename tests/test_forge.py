"""Scene Forge: offline tests (no network, no spend)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studio import forge as forgemod

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


tmp = Path(tempfile.mkdtemp(prefix="forge-test-"))

# -- cost SSOT ---------------------------------------------------------------
check("estimate qwen batch", abs(forgemod.estimate("qwen-fast", 8) - 0.0136) < 1e-9)
check("estimate flux2 batch", abs(forgemod.estimate("flux-2", 8) - 0.32) < 1e-9)
check("every model has cost+ref flag",
      all("cost" in m and "ref_images" in m for m in forgemod.MODELS.values()))

# -- batch numbering ----------------------------------------------------------
b1 = forgemod.next_batch_dir(tmp)
check("first batch is 01", b1.name == "batch-01")
b1.mkdir(parents=True)
(tmp / "forge" / "batch-07").mkdir()
check("numbering continues past gaps",
      forgemod.next_batch_dir(tmp).name == "batch-08")

# -- ref-image guard ----------------------------------------------------------
try:
    forgemod.generate_batch("x", 1, tmp / "x", model_key="qwen-fast",
                            ref_images=["/nonexistent.png"])
    check("ref on non-ref model rejected", False)
except forgemod.ForgeError:
    check("ref on non-ref model rejected", True)

# -- aspect mapping -----------------------------------------------------------
check("1920x1080 -> 16:9", forgemod._aspect(1920, 1080) == "16:9")
check("1080x1920 -> 9:16", forgemod._aspect(1080, 1920) == "9:16")
check("odd size falls back 16:9", forgemod._aspect(1234, 777) == "16:9")

# -- contact sheet (synthetic images) ------------------------------------------
from PIL import Image
batch = tmp / "forge" / "batch-01"
for i in range(1, 6):
    Image.new("RGB", (640, 360), (i * 40, 80, 120)).save(batch / f"{i:02d}.png")
sheet = forgemod.contact_sheet(batch, cols=3, thumb_w=200)
check("sheet written", sheet.is_file() and sheet.name == "sheet.jpg")
im = Image.open(sheet)
check("sheet is a 3x2 grid", im.width == 600 and im.height > 2 * 100)
# re-run must not tile the sheet into itself
sheet2 = forgemod.contact_sheet(batch, cols=3, thumb_w=200)
check("sheet excluded from re-tile", Image.open(sheet2).width == 600)

# -- video model SSOT ----------------------------------------------------------
check("video estimate hailuo ceiling",
      abs(forgemod.estimate_video("hailuo-fast") - 0.48) < 1e-9)
check("video models have fixed clip length",
      all("clip_s" in m and "cost_per_s" in m
          for m in forgemod.VIDEO_MODELS.values()))
check("unverified prices are flagged",
      all(m.get("estimated") for m in forgemod.VIDEO_MODELS.values()))
try:
    forgemod.animate(tmp / "no-such-still.png", "x", tmp / "motion")
    check("animate missing still rejected", False)
except forgemod.ForgeError:
    check("animate missing still rejected", True)

# -- picks --------------------------------------------------------------------
(batch / "manifest.json").write_text(
    json.dumps({"prompt": "p", "picks": []}), encoding="utf-8")
forgemod.record_picks(batch, [7, 2])
m = forgemod.record_picks(batch, [2, 11])
check("picks merged+sorted", m["picks"] == [2, 7, 11])

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
