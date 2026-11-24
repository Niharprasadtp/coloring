"""Render every design side by side (to check the drawings by eye)."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import designs as D

CELL = 14
names = sys.argv[1:] or list(D.DESIGNS)
tiles = []
for n in names:
    d = D.DESIGNS[n]
    D.check(d)
    rows = D.expand(d)
    im = Image.new("RGB", (len(rows[0]) * CELL, len(rows) * CELL))
    dr = ImageDraw.Draw(im)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            dr.rectangle([x * CELL, y * CELL, x * CELL + CELL - 1, y * CELL + CELL - 1], fill="#" + d["colors"][c])
    tiles.append(im)
cols = 5
tw = max(t.width for t in tiles) + 20
th = max(t.height for t in tiles) + 20
sheet = Image.new("RGB", (tw * cols, th * ((len(tiles) + cols - 1) // cols)), "white")
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * tw + 10, (i // cols) * th + 10))
out = Path(__file__).parent / "output" / "designs_contact_sheet.png"
out.parent.mkdir(exist_ok=True)
sheet.save(out)
print(out)
