"""One-page weekly overview: 7 linked days, weekly priorities, habit tracker."""

from __future__ import annotations

from collections import Counter
from datetime import date

from .. import calendar_model as cal
from ..chrome import month_key
from ..geometry import Rect
from ..ink import BOLD
from ..widgets import (checklist, day_key, habit_grid, page_header, section, week_habits,
                       week_key)

ABBR = cal.MONTH_ABBR


def range_label(start: date) -> str:
    end = cal.week_days(start)[-1]
    if start.year != end.year:
        return f"{ABBR[start.month]} {start.day}, {start.year} – {ABBR[end.month]} {end.day}, {end.year}"
    if start.month != end.month:
        return f"{ABBR[start.month]} {start.day} – {ABBR[end.month]} {end.day}, {end.year}"
    return f"{ABBR[start.month]} {start.day} – {end.day}, {end.year}"


def nav_month(start: date) -> tuple[int, int]:
    days = [d for d in cal.week_days(start) if cal.in_range(d)]
    return Counter((d.year, d.month) for d in days).most_common(1)[0][0]


def week_page(P, spec) -> None:
    ink, m, t, o = P.ink, P.m, P.t, P.opts
    start, idx = spec.data["start"], spec.data["index"]
    days = cal.week_days(start)
    wk = cal.iso_week(start, P.fw)[1]
    prev = week_key(P.weeks[idx - 1]) if idx > 0 else None
    nxt = week_key(P.weeks[idx + 1]) if idx + 1 < len(P.weeks) else None
    months = list(dict.fromkeys((d.year, d.month) for d in days if cal.in_range(d)))
    buttons = [(ABBR[mo], month_key(y, mo)) for y, mo in months]
    body = page_header(ink, P.content, f"Week {wk:02d}", range_label(start), buttons=buttons,
                       prev=prev, next=nxt)
    sp = m.space

    if o.landscape:
        side, cols_r = body.take_right(body.w * (0.24 if m.compact else 0.22), sp * 1.5)
        for d, col in zip(days, cols_r.cols(7, m.gap)):
            _day_column(P, col, d)
        pri, hab = side.rows([0.46, 0.54], sp * 1.5)
        checklist(ink, pri, "Weekly priorities", step=m.ruled * (0.9 if m.compact else 1))
        hb = section(ink, hab, "Habits")
        habit_grid(ink, hb, [cal.DAY_ABBR[d.weekday()][:2] for d in days], 4,
                   weekend_rows={i for i, d in enumerate(days) if cal.is_weekend(d)},
                   allow_split=False)
    elif not m.compact:
        band, grid_r = body.take_bottom(m.mm(34), sp * 1.5)
        # Fill down the columns (Mon-Thu | Fri-Sun + priorities) so the
        # weekend stays together instead of Sunday sitting alone on the last row.
        rows = grid_r.grid(2, 4, sp * 1.5, sp)
        slots = [row[c] for c in range(2) for row in rows]
        for i, (d, slot) in enumerate(zip(days, slots)):
            _day_block(P, slot, d, first=i == 0)
        checklist(ink, slots[7], "Weekly priorities")
        week_habits(ink, band, days, 4)
    else:
        pri, rest = body.take_top(m.mm(22), sp)
        band, list_r = rest.take_bottom(m.mm(25), sp)
        checklist(ink, pri, "Weekly priorities", step=m.mm(5.5))
        for i, (d, row) in enumerate(zip(days, list_r.rows(7, m.gap))):
            _day_row(P, row, d, first=i == 0)
        week_habits(ink, band, days, 4)


def _header_text(d: date, first: bool) -> str:
    s = f"{cal.DAY_ABBR[d.weekday()].upper()}  {d.day}"
    if first or d.day == 1:
        s += f"  {ABBR[d.month]}"
    return s


def _day_block(P, r: Rect, d: date, first: bool) -> None:
    ink, m, t = P.ink, P.m, P.t
    head, body = r.take_top(m.tap)
    live = cal.in_range(d)
    ink.box(head, fill=t.tab if live else None, stroke=None if live else t.grid,
            width=m.lw_grid, radius=m.radius)
    color = (t.weekend if cal.is_weekend(d) else t.ink) if live else t.faint
    ink.text_in(head, _header_text(d, first), m.fs_label * 1.12, BOLD, color, align="left",
                pad=m.mm(2.2), tracking=m.fs_label * 0.05)
    if live:
        ink.link(head, day_key(d))
    ink.hlines(body, m.ruled)


def _day_column(P, r: Rect, d: date) -> None:
    ink, m, t = P.ink, P.m, P.t
    head, body = r.take_top(m.tap)
    live = cal.in_range(d)
    ink.box(head, fill=t.tab if live else None, stroke=None if live else t.grid,
            width=m.lw_grid, radius=m.radius)
    color = (t.weekend if cal.is_weekend(d) else t.ink) if live else t.faint
    top, bot = head.rows([0.42, 0.58])
    ink.text_in(top.pad(top=m.mm(0.6)), cal.DAY_ABBR[d.weekday()].upper(), m.fs_small, BOLD,
                t.muted if live else t.faint)
    day = str(d.day) if d.day != 1 else f"{ABBR[d.month]} 1"
    ink.text_in(bot.pad(bottom=m.mm(0.6)), day, m.fs_h, BOLD, color)
    if live:
        ink.link(head, day_key(d))
    ink.hlines(body, m.ruled * (0.85 if m.compact else 1))
    ink.line(r.right + m.gap / 2, r.y, r.right + m.gap / 2, body.top, t.grid, m.lw_grid)


def _day_row(P, r: Rect, d: date, first: bool) -> None:
    ink, m, t = P.ink, P.m, P.t
    tab, lines = r.take_left(max(m.mm(13), m.tap), m.mm(2))
    live = cal.in_range(d)
    ink.box(tab, fill=t.tab if live else None, stroke=None if live else t.grid,
            width=m.lw_grid, radius=m.radius)
    color = (t.weekend if cal.is_weekend(d) else t.ink) if live else t.faint
    top, bot = tab.rows([0.45, 0.55])
    ink.text_in(top.pad(top=m.mm(0.5)), cal.DAY_ABBR[d.weekday()].upper(), m.fs_small, BOLD,
                t.muted if live else t.faint)
    label = str(d.day) if not (first or d.day == 1) else f"{ABBR[d.month]} {d.day}"
    ink.text_in(bot.pad(bottom=m.mm(0.5)), label, m.fs_body, BOLD, color)
    if live:
        ink.link(tab, day_key(d))
    ink.hlines(lines, lines.h / 2, top_line=False)
