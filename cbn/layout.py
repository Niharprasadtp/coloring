"""Page sizes, difficulty presets, and the image-to-page fitting math.

All geometry produced by the pipeline is in image pixel coordinates (origin
top-left, y down). A Placement maps those coordinates onto a PDF page
(origin bottom-left, y up) with one uniform scale, so nothing is stretched.
"""

from dataclasses import dataclass

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import inch

MM2_PER_PT2 = (25.4 / 72) ** 2


@dataclass(frozen=True)
class PageSpec:
    key: str
    label: str
    width: float
    height: float
    margin: float      # safe margin on every side (home printers clip ~0.25in)
    band: float        # footer band for the color strip and reference thumbnail
    ui: float          # scale factor for footer/legend typography
    min_font: float    # smallest region number, in points
    max_font: float    # largest region number, in points
    line_width: float  # outline stroke, in points


PAGE_SPECS = {
    "letter": PageSpec("letter", "US Letter", *LETTER, margin=0.5 * inch,
                       band=0.95 * inch, ui=1.0, min_font=4.5, max_font=10, line_width=0.4),
    "a4": PageSpec("a4", "A4", *A4, margin=0.5 * inch,
                   band=0.95 * inch, ui=1.0, min_font=4.5, max_font=10, line_width=0.4),
    "16x20": PageSpec("16x20", "16x20 in", 16 * inch, 20 * inch, margin=0.75 * inch,
                      band=1.6 * inch, ui=1.7, min_font=6, max_font=16, line_width=0.6),
}


@dataclass(frozen=True)
class Difficulty:
    colors: int            # K for K-Means (before near-duplicate merging)
    min_area_mm2: float    # smallest printable region on the smallest page
    min_radius_pt: float   # region must fit a circle this big to hold a number
    max_regions: int       # above this the page is flagged as too busy
    number_spacing_pt: float  # repeat the number in regions larger than this


DIFFICULTIES = {
    "relaxing": Difficulty(colors=16, min_area_mm2=40, min_radius_pt=4.5,
                           max_regions=400, number_spacing_pt=170),
    "intermediate": Difficulty(colors=24, min_area_mm2=15, min_radius_pt=3.2,
                               max_regions=900, number_spacing_pt=150),
    "expert": Difficulty(colors=32, min_area_mm2=6, min_radius_pt=2.4,
                         max_regions=2500, number_spacing_pt=130),
}


@dataclass(frozen=True)
class Placement:
    scale: float     # points per image pixel
    x0: float        # page x of the drawn image's left edge
    y0: float        # page y of the drawn image's bottom edge
    rotated: bool    # image turned 90 degrees clockwise to fill a portrait page
    img_w: int
    img_h: int

    @property
    def drawn_w(self):
        return (self.img_h if self.rotated else self.img_w) * self.scale

    @property
    def drawn_h(self):
        return (self.img_w if self.rotated else self.img_h) * self.scale

    def to_page(self, x, y):
        """Map image pixel coordinates (scalars or arrays) to page points."""
        if self.rotated:
            x, y = self.img_h - y, x
            h = self.img_w
        else:
            h = self.img_h
        return self.x0 + x * self.scale, self.y0 + (h - y) * self.scale


def content_box(spec):
    """(x, y, w, h) of the area available for the line art."""
    x = spec.margin
    y = spec.margin + spec.band
    return x, y, spec.width - 2 * spec.margin, spec.height - 2 * spec.margin - spec.band


def fit(spec, img_w, img_h, auto_rotate=False):
    """Largest uniform scale that fits the image in the content box, centered."""
    bx, by, bw, bh = content_box(spec)
    scale, rotated = min(bw / img_w, bh / img_h), False
    if auto_rotate:
        turned = min(bw / img_h, bh / img_w)
        if turned > scale * 1.05:
            scale, rotated = turned, True
    dw, dh = (img_h, img_w) if rotated else (img_w, img_h)
    return Placement(scale=scale,
                     x0=bx + (bw - dw * scale) / 2,
                     y0=by + (bh - dh * scale) / 2,
                     rotated=rotated, img_w=img_w, img_h=img_h)


def detail_groups(specs, img_w, img_h, auto_rotate=False, tolerance=0.05):
    """Group page sizes that print the image at nearly the same scale.

    Each group is processed once, with region size limits enforced at the
    group's smallest scale: Letter and A4 share one level of detail, while
    16x20 has room for much finer regions.

    Returns a list of (scale, [specs]).
    """
    groups = []
    for spec in sorted(specs, key=lambda s: fit(s, img_w, img_h, auto_rotate).scale):
        scale = fit(spec, img_w, img_h, auto_rotate).scale
        if groups and scale <= groups[-1][0] * (1 + tolerance):
            groups[-1][1].append(spec)
        else:
            groups.append((scale, [spec]))
    return groups
