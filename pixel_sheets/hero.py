"""Hero thumbnail (listing photo 1): warm Christmas desk, big laptop with the tree ~80% revealed,
zoom bubble on '7 x 10 = 70 ✓', minimal giant text. Everything important stays inside the
centre 2000 x 2000 square so Etsy's 1:1 mobile crop keeps it."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import designs as D
import make_bundle as B
import render as R

W, H = 2667, 2000
SAFE_X0, SAFE_X1 = (W - H) // 2, (W + H) // 2          # 333 .. 2333
RED, GREEN, INK, CREAM = (200, 16, 46), (30, 123, 58), (43, 45, 66), (255, 249, 240)
f = R.font


def wood_desk(seed=5):
    rng = np.random.default_rng(seed)
    y = np.arange(H)[:, None].astype(float)
    x = np.arange(W)[None, :].astype(float)
    # smooth low-frequency warp so the grain lines wander like real wood
    warp = np.asarray(Image.fromarray((rng.random((12, 6)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    grain = np.sin((y / 9.0) + warp * 14 + np.sin(x / 260) * 1.2)
    fine = np.asarray(Image.fromarray((rng.random((H // 3, W // 60)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    t = 0.55 + 0.18 * grain + 0.22 * (fine - 0.5)
    plank = ((y // 500) % 2) * 0.05                       # wide planks, slight tone change
    t = np.clip(t - plank, 0, 1)
    light, dark = np.array([214, 160, 108]), np.array([150, 96, 58])
    img = dark + (light - dark) * t[..., None]
    for k in range(1, 4):                                 # plank seams
        img[k * 500 - 3:k * 500 + 3, :] *= 0.78
    # warm vignette
    vy = (np.arange(H) - H / 2) / (H / 2)
    vx = (np.arange(W) - W / 2) / (W / 2)
    vig = 1 - 0.28 * (vy[:, None] ** 2 + vx[None, :] ** 2)
    img = np.clip(img * vig[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(img).filter(ImageFilter.GaussianBlur(2.5))


def fairy_lights(im, seed=2):
    """Out-of-focus warm lights along the top edge and the top corners."""
    rng = np.random.default_rng(seed)
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    pts = [(int(x), int(40 + 70 * np.sin(x / 300) + rng.integers(-20, 20))) for x in np.linspace(-40, W + 40, 34)]
    d.line(pts, fill=(60, 45, 30, 200), width=6)
    for x, y in pts:
        r = int(rng.integers(26, 46))
        col = [(255, 214, 120), (255, 180, 90), (255, 236, 170), (255, 120, 90)][int(rng.integers(0, 4))]
        d.ellipse([x - r, y - r + 20, x + r, y + r + 20], fill=col + (210,))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    im.paste(glow, (0, 0), glow)


def pine(im, x0, y0, flip=False, seed=1):
    rng = np.random.default_rng(seed)
    layer = Image.new("RGBA", (700, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for b in range(5):
        bx, by = 60 + b * 40, 80 + b * 90
        ex, ey = bx + 520, by + int(rng.integers(-60, 60))
        d.line([bx, by, ex, ey], fill=(70, 50, 30, 255), width=8)
        for k in range(46):
            t = k / 46
            px, py = bx + (ex - bx) * t, by + (ey - by) * t
            for s in (-1, 1):
                d.line([px, py, px + 44 * (1 - t * 0.4), py + s * 58 * (1 - t * 0.4)],
                       fill=[(24, 92, 48, 255), (36, 116, 60, 255), (18, 74, 40, 255)][k % 3], width=7)
    for _ in range(5):                                     # red berries
        cx, cy = int(rng.integers(120, 420)), int(rng.integers(120, 460))
        d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(196, 22, 40, 255))
    if flip:
        layer = layer.transpose(Image.FLIP_LEFT_RIGHT)
    layer = layer.filter(ImageFilter.GaussianBlur(5))      # out of focus
    sh = Image.new("RGBA", layer.size, (30, 15, 5, 0))
    sh.putalpha(layer.getchannel("A").point(lambda v: v // 3))
    im.paste(sh.filter(ImageFilter.GaussianBlur(14)), (x0 + 14, y0 + 22), sh.filter(ImageFilter.GaussianBlur(14)))
    im.paste(layer, (x0, y0), layer)


def ornament(im, cx, cy, r, col, blur=6):
    layer = Image.new("RGBA", (r * 2 + 120, r * 2 + 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = 60, 100
    d.rectangle([ox + r - 26, oy - 40, ox + r + 26, oy + 6], fill=(212, 175, 80, 255))
    d.ellipse([ox, oy, ox + 2 * r, oy + 2 * r], fill=col + (255,))
    hl = tuple(min(255, c + 90) for c in col)
    d.ellipse([ox + r * 0.35, oy + r * 0.3, ox + r * 0.8, oy + r * 0.7], fill=hl + (200,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    R.shadow(im, layer, (cx - r - 60, cy - r - 100), blur=20, offset=(12, 22), alpha=0.35)


def pencil(im, x, y, length=760, angle=-18):
    layer = Image.new("RGBA", (length + 40, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([60, 18, length - 70, 62], fill=(206, 32, 44, 255))
    d.rectangle([60, 18, length - 70, 30], fill=(232, 74, 80, 255))
    d.rectangle([length - 70, 16, length - 20, 64], fill=(190, 190, 196, 255))
    d.rectangle([length - 20, 18, length + 10, 62], fill=(240, 150, 160, 255))
    d.polygon([(60, 18), (60, 62), (0, 40)], fill=(240, 205, 160, 255))
    d.polygon([(18, 33), (18, 47), (0, 40)], fill=(40, 40, 40, 255))
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
    R.shadow(im, layer, (x, y), blur=12, offset=(10, 16), alpha=0.35)


def zoom_bubble(p):
    """Close-up of three answered rows: question, typed answer, green check."""
    rows = [0, 1, 2]
    rw, rh = 600, 118
    b = Image.new("RGB", (rw, rh * len(rows) + 40), "white")
    d = ImageDraw.Draw(b)
    for k, i in enumerate(rows):
        q, a = p.questions[i]
        y = 20 + k * rh
        d.text((32, y + rh // 2), q, font=f("b", 64), fill=INK, anchor="lm")
        d.rectangle([318, y + 12, 468, y + rh - 12], fill=R.YELLOW, outline=R.BORDER, width=4)
        d.text((393, y + rh // 2), a, font=f("b", 62), fill=INK, anchor="mm")
        d.rectangle([476, y + 12, 574, y + rh - 12], fill=R.OK_BG)
        d.text((525, y + rh // 2), "✓", font=f("sym", 76), fill=GREEN, anchor="mm")
    m = Image.new("L", b.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, b.width - 1, b.height - 1], 44, fill=255)
    out = Image.new("RGBA", (b.width + 24, b.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(out).rounded_rectangle([0, 0, out.width - 1, out.height - 1], 56, fill=GREEN + (255,))
    bb = b.convert("RGBA"); bb.putalpha(m)
    out.paste(bb, (12, 12), bb)
    return out


def curved_arrow(d, p0, p1, p2, col, width=22):
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, 60)]
    d.line(pts, fill=col, width=width, joint="curve")
    (ax, ay), (bx, by) = pts[-6], pts[-1]
    ang = np.arctan2(by - ay, bx - ax)
    L, Wd = 80, 50
    tip = (bx + np.cos(ang) * 30, by + np.sin(ang) * 30)
    left = (bx - np.cos(ang) * L / 2 + np.cos(ang + np.pi / 2) * Wd, by - np.sin(ang) * L / 2 + np.sin(ang + np.pi / 2) * Wd)
    right = (bx - np.cos(ang) * L / 2 - np.cos(ang + np.pi / 2) * Wd, by - np.sin(ang) * L / 2 - np.sin(ang + np.pi / 2) * Wd)
    d.polygon([tip, left, right], fill=col)


def mini_card(name, w=360):
    p = B.P.Puzzle("x", D.DESIGNS[name], [("1 + 1 =", "2")])
    pic = R.picture(p, {0}, cell=22, gap=2)
    pic.thumbnail((w - 50, int(w * 1.15)), Image.LANCZOS)
    c = Image.new("RGB", (w, pic.height + 50), "white")
    c.paste(pic, ((w - pic.width) // 2, 25))
    return c


def make(out):
    im = wood_desk()
    fairy_lights(im)
    ornament(im, 120, 1780, 170, (190, 20, 40), blur=7)
    ornament(im, 380, 1930, 110, (214, 170, 60), blur=8)
    ornament(im, W - 150, 1760, 180, (30, 110, 60), blur=7)
    ornament(im, W - 400, 1940, 115, (190, 20, 40), blur=8)
    pencil(im, 300, 1660)

    # fanned cards peeking out on the right, behind the laptop
    for name, ang, x, y in [("snowman", -10, 2020, 470), ("reindeer", 6, 2150, 760),
                            ("santa_hat", -4, 2060, 1080), ("cocoa", 9, 2190, 1250)]:
        c = mini_card(name).convert("RGBA").rotate(ang, expand=True, resample=Image.BICUBIC)
        R.shadow(im, c, (x, y), blur=18, offset=(8, 16), alpha=0.4)

    # laptop: Christmas tree about 80% revealed
    p = B.puzzles_for("Multiplication")[0]
    sheet = R.sheet(p, R.typed_upto(p, 16), "Christmas Multiplication Mystery Picture", cursor=16)
    lap = R.laptop(R.sheets_window(sheet, "Christmas Multiplication Mystery Pictures"), 1800)
    lx, ly = (W - lap.width) // 2, 430
    R.shadow(im, lap, (lx, ly), blur=34, offset=(0, 34), alpha=0.5)

    # title ribbon (inside the safe square)
    d = ImageDraw.Draw(im)
    rib = Image.new("RGBA", (1640, 330), CREAM + (255,))
    R.shadow(im, rib, ((W - 1640) // 2, 60), blur=20, offset=(0, 14), alpha=0.35, radius=60)
    d.text((W // 2, 92), "CHRISTMAS MATH", font=f("bl", 172), fill=RED, anchor="mt")
    d.text((W // 2, 286), "40 Pixel Art Activities", font=f("b", 82), fill=INK, anchor="mt")

    # zoom bubble on the questions + arrow to the tree
    zb = zoom_bubble(p)
    bx, by = SAFE_X0 + 10, 930
    R.shadow(im, zb, (bx, by), blur=22, offset=(0, 18), alpha=0.45, radius=56)
    d = ImageDraw.Draw(im)
    sx = lx + int(1800 * 0.06) + int(1800 * 0.03)              # screen left edge (see render.laptop)
    tree_x, tree_y = sx + 1000, 820
    curved_arrow(d, (bx + zb.width - 30, by - 10), (bx + zb.width + 60, by - 260), (bx + zb.width + 300, by - 210),
                 (255, 200, 40), width=24)

    # trust pill
    txt = "Google Sheets + Excel  •  Self-Checking  •  Grades 2-4"
    tw = d.textlength(txt, font=f("b", 58))
    px0, py0 = (W - tw) / 2 - 60, 1590
    d.rounded_rectangle([px0, py0, px0 + tw + 120, py0 + 120], 60, fill=GREEN, outline="white", width=6)
    d.text((W // 2, py0 + 60), txt, font=f("b", 58), fill="white", anchor="mm")
    im.save(out, quality=93)
    return im


if __name__ == "__main__":
    from pathlib import Path
    o = Path("output/test/hero_test.jpg")
    im = make(o)
    sq = im.crop((SAFE_X0, 0, SAFE_X1, H))
    small = sq.resize((300, 300), Image.LANCZOS)
    board = Image.new("RGB", (1333 + 40 + 300 + 20, 1000), "gray")
    board.paste(im.resize((1333, 1000)), (0, 0))
    board.paste(small, (1373, 0))
    board.paste(sq.resize((150, 150), Image.LANCZOS), (1373, 320))
    board.save("output/test/hero_board.png")
