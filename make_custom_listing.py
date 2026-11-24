"""Etsy draft listing for the custom "mystery photo" color by number (made to order from the buyer's photo).

    .venv/Scripts/python make_custom_listing.py build    # photos + order-instructions PDF + listing.json
    .venv/Scripts/python make_custom_listing.py upload   # create the Etsy DRAFT (once; id kept in uploaded.json)

Examples are built first with custom_photo.py into output/custom_examples/<name>/<level>/ from the
CC0 / public-domain photos in input_photos/examples (see LICENSES.txt there).
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

import make_listing_images as L
from cbn import package
from make_listing_images import (CORAL, INK, MUSTARD, PLUM, TEAL, H, W, background, banner, cover_crop, font,
                                 save_jpg, shadowed, text_c, text_l, wrap)

ROOT = Path(__file__).resolve().parent
EX = ROOT / "output" / "custom_examples"
PHOTOS_IN = ROOT / "input_photos" / "examples"
OUT = ROOT / "output" / "custom_listing"
HERO = "tabby"        # levels, included, close-up
COVER = "pierfamily"
EXAMPLES = ["corgi", "frenchie", "tabby", "beachdog", "bulldog"]
PRICES = {"Relaxing - 16 colors": 299, "Standard - 24 colors": 299, "Detailed - 36 colors": 399}  # cut from 599/599/699 on 2026-11-22


# ---------- example assets ----------

def original(name):
    return ImageOps.exif_transpose(Image.open(PHOTOS_IN / f"{name}.jpg")).convert("RGB")


def kit(name, level="standard"):
    return EX / name / level


def finished(name, level="standard"):
    return Image.open(kit(name, level) / "2_REVEAL_Answer_Key" / "Finished_Picture.png").convert("RGB")


def numbered(name, level="standard", style="Dark_Numbered"):
    """The numbered line art cropped to exactly the finished picture's frame."""
    fin = finished(name, level)
    page = Image.open(kit(name, level) / "1_Color_This" / f"{style}.png").convert("RGB")
    w, h = fin.size
    s = min(package.PNG_W * (1 - 2 * package.PAGE_MARGIN) / w, package.PNG_H * (1 - 2 * package.PAGE_MARGIN) / h)
    x0, y0 = round((package.PNG_W - w * s) / 2), round((package.PNG_H - h * s) / 2)
    return page.crop((x0, y0, x0 + round(w * s), y0 + round(h * s))).resize((w, h), Image.LANCZOS)


def split(name, w, h, level="standard", left_colored=False, slant=0.12):
    """Same crop of the numbered page and the finished picture, joined along a slanted line."""
    col, line = cover_crop(finished(name, level), w, h), cover_crop(numbered(name, level), w, h)
    mask = Image.new("L", (w, h), 0)
    a, b = int(w * (0.5 + slant)), int(w * (0.5 - slant))
    ImageDraw.Draw(mask).polygon([(a, 0), (w, 0), (w, h), (b, h)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(4))
    return Image.composite(line, col, mask) if left_colored else Image.composite(col, line, mask)


def polaroid(photo, w, angle=-6):
    """Original photo as a little printed snapshot."""
    ph = cover_crop(photo, w, w)
    pad, bottom = round(w * 0.07), round(w * 0.24)
    card = Image.new("RGB", (w + 2 * pad, w + pad + bottom), (252, 252, 248))
    card.paste(ph, (pad, pad))
    layer = Image.new("RGBA", card.size)
    layer.paste(card)
    layer.putalpha(255)
    return layer.rotate(angle, expand=True, resample=Image.BICUBIC)


def paste_shadow(canvas, layer, xy, blur=18, offset=(14, 20), alpha=120):
    x, y = xy
    sh = Image.new("RGBA", (layer.width + 100, layer.height + 100), (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (50 + offset[0], 50 + offset[1]), layer.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(sh, (x - 50, y - 50), sh)
    canvas.paste(layer, (x, y), layer)


def pill(canvas, text, x, y, fill, fg, size=46):
    d = ImageDraw.Draw(canvas)
    f = font("segoeuib", size)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + 60, y + size + 40], (size + 40) // 2, fill=fill)
    d.text((x + 30, y + 14), text, font=f, fill=fg)
    return tw + 60


def arrow(canvas, x0, x1, y, color=CORAL, width=16):
    d = ImageDraw.Draw(canvas)
    d.line([(x0, y), (x1 - 30, y)], fill=color, width=width)
    d.polygon([(x1, y), (x1 - 46, y - 32), (x1 - 46, y + 32)], fill=color)


# ---------- photos ----------

def p1_cover(out):
    """Thumbnail: the art fills the frame, half numbered / half colored, original photo pinned in the corner."""
    img = split(COVER, W, H, slant=0.06)
    snap = polaroid(original(COVER), 560, angle=-7)
    paste_shadow(img, snap, (60, 50))
    pill(img, "YOUR PHOTO  →  COLOR BY NUMBER", 70, H - 150, (255, 255, 255), PLUM, size=54)
    pill(img, "DIGITAL", W - 330, 60, TEAL, "white", size=50)
    return save_jpg(img.convert("RGB"), out)


def fit(img, w, h):
    s_ = min(w / img.width, h / img.height)
    return img.resize((round(img.width * s_), round(img.height * s_)), Image.LANCZOS)


def examples_image(names, title, out, seed, labels=None, levels=None):
    """2x2 grid: each result (half numbered, half colored) with its original photo pinned on the corner."""
    img = background(seed)
    text_c(img, title, W / 2, 30, font("georgiab", 112), PLUM)
    text_c(img, "Family, pets, couples, travel and landscapes: send the photo you love", W / 2, 170,
           font("segoeui", 50), INK)
    cell_w, cell_h = 1180, 780
    for i, name in enumerate(names):
        r, c = divmod(i, 2)
        cx, cy = 150 + c * 1250 + cell_w // 2, 270 + r * 810 + cell_h // 2
        lvl = levels[i] if levels else "standard"
        res = fit(finished(name, lvl), cell_w - 40, cell_h - 40)
        art = split(name, res.width, res.height, level=lvl, slant=0.06)
        shadowed(img, art, (cx - art.width // 2 + 40, cy - art.height // 2), border=10)
        snap = polaroid(original(name), 300, angle=-8 if c == 0 else 7)
        paste_shadow(img, snap, (cx - art.width // 2 - 40, cy + art.height // 2 - snap.height + 30))
        if labels:
            d = ImageDraw.Draw(img)
            tw = d.textlength(labels[i], font=font("segoeuib", 44))
            pill(img, labels[i], round(cx + art.width // 2 + 20 - tw - 60), cy - art.height // 2 + 10,
                 [CORAL, TEAL, PLUM, MUSTARD][i], "white" if i != 3 else INK, size=44)
    banner(img, "EVERY PAGE IS MADE FROM YOUR OWN PHOTO  •  UNIQUE GIFT", H - 118)
    return save_jpg(img, out)


def p_examples_big(out):
    """Two large before/after pairs."""
    img = background(21)
    text_c(img, "FROM YOUR PHOTO...", W / 2, 20, font("georgiab", 100), PLUM)
    text_c(img, "YOUR PHOTO", 630, 150, font("segoeuib", 48), TEAL)
    text_c(img, "YOUR COLOR BY NUMBER", 2000, 150, font("segoeuib", 48), TEAL)
    for i, name in enumerate(["kids", "couple"]):
        y = 230 + i * 800
        ph = cover_crop(original(name), 1000, 740)
        shadowed(img, ph, (130, y), border=12)
        arrow(img, 1200, 1400, y + 370)
        shadowed(img, split(name, 1000, 740, level="detailed", slant=0.06), (1500, y), border=12)
    banner(img, "...TO A COLOR BY NUMBER PAGE, READY IN 24 HOURS", H - 118)
    return save_jpg(img, out)


def p_mystery(out):
    img = background(31)
    text_c(img, "A MYSTERY GIFT", W / 2, 30, font("georgiab", 120), PLUM)
    text_c(img, "They won't know what the picture is until they color it in!", W / 2, 185,
           font("segoeui", 54), INK)
    w_, h_ = 760, 1010
    xs = [150, 953, 1757]
    shadowed(img, cover_crop(numbered("beachdog", style="Light_Numbered"), w_, h_), (xs[0], 330), border=12)
    shadowed(img, split("beachdog", w_, h_, slant=0.0), (xs[1], 330), border=12)
    shadowed(img, cover_crop(finished("beachdog"), w_, h_), (xs[2], 330), border=12)
    for x, t in zip(xs, ["1. A page of numbers", "2. Something appears...", "3. The big reveal!"]):
        text_c(img, t, x + w_ / 2 + 12, 1385, font("segoeuib", 54), TEAL)
    text_c(img, "The answer key comes in a separate folder, so no spoilers.", W / 2, 1520,
           font("segoeui", 50), INK)
    text_c(img, "Perfect for Christmas, birthdays, anniversaries and pet lovers.", W / 2, 1600,
           font("segoeui", 50), INK)
    banner(img, "FAMILY  •  PETS  •  COUPLES  •  TRAVEL  •  LANDSCAPES", H - 118)
    return save_jpg(img, out)


def p_levels(out):
    img = background(12)
    text_c(img, "CHOOSE YOUR LEVEL", W / 2, 30, font("georgiab", 118), PLUM)
    w_, h_ = 740, 1040
    for i, (lvl, label, sub, fill) in enumerate([("relaxing", "RELAXING", "16 colors • bigger areas", TEAL),
                                                ("standard", "STANDARD", "24 colors • most popular", CORAL),
                                                ("detailed", "DETAILED", "36 colors • more detail", PLUM)]):
        x = 150 + i * 803
        shadowed(img, split(HERO, w_, h_, level=lvl, slant=0.0), (x, 250), border=12)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([x, 1350, x + w_ + 24, 1560], 36, fill=fill)
        text_c(img, label, x + w_ / 2 + 12, 1365, font("impact", 100), "white")
        text_c(img, sub, x + w_ / 2 + 12, 1478, font("segoeuib", 46), "white")
    banner(img, "SAME PHOTO, THREE LEVELS  •  PICK ONE AT CHECKOUT", H - 118)
    return save_jpg(img, out)


def p_included(out):
    img = background(5)
    text_c(img, "WHAT YOU GET", W / 2, 28, font("georgiab", 118), PLUM)
    rows = [("PDF", CORAL, "US Letter, A4 & 16x20 poster PDFs", "Print at home or at a print shop"),
            ("PNG", TEAL, "Numbered pages for Procreate / iPad", "Dark, light-gray & with-palette styles"),
            (".SW", MUSTARD, "Procreate palette (.swatches)", "One tap to load the numbered colors"),
            ("KEY", PLUM, "Numbered color swatch card", "Plus hex codes for any app or marker"),
            ("SVG", (90, 150, 90), "Scalable line art", "Light-gray lines that vanish under paint"),
            ("?!", (60, 110, 170), "Separate answer key folder", "The finished picture, kept a secret")]
    for i, (badge, color, head, sub) in enumerate(rows):
        y = 250 + i * 245
        ImageDraw.Draw(img).rounded_rectangle([150, y, 330, y + 170], 28, fill=color)
        text_c(img, badge, 240, y + 48, font("impact", 74), "white")
        text_l(img, head, 380, y + 22, font("segoeuib", 58), INK)
        text_l(img, sub, 380, y + 98, font("segoeui", 46), (90, 90, 90))
    pal = Image.open(kit(HERO) / "1_Color_This" / "Palette_Numbered.png").convert("RGB")
    shadowed(img, pal.resize((640, 905)), (1820, 270), border=10, angle=4)
    shadowed(img, cover_crop(numbered(HERO, style="Light_Numbered"), 520, 690), (1620, 1010), border=10, angle=-5)
    banner(img, "ONE ZIP  •  EVERYTHING YOU NEED  •  PRINT OR PAINT DIGITALLY", H - 118)
    return save_jpg(img, out)


def p_how_to_order(out):
    img = background(6)
    text_c(img, "HOW TO ORDER", W / 2, 28, font("georgiab", 124), PLUM)
    steps = [("1", "Choose your level & buy", "Relaxing, Standard or Detailed."),
             ("2", "Send your photo", "Attach it in Etsy Messages right after checkout."),
             ("3", "I make your page", "Every photo is checked by hand before it goes out."),
             ("4", "Get your download link", "Within 24 hours, straight to your Etsy Messages.")]
    d = ImageDraw.Draw(img)
    for i, (num, head, sub) in enumerate(steps):
        y = 260 + i * 375
        d.ellipse([170, y + 5, 370, y + 205], fill=[CORAL, TEAL, MUSTARD, PLUM][i])
        text_c(img, num, 270, y + 18, font("impact", 130), "white" if i != 2 else INK)
        d.rounded_rectangle([430, y - 10, 1800, y + 230], 40, fill=(255, 255, 255))
        text_l(img, head, 480, y + 20, font("segoeuib", 70), INK)
        text_l(img, sub, 480, y + 118, font("segoeui", 46), (80, 80, 80))
    snap = polaroid(original("tabby"), 520, angle=5)
    paste_shadow(img, snap, (1930, 300))
    starburst_y = 1330
    L.starburst(img, 2230, starburst_y, 250, CORAL)
    text_c(img, "READY", 2230, starburst_y - 120, font("impact", 90), "white")
    text_c(img, "IN 24H", 2230, starburst_y - 20, font("impact", 110), "white")
    banner(img, "SEND YOUR PHOTO IN ETSY MESSAGES AFTER CHECKOUT", H - 118)
    return save_jpg(img, out)


def p_photo_tips(out):
    img = background(14)
    text_c(img, "PHOTO TIPS", W / 2, 28, font("georgiab", 124), PLUM)
    tips = [("Bright & sharp", "Daylight works best. Avoid blurry or dark photos."),
            ("Clear subject", "Your family, pet or view should fill most of the photo."),
            ("Original file", "Send the full-size photo, not a screenshot."),
            ("About faces", "Faces become simple color shapes. Full-body, scenic and pet photos look best.")]
    d = ImageDraw.Draw(img)
    for i, (head, sub) in enumerate(tips):
        y = 280 + i * 360
        d.ellipse([160, y + 20, 300, y + 160], fill=(90, 150, 90))
        d.line([(195, y + 92), (225, y + 125), (270, y + 60)], fill="white", width=18)
        text_l(img, head, 350, y + 20, font("segoeuib", 70), INK)
        for k, ln in enumerate(wrap(d, sub, font("segoeui", 48), 1150)):
            text_l(img, ln, 350, y + 110 + k * 60, font("segoeui", 48), (80, 80, 80))
    shadowed(img, cover_crop(original("pierfamily"), 700, 930), (1720, 280), border=14, angle=-3)
    text_c(img, "Not sure? Send it anyway,", 2080, 1340, font("segoeuib", 50), TEAL)
    text_c(img, "I'll tell you before I start.", 2080, 1405, font("segoeuib", 50), TEAL)
    banner(img, "A GOOD PHOTO MAKES A BEAUTIFUL PAGE", H - 118)
    return save_jpg(img, out)


def p_closeup(out):
    img = background(9)
    text_c(img, "CRISP LINES, CLEAR NUMBERS", W / 2, 30, font("georgiab", 104), PLUM)
    line = numbered(HERO)
    col = finished(HERO)
    w, h = line.size
    bw, bh = int(w * 0.34), int(w * 0.34 * 0.7)    # around the cat's left eye
    x0, y0 = int(w * 0.36) - bw // 2, int(h * 0.47) - bh // 2
    box = (x0, y0, x0 + bw, y0 + bh)
    z1 = line.crop(box).resize((1150, 805), Image.LANCZOS)
    z2 = col.crop(box).resize((1150, 805), Image.LANCZOS)
    shadowed(img, z1, (130, 300), border=12)
    shadowed(img, z2, (1380, 300), border=12)
    text_c(img, "Zoomed in on the numbered page", 715, 1160, font("segoeuib", 50), TEAL)
    text_c(img, "The same spot, colored in", 1965, 1160, font("segoeuib", 50), TEAL)
    text_c(img, "Tiny areas that are too small to paint are merged away, so every", W / 2, 1300,
           font("segoeui", 52), INK)
    text_c(img, "space is big enough for its number and for your pencil or brush.", W / 2, 1370,
           font("segoeui", 52), INK)
    banner(img, "MARKERS  •  COLORED PENCILS  •  PAINT  •  PROCREATE", H - 118)
    return save_jpg(img, out)


TERMS = [("1", "Made to order from your photo", "Send your photo in Etsy Messages after checkout."),
         ("2", "Ready within 24 hours", "You get a download link in your Etsy Messages."),
         ("3", "Your photo stays private", "Used only for your order, deleted after delivery."),
         ("4", "Print again and again", "US Letter, A4 & 16x20 poster PDFs included."),
         ("5", "Digital item, nothing shipped", "For personal use. Please don't resell the files."),
         ("6", "Not happy? Message me", "I'll redo it with a different photo or level.")]


# ---------- desk mockups (real generator output on a kraft-paper desk) ----------

import numpy as np

TERRA = (186, 104, 74)


def kraft_bg(seed=0, tone=(214, 196, 168)):
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 7, (H // 2, W // 2, 1))
    fibers = rng.normal(0, 5, (H // 2, W // 2, 1))
    base = np.array(tone, np.float32) + noise + fibers * np.array([1.0, 0.9, 0.8])
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return img.filter(ImageFilter.GaussianBlur(0.8))


def palette_of(name, level="standard"):
    rows = (kit(name, level) / "1_Color_This" / "Hex_Codes.txt").read_text().split()
    return [(int(rows[i]), tuple(int(rows[i + 1][k:k + 2], 16) for k in (1, 3, 5))) for i in range(0, len(rows), 2)]


def pencil(length, color, w=48):
    """A colored pencil pointing right, as RGBA."""
    img = Image.new("RGBA", (length, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body = length - 170
    dark = tuple(max(0, int(c * 0.72)) for c in color)
    light = tuple(min(255, int(c * 1.18 + 18)) for c in color)
    d.rectangle([0, 0, body, w - 1], fill=color)
    d.rectangle([0, 0, body, w // 3], fill=light)
    d.rectangle([0, 2 * w // 3, body, w - 1], fill=dark)
    d.rectangle([0, 0, 22, w - 1], fill=(40, 40, 40))
    d.polygon([(body, 0), (body, w - 1), (length - 44, w / 2 + 9), (length - 44, w / 2 - 9)], fill=(236, 203, 160))
    d.polygon([(body, 0), (body + 18, 6), (body + 18, w - 7), (body, w - 1)], fill=dark)
    d.polygon([(length - 44, w / 2 - 9), (length - 44, w / 2 + 9), (length - 2, w / 2)], fill=dark)
    return img


def place_pencil(canvas, color, xy, angle, length=760):
    paste_shadow(canvas, pencil(length, color).rotate(angle, expand=True, resample=Image.BICUBIC), xy,
                 blur=10, offset=(10, 14), alpha=90)


def swatch_card(colors, cols=2, cell=104):
    rows = (len(colors) + cols - 1) // cols
    card = Image.new("RGB", (cols * (cell + 150) + 50, rows * (cell + 26) + 70), (253, 252, 248))
    d = ImageDraw.Draw(card)
    f = font("segoeuib", 40)
    for i, (num, rgb) in enumerate(colors):
        r, c = divmod(i, cols)
        x, y = 40 + c * (cell + 150), 40 + r * (cell + 26)
        d.text((x, y + cell / 2 - 26), str(num), font=f, fill=(70, 70, 70))
        d.rounded_rectangle([x + 70, y, x + 70 + cell, y + cell], 10, fill=rgb, outline=(205, 205, 205), width=2)
    layer = Image.new("RGBA", card.size)
    layer.paste(card)
    layer.putalpha(255)
    return layer


def sheet(art, margin=70, frame=True):
    """The art printed on a sheet of paper, with the thin frame line of the PDF pages."""
    paper = Image.new("RGB", (art.width + 2 * margin, art.height + 2 * margin), (252, 251, 247))
    paper.paste(art, (margin, margin))
    if frame:
        ImageDraw.Draw(paper).rectangle([margin - 18, margin - 18, margin + art.width + 17, margin + art.height + 17],
                                        outline=(60, 60, 60), width=4)
    layer = Image.new("RGBA", paper.size)
    layer.paste(paper)
    layer.putalpha(255)
    return layer


def corner_colored(name, w, h, level="standard", reach=0.38):
    """Numbered page with the bottom-right corner already colored in, like a page in progress."""
    col, line = cover_crop(finished(name, level), w, h), cover_crop(numbered(name, level), w, h)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon([(int(w * reach), h), (w, int(h * (reach + 0.04))), (w, h)], fill=255)
    return Image.composite(col, line, mask.filter(ImageFilter.GaussianBlur(6)))


def p_desk_cover(out, name="bulldog"):
    img = kraft_bg(1)
    pal = palette_of(name)
    side = 1560
    art = split(name, side, side, slant=0.10)
    paste_shadow(img, sheet(art).rotate(-2, expand=True, resample=Image.BICUBIC), (640, 120), blur=24, alpha=110)
    paste_shadow(img, polaroid(original(name), 560, angle=-9), (40, 40), blur=18)
    warm = sorted((c for _, c in pal), key=lambda c: -sum(c))
    picks = [pal[len(pal) // 3][1], pal[len(pal) // 2][1], pal[2 * len(pal) // 3][1], pal[-4][1]]
    for i, c in enumerate(picks[:3]):
        place_pencil(img, c, (-260 + i * 30, 1100 + i * 150), 28 - i * 6)
    for i, c in enumerate(picks[1:]):
        place_pencil(img, c, (2120 + i * 40, -160 + i * 120), -62 + i * 5, length=700)
    card = swatch_card(pal[:12]).rotate(-6, expand=True, resample=Image.BICUBIC)
    paste_shadow(img, card, (W - card.width + 150, H - card.height + 160), blur=14)
    return save_jpg(img.convert("RGB"), out)


def p_titled(out, name="tabby", level="standard"):
    img = kraft_bg(2, tone=(236, 228, 214))
    text_c(img, "CUSTOM COLOR BY NUMBER", W / 2, 60, font("georgiab", 150), (55, 48, 44))
    d = ImageDraw.Draw(img)
    f = font("segoeuib", 58)
    msg = "FROM YOUR PHOTO  •  DIGITAL DOWNLOAD  •  24H DELIVERY"
    tw = d.textlength(msg, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 60, 265, W / 2 + tw / 2 + 60, 375], 55, fill=TERRA)
    text_c(img, msg, W / 2, 285, f, "white")
    fw, fh = finished(name, level).size
    pw, phh = (760, 1000) if fh > fw else (1100, 825)
    px, sx = (330, 1500) if fh > fw else (40, 1390)
    ph = cover_crop(original(name), pw, phh)
    card = Image.new("RGBA", (ph.width + 50, ph.height + 50), (253, 252, 248, 255))
    card.paste(ph, (25, 25))
    paste_shadow(img, card.rotate(3, expand=True, resample=Image.BICUBIC), (px, 520), blur=18)
    art = corner_colored(name, pw, phh, level, reach=0.38 if fh > fw else 0.05)
    paste_shadow(img, sheet(art, margin=50).rotate(-3, expand=True, resample=Image.BICUBIC), (sx, 490), blur=18)
    d = ImageDraw.Draw(img)
    ax = 1170 if fh > fw else 1150
    d.arc([ax, 860, ax + 260, 1120], 200, 330, fill=(60, 60, 60), width=10)
    d.polygon([(ax + 270, 950), (ax + 225, 930), (ax + 240, 985)], fill=(60, 60, 60))
    pal = palette_of(name, level)
    if fh <= fw:   # landscape: room for the 3 steps under the pictures
        steps = [("1", "Send your photo"), ("2", "Get your page in 24h"), ("3", "Color it & reveal")]
        for i, (n_, t) in enumerate(steps):
            x = 200 + i * 800
            d.ellipse([x, 1560, x + 110, 1670], fill=[TERRA, TEAL, PLUM][i])
            text_c(img, n_, x + 55, 1568, font("impact", 80), "white")
            text_l(img, t, x + 135, 1580, font("segoeuib", 58), (55, 48, 44))
        return save_jpg(img.convert("RGB"), out)
    strip = swatch_card(pal[:7], cols=1, cell=92).rotate(14, expand=True, resample=Image.BICUBIC)
    paste_shadow(img, strip, (-70, H - strip.height + 220), blur=12)
    picks = [pal[3][1], pal[len(pal) // 2][1], pal[-5][1]]
    for i, c in enumerate(picks):
        place_pencil(img, c, (2240 + i * 50, 1200 + i * 60), 118 - i * 4, length=720)
        place_pencil(img, picks[(i + 1) % 3], (-300 + i * 40, 600 + i * 120), 30 - i * 5, length=640)
    return save_jpg(img.convert("RGB"), out)


def p_feature_cover(out, name="couple", level="detailed"):
    """Mobile-first cover: the real half-colored page on the left, every key feature readable on the right."""
    img = kraft_bg(3, tone=(236, 226, 210))
    fw, fh = finished(name, level).size
    aw = 1560
    ah = min(1480, round(aw * fh / fw))
    art = split(name, aw, ah, level=level, slant=0.08)
    page = sheet(art, margin=50).rotate(-2, expand=True, resample=Image.BICUBIC)
    paste_shadow(img, page, (30, 1960 - page.height), blur=22, alpha=110)
    pal = palette_of(name, level)
    for i, c in enumerate([pal[len(pal) // 3][1], pal[len(pal) // 2][1], pal[2 * len(pal) // 3][1]]):
        place_pencil(img, c, (900 + i * 70, 1620 + i * 70), 15 + i * 4, length=700)
    paste_shadow(img, polaroid(original(name), 470, angle=-8), (20, 40), blur=16)
    text_l(img, "YOUR PHOTO", 640, 60, font("georgiab", 112), (55, 48, 44))
    text_l(img, "COLOR BY NUMBER", 640, 185, font("georgiab", 112), TERRA)
    feats = [("24H", TERRA, "Ready in 24 hours", "Sent to your Etsy Messages"),
             ("iPad", TEAL, "Print or Procreate", "PDF + PNG + .swatches"),
             ("3", MUSTARD, "3 levels", "16 • 24 • 36 colors"),
             ("?!", PLUM, "Mystery reveal", "Answer key kept separate"),
             ("A4", (90, 150, 90), "Letter • A4 • 16x20", "All sizes included")]
    d = ImageDraw.Draw(img)
    x0, y0 = 1720, 370
    for i, (badge, color, head, sub) in enumerate(feats):
        y = y0 + i * 310
        d.rounded_rectangle([x0 - 20, y - 20, W - 40, y + 250], 40, fill=(255, 255, 255))
        d.ellipse([x0, y + 15, x0 + 190, y + 205], fill=color)
        text_c(img, badge, x0 + 95, y + 52 if len(badge) > 2 else y + 38, font("impact", 80 if len(badge) > 2 else 110),
               "white" if color != MUSTARD else INK)
        text_l(img, head, x0 + 225, y + 30, font("segoeuib", 62), INK)
        text_l(img, sub, x0 + 225, y + 120, font("segoeui", 50), (90, 90, 90))
    return save_jpg(img.convert("RGB"), out)


def build_photos(d):
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.jpg"):
        old.unlink()
    plan = {
        "01_cover.jpg": p_feature_cover,
        "01b_desk.jpg": lambda o: p_desk_cover(o, "bulldog"),
        "02_custom_cbn.jpg": lambda o: p_titled(o, "kids", "detailed"),
        "03_cover_split.jpg": p1_cover,
        "04_examples.jpg": lambda o: examples_image(["couple", "kids", "tabby", "crete"], "ANY PHOTO YOU LOVE",
                                                    o, 2, labels=["COUPLES & PETS", "KIDS & PETS", "PETS", "LANDSCAPES"],
                                                    levels=["detailed", "detailed", "standard", "standard"]),
        "05_before_after.jpg": p_examples_big,
        "06_mystery.jpg": p_mystery,
        "07_levels.jpg": p_levels,
        "08_included.jpg": p_included,
        "09_how_to_order.jpg": p_how_to_order,
        "10_closeup.jpg": p_closeup,
        "11_photo_tips.jpg": p_photo_tips,
        "12_good_to_know.jpg": lambda o: L.terms_image(o, rows=TERMS),
    }
    for name, fn in plan.items():
        fn(d / name)
        print("photo", name, flush=True)


# ---------- delivery file and text ----------

def order_pdf(path):
    """The file Etsy hands out at checkout: how to send the photo. The real kit follows within 24 hours."""
    c = rl_canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    c.setFillColorRGB(*[v / 255 for v in PLUM])
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 90, "Thank you for your order!")
    c.setFillColorRGB(0.17, 0.17, 0.17)
    c.setFont("Helvetica", 13)
    lines = [
        "Your custom color by number is made from your own photo, so there is one more step:",
        "",
        "1. Open Etsy > Messages and find the conversation for this order.",
        "2. Attach the photo you want turned into a color by number.",
        "   Send the original, full-size photo (not a screenshot), bright and sharp.",
        "3. Tell me the level if you didn't pick one: Relaxing, Standard or Detailed.",
        "",
        "Within 24 hours I'll send you a download link in Etsy Messages with:",
        "  - US Letter, A4 and 16x20 poster PDFs",
        "  - Numbered PNG pages for Procreate / iPad and a .swatches palette",
        "  - A numbered color swatch card and hex codes",
        "  - A separate REVEAL folder with the finished picture (no peeking!)",
        "",
        "Giving it as a mystery gift? Forward the link and tell them not to open",
        "the 2_REVEAL_Answer_Key folder until they have finished coloring.",
        "",
        "Your photo is only used for your order and deleted after delivery.",
        "Questions? Just send me a message.",
    ]
    y = h - 150
    for ln in lines:
        c.drawString(70, y, ln)
        y -= 22
    c.save()


# Worded for DIGITAL buyers (procreate / printable / digital): "custom paint by number" alone is owned by
# physical canvas kits (2026-11-22).
TITLE = ("Custom Paint by Number from Photo, Digital Procreate Color by Number, Printable Personalized "
         "Coloring Page, Mystery Photo Gift")
TAGS = ["color by number", "paint by number", "procreate coloring", "printable coloring", "custom coloring page",
        "photo to coloring", "ipad color by number", "custom portrait", "custom pet portrait", "personalized gift",
        "mystery coloring", "family photo gift", "christmas gift"]
TAXONOMY_ID = 339  # Books > Coloring Books. Tried 75 Drawing & Illustration on 2026-11-22: Etsy flagged "Category" as a search-visibility risk.
PERSONALIZATION = ("After checkout, send your photo in Etsy Messages. Type what's in it here (family, pet, place) "
                   "or 'mystery' if it's a surprise gift.")


def description():
    return """Turn any photo you love into a one-of-a-kind color by number page! Your family, your pet, your partner, a favorite trip or a beautiful view: send me the photo and I'll turn it into a numbered coloring page with its own color palette, ready within 24 hours.

Make it a MYSTERY GIFT: the person coloring won't know what the picture is until it slowly appears under their pencils. The finished picture comes in a separate answer key folder, so nothing is spoiled.

HOW TO ORDER
1. Choose your level and add to cart.
2. Upload your photo in the personalization box when you order, or send it in Etsy Messages after checkout (original full-size file, bright and sharp).
3. I turn your photo into a clean illustration with an AI image tool, then into your numbered page. I check every page by hand and send your download link in Etsy Messages within 24 hours.

CHOOSE YOUR LEVEL
- Relaxing: 16 colors, bigger areas. Great for beginners and kids.
- Standard: 24 colors. The most popular choice.
- Detailed: 36 colors, more detail. For experienced colorists.

WHAT YOU GET
- Print-ready PDFs in US Letter, A4 and 16x20 poster size
- Numbered PNG pages for Procreate / iPad: dark lines, light-gray lines (they vanish under paint) and a version with the palette printed below
- Procreate .swatches palette with the colors in number order
- Numbered color swatch card and hex code list
- Scalable SVG line art
- A separate REVEAL folder with the finished picture and color guides

PHOTO TIPS
- Bright daylight photos work best; avoid blurry or dark ones.
- The people, pet or view you love should fill most of the photo.
- Faces are turned into simple color shapes, like a painting, not a photo-real portrait. Full-body family shots, pets, travel photos and landscapes give the nicest result.
- Not sure about your photo? Send it anyway and I'll let you know before I start.

PERFECT FOR
Christmas gifts, family memories, pet lovers and pet memorials, anniversaries, couples, grandparents, travel memories, birthdays, and anyone who loves to color.

PLEASE NOTE
- This is a digital item. Nothing is shipped.
- At checkout you get a PDF with ordering instructions; your custom files follow by Etsy Messages within 24 hours.
- To get clean shapes and nicer faces, your photo is processed with an AI image tool (Google Gemini). It is used only for your order and deleted after delivery. Please only send photos you have the right to use.
- Colors can look slightly different on screens and printers.
- For personal use only. Please don't share or resell the files.
- Not happy with the result? Message me and I'll redo it with a different photo or level.

The example photos in this listing are AI-generated sample photos and free-license photos (CC0 / public domain) from Wikimedia Commons."""


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(TITLE) <= 140, len(TITLE)
    assert len(TAGS) == 13 and len(set(TAGS)) == 13 and all(len(t) <= 20 for t in TAGS), TAGS
    assert len(PERSONALIZATION) <= 256
    (OUT / "files").mkdir(exist_ok=True)
    order_pdf(OUT / "files" / "How_To_Send_Your_Photo.pdf")
    build_photos(OUT / "photos")
    text = dict(title=TITLE, tags=TAGS, description=description(), prices=PRICES, personalization=PERSONALIZATION)
    (OUT / "listing.json").write_text(json.dumps(text, indent=2, ensure_ascii=False), encoding="utf-8")
    print("built", OUT)


def upload():
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state_file = OUT / "uploaded.json"
    if state_file.exists():
        sys.exit(f"already uploaded: {state_file.read_text()}")
    text = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
        "quantity": 999, "title": text["title"], "description": text["description"],
        "price": min(text["prices"].values()),
        "who_made": "i_did", "when_made": "made_to_order", "taxonomy_id": TAXONOMY_ID, "type": "download",
        "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(text["tags"]),
        "is_personalizable": "true", "personalization_is_required": "false",
        "personalization_char_count_max": 256, "personalization_instructions": text["personalization"],
    })
    lid = listing["listing_id"]
    state_file.write_text(json.dumps({"listing_id": lid}, indent=2))
    print("draft", lid, flush=True)
    for rank, p in enumerate(sorted((OUT / "photos").glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    for rank, p in enumerate(sorted((OUT / "files").iterdir()), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": p.name},
                  files={"file": p})
    print("photos + file uploaded", flush=True)
    try:
        set_levels(e, lid, text["prices"])
        print("level variation set", flush=True)
    except Exception as exc:  # the draft is still fine; the user can add the variation in the editor
        print(f"could not set the level variation by API ({exc}); add it in the Etsy editor", flush=True)
    print(f"https://www.etsy.com/your/shops/me/listing-editor/edit/{lid}")


def update():
    """Push the current text and photos to the existing draft."""
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    lid = json.loads((OUT / "uploaded.json").read_text())["listing_id"]
    text = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    e.request("PATCH", f"/shops/{sid}/listings/{lid}", form={
        "title": text["title"], "description": text["description"], "tags": ",".join(text["tags"]),
        "is_personalizable": "true", "personalization_is_required": "false",
        "personalization_char_count_max": 256, "personalization_instructions": text["personalization"]})
    old = [im["listing_image_id"] for im in e.request("GET", f"/listings/{lid}/images")["results"]]
    new = sorted((OUT / "photos").glob("*.jpg"))
    while old and len(old) + len(new) > 20 and len(old) > 1:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{old.pop()}")
    for rank, f in enumerate(new, 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": f})
    for image_id in old:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
    print(f"updated draft {lid}: text + {len(new)} photos", flush=True)


def set_personalization(e, sid, lid):
    """Etsy's newer personalization API ("Custom options" in the editor; the legacy is_personalizable PATCH
    fields are ignored): a photo upload at checkout plus a text box. Replaces all existing questions.
    The editor refuses to save unless instructions are <= 120 chars and uploads allow >= 2 files."""
    questions = [
        {"question_type": "unlabeled_upload", "question_text": "Upload your photo", "required": False,
         "max_allowed_files": 2,
         "instructions": "Bright, sharp, full-size photo. Or send it in Etsy Messages after checkout."},
        {"question_type": "text_input", "question_text": "What is in your photo?", "required": False,
         "max_allowed_characters": 256,
         "instructions": "Family, pet, couple, place... or type mystery if it is a surprise gift."},
    ]
    for q in questions:
        assert len(q["instructions"]) <= 120 and len(q["question_text"]) <= 45, q
    e.request("POST", f"/shops/{sid}/listings/{lid}/personalization", json_body={"personalization_questions": questions})


def set_levels(e, lid, prices):
    """One custom variation 'Level' with its own price per option."""
    products = [{"sku": "", "property_values": [{"property_id": 513, "property_name": "Level", "value_ids": [],
                                                 "values": [name]}],
                 "offerings": [{"price": price, "quantity": 999, "is_enabled": True}]}
                for name, price in prices.items()]
    e.request("PUT", f"/listings/{lid}/inventory", json_body={
        "products": products, "price_on_property": [513], "quantity_on_property": [], "sku_on_property": []})


def fix():
    """Text, category, personalization and Level variation only (no photos). Etsy's editor can drop the
    personalization + variation when the listing is edited there; this puts them back."""
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    lid = json.loads((OUT / "uploaded.json").read_text())["listing_id"]
    e.request("PATCH", f"/shops/{sid}/listings/{lid}", form={
        "title": TITLE, "tags": ",".join(TAGS), "taxonomy_id": TAXONOMY_ID, "description": description()})
    set_personalization(e, sid, lid)
    set_levels(e, lid, PRICES)
    r = e.request("GET", f"/listings/{lid}")
    inv = e.request("GET", f"/listings/{lid}/inventory")
    print("title:", r["title"])
    print("taxonomy:", r["taxonomy_id"], "variations:", r["has_variations"])
    print("personalization:", [q["question_text"] for q in e.request("GET", f"/listings/{lid}/personalization")["personalization_questions"]])
    for prod in inv["products"]:
        print("  ", [v["values"] for v in prod["property_values"]], prod["offerings"][0]["price"])


if __name__ == "__main__":
    {"build": build, "upload": upload, "update": update, "fix": fix}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
