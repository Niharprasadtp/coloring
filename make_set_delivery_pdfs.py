"""One buyer delivery PDF per themed set, each pointing at that set's zip on Google Drive.

    python make_set_delivery_pdfs.py -i input -c output/collection -o output/sets
Writes output/sets/<Set>/Download_<Set name>.pdf, the same 4 pages as make_delivery_pdf.py
(download link + QR, what's inside, how to use, good to know), with the set's own
featured designs, design count and title.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

import make_delivery_pdf as D
from make_listing_images import Collection, cover_crop
from make_sets import SETS

# Each set's zip on Google Drive (shared as "Anyone with the link"). The links give access to paid files,
# so they live in set_links.json (gitignored) as {"Set1_Cozy_Cottage_Winter": "https://drive.google.com/...", ...}.
LINKS = json.loads((Path(__file__).resolve().parent / "set_links.json").read_text())


def build(col, name, cfg, url, out):
    hero = list(cfg["feat"][0]) + list(cfg["feat"][1])  # 6 featured designs, collection numbering
    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for n in hero:
            path = Path(tmp) / f"tile_{n}.jpg"
            cover_crop(col.art(n), 480, 640).save(path, quality=88)
            tiles.append(path)
        c = rl_canvas.Canvas(str(out), pagesize=A4)
        c.setTitle(f"Your {cfg['title'].title()} Paint by Number download")
        c.setAuthor("Paint by Number Collection")
        D.page_link(c, url, tiles, subtitle=f"for your {cfg['title'].title()} Paint by Number Collection")
        c.showPage()
        D.page_inside(c, len(cfg["designs"]))
        c.showPage()
        D.page_howto(c)
        c.showPage()
        D.page_terms(c)
        c.showPage()
        c.save()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-c", "--collection", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path, help="the sets folder")
    a = p.parse_args()
    col = Collection(a.input, a.collection)
    for name, cfg in SETS.items():
        folder = a.output / name
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / f"Download_{name.split('_', 1)[1]}.pdf"
        build(col, name, cfg, LINKS[name], out)
        print(f"{out} ({out.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    sys.exit(main())
