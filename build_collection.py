"""One color-by-number design per image, each with its own palette, for an Etsy bundle.

    python build_collection.py -i input -o output/collection --difficulty expert
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

from cbn import cli

# Gemini overlays a translucent white sparkle bottom-right: image size -> (distance of its center from the
# corner, scale of the 1792x2400 template, opacity relative to the template).
SPARKLES = {(1792, 2400): (112, 1.0, 1.0), (2048, 2048): (112, 1.0, 1.0), (896, 1200): (119, 0.49, 0.4)}
MIN_SIDE = 1500               # below this the long side is upscaled
_TEMPLATE = {}


def _read(path):
    return cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)


def sparkle_alpha(files):
    """Opacity map (0..1, 129x129 centered on the star) measured on the image whose corner is flattest."""
    if "alpha" in _TEMPLATE:
        return _TEMPLATE["alpha"]
    best = None
    for f in files:
        img = _read(f)
        h, w = img.shape[:2]
        if (w, h) != (1792, 2400):
            continue
        cx, cy = w - 112, h - 112
        box = img[cy - 90:cy + 90, cx - 90:cx + 90].astype(np.float32)
        yy, xx = np.mgrid[-90:90, -90:90]
        ring = (np.hypot(xx, yy) > 62)
        spread = float(box[ring].std(axis=0).mean())
        dark = float(box[ring].mean()) < 90
        if dark and (best is None or spread < best[0]):
            best = (spread, f)
    img = _read(best[1]).astype(np.float32)
    h, w = img.shape[:2]
    cx, cy = w - 112, h - 112
    box = img[cy - 64:cy + 65, cx - 64:cx + 65]
    yy, xx = np.mgrid[-64:65, -64:65]
    ring = (np.hypot(xx, yy) > 56)
    bg = np.median(box[ring], axis=0)
    alpha = np.clip(((box - bg) / (255 - bg)).mean(axis=2), 0, 1)
    alpha[np.hypot(xx, yy) > 60] = 0
    _TEMPLATE["raw"] = alpha.copy()
    alpha = _shape_alpha(alpha)
    _TEMPLATE["alpha"] = alpha
    return alpha


def _shape_alpha(alpha, thr=0.04, blur=0.6, grow=1.0):
    """Clean the measured opacity: drop noise, soften the edge slightly."""
    alpha = np.where(alpha < thr, 0, alpha) ** grow if grow != 1.0 else np.where(alpha < thr, 0, alpha)
    return cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), blur) if blur else alpha.astype(np.float32)


def remove_sparkle(img, alpha, inset, scale, gain=1.0):
    """Undo the white overlay: observed = (1 - a) * original + a * 255."""
    h, w = img.shape[:2]
    if isinstance(inset, tuple):
        ix, iy = inset
    else:
        ix = iy = inset
    if scale != 1.0:
        n = round(alpha.shape[0] * scale) | 1
        alpha = cv2.resize(alpha, (n, n), interpolation=cv2.INTER_AREA)
    r = alpha.shape[0] // 2
    cx, cy = w - ix, h - iy
    region = img[cy - r:cy + r + 1, cx - r:cx + r + 1].astype(np.float32)
    a = np.clip(alpha * gain, 0, 0.9)[:, :, None]
    fixed = (region - 255 * a) / (1 - a)
    img[cy - r:cy + r + 1, cx - r:cx + r + 1] = np.clip(fixed, 0, 255).astype(np.uint8)
    return img


def clean_image(path, files=None, sparkle=True):
    """Load, remove the Gemini sparkle (unless sparkle=False), and upscale small images. Returns (bgr, notes)."""
    img = _read(path)
    notes = []
    h, w = img.shape[:2]
    if not sparkle:
        pass
    elif (w, h) in SPARKLES:
        alpha = sparkle_alpha(files or cli.find_images(path.parent))
        inset, scale, gain = SPARKLES[(w, h)]
        img = remove_sparkle(img, alpha, inset, scale, gain)
    else:
        notes.append(f"size {w}x{h}: unknown size, check the bottom-right corner for a sparkle mark")
    if max(h, w) < MIN_SIDE:
        f = MIN_SIDE / max(h, w)
        img = cv2.resize(img, (round(w * f), round(h * f)), interpolation=cv2.INTER_CUBIC)
        notes.append(f"low resolution {w}x{h}, upscaled x{f:.1f}")
    return img, notes


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path)
    p.add_argument("--difficulty", default="expert", choices=list(cli.DIFFICULTIES))
    p.add_argument("-k", "--colors", type=int, default=24,
                   help="K-Means colors; detail colors added on top keep each design at 30 or fewer")
    p.add_argument("--sizes", default="16x20", help="page size whose detail level is used (finer = smaller numbered regions)")
    p.add_argument("--merge-delta", type=float, default=8.0)
    p.add_argument("--min-area", type=float, help="smallest region in mm^2 (default: from difficulty)")
    p.add_argument("--residual-delta", type=float, default=15.0)
    p.add_argument("--min-radius", type=float, help="thinnest region kept, in points (default: from difficulty)")
    p.add_argument("--details", default="color", choices=["outline", "color", "off"])
    p.add_argument("--only", type=int, nargs="*", help="design numbers to build (default: all)")
    p.add_argument("--no-sparkle", action="store_true", help="images have no Gemini sparkle mark: skip its removal")
    a = p.parse_args()

    images = cli.find_images(a.input)
    a.output.mkdir(parents=True, exist_ok=True)
    summary = []
    for n, path in enumerate(images, 1):
        if a.only and n not in a.only:
            continue
        img, notes = clean_image(path, sparkle=not a.no_sparkle)
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / "in", Path(tmp) / "out"
            src.mkdir()
            ok, buf = cv2.imencode(".png", img)
            buf.tofile(str(src / f"design_{n:02d}.png"))
            rc = cli.main(["-i", str(src), "-o", str(out), "--difficulty", a.difficulty, "-k", str(a.colors),
                           "--sizes", a.sizes, "--title", f"Design {n:02d}", "--package", "--work-size", "2400", "--details", a.details,
                           "--merge-delta", str(a.merge_delta),
                           "--residual-delta", str(a.residual_delta)] + (["--min-area", str(a.min_area)] if a.min_area else [])
                           + (["--min-radius", str(a.min_radius)] if a.min_radius else []))
            if rc != 0 or not (out / "package").exists():
                summary.append(f"Design_{n:02d} ({path.name}): FAILED")
                continue
            dest = a.output / f"Design_{n:02d}"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(out / "package" / "Design_01", dest)
            for f in (out / "package").iterdir():
                if f.is_file():
                    shutil.copy(f, dest / f.name)
            shutil.copy(out / "report.txt", dest / "report.txt")
            shutil.copy(out / "previews" / f"design_{n:02d}_{a.sizes}_colored.png", dest / "preview_colored.png")
        summary.append(f"Design_{n:02d} ({path.name}): built" + (" | " + "; ".join(notes) if notes else ""))
    (a.output / "build_summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    sys.exit(main())
