"""Persistent 1-tap navigation drawn on every page.

* Quick-jump strip along the top: Home | Year | Q1-Q4 | Brain Dump | Projects | Templates.
* Month rail on the side opposite the writing hand: Dec '26, Jan-Dec '27.

When the strip cannot fit all items at the minimum tap size (the compact Move in
portrait), the quarter tabs move into the rail, each placed before its months.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .calendar_model import MONTH_ABBR, MONTHS, quarter_of
from .devices import Metrics, Options
from .geometry import Rect
from .ink import BOLD, Ink
from .theme import Theme


def month_key(year: int, month: int) -> str:
    return f"m-{year}-{month:02d}"


# (section id, label, short label, destination key, group)
SECTIONS = [
    ("home", "Home", "Home", "home", 0),
    ("year", "Year", "Year", "year-1", 0),
    ("q1", "Q1", "Q1", "q1", 1),
    ("q2", "Q2", "Q2", "q2", 1),
    ("q3", "Q3", "Q3", "q3", 1),
    ("q4", "Q4", "Q4", "q4", 1),
    ("braindump", "Brain Dump", "Dump", "bd-1", 2),
    ("projects", "Projects", "Proj.", "projects", 2),
    ("templates", "Templates", "Tmpl.", "templates", 2),
]


@dataclass
class Tab:
    rect: Rect
    label: str
    key: str
    ident: str            # section id or month key
    kind: str             # "section" | "quarter" | "month"
    quarter: int = 0
    sub: str = ""         # optional second line (year on month tabs)


class Chrome:
    def __init__(self, opts: Options, m: Metrics, t: Theme):
        self.opts, self.m, self.t = opts, m, t
        self.tabs: list[Tab] = []
        self._layout()

    # --- layout ------------------------------------------------------------
    def _strip_fits(self, items, avail: float, size: float, short: bool) -> bool:
        m = self.m
        need = sum(max(Ink.width(s[2] if short else s[1], size, BOLD) + m.mm(3), m.tap_min)
                   for s in items)
        return need + m.gap * (len(items) - 1) <= avail

    def _layout(self) -> None:
        m, side = self.m, self.opts.rail_side
        W, H = m.W, m.H
        # Strip spans the content column, so first find the rail width. Try with the
        # quarters in the strip; fall back to quarters in the rail.
        for quarters_in_rail in (False, True):
            rail_items = self._rail_items(quarters_in_rail)
            avail_h = H - 2 * m.edge
            rows_fit = max(int((avail_h + m.gap) // (m.tap + m.gap)), 1)
            if rows_fit * (m.tap_min + m.gap) - m.gap > avail_h:
                rows_fit = max(int((avail_h + m.gap) // (m.tap_min + m.gap)), 1)
            ncols = math.ceil(len(rail_items) / rows_fit)
            rail_w = ncols * m.tap + (ncols - 1) * m.gap
            if side == "left":
                cx0, cx1 = m.edge + rail_w + m.gutter, W - m.margin
            else:
                cx0, cx1 = m.margin, W - m.edge - rail_w - m.gutter
            strip_items = [s for s in SECTIONS if not (quarters_in_rail and s[4] == 1)]
            avail_w = cx1 - cx0
            fits = (self._strip_fits(strip_items, avail_w, m.fs_tab, False)
                    or self._strip_fits(strip_items, avail_w, m.fs_tab, True))
            if fits or quarters_in_rail:
                break
        self.quarters_in_rail = quarters_in_rail
        self.content = Rect(cx0, m.margin, cx1 - cx0, H - m.edge - m.tap - m.gutter - m.margin)

        # Rail tabs, column-major from the outer edge.
        nrows = math.ceil(len(rail_items) / ncols)
        tab_h = min((avail_h - (nrows - 1) * m.gap) / nrows, m.mm(22))
        rail_x0 = m.edge if side == "left" else W - m.edge - rail_w
        for i, item in enumerate(rail_items):
            col, row = divmod(i, nrows)
            if side == "right":
                col = ncols - 1 - col  # first column hugs the outer (right) edge
            x = rail_x0 + col * (m.tap + m.gap)
            y = H - m.edge - (row + 1) * tab_h - row * m.gap
            item.rect = Rect(x, y, m.tap, tab_h)
            self.tabs.append(item)

        # Strip tabs: natural widths, then share the slack evenly.
        short = not self._strip_fits(strip_items, avail_w, m.fs_tab, False)
        labels = [s[2] if short else s[1] for s in strip_items]
        nat = [max(Ink.width(lb, m.fs_tab, BOLD) + m.mm(3), m.tap_min) for lb in labels]
        group_gaps = sum(1 for a, b in zip(strip_items, strip_items[1:]) if a[4] != b[4])
        gaps = m.gap * (len(strip_items) - 1) + m.gap * 2 * group_gaps
        if sum(nat) + gaps > avail_w:     # drop the extra group spacing if tight
            gaps, group_gaps = m.gap * (len(strip_items) - 1), 0
        extra = max((avail_w - sum(nat) - gaps) / len(nat), 0)
        x = cx0
        y = H - m.edge - m.tap
        for i, (s, lb, w) in enumerate(zip(strip_items, labels, nat)):
            if i and group_gaps and strip_items[i - 1][4] != s[4]:
                x += m.gap * 2
            q = int(s[0][1]) if s[4] == 1 else 0
            self.tabs.append(Tab(Rect(x, y, w + extra, m.tap), lb, s[3], s[0],
                                 "quarter" if q else "section", q))
            x += w + extra + m.gap

    def _rail_items(self, with_quarters: bool) -> list[Tab]:
        items, seen_q = [], set()
        for (y, mo) in MONTHS:
            q = quarter_of(y, mo)
            if with_quarters and y == 2027 and q not in seen_q:
                seen_q.add(q)
                items.append(Tab(Rect(0, 0, 0, 0), f"Q{q}", f"q{q}", f"q{q}", "quarter", q))
            sub = f"'{y % 100}" if mo in (1, 12) else ""
            items.append(Tab(Rect(0, 0, 0, 0), MONTH_ABBR[mo].upper(), month_key(y, mo),
                             month_key(y, mo), "month", q, sub))
        return items

    # --- drawing -----------------------------------------------------------
    def draw(self, ink: Ink, section: str | None = None, month: tuple[int, int] | None = None) -> None:
        m, t = self.m, self.t
        active_month = month_key(*month) if month else None
        for tab in self.tabs:
            r = tab.rect
            active = tab.ident == section or tab.ident == active_month
            if active:
                fill = t.q(tab.quarter) if tab.quarter and tab.kind != "section" else t.active
                color = t.active_text
            else:
                fill = t.qt(tab.quarter) if tab.kind == "quarter" else t.tab
                color = t.tab_text
            ink.box(r, fill=fill, radius=m.radius)
            if tab.kind == "month" and not active:
                # Thin quarter-colored stripe on the outer edge.
                sw = m.mm(0.8)
                sx = r.x if self.opts.rail_side == "left" else r.right - sw
                ink.box(Rect(sx, r.y + m.radius, sw, r.h - 2 * m.radius), fill=t.q(tab.quarter))
            if tab.sub and r.h >= m.mm(9.5):
                size = ink.fit_size(tab.label, m.fs_tab, r.w - m.mm(1.6), BOLD)
                ink.text(r.cx, r.cy + size * 0.12, tab.label, size, BOLD, color, "center")
                ink.text(r.cx, r.cy - size * 0.95, tab.sub, m.fs_small, BOLD, color, "center")
            else:
                ink.text_in(r, tab.label, m.fs_tab, BOLD, color, pad=m.mm(0.8))
            ink.link(r, tab.key)
