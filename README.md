# Color by Number Book Generator

Turns a folder of flat-color images into print-ready color-by-number PDF books
in three sizes: US Letter, A4 and 16x20 in.

Each book contains one numbered line-art template per image (with a color strip
and reference thumbnail at the bottom of every page), a blank back after each
template so markers don't bleed through, full-color reference pages, and a
master color key.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Put images in `input/`, then:

```bash
python colorbynumber.py -i input -o output --title "Tuscan Sunset" --difficulty expert
```

Output in `output/`:

- `<title>_letter.pdf`, `<title>_a4.pdf`, `<title>_16x20.pdf`
- `previews/`: line-art and colored PNGs for a quick visual check
- `report.txt`: region and color counts, quality warnings, and the palette

Main options (`python colorbynumber.py -h` for all):

| Option | Purpose |
|---|---|
| `--difficulty relaxing\|intermediate\|expert` | Number of colors and smallest region size |
| `-k N` | Override the number of colors |
| `--details outline\|color\|off` | Shapes too small to number: outlined (default), printed in color, or merged away |
| `--sizes letter a4 16x20` | Which PDFs to build |
| `--auto-rotate` | Turn landscape images sideways to fill portrait pages |
| `--no-blank-backs` | Skip the blank page after each template |
| `--skip-poor` | Leave images flagged by the quality check out of the books |

All images in one run share a single palette, so the whole book uses one set of
numbered colors. The 16x20 PDF keeps more detail than Letter and A4 because
there is room to number smaller shapes.

## How it works

1. Light edge-preserving smoothing, then K-Means in CIELAB for a shared palette,
   plus a second pass that adds small but distinct colors (eyes, markings).
2. Regions too small or thin to hold a number are merged into their neighbors;
   small high-contrast details are kept as unnumbered shapes.
3. Smooth vector outlines are traced from the label map.
4. Each region's number goes at its centroid (image moments, checked with
   `cv2.pointPolygonTest`) or, if that point is unsuitable, at its widest point.
   Large regions get repeated numbers.
5. ReportLab draws everything as vectors, scaled uniformly to fit each page.

## Tests

```bash
python -m pytest
```

## Etsy fulfillment

The automated Etsy order pipeline (webhook, buyer upload page, PDF delivery)
lives in `backend/` and `frontend/`. See [FULFILLMENT.md](FULFILLMENT.md).
