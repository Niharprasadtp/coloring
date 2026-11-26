"""Etsy listing for the personalized kids car coloring book.

    ../.venv/Scripts/python.exe make_listing.py photos   # 12 photos -> ../output/kids_car_listing/photos
    ../.venv/Scripts/python.exe make_listing.py text     # listing.json + checkout PDF
    ../.venv/Scripts/python.exe make_listing.py upload   # create the Etsy DRAFT (once; id kept in uploaded.json)
    ../.venv/Scripts/python.exe make_listing.py update   # push current text + photos to that draft

Reuses (never edits) helpers from ../make_listing_images.py.
"""
from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import make_book as B                                   # noqa: E402
from make_listing_images import H, W, save_jpg, shadowed  # noqa: E402

OUT = ROOT / "output" / "kids_car_listing"
DEMO = OUT / "demo"
LUCKY = str(HERE / "fonts" / "LuckiestGuy-Regular.ttf")
NAVY, YELLOW, RED, BLUE, WHITE = (27, 42, 74), (255, 201, 60), (230, 57, 70), (46, 134, 222), (255, 255, 255)
PRICE = 599
TAXONOMY_ID = 339   # Books > Coloring Books (keep coloring products here; see memory)
HERO_NAME = "Leo"


def lucky(size):
    return ImageFont.truetype(LUCKY, size)


def body(size):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", size)


# ---------- assets ----------

def wood_bg(seed=0):
    """Warm light-wood desk."""
    rng = np.random.default_rng(seed)
    base = np.zeros((H, W, 3), np.float32) + np.array([226, 190, 146], np.float32)
    x = np.arange(W)[None, :]
    y = np.arange(H)[:, None]
    grain = (np.sin(x / 9.0 + np.sin(y / 140.0) * 3) * 4 + rng.normal(0, 4, (H, W)))[..., None]
    base = base + grain * np.array([1.0, 0.85, 0.7])
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for py in range(0, H, 400):
        d.line([(0, py), (W, py)], fill=(196, 158, 116), width=4)
    # soft vignette
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.2, -H * 0.3, W * 1.2, H * 1.3], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (150, 110, 75))
    return Image.composite(img, dark, vig)


def crayon(color, length=620, w=70):
    im = Image.new("RGBA", (length, w + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body_len = length - 120
    d.rounded_rectangle([0, 10, body_len, 10 + w], 16, fill=color + (255,))
    dark = tuple(int(v * 0.7) for v in color)
    for k in (90, body_len - 90):
        d.rectangle([k, 10, k + 26, 10 + w], fill=dark + (255,))
    d.polygon([(body_len - 4, 10 + 6), (length - 10, 10 + w / 2), (body_len - 4, 10 + w - 6)], fill=color + (255,))
    d.ellipse([length - 34, 10 + w / 2 - 12, length - 10, 10 + w / 2 + 12], fill=dark + (255,))
    return im


def put(canvas, layer, xy, angle=0, shadow=True):
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = int(xy[0]), int(xy[1])
    if shadow:
        sh = Image.new("RGBA", (layer.width + 80, layer.height + 80), (0, 0, 0, 0))
        sh.paste((0, 0, 0, 90), (40, 52), layer.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        canvas.paste(sh, (x - 40, y - 40), sh)
    canvas.paste(layer, (x, y), layer)


def crayons(canvas, spots):
    cols = [RED, YELLOW, BLUE, (42, 157, 143), (131, 56, 236), (244, 140, 50)]
    for k, (x, y, a) in enumerate(spots):
        put(canvas, crayon(cols[k % len(cols)]), (x, y), a)


def auto_color(png: Path, out: Path, seed: int, ground=(222, 196, 150)):
    """Kid-style coloring of a line-art page: each enclosed white area gets a bright crayon color."""
    a = np.asarray(Image.open(png).convert("L"))
    n, lab, st, cen = cv2.connectedComponentsWithStats((a > 200).astype(np.uint8), connectivity=4)
    h, w = a.shape
    rng = np.random.default_rng(seed)
    pal = [(230, 57, 70), (255, 183, 3), (33, 158, 188), (42, 157, 143), (244, 162, 97), (131, 56, 236),
           (255, 0, 110), (58, 134, 255), (6, 214, 160)]
    main = pal[seed % len(pal)]
    col = np.zeros((n, 3))
    for i in range(1, n):
        area, cy = st[i][4], cen[i][1] / h
        x0, y0, bw, bh = st[i][:4]
        if area < 60 or (y0 == 0 and y0 + bh == h):     # specks, or the open paper around the drawing
            col[i] = (255, 255, 255)
        elif area > 0.03 * h * w:
            col[i] = (178, 220, 245) if cy < 0.45 else ground
        elif area > 0.004 * h * w and cy > 0.65:
            col[i] = tuple(v * 0.92 for v in ground)
        else:
            col[i] = main if rng.random() < 0.45 else pal[rng.integers(len(pal))]
    res = np.where((lab > 0)[..., None], col[lab] * (a[..., None] / 255.0), np.stack([a] * 3, -1))
    Image.fromarray(res.astype(np.uint8)).save(out)
    return out


def demo_books():
    """Hero book for Leo (plate names colored in) + a few colored pages + covers for other names."""
    DEMO.mkdir(parents=True, exist_ok=True)
    pages = {p["file"]: p for p in B.MANIFEST["pages"]}
    colored = {}
    for k, (f, ground) in enumerate([("car_008.png", (222, 196, 150)), ("car_005.png", (175, 178, 186)),
                                     ("car_001.png", (175, 178, 186)), ("car_015.png", (175, 178, 186)),
                                     ("car_012.png", (222, 196, 150)), ("car_011.png", (175, 178, 186))]):
        colored[f] = auto_color(B.ART / f, DEMO / f"colored_{f}", seed=k + 2, ground=ground)
    B.PLATE_FILL = HexColor("#E63946")
    hero_pdf = DEMO / "Leo_Letter.pdf"
    if not hero_pdf.exists():
        B.build(HERO_NAME, "letter", hero_pdf)
    # single colored pages (same layout, colored art)
    for f, path in colored.items():
        item = dict(pages[f], file=str(path))
        idx = [p["file"] for p in B.MANIFEST["pages"]].index(f) + 1
        c = rl_canvas.Canvas(str(DEMO / f"page_colored_{f}.pdf"), pagesize=letter)
        B.coloring_page(c, *letter, HERO_NAME, idx, len(B.MANIFEST["pages"]), item)
        c.showPage()
        c.save()
    B.PLATE_FILL = None
    for name in ("Maya", "Noah", "Arjun", "Sofia"):
        c = rl_canvas.Canvas(str(DEMO / f"cover_{name}.pdf"), pagesize=letter)
        B.cover(c, *letter, name, 62)
        c.showPage()
        c.save()
    return hero_pdf, colored


def page_img(pdf: Path, idx: int, height: int) -> Image.Image:
    doc = pymupdf.open(pdf)
    p = doc[idx]
    z = height / p.rect.height
    return Image.open(io.BytesIO(p.get_pixmap(matrix=pymupdf.Matrix(z, z)).tobytes("png"))).convert("RGB")


def paper(img: Image.Image, radius=10) -> Image.Image:
    """Page with rounded corners as RGBA."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(m)
    return out


def headline(canvas, lines, y, sizes, fills, stroke=14):
    d = ImageDraw.Draw(canvas)
    for text, size, fill in zip(lines, sizes, fills):
        f = lucky(size)
        tw = d.textlength(text, font=f)
        d.text((W / 2 - tw / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=NAVY)
        y += int(size * 1.02)
    return y


def pill(canvas, text, cx, y, fill=RED, fg=WHITE, size=56):
    d = ImageDraw.Draw(canvas)
    f = lucky(size)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([cx - tw / 2 - 40, y, cx + tw / 2 + 40, y + size + 44], 30, fill=fill, outline=NAVY, width=6)
    d.text((cx - tw / 2, y + 26), text, font=f, fill=fg)


def zoom_circle(canvas, src: Image.Image, box, center, r, label=None):
    crop = src.crop(box)
    s = 2 * r / max(crop.size)
    crop = crop.resize((int(crop.width * s), int(crop.height * s)), Image.LANCZOS)
    disc = Image.new("RGBA", (2 * r, 2 * r), (255, 255, 255, 255))
    disc.paste(crop, ((2 * r - crop.width) // 2, (2 * r - crop.height) // 2))
    m = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    disc.putalpha(m)
    ring = Image.new("RGBA", (2 * r + 40, 2 * r + 40), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, 2 * r + 39, 2 * r + 39], fill=YELLOW + (255,), outline=NAVY, width=8)
    ring.paste(disc, (20, 20), disc)
    put(canvas, ring, (center[0] - r - 20, center[1] - r - 20))
    if label:
        pill(canvas, label, center[0], center[1] + r + 30, size=46)


# ---------- photos ----------

def p01_hero(hero_pdf, colored, out):
    cv = wood_bg(1)
    crayons(cv, [(40, 1500, 18), (2080, 210, -150), (2150, 1700, 160), (60, 140, -20)])
    y = headline(cv, ["THEIR NAME ON", "EVERY PAGE!"], 50, [190, 190], [YELLOW, WHITE], stroke=16)
    cover = page_img(hero_pdf, 0, 1330)
    put(cv, paper(cover), (370, y + 20), angle=4)
    pg = page_img(DEMO / "page_colored_car_008.png.pdf", 0, 1330)
    put(cv, paper(pg), (1260, y + 30), angle=-4)
    # zoom on the plate of the colored page
    big = page_img(DEMO / "page_colored_car_008.png.pdf", 0, 2200)
    s = 2200 / 792
    plate_box = (int((612 / 2 - 62) * s), int((792 - 82) * s), int((612 / 2 + 62) * s), int((792 - 30) * s))
    zoom_circle(cv, big, plate_box, (2030, 1640), 250)
    save_jpg(cv.convert("RGB"), out)


def p02_inside(hero_pdf, out):
    cv = wood_bg(2)
    headline(cv, ["62 PAGES OF CARS"], 60, [150], [YELLOW])
    idx = [0, 1, 2, 3, 4, 8, 17, 25, 38, 47, 55, 61]
    tw, th = 400, 518
    for k, i in enumerate(idx):
        im = page_img(hero_pdf, i, th)
        col, row = k % 6, k // 6
        x = 150 + col * 400 + (k % 2) * 6
        y = 330 + row * 600
        put(cv, paper(im.resize((tw - 30, th - 30))), (x, y), angle=(k % 3 - 1) * 2)
    pill(cv, "MONSTER TRUCKS · RACE CARS · SUPERCARS · CLASSICS", W / 2, 1560, fill=BLUE, size=60)
    d = ImageDraw.Draw(cv)
    t = "Plus: driver's license, checklist, color by number, design your own car & certificate"
    d.text((W / 2 - d.textlength(t, font=body(58)) / 2, 1740), t, font=body(58), fill=NAVY)
    save_jpg(cv.convert("RGB"), out)


def p03_plate(hero_pdf, out):
    cv = wood_bg(3)
    headline(cv, ["THEIR NAME ON EVERY CAR"], 60, [140], [YELLOW])
    pg = page_img(hero_pdf, 9, 1600)
    put(cv, paper(pg), (330, 300), angle=-2)
    big = page_img(hero_pdf, 9, 2400)
    s = 2400 / 792
    box = (int((612 / 2 - 125) * s), int((792 - 104) * s), int((612 / 2 + 125) * s), int((792 - 18) * s))
    zoom_circle(cv, big, box, (1860, 1000), 420, label="A LICENSE PLATE WITH THEIR NAME")
    save_jpg(cv.convert("RGB"), out)


def p_section(hero_pdf, title, colored_pdf, idxs, out, seed):
    cv = wood_bg(seed)
    headline(cv, [title], 60, [150], [YELLOW])
    a = page_img(hero_pdf, idxs[0], 1420)
    b = page_img(colored_pdf, 0, 1500)
    c = page_img(hero_pdf, idxs[1], 1420)
    put(cv, paper(a), (180, 400), angle=7)
    put(cv, paper(c), (1500, 400), angle=-7)
    put(cv, paper(b), (W // 2 - b.width // 2, 300))
    pill(cv, "COLORED EXAMPLE", W / 2, 1830, fill=RED, size=40)
    save_jpg(cv.convert("RGB"), out)


def p_bonus(hero_pdf, out):
    cv = wood_bg(7)
    headline(cv, ["FUN BONUS PAGES"], 60, [150], [YELLOW])
    items = [(2, "DRIVER'S LICENSE"), (3, "CHECKLIST"), (60, "DESIGN YOUR CAR"), (61, "CERTIFICATE")]
    for k, (i, lab) in enumerate(items):
        im = page_img(hero_pdf, i, 900)
        x = 110 + k * 625
        put(cv, paper(im), (x, 420), angle=(-3, 2, -2, 3)[k])
        pill(cv, lab, x + im.width / 2, 1450, fill=(BLUE, RED, BLUE, RED)[k], size=44)
    save_jpg(cv.convert("RGB"), out)


def p_cbn(hero_pdf, out):
    cv = wood_bg(8)
    headline(cv, ["COLOR BY NUMBER TOO"], 60, [150], [YELLOW])
    pg = page_img(hero_pdf, 56, 1560)
    put(cv, paper(pg), (330, 330), angle=-3)
    prev = Image.open(B.ART / B.MANIFEST["cbn"][1]["preview"]).convert("RGB")
    prev = prev.resize((int(prev.width * 900 / prev.height), 900))
    shadowed(cv, prev, (1560, 420), border=24, angle=4)
    pill(cv, "5 EASY PICTURES + COLOR KEY", 2000, 1450, fill=BLUE, size=50)
    save_jpg(cv.convert("RGB"), out)


def p_names(out):
    cv = wood_bg(9)
    headline(cv, ["ANY NAME, ANY KID"], 60, [150], [YELLOW])
    for k, name in enumerate(["Maya", "Noah", "Arjun", "Sofia"]):
        im = page_img(DEMO / f"cover_{name}.pdf", 0, 1150)
        put(cv, paper(im), (90 + k * 640, 420 + (k % 2) * 60), angle=(-4, 3, -2, 4)[k])
    pill(cv, "UP TO 16 LETTERS · NICKNAMES WELCOME", W / 2, 1780, fill=RED, size=50)
    save_jpg(cv.convert("RGB"), out)


def p_how(out):
    cv = wood_bg(10)
    headline(cv, ["HOW IT WORKS"], 60, [150], [YELLOW])
    steps = [("1", "TYPE THE NAME", "Add the child's name in the personalization box at checkout."),
             ("2", "WE MAKE THE BOOK", "Your personalized PDF arrives in Etsy Messages within 24 hours."),
             ("3", "PRINT & COLOR", "Print at home or at a print shop. US Letter and A4 included.")]
    d = ImageDraw.Draw(cv)
    for k, (n, head, text) in enumerate(steps):
        x = 170 + k * 800
        d.rounded_rectangle([x, 500, x + 720, 1500], 40, fill=WHITE, outline=NAVY, width=8)
        d.ellipse([x + 260, 560, x + 460, 760], fill=(RED, BLUE, YELLOW)[k], outline=NAVY, width=8)
        f = lucky(130)
        d.text((x + 360 - d.textlength(n, font=f) / 2, 595), n, font=f, fill=WHITE if k < 2 else NAVY)
        f2 = lucky(70)
        d.text((x + 360 - d.textlength(head, font=f2) / 2, 830), head, font=f2, fill=NAVY)
        words, line, ly = text.split(), "", 990
        for w_ in words + [None]:
            trial = (line + " " + w_).strip() if w_ else None
            if w_ and d.textlength(trial, font=body(60)) <= 640:
                line = trial
                continue
            d.text((x + 360 - d.textlength(line, font=body(60)) / 2, ly), line, font=body(60), fill=(60, 60, 60))
            ly += 84
            line = w_ or ""
    pill(cv, "DIGITAL DOWNLOAD · NOTHING IS SHIPPED", W / 2, 1760, fill=NAVY, size=50)
    save_jpg(cv.convert("RGB"), out)


def p_gift(hero_pdf, out):
    cv = wood_bg(11)
    crayons(cv, [(60, 1650, 8), (2000, 1700, -170), (1900, 120, 200)])
    headline(cv, ["THE PERFECT GIFT"], 60, [160], [YELLOW])
    cover = page_img(hero_pdf, 0, 1250)
    put(cv, paper(cover), (300, 380), angle=-5)
    d = ImageDraw.Draw(cv)
    lines = ["Christmas & stocking stuffers", "Birthdays & party favors", "Road trips & rainy days",
             "Car-loving kids ages 6-12", "Last-minute gift: ready in 24h"]
    for k, t in enumerate(lines):
        y = 520 + k * 210
        d.ellipse([1360, y, 1440, y + 80], fill=(RED, BLUE, YELLOW, RED, BLUE)[k], outline=NAVY, width=5)
        d.text((1480, y), t, font=body(68), fill=NAVY)
    save_jpg(cv.convert("RGB"), out)


def photos():
    pdir = OUT / "photos"
    pdir.mkdir(parents=True, exist_ok=True)
    for f in pdir.glob("*.jpg"):
        f.unlink()
    hero_pdf, colored = demo_books()
    p01_hero(hero_pdf, colored, pdir / "01_hero.jpg")
    p02_inside(hero_pdf, pdir / "02_inside.jpg")
    p03_plate(hero_pdf, pdir / "03_name_plate.jpg")
    order = [p["file"] for p in B.MANIFEST["pages"]]
    pi = lambda f: 4 + order.index(f)                      # page index in the book PDF
    p_section(hero_pdf, "MONSTER TRUCKS & 4X4", DEMO / "page_colored_car_012.png.pdf",
              [pi("car_003.png"), pi("car_018.png")], pdir / "04_monster_trucks.jpg", 4)
    p_section(hero_pdf, "RACE CARS", DEMO / "page_colored_car_005.png.pdf",
              [pi("car_017.png"), pi("car_004.png")], pdir / "05_race_cars.jpg", 5)
    p_section(hero_pdf, "SUPERCARS", DEMO / "page_colored_car_001.png.pdf",
              [pi("car_023.png"), pi("car_048.png")], pdir / "06_supercars.jpg", 6)
    p_section(hero_pdf, "MUSCLE & CLASSIC CARS", DEMO / "page_colored_car_015.png.pdf",
              [pi("car_021.png"), pi("car_002.png")], pdir / "07_classics.jpg", 12)
    p_section(hero_pdf, "STREET & TUNER CARS", DEMO / "page_colored_car_011.png.pdf",
              [pi("car_024.png"), pi("car_028.png")], pdir / "08_street.jpg", 13)
    p_bonus(hero_pdf, pdir / "09_bonus_pages.jpg")
    p_cbn(hero_pdf, pdir / "10_color_by_number.jpg")
    p_names(pdir / "11_any_name.jpg")
    p_how(pdir / "12_how_it_works.jpg")
    p_gift(hero_pdf, pdir / "13_gift.jpg")
    # thumbnail check (rule: photo 1 must read at 300px and 150px, important parts in the centre square)
    hero = Image.open(pdir / "01_hero.jpg")
    sq = hero.crop(((W - H) // 2, 0, (W + H) // 2, H))
    for s in (300, 150):
        sq.resize((s, s), Image.LANCZOS).save(OUT / f"CHECK_thumb_{s}.png")
    print(f"{len(list(pdir.glob('*.jpg')))} photos -> {pdir}")


# ---------- text ----------

TITLE = ("Personalized Car Coloring Book for Kids, Custom Name Coloring Pages, Monster Truck Race Car "
         "Activity, Boys Christmas Gift, Printable PDF")
TAGS = ["custom coloring book", "name coloring book", "car coloring book", "boys coloring book",
        "kids coloring pages", "monster truck pdf", "race car coloring", "gift for 8 year old",
        "stocking stuffer kid", "christmas gift kids", "kids activity pdf", "boy birthday gift",
        "color by number kids"]
NAME_INSTRUCTIONS = "Child's name exactly as it should appear (max 16 letters, Latin alphabet)."


def description():
    return """A coloring book made just for them! Their name goes on the cover, on a license plate under every single car, on their own driver's license and on a Coloring Champion certificate. 62 pages of monster trucks, race cars, supercars and classic cars for kids who love anything with wheels.

HOW IT WORKS
1. Type the child's name in the personalization box (max 16 letters, nicknames welcome).
2. I make the book and send your download link in Etsy Messages within 24 hours.
3. Print at home or at a print shop and start coloring!

WHAT'S INSIDE (62 PAGES)
- Personalized cover: "[NAME]'S CAR COLORING BOOK"
- "This book belongs to" page with the name in big letters to color
- Official driver's license to color, cut out and keep
- Garage checklist: tick off every car they finish
- 50 car coloring pages, each with the child's name on a license plate:
  13 monster trucks & off-road 4x4s, 8 race cars, 13 supercars, 9 muscle & classic cars, 7 street & tuner cars
- 5 easy color by number pictures with a color key and a "finished look" preview
- "Design your dream car" page
- Coloring Champion certificate with their name

YOU GET
- 2 print-ready PDFs: US Letter (8.5x11 in) and A4
- Thick, clear black outlines on clean white pages (one picture per page, so markers don't bleed through onto the next drawing)
- Print as many copies as you like for your own family

GREAT FOR
Christmas gifts and stocking stuffers, birthdays, party favors, road trips, rainy days, restaurants and quiet time. Best for ages 6 to 12 and any car-crazy kid (and grown-ups too).

PLEASE NOTE
- This is a DIGITAL item. Nothing is shipped. Crayons and paper are not included.
- At checkout you get a small PDF with 2 free bonus pages to start coloring right away. The personalized book follows in Etsy Messages within 24 hours.
- Please double-check the spelling of the name. Names use the Latin alphabet (A-Z, accents like é and ü are fine).
- The colored pages in the photos are examples of a finished page. The book pages are black and white, ready to color.
- For personal use only. Please don't share or resell the files.
- Questions or a spelling fix? Just send me a message."""


def checkout_pdf(path: Path):
    """The file Etsy delivers instantly: thank-you note + 2 bonus pages, plate 'SPEED RACER'."""
    W_, H_ = letter
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    c.setTitle("Your personalized car coloring book is on its way")
    B.text_c(c, "THANK YOU!", W_ / 2, H_ - 120, B.TITLE, 64, mode=2, stroke_w=2.2, fill=B.YELLOW, stroke=B.NAVY)
    lines = ["Your personalized car coloring book is being made right now.",
             "",
             "Within 24 hours you'll get a download link in Etsy Messages",
             "(Etsy > Messages, in the conversation for this order) with:",
             "   - the 62-page book in US Letter size",
             "   - the same book in A4 size",
             "",
             "Did you forget to type the name, or spot a typo?",
             "Just send me a message with the correct spelling.",
             "",
             "While you wait, here are 2 FREE bonus pages to start coloring!",
             "Print them on plain paper and grab your crayons."]
    c.setFont("Helvetica", 14)
    y = H_ - 190
    for ln in lines:
        c.drawString(72, y, ln)
        y -= 24
    c.showPage()
    pages = B.MANIFEST["pages"]
    for k, f in enumerate(("car_022.png", "car_017.png"), 1):
        item = next(p for p in pages if p["file"] == f)
        B.coloring_page(c, W_, H_, "SPEED RACER", k, 2, dict(item, section="BONUS PAGE"))
        c.showPage()
    c.save()


def text():
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(TITLE) <= 140, len(TITLE)
    assert len(TAGS) == 13 and len(set(TAGS)) == 13 and all(len(t) <= 20 for t in TAGS), TAGS
    assert len(NAME_INSTRUCTIONS) <= 120
    (OUT / "files").mkdir(exist_ok=True)
    checkout_pdf(OUT / "files" / "Thank_You_Plus_2_Bonus_Pages.pdf")
    data = dict(title=TITLE, tags=TAGS, description=description(), price=PRICE)
    (OUT / "listing.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"title {len(TITLE)} chars; listing.json + checkout PDF -> {OUT}")


# ---------- Etsy ----------

def set_personalization(e, sid, lid):
    q = [{"question_type": "text_input", "question_text": "Child's name", "required": True,
          "max_allowed_characters": 16, "instructions": NAME_INSTRUCTIONS}]
    e.request("POST", f"/shops/{sid}/listings/{lid}/personalization", json_body={"personalization_questions": q})


def upload():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state = OUT / "uploaded.json"
    if state.exists():
        sys.exit(f"already uploaded: {state.read_text()}")
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
        "quantity": 999, "title": t["title"], "description": t["description"], "price": t["price"],
        "who_made": "i_did", "when_made": "made_to_order", "taxonomy_id": TAXONOMY_ID, "type": "download",
        "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(t["tags"]),
        "is_personalizable": "true", "personalization_is_required": "true",
        "personalization_char_count_max": 16, "personalization_instructions": NAME_INSTRUCTIONS})
    lid = listing["listing_id"]
    state.write_text(json.dumps({"listing_id": lid}, indent=2))
    print("draft", lid, flush=True)
    for rank, p in enumerate(sorted((OUT / "photos").glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    for rank, p in enumerate(sorted((OUT / "files").iterdir()), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": p.name}, files={"file": p})
    print("photos + checkout file uploaded", flush=True)
    try:
        set_personalization(e, sid, lid)
        print("personalization question set", flush=True)
    except Exception as exc:
        print(f"could not set personalization by API ({exc}); add 'Child's name' in the Etsy editor", flush=True)
    print(f"https://www.etsy.com/your/shops/me/listing-editor/edit/{lid}")


def update():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    lid = json.loads((OUT / "uploaded.json").read_text())["listing_id"]
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    e.request("PATCH", f"/shops/{sid}/listings/{lid}", form={
        "title": t["title"], "description": t["description"], "tags": ",".join(t["tags"])})
    old = [im["listing_image_id"] for im in e.request("GET", f"/listings/{lid}/images")["results"]]
    new = sorted((OUT / "photos").glob("*.jpg"))
    while old and len(old) + len(new) > 20 and len(old) > 1:      # Etsy: max 20 images, min 1
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{old.pop()}")
    for rank, f in enumerate(new, 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": f})
    for image_id in old:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
    set_personalization(e, sid, lid)
    print(f"updated draft {lid}: text + {len(new)} photos", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"photos": photos, "text": text, "upload": upload, "update": update}.get(cmd, lambda: sys.exit(__doc__))()
