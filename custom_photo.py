"""Custom photo order -> "mystery" color-by-number kit, ready to zip and send.

    python custom_photo.py photo.jpg --name "Buddy" --level standard
    python custom_photo.py photo.jpg --name "Buddy" --level all       # 16, 24 and 36 colors, to compare

Output (output/custom/<name>/<level>/):
    1_Color_This/        Letter, A4 and 16x20 PDFs (no picture preview anywhere), PNG pages for
                         Procreate/iPad, Procreate .swatches, palette sheet and hex codes
    2_REVEAL_Answer_Key/ the finished picture and the colored guides (would spoil the surprise)
    CHECK_original_vs_result.png   side-by-side for your quality review (not for the buyer)
plus <name>_<level>.zip of the two buyer folders.
"""

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from cbn import cli, pdf

LEVELS = {  # Etsy variation -> (cbn difficulty, colors)
    "relaxing": ("relaxing", 16),
    "standard": ("intermediate", 24),
    "detailed": ("expert", 36),
}
WORK_SIDE = 2400
SPOILERS = ("Shadow_Numbered", "Navigation_Map")   # PNG styles that show the colored picture


def load_photo(path):
    """Read a phone photo as BGR, honoring the EXIF rotation (cv2 ignores it)."""
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        rgb = np.asarray(im)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    f = WORK_SIDE / max(h, w)
    interp = cv2.INTER_AREA if f < 1 else cv2.INTER_CUBIC
    return cv2.resize(bgr, (round(w * f), round(h * f)), interpolation=interp), (w, h)


SPARKLE = Path(__file__).resolve().parent / "gemini_sparkle_alpha.npy"   # measured on a 2400x1792 Gemini image


def remove_gemini_mark(bgr):
    """Undo Gemini's white sparkle in the bottom-right corner (observed = (1-a)*original + a*255), then
    inpaint the faint edge it leaves. Template measured at 2400 px wide, centre 102 px from the corner."""
    h, w = bgr.shape[:2]
    alpha = np.load(SPARKLE)
    f = max(h, w) / 2400
    if abs(f - 1) > 0.01:
        n = round(alpha.shape[0] * f) | 1
        alpha = cv2.resize(alpha, (n, n), interpolation=cv2.INTER_AREA)
    r = alpha.shape[0] // 2
    cx, cy = w - round(102 * f), h - round(101 * f)
    img = bgr.astype(np.float32)
    reg = img[cy - r:cy + r + 1, cx - r:cx + r + 1]
    a = alpha[:, :, None]
    img[cy - r:cy + r + 1, cx - r:cx + r + 1] = (reg - 255 * a) / (1 - a)
    out = np.clip(img, 0, 255).astype(np.uint8)
    mask = np.zeros((h, w), np.uint8)
    mask[cy - r:cy + r + 1, cx - r:cx + r + 1] = ((alpha > 0.015) & (alpha < 0.25)).astype(np.uint8) * 255
    return cv2.inpaint(out, cv2.dilate(mask, np.ones((5, 5), np.uint8)), 5, cv2.INPAINT_TELEA)


def flat_cleanup(bgr):
    """For an image that is already a flat-color illustration (e.g. stylized with Gemini): just remove
    compression noise, no posterizing."""
    return cv2.medianBlur(cv2.bilateralFilter(bgr, 5, 20, 5), 3)


def enhance(bgr, strength=1.0):
    """Make a muddy phone photo paintable: lift contrast, then flatten noise, texture and
    soft gradients into clean patches while keeping edges sharp. (No white balance: on
    warm pet photos it pushed backgrounds blue.)"""
    # local contrast on lightness only
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    # a bit more saturation so the palette isn't all browns and grays
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.15, 0, 255)
    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    # mean shift does the posterizing; run it at half size (it is slow) and upsample
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    small = cv2.pyrMeanShiftFiltering(small, sp=round(8 * strength), sr=round(22 * strength), maxLevel=1)
    img = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    for _ in range(2):
        img = cv2.bilateralFilter(img, 9, 40 * strength, 9)
    return img


def build(photo_bgr, out_dir, name, level):
    difficulty, colors = LEVELS[level]
    with tempfile.TemporaryDirectory() as tmp:
        src, work = Path(tmp) / "in", Path(tmp) / "out"
        src.mkdir()
        cv2.imencode(".png", photo_bgr)[1].tofile(str(src / "page.png"))
        pdf.MYSTERY = True
        rc = cli.main(["-i", str(src), "-o", str(work), "--title", f"{name} Mystery Color by Number",
                       "--difficulty", difficulty, "-k", str(colors), "--details", "color",
                       "--package", "--work-size", str(WORK_SIDE), "--auto-rotate", "--no-blank-backs"])
        if rc != 0:
            return None
        if out_dir.exists():
            shutil.rmtree(out_dir)
        color, reveal = out_dir / "1_Color_This", out_dir / "2_REVEAL_Answer_Key"
        color.mkdir(parents=True)
        reveal.mkdir()
        sizes = {"letter": "US_Letter", "a4": "A4", "16x20": "Poster_16x20"}
        for pdf_file in work.glob("*.pdf"):
            size = pdf_file.stem.rsplit("_", 1)[1]
            shutil.copy(pdf_file, color / f"Color_by_Number_{sizes.get(size, size)}.pdf")
        pkg = work / "package"
        for f in [*pkg.glob("Procreate_Palette*.swatches"), pkg / "Color_Palette.png", pkg / "Hex_Codes.txt"]:
            shutil.copy(f, color / f.name)   # over 30 colors Procreate needs two .swatches files
        for png in (pkg / "Design_01" / "PNG").glob("*.png"):
            dest = reveal if png.stem in SPOILERS else color
            shutil.copy(png, dest / f"{png.stem}.png")
        shutil.copy(pkg / "Design_01" / "SVG" / "Light_Numbered.svg", color / "Light_Numbered.svg")
        shutil.copy(next((work / "previews").glob("*_colored.png")), reveal / "Finished_Picture.png")
        (color / "READ_ME_FIRST.txt").write_text(README.format(name=name), encoding="utf-8")
        report = (work / "report.txt").read_text(encoding="utf-8")
        (out_dir / "report.txt").write_text(report, encoding="utf-8")
    return report


def side_by_side(original, result_png, path):
    res = cv2.imdecode(np.fromfile(str(result_png), np.uint8), cv2.IMREAD_COLOR)
    h = 900
    a = cv2.resize(original, (round(original.shape[1] * h / original.shape[0]), h), interpolation=cv2.INTER_AREA)
    b = cv2.resize(res, (round(res.shape[1] * h / res.shape[0]), h), interpolation=cv2.INTER_AREA)
    cv2.imencode(".png", np.hstack([a, np.full((h, 20, 3), 255, np.uint8), b]))[1].tofile(str(path))


def zip_kit(out_dir, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out_dir.rglob("*")):
            if f.is_file() and f.parent != out_dir:   # buyer folders only
                z.write(f, f.relative_to(out_dir))


README = """Your mystery color-by-number: {name}

1. Open the 1_Color_This folder. Print the PDF in your paper size
   (US Letter, A4 or the 16x20 poster), or open a PNG in Procreate.
2. Paint each numbered area with the matching color from the key at
   the bottom of the page. Procreate users: import Procreate_Palette.swatches.
3. No peeking! The finished picture is in 2_REVEAL_Answer_Key.
   Open it only when you are done, or if you get stuck.
"""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("photo", type=Path)
    p.add_argument("--name", required=True, help="order name, e.g. the pet's name (used in titles and folders)")
    p.add_argument("--level", default="standard", choices=[*LEVELS, "all"])
    p.add_argument("--strength", type=float, default=1.0,
                   help="photo smoothing: lower keeps more texture, higher gives bigger, simpler areas")
    p.add_argument("--flat", action="store_true",
                   help="the photo is already a flat-color illustration (Gemini-stylized): skip posterizing")
    p.add_argument("--gemini-mark", action="store_true", help="paint out Gemini's sparkle in the bottom-right corner")
    p.add_argument("-o", "--output", type=Path, default=Path("output/custom"))
    a = p.parse_args()

    original, (w0, h0) = load_photo(a.photo)
    if max(w0, h0) < 1000:
        print(f"WARNING: photo is only {w0}x{h0}; ask the buyer for the original-size file")
    if a.gemini_mark:
        original = remove_gemini_mark(original)
    cleaned = flat_cleanup(original) if a.flat else enhance(original, a.strength)
    slug = cli.slugify(a.name)
    root = a.output / slug
    root.mkdir(parents=True, exist_ok=True)
    cv2.imencode(".png", cleaned)[1].tofile(str(root / "enhanced.png"))
    for level in (LEVELS if a.level == "all" else [a.level]):
        out_dir = root / level
        report = build(cleaned, out_dir, a.name, level)
        if report is None:
            print(f"{level}: FAILED")
            continue
        side_by_side(original, out_dir / "2_REVEAL_Answer_Key" / "Finished_Picture.png",
                     out_dir / "CHECK_original_vs_result.png")
        zip_kit(out_dir, root / f"{slug}_{level}.zip")
        print(f"{level}: " + " | ".join(l.strip() for l in report.splitlines()[:6] if "regions" in l or "FLAG" in l))
    print(f"Done: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
