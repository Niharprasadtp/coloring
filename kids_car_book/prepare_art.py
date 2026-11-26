"""One-time art prep for the personalized kids car coloring book.

Reads (never edits) the user's existing art:
  * the 100-car line-art PDF (pages extracted to art_src/ earlier), and
  * the beginner color-by-number builds in ../output/books_build/cars/0[1-5]_*.
Writes cleaned, print-ready files to art/ plus art/manifest.json.

    ../.venv/Scripts/python.exe prepare_art.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE / "art_src"
CBN_SRC = HERE.parent / "output" / "books_build" / "cars"
OUT = HERE / "art"

# Hand-picked from the 100 pages. Left out: every page with a brand name drawn in as a title
# (39 45 49 52-55 59 85 87 89 99) and every page with a readable logo / trademark text
# (9 16 36 56 60 65 66 73 74 83 86 88 100) -- IP takedown risk.
SECTIONS = [
    ("MONSTER TRUCKS & OFF-ROAD", [8, 3, 12, 22, 18, 31, 38, 43, 62, 95, 19, 70, 82]),
    ("RACE CARS", [5, 17, 4, 6, 35, 47, 71, 20]),
    ("SUPERCARS", [1, 14, 23, 29, 33, 40, 44, 48, 50, 51, 92, 37, 63]),
    ("MUSCLE CARS & CLASSICS", [15, 13, 2, 21, 81, 26, 34, 42, 93]),
    ("STREET & TUNER CARS", [11, 24, 28, 32, 76, 80, 94]),
]
CBN = ["01_split_window_camper_van", "02_classic_bubble_car", "03_little_london_city_car",
       "04_1950s_christmas_pickup", "05_safari_offroader"]


def levels(a: np.ndarray, black: float, white: float) -> np.ndarray:
    """Map <=black to 0 and >=white to 255: kills JPEG grey noise, keeps anti-aliased edges."""
    return (np.clip((a.astype(float) - black) / (white - black), 0, 1) * 255).astype("uint8")


def content_box(a: np.ndarray, thresh: int = 200, pad: int = 8) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(a < thresh)
    h, w = a.shape
    return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + pad + 1), min(h, ys.max() + pad + 1))


def palette(report: Path) -> list[str]:
    cols = re.findall(r"^\s*(\d+)\s+(#[0-9A-Fa-f]{6})", report.read_text(encoding="utf-8"), re.M)
    return [hexv for _, hexv in sorted(cols, key=lambda t: int(t[0]))]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    pages = []
    for section, nums in SECTIONS:
        for n in nums:
            a = np.asarray(Image.open(SRC / f"{n:03d}.jpeg").convert("L"))
            clean = levels(a, 90, 225)
            l, t, r, b = content_box(clean)
            name = f"car_{n:03d}.png"
            Image.fromarray(clean[t:b, l:r]).save(OUT / name, optimize=True)
            pages.append({"file": name, "section": section, "src_page": n})

    cbn = []
    for folder in CBN:
        d = CBN_SRC / folder
        im = Image.open(d / "PNG" / "Dark_Numbered.png").convert("L")
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)          # 600 -> 300 dpi
        a = levels(np.asarray(im), 40, 235)
        l, t, r, b = content_box(a, thresh=230, pad=12)
        name = f"cbn_{folder[:2]}.png"
        Image.fromarray(a[t:b, l:r]).save(OUT / name, optimize=True)
        prev = Image.open(d / "preview_colored.png").convert("RGB")
        prev.thumbnail((600, 600))
        prev.save(OUT / f"cbn_{folder[:2]}_preview.jpg", quality=88)
        cbn.append({"file": name, "preview": f"cbn_{folder[:2]}_preview.jpg", "palette": palette(d / "report.txt")})

    manifest = {"pages": pages, "cbn": cbn}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    size = sum(p.stat().st_size for p in OUT.iterdir()) / 1e6
    print(f"{len(pages)} coloring pages + {len(cbn)} color-by-number pages -> {OUT} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
