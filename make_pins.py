"""Pinterest pins (1000x1500) for every active Etsy listing + a posting schedule.

    .venv/Scripts/python make_pins.py fetch   # download listing photos + titles from Etsy -> output/pinterest/src
    .venv/Scripts/python make_pins.py         # build pins -> output/pinterest/pins + pins_schedule.csv

Two pins per listing: A = the listing cover, B = the "numbered page -> finished painting" image.
"""

import csv
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "pinterest"
SRC = OUT / "src"
PINS = OUT / "pins"
SHOP = "SpellbindinTreasures"
SHOP_ID = 68520525
PW, PH = 1000, 1500
CREAM, PEACH = (255, 246, 233), (255, 226, 205)
TEAL, CORAL, MUSTARD, PLUM, INK = (31, 122, 116), (232, 85, 62), (242, 182, 50), (75, 46, 90), (43, 43, 43)
FONTS = Path("C:/Windows/Fonts")
START = dt.date(2026, 11, 23)
PER_DAY = 4

CUSTOM_ID = 4621704930
B_RANK = {CUSTOM_ID: 2, 4617315630: 4}   # which photo shows "numbers -> painting"; default by type below


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


# ---------- data ----------

def fetch():
    import etsy_api as e
    SRC.mkdir(parents=True, exist_ok=True)
    meta = []
    for l in e.request("GET", f"/shops/{SHOP_ID}/listings/active", params={"limit": 100})["results"]:
        lid = l["listing_id"]
        files = []
        for im in e.request("GET", f"/listings/{lid}/images")["results"][:5]:
            f = SRC / f"{lid}_{im['rank']}.jpg"
            if not f.exists():
                req = urllib.request.Request(im["url_fullxfull"], headers={"User-Agent": "Mozilla/5.0"})
                f.write_bytes(urllib.request.urlopen(req, timeout=60).read())
            files.append(f.name)
        meta.append(dict(id=lid, title=l["title"], tags=l["tags"], price=l["price"]["amount"] // 100,
                         url=l["url"].split("?")[0], files=files, views=l["views"]))
    (OUT / "listings.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(meta), "listings")


def kind(m):
    if m["id"] == CUSTOM_ID:
        return "custom"
    return "single" if m["price"] <= 200 else "book"


def theme(m):
    t = m["title"].lower()
    if m["id"] == CUSTOM_ID:
        return "custom"
    if re.search(r"christmas|winter|gingerbread|snow|hygge|fireplace", t):
        return "christmas"
    if re.search(r"\bcars?\b|jdm|supercar|truck|muscle|garage", t):
        return "cars"
    if re.search(r"owl|fox|wolf|wildlife|woodland|animal|cats|dogs", t):
        return "animals"
    if re.search(r"travel|landscape|beach|ocean|mountain|paris|amalfi|northern|sunset|cottage|village", t):
        return "travel"
    return "general"


BOARDS = {"custom": "Custom Photo Paint by Number Gifts", "christmas": "Christmas Paint by Number & Coloring",
          "cars": "Car Paint by Number & Coloring Pages", "animals": "Animal Paint by Number",
          "travel": "Landscape & Travel Paint by Number", "general": "Procreate Paint by Number"}

HOOKS = {"custom": "Turn your photo into a paint by number",
         "christmas": "Cozy coloring for winter nights",
         "cars": "Paint your dream car, number by number",
         "animals": "Watch it come to life, number by number",
         "travel": "Paint your way around the world",
         "general": "From numbers to masterpiece"}


def headline(m):
    h = m["title"].split(",")[0].strip()
    return re.sub(r"\s+(PDF|iPad)$", "", h)


def pin_title(m):
    parts = [p.strip() for p in m["title"].split(",")]
    t = parts[0]
    for p in parts[1:]:
        if len(t) + 2 + len(p) > 100:
            break
        t += ", " + p
    return t


def description(m, variant):
    k, th = kind(m), theme(m)
    head = headline(m)
    if k == "custom":
        body = ("Send any photo you love (family, pet, couple, a favorite place) and get your own numbered color by "
                "number page within 24 hours. Color it in Procreate on your iPad or print it at home. Make it a "
                "mystery gift: the picture only appears as they color! Perfect Christmas and personalized gift.")
    else:
        what = "a whole book of pages" if k == "book" else "one detailed design"
        body = (f"{head}: {what} you can paint in Procreate on your iPad or print at home. Instant digital download, "
                "every page has its own numbered color palette. A relaxing, screen-free hobby for adults and a "
                "lovely gift for anyone who loves to color.")
    if variant == "b" and k != "custom":
        body = "From numbered page to finished painting. " + body
    tags = ["paintbynumber", "procreate", "colorbynumber", "coloringpages"]
    tags += {"custom": ["customgift", "photogift"], "christmas": ["christmascoloring"], "cars": ["carart"],
             "animals": ["animalart"], "travel": ["landscapeart"], "general": []}[th]
    text = body + " " + " ".join("#" + t for t in tags)
    return text[:500]


# ---------- drawing ----------

def gradient():
    t = np.linspace(0, 1, PH)[:, None, None]
    base = (np.array(CREAM) * (1 - t) + np.array(PEACH) * t) * np.ones((PH, PW, 3))
    return Image.fromarray(base.astype(np.uint8))


def wrap(d, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def fit_text(d, text, name, size, width, max_lines):
    while size > 30:
        f = font(name, size)
        lines = wrap(d, text, f, width)
        if len(lines) <= max_lines and all(d.textlength(l, font=f) <= width for l in lines):
            return f, lines
        size -= 4
    f = font(name, size)
    return f, wrap(d, text, f, width)[:max_lines]


def center(d, text, y, f, fill):
    w = d.textlength(text, font=f)
    d.text(((PW - w) / 2, y), text, font=f, fill=fill)


def paste_photo(canvas, img, box):
    x0, y0, bw, bh = box
    img = img.convert("RGB")
    if img.width / img.height > bw / bh:          # wide photo: trim up to 6% per side so it fills more
        cut = min(int(img.width * 0.06), (img.width - int(img.height * bw / bh)) // 2)
        img = img.crop((cut, 0, img.width - cut, img.height))
    s = min(bw / img.width, bh / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = x0 + (bw - img.width) // 2
    y = y0 + (bh - img.height) // 2
    r = 22
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], r, fill=255)
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x + 6, y + 12, x + img.width + 6, y + img.height + 12], r,
                                         fill=(60, 30, 20, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    canvas.paste(sh, (0, 0), sh)
    canvas.paste(img, (x, y), mask)
    return y + img.height


def pill(d, text, cx, y, f, fill, fg, padx=26, pady=14):
    w = d.textlength(text, font=f)
    box = [cx - w / 2 - padx, y, cx + w / 2 + padx, y + f.size + 2 * pady]
    d.rounded_rectangle(box, (box[3] - box[1]) / 2, fill=fill)
    d.text((cx - w / 2, y + pady - 2), text, font=f, fill=fg)
    return box[3]


def make_pin(m, variant, out):
    k, th = kind(m), theme(m)
    accent = PLUM if variant == "b" else TEAL
    canvas = gradient().convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # header
    kicker = {"custom": "CUSTOM  ·  FROM YOUR PHOTO", "book": "PAINT BY NUMBER BOOK",
              "single": "PAINT BY NUMBER"}[k] + "  ·  PROCREATE + PRINTABLE"
    if k == "custom":
        kicker = "CUSTOM  ·  PROCREATE + PRINTABLE"
    fk = font("segoeuib", 30)
    center(d, kicker, 52, fk, CORAL)
    big = HOOKS[th] if variant == "b" else headline(m)
    f, lines = fit_text(d, big, "georgiab", 86, PW - 100, 3)
    y = 104
    for ln in lines:
        center(d, ln, y, f, INK)
        y += int(f.size * 1.18)
    if variant == "b" and k != "custom":
        fs, sub = fit_text(d, headline(m), "segoeui", 36, PW - 140, 1)
        center(d, sub[0], y + 4, fs, accent)
        y += fs.size + 16
    top = y + 26

    # photo
    rank = B_RANK.get(m["id"], 2 if k == "single" else 5) if variant == "b" else 1
    name = f"{m['id']}_{rank}.jpg"
    if name not in m["files"]:
        name = m["files"][0]
    photo = Image.open(SRC / name)
    block = 230                                   # perks + button + shop name, anchored at the bottom
    area_top, area_bot = top, PH - block - 70
    pw_img = photo.width - 2 * int(photo.width * 0.06) if photo.width / photo.height > (PW - 60) / (area_bot - area_top) else photo.width
    h_img = min(area_bot - area_top, round(photo.height * (PW - 60) / pw_img))
    slack = (area_bot - area_top - h_img) // 2
    bottom = paste_photo(canvas, photo, (30, area_top + slack, PW - 60, h_img))

    # benefits + CTA
    d = ImageDraw.Draw(canvas)
    perks = {"custom": ["Your own photo", "Ready in 24 hours", "Mystery reveal gift"],
             "book": ["Instant download", "iPad + print", "Every page own palette"],
             "single": ["Instant download", "iPad + print", "Numbered palette"]}[k]
    fb = font("segoeuib", 28)
    y = bottom + 40 + slack
    widths = [d.textlength(p, font=fb) + 44 for p in perks]
    gap = 14
    x = (PW - sum(widths) - gap * (len(perks) - 1)) / 2
    for p, w in zip(perks, widths):
        d.rounded_rectangle([x, y, x + w, y + 54], 27, fill=(255, 255, 255), outline=accent, width=3)
        d.text((x + 22, y + 10), p, font=fb, fill=accent)
        x += w + gap
    cta = "Get yours on Etsy  →" if k == "custom" else "Shop the download on Etsy  →"
    yb = pill(d, cta, PW / 2, y + 84, font("segoeuib", 40), CORAL, "white", padx=40, pady=20)
    center(d, SHOP, yb + 18, font("segoeui", 28), (110, 90, 80))
    canvas.convert("RGB").save(out, "JPEG", quality=90, optimize=True)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def build():
    meta = json.loads((OUT / "listings.json").read_text(encoding="utf-8"))
    PINS.mkdir(parents=True, exist_ok=True)
    for f in PINS.glob("*.jpg"):
        f.unlink()
    # Christmas first (season), custom photo kit early, then the rest by views; B pins after all A pins.
    order = {"christmas": 0, "custom": 0, "cars": 1, "animals": 1, "travel": 2, "general": 2}
    meta.sort(key=lambda m: (order[theme(m)], -m["views"]))
    rows = []
    for variant in ("a", "b"):
        for m in meta:
            n = len(rows) + 1
            fname = f"{n:02d}_{slug(headline(m))}_{variant}.jpg"
            make_pin(m, variant, PINS / fname)
            day = START + dt.timedelta(days=(n - 1) // PER_DAY)
            rows.append({"day": day.isoformat(), "file": fname, "board": BOARDS[theme(m)],
                         "title": pin_title(m), "description": description(m, variant), "link": m["url"],
                         "alt_text": f"{headline(m)} digital paint by number page"})
            print(fname, flush=True)
    with open(OUT / "pins_schedule.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "pins ->", PINS)


if __name__ == "__main__":
    fetch() if sys.argv[1:] == ["fetch"] else build()
