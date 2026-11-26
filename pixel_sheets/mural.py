"""Class Mystery Mural: one shared workbook for a whole class.

Tabs
  Class Mural        the big picture (48 x 40), shown on the board
  Teacher Dashboard  names, scores, progress bars, "reveal tile" + "reveal whole mural" switches
  Student 1..30      16 questions each, check marks, score, live preview of the student's own tile
  Key (hidden)       encoded answers (answer*37+1234) and the TRUE/FALSE checks

Every mural square belongs to one question of one student: student s owns tile s (8 x 8), and each of
the 16 questions reveals 4 squares of it. verify() re-reads the saved file and simulates its formulas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

import designs as D
import pixelsheet as P
import questions as Q

MURAL, DASH, KEY = "Class Mural", "Teacher Dashboard", "Key"
TILE, TCOLS, TROWS = 8, 6, 5
STUDENTS = TCOLS * TROWS            # 30
NQ = 16                              # questions per student
ENC_A, ENC_B = 37, 1234              # stored answer = answer * 37 + 1234
M_TOP, M_LEFT = 5, 2                 # mural grid starts at B5
S_TOP = 6                            # student question rows 6..21
S_GRID_COL = 7                       # student preview grid starts at column G
D_TOP = 8                            # dashboard student rows 8..37
D_TOTAL = D_TOP + STUDENTS + 1       # 39
HIDDEN = "FF" + P.HIDDEN_FILL
YELLOW = PatternFill("solid", start_color="FFFFF4B8")
thin = Side(style="thin", color="FFC9CDD6")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
INK, SOFT, GREEN, RED = "FF2B2D42", "FF5C6070", "FF1E7B3A", "FFC0262D"


def student_tab(s: int) -> str:
    return f"Student {s + 1}"


def tile_of(s: int):
    return s // TCOLS, s % TCOLS        # (tile row, tile col)


@dataclass
class Mural:
    design: dict
    topic: str
    title: str
    questions: list                      # [student][question] = (text, answer)
    seed: int = 5

    def owners(self) -> np.ndarray:
        """(H, W, 2) array: student and question index for every mural square."""
        rows = D.expand(self.design)
        h, w = len(rows), len(rows[0])
        assert (h, w) == (TROWS * TILE, TCOLS * TILE), "mural must be 48 x 40"
        own = np.zeros((h, w, 2), int)
        for s in range(STUDENTS):
            tr, tc = tile_of(s)
            part = P.assign_squares(TILE, TILE, NQ, self.seed + s)
            own[tr * TILE:(tr + 1) * TILE, tc * TILE:(tc + 1) * TILE, 0] = s
            own[tr * TILE:(tr + 1) * TILE, tc * TILE:(tc + 1) * TILE, 1] = part
        return own


def make(design: dict, topic: str, seed_base: int = 0) -> Mural:
    gen = Q.GENERATORS[topic]
    qs = [gen(NQ, seed=seed_base + 1000 + s) for s in range(STUDENTS)]
    return Mural(design, topic, f"{design['title']}: Class Mystery Mural", qs)


def key_row(s: int, q: int) -> int:
    return 2 + s * NQ + q


def _color_rules(ws, rng: str, index: dict, colors: dict):
    for c, k in index.items():
        col = "FF" + colors[c]
        ws.conditional_formatting.add(rng, CellIsRule(
            operator="equal", formula=[str(k)], fill=PatternFill("solid", start_color=col, end_color=col),
            font=Font(color=col)))


def _grid_cell(cell):
    cell.fill = PatternFill("solid", start_color=HIDDEN)
    cell.number_format = ";;;"
    w = Side(style="thin", color="FFFFFFFF")
    cell.border = Border(left=w, right=w, top=w, bottom=w)


def build(m: Mural, out: Path, typed: dict | None = None, names: dict | None = None,
          reveal: set | None = None, reveal_all: bool = False) -> Path:
    """typed/names/reveal pre-fill answers for tests: typed = {student: [answers]}."""
    rows = D.expand(m.design)
    letters = sorted(set("".join(rows)), key=lambda c: (c != ".", c))
    index = {c: i + 1 for i, c in enumerate(letters)}
    own = m.owners()
    total = STUDENTS * NQ

    wb = Workbook()
    mural = wb.active
    mural.title = MURAL
    dash = wb.create_sheet(DASH)
    studs = [wb.create_sheet(student_tab(s)) for s in range(STUDENTS)]
    key = wb.create_sheet(KEY)

    # ---- key
    key.append(["Student", "Code", "Correct?", "Revealed?"])
    for s in range(STUDENTS):
        for q, (_, a) in enumerate(m.questions[s]):
            r = key_row(s, q)
            key.cell(r, 1, s + 1)
            key.cell(r, 2, int(a) * ENC_A + ENC_B)
            key.cell(r, 3, f"=IFERROR(VALUE(TRIM('{student_tab(s)}'!D{S_TOP + q}&\"\"))*{ENC_A}+{ENC_B}=B{r},FALSE)")
            key.cell(r, 4, f"=OR(C{r},UPPER(TRIM('{DASH}'!$H${D_TOP + s}&\"\"))=\"Y\","
                           f"UPPER(TRIM('{DASH}'!$C$4&\"\"))=\"Y\")")
    key.sheet_state = "hidden"

    # ---- mural
    mural.sheet_view.showGridLines = False
    mural["B1"] = m.title
    mural["B1"].font = Font(bold=True, size=20, color=INK)
    mural["B2"] = "Every correct answer from every student reveals part of this picture. Let's finish it together!"
    mural["B2"].font = Font(italic=True, size=11, color=SOFT)
    mural["B3"] = (f"=\"Class progress: \"&'{DASH}'!E{D_TOTAL}&\" / {total} correct answers (\"&"
                   f"TEXT('{DASH}'!E{D_TOTAL}/{total},\"0%\")&\")\"")
    mural["B3"].font = Font(bold=True, size=14, color=GREEN)
    h, w = len(rows), len(rows[0])
    for y in range(h):
        mural.row_dimensions[M_TOP + y].height = 16
        for x in range(w):
            s, q = own[y, x]
            c = mural.cell(M_TOP + y, M_LEFT + x, f'=IF({KEY}!$D${key_row(s, q)},{index[rows[y][x]]},"")')
            _grid_cell(c)
    mural.column_dimensions["A"].width = 2
    for x in range(w):
        mural.column_dimensions[L(M_LEFT + x)].width = 2.3
    _color_rules(mural, f"{L(M_LEFT)}{M_TOP}:{L(M_LEFT + w - 1)}{M_TOP + h - 1}", index, m.design["colors"])

    # ---- dashboard
    dash.sheet_view.showGridLines = False
    dash["B1"] = "Teacher Dashboard"
    dash["B1"].font = Font(bold=True, size=20, color=INK)
    dash["B2"] = ("Share this spreadsheet with your class (students can edit). Each student opens their own "
                  "tab. Type Y under Reveal to uncover the tile of an absent student or an empty seat.")
    dash["B2"].font = Font(italic=True, size=10, color=SOFT)
    dash["B4"] = "Reveal whole mural (type Y):"
    dash["B4"].font = Font(bold=True, color=INK)
    dash["C4"].fill, dash["C4"].border = YELLOW, BOX
    if reveal_all:
        dash["C4"] = "Y"
    heads = ["#", "Tile on the mural", "Student name", "Correct", "%", "Progress", "Reveal (Y)"]
    for i, t in enumerate(heads):
        c = dash.cell(D_TOP - 1, 2 + i, t)
        c.font = Font(bold=True, color="FFFFFFFF")
        c.fill = PatternFill("solid", start_color="FF2B2D42")
    for s in range(STUDENTS):
        r = D_TOP + s
        tr, tc = tile_of(s)
        tab = student_tab(s)
        dash.cell(r, 2, s + 1)
        dash.cell(r, 3, f"{tab}: row {tr + 1}, column {tc + 1}")
        dash.cell(r, 4, f"='{tab}'!D2&\"\"")
        dash.cell(r, 5, f"=COUNTIF('{tab}'!E{S_TOP}:E{S_TOP + NQ - 1},\"✓\")")
        dash.cell(r, 6, f"=E{r}/{NQ}").number_format = "0%"
        dash.cell(r, 7, f"=REPT(\"■\",E{r})").font = Font(color=GREEN)
        c = dash.cell(r, 8)
        c.fill, c.border, c.alignment = YELLOW, BOX, Alignment(horizontal="center")
        if reveal and s in reveal:
            c.value = "Y"
        if s % 2:
            for col in range(2, 8):
                dash.cell(r, col).fill = PatternFill("solid", start_color="FFF4F5F8")
    dash.cell(D_TOTAL, 4, "Class total").font = Font(bold=True)
    dash.cell(D_TOTAL, 5, f"=SUM(E{D_TOP}:E{D_TOP + STUDENTS - 1})").font = Font(bold=True)
    c = dash.cell(D_TOTAL, 6, f"=E{D_TOTAL}/{total}")
    c.number_format, c.font = "0%", Font(bold=True)
    for col, wd in zip("ABCDEFGH", [2, 5, 30, 22, 9, 7, 20, 11]):
        dash.column_dimensions[col].width = wd

    # ---- student tabs
    for s, ws in enumerate(studs):
        tr, tc = tile_of(s)
        ws.sheet_view.showGridLines = False
        ws["B1"] = m.title
        ws["B1"].font = Font(bold=True, size=16, color=INK)
        ws["C2"] = "Your name:"
        ws["C2"].font = Font(bold=True, color=INK)
        ws["C2"].alignment = Alignment(horizontal="right")
        ws.merge_cells("D2:F2")
        for col in "DEF":
            ws[f"{col}2"].fill, ws[f"{col}2"].border = YELLOW, BOX
        if names and s in names:
            ws["D2"] = names[s]
        ws["B3"] = (f"You are {student_tab(s)}. Every correct answer reveals part of YOUR piece of the class "
                    f"mural (row {tr + 1}, column {tc + 1}).")
        ws["B3"].font = Font(italic=True, size=10, color=SOFT)
        ws["B4"] = f'="Correct: "&COUNTIF(E{S_TOP}:E{S_TOP + NQ - 1},"✓")&" / {NQ}"'
        ws["B4"].font = Font(bold=True, size=12, color=GREEN)
        for col, t in zip("BCD", ["#", "Question", "Answer"]):
            ws[f"{col}{S_TOP - 1}"] = t
            ws[f"{col}{S_TOP - 1}"].font = Font(bold=True, color=SOFT)
        ws.cell(S_TOP - 1, S_GRID_COL, "Your piece of the mural").font = Font(bold=True, color=SOFT)
        given = (typed or {}).get(s, [])
        for q, (text, a) in enumerate(m.questions[s]):
            r = S_TOP + q
            ws[f"B{r}"] = q + 1
            ws[f"B{r}"].font = Font(size=10, color="FF8A8FA0")
            ws[f"C{r}"] = text
            ws[f"C{r}"].font = Font(size=12)
            ws[f"D{r}"].fill, ws[f"D{r}"].border = YELLOW, BOX
            ws[f"D{r}"].alignment = Alignment(horizontal="center")
            if q < len(given) and given[q] not in (None, ""):
                ws[f"D{r}"] = given[q]
            ws[f"E{r}"] = f'=IF(D{r}="","",IF({KEY}!$C${key_row(s, q)},"✓","✗"))'
            ws[f"E{r}"].alignment = Alignment(horizontal="center")
            ws.row_dimensions[r].height = 20
        last = S_TOP + NQ - 1
        ws.conditional_formatting.add(f"E{S_TOP}:E{last}", CellIsRule(operator="equal", formula=['"✓"'],
            fill=PatternFill("solid", start_color="FFD8F3DC", end_color="FFD8F3DC"), font=Font(bold=True, color=GREEN)))
        ws.conditional_formatting.add(f"E{S_TOP}:E{last}", CellIsRule(operator="equal", formula=['"✗"'],
            fill=PatternFill("solid", start_color="FFFDE2E1", end_color="FFFDE2E1"), font=Font(bold=True, color=RED)))
        for y in range(TILE):
            for x in range(TILE):
                my, mx = tr * TILE + y, tc * TILE + x
                s2, q = own[my, mx]
                assert s2 == s
                c = ws.cell(S_TOP + y, S_GRID_COL + x, f'=IF({KEY}!$D${key_row(s, q)},{index[rows[my][mx]]},"")')
                _grid_cell(c)
        _color_rules(ws, f"{L(S_GRID_COL)}{S_TOP}:{L(S_GRID_COL + TILE - 1)}{S_TOP + TILE - 1}",
                     index, m.design["colors"])
        for col, wd in zip("ABCDEF", [2, 4, 14, 9, 4, 3]):
            ws.column_dimensions[col].width = wd
        for x in range(TILE):
            ws.column_dimensions[L(S_GRID_COL + x)].width = 3.2

    wb.active = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


# ------------------------------------------------------------------ checking

KEY_C = re.compile(r"^=IFERROR\(VALUE\(TRIM\('(.+)'!D(\d+)&\"\"\)\)\*37\+1234=B(\d+),FALSE\)$")
KEY_D = re.compile(r"^=OR\(C(\d+),UPPER\(TRIM\('Teacher Dashboard'!\$H\$(\d+)&\"\"\)\)=\"Y\","
                   r"UPPER\(TRIM\('Teacher Dashboard'!\$C\$4&\"\"\)\)=\"Y\"\)$")
GRID = re.compile(r'^=IF\(Key!\$D\$(\d+),(\d+),""\)$')


def _num(t):
    try:
        return float(str(t).strip())
    except ValueError:
        return None


def parse(path: Path) -> dict:
    wb = load_workbook(path)
    key = wb[KEY]
    rows = {}
    for r in range(2, key.max_row + 1):
        mc, md = KEY_C.match(str(key.cell(r, 3).value)), KEY_D.match(str(key.cell(r, 4).value))
        assert mc and md and int(mc.group(3)) == r and int(md.group(1)) == r, f"bad Key row {r}"
        rows[r] = dict(tab=mc.group(1), arow=int(mc.group(2)), code=key.cell(r, 2).value, dash=int(md.group(2)))

    def grid(ws, top, left, h, w):
        g = np.zeros((h, w, 2), int)
        for y in range(h):
            for x in range(w):
                mm = GRID.match(str(ws.cell(top + y, left + x).value))
                assert mm, f"{ws.title}!{L(left + x)}{top + y}: {ws.cell(top + y, left + x).value}"
                g[y, x] = int(mm.group(1)), int(mm.group(2))
        return g

    def rules(ws):
        out = {}
        for cf in ws.conditional_formatting:
            for rule in cf.rules:
                if rule.operator == "equal" and rule.formula[0].isdigit():
                    out[int(rule.formula[0])] = rule.dxf.fill.fgColor.rgb[-6:].upper()
        return out

    info = {"key": rows, "mural": grid(wb[MURAL], M_TOP, M_LEFT, TROWS * TILE, TCOLS * TILE),
            "mural_rules": rules(wb[MURAL]), "students": {}}
    for s in range(STUDENTS):
        ws = wb[student_tab(s)]
        info["students"][s] = {"grid": grid(ws, S_TOP, S_GRID_COL, TILE, TILE), "rules": rules(ws),
                               "questions": [ws[f"C{S_TOP + q}"].value for q in range(NQ)]}
    assert [ws.title for ws in wb.worksheets][:2] == [MURAL, DASH] and wb[KEY].sheet_state == "hidden"
    return info


def revealed_rows(info, typed: dict, flags: set = frozenset(), reveal_all=False) -> set:
    """typed = {(tab, answer row): text}; flags = dashboard rows with Y."""
    out = set()
    for r, k in info["key"].items():
        v = _num(typed.get((k["tab"], k["arow"]), ""))
        ok = v is not None and v * ENC_A + ENC_B == k["code"]
        if ok or k["dash"] in flags or reveal_all:
            out.add(r)
    return out


def picture(g: np.ndarray, rev: set) -> np.ndarray:
    keyrows, k = g[..., 0], g[..., 1]
    return np.where(np.isin(keyrows, list(rev)), k, 0)


def verify(path: Path, m: Mural) -> list[str]:
    info = parse(path)
    rows = D.expand(m.design)
    letters = sorted(set("".join(rows)), key=lambda c: (c != ".", c))
    index = {c: i + 1 for i, c in enumerate(letters)}
    expect = np.array([[index[c] for c in r] for r in rows])
    rep = []
    # questions and encoded answers
    for s in range(STUDENTS):
        Q.verify(m.questions[s])
        assert info["students"][s]["questions"] == [t for t, _ in m.questions[s]], f"student {s + 1} questions"
        for q, (_, a) in enumerate(m.questions[s]):
            k = info["key"][key_row(s, q)]
            assert k["tab"] == student_tab(s) and k["arow"] == S_TOP + q and k["dash"] == D_TOP + s
            assert (k["code"] - ENC_B) / ENC_A == int(a), f"student {s + 1} q{q + 1} code"
    right = {(student_tab(s), S_TOP + q): a for s in range(STUDENTS) for q, (_, a) in enumerate(m.questions[s])}
    wrong = {kk: str(int(v) + 1) for kk, v in right.items()}
    allrev = revealed_rows(info, right)
    assert (picture(info["mural"], allrev) == expect).all(), "full mural differs from the design"
    assert (picture(info["mural"], revealed_rows(info, wrong)) == 0).all(), "wrong answers reveal squares"
    assert (picture(info["mural"], revealed_rows(info, {})) == 0).all(), "empty sheet reveals squares"
    assert (picture(info["mural"], revealed_rows(info, {}, reveal_all=True)) == expect).all(), "reveal-all"
    count = np.zeros(expect.shape, int)
    for s in range(STUDENTS):
        tr, tc = tile_of(s)
        tile = np.zeros(expect.shape, bool)
        tile[tr * TILE:(tr + 1) * TILE, tc * TILE:(tc + 1) * TILE] = True
        mine = {kk: v for kk, v in right.items() if kk[0] == student_tab(s)}
        got = picture(info["mural"], revealed_rows(info, mine)) > 0
        assert (got == tile).all(), f"student {s + 1} answers reveal outside their tile"
        flag = picture(info["mural"], revealed_rows(info, {}, flags={D_TOP + s})) > 0
        assert (flag == tile).all(), f"reveal switch of student {s + 1}"
        prev = picture(info["students"][s]["grid"], revealed_rows(info, mine))
        assert (prev == expect[tr * TILE:(tr + 1) * TILE, tc * TILE:(tc + 1) * TILE]).all(), f"preview {s + 1}"
        for q in range(NQ):
            one = picture(info["mural"], revealed_rows(info, {(student_tab(s), S_TOP + q): m.questions[s][q][1]})) > 0
            assert one.sum() > 0 and (one <= tile).all(), f"student {s + 1} q{q + 1}"
            count += one
        assert info["students"][s]["rules"] == info["mural_rules"]
    assert (count == 1).all(), "every square must belong to exactly one question"
    for c, k in index.items():
        assert info["mural_rules"].get(k) == m.design["colors"][c].upper(), f"color {k}"
    # typing variations that must count as correct / wrong
    s0, a0 = 0, m.questions[0][0][1]
    for t, ok in [(f" {a0} ", True), (f"{a0}.0", True), (int(a0), True), ("", False), ("abc", False), (f"{a0}0", False)]:
        rev = revealed_rows(info, {(student_tab(0), S_TOP): t})
        assert (key_row(0, 0) in rev) == ok, f"typed {t!r}"
    rep.append(f"OK  {path.name}: {expect.size} mural squares exact, {STUDENTS} students x {NQ} questions, "
               f"tiles, previews, reveal switches and {len(index)} colors all checked")
    return rep
