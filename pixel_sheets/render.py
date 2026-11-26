"""Draw the mystery sheet exactly as Google Sheets shows it (same layout, colors and square split),
plus a laptop mock-up. Used for listing photos and the listing video."""
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import designs as D
import pixelsheet as P

FD = "C:/Windows/Fonts/"
INK, SOFT = (43, 45, 66), (92, 96, 112)
GREEN, RED = (30, 123, 58), (192, 38, 45)
YELLOW, BORDER = (255, 244, 184), (201, 205, 214)
OK_BG, BAD_BG = (216, 243, 220), (253, 226, 225)
HIDDEN = tuple(int(P.HIDDEN_FILL[i:i + 2], 16) for i in (0, 2, 4))


@lru_cache(None)
def font(name: str, size: int):
    files = {"r": "segoeui.ttf", "b": "segoeuib.ttf", "sb": "seguisb.ttf", "i": "segoeuii.ttf",
             "bl": "seguibl.ttf", "sym": "seguisym.ttf", "l": "segoeuil.ttf", "pr": "segoeprb.ttf"}
    return ImageFont.truetype(FD + files[name], size)


def rgb(hexstr: str):
    return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))


def owner_of(p: P.Puzzle) -> np.ndarray:
    rows = D.expand(p.design)
    return P.assign_squares(len(rows), len(rows[0]), len(p.questions), p.seed)


def picture(p: P.Puzzle, revealed: set, cell: int = 20, gap: int = 1) -> Image.Image:
    """Just the grid. revealed = set of question indexes answered correctly."""
    rows = D.expand(p.design)
    own = owner_of(p)
    im = Image.new("RGB", (len(rows[0]) * cell, len(rows) * cell), "white")
    d = ImageDraw.Draw(im)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            col = rgb(p.design["colors"][c]) if own[y, x] in revealed else HIDDEN
            d.rectangle([x * cell, y * cell, x * cell + cell - 1 - gap, y * cell + cell - 1 - gap], fill=col)
    return im


def sheet(p: P.Puzzle, typed: list, title: str, row: int = 30, cursor: int | None = None) -> Image.Image:
    """typed: one entry per question (None = empty). Correctness is checked like the Key tab does."""
    rows = D.expand(p.design)
    h, w, nq = len(rows), len(rows[0]), len(p.questions)
    s = row / 30
    good = [t is not None and str(t).strip().lower() == a.lower() for t, (_, a) in zip(typed, p.questions)]
    top = int(130 * s)
    xn, xq, xa, xc, xg = int(20 * s), int(58 * s), int(220 * s), int(318 * s), int(390 * s)
    W = xg + w * row + int(30 * s)
    H = top + max(nq, h) * row + int(30 * s)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((xn, int(14 * s)), title, font=font("b", int(26 * s)), fill=INK)
    d.text((xn, int(52 * s)), "Type each answer in the yellow box. Every correct answer reveals part of the mystery picture!",
           font=font("i", int(13 * s)), fill=SOFT)
    d.text((xn, int(74 * s)), f"Correct: {sum(good)} / {nq}", font=font("b", int(18 * s)), fill=GREEN)
    hy = top - int(26 * s)
    for x, t in ((xn, "#"), (xq, "Question"), (xa + int(12 * s), "Answer")):
        d.text((x, hy), t, font=font("b", int(15 * s)), fill=SOFT)
    for i, (q, a) in enumerate(p.questions):
        y = top + i * row
        d.text((xq - int(8 * s), y + row // 2), str(i + 1), font=font("r", int(13 * s)), fill=(138, 143, 160), anchor="rm")
        d.text((xq, y + row // 2), q, font=font("r", int(18 * s)), fill=INK, anchor="lm")
        d.rectangle([xa, y, xc - 1, y + row - 1], fill=YELLOW, outline=BORDER)
        if typed[i] is not None:
            d.text(((xa + xc) // 2, y + row // 2), str(typed[i]), font=font("r", int(17 * s)), fill=INK, anchor="mm")
            d.rectangle([xc, y, xc + int(36 * s), y + row - 1], fill=OK_BG if good[i] else BAD_BG)
            d.text((xc + int(18 * s), y + row // 2), "✓" if good[i] else "✗", font=font("sym", int(19 * s)),
                   fill=GREEN if good[i] else RED, anchor="mm")
        if cursor == i:
            d.rectangle([xa, y, xc - 1, y + row - 1], outline=(26, 115, 232), width=max(2, int(3 * s)))
    pic = picture(p, {i for i, g in enumerate(good) if g}, cell=row, gap=max(1, int(2 * s)))
    im.paste(pic, (xg, top))
    return im


def shadow(canvas: Image.Image, layer: Image.Image, xy, blur=24, offset=(0, 22), alpha=0.35, radius=0):
    """Paste layer (RGB or RGBA) on canvas with a soft drop shadow that follows its shape."""
    layer = layer.convert("RGBA")
    a = layer.getchannel("A")
    if radius:
        m = Image.new("L", layer.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, layer.width - 1, layer.height - 1], radius, fill=255)
        a = Image.fromarray(np.minimum(np.asarray(a), np.asarray(m)))
        layer.putalpha(a)
    pad = blur * 3
    sh = Image.new("L", (layer.width + pad * 2, layer.height + pad * 2), 0)
    sh.paste(a.point(lambda v: int(v * alpha)), (pad, pad))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste((40, 30, 30), (xy[0] - pad + offset[0], xy[1] - pad + offset[1]), sh)
    canvas.paste(layer, xy, layer)


def sheets_window(content: Image.Image, doc_title: str, active_tab: int = 0, n_tabs: int = 10,
                  aspect: float = 1.6, labels: list | None = None) -> Image.Image:
    """Wrap a sheet render in a simple Google-Sheets-like window (top bar + tabs), widened to aspect."""
    s = content.width / 1100
    bar, tabs = int(78 * s), int(40 * s)
    need = int((content.height + bar + tabs) * aspect)
    if content.width < need:
        wide = Image.new("RGB", (need, content.height), "white")
        wide.paste(content, (0, 0))
        content = wide
    W, H = content.width, content.height + bar + tabs
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, bar], fill=(249, 251, 253))
    ic = int(30 * s)
    d.rounded_rectangle([int(16 * s), int(12 * s), int(16 * s) + ic, int(12 * s) + int(ic * 1.3)], int(4 * s), fill=(15, 157, 88))
    for k in range(3):
        yy = int(12 * s) + int(ic * 0.45) + k * int(ic * 0.25)
        d.line([int(22 * s), yy, int(16 * s) + ic - int(6 * s), yy], fill="white", width=max(1, int(2 * s)))
    d.text((int(58 * s), int(10 * s)), doc_title, font=font("r", int(17 * s)), fill=INK)
    d.text((int(58 * s), int(36 * s)), "File   Edit   View   Insert   Format   Data   Tools   Extensions   Help",
           font=font("r", int(13 * s)), fill=SOFT)
    d.line([0, bar, W, bar], fill=(218, 220, 224), width=max(1, int(2 * s)))
    im.paste(content, (0, bar))
    ty = bar + content.height
    d.rectangle([0, ty, W, H], fill=(241, 243, 244))
    x = int(16 * s)
    labels = labels or [f"Picture {k + 1}" for k in range(n_tabs)]
    for k, label in enumerate(labels):
        tw = d.textlength(label, font=font("sb", int(13 * s))) + int(24 * s)
        if x + tw > W:
            break
        if k == active_tab:
            d.rectangle([x, ty, x + tw, H], fill=(225, 240, 230))
            d.line([x, H - int(3 * s), x + tw, H - int(3 * s)], fill=(24, 128, 56), width=max(2, int(3 * s)))
        d.text((x + tw / 2, ty + tabs / 2), label, font=font("sb", int(13 * s)),
               fill=(24, 128, 56) if k == active_tab else SOFT, anchor="mm")
        x += tw + int(4 * s)
    return im


def laptop(screen: Image.Image, width: int) -> Image.Image:
    """Laptop mock-up around a screen image (screen is scaled to fit)."""
    bez = int(width * 0.03)
    sw = width - 2 * int(width * 0.06) - 2 * bez
    sh = int(sw * 0.625)
    scr = screen.copy()
    scr.thumbnail((sw, sh), Image.LANCZOS)
    screen_area = Image.new("RGB", (sw, sh), "white")
    screen_area.paste(scr, ((sw - scr.width) // 2, 0))
    lid_w, lid_h = sw + 2 * bez, sh + 2 * bez
    base_h = int(width * 0.035)
    im = Image.new("RGBA", (width, lid_h + base_h + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lx = (width - lid_w) // 2
    d.rounded_rectangle([lx, 0, lx + lid_w, lid_h], int(bez * 0.9), fill=(32, 35, 44))
    im.paste(screen_area, (lx + bez, bez))
    d.ellipse([width // 2 - 4, bez // 2 - 4, width // 2 + 4, bez // 2 + 4], fill=(70, 74, 86))
    d.polygon([(0, lid_h + base_h * 0.35), (width, lid_h + base_h * 0.35), (width - base_h, lid_h + base_h), (base_h, lid_h + base_h)],
              fill=(196, 200, 208))
    d.rectangle([0, lid_h, width, lid_h + int(base_h * 0.35)], fill=(222, 225, 231))
    d.rounded_rectangle([width // 2 - int(width * 0.08), lid_h, width // 2 + int(width * 0.08), lid_h + int(base_h * 0.25)],
                        6, fill=(186, 190, 198))
    return im


def typed_upto(p: P.Puzzle, k: int, wrong: dict | None = None) -> list:
    """First k answers typed correctly (wrong = {index: wrong text} to show a mistake)."""
    out = []
    for i, (_, a) in enumerate(p.questions):
        if i < k:
            out.append((wrong or {}).get(i, a))
        else:
            out.append(None)
    return out
