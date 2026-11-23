"""Drawing primitives on a ReportLab canvas, plus tap-target-checked internal links."""

from __future__ import annotations

import math

from reportlab.pdfbase.pdfmetrics import stringWidth

from .devices import Metrics
from .geometry import Rect
from .theme import Theme

REGULAR = "Helvetica"
BOLD = "Helvetica-Bold"
LIGHT = "Helvetica"  # standard-14 has no light weight; color does the work


class LayoutError(RuntimeError):
    """A tap target is too small, overlaps another, or points nowhere."""


class Ink:
    def __init__(self, canvas, metrics: Metrics, theme: Theme, keys: set[str]):
        self.c = canvas
        self.m = metrics
        self.t = theme
        self.keys = keys
        self.page_key = ""
        self.targets: list[tuple[Rect, str]] = []
        self.link_count = 0

    def start_page(self, key: str) -> None:
        self.page_key = key
        self.targets = []

    # --- text --------------------------------------------------------------
    @staticmethod
    def width(s: str, size: float, font: str = REGULAR, tracking: float = 0.0) -> float:
        return stringWidth(s, font, size) + tracking * max(len(s) - 1, 0)

    def fit_size(self, s: str, size: float, max_w: float, font: str = REGULAR,
                 min_size: float | None = None, tracking: float = 0.0) -> float:
        min_size = min_size or size * 0.6
        while size > min_size and self.width(s, size, font, tracking) > max_w:
            size *= 0.94
        return size

    def text(self, x: float, y: float, s: str, size: float, font: str = REGULAR,
             color=None, align: str = "left", tracking: float = 0.0) -> float:
        """Draw at baseline y. Returns the drawn width."""
        c = self.c
        w = self.width(s, size, font, tracking)
        if align == "center":
            x -= w / 2
        elif align == "right":
            x -= w
        c.setFillColor(color if color is not None else self.t.ink)
        c.setFont(font, size)
        if tracking:
            c.drawString(x, y, s, charSpace=tracking)
        else:
            c.drawString(x, y, s)
        return w

    def text_in(self, r: Rect, s: str, size: float, font: str = REGULAR, color=None,
                align: str = "center", pad: float = 0.0, tracking: float = 0.0,
                valign: str = "middle") -> float:
        """Draw text inside r, shrinking to fit the width. Returns final size."""
        size = self.fit_size(s, size, r.w - 2 * pad, font, tracking=tracking)
        cap = size * 0.70
        if valign == "middle":
            y = r.cy - cap / 2
        elif valign == "top":
            y = r.top - pad - cap
        else:
            y = r.y + pad
        x = {"left": r.x + pad, "center": r.cx, "right": r.right - pad}[align]
        self.text(x, y, s, size, font, color, align, tracking)
        return size

    def label(self, x: float, y_top: float, s: str, color=None, size: float | None = None,
              bar: bool = True, max_w: float | None = None) -> float:
        """Small uppercase section label with an accent tick. Returns the height used."""
        m = self.m
        size = size or m.fs_label
        cap = size * 0.70
        if max_w:
            size = self.fit_size(s.upper(), size, max_w - m.mm(2), BOLD, tracking=size * 0.08)
        tx = x
        if bar:
            self.box(Rect(x, y_top - cap, m.mm(0.7), cap), fill=self.t.accent)
            tx = x + m.mm(1.8)
        self.text(tx, y_top - cap, s.upper(), size, BOLD, color or self.t.muted,
                  tracking=size * 0.08)
        return cap + m.mm(1.6)

    # --- shapes ------------------------------------------------------------
    def line(self, x1, y1, x2, y2, color=None, width=None, dash=None) -> None:
        c = self.c
        c.setStrokeColor(color if color is not None else self.t.rule)
        c.setLineWidth(width if width is not None else self.m.lw_rule)
        c.setDash(dash or [])
        c.line(x1, y1, x2, y2)
        if dash:
            c.setDash([])

    def box(self, r: Rect, stroke=None, fill=None, width=None, radius: float = 0.0,
            dash=None) -> None:
        c = self.c
        if stroke is not None:
            c.setStrokeColor(stroke)
            c.setLineWidth(width if width is not None else self.m.lw_box)
            c.setDash(dash or [])
        if fill is not None:
            c.setFillColor(fill)
        if radius:
            c.roundRect(r.x, r.y, r.w, r.h, radius, stroke=stroke is not None, fill=fill is not None)
        else:
            c.rect(r.x, r.y, r.w, r.h, stroke=stroke is not None, fill=fill is not None)
        if dash:
            c.setDash([])

    def circle(self, x, y, radius, stroke=None, fill=None, width=None) -> None:
        c = self.c
        if stroke is not None:
            c.setStrokeColor(stroke)
            c.setLineWidth(width if width is not None else self.m.lw_box)
        if fill is not None:
            c.setFillColor(fill)
        c.circle(x, y, radius, stroke=stroke is not None, fill=fill is not None)

    def checkbox(self, x: float, cy: float, size: float | None = None, color=None) -> float:
        size = size or self.m.mm(2.8)
        self.box(Rect(x, cy - size / 2, size, size), stroke=color or self.t.rule,
                 width=self.m.lw_box, radius=size * 0.18)
        return size

    def triangle(self, r: Rect, direction: str, color=None) -> None:
        s = min(r.w, r.h) * 0.28
        cx, cy = r.cx, r.cy
        p = self.c.beginPath()
        if direction == "left":
            p.moveTo(cx + s * 0.55, cy + s)
            p.lineTo(cx - s * 0.65, cy)
            p.lineTo(cx + s * 0.55, cy - s)
        else:
            p.moveTo(cx - s * 0.55, cy + s)
            p.lineTo(cx + s * 0.65, cy)
            p.lineTo(cx - s * 0.55, cy - s)
        p.close()
        self.c.setFillColor(color if color is not None else self.t.ink)
        self.c.drawPath(p, stroke=0, fill=1)

    # --- writing surfaces ----------------------------------------------------
    def _snap(self, start: float, length: float, step: float) -> tuple[float, int]:
        n = max(int(math.floor(length / step + 1e-6)), 1)
        return start + (length - n * step) / 2, n

    def grid(self, r: Rect, step: float | None = None, color=None, width=None,
             major: int = 0) -> None:
        """Fine grid, centered in r so partial cells are split evenly."""
        step = step or self.m.grid
        x0, nx = self._snap(r.x, r.w, step)
        y0, ny = self._snap(r.y, r.h, step)
        c = self.c
        minor, majors = c.beginPath(), c.beginPath()
        for i in range(nx + 1):
            p = majors if major and i % major == 0 else minor
            x = x0 + i * step
            p.moveTo(x, y0)
            p.lineTo(x, y0 + ny * step)
        for j in range(ny + 1):
            p = majors if major and j % major == 0 else minor
            y = y0 + j * step
            p.moveTo(x0, y)
            p.lineTo(x0 + nx * step, y)
        c.setDash([])
        c.setLineCap(0)
        c.setStrokeColor(color if color is not None else self.t.grid)
        c.setLineWidth(width if width is not None else self.m.lw_grid)
        c.drawPath(minor, stroke=1, fill=0)
        if major:
            c.setStrokeColor(self.t.rule)
            c.drawPath(majors, stroke=1, fill=0)

    def dots(self, r: Rect, step: float | None = None, color=None, size: float | None = None,
             iso: bool = False) -> None:
        step = step or self.m.dot
        dy = step * (math.sqrt(3) / 2 if iso else 1)
        x0, nx = self._snap(r.x, r.w, step)
        y0, ny = self._snap(r.y, r.h, dy)
        c = self.c
        p = c.beginPath()
        for j in range(ny + 1):
            off = step / 2 if iso and j % 2 else 0.0
            for i in range(nx + 1):
                x = x0 + i * step + off
                if x > r.right + 0.01:
                    continue
                y = y0 + j * dy
                p.moveTo(x, y)
                p.lineTo(x + 0.01, y)
        c.setDash([])
        c.setLineCap(1)
        c.setStrokeColor(color if color is not None else self.t.rule)
        c.setLineWidth(size or self.m.pt(1.1))
        c.drawPath(p, stroke=1, fill=0)
        c.setLineCap(0)

    def hlines(self, r: Rect, step: float | None = None, color=None, width=None,
               dash=None, top_line: bool = False) -> list[float]:
        """Ruled lines from the top of r down. Returns the y of each line."""
        step = step or self.m.ruled
        ys = []
        y = r.top if top_line else r.top - step
        while y >= r.y - 0.01:
            ys.append(y)
            y -= step
        if not ys:
            return ys
        c = self.c
        p = c.beginPath()
        for y in ys:
            p.moveTo(r.x, y)
            p.lineTo(r.right, y)
        c.setStrokeColor(color if color is not None else self.t.rule)
        c.setLineWidth(width if width is not None else self.m.lw_rule)
        c.setDash(dash or [])
        c.drawPath(p, stroke=1, fill=0)
        c.setDash([])
        return ys

    # --- links -------------------------------------------------------------
    def link(self, r: Rect, key: str) -> None:
        """Internal hyperlink. Enforces minimum tap size and no overlap on the page."""
        if key not in self.keys:
            raise LayoutError(f"page {self.page_key!r}: link to unknown page {key!r}")
        floor = self.m.tap_min - 0.01
        if r.w < floor or r.h < floor:
            raise LayoutError(
                f"page {self.page_key!r}: tap target to {key!r} is "
                f"{self.m.to_mm(r.w):.1f}x{self.m.to_mm(r.h):.1f} mm "
                f"(minimum {self.m.tap_min_mm} mm)")
        eps = self.m.mm(0.05) ** 2
        for other, okey in self.targets:
            if r.overlap_area(other) > eps:
                raise LayoutError(f"page {self.page_key!r}: tap targets {okey!r} and {key!r} overlap")
        self.targets.append((r, key))
        self.c.linkRect("", key, (r.x, r.y, r.right, r.top), relative=0, thickness=0)
        self.link_count += 1
