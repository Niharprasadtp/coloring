"""Daily pages: hourly timeline, Top 3, to-do, notes (+ ADHD support blocks)."""

from __future__ import annotations

from datetime import date, timedelta

from .. import calendar_model as cal
from ..chrome import month_key
from ..geometry import Rect
from ..ink import BOLD, REGULAR
from ..widgets import arrow, button, button_width, checklist, day_key, section, week_key

HOURS = list(range(6, 23))  # 6 AM .. 10 PM, one row each


def day_page(P, spec) -> None:
    ink, m, t, o = P.ink, P.m, P.t, P.opts
    d: date = spec.data["day"]
    body = _header(P, d)
    adhd = o.daily_style == "adhd"
    sp = m.space
    if adhd:
        bar, body = body.take_top(m.mm(9.5 if m.compact else 12), sp * 1.2)
        timeblock_bar(P, bar)
    top3_h = m.fs_label * 0.7 + m.mm(1.6) + 3 * m.ruled * (0.9 if m.compact else 1.0)

    if o.landscape:
        short = m.compact  # ~66 mm of height: hours wrap into two columns
        c1, c2, c3 = body.cols([0.42, 0.29, 0.29] if short else [0.32, 0.33, 0.35], sp * 1.5)
        timeline(P, c1)
        t3, rest = c2.take_top(top3_h, sp * 1.5)
        top3(P, t3)
        if adhd and not short:
            en, rest = rest.take_top(_energy_h(P), sp * 1.5)
            energy(P, en)
        checklist(ink, rest, "To-do", step=m.ruled * (0.9 if m.compact else 1))
        if adhd and short:
            en, bd = c3.take_top(_energy_h(P), sp * 1.5)
            energy(P, en)
            _area(P, bd, "Brain dump / notes", "dots")
        elif adhd:
            bd, notes = c3.rows([0.45, 0.55], sp * 1.5)
            _area(P, bd, "Brain dump", "dots")
            _area(P, notes, "Notes", "grid")
        else:
            _area(P, c3, "Notes", "grid")
        return

    # Portrait.
    if adhd and not m.compact:
        row, body = body.take_top(max(top3_h, _energy_h(P)), sp * 1.5)
        a, b = row.cols([0.58, 0.42], sp * 1.5)
        top3(P, a)
        energy(P, b)
    else:
        row, body = body.take_top(top3_h, sp * 1.5)
        top3(P, row)
    left, right = body.cols([0.55 if m.compact else 0.47, 0.45 if m.compact else 0.53], sp * 1.5)
    timeline(P, left)
    step = m.ruled * (0.9 if m.compact else 1.0)
    if adhd and m.compact:
        en, rest = right.take_top(_energy_h(P), sp)
        energy(P, en)
        todo, bd = rest.rows([0.5, 0.5], sp)
        checklist(ink, todo, "To-do", step=step)
        _area(P, bd, "Brain dump / notes", "dots")
    elif adhd:
        todo, bd, notes = right.rows([0.34, 0.33, 0.33], sp * 1.5)
        checklist(ink, todo, "To-do", step=step)
        _area(P, bd, "Brain dump", "dots")
        _area(P, notes, "Notes", "grid")
    else:
        todo, notes = right.rows([0.42, 0.58], sp * 1.5)
        checklist(ink, todo, "To-do", step=step)
        _area(P, notes, "Notes", "grid")


# --- header ---------------------------------------------------------------------------
def _header(P, d: date) -> Rect:
    ink, m, t = P.ink, P.m, P.t
    row, body = P.content.take_top(m.tap, m.space)
    x = row.right
    one = timedelta(days=1)
    for direction, other in (("right", d + one), ("left", d - one)):
        x -= m.tap
        arrow(ink, Rect(x, row.y, m.tap, m.tap), day_key(other) if cal.in_range(other) else None,
              direction)
        x -= m.gap
    ws = cal.week_start(d, P.fw)
    wk = cal.iso_week(ws, P.fw)[1]
    for label, key in ((f"W{wk:02d}" if m.compact else f"Week {wk:02d}", week_key(ws)),
                       (cal.MONTH_ABBR[d.month] if m.compact else cal.month_label(d.year, d.month),
                        month_key(d.year, d.month))):
        w = button_width(ink, label)
        x -= w
        button(ink, Rect(x, row.y, w, m.tap), label, key)
        x -= m.gap
    num_color = t.weekend if cal.is_weekend(d) else t.ink
    w = ink.text(row.x, row.cy - m.fs_big * 0.36, str(d.day), m.fs_big, BOLD, num_color)
    tx = row.x + w + m.mm(2.5)
    avail = x - tx - m.mm(1)
    name = cal.DAY_NAMES[d.weekday()]
    s1 = ink.fit_size(name, m.fs_h, avail, BOLD)
    ink.text(tx, row.cy + m.mm(0.5), name, s1, BOLD, t.ink)
    doy = cal.day_of_year(d)
    left = (date(d.year, 12, 31) - d).days
    info = f"{cal.MONTH_ABBR[d.month]} {d.year} · day {doy} · {left} left"
    s2 = ink.fit_size(info, m.fs_small, avail)
    ink.text(tx, row.cy - m.mm(0.6) - s2 * 0.75, info, s2, REGULAR, t.muted)
    ink.line(row.x, row.y - m.space / 2, row.right, row.y - m.space / 2, t.rule, m.lw_rule)
    return body


# --- blocks ---------------------------------------------------------------------------
def top3(P, r: Rect) -> None:
    ink, m, t = P.ink, P.m, P.t
    body = section(ink, r, "Top 3 priorities")
    step = body.h / 3
    rad = min(step * 0.3, m.mm(2.1))
    for i in range(3):
        y = body.top - (i + 1) * step
        cx = body.x + rad + m.mm(0.3)
        ink.circle(cx, y + step / 2, rad, stroke=t.accent, width=m.lw_box)
        ink.text(cx, y + step / 2 - m.fs_small * 0.35, str(i + 1), m.fs_small, BOLD, t.accent,
                 "center")
        ink.line(cx + rad + m.mm(2), y, body.right - m.mm(4.5), y, t.rule, m.lw_rule)
        ink.checkbox(body.right - m.mm(3), y + step / 2, min(m.mm(2.8), step * 0.5))


def timeline(P, r: Rect) -> None:
    ink, m = P.ink, P.m
    body = section(ink, r, "Schedule")
    if body.h / len(HOURS) < m.mm(4.5) and body.w > m.mm(50):
        half = (len(HOURS) + 1) // 2
        a, b = body.cols(2, m.space)
        _hours(P, a, HOURS[:half], half)
        _hours(P, b, HOURS[half:], half)
    else:
        _hours(P, body, HOURS, len(HOURS))


def _hours(P, body: Rect, hours: list[int], n: int) -> None:
    ink, m, t = P.ink, P.m, P.t
    rh = body.h / n
    lab_w = m.mm(7.5 if m.compact else 9)
    size = min(m.fs_label * 1.05, rh * 0.5)
    for i, h in enumerate(hours):
        y = body.top - i * rh
        ink.line(body.x, y, body.right, y, t.rule, m.lw_rule)
        ink.line(body.x + lab_w, y - rh / 2, body.right, y - rh / 2, t.grid, m.lw_grid,
                 dash=[m.mm(0.6), m.mm(0.9)])
        h12 = h % 12 or 12
        w = ink.text(body.x + m.mm(0.5), y - m.mm(0.8) - size * 0.72, str(h12), size, BOLD, t.soft)
        if h in (6, 12) or i == 0 or not m.compact:
            ink.text(body.x + m.mm(0.8) + w, y - m.mm(0.8) - size * 0.72,
                     "am" if h < 12 else "pm", size * 0.72, REGULAR, t.muted)
    bottom = body.top - len(hours) * rh
    ink.line(body.x, bottom, body.right, bottom, t.rule, m.lw_rule)
    ink.line(body.x + lab_w, bottom, body.x + lab_w, body.top, t.grid, m.lw_grid)


def _energy_h(P) -> float:
    m = P.m
    return m.fs_label * 0.7 + m.mm(1.6) + 3 * m.mm(5.5 if m.compact else 7)


def energy(P, r: Rect) -> None:
    ink, m, t = P.ink, P.m, P.t
    body = section(ink, r, "Energy & focus check")
    rows = body.rows(3)
    lab_w = m.mm(12 if m.compact else 15)
    for name, row in zip(("Energy", "Focus", "Mood"), rows):
        ink.text(row.x, row.cy - m.fs_label * 0.35, name, m.fs_label, BOLD, t.soft)
        dots = Rect(row.x + lab_w, row.y, row.w - lab_w, row.h).cols(5)
        rad = min(row.h * 0.28, dots[0].w * 0.3)
        for i, c in enumerate(dots):
            ink.circle(c.cx, c.cy, rad, stroke=t.rule, width=m.lw_box)
            ink.text(c.cx, c.cy - m.fs_small * 0.3, str(i + 1), m.fs_small * 0.8, REGULAR, t.faint,
                     "center")


def timeblock_bar(P, r: Rect) -> None:
    """Visual day bar: one cell per hour from 6 AM to 10 PM to shade blocks of time."""
    ink, m, t = P.ink, P.m, P.t
    body = section(ink, r, "Time blocks")
    hours = HOURS[:-1]  # 16 one-hour cells, 6-22
    cells = body.cols(len(hours))
    for i, (h, c) in enumerate(zip(hours, cells)):
        ink.box(c, stroke=t.rule, width=m.lw_grid)
        if not m.compact or h % 2 == 0:
            ink.text(c.x + m.mm(0.7), c.top - m.mm(0.7) - m.fs_small * 0.6, str(h % 12 or 12),
                     m.fs_small * 0.8, REGULAR, t.muted)


def _area(P, r: Rect, title: str, kind: str) -> None:
    ink = P.ink
    body = section(ink, r, title)
    if kind == "grid":
        ink.grid(body)
    else:
        ink.dots(body)
