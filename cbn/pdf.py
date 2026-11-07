"""ReportLab book assembly: template pages, reference gallery, master color key."""

import io
import math
from dataclasses import dataclass, field

import cv2
import numpy as np
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfgen.canvas import FILL_EVEN_ODD

from .layout import fit

LINE_GRAY = 0.55     # outlines: light enough to vanish under color
NUMBER_GRAY = 0.45
TEXT_GRAY = 0.3
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
_FLIPS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}


@dataclass
class BookPage:
    name: str
    width: int                  # working image size in pixels
    height: int
    outlines: list              # (N, 2) arrays of (x, y) image coordinates
    markers: list               # regions.Marker
    used: list                  # 0-based palette indices present on the page
    reference: np.ndarray = field(repr=False)  # quantized RGB image
    details: list = field(default_factory=list)  # (rgb, [polygons]) too small to number
    detail_style: str = "outline"  # "outline": drawn for the buyer to color; "color": printed filled in


def _needs_underline(text, n_colors):
    """True when the number reads as a different valid number upside down (6/9, 16/91, ...)."""
    if not all(ch in _FLIPS for ch in text):
        return False
    flipped = "".join(_FLIPS[ch] for ch in reversed(text))
    return flipped != text and 1 <= int(flipped) <= n_colors


def _jpeg(rgb, max_side):
    rgb = np.ascontiguousarray(rgb)
    h, w = rgb.shape[:2]
    f = min(1.0, max_side / max(h, w))
    if f < 1:
        rgb = cv2.resize(rgb, (round(w * f), round(h * f)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return ImageReader(io.BytesIO(buf.tobytes()))


def _swatch(c, x, y, size, rgb):
    c.setFillColorRGB(*(np.asarray(rgb) / 255))
    c.setStrokeGray(0.6)
    c.setLineWidth(0.5)
    c.rect(x, y, size, size, stroke=1, fill=1)


def _draw_number(c, x, y, text, size, rotated, underline):
    c.saveState()
    c.translate(x, y)
    if rotated:
        c.rotate(-90)
    c.setFont(FONT, size)
    c.drawCentredString(0, -0.36 * size, text)
    if underline:
        half = stringWidth(text, FONT, size) / 2
        c.setLineWidth(0.07 * size)
        c.line(-half, -0.5 * size, half, -0.5 * size)
    c.restoreState()


def _template_page(c, spec, page, palette, n_colors, title, page_no, auto_rotate):
    pl = fit(spec, page.width, page.height, auto_rotate)

    # Line art: one path with every outline.
    c.setStrokeGray(LINE_GRAY)
    c.setLineWidth(spec.line_width)
    c.setLineJoin(1)
    c.setLineCap(1)
    path = c.beginPath()
    for line in page.outlines:
        xs, ys = pl.to_page(line[:, 0], line[:, 1])
        path.moveTo(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(x, y)
    c.drawPath(path, stroke=1, fill=0)
    c.rect(pl.x0, pl.y0, pl.drawn_w, pl.drawn_h, stroke=1, fill=0)

    # Details too small to number (eyes, pupils, fine markings): printed in
    # color, or outlined for the buyer to color from the reference page.
    outline = page.detail_style == "outline"
    if outline:
        c.setStrokeGray(LINE_GRAY)
        c.setLineWidth(spec.line_width)
    for rgb, polys in page.details:
        c.setFillColorRGB(*(np.asarray(rgb) / 255))
        path = c.beginPath()
        for poly in polys:
            xs, ys = pl.to_page(poly[:, 0], poly[:, 1])
            path.moveTo(xs[0], ys[0])
            for x, y in zip(xs[1:], ys[1:]):
                path.lineTo(x, y)
            path.close()
        c.drawPath(path, stroke=int(outline), fill=int(not outline), fillMode=FILL_EVEN_ODD)

    # Region numbers, sized to the space available in each region.
    c.setFillGray(NUMBER_GRAY)
    c.setStrokeGray(NUMBER_GRAY)
    for m in page.markers:
        text = str(m.color + 1)
        room = m.radius * pl.scale
        size = 0.85 * room / (0.66 if len(text) > 1 else 0.46)
        size = min(max(size, spec.min_font), spec.max_font)
        x, y = pl.to_page(m.x, m.y)
        _draw_number(c, x, y, text, size, pl.rotated, _needs_underline(text, n_colors))

    _footer(c, spec, page, palette, title, page_no, pl.rotated)


def _footer(c, spec, page, palette, title, page_no, rotated):
    """Color strip for this page's numbers, a reference thumbnail, and the page number."""
    ui = spec.ui
    left, bottom = spec.margin, spec.margin
    width, top = spec.width - 2 * spec.margin, spec.margin + spec.band - 6 * ui

    ref = np.rot90(page.reference, k=-1) if rotated else page.reference
    th = top - bottom
    tw = min(th * ref.shape[1] / ref.shape[0], width * 0.3)
    th = tw * ref.shape[0] / ref.shape[1]
    c.drawImage(_jpeg(ref, 500), left + width - tw, bottom, tw, th)

    caption = 8 * ui
    c.setFillGray(TEXT_GRAY)
    c.setFont(FONT, 7 * ui)
    c.drawString(left, bottom, f"{title}  ·  page {page_no}")

    strip_w = width - tw - 12 * ui
    strip_h = top - (bottom + caption + 4 * ui)
    n = len(page.used)
    rows = 1
    while rows < 3 and strip_w / math.ceil(n / rows) < 26 * ui:
        rows += 1
    per_row = math.ceil(n / rows)
    cell_w = min(strip_w / per_row, 40 * ui)
    row_h = strip_h / rows
    sq = min(row_h * 0.55, cell_w * 0.6)
    num_size = min(row_h * 0.3, 9 * ui)
    for i, color in enumerate(page.used):
        r, col = divmod(i, per_row)
        cx = left + col * cell_w + cell_w / 2
        y_top = top - r * row_h
        _swatch(c, cx - sq / 2, y_top - sq, sq, palette[color])
        c.setFillGray(TEXT_GRAY)
        c.setFont(FONT_BOLD, num_size)
        c.drawCentredString(cx, y_top - sq - num_size * 1.05, str(color + 1))


def _blank_back(c, spec):
    c.setFillGray(0.7)
    c.setFont(FONT, 7 * spec.ui)
    c.drawCentredString(spec.width / 2, spec.margin,
                        "This page is intentionally blank so markers do not bleed through.")


def _heading(c, spec, text, sub=None):
    ui = spec.ui
    c.setFillGray(0.15)
    c.setFont(FONT_BOLD, 20 * ui)
    y = spec.height - spec.margin - 20 * ui
    c.drawString(spec.margin, y, text)
    if sub:
        c.setFillGray(TEXT_GRAY)
        c.setFont(FONT, 9 * ui)
        c.drawString(spec.margin, y - 16 * ui, sub)
    return y - 34 * ui


def _gallery(c, spec, pages):
    """Full-color references, four per page."""
    ui = spec.ui
    for start in range(0, len(pages), 4):
        top = _heading(c, spec, "Color Reference", "What each finished page looks like.")
        width = spec.width - 2 * spec.margin
        cell_w, cell_h = width / 2, (top - spec.margin) / 2
        for i, page in enumerate(pages[start:start + 4]):
            r, col = divmod(i, 2)
            x = spec.margin + col * cell_w
            y = top - (r + 1) * cell_h
            avail_w, avail_h = cell_w - 12 * ui, cell_h - 12 * ui
            s = min(avail_w / page.width, avail_h / page.height)
            w, h = page.width * s, page.height * s
            c.drawImage(_jpeg(page.reference, 1200), x + (cell_w - w) / 2, y + (cell_h - h) / 2, w, h)
        c.showPage()


def _master_key(c, spec, palette):
    ui = spec.ui
    cell_w, cell_h, sq = 132 * ui, 46 * ui, 32 * ui
    width = spec.width - 2 * spec.margin
    cols = max(1, int(width // cell_w))
    cell_w = width / cols
    sub = f"{len(palette)} colors · Print this page to check how your printer reproduces each color."
    i = 0
    while i < len(palette):
        top = _heading(c, spec, "Master Color Key", sub)
        rows = max(1, int((top - spec.margin) // cell_h))
        for slot in range(rows * cols):
            if i >= len(palette):
                break
            r, col = divmod(slot, cols)
            x = spec.margin + col * cell_w
            y = top - (r + 1) * cell_h
            rgb = palette[i]
            _swatch(c, x, y + (cell_h - sq) / 2, sq, rgb)
            c.setFillGray(0.15)
            c.setFont(FONT_BOLD, 14 * ui)
            c.drawString(x + sq + 8 * ui, y + cell_h / 2 + 2 * ui, str(i + 1))
            c.setFillGray(TEXT_GRAY)
            c.setFont(FONT, 7 * ui)
            hexcode = "#%02X%02X%02X" % tuple(int(v) for v in rgb)
            c.drawString(x + sq + 8 * ui, y + cell_h / 2 - 9 * ui,
                         f"{hexcode}  RGB {rgb[0]}, {rgb[1]}, {rgb[2]}")
            i += 1
        c.showPage()


def build_pdf(path, spec, pages, palette, title, auto_rotate=False, blank_backs=True):
    """Write one book: templates (with blank backs), reference gallery, master key."""
    c = rl_canvas.Canvas(str(path), pagesize=(spec.width, spec.height), pageCompression=1)
    c.setTitle(f"{title} ({spec.label})")
    c.setSubject("Color by number")
    for page_no, page in enumerate(pages, start=1):
        _template_page(c, spec, page, palette, len(palette), title, page_no, auto_rotate)
        c.showPage()
        if blank_backs:
            _blank_back(c, spec)
            c.showPage()
    _gallery(c, spec, pages)
    _master_key(c, spec, palette)
    c.save()
