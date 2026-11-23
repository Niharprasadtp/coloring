"""Color palettes tuned for E-Ink: muted accents on paper white, or pure grayscale."""

from __future__ import annotations

from dataclasses import dataclass

from reportlab.lib.colors import Color, HexColor, white


@dataclass(frozen=True)
class Theme:
    name: str
    ink: Color          # primary text
    soft: Color         # secondary text
    muted: Color        # section labels, hour labels
    faint: Color        # out-of-month / out-of-range numbers
    grid: Color         # fine grid and dot lines
    rule: Color         # ruled lines, light borders
    tab: Color          # inactive tab fill
    tab_text: Color
    active: Color       # active non-month tab
    active_text: Color
    accent: Color       # section label bars, highlights
    weekend: Color
    quarter: tuple      # accent per quarter, index 1..4 (0 unused)
    tint: tuple         # light fill per quarter, index 1..4
    paper: Color = white

    def q(self, quarter: int) -> Color:
        return self.quarter[quarter]

    def qt(self, quarter: int) -> Color:
        return self.tint[quarter]


_SAGE, _SLATE, _TERRA, _WARM = (HexColor(c) for c in ("#7A9A80", "#5D7086", "#B5715A", "#958E83"))

EINK_COLOR = Theme(
    name="eink_color",
    ink=HexColor("#262626"),
    soft=HexColor("#474644"),
    muted=HexColor("#7A756D"),
    faint=HexColor("#BDB8B0"),
    grid=HexColor("#D2CFC9"),
    rule=HexColor("#B6B1A8"),
    tab=HexColor("#F0EEEA"),
    tab_text=HexColor("#474644"),
    active=_SLATE,
    active_text=white,
    accent=_SAGE,
    weekend=_TERRA,
    quarter=(None, _SAGE, _SLATE, _TERRA, _WARM),
    tint=(None, HexColor("#E6EDE7"), HexColor("#E2E7EE"), HexColor("#F3E5DE"), HexColor("#EEEBE6")),
)

BW = Theme(
    name="bw",
    ink=HexColor("#000000"),
    soft=HexColor("#2E2E2E"),
    muted=HexColor("#4D4D4D"),
    faint=HexColor("#A6A6A6"),
    grid=HexColor("#BDBDBD"),
    rule=HexColor("#8A8A8A"),
    tab=HexColor("#EBEBEB"),
    tab_text=HexColor("#1A1A1A"),
    active=HexColor("#000000"),
    active_text=white,
    accent=HexColor("#000000"),
    weekend=HexColor("#000000"),
    quarter=(None,) + (HexColor("#2E2E2E"),) * 4,
    tint=(None,) + (HexColor("#E8E8E8"),) * 4,
)


def theme_for(mode: str) -> Theme:
    return EINK_COLOR if mode == "eink_color" else BW
