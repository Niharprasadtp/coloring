# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Python color-by-number generator (`cbn/`). It turns a folder of flat-color images (up to about 50 per run) into print-ready PDF books in Letter, A4 and 16x20 sizes. The entry point is `colorbynumber.py`, which calls `cbn.cli.main`.

This `standalone-generator` branch has no Etsy fulfillment pipeline. That code is on `main`, in `backend/` and `frontend/`.

## Commands

Dependencies live only in `.venv`. System `python3` lacks them, and plain `python` isn't installed outside the venv.
```bash
source .venv/bin/activate
pip install -r requirements.txt
python colorbynumber.py -i input -o output --title "Name" --difficulty expert   # -h for all options
python -m pytest                                         # all tests
python -m pytest tests/test_pipeline.py::test_end_to_end # single test
```

## Architecture

`cli.run` drives two passes:
- **Pass 1, shared palette:** every image is loaded and smoothed (`quantize`). Pixels are pooled across all images and clustered with K-Means in CIELAB, so one palette covers the whole book. A residual pass then adds small, distinct colors that K-Means missed, such as eyes and markings. Per-image sample counts shrink as the image count grows (`MAX_SAMPLES`, `MAX_RESIDUAL`).
- **Pass 2, per image and per "detail group":** `layout.detail_groups` groups page sizes that print the image at about the same scale. For each group, `regions.cleanup` merges regions too small or thin to number and keeps high-contrast specks as unnumbered "details". Then `place_numbers` and `trace_outlines` run. `pdf.build_pdf` (ReportLab, all vectors) and `preview` produce the output.

The pipeline works in physical units: thresholds are given in mm² or pt and converted to pixels with the group's scale (`MM2_PER_PT2`, `scale`). The 16x20 book therefore keeps more detail than Letter/A4. Detail size caps are measured on the *smallest* page so every PDF keeps the same details. All geometry is in image pixel coordinates (top-left origin); `layout.Placement` maps it onto PDF coordinates (bottom-left origin) with one uniform scale.

Every page is held in memory until the PDFs are written. To keep large batches within RAM, each full-size image is freed after pass 2, and `BookPage.reference` is stored downscaled to `REFERENCE_MAX_SIDE`, the largest size the PDF ever draws it. Keep that invariant when adding per-page data.

The PDFs deliberately show no source file names. The footer shows only the book title and page number.
