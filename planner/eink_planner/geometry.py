"""Rectangles in PDF page units (origin bottom-left) with top-down split helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def top(self) -> float:
        return self.y + self.h

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def pad(self, left=0.0, top=0.0, right=0.0, bottom=0.0) -> "Rect":
        return Rect(self.x + left, self.y + bottom, self.w - left - right, self.h - top - bottom)

    def inset(self, dx: float, dy: float | None = None) -> "Rect":
        dy = dx if dy is None else dy
        return self.pad(dx, dy, dx, dy)

    # --- slicing -----------------------------------------------------------
    def take_top(self, h: float, gap: float = 0.0) -> tuple["Rect", "Rect"]:
        """Return (top slice of height h, remainder below it minus gap)."""
        return (Rect(self.x, self.top - h, self.w, h),
                Rect(self.x, self.y, self.w, self.h - h - gap))

    def take_bottom(self, h: float, gap: float = 0.0) -> tuple["Rect", "Rect"]:
        return (Rect(self.x, self.y, self.w, h),
                Rect(self.x, self.y + h + gap, self.w, self.h - h - gap))

    def take_left(self, w: float, gap: float = 0.0) -> tuple["Rect", "Rect"]:
        return (Rect(self.x, self.y, w, self.h),
                Rect(self.x + w + gap, self.y, self.w - w - gap, self.h))

    def take_right(self, w: float, gap: float = 0.0) -> tuple["Rect", "Rect"]:
        return (Rect(self.right - w, self.y, w, self.h),
                Rect(self.x, self.y, self.w - w - gap, self.h))

    # --- splitting ---------------------------------------------------------
    @staticmethod
    def _sizes(total: float, spec, gap: float) -> list[float]:
        """spec: int (equal parts), list of weights, or list of fixed sizes / None (flex)."""
        if isinstance(spec, int):
            spec = [1.0] * spec
        if any(s is None for s in spec):
            fixed = sum(s for s in spec if s is not None)
            n_flex = sum(1 for s in spec if s is None)
            flex = (total - fixed - gap * (len(spec) - 1)) / n_flex
            return [flex if s is None else s for s in spec]
        avail = total - gap * (len(spec) - 1)
        tot = float(sum(spec))
        return [avail * s / tot for s in spec]

    def rows(self, spec, gap: float = 0.0) -> list["Rect"]:
        """Split vertically, first item on top."""
        out, y = [], self.top
        for s in self._sizes(self.h, spec, gap):
            out.append(Rect(self.x, y - s, self.w, s))
            y -= s + gap
        return out

    def cols(self, spec, gap: float = 0.0) -> list["Rect"]:
        out, x = [], self.x
        for s in self._sizes(self.w, spec, gap):
            out.append(Rect(x, self.y, s, self.h))
            x += s + gap
        return out

    def grid(self, ncols: int, nrows: int, gx: float = 0.0, gy: float = 0.0) -> list[list["Rect"]]:
        """Cells as rows (top first) of columns (left first)."""
        return [r.cols(ncols, gx) for r in self.rows(nrows, gy)]

    def overlap_area(self, o: "Rect") -> float:
        w = min(self.right, o.right) - max(self.x, o.x)
        h = min(self.top, o.top) - max(self.y, o.y)
        return w * h if w > 0 and h > 0 else 0.0
