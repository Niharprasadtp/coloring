"""Personalized kids car coloring book: the child's name on the cover and on every page.

    ../.venv/Scripts/python.exe make_book.py "Aarav"             # Letter + A4 PDFs
    ../.venv/Scripts/python.exe make_book.py "Aarav" --preview   # also a PNG contact sheet to check

Output: ../output/kids_car_book/<Name>/<Name>_Car_Coloring_Book_{Letter,A4}.pdf
Needs art/ from prepare_art.py (run once).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
ART = HERE / "art"
OUT = HERE.parent / "output" / "kids_car_book"
MANIFEST = json.loads((ART / "manifest.json").read_text(encoding="utf-8"))

pdfmetrics.registerFont(TTFont("Lucky", str(HERE / "fonts" / "LuckiestGuy-Regular.ttf")))
TITLE, BODY = "Lucky", "Helvetica-Bold"
NAVY, RED, YELLOW, BLUE, ROAD = (HexColor(h) for h in ("#1B2A4A", "#E63946", "#FFC93C", "#2E86DE", "#3B3F46"))
GREY = HexColor("#6B7280")
MAX_NAME = 16
PLATE_FILL = None   # listing photos only: a HexColor fills the plate name, as if the child colored it in


# ---------- helpers ----------

def clean_name(raw: str) -> str:
    name = re.sub(r"\s+", " ", raw).strip()
    if not name:
        raise SystemExit("Name is empty.")
    if len(name) > MAX_NAME:
        raise SystemExit(f"Name '{name}' is longer than {MAX_NAME} characters. Use a shorter form or nickname.")
    face = pdfmetrics.getFont(TITLE).face
    missing = [ch for ch in name.upper() if ch != " " and ord(ch) not in face.charToGlyph]
    if missing:
        raise SystemExit(f"The title font has no glyph for {''.join(sorted(set(missing)))!r}. Use Latin letters.")
    return name


def possessive(name: str) -> str:
    up = name.upper()
    return up + ("'" if up.endswith("S") else "'S")


def fit(text: str, font: str, max_w: float, max_size: float, min_size: float = 6) -> float:
    w = pdfmetrics.stringWidth(text, font, 1)
    return max(min_size, min(max_size, max_w / w if w else max_size))


def text_c(c, text, x, y, font, size, mode=0, stroke_w=1.0, fill=black, stroke=black):
    """Centered text. mode 0 = filled, 1 = outline only (colorable), 2 = fill + outline."""
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(stroke_w)
    c.setLineJoin(1)
    t = c.beginText()
    t.setTextRenderMode(mode)
    t.setFont(font, size)
    t.setTextOrigin(x - pdfmetrics.stringWidth(text, font, size) / 2, y)
    t.textLine(text)
    c.drawText(t)
    c.restoreState()


def image_fit(c, path: Path, x, y, w, h, valign="middle"):
    im = Image.open(path)
    s = min(w / im.width, h / im.height)
    dw, dh = im.width * s, im.height * s
    dy = y + (h - dh) / 2 if valign == "middle" else y + h - dh if valign == "top" else y
    c.drawImage(ImageReader(str(path)), x + (w - dw) / 2, dy, dw, dh)
    return x + (w - dw) / 2, dy, dw, dh


def plate(c, cx, y, name, top_text, w=236, h=74):
    """A license plate with the child's name in colorable outline letters."""
    x = cx - w / 2
    c.saveState()
    c.setStrokeColor(black)
    c.setFillColor(white)
    c.setLineWidth(2.6)
    c.roundRect(x, y, w, h, 11, stroke=1, fill=1)
    c.setLineWidth(0.9)
    c.roundRect(x + 5, y + 5, w - 10, h - 10, 7, stroke=1, fill=0)
    for sx, sy in ((x + 15, y + h - 14), (x + w - 15, y + h - 14), (x + 15, y + 14), (x + w - 15, y + 14)):
        c.circle(sx, sy, 3.2, stroke=1, fill=0)
    c.restoreState()
    text_c(c, top_text, cx, y + h - 19, TITLE, 9)
    up = name.upper()
    size = fit(up, TITLE, w - 56, 34)
    if PLATE_FILL is None:
        text_c(c, up, cx, y + 15 + (34 - size) * 0.35, TITLE, size, mode=1, stroke_w=1.3)
    else:
        text_c(c, up, cx, y + 15 + (34 - size) * 0.35, TITLE, size, mode=2, stroke_w=1.3, fill=PLATE_FILL)


def header(c, W, H, left, right, done_box=True):
    c.setFont(TITLE, 13)
    c.setFillColor(black)
    c.drawString(36, H - 38, left)
    rx = W - 36
    if done_box:
        c.setLineWidth(1.4)
        c.rect(rx - 15, H - 41, 15, 15, stroke=1, fill=0)
        c.setFont(TITLE, 11)
        c.drawRightString(rx - 21, H - 38, "DONE!")
        rx -= 76
    c.setFont(TITLE, 13)
    c.drawRightString(rx, H - 38, right)
    c.setLineWidth(0.8)
    c.line(36, H - 48, W - 36, H - 48)


def checker_strip(c, x, y, w, sq, rows=2, filled=True):
    n = int(w // sq)
    x0 = x + (w - n * sq) / 2
    c.setLineWidth(0.8)
    for r in range(rows):
        for i in range(n):
            dark = (i + r) % 2 == 0
            c.setFillColor(black if dark and filled else white)
            c.rect(x0 + i * sq, y + r * sq, sq, sq, stroke=1, fill=1)


def star(c, cx, cy, r, fill=False):
    p = c.beginPath()
    for k in range(10):
        rad = r if k % 2 == 0 else r * 0.45
        a = math.pi / 2 + k * math.pi / 5
        (p.moveTo if k == 0 else p.lineTo)(cx + rad * math.cos(a), cy + rad * math.sin(a))
    p.close()
    c.setLineWidth(1.4)
    c.drawPath(p, stroke=1, fill=1 if fill else 0)


# ---------- pages ----------

def cover(c, W, H, name, total_pages):
    c.setFillColor(BLUE)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    # road
    road_h = H * 0.17
    c.setFillColor(ROAD)
    c.rect(0, 0, W, road_h, stroke=0, fill=1)
    c.setFillColor(YELLOW)
    for i in range(0, int(W) + 60, 60):
        c.rect(i, road_h * 0.47, 34, 6, stroke=0, fill=1)
    c.setFillColor(white)
    c.rect(0, road_h - 6, W, 6, stroke=0, fill=1)
    # checkered top
    c.setStrokeColor(black)
    checker_strip(c, 0, H - 36, W, 18, rows=2)
    # title
    pos = possessive(name)
    size = fit(pos, TITLE, W - 70, 104, 30)
    y = H - 60 - size * 0.86
    text_c(c, pos, W / 2, y, TITLE, size, mode=2, stroke_w=max(2.5, size / 22), fill=YELLOW, stroke=NAVY)
    s2 = fit("CAR COLORING BOOK", TITLE, W - 70, 58)
    y2 = y - s2 * 1.05
    text_c(c, "CAR COLORING BOOK", W / 2, y2, TITLE, s2, mode=2, stroke_w=2.2, fill=white, stroke=NAVY)
    # ribbon
    rib_y = y2 - 46
    c.setFillColor(RED)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.roundRect(W * 0.12, rib_y, W * 0.76, 32, 8, stroke=1, fill=1)
    text_c(c, "MONSTER TRUCKS · RACE CARS · SUPERCARS", W / 2, rib_y + 10,
           TITLE, fit("MONSTER TRUCKS · RACE CARS · SUPERCARS", TITLE, W * 0.70, 17), fill=white)
    # hero card (tilted page with line art)
    card_w = W * 0.66
    top = rib_y - 22
    bottom = road_h * 0.55
    card_h = top - bottom
    cx, cy = W / 2, bottom + card_h / 2
    c.saveState()
    c.translate(cx, cy)
    c.rotate(-3.5)
    c.setFillColor(HexColor("#00000040"))
    c.roundRect(-card_w / 2 + 7, -card_h / 2 - 7, card_w, card_h, 10, stroke=0, fill=1)
    c.setFillColor(white)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.roundRect(-card_w / 2, -card_h / 2, card_w, card_h, 10, stroke=1, fill=1)
    image_fit(c, ART / "car_008.png", -card_w / 2 + 14, -card_h / 2 + 14, card_w - 28, card_h - 28)
    c.restoreState()
    # page-count badge
    bx, by, br = W * 0.83, top - 40, 46
    c.setFillColor(YELLOW)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.circle(bx, by, br, stroke=1, fill=1)
    text_c(c, str(total_pages), bx, by - 2, TITLE, 34, fill=NAVY)
    text_c(c, "PAGES", bx, by - 22, TITLE, 13, fill=NAVY)
    # personal line on the road
    line = f"MADE ESPECIALLY FOR {name.upper()}"
    text_c(c, line, W / 2, road_h * 0.16, TITLE, fit(line, TITLE, W - 80, 20), fill=white)


def belongs_to(c, W, H, name):
    checker_strip(c, 36, H - 72, W - 72, 18, rows=2, filled=True)
    checker_strip(c, 36, 36, W - 72, 18, rows=2, filled=True)
    text_c(c, "THIS BOOK", W / 2, H - 170, TITLE, 58, mode=1, stroke_w=1.6)
    text_c(c, "BELONGS TO", W / 2, H - 236, TITLE, 58, mode=1, stroke_w=1.6)
    up = name.upper()
    size = fit(up, TITLE, W - 90, 140, 40)
    text_c(c, up, W / 2, H * 0.50 - size * 0.3, TITLE, size, mode=1, stroke_w=2.2)
    for sx in (W * 0.16, W * 0.84):
        star(c, sx, H * 0.62, 20)
    image_fit(c, ART / "car_001.png", 70, 92, W - 140, H * 0.30)


def license_page(c, W, H, name):
    text_c(c, "MY OFFICIAL", W / 2, H - 100, TITLE, 40, mode=1, stroke_w=1.4)
    text_c(c, "DRIVER'S LICENSE", W / 2, H - 150, TITLE, 46, mode=1, stroke_w=1.4)
    cw, ch = min(W - 90, 470), 300
    x, y = (W - cw) / 2, H - 200 - ch
    c.setDash(6, 4)
    c.setLineWidth(1)
    c.roundRect(x - 12, y - 12, cw + 24, ch + 24, 16, stroke=1, fill=0)
    c.setDash()
    c.setFont(BODY, 8)
    c.drawString(x - 8, y + ch + 16, "CUT ALONG THE DASHED LINE")
    c.setLineWidth(2.4)
    c.roundRect(x, y, cw, ch, 14, stroke=1, fill=0)
    c.setFillColor(black)
    c.roundRect(x, y + ch - 50, cw, 50, 14, stroke=0, fill=1)
    c.rect(x, y + ch - 50, cw, 20, stroke=0, fill=1)
    text_c(c, "DREAM GARAGE DRIVING CLUB", x + cw / 2, y + ch - 33, TITLE,
           fit("DREAM GARAGE DRIVING CLUB", TITLE, cw - 40, 24), fill=white)
    # photo box
    c.setLineWidth(1.6)
    c.roundRect(x + 18, y + 64, 128, 158, 8, stroke=1, fill=0)
    c.setFont(BODY, 9)
    c.drawCentredString(x + 82, y + 72, "DRAW YOUR FACE!")
    num = int(hashlib.sha1(name.upper().encode()).hexdigest(), 16) % 9000 + 1000
    fx = x + 166
    rows = [("NAME", name.upper()), ("LICENSE NO.", f"DG-{num}"), ("CLASS", "SUPERCARS & MONSTER TRUCKS"),
            ("SKILL", "COLORING CHAMPION"), ("EXPIRES", "NEVER!")]
    ty = y + ch - 80
    for label, val in rows:
        c.setFont(BODY, 8)
        c.setFillColor(GREY)
        c.drawString(fx, ty + 13, label)
        c.setFillColor(black)
        c.setFont(TITLE, fit(val, TITLE, cw - (fx - x) - 20, 17))
        c.drawString(fx, ty - 4, val)
        ty -= 38
    c.setLineWidth(1)
    c.line(fx, y + 40, x + cw - 20, y + 40)
    c.setFont(BODY, 8)
    c.drawString(fx, y + 28, "SIGNATURE")
    for i in range(3):
        star(c, x + 40 + i * 30, y + 34, 9)
    text_c(c, "Color it, cut it out and keep it in your pocket!", W / 2, y - 50, BODY, 14)


def checklist(c, W, H, name, pages, n_cbn):
    text_c(c, "MY GARAGE CHECKLIST", W / 2, H - 92, TITLE, fit("MY GARAGE CHECKLIST", TITLE, W - 80, 46), mode=1, stroke_w=1.4)
    text_c(c, f"Tick a box every time you finish a car, {name}!", W / 2, H - 124, BODY, 14)
    cols = 5
    labels = [str(i + 1) for i in range(len(pages))] + [f"CBN {i + 1}" for i in range(n_cbn)]
    rows = math.ceil(len(labels) / cols)
    top, bottom = H - 150, 60
    cell_h = (top - bottom) / rows
    cell_w = (W - 72) / cols
    for k, lab in enumerate(labels):
        r, col = divmod(k, cols)
        x = 36 + col * cell_w
        y = top - (r + 1) * cell_h
        c.setLineWidth(1.2)
        c.roundRect(x + 4, y + 3, cell_w - 8, cell_h - 6, 6, stroke=1, fill=0)
        c.setFont(TITLE, min(16, cell_h * 0.5))
        c.drawString(x + 12, y + cell_h / 2 - 5, ("CAR " if lab.isdigit() else "") + lab)
        bs = min(16, cell_h - 14)
        c.rect(x + cell_w - 14 - bs, y + (cell_h - bs) / 2, bs, bs, stroke=1, fill=0)


def coloring_page(c, W, H, name, idx, total, item):
    header(c, W, H, item["section"], f"CAR {idx}/{total}")
    image_fit(c, ART / item["file"], 36, 108, W - 72, H - 160)
    plate(c, W / 2, 24, name, f"DREAM GARAGE  ·  NO. {idx:02d}")


def cbn_divider(c, W, H, name):
    text_c(c, "COLOR", W / 2, H - 200, TITLE, 92, mode=1, stroke_w=2)
    text_c(c, "BY NUMBER", W / 2, H - 290, TITLE, fit("BY NUMBER", TITLE, W - 80, 92), mode=1, stroke_w=2)
    lines = ["Every space has a number.",
             "Find that number in the COLOR KEY",
             "and color the space with the same color.",
             "Peek at the little picture to see the finished car!"]
    for i, ln in enumerate(lines):
        text_c(c, ln, W / 2, H - 370 - i * 26, BODY, 16)
    # demo: three numbered blobs with key
    demo = [("#E63946", "1"), ("#FFC93C", "2"), ("#2E86DE", "3")]
    for i, (hx, n) in enumerate(demo):
        x = W / 2 - 120 + i * 120
        c.setFillColor(HexColor(hx))
        c.setLineWidth(1.4)
        c.circle(x, 200, 34, stroke=1, fill=1)
        text_c(c, n, x, 190, TITLE, 30, fill=black)
    text_c(c, f"You've got this, {name}!", W / 2, 110, TITLE, fit(f"You've got this, {name}!", TITLE, W - 80, 34), mode=1, stroke_w=1.2)


def lum(hx: str) -> float:
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def cbn_page(c, W, H, name, idx, total, item):
    header(c, W, H, "COLOR BY NUMBER", f"PICTURE {idx}/{total}")
    image_fit(c, ART / item["file"], 36, 176, W - 72, H - 228)
    pal = item["palette"]
    per_row = 9
    d = 24
    gap = (W - 72 - 96 - per_row * d) / (per_row - 1)
    c.setFont(TITLE, 10)
    c.drawString(36, 162, "COLOR KEY")
    for k, hx in enumerate(pal):
        r, col = divmod(k, per_row)
        x = 36 + d / 2 + col * (d + gap)
        y = 142 - r * (d + 8)
        c.setFillColor(HexColor(hx))
        c.setStrokeColor(black)
        c.setLineWidth(1)
        c.circle(x, y, d / 2, stroke=1, fill=1)
        text_c(c, str(k + 1), x, y - 4, BODY, 10, fill=white if lum(hx) < 140 else black)
    # finished-look thumbnail
    tx, ty, tw, th = W - 36 - 84, 100, 84, 74
    c.setFont(BODY, 7)
    c.setFillColor(black)
    image_fit(c, ART / item["preview"], tx, ty + 10, tw, th - 10)
    c.drawCentredString(tx + tw / 2, ty + 1, "FINISHED LOOK")
    plate(c, W / 2, 20, name, f"DREAM GARAGE  ·  PICTURE {idx}", h=70)


def design_own(c, W, H, name):
    t = f"DESIGN YOUR DREAM CAR, {name.upper()}!"
    text_c(c, t, W / 2, H - 80, TITLE, fit(t, TITLE, W - 70, 40), mode=1, stroke_w=1.3)
    c.setLineWidth(2.2)
    c.roundRect(36, 230, W - 72, H - 340, 16, stroke=1, fill=0)
    c.setLineWidth(1.2)
    c.line(50, 300, W - 50, 300)
    c.setDash(14, 10)
    c.line(50, 268, W - 50, 268)
    c.setDash()
    prompts = ["My car's name:", "Top speed:", "Super power:"]
    for i, p in enumerate(prompts):
        y = 182 - i * 46
        c.setFont(TITLE, 18)
        c.drawString(40, y, p)
        c.setLineWidth(1)
        c.line(40 + pdfmetrics.stringWidth(p, TITLE, 18) + 10, y - 2, W - 40, y - 2)


def trophy(c, cx, y, s=1.0):
    c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx - 55 * s, y + 150 * s)
    p.lineTo(cx + 55 * s, y + 150 * s)
    p.curveTo(cx + 55 * s, y + 80 * s, cx + 30 * s, y + 60 * s, cx, y + 58 * s)
    p.curveTo(cx - 30 * s, y + 60 * s, cx - 55 * s, y + 80 * s, cx - 55 * s, y + 150 * s)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    for sgn in (-1, 1):
        h = c.beginPath()
        h.moveTo(cx + sgn * 52 * s, y + 138 * s)
        h.curveTo(cx + sgn * 90 * s, y + 138 * s, cx + sgn * 85 * s, y + 90 * s, cx + sgn * 40 * s, y + 80 * s)
        c.drawPath(h, stroke=1, fill=0)
    c.rect(cx - 9 * s, y + 30 * s, 18 * s, 28 * s, stroke=1, fill=0)
    c.roundRect(cx - 40 * s, y, 80 * s, 30 * s, 4, stroke=1, fill=0)
    star(c, cx, y + 108 * s, 22 * s)


def certificate(c, W, H, name, n_cars):
    c.setLineWidth(3)
    c.roundRect(28, 28, W - 56, H - 56, 18, stroke=1, fill=0)
    c.setLineWidth(1)
    c.roundRect(38, 38, W - 76, H - 76, 12, stroke=1, fill=0)
    checker_strip(c, 60, H - 96, W - 120, 14, rows=2)
    text_c(c, "CERTIFICATE", W / 2, H - 170, TITLE, 62, mode=1, stroke_w=1.8)
    text_c(c, "OF AWESOME COLORING", W / 2, H - 214, TITLE, fit("OF AWESOME COLORING", TITLE, W - 120, 36))
    text_c(c, "This certifies that", W / 2, H - 262, BODY, 16)
    up = name.upper()
    size = fit(up, TITLE, W - 130, 96, 30)
    text_c(c, up, W / 2, H - 290 - size * 0.8, TITLE, size, mode=1, stroke_w=2)
    text_c(c, f"colored all {n_cars} cars in the Dream Garage", W / 2, H - 330 - size * 0.8, BODY, 16)
    text_c(c, "and is now an official", W / 2, H - 352 - size * 0.8, BODY, 16)
    text_c(c, "COLORING CHAMPION!", W / 2, H - 392 - size * 0.8, TITLE, 34)
    trophy(c, W / 2, 130, 0.9)
    for sx in (W * 0.2, W * 0.8):
        star(c, sx, 230, 22)
    c.setLineWidth(1)
    c.line(70, 96, 240, 96)
    c.line(W - 240, 96, W - 70, 96)
    c.setFont(BODY, 11)
    c.drawCentredString(155, 80, "DATE")
    c.drawCentredString(W - 155, 80, "SIGNED")


# ---------- book ----------

def build(name: str, size: str, dest: Path) -> int:
    W, H = {"letter": letter, "a4": A4}[size]
    pages, cbn = MANIFEST["pages"], MANIFEST["cbn"]
    total_pages = 4 + len(pages) + 1 + len(cbn) + 2
    c = canvas.Canvas(str(dest), pagesize=(W, H))
    c.setTitle(f"{possessive(name).title()} Car Coloring Book")
    c.setAuthor("SpellbindinTreasures")
    c.setSubject("Personalized car coloring book for kids")
    steps = [lambda: cover(c, W, H, name, total_pages),
             lambda: belongs_to(c, W, H, name),
             lambda: license_page(c, W, H, name),
             lambda: checklist(c, W, H, name, pages, len(cbn))]
    steps += [lambda i=i, p=p: coloring_page(c, W, H, name, i, len(pages), p) for i, p in enumerate(pages, 1)]
    steps += [lambda: cbn_divider(c, W, H, name)]
    steps += [lambda i=i, p=p: cbn_page(c, W, H, name, i, len(cbn), p) for i, p in enumerate(cbn, 1)]
    steps += [lambda: design_own(c, W, H, name), lambda: certificate(c, W, H, name, len(pages))]
    assert len(steps) == total_pages
    for step in steps:
        step()
        c.showPage()
    c.save()
    return total_pages


def preview(pdf: Path, out_png: Path, pages: list[int]) -> None:
    import pymupdf
    doc = pymupdf.open(pdf)
    ims = []
    for i in pages:
        pix = doc[i].get_pixmap(dpi=50)
        ims.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
    w, h = ims[0].size
    cols = min(6, len(ims))
    sheet = Image.new("RGB", (cols * w, math.ceil(len(ims) / cols) * h), "white")
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.save(out_png)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="child's name, e.g. \"Aarav\" (max 16 Latin characters)")
    ap.add_argument("--sizes", default="letter,a4")
    ap.add_argument("--preview", action="store_true", help="also write a PNG contact sheet of key pages")
    args = ap.parse_args()
    name = clean_name(args.name)
    slug = re.sub(r"[^\w]+", "_", name).strip("_") or "Child"
    folder = OUT / slug
    folder.mkdir(parents=True, exist_ok=True)
    for size in args.sizes.split(","):
        dest = folder / f"{slug}_Car_Coloring_Book_{'Letter' if size == 'letter' else 'A4'}.pdf"
        n = build(name, size, dest)
        print(f"{dest}  ({n} pages, {dest.stat().st_size / 1e6:.1f} MB)")
        if args.preview and size == "letter":
            png = folder / "CHECK_preview.png"
            preview(dest, png, [0, 1, 2, 3, 4, 20, 54, 55, 56, 60, 61])
            print(f"preview: {png}")


if __name__ == "__main__":
    main()
