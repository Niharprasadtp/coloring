"""Mystery pixel-art spreadsheets (Excel + Google Sheets).

How the sheet works
-------------------
* Puzzle tab: questions on the left, a grid on the right.
* Hidden "Key" tab: the answers, and one TRUE/FALSE check per question.
* Every grid square holds  =IF(Key!$C$r, k, "")  -> the color number k shows up only when
  the question that owns this square is answered correctly.
* One conditional-format rule per color ("cell = k -> fill with color k"). The number itself is
  hidden with the ;;; number format. These simple rules work in Excel and Google Sheets.

verify() re-opens the saved .xlsx and simulates the formulas: every square must come out exactly
the design's color when all answers are right, and nothing may show when answers are wrong.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw

import designs as D
import questions as Q

TOP = 5                  # first row of questions / grid
GRID_COL = 7             # column G: first grid column
HIDDEN_FILL = "E4E6EB"   # grid squares before they are revealed
KEY = "Key"


@dataclass
class Puzzle:
    name: str            # tab name
    design: dict
    questions: list      # [(question text, answer text)]
    seed: int = 1        # how the grid is split between questions


def assign_squares(h: int, w: int, n: int, seed: int = 1) -> np.ndarray:
    """Split the grid into n compact patches (one per question), all about the same size."""
    rng = np.random.default_rng(seed)
    pts = np.array([(y, x) for y in range(h) for x in range(w)], float)
    cent = pts[rng.choice(len(pts), n, replace=False)]
    size = len(pts) / n
    for _ in range(40):
        # balanced assignment: fill the nearest patch that still has room
        d = ((pts[:, None, :] - cent[None]) ** 2).sum(-1)
        lab = np.full(len(pts), -1)
        room = np.full(n, int(np.ceil(size)))
        for i in np.argsort(d.min(1)):
            for c in np.argsort(d[i]):
                if room[c] > 0:
                    lab[i] = c; room[c] -= 1
                    break
        cent = np.array([pts[lab == c].mean(0) for c in range(n)])
    return lab.reshape(h, w)


def _hex(c: str) -> str:
    return "FF" + c.upper()


def build(puzzles: list[Puzzle], out: Path, title: str, answers: dict | None = None) -> Path:
    """answers: optional {tab name: [typed answers]} to pre-fill (used only for testing)."""
    wb = Workbook()
    wb.remove(wb.active)
    key = wb.create_sheet(KEY)
    key.append(["Puzzle", "Answer", "Correct?"])
    krow = 1
    thin = Side(style="thin", color="FFC9CDD6")

    for p in puzzles:
        D.check(p.design)
        Q.verify(p.questions)
        rows = D.expand(p.design)
        h, w, nq = len(rows), len(rows[0]), len(p.questions)
        letters = sorted(set("".join(rows)), key=lambda c: (c != ".", c))
        index = {c: i + 1 for i, c in enumerate(letters)}       # color number per letter
        owner = assign_squares(h, w, nq, p.seed)

        ws = wb.create_sheet(p.name)
        ws.sheet_view.showGridLines = False
        ws.sheet_view.zoomScale = 100
        ws["B1"] = title
        ws["B1"].font = Font(bold=True, size=16, color="FF2B2D42")
        ws["B2"] = "Type each answer in the yellow box. Every correct answer reveals part of the mystery picture!"
        ws["B2"].font = Font(italic=True, size=10, color="FF5C6070")
        last = TOP + nq - 1
        ws["B3"] = f'="Correct: "&COUNTIF(E{TOP}:E{last},"✓")&" / {nq}"'
        ws["B3"].font = Font(bold=True, size=12, color="FF1E7B3A")
        for c, t in zip("BCDE", ["#", "Question", "Answer", ""]):
            ws[f"{c}{TOP - 1}"] = t
            ws[f"{c}{TOP - 1}"].font = Font(bold=True, color="FF5C6070")

        given = (answers or {}).get(p.name, [])
        for i, (q, a) in enumerate(p.questions):
            r = TOP + i
            krow += 1
            key.cell(krow, 1, p.name)
            key.cell(krow, 2, a).number_format = "@"
            key.cell(krow, 3, f'=LOWER(TRIM(\'{p.name}\'!D{r}&""))=LOWER(B{krow})')
            ws[f"B{r}"] = i + 1
            ws[f"C{r}"] = q
            ws[f"D{r}"].fill = PatternFill("solid", start_color="FFFFF4B8")
            ws[f"D{r}"].border = Border(left=thin, right=thin, top=thin, bottom=thin)
            ws[f"D{r}"].alignment = Alignment(horizontal="center")
            if i < len(given) and given[i] != "":
                ws[f"D{r}"] = given[i]
            ws[f"E{r}"] = f'=IF(D{r}="","",IF({KEY}!$C${krow},"✓","✗"))'
            ws[f"E{r}"].alignment = Alignment(horizontal="center")
            for c in "BC":
                ws[f"{c}{r}"].font = Font(size=12)
            ws[f"B{r}"].font = Font(size=10, color="FF8A8FA0")
            # this question's squares
            for y in range(h):
                for x in range(w):
                    if owner[y, x] == i:
                        ws.cell(TOP + y, GRID_COL + x, f'=IF({KEY}!$C${krow},{index[rows[y][x]]},"")')

        ok_green = PatternFill("solid", start_color="FFD8F3DC", end_color="FFD8F3DC")
        bad_red = PatternFill("solid", start_color="FFFDE2E1", end_color="FFFDE2E1")
        ws.conditional_formatting.add(f"E{TOP}:E{last}", CellIsRule(operator="equal", formula=['"✓"'],
                                      fill=ok_green, font=Font(bold=True, color="FF1E7B3A")))
        ws.conditional_formatting.add(f"E{TOP}:E{last}", CellIsRule(operator="equal", formula=['"✗"'],
                                      fill=bad_red, font=Font(bold=True, color="FFC0262D")))

        grid = f"{get_column_letter(GRID_COL)}{TOP}:{get_column_letter(GRID_COL + w - 1)}{TOP + h - 1}"
        for c, k in index.items():
            col = _hex(p.design["colors"][c])
            ws.conditional_formatting.add(grid, CellIsRule(
                operator="equal", formula=[str(k)],
                fill=PatternFill("solid", start_color=col, end_color=col), font=Font(color=col)))
        hidden = PatternFill("solid", start_color=_hex(HIDDEN_FILL))
        for y in range(h):
            ws.row_dimensions[TOP + y].height = 18
            for x in range(w):
                cell = ws.cell(TOP + y, GRID_COL + x)
                cell.fill = hidden
                cell.number_format = ";;;"
                cell.border = Border(left=Side(style="thin", color="FFFFFFFF"), right=Side(style="thin", color="FFFFFFFF"),
                                     top=Side(style="thin", color="FFFFFFFF"), bottom=Side(style="thin", color="FFFFFFFF"))
        for r in range(TOP, last + 1):
            ws.row_dimensions[r].height = max(ws.row_dimensions[r].height or 0, 18)
        ws.column_dimensions["A"].width = 2
        ws.column_dimensions["B"].width = 4
        ws.column_dimensions["C"].width = 14
        ws.column_dimensions["D"].width = 9
        ws.column_dimensions["E"].width = 4
        ws.column_dimensions["F"].width = 3
        for x in range(w):
            ws.column_dimensions[get_column_letter(GRID_COL + x)].width = 2.6

    key.sheet_state = "hidden"
    key.column_dimensions["A"].width = 18
    wb.move_sheet(KEY, offset=len(wb.sheetnames))
    wb.active = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


# ---------------------------------------------------------------- checking

GRID_RE = re.compile(r'^=IF\(Key!\$C\$(\d+),(\d+),""\)$')
KEY_RE = re.compile(r"^=LOWER\(TRIM\('(.+)'!D(\d+)&\"\"\)\)=LOWER\(B(\d+)\)$")


def parse(path: Path) -> dict:
    """Read the saved workbook's formulas once."""
    wb = load_workbook(path)
    key = wb[KEY]
    checks = {}                                   # Key row -> (tab, answer row, answer text)
    for r in range(2, key.max_row + 1):
        m = KEY_RE.match(str(key.cell(r, 3).value))
        assert m and int(m.group(3)) == r, f"bad Key formula row {r}"
        checks[r] = (m.group(1), int(m.group(2)), str(key.cell(r, 2).value))
    tabs = {}
    for ws in wb.worksheets:
        if ws.title == KEY:
            continue
        cells = {}
        for row in ws.iter_rows(min_row=TOP, min_col=GRID_COL):
            for c in row:
                if c.value is None:
                    continue
                m = GRID_RE.match(str(c.value))
                assert m, f"{ws.title}!{c.coordinate}: unexpected {c.value}"
                cells[(c.row - TOP, c.column - GRID_COL)] = (int(m.group(1)), int(m.group(2)))
        rules = {}
        for cf in ws.conditional_formatting:
            for rule in cf.rules:
                if rule.operator == "equal" and rule.formula[0].isdigit():
                    rules[int(rule.formula[0])] = rule.dxf.fill.fgColor.rgb[-6:].upper()
        questions = {r: ws[f"C{r}"].value for r in range(TOP, ws.max_row + 1) if ws[f"C{r}"].value}
        tabs[ws.title] = {"cells": cells, "rules": rules, "questions": questions}
    return {"checks": checks, "tabs": tabs}


def simulate(wbinfo: dict, tab: str, typed: dict) -> np.ndarray:
    """Evaluate the formulas of one tab. typed: {answer row: text} -> color-number grid (0 = hidden)."""
    ok = {r: (t == tab and str(typed.get(qr, "")).strip().lower() == a.lower())
          for r, (t, qr, a) in wbinfo["checks"].items()}
    cells = wbinfo["tabs"][tab]["cells"]
    h = max(y for y, _ in cells) + 1
    w = max(x for _, x in cells) + 1
    g = np.zeros((h, w), int)
    for (y, x), (kr, k) in cells.items():
        g[y, x] = k if ok[kr] else 0
    return g


def verify(path: Path, puzzles: list[Puzzle]) -> list[str]:
    info = parse(path)
    report = []
    for p in puzzles:
        rows = D.expand(p.design)
        h, w = len(rows), len(rows[0])
        letters = sorted(set("".join(rows)), key=lambda c: (c != ".", c))
        index = {c: i + 1 for i, c in enumerate(letters)}
        expect = np.array([[index[c] for c in r] for r in rows])
        tab = info["tabs"][p.name]
        assert len(tab["cells"]) == h * w, f"{p.name}: {len(tab['cells'])} squares, expected {h * w}"
        # the questions in the sheet are the ones we checked, and the Key holds their answers
        for i, (q, a) in enumerate(p.questions):
            assert tab["questions"].get(TOP + i) == q, f"{p.name}: question {i + 1} text differs"
            kr = [r for r, (t, qr, _) in info["checks"].items() if t == p.name and qr == TOP + i]
            assert len(kr) == 1 and info["checks"][kr[0]][2] == a, f"{p.name}: key for question {i + 1}"
        right = {TOP + i: a for i, (_, a) in enumerate(p.questions)}
        wrong = {TOP + i: str(int(a) + 1) for i, (_, a) in enumerate(p.questions)}
        g = simulate(info, p.name, right)
        assert g.shape == expect.shape and (g == expect).all(), f"{p.name}: picture mismatch"
        assert (simulate(info, p.name, wrong) == 0).all(), f"{p.name}: wrong answers reveal squares"
        total = np.zeros((h, w), int)
        for i, (_, a) in enumerate(p.questions):
            one = simulate(info, p.name, {TOP + i: a})
            assert (one > 0).sum() > 0, f"{p.name}: question {i + 1} reveals nothing"
            total += one > 0
        assert (total == 1).all(), f"{p.name}: every square must belong to exactly one question"
        for c, k in index.items():
            assert tab["rules"].get(k) == p.design["colors"][c].upper(), f"{p.name}: color {k} rule wrong"
        report.append(f"OK  {p.name} ({p.design['title']}): {h * w} squares exact, "
                      f"{len(p.questions)} questions, {len(index)} colors")
    return report


def preview(p: Puzzle, out: Path, reveal: float = 1.0, cell: int = 24, seed: int = 3) -> Path:
    """Picture of the grid with a fraction of the questions answered (for listing photos)."""
    rows = D.expand(p.design)
    h, w, nq = len(rows), len(rows[0]), len(p.questions)
    owner = assign_squares(h, w, nq, p.seed)
    shown = set(np.random.default_rng(seed).permutation(nq)[: round(reveal * nq)])
    img = Image.new("RGB", (w * cell, h * cell), "white")
    d = ImageDraw.Draw(img)
    for y in range(h):
        for x in range(w):
            col = p.design["colors"][rows[y][x]] if owner[y, x] in shown else HIDDEN_FILL
            d.rectangle([x * cell, y * cell, x * cell + cell - 2, y * cell + cell - 2], fill="#" + col)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out
