"""Click-focused Etsy cover: photo-style flat lay with an iPad showing a half-painted design.

    python make_cover.py            # writes listing/01_cover.jpg for each set (old cover kept as zz_old_cover.jpg)
"""

import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import make_listing_images as L
from make_listing_images import cover_crop, save_jpg

W, H = 2500, 2000                       # 5:4
SAFE = (270, 140, 2230, 1860)           # inside the centre 2000x2000 square (survives a square crop); edges stay plain desk
BG_PHOTO = Path("cover_bg.jpg")         # optional: a real empty-desk photo; used instead of the drawn wood

FONTS = Path("C:/Windows/Fonts")
INK, PLUM, CORAL, CREAM = (40, 36, 40), (75, 46, 90), (226, 82, 58), (253, 249, 242)


def font(name, size, variation=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if variation:
        f.set_variation_by_name(variation)
    return f


# ---------- surface ----------

def anoise(rng, sy, sx):
    """Smooth noise in [0,1] with feature size sy x sx px (stretched along x when sx > sy)."""
    small = rng.random((H // sy + 3, W // sx + 3)).astype(np.float32)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC)


def wood(seed=3, base=(219, 190, 152)):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    plank = 500
    idx = (yy // plank).astype(np.int32)
    warp = anoise(rng, 120, 900) * 160 + anoise(rng, 40, 300) * 30
    g = (yy + warp + idx * 53.0) / 21.0
    rings = (0.5 + 0.5 * np.sin(g)) ** 4
    fibers = anoise(rng, 2, 160)
    knots = anoise(rng, 300, 1200)
    tone = np.array([1 + 0.035 * np.sin(i * 2.1 + 1) for i in range(H // plank + 2)], np.float32)[idx]
    v = tone * (1 - 0.11 * rings - 0.07 * fibers - 0.05 * knots)
    img = np.array(base, np.float32)[None, None] * v[..., None]
    seam = np.abs((yy % plank) - 0) < 3
    img[seam] *= 0.80
    img[np.abs((yy % plank) - 3) < 2] *= 1.04
    light = 1.10 - 0.20 * (0.55 * xx / W + 0.45 * yy / H)
    img *= light[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))


def marble(seed=5):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    turb = sum(anoise(rng, s, s) * (s / 400) for s in (400, 200, 100, 50, 25))
    veins = np.abs(np.sin((xx * 0.6 + yy * 0.8) / 260 + turb * 5.0)) ** 0.25
    v = 0.86 + 0.14 * veins - 0.03 * anoise(rng, 60, 60)
    img = np.array((247, 245, 242), np.float32)[None, None] * v[..., None]
    img[..., 2] *= 0.995
    img *= (1.04 - 0.08 * (0.5 * xx / W + 0.5 * yy / H))[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ---------- helpers ----------

def drop(canvas, layer, xy, blur=28, offset=(26, 34), alpha=120):
    """Paste RGBA layer at xy with a soft shadow."""
    x, y = xy
    a = layer.split()[3]
    pad = blur * 3
    sh = Image.new("L", (layer.width + 2 * pad, layer.height + 2 * pad), 0)
    sh.paste(a.point(lambda p: p * alpha // 255), (pad, pad))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    black = Image.new("RGBA", sh.size, (30, 20, 10, 255))
    black.putalpha(sh)
    canvas.alpha_composite(black, (x - pad + offset[0], y - pad + offset[1]))
    canvas.alpha_composite(layer, (x, y))


def rounded(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def rotate(layer, angle):
    return layer.rotate(angle, expand=True, resample=Image.BICUBIC)


# ---------- objects ----------

def split_screen(col, n, sw, sh, seed=1):
    """Top-left numbered line art, bottom-right painted, with a brushy diagonal edge."""
    rect = col.rect(n)
    line = cover_crop(col.style_img(n, "Dark_Numbered", rect), sw, sh).convert("RGB")
    color = cover_crop(col.art(n), sw, sh).convert("RGB")
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    # boundary runs from (0.78 w, 0) to (0.18 w, h)
    bx = sw * (0.78 - 0.60 * yy / sh)
    wob = cv2.resize(rng.random((sh // 60 + 2, 3)).astype(np.float32), (sw, sh), interpolation=cv2.INTER_CUBIC)
    streak = cv2.resize(rng.random((sh // 9 + 2, 2)).astype(np.float32), (sw, sh), interpolation=cv2.INTER_LINEAR)
    d = xx - bx + (wob - 0.5) * 90 + (streak - 0.5) * 70
    m = np.clip(d / 5 + 0.5, 0, 1)
    mask = Image.fromarray((m * 255).astype(np.uint8))
    return Image.composite(color, line, mask)


def ipad(screen):
    sw, sh = screen.size
    bez, r_out, r_in = 44, 78, 34
    w, h = sw + 2 * bez, sh + 2 * bez
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r_out, fill=(178, 180, 184, 255))
    d.rounded_rectangle([5, 5, w - 6, h - 6], r_out - 5, fill=(18, 18, 20, 255))
    scr = screen.convert("RGBA")
    # glass glare
    gl = np.zeros((sh, sw), np.float32)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    gl += np.clip(1 - (xx / sw + yy / sh) / 0.9, 0, 1) * 0.10
    glare = Image.new("RGBA", (sw, sh), (255, 255, 255, 0))
    glare.putalpha(Image.fromarray((gl * 255).astype(np.uint8)))
    scr.alpha_composite(glare)
    body.paste(scr, (bez, bez), rounded((sw, sh), r_in))
    d.ellipse([w // 2 - 7, bez // 2 - 7, w // 2 + 7, bez // 2 + 7], fill=(40, 42, 50, 255))
    return body


def pencil(length=1020, width=44):
    yy, xx = np.mgrid[0:width, 0:length].astype(np.float32)
    v = (yy - width / 2 + 0.5) / (width / 2)
    shade = 0.80 + 0.20 * np.sqrt(np.clip(1 - v ** 2, 0, 1)) + 0.10 * np.exp(-((v + 0.45) / 0.18) ** 2)
    rgb = np.clip(np.stack([shade * 250, shade * 250, shade * 252], -1), 0, 255)
    tip = 110
    half = np.where(xx < tip, 4 + (width / 2 - 4) * (xx / tip) ** 0.9, width / 2)
    alpha = (np.abs(yy - width / 2 + 0.5) <= half).astype(np.float32)
    nib = xx < 26
    rgb[nib] = rgb[nib] * 0.72
    rgb[(xx > 640) & (xx < 648)] *= 0.93          # flat-side seam
    end = xx > length - 10
    alpha[end] *= np.clip((length - xx[end]) / 10, 0, 1)
    out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").filter(ImageFilter.GaussianBlur(0.7))


def coffee(r=260):
    size = 2 * r + 160
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    c = size // 2
    d = ImageDraw.Draw(img)
    # handle
    d.rounded_rectangle([c + int(r * 0.55), c - 34, c + int(r * 0.98), c + 34], 30, fill=(244, 242, 238, 255))
    d.ellipse([c - r, c - r, c + r, c + r], fill=(242, 239, 233, 255))                       # saucer
    d.ellipse([c - r + 26, c - r + 26, c + r - 26, c + r - 26], outline=(225, 221, 214, 255), width=6)
    cr = int(r * 0.66)
    d.ellipse([c - cr, c - cr, c + cr, c + cr], fill=(252, 251, 249, 255))                   # cup rim
    k = cr - 22
    yy, xx = np.mgrid[-k:k + 1, -k:k + 1].astype(np.float32)
    rr = np.hypot(xx, yy) / k
    base = np.array((92, 55, 32), np.float32)
    crema = np.array((176, 122, 76), np.float32)
    t = np.clip((rr - 0.55) / 0.45, 0, 1)[..., None]
    col = base * (1 - t) + crema * t
    # latte heart
    hx, hy = xx / (k * 0.42), -(yy + k * 0.05) / (k * 0.42)
    heart = (hx ** 2 + hy ** 2 - 1) ** 3 - hx ** 2 * hy ** 3 <= 0
    col[heart] = (238, 220, 196)
    a = (rr <= 1).astype(np.float32) * 255
    liquid = Image.fromarray(np.dstack([col, a]).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(1.2))
    img.alpha_composite(liquid, (c - k, c - k))
    return img


def paper(art, w=760, h=1013, margin=46):
    p = Image.new("RGBA", (w, h), (253, 252, 249, 255))
    p.paste(cover_crop(art, w - 2 * margin, h - 2 * margin - 40).convert("RGB"), (margin, margin))
    return p


def palette_strip(colors, cols=10, r=34, gap=16):
    w = cols * (2 * r + gap) + gap
    rows = (len(colors) + cols - 1) // cols
    img = Image.new("RGBA", (w, rows * (2 * r + gap) + gap), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, rgb in enumerate(colors):
        rr, cc = divmod(i, cols)
        x, y = gap + cc * (2 * r + gap), gap + rr * (2 * r + gap)
        d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=rgb + (255,), outline=(255, 255, 255, 255), width=4)
    return img


def hexes(col, n):
    text = (col.root / f"Design_{n:02d}" / "Hex_Codes.txt").read_text()
    return [tuple(int(h.split("#")[1][i:i + 2], 16) for i in (0, 2, 4)) for h in text.split("\n") if "#" in h]


def center_text(d, text, cx, y, f, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


# ---------- the cover ----------

def straight_split(col, n, sw, sh):
    """Top-left numbered line art, bottom-right painted, split by one clean diagonal."""
    rect = col.rect(n)
    line = cover_crop(col.style_img(n, "Dark_Numbered", rect), sw, sh).convert("RGB")
    color = cover_crop(col.art(n), sw, sh).convert("RGB")
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    x0, x1 = sw * 0.92, sw * 0.08                      # split runs from top-right to bottom-left
    d = (xx - (x0 + (x1 - x0) * yy / sh)) / np.hypot(1, (x1 - x0) / sh)
    m = np.clip(d / 1.5 + 0.5, 0, 1)
    img = Image.composite(color, line, Image.fromarray((m * 255).astype(np.uint8)))
    return img


def fit(d, lines, name, variation, width, max_size):
    size = max_size
    while size > 40 and max(d.textlength(t, font=font(name, size, variation)) for t in lines) > width:
        size -= 4
    return font(name, size, variation)


def surface(kind):
    if BG_PHOTO.exists():
        return cover_crop(Image.open(BG_PHOTO).convert("RGB"), W, H)
    return wood() if kind == "wood" else marble()


def make(col, hero, count, theme, out, kind="wood"):
    canvas = surface(kind).convert("RGBA")
    sx0, sy0, sx1, sy1 = SAFE

    # iPad: right side of the safe area, full safe height
    ph = sy1 - sy0
    bez = 44
    sh = ph - 2 * bez
    sw = round(sh * 0.715)
    pad = ipad(straight_split(col, hero, sw, sh))
    px, py = sx1 - pad.width, sy0
    drop(canvas, pad, (px, py), blur=40, offset=(30, 42), alpha=150)

    # text card: left side, narrower than the iPad
    cw_, ch_ = 610, 1080
    cx0, cy0 = sx0, (sy0 + sy1) // 2 - ch_ // 2 - 40
    card = Image.new("RGBA", (cw_, ch_), CREAM + (255,))
    card.putalpha(rounded((cw_, ch_), 40))
    d = ImageDraw.Draw(card)
    big = fit(d, theme, "bahnschrift.ttf", "Bold Condensed", cw_ - 70, 210)
    mid = fit(d, ["Color by Number"], "georgiab.ttf", None, cw_ - 80, 74)
    small = font("segoeuib.ttf", 50)
    lh = big.size * 1.02
    block = lh * len(theme) + 60 + 90 + 74
    y = (ch_ - block) / 2 + 30
    for t in theme:
        center_text(d, t, cw_ / 2, y, big, PLUM)
        y += lh
    y += 26
    d.line([(cw_ / 2 - 130, y), (cw_ / 2 + 130, y)], fill=(222, 205, 182), width=5)
    y += 34
    center_text(d, "Color by Number", cw_ / 2, y, mid, INK)
    y += 108
    center_text(d, "PROCREATE  &  PRINT", cw_ / 2, y, small, CORAL)
    drop(canvas, card, (cx0, cy0), blur=30, offset=(18, 26), alpha=95)

    # stylus on the desk under the card, pointing at the iPad
    pen = rotate(pencil(660, 40), 10)
    drop(canvas, pen, (cx0 + 0, cy0 + ch_ + 50), blur=10, offset=(14, 20), alpha=120)

    # red badge on the card's top-right corner, upper middle of the image
    br = 195
    badge = Image.new("RGBA", (2 * br, 2 * br), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.ellipse([0, 0, 2 * br - 1, 2 * br - 1], fill=CORAL + (255,))
    bd.ellipse([13, 13, 2 * br - 14, 2 * br - 14], outline=(255, 255, 255, 210), width=5)
    center_text(bd, str(count), br, 30, font("bahnschrift.ttf", 225, "Bold"), (255, 255, 255))
    center_text(bd, "PAGES", br, 258, font("bahnschrift.ttf", 74, "Bold"), (255, 255, 255))
    badge = rotate(badge, 8)
    drop(canvas, badge, (cx0 + cw_ - badge.width // 2 - 10, max(sy0, cy0 - badge.height // 2 + 20)),
         blur=18, offset=(12, 18), alpha=110)

    # soft window light
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bands = np.clip(np.sin((xx + yy * 0.55) / 210) * 1.6, 0, 1)
    light = cv2.GaussianBlur(bands, (0, 0), 60) * 0.05
    rgb = np.asarray(canvas.convert("RGB")).astype(np.float32)
    rgb = rgb * (1 + light[..., None]) + 255 * light[..., None] * 0.2
    return save_jpg(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), out)


SETS = {
    "Set1_Cozy_Cottage_Winter": dict(hero=26, theme=["COZY", "COTTAGE"], kind="wood"),
    "Set2_Wildlife_Scenic_Nature": dict(hero=1, theme=["WILDLIFE &", "NATURE"], kind="wood"),
    "Set3_Sunsets_Travel": dict(hero=11, theme=["SUNSETS &", "TRAVEL"], kind="marble"),
}


def main():
    root = Path("output")
    col = L.Collection(Path("input"), root / "collection")
    only = sys.argv[1:]
    jobs = [(root / "sets" / k / "listing", dict(v, count=15)) for k, v in SETS.items()]
    jobs.append((root / "listing", dict(hero=31, theme=["REALISTIC", "& COZY"], count=46, kind="wood")))
    for folder, cfg in jobs:
        if only and not any(o in str(folder) for o in only):
            continue
        old, new = folder / "zz_old_cover.jpg", folder / "01_cover.jpg"
        if not old.exists() and new.exists():
            shutil.copy(new, old)
        make(col, cfg["hero"], cfg["count"], cfg["theme"], new, cfg["kind"])
        print(new)


if __name__ == "__main__":
    sys.exit(main())
