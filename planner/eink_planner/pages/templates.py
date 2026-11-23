"""Duplicate-ready template library: an index page plus one clean page per template."""

from __future__ import annotations

import math
from datetime import date

from ..geometry import Rect
from ..ink import BOLD, REGULAR
from ..widgets import checklist, habit_grid, habit_matrix, lines_box, numbered_lines, page_header, section, table
from .workspace import field


# --- template bodies (each draws into the body rect r) -----------------------------------
def _lined(P, r):
    P.ink.hlines(r, P.m.ruled)


def _narrow(P, r):
    P.ink.hlines(r, P.m.mm(5 if P.m.compact else 5.5))


def _dots(P, r):
    P.ink.dots(r)


def _graph(P, r):
    P.ink.grid(r, major=5)


def _iso(P, r):
    P.ink.dots(r, P.m.dot, iso=True)


def _blank(P, r):
    pass


def _cornell(P, r):
    ink, m, t = P.ink, P.m, P.t
    main, summary = r.rows([0.78, 0.22], m.space)
    cue, notes = main.cols([0.3, 0.7], m.space)
    lines_box(ink, cue, "Cues & questions")
    lines_box(ink, notes, "Notes")
    ink.line(cue.right + m.space / 2, main.y, cue.right + m.space / 2, main.top, t.soft, m.lw_box)
    ink.line(r.x, summary.top + m.space / 2, r.right, summary.top + m.space / 2, t.soft, m.lw_box)
    lines_box(ink, summary, "Summary")


def _meeting(P, r):
    ink, m = P.ink, P.m
    sp = m.space * 1.5
    fh = m.mm(8 if m.compact else 9.5)
    meta, r = r.take_top(fh, sp)
    for lb, c in zip(("Meeting", "Date", "Time"), meta.cols([2, 1, 1], m.space)):
        field(ink, c, lb)
    att, r = r.take_top(fh, sp)
    field(ink, att, "Attendees")
    agenda, r = r.take_top(m.fs_label + 3 * m.ruled, sp)
    lines_box(ink, agenda, "Agenda")
    notes, acts = r.rows([0.6, 0.4], sp)
    lines_box(ink, notes, "Discussion")
    table(ink, section(ink, acts, "Action items"), [("Action", 4), ("Owner", 1.5), ("Due", 1.2)])


def _matrix(P, r):
    ink, m, t = P.ink, P.m, P.t
    axis = m.mm(6)
    top_lab, r = r.take_top(axis)
    side_lab, grid = r.take_left(axis)
    cols = grid.cols(2, m.space)
    for lb, c in zip(("URGENT", "NOT URGENT"), cols):
        ink.text(c.cx, top_lab.y + m.mm(1.5), lb, m.fs_label, BOLD, t.muted, "center",
                 tracking=m.fs_label * 0.1)
    rows = grid.rows(2, m.space)
    for lb, rr in zip(("IMPORTANT", "NOT IMPORTANT"), rows):
        c = ink.c
        c.saveState()
        c.translate(side_lab.x + m.mm(4), rr.cy)
        c.rotate(90)
        ink.text(0, 0, lb, m.fs_label, BOLD, t.muted, "center", tracking=m.fs_label * 0.1)
        c.restoreState()
    quads = [("Do first", 3), ("Schedule", 2), ("Delegate", 4), ("Eliminate", 1)]
    for (title, q), cell in zip(quads, [c for row in grid.grid(2, 2, m.space, m.space) for c in row]):
        ink.box(cell, fill=t.qt(q), radius=m.radius)
        inner = cell.inset(m.mm(2.5))
        checklist(ink, inner, title)


def _pomodoro(P, r):
    ink, m, t = P.ink, P.m, P.t
    top, bottom = r.rows([0.68, 0.32], m.space * 1.5)
    body = section(ink, top, "Focus sessions — fill one tomato per 25 minutes")
    n_tom = 6 if m.compact else 8
    cols = table(ink, body, [("Task", 3), ("Sessions", 3 if not m.compact else 2.6), ("Done", 0.8)],
                 row_h=m.mm(8 if m.compact else 9.5))
    hdr_h = m.mm(6)
    row_h = m.mm(8 if m.compact else 9.5)
    n = int(cols[0].h // row_h)
    sess = cols[1]
    for i in range(n):
        cy = sess.top - (i + 0.5) * row_h
        step = sess.w / n_tom
        rad = min(step * 0.3, row_h * 0.28)
        for k in range(n_tom):
            ink.circle(sess.x + (k + 0.5) * step, cy, rad, stroke=t.rule, width=m.lw_box)
        ink.checkbox(cols[2].cx - m.mm(1.4), cy)
    a, b = bottom.cols(2, m.space * 1.5)
    lines_box(ink, a, "Distractions")
    lines_box(ink, b, "Wins & notes")


def _routine(P, r):
    ink, m = P.ink, P.m
    parts = r.cols(3, m.space * 1.5) if P.opts.landscape else r.rows(3, m.space * 1.5)
    for title, part in zip(("Morning", "Afternoon", "Evening"), parts):
        table(ink, section(ink, part, title), [("Time", 1), ("Routine", 4), ("Done", 0.9)],
              row_h=m.ruled * 0.95)


def _habits(P, r):
    ink, m, t = P.ink, P.m, P.t
    head, r = r.take_top(m.mm(8), m.space)
    for lb, c in zip(("Month", "Focus"), head.cols([1, 2], m.space)):
        field(ink, c, lb)
    if (r.w - min(m.mm(32), r.w * 0.22)) / 31 >= m.mm(3.4):
        habit_matrix(ink, r, [date(2027, 1, d) for d in range(1, 32)],
                     9 if P.opts.landscape else 12)
    else:
        habit_grid(ink, r, [str(i) for i in range(1, 32)], 6)


def _reading(P, r):
    cols = ([("Title", 3), ("Author", 2), ("Done", 1), ("Rating", 1)] if P.m.compact else
            [("Title", 3.4), ("Author", 2.2), ("Genre", 1.4), ("Started", 1.2), ("Finished", 1.2),
             ("Rating", 1.1)])
    table(P.ink, r, cols, row_h=P.m.ruled * 1.15)


def _budget(P, r):
    ink, m = P.ink, P.m
    head, r = r.take_top(m.mm(8), m.space * 1.5)
    for lb, c in zip(("Month", "Income", "Savings goal"), head.cols(3, m.space)):
        field(ink, c, lb)
    main, summary = r.rows([0.78, 0.22], m.space * 1.5)
    table(ink, section(ink, main, "Expenses"),
          [("Category", 3), ("Planned", 1.4), ("Actual", 1.4), ("Difference", 1.5)])
    cells = summary.cols(3, m.space)
    for lb, c in zip(("Total income", "Total spent", "Left over"), cells):
        ink.box(c, stroke=P.t.rule, radius=m.radius, width=m.lw_grid)
        ink.text(c.x + m.mm(2), c.top - m.mm(2) - m.fs_small * 0.7, lb.upper(), m.fs_small, BOLD,
                 P.t.muted)


def _bills(P, r):
    ink, m = P.ink, P.m
    if m.compact or r.w < m.mm(150):
        table(ink, r, [("Bill", 3), ("Due", 1), ("Amount", 1.4), ("Paid", 0.9)], row_h=m.ruled * 1.1)
        return
    cols = [("Bill", 3), ("Due", 1), ("Amount", 1.4)] + [(mo, 0.62) for mo in
                                                         ("J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D")]
    rects = table(ink, r, cols, row_h=m.ruled * 1.15)
    row_h = m.ruled * 1.15
    n = int(rects[0].h // row_h + 0.01)
    for c in rects[3:]:
        for i in range(n):
            ink.checkbox(c.cx - m.mm(1.3), c.top - (i + 0.5) * row_h, m.mm(2.6))


def _debt(P, r):
    ink, m, t = P.ink, P.m, P.t
    top, bottom = r.rows([0.5, 0.5], m.space * 1.5)
    table(ink, section(ink, top, "Debts"),
          [("Debt", 2.6), ("Balance", 1.4), ("Rate", 1), ("Min pay", 1.3), ("Paid off", 1.2)])
    body = section(ink, bottom, "Payoff progress — shade one box per $____ paid")
    _box_grid(P, body, 10, 5 if not P.opts.landscape else 4)


def _savings(P, r):
    ink, m = P.ink, P.m
    head, r = r.take_top(m.mm(8), m.space * 1.5)
    for lb, c in zip(("Saving for", "Goal amount", "By"), head.cols([2, 1, 1], m.space)):
        field(ink, c, lb)
    a, b = (r.cols([0.55, 0.45], m.space * 1.5) if P.opts.landscape else r.rows([0.55, 0.45], m.space * 1.5))
    _box_grid(P, section(ink, a, "100 squares — each is 1% of the goal"), 10, 10)
    table(ink, section(ink, b, "Deposits"), [("Date", 1.2), ("Amount", 1.3), ("Running total", 1.6)])


def _box_grid(P, r, cols, rows):
    ink, m, t = P.ink, P.m, P.t
    s = min(r.w / cols, r.h / rows)
    x0 = r.x + (r.w - s * cols) / 2
    y0 = r.top - s * rows
    for j in range(rows):
        for i in range(cols):
            ink.box(Rect(x0 + i * s + s * 0.08, y0 + j * s + s * 0.08, s * 0.84, s * 0.84),
                    stroke=t.rule, width=m.lw_grid, radius=s * 0.1)


def _meals(P, r):
    ink, m, t = P.ink, P.m, P.t
    if P.opts.landscape:
        plan, groc = r.cols([0.72, 0.28], m.space * 1.5)
    else:
        plan, groc = r.rows([0.68, 0.32], m.space * 1.5)
    meals = ["Breakfast", "Lunch", "Dinner", "Snacks"]
    hdr, grid = plan.take_top(m.mm(6))
    day_w = m.mm(12 if m.compact else 16)
    cols = Rect(plan.x + day_w, grid.y, plan.w - day_w, grid.h).cols(4)
    for lb, c in zip(meals, cols):
        ink.text(c.x + m.mm(1), hdr.y + m.mm(1.6), lb.upper(), m.fs_small, BOLD, t.muted)
    rh = grid.h / 7
    for i, d in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        y = grid.top - (i + 1) * rh
        ink.line(plan.x, y + rh, plan.right, y + rh, t.rule, m.lw_rule)
        ink.text(plan.x + m.mm(1), y + rh - m.mm(1.5) - m.fs_label * 0.7, d.upper(), m.fs_label,
                 BOLD, t.soft)
    ink.line(plan.x, grid.y, plan.right, grid.y, t.rule, m.lw_rule)
    for c in cols:
        ink.line(c.x, grid.y, c.x, grid.top, t.grid, m.lw_grid)
    if P.opts.landscape:
        checklist(ink, groc, "Grocery list")
    else:
        for part, title in zip(groc.cols(2, m.space * 1.5), ("Grocery list", "")):
            checklist(ink, part if title else part.pad(top=m.fs_label * 0.7 + m.mm(1.6)),
                      title or None)


def _workout(P, r):
    ink, m = P.ink, P.m
    head, r = r.take_top(m.mm(8), m.space * 1.5)
    for lb, c in zip(("Date", "Focus", "Duration"), head.cols(3, m.space)):
        field(ink, c, lb)
    strength, rest = r.rows([0.6, 0.4], m.space * 1.5)
    table(ink, section(ink, strength, "Strength"),
          [("Exercise", 3), ("Sets", 1), ("Reps", 1), ("Weight", 1.2)] +
          ([] if m.compact else [("Notes", 2)]))
    cardio, notes = rest.cols(2, m.space * 1.5)
    table(ink, section(ink, cardio, "Cardio"), [("Activity", 2), ("Time", 1), ("Distance", 1.2)])
    lines_box(ink, notes, "How I felt")


def _gratitude(P, r):
    ink, m = P.ink, P.m
    head, r = r.take_top(m.mm(8), m.space * 1.5)
    field(ink, head.cols(2, m.space)[0], "Date")
    a, b, c, d = r.rows([0.3, 0.25, 0.2, 0.25], m.space * 1.5)
    numbered_lines(ink, a, "Three things I'm grateful for", 3)
    lines_box(ink, b, "Today's highlight")
    lines_box(ink, c, "Affirmation")
    lines_box(ink, d, "Let go of")


def _goal(P, r):
    ink, m = P.ink, P.m
    fh = m.mm(9)
    g, r = r.take_top(fh, m.space * 1.5)
    field(ink, g, "Goal")
    meta, r = r.take_top(fh, m.space * 1.5)
    for lb, c in zip(("Start", "Deadline", "Reward"), meta.cols(3, m.space)):
        field(ink, c, lb)
    why, steps, obst = r.rows([0.2, 0.45, 0.35], m.space * 1.5)
    lines_box(ink, why, "Why it matters")
    table(ink, section(ink, steps, "Action steps"), [("Step", 4), ("By", 1.3), ("Done", 0.9)])
    a, b = obst.cols(2, m.space * 1.5)
    lines_box(ink, a, "Obstacles")
    lines_box(ink, b, "Solutions")


def _todo(P, r):
    ink, m = P.ink, P.m
    head, r = r.take_top(m.mm(8), m.space * 1.5)
    field(ink, head.cols(2, m.space)[0], "Date")
    if m.compact and not P.opts.landscape:
        checklist(ink, r)
    else:
        for part in r.cols(2, m.space * 2):
            checklist(ink, part)


def _storyboard(P, r):
    ink, m, t = P.ink, P.m, P.t
    if m.compact:
        ncols, nrows = (3, 1) if P.opts.landscape else (1, 3)
    else:
        ncols, nrows = (3, 2) if P.opts.landscape else (2, 3)
    for row in r.grid(ncols, nrows, m.space * 1.5, m.space * 1.5):
        for cell in row:
            frame, cap = cell.rows([0.74, 0.26], m.mm(1.5))
            ink.box(frame, stroke=t.soft, width=m.lw_box, radius=m.radius)
            ink.hlines(cap, cap.h / 2.2)


# (slug, title, renderer, index icon)
_RAW = [
    ("lined", "Lined", _lined, "lines"),
    ("narrow-lined", "Narrow Lined", _narrow, "lines"),
    ("dot-grid", "Dot Grid", _dots, "dots"),
    ("fine-graph", "Fine Graph", _graph, "grid"),
    ("isometric", "Isometric Dot Grid", _iso, "dots"),
    ("cornell", "Cornell Notes", _cornell, "split"),
    ("meeting", "Meeting Minutes", _meeting, "table"),
    ("priority-matrix", "Priority Matrix", _matrix, "quad"),
    ("pomodoro", "Pomodoro Tracker", _pomodoro, "circles"),
    ("daily-routine", "Daily Routine", _routine, "table"),
    ("habit-tracker", "Habit Tracker", _habits, "grid"),
    ("reading-log", "Reading Log", _reading, "table"),
    ("monthly-budget", "Monthly Budget", _budget, "table"),
    ("bill-tracker", "Bill Tracker", _bills, "table"),
    ("debt-payoff", "Debt Payoff", _debt, "boxes"),
    ("savings", "Savings Tracker", _savings, "boxes"),
    ("meal-planner", "Meal Planner", _meals, "table"),
    ("workout", "Workout Log", _workout, "table"),
    ("gratitude", "Gratitude Journal", _gratitude, "lines"),
    ("goal-planner", "Goal Planner", _goal, "split"),
    ("todo", "To-Do List", _todo, "checks"),
    ("storyboard", "Storyboard", _storyboard, "quad"),
    ("blank", "Blank Sketch", _blank, "blank"),
]
TEMPLATES = [(s, title, (fn, icon)) for s, title, fn, icon in _RAW]
_BY_SLUG = {s: (title, fn, icon) for s, title, (fn, icon) in TEMPLATES}


# --- pages ---------------------------------------------------------------------------------
def template_page(P, spec) -> None:
    title, fn, _ = _BY_SLUG[spec.data["slug"]]
    body = page_header(P.ink, P.content, title)
    fn(P, body)


def template_index(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    body = page_header(ink, P.content, "Templates", f"{len(TEMPLATES)} duplicate-ready layouts")
    note_h = m.mm(6)
    note_r, grid_r = body.take_bottom(note_h, m.space)
    n = len(TEMPLATES)
    g = m.gap * 1.5
    for ncols in range(1, 7):
        nrows = math.ceil(n / ncols)
        th = (grid_r.h - (nrows - 1) * g) / nrows
        if th >= m.tap:
            break
    th = min(th, m.mm(16))
    tw = (grid_r.w - (ncols - 1) * g) / ncols
    for i, (slug, title, (_, icon)) in enumerate(TEMPLATES):
        col, row = divmod(i, nrows)
        cell = Rect(grid_r.x + col * (tw + g), grid_r.top - (row + 1) * th - row * g, tw, th)
        ink.box(cell, fill=t.tab, radius=m.radius)
        isz = min(cell.h - m.mm(3), m.mm(9))
        icon_r = Rect(cell.x + m.mm(1.5), cell.cy - isz / 2, isz, isz)
        _icon(P, icon_r, icon)
        tx = icon_r.right + m.mm(2.5)
        s = ink.fit_size(title, m.fs_body, cell.right - tx - m.mm(1.5), BOLD)
        ink.text(tx, cell.cy - s * 0.35, title, s, BOLD, t.ink)
        ink.link(cell, f"t-{slug}")
    msg = "Tip: open a template and use your tablet's Duplicate Page tool to reuse it."
    s = ink.fit_size(msg, m.fs_small, note_r.w)
    ink.text(note_r.x, note_r.y + m.mm(1.5), msg, s, REGULAR, t.muted)


def _icon(P, r: Rect, kind: str) -> None:
    ink, m, t = P.ink, P.m, P.t
    ink.box(r, fill=t.paper, stroke=t.grid, width=m.lw_grid, radius=m.radius * 0.6)
    inner = r.inset(r.w * 0.18)
    if kind == "lines":
        ink.hlines(inner, inner.h / 4, color=t.rule)
    elif kind == "dots":
        ink.dots(inner, inner.w / 3, color=t.rule, size=m.pt(1.2))
    elif kind == "grid":
        ink.grid(inner, inner.w / 4, color=t.rule)
    elif kind == "split":
        ink.line(inner.x + inner.w * 0.33, inner.y + inner.h * 0.25, inner.x + inner.w * 0.33, inner.top, t.rule)
        ink.line(inner.x, inner.y + inner.h * 0.25, inner.right, inner.y + inner.h * 0.25, t.rule)
    elif kind == "table":
        ink.hlines(inner, inner.h / 4, color=t.rule, top_line=True)
        ink.line(inner.x + inner.w * 0.4, inner.y, inner.x + inner.w * 0.4, inner.top, t.rule)
    elif kind == "quad":
        ink.line(inner.cx, inner.y, inner.cx, inner.top, t.rule)
        ink.line(inner.x, inner.cy, inner.right, inner.cy, t.rule)
    elif kind == "circles":
        for i in range(3):
            ink.circle(inner.x + inner.w * (i + 0.5) / 3, inner.cy, inner.w / 8, stroke=t.rule,
                       width=m.lw_grid)
    elif kind == "boxes":
        _box_grid(P, inner, 3, 3)
    elif kind == "checks":
        for i in range(3):
            y = inner.top - (i + 0.5) * inner.h / 3
            ink.box(Rect(inner.x, y - inner.h / 10, inner.h / 5, inner.h / 5), stroke=t.rule,
                    width=m.lw_grid)
            ink.line(inner.x + inner.h / 3, y, inner.right, y, t.rule)
