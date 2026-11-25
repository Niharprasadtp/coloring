"""Large-print puzzle book -> print-ready PDFs (US Letter + A4), answer key, PNG previews.

    python make_book.py                 # build everything into output/
    python make_book.py --previews 0    # skip PNG previews

Every puzzle is verified (puzzles.verify_*) before anything is drawn; a failed check stops the build.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

import content_christmas as C
import puzzles as P

OUT = Path(__file__).parent / "output"
INK = HexColor("#111111")
SOFT = HexColor("#555555")
HINT = HexColor("#8A8A8A")
RED = HexColor("#A4161A")
GREEN = HexColor("#1B5E20")
GOLD = HexColor("#C9A227")
MARK = HexColor("#F4C7C3")       # answer-key highlight
B, R_ = "Helvetica-Bold", "Helvetica"
MARGIN = 0.6 * inch


# ------------------------------------------------------------------ book plan


@dataclass
class Item:
    kind: str          # sudoku | wordsearch | maze | cryptogram | patterns | scramble
    title: str
    how: str           # one-line instruction under the title
    data: object
    label: str = ""    # e.g. "Easy"
    page: int = 0


MAZE_THEMES = ["Help Santa reach the chimney", "Guide the reindeer home", "Lead the elf to the workshop",
               "Take the sleigh to the village", "Find the way to the Christmas tree", "Carry the gift to the door",
               "Bring the cocoa to the fireplace", "Help the carolers find the church",
               "Get the snowman to the park", "Deliver the letter to the North Pole"]


def plan() -> list[Item]:
    dictionary = P._dictionary()
    items: dict[str, list[Item]] = {k: [] for k in
                                    ("sudoku6", "sudoku9", "wordsearch", "maze", "cryptogram", "patterns", "scramble")}

    for i, givens in enumerate([18, 17, 16, 15, 14, 13]):
        s = P.make_sudoku(6, givens, seed=600 + i)
        items["sudoku6"].append(Item("sudoku", f"Mini Sudoku {i + 1}", "Fill each row, column and box with 1 to 6.",
                                     s, "Easy"))
    for i, givens in enumerate([38, 36, 35, 34, 32, 31, 30, 29]):
        s = P.make_sudoku(9, givens, seed=900 + i)
        items["sudoku9"].append(Item("sudoku", f"Sudoku {i + 1}", "Fill each row, column and box with 1 to 9.",
                                     s, "Easy" if i < 4 else "Medium"))
    for i, (theme, words) in enumerate(C.WORD_SEARCHES):
        diag = i >= 6
        ws = P.make_wordsearch(theme, words, 13, P.ALL_DIRS[:4] if diag else P.ALL_DIRS[:2], seed=1300 + i)
        how = ("Words go across, down or diagonally." if diag else "Words go across (left to right) or down.")
        items["wordsearch"].append(Item("wordsearch", theme, how, ws, "Medium" if diag else "Easy"))
    sizes = [(7, 9), (8, 10), (8, 10), (9, 11), (9, 11), (10, 12), (10, 12), (11, 13), (11, 14), (12, 15)]
    for i, (w, h) in enumerate(sizes):
        items["maze"].append(Item("maze", f"Maze {i + 1}", MAZE_THEMES[i] + ".", P.make_maze(w, h, seed=700 + i),
                                  "Easy" if i < 5 else "Medium"))
    hints = [4, 4, 4, 3, 3, 3, 2, 2, 2, 2]
    carols = sorted(C.CAROLS, key=lambda t: len(t[0]))[:10]
    for i in range(1, len(carols) - 1):                 # no two lines from the same carol in a row
        if carols[i][1] == carols[i - 1][1]:
            carols[i], carols[i + 1] = carols[i + 1], carols[i]
    for i, ((text, src), h) in enumerate(zip(carols, hints)):
        items["cryptogram"].append(Item("cryptogram", f"Carol Code-Breaker {i + 1}",
                                        "Each letter stands for a different letter. Crack the code!",
                                        P.make_cryptogram(text, src, h, seed=400 + i), "Easy" if h >= 4 else "Medium"))
    used = set()
    for i, lvl in enumerate([1, 1, 2]):
        items["patterns"].append(Item("patterns", f"Number Patterns {i + 1}", "What number comes next?",
                                      P.make_patterns(lvl, 8, seed=500 + i, used=used), "Easy" if lvl == 1 else "Medium"))
    words = sorted([w for w in C.SCRAMBLE_WORDS if P.scramble_ok(w, dictionary)], key=len)
    step = len(words) / 30
    words = [words[int(k * step)] for k in range(30)]
    for i in range(3):
        items["scramble"].append(Item("scramble", f"Christmas Word Scramble {i + 1}",
                                      "Unscramble each Christmas word.",
                                      P.make_scrambles(words[i * 10:(i + 1) * 10], seed=800 + i, dictionary=dictionary),
                                      ["Easy", "Medium", "Medium"][i]))

    # ---- verify everything before drawing
    for it in [x for v in items.values() for x in v]:
        {"sudoku": P.verify_sudoku, "wordsearch": P.verify_wordsearch, "maze": P.verify_maze,
         "cryptogram": P.verify_cryptogram}.get(it.kind, lambda d: None)(it.data)
        if it.kind == "patterns":
            for p in it.data:
                P.verify_pattern(p)
        if it.kind == "scramble":
            for pair in it.data:
                P.verify_scramble(pair, dictionary)

    # ---- interleave: each type easiest -> hardest, spread evenly through the book
    keyed = []
    for t, (name, lst) in enumerate(items.items()):
        for i, it in enumerate(lst):
            keyed.append(((i + 0.5) / len(lst), t, it))
    order = [it for _, _, it in sorted(keyed, key=lambda k: (k[0], k[1]))]
    for i in range(1, len(order)):                      # avoid two of the same kind in a row
        if order[i].kind == order[i - 1].kind:
            for j in range(i + 1, len(order)):
                if order[j].kind != order[i - 1].kind and (i + 1 >= len(order) or order[j].kind != order[i + 1].kind):
                    order[i], order[j] = order[j], order[i]
                    break
    return order


# ------------------------------------------------------------------ drawing helpers


def snowflake(c, x, y, r, color=GREEN, w=1.6):
    c.setStrokeColor(color); c.setLineWidth(w); c.setLineCap(1)
    for k in range(6):
        a = math.pi / 3 * k
        ex, ey = x + r * math.cos(a), y + r * math.sin(a)
        c.line(x, y, ex, ey)
        for f in (0.55,):
            bx, by = x + r * f * math.cos(a), y + r * f * math.sin(a)
            for s in (-1, 1):
                b = a + s * math.pi / 4
                c.line(bx, by, bx + r * 0.3 * math.cos(b), by + r * 0.3 * math.sin(b))


def centered(c, text, x, y, font, size, color=INK):
    c.setFont(font, size); c.setFillColor(color)
    c.drawCentredString(x, y, text)


def fit_size(text, font, size, max_w):
    while stringWidth(text, font, size) > max_w and size > 8:
        size -= 0.5
    return size


class Book:
    def __init__(self, path: Path, pagesize):
        self.W, self.H = pagesize
        self.c = Canvas(str(path), pagesize=pagesize)
        self.c.setTitle(C.TITLE); self.c.setAuthor(""); self.c.setSubject(C.SUBTITLE)
        self.page = 1

    # frame -----------------------------------------------------------
    def header(self, title, how, label=""):
        c, W, H = self.c, self.W, self.H
        size = fit_size(title, B, 32, W - 2 * MARGIN - 1.4 * inch)
        centered(c, title, W / 2, H - 0.95 * inch, B, size, RED)
        tw = stringWidth(title, B, size)
        for s in (-1, 1):
            snowflake(c, W / 2 + s * (tw / 2 + 0.38 * inch), H - 0.95 * inch + 0.13 * inch, 0.17 * inch)
        hs = fit_size(how, R_, 18, W - 2 * MARGIN)
        centered(c, how, W / 2, H - 1.35 * inch, R_, hs, SOFT)
        if label:
            c.setFont(B, 13); c.setFillColor(GREEN)
            c.drawRightString(W - MARGIN, H - 0.45 * inch, label.upper())

    def footer(self):
        c = self.c
        c.setStrokeColor(GOLD); c.setLineWidth(1)
        c.line(MARGIN, 0.72 * inch, self.W - MARGIN, 0.72 * inch)
        c.setFont(R_, 13); c.setFillColor(SOFT)
        c.drawString(MARGIN, 0.45 * inch, C.TITLE)
        c.setFont(B, 16); c.setFillColor(INK)
        c.drawRightString(self.W - MARGIN, 0.45 * inch, str(self.page))

    def next(self, footer=True):
        if footer:
            self.footer()
        self.c.showPage(); self.page += 1

    @property
    def area(self):                       # x0, y0, x1, y1 of the content area
        return MARGIN, 0.95 * inch, self.W - MARGIN, self.H - 1.7 * inch

    # puzzles -----------------------------------------------------------
    def sudoku(self, s: P.Sudoku, box, solved=False):
        c = self.c
        x0, y0, x1, y1 = box
        side = min(x1 - x0, y1 - y0, 6.9 * inch)
        cell = side / s.n
        gx, gy = (x0 + x1) / 2 - side / 2, (y0 + y1) / 2 - side / 2
        c.setFillColor(white); c.rect(gx, gy, side, side, fill=1, stroke=0)
        for k in range(s.n + 1):
            c.setStrokeColor(INK)
            c.setLineWidth(3.2 if k % s.bc == 0 else 0.9)
            c.line(gx + k * cell, gy, gx + k * cell, gy + side)
            c.setLineWidth(3.2 if k % s.br == 0 else 0.9)
            c.line(gx, gy + side - k * cell, gx + side, gy + side - k * cell)
        fs = cell * 0.58
        for r in range(s.n):
            for col in range(s.n):
                v = s.puzzle[r][col]
                color = INK
                if not v and solved:
                    v, color = s.solution[r][col], RED
                if v:
                    c.setFont(B if color is INK else R_, fs); c.setFillColor(color)
                    c.drawCentredString(gx + (col + 0.5) * cell, gy + side - (r + 0.5) * cell - fs * 0.36, str(v))

    def wordsearch(self, ws: P.WordSearch, box, solved=False):
        c = self.c
        x0, y0, x1, y1 = box
        n = len(ws.grid)
        list_h = 0 if solved else 1.45 * inch
        side = min(x1 - x0, y1 - y0 - list_h, 6.9 * inch)
        cell = side / n
        gx, gy = (x0 + x1) / 2 - side / 2, y1 - side
        c.setStrokeColor(INK); c.setLineWidth(2.2)
        c.roundRect(gx - 4, gy - 4, side + 8, side + 8, 8, stroke=1, fill=0)
        if solved:
            c.setStrokeColor(MARK); c.setLineCap(1); c.setLineWidth(cell * 0.78)
            for w, (r, col, dr, dc) in ws.places.items():
                xa, ya = gx + (col + 0.5) * cell, gy + side - (r + 0.5) * cell
                L = len(w) - 1
                c.line(xa, ya, xa + dc * L * cell, ya - dr * L * cell)
        fs = cell * 0.6
        c.setFont(B, fs); c.setFillColor(INK)
        for r, row in enumerate(ws.grid):
            for col, ch in enumerate(row):
                c.drawCentredString(gx + (col + 0.5) * cell, gy + side - (r + 0.5) * cell - fs * 0.36, ch)
        if solved:
            return
        words = sorted(ws.words)
        cols = 3
        rows = math.ceil(len(words) / cols)
        colw = (x1 - x0) / cols
        lh = (list_h - 0.25 * inch) / rows
        fs = min(19, fit_size(max(words, key=len), B, 19, colw - 0.45 * inch))
        for i, w in enumerate(words):
            cx = x0 + (i // rows) * colw + 0.15 * inch
            cy = gy - 0.45 * inch - (i % rows) * lh
            c.setStrokeColor(SOFT); c.setLineWidth(1.2)
            c.rect(cx, cy - 2, 0.17 * inch, 0.17 * inch)
            c.setFont(B, fs); c.setFillColor(INK)
            c.drawString(cx + 0.28 * inch, cy, w)

    def maze(self, m: P.Maze, box, solved=False):
        c = self.c
        x0, y0, x1, y1 = box
        pad = 0.4 * inch
        cell = min((x1 - x0) / m.w, (y1 - y0 - 2 * pad) / m.h)
        mw, mh = cell * m.w, cell * m.h
        gx, gy = (x0 + x1) / 2 - mw / 2, (y0 + y1) / 2 - mh / 2
        top = gy + mh

        def X(col): return gx + col * cell
        def Y(r): return top - r * cell
        c.setStrokeColor(INK); c.setLineCap(1); c.setLineWidth(max(2.0, cell * 0.07))
        for r in range(m.h):
            for col in range(m.w):
                if r == 0 and col != 0:
                    c.line(X(col), Y(0), X(col + 1), Y(0))                   # top edge (gap at start)
                if col == 0:
                    c.line(X(0), Y(r), X(0), Y(r + 1))
                if ((r, col), (r, col + 1)) not in m.open:
                    c.line(X(col + 1), Y(r), X(col + 1), Y(r + 1))
                if ((r, col), (r + 1, col)) not in m.open and not (r == m.h - 1 and col == m.w - 1):
                    c.line(X(col), Y(r + 1), X(col + 1), Y(r + 1))
        fs = 15 if not solved else 10
        c.setFont(B, fs); c.setFillColor(GREEN)
        c.drawCentredString(X(0.5), Y(0) + 0.12 * inch, "START")
        c.setFillColor(RED)
        c.drawCentredString(X(m.w - 0.5), Y(m.h) - 0.12 * inch - fs * 0.75, "FINISH")
        if solved:
            c.setStrokeColor(RED); c.setLineWidth(max(1.5, cell * 0.18))
            pts = [(X(col + 0.5), Y(r + 0.5)) for r, col in m.path]
            pts = [(pts[0][0], Y(0))] + pts + [(pts[-1][0], Y(m.h))]
            p = c.beginPath(); p.moveTo(*pts[0])
            for pt in pts[1:]:
                p.lineTo(*pt)
            c.drawPath(p, stroke=1, fill=0)

    def cryptogram(self, cg: P.Cryptogram, box):
        c = self.c
        x0, y0, x1, y1 = box
        tracker_h = 1.75 * inch
        bw = 0.6 * inch
        per = int((x1 - x0) // bw)
        def wrap(limit):
            lines, cur = [], ""
            for word in cg.text.split(" "):
                cand = (cur + " " + word) if cur else word
                if len(cand) <= limit:
                    cur = cand
                else:
                    lines.append(cur); cur = word
            return lines + [cur]
        lines = wrap(per)
        for limit in range(math.ceil(len(cg.text) / len(lines)), per + 1):   # same line count, evener lengths
            if len(wrap(limit)) == len(lines):
                lines = wrap(limit); break
        lh = min(1.4 * inch, (y1 - y0 - tracker_h - 0.3 * inch) / len(lines))
        coded = {ch: cg.key[ch] for ch in P.ABC}
        y = y1 - 0.35 * inch
        for line in lines:
            lx = (x0 + x1) / 2 - len(line) * bw / 2
            base = y - 0.62 * inch                    # writing line
            for k, ch in enumerate(line):
                cx = lx + (k + 0.5) * bw
                if ch in coded:
                    c.setStrokeColor(INK); c.setLineWidth(1.6)
                    c.line(cx - bw * 0.38, base, cx + bw * 0.38, base)
                    if ch in cg.hints:
                        c.setFont(B, 28); c.setFillColor(HINT)
                        c.drawCentredString(cx, base + 7, ch)
                    c.setFont(B, 26); c.setFillColor(RED)
                    c.drawCentredString(cx, base - 0.42 * inch, coded[ch])
                elif ch != " ":
                    c.setFont(B, 26); c.setFillColor(INK)
                    c.drawCentredString(cx, base + 7, ch)
            y -= lh
        # letter tracker
        ty = y0 + tracker_h - 0.15 * inch
        centered(c, "Code tracker:  write the real letter under each code letter", (x0 + x1) / 2, ty, R_, 14, SOFT)
        bw2 = (x1 - x0) / 13
        for row in range(2):
            for k in range(13):
                letter = P.ABC[row * 13 + k]
                cx = x0 + (k + 0.5) * bw2
                yy = ty - 0.45 * inch - row * 0.72 * inch
                c.setFont(B, 17); c.setFillColor(RED)
                c.drawCentredString(cx, yy, letter)
                c.setStrokeColor(SOFT); c.setLineWidth(1)
                c.rect(cx - bw2 * 0.36, yy - 0.38 * inch, bw2 * 0.72, 0.3 * inch)
        given = {cg.key[h]: h for h in cg.hints}
        for row in range(2):
            for k in range(13):
                letter = P.ABC[row * 13 + k]
                if letter in given:
                    c.setFont(B, 15); c.setFillColor(HINT)
                    c.drawCentredString(x0 + (k + 0.5) * bw2, ty - 0.45 * inch - row * 0.72 * inch - 0.32 * inch,
                                        given[letter])

    def patterns(self, pats, box):
        c = self.c
        x0, y0, x1, y1 = box
        rh = (y1 - y0) / len(pats)
        bw = (x1 - x0 - 0.5 * inch) / 6
        for i, p in enumerate(pats):
            y = y1 - (i + 0.5) * rh
            c.setFont(B, 17); c.setFillColor(GREEN)
            c.drawString(x0, y - 6, f"{i + 1}.")
            for k in range(6):
                cx = x0 + 0.5 * inch + (k + 0.5) * bw
                c.setStrokeColor(INK if k == 5 else SOFT); c.setLineWidth(2.4 if k == 5 else 1)
                c.roundRect(cx - bw * 0.42, y - 0.3 * inch, bw * 0.84, 0.6 * inch, 8)
                if k < 5:
                    c.setFont(B, 24); c.setFillColor(INK)
                    c.drawCentredString(cx, y - 8, str(p.shown[k]))
                else:
                    c.setFont(B, 24); c.setFillColor(HINT)
                    c.drawCentredString(cx, y - 8, "?")

    def scramble(self, pairs, box):
        c = self.c
        x0, y0, x1, y1 = box
        rh = (y1 - y0) / len(pairs)
        for i, (s, _) in enumerate(pairs):
            y = y1 - (i + 0.55) * rh
            c.setFont(B, 17); c.setFillColor(GREEN)
            c.drawString(x0, y, f"{i + 1}.")
            c.setFont(B, 25); c.setFillColor(RED)
            c.drawString(x0 + 0.5 * inch, y, "  ".join(s))
            c.setStrokeColor(INK); c.setLineWidth(1.4)
            c.line(x0 + 4.1 * inch, y - 3, x1, y - 3)

    def puzzle_page(self, it: Item):
        self.header(it.title, it.how, it.label)
        draw = getattr(self, it.kind)
        draw(it.data, self.area)
        it.page = self.page
        self.next()

    # front / back matter ------------------------------------------------------
    def cover(self, n_puzzles):
        c, W, H = self.c, self.W, self.H
        c.setStrokeColor(RED); c.setLineWidth(6)
        c.rect(0.4 * inch, 0.4 * inch, W - 0.8 * inch, H - 0.8 * inch)
        c.setStrokeColor(GOLD); c.setLineWidth(1.5)
        c.rect(0.55 * inch, 0.55 * inch, W - 1.1 * inch, H - 1.1 * inch)
        centered(c, "LARGE PRINT", W / 2, H - 1.7 * inch, B, 30, GREEN)
        centered(c, "Christmas", W / 2, H - 2.75 * inch, B, 76, RED)
        centered(c, "Puzzle Book", W / 2, H - 3.65 * inch, B, 54, INK)
        # tree
        tx, ty = W / 2, H - 7.6 * inch
        for k, (wd, ht) in enumerate([(2.9, 1.5), (2.3, 1.35), (1.6, 1.2)]):
            y = ty + k * 0.95 * inch
            p = c.beginPath(); p.moveTo(tx - wd / 2 * inch, y); p.lineTo(tx + wd / 2 * inch, y)
            p.lineTo(tx, y + ht * inch); p.close()
            c.setFillColor(GREEN); c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(HexColor("#6D4C2F")); c.rect(tx - 0.22 * inch, ty - 0.4 * inch, 0.44 * inch, 0.4 * inch, fill=1, stroke=0)
        for ox, oy, col in [(-0.8, 0.3, RED), (0.6, 0.45, GOLD), (-0.3, 1.1, GOLD), (0.45, 1.3, RED),
                            (-0.15, 2.05, RED), (0.95, 0.15, GOLD), (-1.05, 0.12, GOLD), (0.2, 0.55, RED)]:
            c.setFillColor(col); c.circle(tx + ox * inch, ty + oy * inch, 0.09 * inch, fill=1, stroke=0)
        c.setFillColor(GOLD)
        star = c.beginPath()
        sy = ty + 3.25 * inch
        for k in range(10):
            a = math.pi / 2 + k * math.pi / 5
            rr = 0.28 * inch if k % 2 == 0 else 0.12 * inch
            (star.moveTo if k == 0 else star.lineTo)(tx + rr * math.cos(a), sy + rr * math.sin(a))
        star.close(); c.drawPath(star, fill=1, stroke=0)
        for sx, sy2, r in [(1.4, 6.6, .25), (W / inch - 1.5, 6.9, .3), (1.9, 4.1, .18), (W / inch - 1.9, 4.4, .2),
                           (1.3, 3.1, .14), (W / inch - 1.3, 3.3, .16)]:
            snowflake(c, sx * inch, sy2 * inch, r * inch, HexColor("#7FA7C9"), 1.4)
        centered(c, f"{n_puzzles} relaxing puzzles  •  Easy to read  •  Answers included", W / 2, 2.15 * inch, B, 17, INK)
        centered(c, "Sudoku  •  Word Search  •  Mazes  •  Carol Code-Breakers", W / 2, 1.7 * inch, R_, 16, SOFT)
        centered(c, "Number Patterns  •  Word Scrambles", W / 2, 1.35 * inch, R_, 16, SOFT)
        self.next(footer=False)

    def how_to(self, answers_page):
        c, W = self.c, self.W
        self.header("How to Play", "A quick guide to each kind of puzzle")
        x0, y0, x1, y1 = self.area
        rules = [
            ("Sudoku", "Fill every empty square so each row, each column and each bold box has every number "
                       "exactly once (1 to 6 in Mini Sudoku, 1 to 9 in Sudoku). No guessing is ever needed."),
            ("Word Search", "Find each word in the grid and circle it. Words go across or down; later puzzles "
                            "also go diagonally. Tick the box next to each word you find."),
            ("Mazes", "Start at START and draw a path to FINISH without crossing a wall. There is exactly one way."),
            ("Carol Code-Breakers", "A line from a classic carol is written in code: every letter has been swapped "
                                    "for another. A few letters are given in grey to get you started."),
            ("Number Patterns", "Look at how the numbers change, then write the number that comes next."),
            ("Word Scrambles", "The letters of a Christmas word have been mixed up. Write the word on the line."),
        ]
        y = y1 - 0.1 * inch
        for name, text in rules:
            c.setFont(B, 21); c.setFillColor(RED); c.drawString(x0, y, name)
            y -= 0.36 * inch
            c.setFont(R_, 17); c.setFillColor(INK)
            line = ""
            for word in text.split():
                if stringWidth(line + " " + word, R_, 17) > x1 - x0:
                    c.drawString(x0, y, line); y -= 0.3 * inch; line = word
                else:
                    line = (line + " " + word).strip()
            c.drawString(x0, y, line)
            y -= 0.5 * inch
        c.setFont(B, 17); c.setFillColor(GREEN)
        c.drawString(x0, y, "Puzzles get a little harder as you go.")
        c.drawString(x0, y - 0.32 * inch, f"Answers start on page {answers_page}.")
        self.next()

    def answers(self, items: list[Item]):
        grids = [it for it in items if it.kind in ("sudoku", "wordsearch", "maze")]
        texts = [it for it in items if it.kind not in ("sudoku", "wordsearch", "maze")]
        x0, y0, x1, y1 = self.area
        mid = (y0 + y1) / 2
        for i in range(0, len(grids), 2):
            self.header("Answers", "Puzzle answers in page order")
            for j, it in enumerate(grids[i:i + 2]):
                top = y1 if j == 0 else mid - 0.1 * inch
                c = self.c
                c.setFont(B, 16); c.setFillColor(RED)
                c.drawString(x0, top - 0.05 * inch, f"Page {it.page}:  {it.title}")
                box = (x0 + 0.9 * inch, top - (y1 - mid) + 0.25 * inch, x1 - 0.9 * inch, top - 0.35 * inch)
                getattr(self, it.kind)(it.data, box, solved=True)
            self.next()
        # text answers
        c = self.c
        blocks = []
        for it in texts:
            lines = []
            if it.kind == "cryptogram":
                lines = [it.data.text, f"from \"{it.data.source}\""]
            elif it.kind == "patterns":
                lines = [f"{k + 1}.  {p.answer}   ({p.rule})" for k, p in enumerate(it.data)]
            else:
                lines = ["   ".join(f"{k + 1}. {w}" for k, (_, w) in enumerate(it.data[r:r + 2], start=r))
                         for r in range(0, len(it.data), 2)]
            blocks.append((f"Page {it.page}:  {it.title}", lines))
        y = None
        for head, lines in blocks:
            need = 0.42 * inch + len(lines) * 0.3 * inch + 0.25 * inch
            if y is None or y - need < y0:
                if y is not None:
                    self.next()
                self.header("Answers", "Puzzle answers in page order")
                y = y1
            c.setFont(B, 17); c.setFillColor(RED); c.drawString(x0, y, head)
            y -= 0.36 * inch
            for ln in lines:
                fs = fit_size(ln, R_, 15, x1 - x0 - 0.2 * inch)
                c.setFont(R_, fs); c.setFillColor(INK); c.drawString(x0 + 0.2 * inch, y, ln)
                y -= 0.3 * inch
            y -= 0.25 * inch
        self.next()

    def save(self):
        self.c.save()


def build(items, path, pagesize):
    bk = Book(path, pagesize)
    bk.cover(len(items))
    answers_page = 3 + len(items)
    bk.how_to(answers_page)
    for it in items:
        bk.puzzle_page(it)
    assert bk.page == answers_page
    bk.answers(items)
    bk.save()
    return bk.page - 1


def previews(pdf: Path, out_dir: Path, dpi=80):
    import pymupdf
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf)
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=dpi).save(out_dir / f"page_{i + 1:02d}.png")
    return len(doc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previews", type=int, default=1)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    items = plan()
    counts = {}
    for it in items:
        counts[it.kind] = counts.get(it.kind, 0) + 1
    print(f"{len(items)} puzzles verified: {counts}")
    for name, size in (("Letter", LETTER), ("A4", A4)):
        path = OUT / f"Large_Print_Christmas_Puzzle_Book_{name}.pdf"
        pages = build(items, path, size)
        print(f"{path.name}: {pages} pages")
    if args.previews:
        n = previews(OUT / "Large_Print_Christmas_Puzzle_Book_Letter.pdf", OUT / "previews")
        print(f"previews: {n} PNGs in {OUT / 'previews'}")


if __name__ == "__main__":
    main()
