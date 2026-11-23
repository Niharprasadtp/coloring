"""Cover, Home dashboard, Year at a Glance, Quarterly and Monthly pages."""

from __future__ import annotations

import math
from datetime import date

from .. import calendar_model as cal
from ..chrome import month_key
from ..geometry import Rect
from ..ink import BOLD, REGULAR
from ..widgets import (button, checklist, day_key, habit_grid, habit_matrix, lines_box, month_block,
                       page_header, section, week_key)


# --- shared helpers -------------------------------------------------------------------
def tile(ink, r: Rect, title: str, sub: str = "", key: str | None = None, *, fill=None,
         stripe=None, size=None) -> None:
    m, t = ink.m, ink.t
    ink.box(r, fill=fill if fill is not None else t.tab, radius=m.radius)
    x = r.x + m.mm(2.6)
    if stripe is not None:
        ink.box(Rect(r.x + m.mm(1.1), r.y + m.mm(1.6), m.mm(0.9), r.h - m.mm(3.2)), fill=stripe)
        x += m.mm(0.6)
    size = ink.fit_size(title, size or m.fs_h, r.right - x - m.mm(1.5), BOLD)
    if sub and r.h >= m.mm(10):
        ink.text(x, r.cy + m.mm(0.4), title, size, BOLD, t.ink)
        s2 = ink.fit_size(sub, m.fs_small, r.right - x - m.mm(1.5))
        ink.text(x, r.cy - m.mm(0.6) - s2 * 0.75, sub, s2, REGULAR, t.muted)
    else:
        ink.text(x, r.cy - size * 0.35, title, size, BOLD, t.ink)
    if key:
        ink.link(r, key)


def _fit(P, w: float, h: float, mw: float, mh: float) -> tuple[int, int]:
    sp = P.m.space
    return max(int((w + sp) // (mw + sp)), 1), max(int((h + sp) // (mh + sp)), 1)


def _block_min(P, week_col: bool) -> tuple[float, float]:
    m = P.m
    return (7 + week_col) * m.tap_min, m.tap + m.mm(4) + 6 * m.tap_min


def _seq_neighbors(P, key: str, pred) -> tuple[str | None, str | None]:
    seq = [s.key for s in P.specs if pred(s.key)]
    i = seq.index(key)
    return (seq[i - 1] if i > 0 else None), (seq[i + 1] if i + 1 < len(seq) else None)


def _is_quarter_key(k: str) -> bool:
    return len(k) >= 2 and k[0] == "q" and k[1].isdigit()


# --- cover ---------------------------------------------------------------------------
def cover(P, spec) -> None:
    ink, m, t, o = P.ink, P.m, P.t, P.opts
    r = P.content
    x = r.x + m.mm(2)
    y = r.top - m.mm(10 if m.compact else 18)
    ink.text(x, y, "PLANNER", m.fs_h, BOLD, t.muted, tracking=m.fs_h * 0.4)
    y -= m.fs_display * 0.74 + m.mm(5)
    size = ink.fit_size("2027", m.fs_display, r.w - m.mm(4), BOLD)
    ink.text(x - size * 0.03, y, "2027", size, BOLD, t.ink)
    y -= m.fs_h + m.mm(5)
    ink.text(x, y, "December 2026 — December 2027", m.fs_h, REGULAR, t.soft)
    y -= m.mm(7)
    sq = m.mm(2.6)
    for i, q in enumerate((4, 1, 2, 3)):
        ink.box(Rect(x + i * (sq + m.mm(1.4)), y, sq, sq), fill=t.q(q), radius=sq * 0.2)

    # Lower panel: fine grid with an ownership plate, Hobonichi style.
    btn_row, _ = r.take_bottom(m.tap)
    panel_top = y - m.mm(10)
    panel_h = min(panel_top - btn_row.top - m.space * 2, r.h * 0.34)
    panel = Rect(r.x, btn_row.top + m.space * 2, r.w, panel_h)
    if panel.h > m.mm(30):
        ink.grid(panel)
        plate_h = m.mm(22 if not m.compact else 18)
        plate = Rect(panel.x + m.mm(6), panel.y + m.mm(6), min(panel.w - m.mm(12), m.mm(110)), plate_h)
        ink.box(plate, fill=t.paper, stroke=t.rule, radius=m.radius)
        rows = plate.inset(m.mm(3), m.mm(2.5)).rows(2, m.mm(2))
        for label, rr in zip(("This planner belongs to", "Contact"), rows):
            ink.text(rr.x, rr.top - m.fs_small, label.upper(), m.fs_small, BOLD, t.muted,
                     tracking=m.fs_small * 0.08)
            ink.line(rr.x, rr.y + m.mm(0.5), rr.right, rr.y + m.mm(0.5), t.rule, m.lw_rule)
    bw = max(m.mm(42 if not m.compact else 30), m.tap)
    button(ink, Rect(r.x, btn_row.y, bw, m.tap), "Open Planner", "home", active=True)
    info = (f"{o.device.label} · {o.orientation.capitalize()} · "
            f"{'Monday' if o.week_start == 'mon' else 'Sunday'} start")
    s = ink.fit_size(info, m.fs_small, r.w - bw - m.mm(4))
    ink.text(r.right, btn_row.cy - s * 0.35, info, s, REGULAR, t.muted, "right")


# --- home dashboard --------------------------------------------------------------------
def home(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    body = page_header(ink, P.content, "Home", "December 2026 – December 2027")
    th = max(m.tap * (1.15 if m.compact else 1.3), m.tap_min)
    g = m.gap * 1.4
    lab_h = m.fs_label * 0.7 + m.mm(1.6)
    from .templates import TEMPLATES

    def labelled(r: Rect, text: str, h: float, gap: float) -> tuple[Rect, Rect]:
        ink.label(r.x, r.top, text)
        return r.pad(top=lab_h).take_top(h, gap)

    def overview(r):
        row, r = labelled(r, "Overview", th, m.space * 1.5)
        a, b = row.cols(2, g)
        tile(ink, a, "Year at a Glance", "Every month and day", "year-1")
        tile(ink, b, "December 2026", "Lead-in month", month_key(2026, 12), stripe=t.q(4))
        return r

    def quarters(r):
        block, r = labelled(r, "2027 by Quarter", 4 * th + 3 * g, m.space * 1.5)
        for q, row in zip(range(1, 5), block.rows(4, g)):
            qc, rest = row.take_left(row.w * 0.24, g)
            mons = cal.quarter_months(q)
            tile(ink, qc, f"Q{q}", f"{cal.MONTH_ABBR[mons[0][1]]} – {cal.MONTH_ABBR[mons[-1][1]]}",
                 f"q{q}", fill=t.qt(q))
            for (y, mo), cell in zip(mons, rest.cols(3, g)):
                tile(ink, cell, cal.MONTH_NAMES[mo] if cell.w > m.mm(28) else cal.MONTH_ABBR[mo],
                     "", month_key(y, mo), stripe=t.q(q))
        return r

    def workspace(r):
        row, r = labelled(r, "Workspace", th, m.space * 1.5)
        for (title, sub, key), cell in zip(
                [("Brain Dump", "5 pages", "bd-1"), ("Projects", "10 hubs", "projects"),
                 ("Templates", f"{len(TEMPLATES)} layouts", "templates")], row.cols(3, g)):
            tile(ink, cell, title, sub, key)
        return r

    if P.opts.landscape:
        left, right = body.cols([0.42, 0.58], m.space * 2)
        rest = workspace(overview(left))
        quarters(right)
    else:
        rest = workspace(quarters(overview(body)))
    _week_index(P, rest)


def _week_index(P, r: Rect) -> None:
    """Grid of every weekly page, drawn only when it fits at full tap size."""
    ink, m, t = P.ink, P.m, P.t
    cols = int((r.w + m.gap) // (m.tap + m.gap))
    if cols < 1:
        return
    rows = math.ceil(len(P.weeks) / cols)
    lab_h = m.fs_label * 0.7 + m.mm(1.6)
    if r.h < lab_h + rows * (m.tap_min + m.gap):
        return
    r = r.pad(top=ink.label(r.x, r.top, "Weeks"))
    ch = min((r.h - (rows - 1) * m.gap) / rows, m.tap)
    cw = (r.w - (cols - 1) * m.gap) / cols
    for i, start in enumerate(P.weeks):
        rr, cc = divmod(i, cols)
        cell = Rect(r.x + cc * (cw + m.gap), r.top - (rr + 1) * ch - rr * m.gap, cw, ch)
        ink.box(cell, fill=t.tab, radius=m.radius)
        ink.text_in(cell, f"{cal.iso_week(start, P.fw)[1]:02d}", m.fs_small, BOLD, t.tab_text)
        ink.link(cell, week_key(start))


# --- year at a glance -----------------------------------------------------------------
def _year_grid(P) -> tuple[int, int]:
    mw, mh = _block_min(P, False)
    return _fit(P, P.body.w, P.body.h, mw, mh)


def year_chunks(P) -> list[list[tuple[int, int]]]:
    cols, rows = _year_grid(P)
    pages = math.ceil(len(cal.MONTHS) / (cols * rows))
    base, extra = divmod(len(cal.MONTHS), pages)
    out, i = [], 0
    for p in range(pages):
        n = base + (1 if p < extra else 0)
        out.append(cal.MONTHS[i:i + n])
        i += n
    return out


def year_page(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    months, idx, count = spec.data["months"], spec.data["index"], spec.data["count"]
    sub = f"{cal.month_label(*months[0], short=True)} – {cal.month_label(*months[-1], short=True)}"
    if count > 1:
        sub += f"  ·  {idx + 1}/{count}"
    prev = f"year-{idx}" if idx > 0 else None
    nxt = f"year-{idx + 2}" if idx + 1 < count else None
    body = page_header(ink, P.content, "Year at a Glance", sub,
                       prev=prev if count > 1 else False, next=nxt if count > 1 else False)
    cols, rows = _year_grid(P)
    cells = [c for row in body.grid(cols, rows, m.space, m.space) for c in row]
    for (y, mo), cell in zip(months, cells):
        month_block(ink, cell, y, mo, P.fw, quarter_color=t.q(cal.quarter_of(y, mo)))


# --- quarterly ---------------------------------------------------------------------------
def quarter_plan(P, q: int) -> list[tuple[str, list]]:
    mw, mh = _block_min(P, True)
    body = P.body
    cols, rows = _fit(P, body.w, body.h, mw, mh)
    months = cal.quarter_months(q)
    if cols >= 3 and body.h >= mh + P.m.mm(28):
        return [("row", months)]
    if cols >= 2 and rows >= 2:
        return [("2x2", months)]
    per = max(cols * rows, 1)
    return [("chunk", months[i:i + per]) for i in range(0, 3, per)]


def quarter_page(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    q, mode, months = spec.data["q"], spec.data["mode"], spec.data["months"]
    names = f"{cal.MONTH_NAMES[3 * q - 2]} – {cal.MONTH_NAMES[3 * q]}"
    if spec.data["count"] > 1:
        names += f"  ·  {spec.data['index'] + 1}/{spec.data['count']}"
    prev, nxt = _seq_neighbors(P, spec.key, _is_quarter_key)
    body = page_header(ink, P.content, f"Q{q} 2027", names,
                       buttons=[("Goals" if m.compact else "Goals & Review", f"q{q}-goals")],
                       prev=prev, next=nxt)
    color = t.q(q)
    week_keys = P.week_keys
    if mode == "row":
        _, mh = _block_min(P, True)
        top, bottom = body.take_top(max(mh, body.h * 0.62), m.space * 1.5)
        for (y, mo), cell, low in zip(months, top.cols(3, m.space * 1.5), bottom.cols(3, m.space * 1.5)):
            month_block(ink, cell, y, mo, P.fw, week_col=True, week_keys=week_keys, quarter_color=color)
            lines_box(ink, low, f"{cal.MONTH_ABBR[mo]} key dates")
    elif mode == "2x2":
        cells = [c for row in body.grid(2, 2, m.space * 1.5, m.space * 1.5) for c in row]
        for (y, mo), cell in zip(months, cells):
            month_block(ink, cell, y, mo, P.fw, week_col=True, week_keys=week_keys, quarter_color=color)
        lines_box(ink, cells[3], "Milestones & key dates")
    else:
        mw, mh = _block_min(P, True)
        cols, rows = _fit(P, body.w, body.h, mw, mh)
        cells = [c for row in body.grid(cols, rows, m.space, m.space) for c in row]
        for (y, mo), cell in zip(months, cells):
            month_block(ink, cell, y, mo, P.fw, week_col=True, week_keys=week_keys, quarter_color=color)


def quarter_goals(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    q = spec.data["q"]
    prev, nxt = _seq_neighbors(P, spec.key, _is_quarter_key)
    body = page_header(ink, P.content, f"Q{q} Goals & Review",
                       f"{cal.MONTH_ABBR[3 * q - 2]} – {cal.MONTH_ABBR[3 * q]} 2027",
                       buttons=[("Overview", f"q{q}")], prev=prev, next=nxt)
    sp = m.space * 1.5
    if P.opts.landscape:
        left, right = body.cols(2, sp)
        goals_r = left
        miles_r, review_r = right.rows([0.45, 0.55], sp)
    else:
        goals_r, miles_r, review_r = body.rows([0.52, 0.2, 0.28], sp)

    # Goals: three cards.
    cards = section(ink, goals_r, "Quarter goals").rows(3, m.space)
    for i, card in enumerate(cards, 1):
        ink.box(card, stroke=t.grid, width=m.lw_grid, radius=m.radius)
        inner = card.inset(m.mm(2.5), m.mm(1.5))
        head, rest = inner.take_top(m.ruled * 0.9, m.mm(1))
        ink.text(head.x, head.y + m.mm(1.2), str(i), m.fs_title * 0.9, BOLD, t.q(q))
        ink.line(head.x + m.mm(7), head.y + m.mm(0.8), head.right, head.y + m.mm(0.8), t.rule)
        # Two lines per column, shrinking the spacing (not below 4 mm) to make them fit.
        step = min(m.ruled * 0.85, m.mm(5.5), (rest.h - m.mm(4.5)) / 2.05)
        if step < m.mm(4):   # too short for two columns of lines
            lines_box(ink, rest.pad(top=m.mm(1)), "Why it matters / key results",
                      step=min(m.ruled * 0.85, m.mm(5.5)))
        else:
            why, krs = rest.cols([0.42, 0.58], m.space)
            lines_box(ink, why.pad(top=m.mm(1)), "Why it matters", step=step)
            checklist(ink, krs.pad(top=m.mm(1)), "Key results", step=step)

    # Monthly milestones with a tap target for each month.
    mr = section(ink, miles_r, "Monthly milestones")
    for (y, mo), col in zip(cal.quarter_months(q), mr.cols(3, m.space)):
        btn, rest = col.take_top(m.tap, m.mm(1))
        button(ink, btn, cal.MONTH_NAMES[mo] if btn.w > m.mm(26) else cal.MONTH_ABBR[mo],
               month_key(y, mo), fill=t.qt(q))
        ink.hlines(rest, m.ruled * 0.9)

    rr = section(ink, review_r, "Quarter review")
    for title, col in zip(("Wins", "Lessons", "Carry forward"), rr.cols(3, m.space)):
        lines_box(ink, col, title, step=m.ruled * 0.9)


# --- monthly ---------------------------------------------------------------------------
def month_page(P, spec) -> None:
    ink, m, t = P.ink, P.m, P.t
    y, mo = spec.data["year"], spec.data["mon"]
    i = cal.MONTHS.index((y, mo))
    prev = month_key(*cal.MONTHS[i - 1]) if i > 0 else None
    nxt = month_key(*cal.MONTHS[i + 1]) if i + 1 < len(cal.MONTHS) else None
    q = cal.quarter_of(y, mo)
    buttons = [("Habits", spec.key + "-h")] if m.compact else []
    body = page_header(ink, P.content, cal.MONTH_NAMES[mo], f"{y}  ·  Q{q}", buttons=buttons,
                       prev=prev, next=nxt)
    if m.compact:
        _month_grid(P, body, y, mo)
        return
    side, grid = body.take_right(body.w * (0.27 if P.opts.landscape else 0.31), m.space * 1.5)
    _month_grid(P, grid, y, mo)
    _focus_and_habits(P, side, y, mo, n_habits=5 if not P.opts.landscape else 6)


def month_habits(P, spec) -> None:
    ink, m = P.ink, P.m
    y, mo = spec.data["year"], spec.data["mon"]
    body = page_header(ink, P.content, cal.MONTH_NAMES[mo], "Focus & Habits",
                       buttons=[("Calendar", month_key(y, mo))])
    if P.opts.landscape:
        focus, habits = body.cols([0.3, 0.7], m.space * 1.5)
        fb = section(ink, focus, "Monthly focus")
        n_top, rest = fb.take_top(min(fb.h * 0.6, 3 * m.ruled * 1.15))
        _numbered(P, n_top, 3)
        ink.hlines(rest, m.ruled)
        habit_matrix(ink, section(ink, habits, "Habit tracker"),
                     [date(y, mo, d) for d in range(1, cal.days_in_month(y, mo) + 1)], 6)
        return
    _focus_and_habits(P, body, y, mo, n_habits=6)


def _month_grid(P, r: Rect, y: int, mo: int) -> None:
    ink, m, t = P.ink, P.m, P.t
    hdr, grid = r.take_top(m.mm(5.5))
    wk_w = m.tap
    order = cal.weekday_order(P.fw)
    rows = cal.month_rows(y, mo, P.fw)
    cw = (r.w - wk_w) / 7
    rh = grid.h / len(rows)
    ink.text(r.x + wk_w / 2, hdr.y + m.mm(1.6), "WK", m.fs_small, BOLD, t.muted, "center")
    for j, wd in enumerate(order):
        lb = cal.DAY_ABBR[wd].upper()[: 2 if m.compact else 3]
        ink.text(r.x + wk_w + (j + 0.5) * cw, hdr.y + m.mm(1.6), lb, m.fs_small, BOLD,
                 t.weekend if wd >= 5 else t.muted, "center", tracking=m.fs_small * 0.06)
    # Grid lines.
    ink.line(r.x, grid.top, r.right, grid.top, t.soft, m.lw_box)
    for i in range(1, len(rows) + 1):
        yy = grid.top - i * rh
        ink.line(r.x, yy, r.right, yy, t.rule, m.lw_rule)
    for j in range(8):
        xx = r.x + wk_w + j * cw
        ink.line(xx, grid.y, xx, grid.top, t.grid, m.lw_grid)
    for i, start in enumerate(rows):
        ry = grid.top - (i + 1) * rh
        wcell = Rect(r.x, ry, wk_w, rh)
        wk = cal.iso_week(start, P.fw)[1]
        ink.text(wcell.cx, wcell.top - m.mm(2) - m.fs_small * 0.7, f"W{wk:02d}", m.fs_small, BOLD,
                 t.muted, "center")
        if week_key(start) in P.week_keys:
            ink.link(wcell, week_key(start))
        for j, d in enumerate(cal.week_days(start)):
            cell = Rect(r.x + wk_w + j * cw, ry, cw, rh)
            inside = d.month == mo
            color = (t.weekend if cal.is_weekend(d) else t.ink) if inside else t.faint
            ink.text(cell.x + m.mm(1.4), cell.top - m.mm(1.4) - m.fs_body * 0.72, str(d.day),
                     m.fs_body, BOLD if inside else REGULAR, color)
            if inside and cal.in_range(d):
                ink.link(cell, day_key(d))


def _focus_and_habits(P, r: Rect, y: int, mo: int, n_habits: int) -> None:
    ink, m, t = P.ink, P.m, P.t
    focus, habits = r.take_top(r.h * 0.3, m.space * 1.5)
    body = section(ink, focus, "Monthly focus")
    n_top, rest = body.take_top(min(body.h * 0.62, 3 * m.ruled * 1.15))
    _numbered(P, n_top, 3)
    ink.hlines(rest, m.ruled)
    hb = section(ink, habits, "Habit tracker")
    days = list(range(1, cal.days_in_month(y, mo) + 1))
    weekend = {i for i, d in enumerate(days) if date(y, mo, d).weekday() >= 5}
    habit_grid(ink, hb, [str(d) for d in days], n_habits, weekend_rows=weekend)


def _numbered(P, r: Rect, n: int) -> None:
    ink, m, t = P.ink, P.m, P.t
    step = r.h / n
    rad = min(step * 0.3, m.mm(2.1))
    for i in range(n):
        yy = r.top - (i + 1) * step
        ink.circle(r.x + rad + m.mm(0.3), yy + step / 2, rad, stroke=t.accent, width=m.lw_box)
        ink.text(r.x + rad + m.mm(0.3), yy + step / 2 - m.fs_small * 0.35, str(i + 1), m.fs_small,
                 BOLD, t.accent, "center")
        ink.line(r.x + 2 * rad + m.mm(2), yy, r.right, yy, t.rule, m.lw_rule)
