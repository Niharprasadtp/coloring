"""Device presets, run options, and physical-unit metrics.

Each page is sized in PDF points equal to the device's native pixel grid, so on the
tablet one page unit is one screen pixel. Physical sizes (mm for tap targets and
grids, pt for type) are converted with the device's PPI, which keeps tap targets
and text the same physical size on every tablet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    key: str
    label: str
    slug: str
    width: int   # portrait, px
    height: int  # portrait, px
    ppi: int
    compact: bool = False
    grayscale_only: bool = False


DEVICES: dict[str, Device] = {
    "remarkable_pro": Device("remarkable_pro", "reMarkable Paper Pro", "reMarkable-Paper-Pro",
                             1620, 2160, 229),
    "remarkable_move": Device("remarkable_move", "reMarkable Paper Pro Move", "reMarkable-Move",
                              954, 1696, 264, compact=True),
    "kindle_scribe": Device("kindle_scribe", "Kindle Scribe", "Kindle-Scribe",
                            1860, 2480, 300, grayscale_only=True),
}

ORIENTATIONS = ("portrait", "landscape")
WEEK_STARTS = ("mon", "sun")
HANDS = ("right", "left")
COLOR_MODES = ("eink_color", "bw")
DAILY_STYLES = ("minimal", "adhd")


@dataclass(frozen=True)
class Options:
    device: Device
    orientation: str = "portrait"
    week_start: str = "mon"
    handedness: str = "right"
    color_mode: str = "eink_color"
    daily_style: str = "minimal"

    def __post_init__(self):
        for value, allowed in ((self.orientation, ORIENTATIONS), (self.week_start, WEEK_STARTS),
                               (self.handedness, HANDS), (self.color_mode, COLOR_MODES),
                               (self.daily_style, DAILY_STYLES)):
            if value not in allowed:
                raise ValueError(f"{value!r} is not one of {allowed}")

    @property
    def landscape(self) -> bool:
        return self.orientation == "landscape"

    @property
    def page_size(self) -> tuple[int, int]:
        w, h = self.device.width, self.device.height
        return (h, w) if self.landscape else (w, h)

    @property
    def first_weekday(self) -> int:
        """Python weekday() of the first column: 0 = Monday, 6 = Sunday."""
        return 0 if self.week_start == "mon" else 6

    @property
    def effective_color_mode(self) -> str:
        """Kindle Scribe is grayscale-only, so it always gets the high-contrast palette."""
        return "bw" if self.device.grayscale_only else self.color_mode

    @property
    def rail_side(self) -> str:
        """Side tab rail sits opposite the writing hand."""
        return "left" if self.handedness == "right" else "right"

    def file_stem(self) -> str:
        parts = [
            "Planner-2027",
            self.device.slug,
            self.orientation.capitalize(),
            "Mon-Start" if self.week_start == "mon" else "Sun-Start",
            "Right-Hand" if self.handedness == "right" else "Left-Hand",
            "Color" if self.effective_color_mode == "eink_color" else "BW",
            "ADHD" if self.daily_style == "adhd" else "Minimal",
        ]
        return "_".join(parts)


class Metrics:
    """Physical sizes converted to page units for one device/orientation."""

    def __init__(self, opts: Options):
        d = opts.device
        self.ppi = d.ppi
        self.compact = d.compact
        self.landscape = opts.landscape
        self.W, self.H = opts.page_size
        c = d.compact
        # Tap targets: the spec asks for 8-10 mm. 8 mm is a hard floor everywhere; the
        # larger tablets get a roomier preferred size.
        self.tap_min_mm = 8.0
        self.tap_min = self.mm(self.tap_min_mm)
        self.tap = self.mm(8.0 if c else 9.5)
        self.gap = self.mm(1.0 if c else 1.5)
        self.edge = self.mm(1.5 if c else 2.5)       # page edge to nav
        self.gutter = self.mm(2.5 if c else 4.0)     # nav to content
        self.margin = self.mm(3.0 if c else 5.0)     # content to free page edges
        self.space = self.mm(2.5 if c else 4.0)      # between blocks
        self.grid = self.mm(3.2 if c else 3.7)       # Hobonichi-style fine grid
        self.ruled = self.mm(6.0 if c else 7.0)
        self.dot = self.mm(4.5 if c else 5.0)
        self.radius = self.mm(1.0 if c else 1.4)
        # Type sizes in physical points.
        self.fs_display = self.pt(64 if c else 96)
        self.fs_title = self.pt(14 if c else 18)
        self.fs_big = self.pt(20 if c else 26)
        self.fs_h = self.pt(9 if c else 11)
        self.fs_body = self.pt(7.5 if c else 9)
        self.fs_label = self.pt(6.2 if c else 7.2)
        self.fs_small = self.pt(5.6 if c else 6.5)
        self.fs_tab = self.pt(6.4 if c else 8)
        # Line weights in physical points.
        self.lw_grid = self.pt(0.3)
        self.lw_rule = self.pt(0.4)
        self.lw_box = self.pt(0.6)
        self.lw_bold = self.pt(1.2)

    def mm(self, v: float) -> float:
        return v * self.ppi / 25.4

    def pt(self, v: float) -> float:
        return v * self.ppi / 72.0

    def to_mm(self, units: float) -> float:
        return units * 25.4 / self.ppi
