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
    family: str  # "remarkable" | "kindle" | "supernote": install steps and quirks
    compact: bool = False
    grayscale_only: bool = False
    # Height kept free at the top of the month rail. reMarkable draws its round
    # toolbar button in the top corner on the side away from the writing hand,
    # which is the rail's side, so a tab there would sit under the button.
    toolbar_corner_mm: float = 0.0


_RM_CORNER = 14.0

DEVICES: dict[str, Device] = {
    "remarkable_pro": Device("remarkable_pro", "reMarkable Paper Pro", "reMarkable-Paper-Pro",
                             1620, 2160, 229, "remarkable", toolbar_corner_mm=_RM_CORNER),
    "remarkable_move": Device("remarkable_move", "reMarkable Paper Pro Move", "reMarkable-Move",
                              954, 1696, 264, "remarkable", compact=True,
                              toolbar_corner_mm=_RM_CORNER),
    "remarkable_2": Device("remarkable_2", "reMarkable 2", "reMarkable-2",
                           1404, 1872, 226, "remarkable", grayscale_only=True,
                           toolbar_corner_mm=_RM_CORNER),
    "kindle_scribe": Device("kindle_scribe", "Kindle Scribe (11-inch, 2025)", "Kindle-Scribe-11in",
                            1980, 2640, 300, "kindle", grayscale_only=True),
    "kindle_scribe_colorsoft": Device("kindle_scribe_colorsoft", "Kindle Scribe Colorsoft",
                                      "Kindle-Scribe-Colorsoft", 1980, 2640, 300, "kindle"),
    "kindle_scribe_10": Device("kindle_scribe_10", "Kindle Scribe (10.2-inch, 2022/2024)",
                               "Kindle-Scribe-10in", 1860, 2480, 300, "kindle",
                               grayscale_only=True),
    "supernote_manta": Device("supernote_manta", "Supernote Manta", "Supernote-Manta",
                              1920, 2560, 300, "supernote", grayscale_only=True),
    "supernote_nomad": Device("supernote_nomad", "Supernote Nomad", "Supernote-Nomad",
                              1404, 1872, 300, "supernote", compact=True, grayscale_only=True),
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
        """Grayscale-only screens always get the high-contrast palette."""
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
        # Taps right at the screen edge are unreliable on some tablets, so the nav
        # keeps a few millimetres clear of it.
        self.edge = self.mm(2.5 if c else 3.0)       # page edge to nav
        self.toolbar_corner = self.mm(d.toolbar_corner_mm)
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
