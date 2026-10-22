"""Turn one uploaded image into the files the buyer picked.

    python3 process_image.py input.jpg OUTPUT_DIR --format dark --format procreate

Formats: dark, light, palette, contour, palette_pdf, procreate.

MOCK: produces placeholder variations with Pillow so the pipeline can be
tested end to end. Replace the make_* functions with the real color-by-number
logic (see cbn/ in the repo root, which the Docker image copies to /app/cbn).

Contract with the Node server:
- write every output file into OUTPUT_DIR, plus OUTPUT_DIR/manifest.json:
  [{"file": "dark-numbered.pdf", "label": "...", "format": "dark"}, ...]
- print "PROGRESS <0-100> <message>" lines on stdout as work advances
- exit 0 on success; on failure exit non-zero with the reason on stderr
"""

import argparse
import colorsys
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

# Refuse decompression bombs: ~40 MP is plenty for a print and keeps RAM bounded.
Image.MAX_IMAGE_PIXELS = 40_000_000
# Largest side kept; JPEG draft mode decodes at reduced size, so huge photos
# never get fully expanded in memory.
MAX_SIDE = 3000
PALETTE_SIZE = 12

FORMATS = {
    "dark": "Dark Numbered Version",
    "light": "Light Numbered Version",
    "palette": "Palette Numbered Version",
    "contour": "Contour/Outline Version (Unnumbered)",
    "palette_pdf": "Digital + Printable Color Palette",
    "procreate": "Color Palette for Procreate",
}


def progress(pct: int, message: str) -> None:
    print(f"PROGRESS {pct} {message}", flush=True)


def load(path: Path) -> Image.Image:
    with Image.open(path) as img:
        img.draft("RGB", (MAX_SIDE, MAX_SIDE))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_SIDE, MAX_SIDE))
        return img.convert("RGB")


def extract_palette(img: Image.Image) -> list[tuple[int, int, int]]:
    small = img.copy()
    small.thumbnail((400, 400))
    quant = small.quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT)
    flat = quant.getpalette()[: PALETTE_SIZE * 3]
    return [tuple(flat[i : i + 3]) for i in range(0, len(flat), 3)]


def stamp(img: Image.Image, text: str) -> Image.Image:
    """Label mock output so nobody mistakes it for the real thing."""
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=max(16, img.width // 30))
    draw.rectangle((0, 0, img.width, font.size * 2), fill="white")
    draw.text((font.size // 2, font.size // 2), f"MOCK - {text}", fill="black", font=font)
    return img


def save_pdf_and_png(img: Image.Image, out_dir: Path, stem: str, key: str) -> list[dict]:
    img.save(out_dir / f"{stem}.png", optimize=True)
    img.save(out_dir / f"{stem}.pdf", "PDF", resolution=150)
    label = FORMATS[key]
    return [
        {"file": f"{stem}.pdf", "label": f"{label} (PDF)", "format": key},
        {"file": f"{stem}.png", "label": f"{label} (PNG)", "format": key},
    ]


def make_dark(img, palette, out_dir):
    out = ImageOps.posterize(ImageEnhance.Brightness(img).enhance(0.55), 3)
    return save_pdf_and_png(stamp(out, FORMATS["dark"]), out_dir, "dark-numbered", "dark")


def make_light(img, palette, out_dir):
    out = Image.blend(ImageOps.posterize(img, 3), Image.new("RGB", img.size, "white"), 0.65)
    return save_pdf_and_png(stamp(out, FORMATS["light"]), out_dir, "light-numbered", "light")


def make_palette_version(img, palette, out_dir):
    out = img.quantize(colors=PALETTE_SIZE, method=Image.Quantize.MEDIANCUT).convert("RGB")
    strip_h = max(40, img.height // 12)
    page = Image.new("RGB", (img.width, img.height + strip_h), "white")
    page.paste(out, (0, 0))
    draw = ImageDraw.Draw(page)
    w = img.width / len(palette)
    for i, rgb in enumerate(palette):
        draw.rectangle((i * w, img.height, (i + 1) * w, page.height), fill=rgb, outline="black")
    return save_pdf_and_png(stamp(page, FORMATS["palette"]), out_dir, "palette-numbered", "palette")


def make_contour(img, palette, out_dir):
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    out = ImageOps.invert(ImageOps.autocontrast(edges)).convert("RGB")
    return save_pdf_and_png(stamp(out, FORMATS["contour"]), out_dir, "contour-outline", "contour")


def make_palette_sheet(img, palette, out_dir):
    cols, cell, pad = 4, 260, 40
    rows = -(-len(palette) // cols)
    sheet = Image.new("RGB", (cols * cell + pad * 2, rows * (cell + 60) + pad * 2 + 60), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=24)
    for i, rgb in enumerate(palette):
        x = pad + (i % cols) * cell
        y = pad + 60 + (i // cols) * (cell + 60)
        draw.rectangle((x + 10, y, x + cell - 10, y + cell - 20), fill=rgb, outline="black")
        draw.text((x + 10, y + cell - 10), f"{i + 1}  #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}", fill="black", font=font)
    return save_pdf_and_png(stamp(sheet, FORMATS["palette_pdf"]), out_dir, "color-palette", "palette_pdf")


def make_procreate(img, palette, out_dir):
    # Procreate .swatches: a zip holding Swatches.json with HSB values in 0..1.
    swatches = []
    for r, g, b in palette:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        swatches.append({"hue": h, "saturation": s, "brightness": v, "alpha": 1, "colorSpace": 0})
    data = [{"name": "Color by Number", "swatches": swatches}]
    with zipfile.ZipFile(out_dir / "color-palette.swatches", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Swatches.json", json.dumps(data))
    return [{"file": "color-palette.swatches", "label": "Color Palette for Procreate (.swatches)", "format": "procreate"}]


MAKERS = {
    "dark": make_dark,
    "light": make_light,
    "palette": make_palette_version,
    "contour": make_contour,
    "palette_pdf": make_palette_sheet,
    "procreate": make_procreate,
}


def run(input_path: Path, out_dir: Path, formats: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    progress(5, "Reading your photo")
    img = load(input_path)
    progress(15, "Finding the color palette")
    palette = extract_palette(img)

    manifest = []
    for i, key in enumerate(formats):
        progress(15 + 80 * i // len(formats), f"Creating {FORMATS[key]}")
        manifest += MAKERS[key](img, palette, out_dir)

    (out_dir / "manifest.json").write_text(json.dumps(manifest))
    progress(100, "Done")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", type=Path)
    p.add_argument("output_dir", type=Path)
    p.add_argument("--format", dest="formats", action="append", choices=FORMATS, required=True)
    args = p.parse_args(argv)
    formats = list(dict.fromkeys(args.formats))  # dedupe, keep order
    try:
        run(args.input, args.output_dir, formats)
    except Exception as exc:  # report any failure to the Node side
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
