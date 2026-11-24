"""Best-seller style Etsy cover (4:3): numbered line-art background, big headline, hero iPad with palette,
eight more designs on the sides, page badge and zones/colors bars.

    python make_cover_bs.py            # writes listing/01_cover.jpg for every listing
"""

import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import make_listing_images as L
from make_cover import drop, font, hexes, pencil, rotate, rounded, straight_split
from make_listing_images import cover_crop, pil_from_bgr, save_jpg

W, H = 2667, 2000
INK = (52, 52, 58)


def frame(art, w, h, bez=26, r=46):
    """Dark tablet frame around art (RGBA)."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, fill=(150, 152, 158, 255))
    d.rounded_rectangle([4, 4, w - 5, h - 5], r - 4, fill=(20, 20, 24, 255))
    sw, sh = w - 2 * bez, h - 2 * bez
    img.paste(art.convert("RGB").resize((sw, sh)) if art.size != (sw, sh) else art.convert("RGB"),
              (bez, bez), rounded((sw, sh), max(8, r - bez)))
    return img


def palette_band(colors, w, h):
    band = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(band)
    per_row = (len(colors) + 1) // 2
    r = min(int(w / per_row / 2) - 5, int(h / 4) - 6)
    step = w / per_row
    for i, rgb in enumerate(colors):
        row, c = divmod(i, per_row)
        cx, cy = step * (c + 0.5), h * (0.28 + 0.46 * row)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb, outline=(225, 225, 225), width=2)
        ink = (255, 255, 255) if 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] < 150 else (40, 40, 40)
        f = font("segoeuib.ttf", int(r * 0.85))
        t = str(i + 1)
        d.text((cx - d.textlength(t, font=f) / 2, cy - r * 0.62), t, font=f, fill=ink)
    return band


def scallop_badge(w, h, count):
    pad = 40
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = img.width / 2, img.height / 2
    a, b = w / 2 - 40, h / 2 - 40
    d.ellipse([cx - a, cy - b, cx + a, cy + b], fill=(14, 14, 16, 255))
    for t in np.linspace(0, 2 * np.pi, 22, endpoint=False):
        x, y = cx + a * np.cos(t), cy + b * np.sin(t)
        d.ellipse([x - 52, y - 52, x + 52, y + 52], fill=(14, 14, 16, 255))
    f1, f2 = font("bahnschrift.ttf", 300, "Bold"), font("bahnschrift.ttf", 128, "Bold")
    t1, t2 = str(count), "PAGES"
    d.text((cx - d.textlength(t1, font=f1) / 2, cy - 225), t1, font=f1, fill="white")
    d.text((cx - d.textlength(t2, font=f2) / 2, cy + 62), t2, font=f2, fill="white")
    return img


def pill(text, fill, size=74):
    f = font("segoeuib.ttf", size)
    tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f)
    w, h = int(tw + 80), int(size * 1.55)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=fill + (255,))
    d.text((40, h * 0.12), text, font=f, fill="white")
    return img


def bar(text, fill, fg, h=150, size=112):
    f = font("bahnschrift.ttf", size, "Bold")
    tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=f)
    img = Image.new("RGBA", (int(tw + 70), h), fill + (255,))
    ImageDraw.Draw(img).text((35, (h - size) / 2 - 10), text, font=f, fill=fg)
    return img


def outlined(d, xy_center_x, y, text, f, fill, stroke=10):
    w = d.textlength(text, font=f)
    d.text((xy_center_x - w / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(255, 255, 255))


def magnifier(col, n, r=200):
    rect = col.rect(n)
    big = col.render(n, "Dark_Numbered")
    x0, y0, x1, y1 = rect
    cx, cy = x0 + int((x1 - x0) * 0.62), y0 + int((y1 - y0) * 0.55)
    s = 820
    crop = pil_from_bgr(big[cy - s // 2:cy + s // 2, cx - s // 2:cx + s // 2]).resize((2 * r, 2 * r), Image.LANCZOS)
    img = Image.new("RGBA", (2 * r + 30, 2 * r + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, img.width - 1, img.height - 1], fill=(20, 20, 22, 255))
    m = Image.new("L", crop.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, crop.width - 1, crop.height - 1], fill=255)
    img.paste(crop, (15, 15), m)
    return img


def bubble(text, fill, w=405, h=96, size=None):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=fill + (255,))
    r = h // 2 - 14
    cx, cy = 14 + r, h // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 255))
    d.line([(cx - r * 0.45, cy + 2), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.4)], fill=fill + (255,),
           width=8, joint="curve")
    if size is None:
        size = 46
        while d.textlength(text, font=font("segoeuib.ttf", size)) > w - 2 * r - 52:
            size -= 2
    f = font("segoeuib.ttf", size)
    d.text((2 * r + 34, (h - size * 1.33) / 2), text, font=f, fill="white")
    return img


FEATURES = [(".swatches palette", (32, 160, 190)), ("6 PNG styles", (232, 96, 70)),
            ("Print A4 PDF", (58, 132, 226)), ("SVG vectors", (124, 84, 190)),
            ("Palette sheet", (226, 150, 30)), ("Hex color codes", (40, 160, 110)),
            ("600 DPI hi-res", (210, 70, 120)), ("Instant download", (70, 90, 110))]


THEMES = {   # light top, light bottom, dark accent
    "cozy": ((253, 238, 222), (244, 204, 176), (156, 70, 42)),
    "wild": ((234, 243, 230), (196, 220, 194), (40, 92, 62)),
    "sunset": ((248, 230, 242), (220, 196, 234), (96, 52, 124)),
    "teal": ((228, 244, 244), (188, 222, 224), (22, 98, 110)),
}


def backdrop(col, hero, top, bottom):
    yy = np.linspace(0, 1, H)[:, None, None]
    grad = (np.array(top) * (1 - yy) + np.array(bottom) * yy) * np.ones((H, W, 3))
    page = col.style_img(hero, "Contour").convert("L")
    page = page.resize((W // 3, round(W / 3 * page.height / page.width)), Image.LANCZOS)
    tile = Image.new("L", (W, H), 255)
    for i in range(3):
        p = page if i % 2 == 0 else page.transpose(Image.FLIP_LEFT_RIGHT)
        tile.paste(p, (i * page.width, (H - page.height) // 2))
    lines = np.asarray(tile, np.float32)[..., None] / 255
    img = grad * (1 - 0.16 * (1 - lines))
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def ribbon(text, color, w=1950, h=230):
    notch, tail = 70, 120
    img = Image.new("RGBA", (w + 2 * tail, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    dark = tuple(int(c * 0.7) for c in color) + (255,)
    W2 = w + 2 * tail
    d.polygon([(0, 40), (tail + 10, 40), (tail + 10, h + 40), (0, h + 40), (notch, h / 2 + 40)], fill=dark)
    d.polygon([(W2, 40), (W2 - tail - 10, 40), (W2 - tail - 10, h + 40), (W2, h + 40), (W2 - notch, h / 2 + 40)],
              fill=dark)
    d.rectangle([tail, 0, tail + w, h], fill=color + (255,))
    d.polygon([(tail, h), (tail + 30, h + 40), (tail + 30, h)], fill=tuple(int(c * 0.45) for c in color) + (255,))
    d.polygon([(tail + w, h), (tail + w - 30, h + 40), (tail + w - 30, h)], fill=tuple(int(c * 0.45) for c in color) + (255,))
    f = font("bahnschrift.ttf", 176, "Bold")
    tw = d.textlength(text, font=f)
    d.text((tail + (w - tw) / 2, 8), text, font=f, fill="white")
    return img


def seal(count, fill=(232, 74, 52), r=245):
    img = Image.new("RGBA", (2 * r + 20, 2 * r + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = img.width / 2
    pts = []
    for i in range(48):
        a = np.pi * i / 24
        rr = r if i % 2 == 0 else r - 24
        pts.append((c + rr * np.cos(a), c + rr * np.sin(a)))
    d.polygon(pts, fill=fill + (255,))
    d.ellipse([c - r + 46, c - r + 46, c + r - 46, c + r - 46], outline=(255, 255, 255, 230), width=6)
    f1, f2 = font("bahnschrift.ttf", 230, "Bold"), font("bahnschrift.ttf", 84, "Bold")
    d.text((c - d.textlength(str(count), font=f1) / 2, c - 190), str(count), font=f1, fill="white")
    d.text((c - d.textlength("PAGES", font=f2) / 2, c + 52), "PAGES", font=f2, fill="white")
    return img


def stat_card(big, small, accent, w=780, h=170):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=(255, 255, 255, 255))
    d.ellipse([16, 16, h - 16, h - 16], fill=accent + (255,))
    size = 84
    while d.textlength(big, font=font("bahnschrift.ttf", size, "Bold")) > w - h - 40:
        size -= 4
    fb, fs = font("bahnschrift.ttf", size, "Bold"), font("segoeuib.ttf", 44)
    d.text((h + 10, 18 + (84 - size) * 0.6), big, font=fb, fill=INK)
    d.text((h + 12, 104), small, font=fs, fill=(110, 110, 115))
    return img


def make(col, hero, others, count, theme, designs, out, palette="teal", cards=None):
    """cards: optional [(big, small, rgb), x3] to replace the default zones / colors / iPad stat cards."""
    top, bottom, accent = THEMES[palette]
    canvas = backdrop(col, hero, top, bottom).convert("RGBA")

    # fanned tablets, 3 each side, outer ones lower and more tilted
    tw, th = 430, 560
    fan = [(-15, 40, 650), (-10, 300, 540), (-5, 560, 450)]
    for i, (ang, x, y) in enumerate(fan):
        for side, n in ((0, others[i]), (1, others[3 + i])):
            tab = rotate(frame(cover_crop(col.art(n), tw - 52, th - 52), tw, th), -ang if side else ang)
            px = x if side == 0 else W - x - tab.width
            drop(canvas, tab, (px, y), blur=18, offset=(10, 16), alpha=120)

    # hero iPad: split numbered / painted, palette under the art
    hw, hh, bez = 900, 1220, 28
    sw, sh = hw - 2 * bez, hh - 2 * bez
    band_h = 150
    screen = Image.new("RGB", (sw, sh), "white")
    screen.paste(straight_split(col, hero, sw, sh - band_h), (0, 0))
    screen.paste(palette_band(hexes(col, hero)[:30], sw, band_h), (0, sh - band_h))
    hx, hy = (W - hw) // 2, 420
    drop(canvas, frame(screen, hw, hh, bez=bez, r=60), (hx, hy), blur=34, offset=(20, 28), alpha=170)
    pen = rotate(pencil(820, 42), 52)
    drop(canvas, pen, (hx + hw - 330, hy + hh - pen.height - 120), blur=10, offset=(14, 20), alpha=130)

    # headline: theme in script, PAINT BY NUMBER on a ribbon
    d = ImageDraw.Draw(canvas)
    f = font("segoeprb.ttf", 112)
    tw_ = d.textlength(theme, font=f)
    d.text(((W - tw_) / 2, 0), theme, font=f, fill=accent, stroke_width=8, stroke_fill=(255, 255, 255))
    rib = ribbon("PAINT BY NUMBER", accent)
    drop(canvas, rib, ((W - rib.width) // 2, 165), blur=14, offset=(8, 12), alpha=110)

    # page seal on the hero's upper right corner
    sl = rotate(seal(count), 10)
    drop(canvas, sl, (hx - sl.width // 2 + 30, hy + 20), blur=16, offset=(10, 14), alpha=120)

    # feature bubbles: 2 x 2 on each side under the fanned tablets
    bw, bh, gx, gy = 405, 96, 18, 22
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bsize = 48
    while max(probe.textlength(t, font=font("segoeuib.ttf", bsize)) for t, _ in FEATURES) > bw - 2 * (bh // 2 - 14) - 52:
        bsize -= 2
    for i, (text, fill) in enumerate(FEATURES):
        side, k = divmod(i, 4)
        r_, c_ = divmod(k, 2)
        x0 = 40 if side == 0 else W - 40 - 2 * bw - gx
        drop(canvas, bubble(text, fill, bw, bh, bsize), (x0 + c_ * (bw + gx), 1400 + r_ * (bh + gy)),
             blur=8, offset=(4, 7), alpha=90)

    # stat cards
    stats = [col.stats[n] for n in designs if col.stats.get(n)]
    zl, zh = min(s[0] for s in stats), max(s[0] for s in stats)
    cl, ch = min(s[1] for s in stats), max(s[1] for s in stats)
    cards = ([stat_card(big, small, rgb) for big, small, rgb in cards] if cards else
             [stat_card(f"{round(zl, -1):,}-{round(zh, -2):,}", "numbered zones", (255, 196, 30)),
              stat_card(f"{cl}-{ch} colors", "own palette per page", (30, 186, 150)),
              stat_card("iPad + Print", "Procreate & paper", (70, 130, 230))])
    gap = 40
    total = sum(c.width for c in cards) + gap * 2
    x = (W - total) // 2
    for c in cards:
        drop(canvas, c, (x, 1720), blur=12, offset=(6, 10), alpha=100)
        x += c.width + gap
    return save_jpg(canvas.convert("RGB"), out)


JOBS = {
    "output/sets/Set1_Cozy_Cottage_Winter/listing": dict(
        hero=26, others=[20, 25, 45, 23, 28, 27, 24, 19], theme="Cozy Cottage", count=15, palette="cozy",
        designs=[5, 7, 19, 20, 23, 24, 25, 26, 27, 28, 32, 36, 38, 44, 45]),
    "output/sets/Set2_Wildlife_Scenic_Nature/listing": dict(
        hero=1, others=[8, 22, 46, 35, 21, 37, 6, 40], theme="Wildlife & Nature", count=15, palette="wild",
        designs=[1, 2, 3, 6, 8, 21, 22, 34, 35, 37, 39, 40, 41, 42, 46]),
    "output/sets/Set3_Sunsets_Travel/listing": dict(
        hero=29, others=[11, 31, 12, 30, 13, 43, 16, 9], theme="Sunsets & Travel", count=15, palette="sunset",
        designs=[4, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 29, 30, 31, 43]),
    "output/listing": dict(
        hero=31, others=[1, 26, 8, 12, 21, 37, 30, 11], theme="Realistic & Cozy", count=46, palette="teal",
        designs=list(range(1, 47))),
}


def main():
    col = L.Collection(Path("input"), Path("output/collection"))
    only = sys.argv[1:]
    for folder, c in JOBS.items():
        if only and not any(o in folder for o in only):
            continue
        folder = Path(folder)
        cur, keep = folder / "01_cover.jpg", folder / "zz_cover_v3.jpg"
        if cur.exists() and not keep.exists():
            shutil.copy(cur, keep)
        make(col, c["hero"], c["others"], c["count"], c["theme"], c["designs"], cur, c["palette"])
        print(cur)


if __name__ == "__main__":
    sys.exit(main())
