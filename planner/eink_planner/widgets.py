"""Reusable page pieces: headers, buttons, month blocks, tables, checklists."""

from __future__ import annotations

from datetime import date, timedelta

from .calendar_model import (DAY_ABBR, MONTH_NAMES, days_in_month, in_range, is_weekend,
                             iso_week, month_rows, weekday_order)
from .chrome import month_key
from .geometry import Rect
from .ink import BOLD, REGULAR, Ink


def day_key(d: date) -> str:
    return f"d-{d.isoformat()}"


def week_key(start: date) -> str:
    return f"w-{start.isoformat()}"


# --- buttons ---------------------------------------------------------------------
def button(ink: Ink, r: Rect, label: str, key: str | None = None, *, active: bool = False,
           fill=None, color=None, size: float | None = None, sub: str = "") -> None:
    m, t = ink.m, ink.t
    if active:
        fill, color = (fill or t.active), t.active_text
    else:
        fill = t.tab if fill is None else fill
        color = color or (t.tab_text if key else t.faint)
    ink.box(r, fill=fill, radius=m.radius)
    size = size or m.fs_tab
    if sub:
        s = ink.fit_size(label, size, r.w - m.mm(2), BOLD)
        ink.text(r.cx, r.cy + s * 0.15, label, s, BOLD, color, "center")
        ink.text(r.cx, r.cy - s * 0.95, sub, m.fs_small, REGULAR, color, "center")
    else:
        ink.text_in(r, label, size, BOLD, color, pad=m.mm(1))
    if key:
        ink.link(r, key)


def arrow(ink: Ink, r: Rect, key: str | None, direction: str) -> None:
    t = ink.t
    ink.box(r, fill=t.tab, radius=ink.m.radius)
    ink.triangle(r, direction, t.ink if key else t.faint)
    if key:
        ink.link(r, key)


def button_width(ink: Ink, label: str, size: float | None = None) -> float:
    m = ink.m
    return max(Ink.width(label, size or m.fs_tab, BOLD) + m.mm(4), m.tap)


# --- page header ---------------------------------------------------------------------
def page_header(ink: Ink, r: Rect, title: str, subtitle: str = "", *,
                buttons: list[tuple] = (), prev: str | None | bool = False,
                next: str | None | bool = False) -> Rect:
    """Header row (one tap tall) with title on the left and buttons on the right.

    buttons: (label, key[, active]) tuples. prev/next: a key, None (disabled arrow),
    or False (no arrow). Returns the remaining body rect.
    """
    m, t = ink.m, ink.t
    row, rest = r.take_top(m.tap, m.space)
    x = row.right
    for direction, key in (("right", next), ("left", prev)):
        if key is False:
            continue
        x -= m.tap
        arrow(ink, Rect(x, row.y, m.tap, m.tap), key, direction)
        x -= m.gap
    for b in reversed(list(buttons)):
        label, key = b[0], b[1]
        active = b[2] if len(b) > 2 else False
        w = button_width(ink, label)
        x -= w
        button(ink, Rect(x, row.y, w, m.tap), label, key, active=active)
        x -= m.gap
    avail = x - row.x - m.mm(2)
    if m.compact and subtitle:
        ts = ink.fit_size(title, m.fs_title * 0.82, avail, BOLD)
        ink.text(row.x, row.cy + m.mm(0.4), title, ts, BOLD, t.ink)
        ss = ink.fit_size(subtitle, m.fs_label, avail)
        ink.text(row.x, row.y + m.mm(0.6), subtitle, ss, REGULAR, t.muted)
    else:
        ts = ink.fit_size(title, m.fs_title, avail, BOLD)
        base = row.cy - ts * 0.35
        w = ink.text(row.x, base, title, ts, BOLD, t.ink)
        if subtitle:
            sx = row.x + w + m.mm(2.5)
            ss = ink.fit_size(subtitle, m.fs_h, max(x - sx - m.mm(2), 1))
            if Ink.width(subtitle, ss) <= x - sx - m.mm(2):
                ink.text(sx, base, subtitle, ss, REGULAR, t.muted)
    ink.line(row.x, row.y - m.space / 2, row.right, row.y - m.space / 2, t.rule, m.lw_rule)
    return rest


# --- month mini-calendar -------------------------------------------------------------
def month_block_min(ink: Ink, week_col: bool) -> tuple[float, float]:
    m = ink.m
    cols = 7 + (1 if week_col else 0)
    return cols * m.tap_min, m.tap + m.mm(4) + 6 * m.tap_min


def month_block(ink: Ink, r: Rect, year: int, month: int, first_weekday: int, *,
                week_col: bool = False, week_keys: set[str] = frozenset(),
                quarter_color=None) -> None:
    m, t = ink.m, ink.t
    title, rest = r.take_top(m.tap)
    hdr, grid = rest.take_top(m.mm(4))
    # Title: whole row is the tap target for the monthly page.
    if quarter_color is not None:
        ink.box(Rect(title.x, title.cy - m.mm(2), m.mm(0.9), m.mm(4)), fill=quarter_color)
    tx = title.x + m.mm(2.2)
    w = ink.text(tx, title.cy - m.fs_h * 0.35, MONTH_NAMES[month], m.fs_h, BOLD, t.ink)
    ink.text(tx + w + m.mm(1.5), title.cy - m.fs_h * 0.35, str(year), m.fs_h, REGULAR, t.muted)
    ink.link(title, month_key(year, month))

    cols = 7 + (1 if week_col else 0)
    cw = r.w / cols
    order = weekday_order(first_weekday)
    labels = (["Wk"] if week_col else []) + [DAY_ABBR[d][0] for d in order]
    for i, lb in enumerate(labels):
        color = t.weekend if (i - week_col >= 0 and order[i - week_col] >= 5) else t.muted
        ink.text(r.x + (i + 0.5) * cw, hdr.y + m.mm(1.1), lb, m.fs_small, BOLD, color, "center")
    ink.line(r.x, hdr.y, r.right, hdr.y, t.rule, m.lw_rule)

    rh = grid.h / 6
    for i, start in enumerate(month_rows(year, month, first_weekday, fixed=6)):
        ry = grid.top - (i + 1) * rh
        days = [start + timedelta(days=j) for j in range(7)]
        if week_col and any(d.month == month for d in days):
            cell = Rect(r.x, ry, cw, rh)
            wk = iso_week(start, first_weekday)[1]
            ink.text(cell.cx, cell.cy - m.fs_small * 0.35, f"{wk:02d}", m.fs_small, REGULAR,
                     t.muted, "center")
            if week_key(start) in week_keys:
                ink.link(cell, week_key(start))
        for j, d in enumerate(days):
            if d.month != month:
                continue
            cell = Rect(r.x + (j + week_col) * cw, ry, cw, rh)
            color = t.weekend if is_weekend(d) else t.ink
            ink.text(cell.cx, cell.cy - m.fs_body * 0.35, str(d.day), m.fs_body, REGULAR,
                     color, "center")
            if in_range(d):
                ink.link(cell, day_key(d))


# --- writing blocks -------------------------------------------------------------------
def section(ink: Ink, r: Rect, title: str) -> Rect:
    """Section label at the top of r. Returns the rect below it."""
    h = ink.label(r.x, r.top, title, max_w=r.w)
    return r.pad(top=h)


def lines_box(ink: Ink, r: Rect, title: str | None = None, step: float | None = None,
              kind: str = "lines") -> Rect:
    body = section(ink, r, title) if title else r
    if kind == "lines":
        ink.hlines(body, step)
    elif kind == "grid":
        ink.grid(body)
    elif kind == "dots":
        ink.dots(body)
    elif kind == "box":
        ink.box(body, stroke=ink.t.rule, radius=ink.m.radius)
    return body


def checklist(ink: Ink, r: Rect, title: str | None = None, step: float | None = None,
              max_rows: int = 99) -> int:
    m, t = ink.m, ink.t
    body = section(ink, r, title) if title else r
    step = step or m.ruled
    ys = ink.hlines(body, step)[:max_rows]
    box = min(m.mm(2.8), step * 0.5)
    for y in ys:
        ink.checkbox(body.x + m.mm(0.4), y + step / 2, box)
    return len(ys)


def numbered_lines(ink: Ink, r: Rect, title: str, n: int = 3, step: float | None = None) -> None:
    m, t = ink.m, ink.t
    body = section(ink, r, title)
    step = step or min(m.ruled * 1.15, body.h / n)
    for i in range(n):
        y = body.top - (i + 1) * step
        rad = min(step * 0.3, m.mm(2.1))
        ink.circle(body.x + rad + m.mm(0.3), y + step / 2, rad, stroke=t.accent, width=m.lw_box)
        ink.text(body.x + rad + m.mm(0.3), y + step / 2 - m.fs_small * 0.35, str(i + 1),
                 m.fs_small, BOLD, t.accent, "center")
        ink.line(body.x + 2 * rad + m.mm(2), y, body.right, y, t.rule, m.lw_rule)


def table(ink: Ink, r: Rect, columns: list[tuple[str, float]], row_h: float | None = None,
          header_h: float | None = None, max_rows: int = 999) -> list[Rect]:
    """Ruled table with small uppercase headers. Returns the column rects of the body."""
    m, t = ink.m, ink.t
    header_h = header_h or m.mm(6)
    row_h = row_h or m.ruled
    hdr, body = r.take_top(header_h)
    cols = r.cols([w for _, w in columns])
    for (label, _), c in zip(columns, cols):
        s = ink.fit_size(label.upper(), m.fs_small, c.w - m.mm(2), BOLD)
        ink.text(c.x + m.mm(1), hdr.y + m.mm(1.6), label.upper(), s, BOLD, t.muted,
                 tracking=s * 0.05)
    ink.line(r.x, hdr.y, r.right, hdr.y, t.soft, m.lw_box)
    n = min(int(body.h // row_h), max_rows)
    bottom = hdr.y - n * row_h
    ink.hlines(Rect(r.x, bottom, r.w, hdr.y - bottom), row_h)
    for c in cols[1:]:
        ink.line(c.x, bottom, c.x, hdr.y, t.grid, m.lw_grid)
    return [Rect(c.x, bottom, c.w, hdr.y - bottom) for c in cols]


def habit_grid(ink: Ink, r: Rect, row_labels: list[str], n_habits: int, *,
               weekend_rows: set[int] = frozenset(), allow_split: bool = True) -> None:
    """Rows = days (labels), columns = habits with blank header boxes for names."""
    m, t = ink.m, ink.t
    head_h = m.mm(9 if not m.compact else 7)
    n = len(row_labels)
    blocks = 1
    if allow_split and (r.h - head_h) / n < m.mm(4) and r.w >= m.mm(55):
        blocks = 2
    per = -(-n // blocks)
    for b, br in enumerate(r.cols(blocks, m.space)):
        labels = row_labels[b * per:(b + 1) * per]
        idx0 = b * per
        hdr, body = br.take_top(head_h)
        lab_w = m.mm(5.5)
        cols = Rect(br.x + lab_w, br.y, br.w - lab_w, br.h).cols(n_habits)
        for c in cols:
            ink.box(Rect(c.x + m.mm(0.4), hdr.y + m.mm(0.8), c.w - m.mm(0.8), hdr.h - m.mm(1.2)),
                    stroke=t.grid, width=m.lw_grid, radius=m.radius * 0.6)
        rh = body.h / per
        p = ink.c.beginPath()
        for i in range(len(labels) + 1):
            y = body.top - i * rh
            p.moveTo(br.x + lab_w, y)
            p.lineTo(br.right, y)
        bottom = body.top - len(labels) * rh
        for c in cols + [Rect(br.right, 0, 0, 0)]:
            p.moveTo(c.x, body.top)
            p.lineTo(c.x, bottom)
        ink.c.setStrokeColor(t.grid)
        ink.c.setLineWidth(m.lw_grid)
        ink.c.drawPath(p, stroke=1, fill=0)
        size = min(m.fs_small, rh * 0.62)
        for i, lb in enumerate(labels):
            y = body.top - (i + 0.5) * rh - size * 0.35
            color = t.weekend if (idx0 + i) in weekend_rows else t.muted
            ink.text(br.x + lab_w - m.mm(1), y, lb, size, REGULAR, color, "right")


def week_habits(ink: Ink, r: Rect, days: list[date], n_habits: int, title: str = "Habit Tracker") -> None:
    """Rows = habits (write the name), columns = the 7 days."""
    m, t = ink.m, ink.t
    body = section(ink, r, title)
    hdr, grid = body.take_top(m.mm(4.5))
    name_w = body.w * 0.34
    cols = Rect(body.x + name_w, grid.y, body.w - name_w, grid.h).cols(7)
    for c, d in zip(cols, days):
        ink.text(c.cx, hdr.y + m.mm(1.2), DAY_ABBR[d.weekday()][:2], m.fs_small, BOLD,
                 t.weekend if is_weekend(d) else t.muted, "center")
    rh = grid.h / n_habits
    rad = min(rh, cols[0].w) * 0.26
    for i in range(n_habits):
        y = grid.top - (i + 1) * rh
        ink.line(body.x, y, body.right, y, t.rule, m.lw_rule)
        for c in cols:
            ink.circle(c.cx, y + rh / 2, rad, stroke=t.grid, width=m.lw_grid)


def day_rows(year: int, month: int) -> list[date]:
    return [date(year, month, i) for i in range(1, days_in_month(year, month) + 1)]


def habit_matrix(ink: Ink, r: Rect, days: list[date], n_habits: int) -> None:
    """Rows = habits (write the name on the left), columns = days of the month."""
    m, t = ink.m, ink.t
    name_w = min(m.mm(32), r.w * 0.22)
    hdr, grid = r.take_top(m.mm(5))
    cols = Rect(r.x + name_w, grid.y, r.w - name_w, grid.h).cols(len(days))
    size = min(m.fs_small * 0.85, cols[0].w * 0.62 / max(len(str(len(days))), 1) * 1.6)
    for d, c in zip(days, cols):
        ink.text(c.cx, hdr.y + m.mm(1.4), str(d.day), size, BOLD,
                 t.weekend if is_weekend(d) else t.muted, "center")
    ink.text(r.x, hdr.y + m.mm(1.4), "HABIT", m.fs_small, BOLD, t.muted)
    rh = grid.h / n_habits
    p = ink.c.beginPath()
    for i in range(n_habits + 1):
        p.moveTo(r.x, grid.top - i * rh)
        p.lineTo(r.right, grid.top - i * rh)
    for c in cols + [Rect(r.right, 0, 0, 0)]:
        p.moveTo(c.x, grid.y)
        p.lineTo(c.x, grid.top)
    ink.c.setStrokeColor(t.grid)
    ink.c.setLineWidth(m.lw_grid)
    ink.c.drawPath(p, stroke=1, fill=0)
