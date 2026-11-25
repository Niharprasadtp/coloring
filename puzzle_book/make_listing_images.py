"""Etsy listing photos built from the REAL book pages (no AI-drawn puzzles).

    python make_listing_images.py     -> output/listing/01_hero.jpg ... 05_pages.jpg

Run make_book.py first (it writes the PDFs these photos are cut from).
"""
from __future__ import annotations

import io
import math
import random
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import make_book as M

PDF = M.OUT / "Large_Print_Christmas_Puzzle_Book_Letter.pdf"
OUT = M.OUT / "listing"
W, H = 2667, 2000                       # 4:3, Etsy's recommended listing photo shape
CREAM = (253, 248, 240)
RED, DRED, GREEN, GOLD, INK, SOFT = (176, 22, 30), (130, 14, 22), (27, 94, 32), (201, 162, 39), (25, 25, 25), (85, 85, 85)
FONT_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"


def font(size, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, size)


_doc = None


def page(n: int, height: int) -> Image.Image:
    """Book page n (1-based) rendered so its height is `height` pixels."""
    global _doc
    _doc = _doc or pymupdf.open(PDF)
    p = _doc[n - 1]
    z = height / p.rect.height
    pix = p.get_pixmap(matrix=pymupdf.Matrix(z, z))
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def find_page(title: str) -> int:
    global _doc
    _doc = _doc or pymupdf.open(PDF)
    for i, p in enumerate(_doc):
        if title in p.get_text():
            return i + 1
    raise KeyError(title)


def background(seed=0) -> Image.Image:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    rng = random.Random(seed)
    for _ in range(26):                                   # faint snowflakes
        x, y, r = rng.randint(0, W), rng.randint(0, H), rng.randint(18, 46)
        for k in range(6):
            a = math.pi / 3 * k
            d.line([x, y, x + r * math.cos(a), y + r * math.sin(a)], fill=(226, 232, 238), width=4)
    return im


def paste_page(canvas, img, x, y, angle=0.0, border=0):
    """Paste a page with a soft drop shadow; (x, y) = top-left before rotation."""
    if border:
        framed = Image.new("RGB", (img.width + 2 * border, img.height + 2 * border), (210, 210, 210))
        framed.paste(img, (border, border)); img = framed
    img = img.convert("RGBA")
    if angle:
        img = img.rotate(angle, expand=True, resample=Image.BICUBIC)
    alpha = img.split()[-1]
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.35)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.paste(shadow, (x + 18, y + 26), shadow)
    canvas.paste(img, (x, y), img)


def pill(d, cx, cy, text, size, fill, fg=(255, 255, 255), pad=(44, 22)):
    f = font(size)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    w, h = r - l + 2 * pad[0], b - t + 2 * pad[1]
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=h / 2, fill=fill)
    d.text((cx, cy), text, font=f, fill=fg, anchor="mm")
    return w, h


def title_band(im, text, sub=None, color=RED):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 250 if sub else 210], fill=color)
    d.rectangle([0, (250 if sub else 210), W, (250 if sub else 210) + 12], fill=GOLD)
    d.text((W / 2, 105), text, font=font(112), fill="white", anchor="mm")
    if sub:
        d.text((W / 2, 205), sub, font=font(56, False), fill=(255, 236, 236), anchor="mm")
    return d


# ---------------------------------------------------------------- photos


def hero_v1():
    """First design (fanned pages, 4 badges). Kept for the phone comparison."""
    im = background(1)
    d = title_band(im, "LARGE PRINT Christmas Puzzle Book")
    ph = 1560
    left = page(find_page("Deck the Halls"), ph)
    mid = page(find_page("Mini Sudoku 1"), ph)
    right = page(find_page("Maze 1"), ph)
    paste_page(im, left, 120, 330, angle=5)
    paste_page(im, right, W - right.width - 200, 330, angle=-5)
    paste_page(im, mid, W // 2 - mid.width // 2, 300)
    # badges
    pill(d, 430, 1830, "52 PUZZLES", 92, RED)
    pill(d, W // 2, 1830, "ANSWER KEY INCLUDED", 80, GREEN)
    pill(d, W - 430, 1830, "INSTANT PDF", 92, RED)
    pill(d, W - 330, 330, "US LETTER + A4", 52, INK)
    return im


PINE, PINE_DK = (20, 72, 42), (14, 54, 31)


def p01_hero():
    """Thumbnail: dark background so white pages pop, big title, only 3 badges.
    Everything important sits inside the centre 2000x2000 square, so a square crop on mobile keeps it."""
    im = Image.new("RGB", (W, H), PINE)
    d = ImageDraw.Draw(im)
    rng = random.Random(7)
    for _ in range(40):                                   # subtle darker snowflakes
        x, y, r = rng.randint(0, W), rng.randint(0, H), rng.randint(20, 60)
        for k in range(6):
            a = math.pi / 3 * k
            d.line([x, y, x + r * math.cos(a), y + r * math.sin(a)], fill=PINE_DK, width=6)
    safe = (W - 2000) // 2                                # 333: left edge of the centre square
    # pages: word search behind, sudoku in front
    back = page(find_page("Deck the Halls"), 1480)
    front = page(find_page("Mini Sudoku 1"), 1560)
    paste_page(im, back, safe + 1080, 150, angle=-7)
    paste_page(im, front, safe + 900, 250, angle=3)
    # title: sized to the left column so it never runs onto the pages
    x, col_w = safe + 10, 830
    big = 240
    while max(d.textlength(t, font=font(big)) for t in ("Christmas", "Puzzle", "Book")) > col_w:
        big -= 4
    d.text((x, 300), "LARGE PRINT", font=font(int(big * 0.6)), fill=(242, 196, 70))
    for i, t in enumerate(("Christmas", "Puzzle", "Book")):
        d.text((x - 6, 420 + i * int(big * 1.12)), t, font=font(big), fill="white")
    # 3 badges, stacked, same width
    for i, (text, bg, fg) in enumerate([("52 PUZZLES", (200, 30, 40), "white"),
                                        ("INSTANT PDF", "white", PINE),
                                        ("LETTER + A4", "white", PINE)]):
        y = 1150 + i * 200
        d.rounded_rectangle([x, y, x + 760, y + 150], radius=75, fill=bg)
        d.text((x + 380, y + 76), text, font=font(84), fill=fg, anchor="mm")
    return im


def phone_preview(paths, out):
    """How thumbnails look in Etsy's mobile search grid (about 180 px wide at 2x)."""
    tw = 360
    th = int(tw * 3 / 4)
    cols = len(paths)
    S = Image.new("RGB", (cols * (tw + 40) + 40, th * 2 + 200), "white")
    d = ImageDraw.Draw(S)
    for i, p in enumerate(paths):
        img = Image.open(p)
        x = 40 + i * (tw + 40)
        d.text((x, 20), Path(p).stem, font=font(26), fill=INK)
        S.paste(img.resize((tw, th), Image.LANCZOS), (x, 70))                       # 4:3 grid
        sq = img.crop(((img.width - img.height) // 2, 0, (img.width + img.height) // 2, img.height))
        S.paste(sq.resize((th, th), Image.LANCZOS), (x + (tw - th) // 2, th + 120))  # square crop
    d.text((40, th + 80), "square crop (mobile app):", font=font(24, False), fill=SOFT)
    S.save(out)


def p02_checked():
    im = background(2)
    d = title_band(im, "Every Puzzle Checked by Computer", "No broken grids. No wrong answers.", GREEN)
    ph = 1180
    n_sud = find_page("Sudoku 2")
    n_maze = find_page("Maze 3")
    ans = [i + 1 for i, p in enumerate(_doc) if "Answers" in p.get_text()]
    n_sud_ans = next(a for a in ans if f"Page {n_sud}:" in _doc[a - 1].get_text())
    n_maze_ans = next(a for a in ans if f"Page {n_maze}:" in _doc[a - 1].get_text())
    y = 360
    insets = []
    for k, (q, a, label) in enumerate([(n_sud, n_sud_ans, "Sudoku"), (n_maze, n_maze_ans, "Maze")]):
        x = 90 + k * 1300
        pq = page(q, ph)
        paste_page(im, pq, x, y)
        # crop the matching solved grid out of the answer page (top or bottom half)
        full = page(a, ph * 2)
        top_half = f"Page {q}:" in _first_block_text(a)
        y0, y1 = (0.172, 0.53) if top_half else (0.566, 0.92)
        sol = trim(full.crop((0, int(full.height * y0), full.width, int(full.height * y1))), pad=24)
        sol = sol.resize((int(sol.width * 600 / sol.height), 600))
        insets.append((sol, x + pq.width - 200))
        pill(d, x + pq.width // 2, y + ph + 90, f"{label}  →  answer", 54, RED)
    for sol, sx in insets:                      # drawn last so no page covers them
        paste_page(im, sol, sx, y + 470, border=6)
        pill(d, sx + sol.width // 2, y + 450, "ANSWER", 44, GREEN)
    bullets = ["Each Sudoku: exactly one solution, no guessing",
               "Each maze: exactly one route",
               "Each word search word: appears exactly once"]
    for i, b in enumerate(bullets):
        d.text((W / 2, 1745 + i * 78), b, font=font(52), fill=INK, anchor="mm")
    return im


def trim(img, pad=0):
    """Crop away the white margin around the drawing."""
    from PIL import ImageChops
    box = ImageChops.difference(img, Image.new("RGB", img.size, "white")).getbbox()
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def _first_block_text(n):
    """Text of the top half of an answer page (to tell which half shows a given puzzle)."""
    p = _doc[n - 1]
    r = p.rect
    return p.get_text(clip=pymupdf.Rect(0, 0, r.width, r.height * 0.5))


def p03_inside():
    im = background(3)
    d = title_band(im, "What's Inside: 52 Puzzles", "Starts easy, gets a little harder as you go")
    items = [("Mini Sudoku 1", "6 Mini Sudoku"), ("Sudoku 3", "8 Sudoku"), ("Christmas Baking", "12 Word Searches"),
             ("Maze 4", "10 Mazes"), ("Carol Code-Breaker 3", "10 Carol Code-Breakers"),
             ("Christmas Word Scramble 1", "30 Word Scrambles")]
    ph = 700
    for i, (t, label) in enumerate(items):
        col, row = i % 3, i // 3
        pg = page(find_page(t), ph)
        x = 210 + col * 790
        y = 320 + row * 830
        paste_page(im, pg, x + (560 - pg.width) // 2 + 50, y)
        d.text((x + 330, y + ph + 50), label, font=font(54), fill=RED if row == 0 else GREEN, anchor="mm")
    return im


def p04_large_print():
    im = background(4)
    d = title_band(im, "Big, Bold, Easy-to-Read Print")
    pg = page(find_page("Winter Weather"), 3300)
    k = pg.height / 11.0                                  # pixels per inch (US Letter)
    cell = 6.9 / 13                                       # grid cell size in inches (see make_book.wordsearch)
    gx, gy = 0.8, 1.7                                     # grid top-left in inches from the page's top-left
    crop = pg.crop((int((gx - 0.12) * k), int((gy - 0.12) * k), int((gx + 7 * cell) * k), int((gy + 6 * cell) * k)))
    crop = crop.resize((1500, int(1500 * crop.height / crop.width)))
    paste_page(im, crop, 120, 380, border=4)
    x = 1730
    for i, line in enumerate(["One puzzle per page", "Large letters & numbers", "Bold grid lines",
                              "Prints well in", "black & white"]):
        d.text((x, 520 + i * 150 + (0 if i < 4 else -40)), line, font=font(68 if i < 3 else 60),
               fill=INK if i < 3 else SOFT)
    pill(d, x + 400, 1650, "76 PAGES", 80, GREEN)
    return im


def p05_pages():
    im = background(5)
    d = title_band(im, "76 Pages: US Letter & A4 PDFs", "Print at home as many times as you need")
    total = len(pymupdf.open(PDF))
    picks = [1, 2] + [find_page(t) for t in ("Number Patterns 1", "Christmas Word Scramble 2", "Sudoku 6",
                                             "Holiday Traditions", "Maze 8", "Carol Code-Breaker 9")] + \
            [total - 7, total - 2]
    ph = 760
    for i, n in enumerate(picks):
        col, row = i % 5, i // 5
        pg = page(n, ph)
        paste_page(im, pg, 120 + col * 500, 320 + row * 830)
    return im


PHOTOS = [p01_hero, p02_checked, p03_inside, p04_large_print, p05_pages]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for k, fn in enumerate(PHOTOS, 1):
        name = f"{k:02d}_{fn.__name__.split('_', 1)[1]}.jpg"
        fn().save(OUT / name, quality=92)
        print(OUT / name)
    hero_v1().save(OUT / "alt_hero_v1.jpg", quality=92)
    phone_preview([OUT / "alt_hero_v1.jpg", OUT / "01_hero.jpg"], OUT / "phone_preview.png")


if __name__ == "__main__":
    main()
