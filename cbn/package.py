"""Etsy-style download package: PNG/PDF/SVG styles, Procreate .swatches and palette sheets."""

import colorsys
import io
import json
import zipfile
from pathlib import Path

import cv2
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

from .preview import save_png

PNG_W, PNG_H = 4961, 7016          # A4 at 600 DPI
PAGE_MARGIN = 0.05                 # fraction of the width kept clear at the sides
STRIP_H = 520                      # palette strip height in the "palette" style
DARK = dict(line=(40, 40, 40), number=(30, 30, 30))
LIGHT = dict(line=(185, 185, 185), number=(150, 150, 150))
# Light gray that stays readable on paper but vanishes under paint.
PRINT_LIGHT = dict(line=(175, 175, 175), number=(140, 140, 140))
PALETTE_LOOK = DARK                # look of the "palette" style (the printable book page)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def _luma(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _reference(page, palette, lut):
    """Full-size quantized color image, including the pre-colored details."""
    ref = palette[lut[page.labels]]
    mask = page.detail_map >= 0
    ref[mask] = palette[lut[page.detail_map[mask]]]
    return ref


def _fit_scale(page, strip=0):
    avail_w = PNG_W * (1 - 2 * PAGE_MARGIN)
    avail_h = PNG_H * (1 - 2 * PAGE_MARGIN) - strip
    scale = min(avail_w / page.width, avail_h / page.height)
    x0 = round((PNG_W - page.width * scale) / 2)
    y0 = round((PNG_H - strip - page.height * scale) / 2)
    return scale, x0, y0


def _draw_art(canvas, page, scale, x0, y0, line, number, numbers=True, fill_details=False):
    """Draw outlines, details and numbers of one page onto canvas at (x0, y0)."""
    thick = max(2, round(scale * 1.2))

    def pts(a):
        return np.round((a * scale + [x0, y0]) * 16).astype(np.int32)

    cv2.polylines(canvas, [pts(o) for o in page.outlines], False, line, thick, cv2.LINE_AA, shift=4)
    for rgb, polys in page.details:
        if fill_details and page.detail_style == "color":
            cv2.fillPoly(canvas, [pts(p) for p in polys], tuple(int(v) for v in rgb), cv2.LINE_AA, shift=4)
        cv2.polylines(canvas, [pts(p) for p in polys], True, line, max(1, thick - 1), cv2.LINE_AA, shift=4)
    if not numbers:
        return
    for m in page.markers:
        text = str(m.color + 1)
        fs = float(np.clip(m.radius / (14 if len(text) > 1 else 10), 0.25, 0.9)) * scale
        (tw, th), _ = cv2.getTextSize(text, FONT, fs, max(1, round(scale * 0.9)))
        org = (round(m.x * scale + x0 - tw / 2), round(m.y * scale + y0 + th / 2))
        cv2.putText(canvas, text, org, FONT, fs, number, max(1, round(scale * 0.9)), cv2.LINE_AA)


def _palette_strip(canvas, palette, y, number_color=(60, 60, 60)):
    n = len(palette)
    per_row = (n + 1) // 2 if n > 15 else n
    cell = (PNG_W * 0.9) / per_row
    r = int(min(cell * 0.38, 90))
    for i, rgb in enumerate(palette):
        row, col = divmod(i, per_row)
        cx = int(PNG_W * 0.05 + cell * (col + 0.5))
        cy = int(y + 140 + row * 230)
        cv2.circle(canvas, (cx, cy), r, tuple(int(v) for v in rgb), -1, cv2.LINE_AA)
        cv2.circle(canvas, (cx, cy), r, (120, 120, 120), 3, cv2.LINE_AA)
        text = str(i + 1)
        (tw, th), _ = cv2.getTextSize(text, FONT, 2.4, 5)
        ink = (255, 255, 255) if _luma(rgb) < 140 else (30, 30, 30)
        cv2.putText(canvas, text, (cx - tw // 2, cy + th // 2), FONT, 2.4, ink, 5, cv2.LINE_AA)


def render_style(page, palette, lut, style):
    canvas = np.full((PNG_H, PNG_W, 3), 255, np.uint8)
    strip = STRIP_H if style == "palette" else 0
    scale, x0, y0 = _fit_scale(page, strip)
    h, w = round(page.height * scale), round(page.width * scale)
    if style in ("shadow", "navigation"):
        ref = cv2.resize(_reference(page, palette, lut), (w, h), interpolation=cv2.INTER_NEAREST)
        if style == "shadow":
            ref = (ref * 0.38 + 255 * 0.62).astype(np.uint8)
        canvas[y0:y0 + h, x0:x0 + w] = ref
    if style == "navigation":
        _draw_art(canvas, page, scale, x0, y0, (30, 30, 30), (20, 20, 20), numbers=False)
        # numbers in contrast ink, since the regions are colored
        for m in page.markers:
            rgb = palette[lut[m.color]] if False else palette[m.color]
            text = str(m.color + 1)
            fs = float(np.clip(m.radius / (14 if len(text) > 1 else 10), 0.25, 0.9)) * scale
            (tw, th), _ = cv2.getTextSize(text, FONT, fs, max(1, round(scale * 0.9)))
            ink = (255, 255, 255) if _luma(rgb) < 120 else (20, 20, 20)
            cv2.putText(canvas, text, (round(m.x * scale + x0 - tw / 2), round(m.y * scale + y0 + th / 2)),
                        FONT, fs, ink, max(1, round(scale * 0.9)), cv2.LINE_AA)
    else:
        look = LIGHT if style == "light" else PALETTE_LOOK if style == "palette" else DARK
        _draw_art(canvas, page, scale, x0, y0, look["line"], look["number"], numbers=style != "contour",
                  fill_details=style != "contour")
    if style == "palette":
        _palette_strip(canvas, palette, PNG_H - STRIP_H - 40)
    return canvas


def render_svg(page, palette, look):
    w, h = page.width, page.height
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           f'<g fill="none" stroke="rgb{look["line"]}" stroke-width="1.2" stroke-linejoin="round">']
    for o in page.outlines:
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in o)
        out.append(f'<path d="{d}"/>')
    for _, polys in page.details:
        for p in polys:
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in p) + "Z"
            out.append(f'<path d="{d}"/>')
    out.append(f'</g><g fill="rgb{look["number"]}" font-family="Helvetica, Arial, sans-serif" text-anchor="middle">')
    for m in page.markers:
        text = str(m.color + 1)
        size = float(np.clip(m.radius * 1.1 / (1.4 if len(text) > 1 else 1.0), 6, 22))
        out.append(f'<text x="{m.x:.1f}" y="{m.y + size * 0.35:.1f}" font-size="{size:.1f}">{text}</text>')
    out.append("</g></svg>")
    return "\n".join(out)


def swatches_file(path, palette, name):
    """Procreate palette: a zip holding Swatches.json (30 slots, HSB colors).

    Palettes over 30 colors are split into numbered files; returns the written paths.
    """
    chunks = [palette[i:i + 30] for i in range(0, len(palette), 30)] or [palette]
    paths = []
    for part, chunk in enumerate(chunks, 1):
        items = []
        for r, g, b in chunk:
            hue, sat, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            items.append({"hue": hue, "saturation": sat, "brightness": val, "alpha": 1,
                          "origin": 2, "colorSpace": 0, "colorProfile": "", "timestamp": 0})
        items += [None] * (30 - len(items))
        label = name if len(chunks) == 1 else f"{name} ({part}-{len(chunks)}: colors {part * 30 - 29}+)"
        out = path if len(chunks) == 1 else path.with_name(f"{path.stem}_{part}{path.suffix}")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Swatches.json", json.dumps({"name": label, "swatches": items}))
        paths.append(out)
    return paths


def palette_sheet(palette):
    n = len(palette)
    per_row = 10
    rows = -(-n // per_row)
    cell, pad = 260, 60
    img = np.full((rows * 340 + pad * 2 + 120, per_row * cell + pad * 2, 3), 255, np.uint8)
    cv2.putText(img, "COLOR PALETTE", (pad, pad + 40), FONT, 1.6, (60, 60, 60), 3, cv2.LINE_AA)
    for i, rgb in enumerate(palette):
        row, col = divmod(i, per_row)
        cx, cy = pad + col * cell + cell // 2, pad + 160 + row * 340
        cv2.circle(img, (cx, cy), 95, tuple(int(v) for v in rgb), -1, cv2.LINE_AA)
        cv2.circle(img, (cx, cy), 95, (120, 120, 120), 3, cv2.LINE_AA)
        t = str(i + 1)
        (tw, th), _ = cv2.getTextSize(t, FONT, 2.2, 5)
        cv2.putText(img, t, (cx - tw // 2, cy + th // 2), FONT, 2.2,
                    (255, 255, 255) if _luma(rgb) < 140 else (30, 30, 30), 5, cv2.LINE_AA)
        hx = "#%02X%02X%02X" % tuple(rgb)
        (tw, th), _ = cv2.getTextSize(hx, FONT, 0.9, 2)
        cv2.putText(img, hx, (cx - tw // 2, cy + 160), FONT, 0.9, (70, 70, 70), 2, cv2.LINE_AA)
    return img


def palette_svg(palette):
    per_row, cell = 10, 130
    rows = -(-len(palette) // per_row)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {per_row * cell + 60} {rows * 170 + 100}" '
           f'font-family="Helvetica, Arial, sans-serif" text-anchor="middle">',
           '<rect width="100%" height="100%" fill="#fff"/>',
           '<text x="30" y="40" font-size="26" text-anchor="start" fill="#444">COLOR PALETTE</text>']
    for i, (r, g, b) in enumerate(palette):
        row, col = divmod(i, per_row)
        cx, cy = 30 + col * cell + cell / 2, 100 + row * 170
        ink = "#fff" if _luma((r, g, b)) < 140 else "#1e1e1e"
        out.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="rgb({r},{g},{b})" stroke="#777" stroke-width="1.5"/>')
        out.append(f'<text x="{cx}" y="{cy + 10}" font-size="28" fill="{ink}">{i + 1}</text>')
        out.append(f'<text x="{cx}" y="{cy + 78}" font-size="15" fill="#444">#{r:02X}{g:02X}{b:02X}</text>')
    out.append("</svg>")
    return "\n".join(out)


def _style_pdf(path, images):
    """A4 PDF with one page per rendered style (300 DPI)."""
    c = rl_canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    pw, ph = A4
    for img in images:
        small = cv2.resize(img, (2480, 3508), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".png", cv2.cvtColor(small, cv2.COLOR_RGB2BGR))
        c.drawImage(ImageReader(io.BytesIO(buf.tobytes())), 0, 0, pw, ph)
        c.showPage()
    c.save()


def verify_page(page, lut):
    """Return a list of problems: numbers sitting on the wrong color, regions left without a number."""
    from .regions import region_map
    problems = []
    h, w = page.labels.shape
    ids, _ = region_map(page.labels.astype(np.int32))
    numbered = set()
    for m in page.markers:
        x, y = int(round(m.x)), int(round(m.y))
        if not (0 <= x < w and 0 <= y < h):
            problems.append(f"number {m.color + 1} at ({x},{y}) is outside the image")
            continue
        if lut[page.labels[y, x]] != m.color:
            problems.append(f"number {m.color + 1} at ({x},{y}) sits on color {lut[page.labels[y, x]] + 1}")
        numbered.add(int(ids[y, x]))
    missing = set(np.unique(ids)) - numbered - {0}
    if missing:
        problems.append(f"{len(missing)} region(s) have no number")
    return problems


def build_package(root, pages, palette, old_palette, title):
    """Write the sellable download folder. pages are the A4 BookPages after palette pruning."""
    root.mkdir(parents=True, exist_ok=True)
    # map each pre-pruning palette index to its post-pruning index
    lut = np.zeros(len(old_palette), np.int32)
    for i, row in enumerate(old_palette):
        hits = np.where((palette == row).all(axis=1))[0]
        lut[i] = hits[0] if len(hits) else 0
    palette = np.asarray(palette)

    swatches_file(root / "Procreate_Palette.swatches", palette, title)
    save_png(root / "Color_Palette.png", palette_sheet(palette))
    (root / "Color_Palette.svg").write_text(palette_svg(palette), encoding="utf-8")
    (root / "Hex_Codes.txt").write_text(
        "\n".join(f"{i + 1}  #{r:02X}{g:02X}{b:02X}" for i, (r, g, b) in enumerate(palette)) + "\n",
        encoding="utf-8")

    problems = []
    for n, page in enumerate(pages, 1):
        problems += [f"{page.name}: {p}" for p in verify_page(page, lut)]
        d = root / f"Design_{n:02d}"
        for sub in ("PNG", "PDF", "SVG"):
            (d / sub).mkdir(parents=True, exist_ok=True)
        styles = {"Dark_Numbered": "dark", "Light_Numbered": "light", "Shadow_Numbered": "shadow",
                  "Navigation_Map": "navigation", "Palette_Numbered": "palette", "Contour": "contour"}
        rendered = {}
        for fname, style in styles.items():
            img = render_style(page, palette, lut, style)
            rendered[style] = img
            save_png(d / "PNG" / f"{fname}.png", img)
        _style_pdf(d / "PDF" / f"Design_{n:02d}_A4.pdf",
                   [rendered[s] for s in ("dark", "light", "shadow", "palette")])
        (d / "SVG" / "Dark_Numbered.svg").write_text(render_svg(page, palette, DARK), encoding="utf-8")
        (d / "SVG" / "Light_Numbered.svg").write_text(render_svg(page, palette, LIGHT), encoding="utf-8")
    return problems
