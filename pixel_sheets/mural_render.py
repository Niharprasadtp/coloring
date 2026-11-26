"""Pictures of the class murals for the guide, listing photos and video (same tiles/patches as the sheets)."""
import numpy as np
from PIL import Image, ImageDraw

import designs as D
import mural as M
import render as R


def image(m: M.Mural, revealed=None, cell=20, gap=1, tiles=False) -> Image.Image:
    """revealed: None = everything, or a set of (student, question) pairs."""
    rows = D.expand(m.design)
    own = m.owners()
    h, w = len(rows), len(rows[0])
    im = Image.new("RGB", (w * cell, h * cell), "white")
    d = ImageDraw.Draw(im)
    for y in range(h):
        for x in range(w):
            s, q = own[y, x]
            show = revealed is None or (s, q) in revealed
            col = R.rgb(m.design["colors"][rows[y][x]]) if show else R.HIDDEN
            d.rectangle([x * cell, y * cell, x * cell + cell - 1 - gap, y * cell + cell - 1 - gap], fill=col)
    if tiles:
        for k in range(1, M.TCOLS):
            d.line([k * M.TILE * cell - 1, 0, k * M.TILE * cell - 1, im.height], fill=(200, 16, 46), width=max(2, cell // 6))
        for k in range(1, M.TROWS):
            d.line([0, k * M.TILE * cell - 1, im.width, k * M.TILE * cell - 1], fill=(200, 16, 46), width=max(2, cell // 6))
    return im


def class_progress(m: M.Mural, frac: float, seed=7, absent=()):
    """A believable half-finished class: students at different stages."""
    rng = np.random.default_rng(seed)
    rev = set()
    for s in range(M.STUDENTS):
        if s in absent:
            rev |= {(s, q) for q in range(M.NQ)}
            continue
        k = int(np.clip(rng.normal(frac * M.NQ, 3), 0, M.NQ))
        rev |= {(s, q) for q in rng.permutation(M.NQ)[:k]}
    return rev


TABS = ["Class Mural", "Teacher Dashboard"] + [f"Student {k}" for k in range(1, 9)]
NAMES = ["Ava", "Liam", "Mia", "Noah", "Zoe", "Eli", "Ivy", "Leo", "Ruby", "Max", "Aria", "Sam", "Nora", "Owen",
         "Lily", "Jack", "Emma", "Kai", "Ella", "Finn", "Ada", "Theo", "Rosa", "Luca", "Maya", "Ben", "Isla",
         "Omar", "Cleo", "Jude"]


def scores(rev):
    return [sum(1 for q in range(M.NQ) if (s, q) in rev) for s in range(M.STUDENTS)]


def mural_tab(m, rev, cell=21):
    """The Class Mural tab as the teacher projects it."""
    f = R.font
    pic = image(m, rev, cell=cell, gap=2)
    done = len(rev) if rev is not None else M.STUDENTS * M.NQ
    total = M.STUDENTS * M.NQ
    s = cell / 21
    im = Image.new("RGB", (pic.width + int(60 * s), pic.height + int(140 * s)), "white")
    d = ImageDraw.Draw(im)
    d.text((int(30 * s), int(14 * s)), m.title.split(" (")[0], font=f("b", int(30 * s)), fill=R.INK)
    d.text((int(30 * s), int(58 * s)), "Every correct answer from every student reveals part of this picture. "
           "Let's finish it together!", font=f("i", int(14 * s)), fill=R.SOFT)
    d.text((int(30 * s), int(84 * s)), f"Class progress: {done} / {total} correct answers ({round(100 * done / total)}%)",
           font=f("b", int(19 * s)), fill=R.GREEN)
    im.paste(pic, (int(30 * s), int(120 * s)))
    return im


def dashboard_tab(rev, absent=(), rows=30, scale=1.0):
    f = R.font
    sc = scores(rev)
    s = scale
    rh = int(28 * s)
    W = int(1100 * s)
    im = Image.new("RGB", (W, int(150 * s) + rows * rh + int(60 * s)), "white")
    d = ImageDraw.Draw(im)
    d.text((int(30 * s), int(14 * s)), "Teacher Dashboard", font=f("b", int(30 * s)), fill=R.INK)
    d.text((int(30 * s), int(60 * s)), "Type Y under Reveal to uncover the tile of an absent student or an empty seat.",
           font=f("i", int(14 * s)), fill=R.SOFT)
    hy = int(100 * s)
    d.rectangle([int(24 * s), hy, W - int(24 * s), hy + rh], fill=R.INK)
    cols = [(30, "#"), (70, "Tile"), (300, "Student name"), (520, "Correct"), (620, "%"), (690, "Progress"), (990, "Reveal")]
    for x, t in cols:
        d.text((int(x * s), hy + rh // 2), t, font=f("b", int(15 * s)), fill="white", anchor="lm")
    for k in range(rows):
        y = hy + rh + k * rh
        if k % 2:
            d.rectangle([int(24 * s), y, W - int(24 * s), y + rh], fill=(244, 245, 248))
        tr, tc = M.tile_of(k)
        absent_k = k in absent
        vals = [str(k + 1), f"Student {k + 1}: row {tr + 1}, col {tc + 1}", "" if absent_k else NAMES[k],
                str(0 if absent_k else sc[k]), f"{0 if absent_k else round(100 * sc[k] / M.NQ)}%"]
        for (x, _), v in zip(cols, vals):
            d.text((int(x * s), y + rh // 2), v, font=f("r", int(15 * s)), fill=R.INK, anchor="lm")
        if not absent_k:
            d.text((int(690 * s), y + rh // 2), "■" * sc[k], font=f("sym", int(14 * s)), fill=R.GREEN, anchor="lm")
        d.rectangle([int(975 * s), y + 3, int(1060 * s), y + rh - 3], fill=R.YELLOW, outline=R.BORDER)
        if absent_k:
            d.text((int(1017 * s), y + rh // 2), "Y", font=f("b", int(15 * s)), fill=R.INK, anchor="mm")
    return im


def student_tab(m, s_idx, typed, row=34):
    """A student's tab: name, questions, checks and the live preview of their tile."""
    f = R.font
    s = row / 34
    rows = len(m.questions[s_idx])
    good = [t is not None and str(t) == a for t, (_, a) in zip(typed, m.questions[s_idx])]
    top = int(150 * s)
    W = int(1000 * s)
    im = Image.new("RGB", (W, top + rows * row + int(30 * s)), "white")
    d = ImageDraw.Draw(im)
    d.text((int(24 * s), int(12 * s)), m.title.split(" (")[0], font=f("b", int(24 * s)), fill=R.INK)
    d.text((int(24 * s), int(56 * s)), "Your name:", font=f("b", int(17 * s)), fill=R.INK)
    d.rectangle([int(140 * s), int(50 * s), int(330 * s), int(84 * s)], fill=R.YELLOW, outline=R.BORDER)
    d.text((int(150 * s), int(67 * s)), NAMES[s_idx], font=f("r", int(17 * s)), fill=R.INK, anchor="lm")
    tr, tc = M.tile_of(s_idx)
    d.text((int(24 * s), int(96 * s)), f"You are Student {s_idx + 1}. Every correct answer reveals part of YOUR "
           f"piece of the class mural.", font=f("i", int(13 * s)), fill=R.SOFT)
    d.text((int(24 * s), int(118 * s)), f"Correct: {sum(good)} / {rows}", font=f("b", int(18 * s)), fill=R.GREEN)
    xq, xa, xc = int(60 * s), int(220 * s), int(320 * s)
    for i, (q, a) in enumerate(m.questions[s_idx]):
        y = top + i * row
        d.text((xq - int(8 * s), y + row // 2), str(i + 1), font=f("r", int(13 * s)), fill=(138, 143, 160), anchor="rm")
        d.text((xq, y + row // 2), q, font=f("r", int(19 * s)), fill=R.INK, anchor="lm")
        d.rectangle([xa, y + 2, xc - 2, y + row - 2], fill=R.YELLOW, outline=R.BORDER)
        if typed[i] is not None:
            d.text(((xa + xc) // 2, y + row // 2), str(typed[i]), font=f("r", int(18 * s)), fill=R.INK, anchor="mm")
            d.rectangle([xc, y + 2, xc + int(38 * s), y + row - 2], fill=R.OK_BG if good[i] else R.BAD_BG)
            d.text((xc + int(19 * s), y + row // 2), "✓" if good[i] else "✗", font=f("sym", int(20 * s)),
                   fill=R.GREEN if good[i] else R.RED, anchor="mm")
    d.text((int(430 * s), top - int(26 * s)), "Your piece of the mural", font=f("b", int(15 * s)), fill=R.SOFT)
    rows_d = D.expand(m.design)
    own = m.owners()
    cell = int(56 * s)
    for y in range(M.TILE):
        for x in range(M.TILE):
            my, mx = tr * M.TILE + y, tc * M.TILE + x
            q = own[my, mx, 1]
            col = R.rgb(m.design["colors"][rows_d[my][mx]]) if good[q] else R.HIDDEN
            x0, y0 = int(430 * s) + x * cell, top + y * cell
            d.rectangle([x0, y0, x0 + cell - 3, y0 + cell - 3], fill=col)
    return im
