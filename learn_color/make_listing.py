"""Etsy listing for the color-by-code math bundle (run make_bundle.py first).

    ../.venv/Scripts/python.exe make_listing.py photos   # -> ../output/learn_color/listing/photos
    ../.venv/Scripts/python.exe make_listing.py text     # listing.json
    ../.venv/Scripts/python.exe make_listing.py upload   # Etsy DRAFT in "Teacher Resources" (once)
    ../.venv/Scripts/python.exe make_listing.py update   # push text + photos to that draft
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT))
import importlib.util                                                         # noqa: E402

import color_by_code as cbc                                                   # noqa: E402
import make_bundle as MB                                                      # noqa: E402
from make_listing_images import H, W, save_jpg                                # noqa: E402

# shared photo helpers from the kids car book listing (same file name as this one: load it by path)
sys.path.insert(2, str(ROOT / "kids_car_book"))
_spec = importlib.util.spec_from_file_location("kids_listing", ROOT / "kids_car_book" / "make_listing.py")
KL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(KL)
BLUE, NAVY, RED, WHITE, YELLOW = KL.BLUE, KL.NAVY, KL.RED, KL.WHITE, KL.YELLOW
body, crayons, headline, lucky, paper, pill, put, wood_bg, zoom_circle = (
    KL.body, KL.crayons, KL.headline, KL.lucky, KL.paper, KL.pill, KL.put, KL.wood_bg, KL.zoom_circle)

OUT = ROOT / "output" / "learn_color" / "listing"
PHOTOS = OUT / "photos"
PRICE = 499
TAXONOMY = 12471          # Worksheets (same as the Christmas math mystery pictures)
SECTION = "Teacher Resources"
LEVEL_PDF = {s: MB.OUT / f"Color_by_Code_{f}_Letter.pdf" for s, f, _ in MB.LEVELS}
GREEN = (42, 157, 90)


# ---------- page images ----------

def page_img(pdf: Path, idx: int, height: int) -> Image.Image:
    p = pymupdf.open(pdf)[idx]
    z = height / p.rect.height
    return Image.open(io.BytesIO(p.get_pixmap(matrix=pymupdf.Matrix(z, z)).tobytes("png"))).convert("RGB")


def overlays() -> Path:
    """One page per picture with only the finished picture, placed exactly where the worksheet puts it."""
    pdf = OUT / "colored_overlays.pdf"
    Wl, Hl = letter
    c = canvas.Canvas(str(pdf), pagesize=letter)
    for path in MB.PICTURES:
        pic = cbc.prepare(path, Wl, Hl)
        cbc.answer_picture(c, pic, pic["ox"], pic["oy"] - pic["dh"], pic["dw"], pic["dh"])
        c.showPage()
    c.save()
    return pdf


def colored(skill: str, n: int, height: int, frac: float = 1.0) -> Image.Image:
    """Worksheet n (1-based) colored in like a finished sheet: the crayon colors multiply over the page,
    so outlines and problems still show. frac < 1 colors only the left part (diagonal edge)."""
    ws = np.asarray(page_img(LEVEL_PDF[skill], n, height)).astype(float)
    col = np.asarray(page_img(OUT / "colored_overlays.pdf", n - 1, height)).astype(float)
    out = ws * col / 255.0
    if frac < 1:
        h, w = ws.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        left = xx < (frac * w + (yy - h / 2) * 0.35)
        out = np.where(left[..., None], out, ws)
    return Image.fromarray(out.astype(np.uint8))


# ---------- photos ----------

def p01_hero(out):
    cv = wood_bg(21)
    crayons(cv, [(30, 1560, 14), (2050, 180, -150), (2120, 1650, 165), (40, 120, -18)])
    y = headline(cv, ["SOLVE IT.", "COLOR IT!"], 40, [180, 180], [YELLOW, WHITE], stroke=16)
    pg = colored("add10", 1, 1460, frac=0.55)
    put(cv, paper(pg), (W // 2 - pg.width // 2 - 120, y - 40), angle=-3)
    big = colored("add10", 1, 2600, frac=0.55)
    s = 2600 / 792
    box = (int(250 * s), int(330 * s), int(380 * s), int(460 * s))     # problems around the penguin's face
    zoom_circle(cv, big, box, (2010, 1180), 300, label="SELF-CHECKING MATH")
    save_jpg(cv.convert("RGB"), out)


def p02_levels(out):
    cv = wood_bg(22)
    headline(cv, ["4 LEVELS, SAME PICTURE"], 50, [140], [YELLOW])
    labels = [("add10", "ADDITION · K-1", RED), ("sub10", "SUBTRACTION · K-1", BLUE),
              ("mult", "MULTIPLICATION · 3-4", GREEN), ("div", "DIVISION · 3-4", (131, 56, 236))]
    for k, (skill, lab, col) in enumerate(labels):
        im = page_img(LEVEL_PDF[skill], 2, 1180)
        x = 70 + k * 640
        put(cv, paper(im), (x, 320), angle=(-2, 1.5, -1.5, 2)[k])
        pill(cv, lab, x + im.width / 2, 1560, fill=col, size=40)
    d = ImageDraw.Draw(cv)
    t = "Differentiate with ease: the whole class colors the same picture at their own level"
    d.text((W / 2 - d.textlength(t, font=body(54)) / 2, 1740), t, font=body(54), fill=NAVY)
    save_jpg(cv.convert("RGB"), out)


def p03_pictures(out):
    cv = wood_bg(23)
    headline(cv, ["10 MYSTERY PICTURES"], 50, [150], [YELLOW])
    for k in range(10):
        im = colored("add10", k + 1, 1000)
        im = im.crop((0, int(im.height * 0.14), im.width, int(im.height * 0.84)))
        im = im.resize((460, int(460 * im.height / im.width)))
        col, row = k % 5, k // 5
        put(cv, paper(im), (90 + col * 505, 330 + row * 760), angle=((k % 3) - 1) * 2)
    save_jpg(cv.convert("RGB"), out)


def p04_key(out):
    cv = wood_bg(24)
    headline(cv, ["CRAYON COLOR KEY"], 50, [150], [YELLOW])
    pg = page_img(LEVEL_PDF["mult"], 5, 1560)
    put(cv, paper(pg), (150, 300), angle=-2)
    d = ImageDraw.Draw(cv)
    pts = ["Plain crayon colors, named in the key", "Tiny parts come pre-colored",
           "Spaces with no problem stay white", "Big, clear numbers", "Answer keys included"]
    for k, t in enumerate(pts):
        y = 520 + k * 210
        d.ellipse([1430, y, 1510, y + 80], fill=(RED, BLUE, YELLOW, GREEN, RED)[k], outline=NAVY, width=5)
        d.text((1550, y + 2), t, font=body(62), fill=NAVY)
    save_jpg(cv.convert("RGB"), out)


def p_pair(out, skill, n, title, seed):
    cv = wood_bg(seed)
    headline(cv, [title], 50, [150], [YELLOW])
    a = page_img(LEVEL_PDF[skill], n, 1500)
    b = colored(skill, n, 1500)
    put(cv, paper(a), (170, 330), angle=-3)
    put(cv, paper(b), (1360, 330), angle=3)
    pill(cv, "BEFORE", 170 + a.width / 2, 1860, fill=NAVY, size=44)
    pill(cv, "AFTER", 1360 + b.width / 2, 1860, fill=RED, size=44)
    save_jpg(cv.convert("RGB"), out)


def p_answers(out):
    cv = wood_bg(26)
    headline(cv, ["ANSWER KEYS INCLUDED"], 50, [150], [YELLOW])
    t = page_img(LEVEL_PDF["add10"], 0, 1400)
    a = page_img(LEVEL_PDF["add10"], 11, 1400)
    put(cv, paper(t), (250, 380), angle=-3)
    put(cv, paper(a), (1350, 380), angle=3)
    pill(cv, "TEACHER PAGE", 250 + t.width / 2, 1840, fill=BLUE, size=44)
    pill(cv, "4 ANSWER KEYS PER PAGE", 1350 + a.width / 2, 1840, fill=RED, size=44)
    save_jpg(cv.convert("RGB"), out)


def p_included(out):
    cv = wood_bg(27)
    headline(cv, ["WHAT YOU GET"], 50, [150], [YELLOW])
    d = ImageDraw.Draw(cv)
    d.rounded_rectangle([330, 330, W - 330, 1800], 50, fill=WHITE, outline=NAVY, width=8)
    rows = [("40", "worksheets: 10 pictures x 4 levels"),
            ("4", "PDFs: Addition, Subtraction, Multiplication, Division"),
            ("10", "answer keys in every PDF"),
            ("2", "paper sizes: US Letter + A4"),
            ("1", "teacher page with tips and how it works")]
    for k, (n, t) in enumerate(rows):
        y = 430 + k * 265
        d.ellipse([440, y, 640, y + 200], fill=(RED, BLUE, GREEN, YELLOW, RED)[k], outline=NAVY, width=6)
        f = lucky(100 if len(n) < 2 else 90)
        d.text((540 - d.textlength(n, font=f) / 2, y + 48), n, font=f, fill=WHITE if k != 3 else NAVY)
        d.text((700, y + 62), t, font=body(64), fill=NAVY)
    save_jpg(cv.convert("RGB"), out)


def p_benefits(out):
    """What children get out of it, around a half-colored sheet."""
    from PIL import ImageFont
    sym = lambda size: ImageFont.truetype("C:/Windows/Fonts/seguisym.ttf", size)
    cv = wood_bg(29)
    headline(cv, ["LEARN WHILE THEY COLOR"], 40, [140], [YELLOW])
    pg = colored("mult", 5, 1480, frac=0.58)
    put(cv, paper(pg), (W // 2 - pg.width // 2, 290), angle=-1.5)
    left = [("+\u00d7", "lucky", "MATH FACT FLUENCY", ["Dozens of math facts", "practiced on every page"], RED),
            ("\U0001F50D", "sym", "THINKING SKILLS", ["Solve, match the key,", "discover the picture"], BLUE),
            ("\U0001F4A1", "sym", "MEMORY", ["Repetition helps", "math facts stick"], GREEN)]
    right = [("\U0001F3AF", "sym", "FOCUS & PATIENCE", ["Calm, steady work,", "one space at a time"], (131, 56, 236)),
             ("\u270e", "sym", "FINE MOTOR SKILLS", ["Coloring inside the lines", "builds hand control"], (244, 140, 50)),
             ("\u2713", "sym", "CONFIDENCE", ["A wrong color shows a", "mistake kids can fix"], RED)]
    d = ImageDraw.Draw(cv)
    card_w, card_h = 740, 400
    for side, items in (("L", left), ("R", right)):
        x = 50 if side == "L" else W - 50 - card_w
        for k, (icon, kind, title, lines, col) in enumerate(items):
            y = 300 + k * (card_h + 60)
            d.rounded_rectangle([x, y, x + card_w, y + card_h], 40, fill=WHITE, outline=NAVY, width=7)
            cx, cy, r = x + 120, y + card_h // 2, 88
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=NAVY, width=6)
            f = lucky(92) if kind == "lucky" else sym(104)
            bb = d.textbbox((0, 0), icon, font=f)
            d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), icon, font=f, fill=WHITE)
            tx = x + 240
            room = x + card_w - 30 - tx
            size = 56
            while d.textlength(title, font=lucky(size)) > room:
                size -= 2
            d.text((tx, y + 70 + (56 - size) // 2), title, font=lucky(size), fill=NAVY)
            size = 40
            while max(d.textlength(ln, font=body(size)) for ln in lines) > room:
                size -= 1
            for j, ln in enumerate(lines):
                d.text((tx, y + 170 + j * 58), ln, font=body(size), fill=(70, 70, 70))
    pill(cv, "STUDY + COLOR = LEARNING THAT FEELS LIKE PLAY", W / 2, 1810, fill=NAVY, size=52)
    save_jpg(cv.convert("RGB"), out)


def p_uses(out):
    cv = wood_bg(28)
    crayons(cv, [(60, 1680, 10), (2000, 1700, -170)])
    headline(cv, ["PERFECT FOR"], 50, [160], [YELLOW])
    pg = colored("mult", 8, 1300, frac=0.6)
    put(cv, paper(pg), (200, 360), angle=-4)
    d = ImageDraw.Draw(cv)
    uses = ["Early finishers", "Math centers & stations", "Sub plans", "Homework & homeschool",
            "Winter break & holiday parties", "Fact fluency practice"]
    for k, t in enumerate(uses):
        y = 430 + k * 205
        d.ellipse([1300, y, 1380, y + 80], fill=(RED, BLUE, YELLOW, GREEN, RED, BLUE)[k], outline=NAVY, width=5)
        d.text((1420, y + 2), t, font=body(66), fill=NAVY)
    save_jpg(cv.convert("RGB"), out)


def photos():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    for f in PHOTOS.glob("*.jpg"):
        f.unlink()
    overlays()
    p01_hero(PHOTOS / "01_hero.jpg")
    p_benefits(PHOTOS / "01b_benefits.jpg")
    p02_levels(PHOTOS / "02_four_levels.jpg")
    p03_pictures(PHOTOS / "03_ten_pictures.jpg")
    p_pair(PHOTOS / "04_addition.jpg", "add10", 3, "ADDITION TO 10", 31)
    p_pair(PHOTOS / "05_multiplication.jpg", "mult", 5, "MULTIPLICATION", 32)
    p04_key(PHOTOS / "06_color_key.jpg")
    p_pair(PHOTOS / "07_subtraction.jpg", "sub10", 7, "SUBTRACTION WITHIN 10", 33)
    p_pair(PHOTOS / "08_division.jpg", "div", 2, "DIVISION", 34)
    p_answers(PHOTOS / "09_answer_keys.jpg")
    p_included(PHOTOS / "10_what_you_get.jpg")
    p_uses(PHOTOS / "11_perfect_for.jpg")
    hero = Image.open(PHOTOS / "01_hero.jpg")
    sq = hero.crop(((W - H) // 2, 0, (W + H) // 2, H))
    for s in (300, 150):
        sq.resize((s, s), Image.LANCZOS).save(OUT / f"CHECK_thumb_{s}.png")
    print(f"{len(list(PHOTOS.glob('*.jpg')))} photos -> {PHOTOS}")


# ---------- text ----------

TITLE = ("Color by Code Math Worksheets, Addition Subtraction Multiplication Division, Self Checking "
         "Mystery Pictures, Printable Math Coloring")
TAGS = ["color by code", "color by number math", "math coloring pages", "mystery picture math",
        "addition worksheets", "subtraction practice", "multiplication facts", "division worksheet",
        "kindergarten math", "1st grade math", "3rd grade math", "homeschool math", "early finishers"]


def description():
    return """Math practice that kids actually want to finish! Every space in the picture holds a math problem. Solve it, find the answer in the color key and color the space with that crayon. When the answers are right, a cute mystery picture appears: a penguin, a squirrel, a camper van, a snowman and more. If a color looks wrong, there's a mistake to find, so every sheet checks itself.

4 LEVELS, SAME 10 PICTURES
- Addition to 10 (Kindergarten - Grade 1)
- Subtraction within 10 (Kindergarten - Grade 1)
- Multiplication facts (Grades 3 - 4)
- Division facts (Grades 3 - 4)
The whole class can color the same picture at their own level: easy differentiation with no extra prep.

WHAT YOU GET
- 4 printable PDFs, one per level, each with:
  - a teacher page (how it works, tips)
  - 10 color-by-code worksheets (one mystery picture per page)
  - answer keys: the finished pictures with the answer for every color, 4 per page
- 40 worksheets in total
- US Letter PDFs plus an A4 version of every level (zip)

KID-FRIENDLY DETAILS
- Only plain crayon colors, and each color's name is printed in the key (RED, ORANGE, BROWN, LIGHT BLUE ...)
- Problems are printed big and clear; tiny parts come already colored in
- Spaces with no problem simply stay white
- Name and date lines on every sheet
- Every problem was checked by computer against its color before the files were made

PERFECT FOR
Early finishers, math centers and stations, sub plans, homework, homeschool, fact fluency practice, winter break, holiday parties and calm Friday afternoons.

PLEASE NOTE
- This is a DIGITAL download. Nothing is shipped.
- Print at home or school on plain paper. Crayons or colored pencils work best.
- The colored pages in the photos show finished examples; the worksheets print in black and white with a colored key.
- For use in your own classroom or home: copy as many as you need for your students. Please don't share the files, upload them to other sites or resell them."""


def text():
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(TITLE) <= 140, len(TITLE)
    assert len(TAGS) == 13 and len(set(TAGS)) == 13 and all(len(t) <= 20 for t in TAGS), TAGS
    (OUT / "listing.json").write_text(json.dumps(dict(title=TITLE, tags=TAGS, description=description(),
                                                      price=PRICE), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"title {len(TITLE)} chars -> {OUT / 'listing.json'}")


# ---------- Etsy ----------

def files():
    return [LEVEL_PDF[s] for s, _, _ in MB.LEVELS] + [MB.OUT / "Color_by_Code_All_4_Levels_A4.zip"]


def upload():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state = OUT / "uploaded.json"
    if state.exists():
        sys.exit(f"already uploaded: {state.read_text()}")
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    sections = {s["title"]: s["shop_section_id"] for s in e.request("GET", f"/shops/{sid}/sections")["results"]}
    if SECTION not in sections:
        sections[SECTION] = e.request("POST", f"/shops/{sid}/sections", form={"title": SECTION})["shop_section_id"]
    listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
        "quantity": 999, "title": t["title"], "description": t["description"], "price": t["price"],
        "who_made": "i_did", "when_made": "2020_2026", "taxonomy_id": TAXONOMY, "type": "download",
        "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(t["tags"]),
        "shop_section_id": sections[SECTION]})
    lid = listing["listing_id"]
    state.write_text(json.dumps({"listing_id": lid}, indent=2))
    print("draft", lid, flush=True)
    for rank, p in enumerate(sorted(PHOTOS.glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    for rank, p in enumerate(files(), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": p.name}, files={"file": p})
    print("photos + 5 files uploaded", flush=True)
    print(f"https://www.etsy.com/your/shops/me/listing-editor/edit/{lid}")


def update():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    lid = json.loads((OUT / "uploaded.json").read_text())["listing_id"]
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    e.request("PATCH", f"/shops/{sid}/listings/{lid}", form={"title": t["title"], "description": t["description"],
                                                            "tags": ",".join(t["tags"])})
    old = [im["listing_image_id"] for im in e.request("GET", f"/listings/{lid}/images")["results"]]
    for image_id in old[1:]:            # Etsy: at least 1 image at all times, max 20
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
    for rank, p in enumerate(sorted(PHOTOS.glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    for image_id in old[:1]:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
    print(f"updated draft {lid}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"photos": photos, "text": text, "upload": upload, "update": update}.get(cmd, lambda: sys.exit(__doc__))()
