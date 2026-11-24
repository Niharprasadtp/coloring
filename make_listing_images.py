"""Etsy listing photos (2667x2000 JPG, under 1 MB) built from the finished collection.

    python make_listing_images.py -i input -c output/collection -o output/listing
"""

import argparse
import math
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from build_collection import clean_image
from cbn import cli

W, H = 2667, 2000
CREAM, PEACH = (255, 246, 233), (255, 226, 205)
TEAL, CORAL, MUSTARD, PLUM, INK = (31, 122, 116), (232, 85, 62), (242, 182, 50), (75, 46, 90), (43, 43, 43)
FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


def background(seed=0):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, H)[:, None, None]
    base = (np.array(CREAM) * (1 - t) + np.array(PEACH) * t) * np.ones((H, W, 3))
    img = Image.fromarray(base.astype(np.uint8))
    blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(blobs)
    for color in (TEAL, CORAL, MUSTARD, (150, 190, 170)):
        for _ in range(3):
            cx, cy, r = int(rng.integers(0, W)), int(rng.integers(0, H)), int(rng.integers(160, 420))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (46,))
    img.paste(blobs.filter(ImageFilter.GaussianBlur(70)), (0, 0), blobs.filter(ImageFilter.GaussianBlur(70)))
    return img.convert("RGB")


def shadowed(canvas, img, xy, border=14, radius=18, angle=0):
    """Paste img with a white border and drop shadow at top-left xy."""
    img = img.convert("RGB")
    framed = Image.new("RGB", (img.width + 2 * border, img.height + 2 * border), "white")
    framed.paste(img, (border, border))
    mask = Image.new("L", framed.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, framed.width - 1, framed.height - 1], radius, fill=255)
    layer = Image.new("RGBA", framed.size)
    layer.paste(framed, (0, 0), mask)
    layer.putalpha(mask)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    x, y = xy
    sh = Image.new("RGBA", (layer.width + 120, layer.height + 120), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 110), (60, 74), layer.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    canvas.paste(sh, (x - 60, y - 60), sh)
    canvas.paste(layer, (x, y), layer)
    return layer.size


def tag(canvas, text, right, top, fill, fg, size=34):
    d = ImageDraw.Draw(canvas)
    f = font("segoeuib", size)
    tw = d.textlength(text, font=f)
    box = [right - tw - 36, top, right, top + size + 26]
    d.rounded_rectangle(box, 8, fill=fill)
    d.text((box[0] + 18, top + 9), text, font=f, fill=fg)


def text_c(canvas, text, cx, y, f, fill, stroke=0, stroke_fill=None):
    d = ImageDraw.Draw(canvas)
    tw = d.textlength(text, font=f)
    d.text((cx - tw / 2, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def text_l(canvas, text, x, y, f, fill):
    ImageDraw.Draw(canvas).text((x, y), text, font=f, fill=fill)


def starburst(canvas, cx, cy, r, fill, points=20):
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points
        rr = r if i % 2 == 0 else r * 0.88
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    ImageDraw.Draw(canvas).polygon(pts, fill=fill)


def banner(canvas, text, y, fill=TEAL, fg="white", size=52):
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, y, W, y + size + 50], fill=fill)
    text_c(canvas, text, W / 2, y + 22, font("segoeuib", size), fg)


def save_jpg(img, path, max_bytes=980_000):
    for q in range(94, 50, -4):
        img.save(path, "JPEG", quality=q, optimize=True, subsampling=0 if q > 85 else 2, dpi=(72, 72))
        if Path(path).stat().st_size <= max_bytes:
            return q
    return q


def cover_crop(img, w, h):
    """Fill w x h with img (PIL), cropping the overflow around the center."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def pil_from_bgr(a):
    return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))


CHRISTMAS = {19, 24, 25, 32}   # fireplace, winter village, gingerbread, Christmas cottage: not shown in the listing


class Collection:
    def __init__(self, inp, root):
        self.files = cli.find_images(inp)
        self.root = root
        self.stats = {}
        for n in range(1, len(self.files) + 1):
            rep = root / f"Design_{n:02d}" / "report.txt"
            if rep.exists():
                text = rep.read_text(encoding="utf-8")
                m = re.search(r"(\d+) regions", text)
                c = re.search(r"Palette: (\d+) colors", text)
                self.stats[n] = (int(m.group(1)), int(c.group(1))) if m and c else None
        self._art = {}

    def art(self, n):
        """Original artwork (sparkle removed) as PIL."""
        if n not in self._art:
            img, _ = clean_image(self.files[n - 1])
            self._art[n] = pil_from_bgr(img)
        return self._art[n]

    def render(self, n, style):
        path = self.root / f"Design_{n:02d}" / "PNG" / f"{style}.png"
        return cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)

    def rect(self, n):
        """Bounding box of the artwork on the 4961x7016 renders (from the full-coverage navigation map)."""
        nav = self.render(n, "Navigation_Map")
        small = nav[::8, ::8]
        ys, xs = np.where((small < 250).any(axis=2))
        return xs.min() * 8, ys.min() * 8, (xs.max() + 1) * 8, (ys.max() + 1) * 8

    def style_img(self, n, style, rect=None):
        x0, y0, x1, y1 = rect or self.rect(n)
        return pil_from_bgr(self.render(n, style)[y0:y1, x0:x1])

    def tiles(self, ns, size):
        """Pre-sized artwork cards."""
        return {n: cover_crop(self.art(n), *size) for n in ns}


def grid_image(col, ns, title, subtitle, out, rows=2, cols=4, seed=0):
    img = background(seed)
    cw, ch = 560, 746
    gap = 34
    tw = cols * cw + (cols - 1) * gap
    x0 = (W - tw) // 2
    text_c(img, title, W / 2, 28, font("georgiab", 118), PLUM)
    text_c(img, subtitle, W / 2, 168, font("segoeuib", 54), CORAL)
    tiles = col.tiles(ns, (cw, ch))
    y0 = 262
    for i, n in enumerate(ns):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gap), y0 + r * (ch + gap + 14)
        shadowed(img, tiles[n], (x, y), border=12)
        if col.stats.get(n):
            regions, colors = col.stats[n]
            tag(img, f"{colors} COLORS", x + cw + 12 - 4, y + 22, TEAL, "white", 32)
            tag(img, f"{round(regions, -1):,} ZONES", x + cw + 12 - 4, y + 22 + 70, MUSTARD, INK, 32)
    banner(img, "INSTANT DOWNLOAD  •  PROCREATE  •  PRINTABLE  •  PNG  PDF  SVG", H - 118)
    return save_jpg(img, out)


NAMES = {5: "Antique Desk Still Life", 1: "Red Fox in Snow", 8: "Barn Owl in the Oak",
         31: "Greek Alley & Cat", 37: "Alpine Lake Cabin", 6: "Highland Cattle"}


def tag_zones(col, img, n, x, y, cw):
    if col.stats.get(n):
        regions, colors = col.stats[n]
        tag(img, f"{colors} COLORS", x + cw + 8, y + 22, TEAL, "white", 32)
        tag(img, f"{round(regions, -1):,} ZONES", x + cw + 8, y + 92, MUSTARD, INK, 32)


def cover(col, ns, out):
    img = background(1)
    cw, ch, gap = 555, 740, 34
    cols = 3
    x0 = W - 90 - (cols * cw + (cols - 1) * gap)
    text_c(img, "PAINT BY NUMBER COLLECTION", W / 2, 26, font("georgiab", 112), PLUM)
    tiles = col.tiles(ns, (cw, ch))
    y0 = 200
    for i, n in enumerate(ns):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gap), y0 + r * (ch + gap + 14)
        shadowed(img, tiles[n], (x, y), border=12)
        tag_zones(col, img, n, x, y, cw)
    # left panel
    starburst(img, 410, 480, 300, CORAL)
    text_c(img, str(len(col.files)), 410, 330, font("impact", 250), "white")
    text_c(img, "PAGES", 410, 590, font("segoeuib", 100), "white")
    for i, (line, f_, color) in enumerate([("Realistic  •  Cozy  •  Travel", "segoeuib", PLUM),
                                           ("Procreate iPad", "georgiab", CORAL),
                                           ("+ Printable", "georgiab", CORAL)]):
        text_c(img, line, 410, 880 + i * 105 - (20 if i else 0), font(f_, 52 if i == 0 else 78), color)
    for i, ln in enumerate(["6 PNG styles per page", "PDF  +  SVG  +  .swatches", "Up to 34 colors each"]):
        text_c(img, ln, 410, 1260 + i * 80, font("segoeui", 48), INK)
    banner(img, "INSTANT DOWNLOAD  •  PNG  PDF  SVG  •  PROCREATE PALETTE INCLUDED", H - 118)
    return save_jpg(img, out)


def featured_image(col, ns, title, subtitle, out, seed=0):
    img = background(seed)
    cw, ch, gap = 780, 1040, 62
    x0 = (W - (3 * cw + 2 * gap)) // 2
    text_c(img, title, W / 2, 24, font("georgiab", 112), PLUM)
    text_c(img, subtitle, W / 2, 158, font("segoeuib", 52), CORAL)
    tiles = col.tiles(ns, (cw, ch))
    y = 250
    for i, n in enumerate(ns):
        x = x0 + i * (cw + gap)
        shadowed(img, tiles[n], (x, y), border=14)
        tag_zones(col, img, n, x, y, cw)
        text_c(img, NAMES.get(n, f"Design {n}"), x + cw / 2 + 14, y + ch + 52, font("georgiab", 58), PLUM)
    banner(img, "REALISTIC DETAIL  •  EVERY PAGE WITH ITS OWN COLOR PALETTE", H - 118)
    return save_jpg(img, out)


TAGLINES = {5: "A brass telescope, a quill and a handwritten letter in warm candlelight.",
            1: "A red fox in a sunlit birch forest, every strand of fur painted by number.",
            8: "A barn owl watching from its mossy hollow, with ferns and ivy all around.",
            31: "Whitewashed steps, bougainvillea and a curious cat above the blue Aegean.",
            37: "Golden larches, a glassy turquoise lake and a cosy wooden cabin.",
            6: "Shaggy Highland cattle on a heather moor beside an old stone wall."}


def wrap(draw, text, f, width):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def spotlight(col, n, out, seed=0):
    img = background(30 + seed)
    rect = col.rect(n)
    cw, ch = 1000, 1333
    shadowed(img, cover_crop(col.art(n), cw, ch), (150, 240), border=16)
    x = 1330
    d = ImageDraw.Draw(img)
    text_l(img, "FEATURED DESIGN", x, 250, font("segoeuib", 46), CORAL)
    for i, line in enumerate(wrap(d, NAMES[n], font("georgiab", 100), 1250)):
        text_l(img, line, x, 320 + i * 118, font("georgiab", 100), PLUM)
    y = 320 + 118 * len(wrap(d, NAMES[n], font("georgiab", 100), 1250)) + 20
    for i, line in enumerate(wrap(d, TAGLINES[n], font("segoeui", 48), 1250)):
        text_l(img, line, x, y + i * 66, font("segoeui", 48), INK)
    y += 66 * len(wrap(d, TAGLINES[n], font("segoeui", 48), 1250)) + 30
    if col.stats.get(n):
        regions, colors = col.stats[n]
        for j, (big, small, fill, fg) in enumerate([(f"{round(regions, -1):,}", "ZONES", MUSTARD, INK),
                                                    (str(colors), "COLORS", TEAL, "white")]):
            bx = x + j * 330
            d.rounded_rectangle([bx, y, bx + 300, y + 190], 26, fill=fill)
            text_c(img, big, bx + 150, y + 14, font("impact", 100), fg)
            text_c(img, small, bx + 150, y + 126, font("segoeuib", 42), fg)
    ty = 1330
    thumbs = [("Numbered", col.style_img(n, "Dark_Numbered", rect)), ("Color map", col.style_img(n, "Navigation_Map", rect)),
              ("Palette", col.style_img(n, "Palette_Numbered"))]
    for j, (label, pic) in enumerate(thumbs):
        tx = x + j * 400
        shadowed(img, cover_crop(pic, 340, 453) if j < 2 else pic.resize((340, 453)), (tx, ty), border=8)
        text_c(img, label, tx + 178, ty + 480, font("segoeuib", 38), TEAL)
    banner(img, "INCLUDED: 6 PNG STYLES  •  A4 PDF  •  SVG  •  PROCREATE PALETTE", H - 118)
    return save_jpg(img, out)


def terms_image(out, rows=None):
    img = background(40)
    text_c(img, "GOOD TO KNOW", W / 2, 28, font("georgiab", 120), PLUM)
    rows = rows or [("1", "Instant digital download", "No waiting. Your files are ready right after checkout."),
            ("2", "Download link inside the PDF", "Open the PDF from Etsy to get all your files."),
            ("3", "Print at home or at a print shop", "A4 print-ready. Print again and again for yourself."),
            ("4", "Paint digitally on your iPad", "Works great in Procreate. Palette file included."),
            ("5", "For personal use only", "No physical item is shipped. Files are not for resale."),
            ("6", "Questions? Just message me", "Happy to help with downloads and file questions.")]
    colors = [CORAL, TEAL, MUSTARD, PLUM, (90, 150, 90), (60, 110, 170)]
    d = ImageDraw.Draw(img)
    for i, (num, head, sub) in enumerate(rows):
        r, c = divmod(i, 2)
        x, y = 140 + c * 1220, 290 + r * 440
        d.rounded_rectangle([x, y, x + 1170, y + 360], 40, fill=(255, 255, 255))
        d.ellipse([x + 40, y + 90, x + 220, y + 270], fill=colors[i])
        text_c(img, num, x + 130, y + 100, font("impact", 120), "white" if i != 2 else INK)
        text_l(img, head, x + 260, y + 90, font("segoeuib", 54), INK)
        for k, line in enumerate(wrap(d, sub, font("segoeui", 42), 860)):
            text_l(img, line, x + 260, y + 170 + k * 56, font("segoeui", 42), (80, 80, 80))
    banner(img, "THANK YOU FOR SHOPPING  •  HAPPY PAINTING", H - 118)
    return save_jpg(img, out)


def detail_image(col, n, center, size, title, out):
    """Original | color map | numbered line art of the same small area (proves the detail is kept)."""
    img = background(13)
    rect = col.rect(n)
    x0, y0, x1, y1 = rect
    art = col.art(n)
    k = (x1 - x0) / art.width
    cx, cy = center
    h2 = size // 2
    orig = art.crop((cx - h2, cy - h2, cx + h2, cy + h2))
    rx, ry, rs = int(x0 + cx * k), int(y0 + cy * k), int(h2 * k)
    panels = []
    for style in ("Navigation_Map", "Dark_Numbered"):
        panels.append(pil_from_bgr(col.render(n, style)[ry - rs:ry + rs, rx - rs:rx + rs]))
    pw = 780
    gap = 55
    x = (W - (3 * pw + 2 * gap)) // 2
    text_c(img, "EVERY DETAIL IS KEPT", W / 2, 24, font("georgiab", 112), PLUM)
    text_c(img, "Even the eyes: close-up of the same area on the original, color map and numbered page", W / 2,
           158, font("segoeuib", 46), CORAL)
    for i, (pic, label) in enumerate(zip([orig] + panels, ["ORIGINAL", "COLOR MAP", "NUMBERED PAGE"])):
        shadowed(img, pic.resize((pw, pw), Image.LANCZOS), (x + i * (pw + gap), 330), border=14)
        text_c(img, label, x + i * (pw + gap) + pw / 2 + 14, 330 + pw + 50, font("segoeuib", 60), TEAL)
    for i, ln in enumerate(["Dark rims, irises and highlights get their own numbers",
                            "Smooth outlines that stay sharp when you zoom"]):
        text_c(img, ln, W / 2, 1330 + 90 + i * 100, font("segoeui", 58), INK)
    banner(img, "WHAT YOU SEE IS WHAT YOU PAINT  •  HIGH-RESOLUTION 4961 x 7016 PX", H - 118)
    return save_jpg(img, out)


def styles_image(col, n, out):
    img = background(2)
    rect = col.rect(n)
    names = [("Dark_Numbered", "Dark Numbered"), ("Light_Numbered", "Light Numbered"),
             ("Shadow_Numbered", "Shadow Guide"), ("Navigation_Map", "Color Map"),
             ("Palette_Numbered", "With Palette"), ("Contour", "Contour (no numbers)")]
    cw, ch, gap = 500, 667, 40
    for i, (style, label) in enumerate(names):
        r, c = divmod(i, 3)
        x, y = 70 + c * (cw + gap + 24), 250 + r * (ch + gap + 80)
        card = col.style_img(n, style, rect if style != "Palette_Numbered" else None)
        shadowed(img, cover_crop(card, cw, ch) if style != "Palette_Numbered" else card.resize((cw, ch)),
                 (x, y), border=10)
        text_c(img, label, x + cw / 2 + 10, y + ch + 34, font("segoeuib", 42), PLUM)
    text_c(img, "6 PNG STYLES", 2667 - 470, 330, font("georgiab", 84), PLUM)
    text_c(img, "in EVERY design", 2667 - 470, 445, font("georgiab", 84), CORAL)
    lines = ["Dark & light numbered line art", "Shadow guide: faded color hint", "Full-color number map",
             "Palette printed under the art", "Clean contour, no numbers", "4961 x 7016 px (A4 at 600 DPI)"]
    for i, ln in enumerate(lines):
        text_l(img, "•  " + ln, 1830, 620 + i * 92, font("segoeui", 46), INK)
    banner(img, "SHARP LINES  •  READABLE NUMBERS  •  EVERY DESIGN", H - 118)
    return save_jpg(img, out)


def before_after(col, n, out):
    img = background(3)
    rect = col.rect(n)
    left = col.style_img(n, "Dark_Numbered", rect)
    right = col.art(n)
    ch = 1250
    cw = round(ch * 0.75)
    L, R = cover_crop(left, cw, ch), cover_crop(right, cw, ch)
    text_c(img, "FROM NUMBERS TO MASTERPIECE", W / 2, 30, font("georgiab", 112), PLUM)
    text_c(img, "Match each number to its color and paint", W / 2, 165, font("segoeuib", 54), CORAL)
    xl, xr, y = 250, W - 250 - cw - 28, 310
    shadowed(img, L, (xl, y))
    shadowed(img, R, (xr, y))
    cx = W // 2
    d = ImageDraw.Draw(img)
    d.polygon([(cx - 130, y + ch / 2 - 60), (cx + 40, y + ch / 2 - 60), (cx + 40, y + ch / 2 - 130),
               (cx + 150, y + ch / 2), (cx + 40, y + ch / 2 + 130), (cx + 40, y + ch / 2 + 60),
               (cx - 130, y + ch / 2 + 60)], fill=CORAL)
    text_c(img, "NUMBERED PAGE", xl + cw / 2 + 14, y + ch + 50, font("segoeuib", 56), TEAL)
    text_c(img, "FINISHED PAINTING", xr + cw / 2 + 14, y + ch + 50, font("segoeuib", 56), TEAL)
    banner(img, "INSTANT DOWNLOAD  •  PRINT OR PAINT ON YOUR iPAD", H - 118)
    return save_jpg(img, out)


def ipad_image(col, n, out):
    img = background(4)
    rect = col.rect(n)
    colored = col.art(n)
    line = col.style_img(n, "Dark_Numbered", rect)
    sw, sh = 920, 1226
    frame = 40
    fx, fy = 170, 250
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([fx, fy, fx + sw + 2 * frame, fy + sh + 2 * frame], 64, fill=(25, 25, 30))
    screen_img = cover_crop(colored, sw, sh)
    line_img = cover_crop(line, sw, sh)
    mask = Image.new("L", (sw, sh), 0)
    md = ImageDraw.Draw(mask)
    md.polygon([(0, 0), (int(sw * 0.62), 0), (int(sw * 0.44), sh), (0, sh)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    composed = Image.composite(screen_img, line_img, mask)
    base = Image.new("RGB", (sw + 2 * frame, sh + 2 * frame), (25, 25, 30))
    base.paste(composed, (frame, frame))
    bmask = Image.new("L", base.size, 0)
    ImageDraw.Draw(bmask).rounded_rectangle([0, 0, base.width - 1, base.height - 1], 64, fill=255)
    img.paste(base, (fx, fy), bmask)
    text_l(img, "PAINT ON YOUR iPAD", 1300, 270, font("georgiab", 112), PLUM)
    text_l(img, "Works great in Procreate", 1300, 410, font("segoeuib", 62), CORAL)
    for i, ln in enumerate(["Import the PNG line art", "Load the one-tap .swatches palette",
                            "Tap a color, fill the number", "Zoom in for fine detail",
                            "Undo mistakes, paint again & again"]):
        text_l(img, "•  " + ln, 1300, 560 + i * 100, font("segoeui", 54), INK)
    # magnifier on the numbers
    big = col.render(n, "Dark_Numbered")
    x0, y0, x1, y1 = rect
    cx0, cy0 = x0 + (x1 - x0) // 2, y0 + (y1 - y0) // 2
    crop = pil_from_bgr(big[cy0 - 520:cy0 + 520, cx0 - 520:cx0 + 520]).resize((620, 620), Image.LANCZOS)
    m = Image.new("L", crop.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, crop.width - 1, crop.height - 1], fill=255)
    mx, my = 1560, 1130
    ring = Image.new("RGBA", (crop.width + 40, crop.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, ring.width - 1, ring.height - 1], fill=CORAL + (255,))
    shadowed_circle = ring.filter(ImageFilter.GaussianBlur(0))
    img.paste(shadowed_circle, (mx - 20, my - 20), shadowed_circle)
    img.paste(crop, (mx, my), m)
    banner(img, "PNG + PROCREATE .SWATCHES PALETTE  •  NO PHYSICAL ITEM SHIPPED", H - 118)
    return save_jpg(img, out)


def included_image(col, n, out, rows=None):
    img = background(5)
    text_c(img, "WHAT'S INCLUDED", W / 2, 28, font("georgiab", 118), PLUM)
    count = getattr(col, "count", len(col.files))
    rows = rows or [("PNG", TEAL, f"{count} designs  •  6 styles each", "4961 x 7016 px, ready for Procreate"),
            ("PDF", CORAL, "A4 print-ready pages", "Dark, light, shadow & palette versions"),
            ("SVG", PLUM, "Scalable vector files", "Numbered dark & light, any size"),
            (".SW", MUSTARD, "Procreate palette (.swatches)", "One-tap import, colors in number order"),
            ("PAL", (90, 150, 90), "Printable color palette sheet", "PNG + SVG with hex codes"),
            ("HEX", (60, 110, 170), "Hex code list", "For any other painting app")]
    for i, (badge, color, head, sub) in enumerate(rows):
        y = 260 + i * 245
        ImageDraw.Draw(img).rounded_rectangle([150, y, 330, y + 170], 28, fill=color)
        text_c(img, badge, 240, y + 48, font("impact", 74 if len(badge) < 4 else 62), "white")
        text_l(img, head, 380, y + 22, font("segoeuib", 60), INK)
        text_l(img, sub, 380, y + 98, font("segoeui", 46), (90, 90, 90))
    rect = col.rect(n)
    cards = [col.style_img(n, "Dark_Numbered", rect), col.style_img(n, "Navigation_Map", rect),
             col.style_img(n, "Palette_Numbered")]
    for i, c in enumerate(cards):
        w_, h_ = 440, 587
        shadowed(img, cover_crop(c, w_, h_) if i < 2 else c.resize((w_, h_)),
                 (1560 + (i % 2) * 500, 330 + (i // 2) * 700 + (i % 2) * 110), border=10, angle=-4 + i * 4)
    banner(img, "ONE DOWNLOAD  •  EVERYTHING YOU NEED  •  PRINT OR PAINT DIGITALLY", H - 118)
    return save_jpg(img, out)


def howto_image(col, n, out, steps=None):
    img = background(6)
    text_c(img, "HOW IT WORKS", W / 2, 28, font("georgiab", 124), PLUM)
    steps = steps or [("1", "Download", "Open the link in your PDF and download your files instantly."),
             ("2", "Print or open on iPad", "Print the A4 PDF, or import the PNG into Procreate."),
             ("3", "Load the palette", "Tap the .swatches file to add the numbered colors."),
             ("4", "Paint by number", "Match each number to its color. Relax and enjoy!")]
    for i, (num, head, sub) in enumerate(steps):
        y = 270 + i * 375
        d = ImageDraw.Draw(img)
        d.ellipse([170, y + 5, 370, y + 205], fill=[CORAL, TEAL, MUSTARD, PLUM][i])
        text_c(img, num, 270, y + 18, font("impact", 130), "white" if i != 2 else INK)
        d.rounded_rectangle([430, y - 10, 1760, y + 230], 40, fill=(255, 255, 255))
        text_l(img, head, 480, y + 20, font("segoeuib", 70), INK)
        text_l(img, sub, 480, y + 118, font("segoeui", 44), (80, 80, 80))
    rect = col.rect(n)
    line = col.style_img(n, "Palette_Numbered")
    shadowed(img, line.resize((740, 1000)), (1830, 330), border=12, angle=3)
    text_c(img, "Tip: in Procreate set the line art to Multiply", 2667 - 400, 1500, font("segoeuib", 38), TEAL)
    text_c(img, "and paint on a layer underneath.", 2667 - 400, 1552, font("segoeuib", 38), TEAL)
    banner(img, "BEGINNER FRIENDLY  •  NO SKILLS NEEDED  •  PRINT AS OFTEN AS YOU LIKE", H - 118)
    return save_jpg(img, out)


def zones_image(col, out):
    img = background(7)
    ranked = sorted((v[0], n) for n, v in col.stats.items() if v and n not in CHRISTMAS)
    lo, hi = ranked[0][0], ranked[-1][0]
    text_c(img, "EASY TO EXPERT", W / 2, 28, font("georgiab", 124), PLUM)
    text_c(img, f"From about {round(lo, -1):,} to {round(hi, -2):,} zones, so there's a page for every mood",
           W / 2, 170, font("segoeuib", 52), CORAL)
    picks = [("RELAXING", TEAL, ranked[1]), ("MEDIUM", MUSTARD, ranked[len(ranked) // 2]),
             ("EXPERT", CORAL, ranked[-2])]
    cw, ch = 760, 1013
    for i, (label, color, (regions, n)) in enumerate(picks):
        x = 150 + i * (cw + 95) - 12
        shadowed(img, cover_crop(col.art(n), cw, ch), (x, 300), border=12)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x, 300 + ch + 70, x + cw + 24, 300 + ch + 230], 30, fill=color)
        text_c(img, label, x + cw / 2 + 12, 300 + ch + 82, font("impact", 80), "white" if i != 1 else INK)
        text_c(img, f"~{round(regions, -1):,} zones", x + cw / 2 + 12, 300 + ch + 166, font("segoeuib", 48),
               "white" if i != 1 else INK)
    banner(img, "CHOOSE YOUR CHALLENGE  •  CLEARLY NUMBERED ZONES", H - 118)
    return save_jpg(img, out)


def closeup_image(col, n, out):
    img = background(8)
    rect = col.rect(n)
    big = col.render(n, "Dark_Numbered")
    x0, y0, x1, y1 = rect
    cx0, cy0 = x0 + int((x1 - x0) * 0.5), y0 + int((y1 - y0) * 0.55)
    s = 760
    crop = pil_from_bgr(big[cy0 - s // 2:cy0 + s // 2, cx0 - s // 2:cx0 + s // 2]).resize((1500, 1500), Image.LANCZOS)
    shadowed(img, crop, (140, 250), border=16)
    text_l(img, "CRISP LINES", 1760, 340, font("georgiab", 64), PLUM)
    text_l(img, "READABLE NUMBERS", 1760, 430, font("georgiab", 64), CORAL)   # larger runs off the right edge
    for i, ln in enumerate(["Smooth vector outlines", "Clear numbered regions", "Sharp at A4 print size",
                            "Zoom in on iPad, still crisp", "Verified: each number matches", "its color"]):
        text_l(img, "•  " + ln if i < 5 else "    " + ln, 1760, 650 + i * 92, font("segoeui", 50), INK)
    thumb = col.style_img(n, "Dark_Numbered", rect).resize((300, 400))
    shadowed(img, thumb, (1790, 1250), border=8)
    td = ImageDraw.Draw(img)
    fx, fy = 1790 + 8 + int(300 * (cx0 - x0) / (x1 - x0)), 1250 + 8 + int(400 * (cy0 - y0) / (y1 - y0))
    rw, rh = int(300 * s / (x1 - x0)), int(400 * s / (y1 - y0))
    td.rectangle([fx - rw // 2, fy - rh // 2, fx + rw // 2, fy + rh // 2], outline=CORAL, width=6)
    text_l(img, "Zoomed area", 2130, 1400, font("segoeuib", 44), TEAL)
    banner(img, "A4 AT 600 DPI  •  4961 x 7016 PX PNG", H - 118)
    return save_jpg(img, out)


def palette_image(col, n, out):
    img = background(9)
    hexes = (col.root / f"Design_{n:02d}" / "Hex_Codes.txt").read_text().split("\n")
    colors = [tuple(int(h.split("#")[1][i:i + 2], 16) for i in (0, 2, 4)) for h in hexes if "#" in h]
    text_c(img, "A COLOR PALETTE FOR EVERY PAGE", W / 2, 28, font("georgiab", 104), PLUM)
    text_c(img, "Procreate .swatches  •  printable palette sheet  •  hex codes", W / 2, 158,
           font("segoeuib", 52), CORAL)
    d = ImageDraw.Draw(img)
    per_row = 8
    for i, rgb in enumerate(colors):
        r, c = divmod(i, per_row)
        cx, cy = 330 + c * 290, 440 + r * 330
        d.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=rgb, outline=(255, 255, 255), width=10)
        ink = (255, 255, 255) if 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2] < 140 else (30, 30, 30)
        text_c(img, str(i + 1), cx, cy - 44, font("segoeuib", 84), ink)
        text_c(img, "#%02X%02X%02X" % rgb, cx, cy + 140, font("segoeui", 36), (70, 70, 70))
    banner(img, "ONE-TAP IMPORT INTO PROCREATE  •  NUMBERS MATCH THE PAGE", H - 118)
    return save_jpg(img, out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-c", "--collection", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    col = Collection(a.input, a.collection)

    hero = [5, 1, 8, 31, 37, 6]
    plan = {
        "01_cover.jpg": lambda o: cover(col, hero, o),
        "02_featured_realistic.jpg": lambda o: featured_image(col, [5, 1, 8], "REALISTIC MASTERPIECES",
                                                              "Wildlife and still life, painted by number", o, seed=21),
        "03_featured_scenery.jpg": lambda o: featured_image(col, [31, 37, 6], "SCENERY YOU CAN PAINT",
                                                            "Travel, mountains and highlands", o, seed=22),
        "04_detail_eyes.jpg": lambda o: detail_image(col, 1, (1300, 1085), 520, "", o),
        "05_before_after.jpg": lambda o: before_after(col, 39, o),
        "06_ipad.jpg": lambda o: ipad_image(col, 8, o),
        "07_six_styles.jpg": lambda o: styles_image(col, 31, o),
        "08_spotlight_fox.jpg": lambda o: spotlight(col, 1, o, 1),
        "09_spotlight_owl.jpg": lambda o: spotlight(col, 8, o, 2),
        "10_spotlight_desk.jpg": lambda o: spotlight(col, 5, o, 3),
        "11_spotlight_greek_alley.jpg": lambda o: spotlight(col, 31, o, 4),
        "12_spotlight_alpine_lake.jpg": lambda o: spotlight(col, 37, o, 5),
        "13_spotlight_highland_cattle.jpg": lambda o: spotlight(col, 6, o, 6),
        "14_included.jpg": lambda o: included_image(col, 31, o),
        "15_how_it_works.jpg": lambda o: howto_image(col, 31, o),
        "16_difficulty.jpg": lambda o: zones_image(col, o),
        "17_travel_nature.jpg": lambda o: grid_image(col, [30, 33, 14, 11, 12, 17, 43, 29],
                                                     "TRAVEL & NATURE", "Coasts, forests, aurora skies and more", o, seed=11),
        "18_cozy_fantasy.jpg": lambda o: grid_image(col, [26, 27, 23, 45, 28, 20, 22, 44],
                                                    "COZY & FANTASY", "Reading nooks, potions, gardens and still life", o, seed=12),
        "19_palette.jpg": lambda o: palette_image(col, 1, o),
        "20_good_to_know.jpg": lambda o: terms_image(o),
    }
    for name, fn in plan.items():
        out = a.output / name
        q = fn(out)
        print(f"{name}: {out.stat().st_size / 1024:.0f} KB (quality {q})")


if __name__ == "__main__":
    sys.exit(main())
