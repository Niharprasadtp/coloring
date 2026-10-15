"""Command-line entry point: images in, color-by-number PDF books out."""

import argparse
import logging
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from . import preview, quantize, regions
from .layout import DIFFICULTIES, MM2_PER_PT2, PAGE_SPECS, detail_groups
from .pdf import BookPage, build_pdf

log = logging.getLogger("cbn")

SAMPLES_PER_IMAGE = 40_000
MAX_SAMPLES = 400_000
# Quality thresholds for flagging source images that will convert poorly.
MAX_MEAN_DELTA_E = 10.0
MAX_CHANGED_FRACTION = 0.20
MIN_REGIONS = 15
# Small-detail rescue: colors the palette misses by more than this delta E
# get a second clustering pass; details must print at least this big.
RESIDUAL_DELTA = 15.0
RESIDUAL_PER_IMAGE = 30_000
DETAIL_MIN_AREA_MM2 = 0.2
DETAIL_MAX_AREA_MM2 = 4.5
DETAIL_MIN_RADIUS_PT = 0.5


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="colorbynumber",
        description="Turn a folder of flat-color images into print-ready color-by-number PDF books.")
    p.add_argument("-i", "--input", required=True, type=Path, help="folder of source images")
    p.add_argument("-o", "--output", required=True, type=Path, help="folder for PDFs, previews and report")
    p.add_argument("-k", "--colors", type=int,
                   help="number of colors before near-duplicates are merged (default: from --difficulty)")
    p.add_argument("--difficulty", choices=DIFFICULTIES, default="intermediate",
                   help="preset for colors, smallest region and numbers per region (default: intermediate)")
    p.add_argument("--min-area", type=float, metavar="MM2",
                   help="smallest region in mm^2 as printed on the smallest page (default: from --difficulty)")
    p.add_argument("--sizes", nargs="+", choices=PAGE_SPECS, default=list(PAGE_SPECS),
                   help="page sizes to build (default: all)")
    p.add_argument("--title", default="Color by Number", help="book title, used in footers and file names")
    p.add_argument("--merge-delta", type=float, default=8.0,
                   help="merge palette colors closer than this CIELAB delta E (0 disables, default: 8)")
    p.add_argument("--auto-rotate", action="store_true",
                   help="turn landscape images sideways when that fills a portrait page better")
    p.add_argument("--no-blank-backs", action="store_true",
                   help="do not insert a blank page after each template")
    p.add_argument("--details", choices=("outline", "color", "off"), default="outline",
                   help="small shapes too small to number (eyes, teeth, markings): print them already "
                        "colored, print them as outlines to color from the reference page, or merge "
                        "them away (default: outline)")
    p.add_argument("--skip-poor", action="store_true",
                   help="leave images flagged by the quality check out of the PDFs")
    p.add_argument("--work-size", type=int, default=2000,
                   help="long side in pixels used for processing (default: 2000)")
    p.add_argument("--seed", type=int, default=0, help="random seed for K-Means sampling")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "book"


def find_images(folder):
    return sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix.lower() in quantize.IMAGE_EXTS)


def quality_flags(mean_de, changed, n_regions, max_regions):
    flags = []
    if mean_de > MAX_MEAN_DELTA_E:
        flags.append(f"strong gradients or shading (mean color error {mean_de:.1f}); may look blotchy")
    if changed > MAX_CHANGED_FRACTION:
        flags.append(f"{changed:.0%} of the image was fine detail too small to number")
    if n_regions > max_regions:
        flags.append(f"{n_regions} regions is very busy for this difficulty")
    if n_regions < MIN_REGIONS:
        flags.append(f"only {n_regions} regions; may be too simple")
    return flags


def run(args):
    images = find_images(args.input)
    if not images:
        log.error("no images found in %s", args.input)
        return 1
    preset = DIFFICULTIES[args.difficulty]
    k = args.colors or preset.colors
    min_area_mm2 = args.min_area if args.min_area is not None else preset.min_area_mm2
    specs = [PAGE_SPECS[s] for s in args.sizes]
    preview_dir = args.output / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    # Pass 1: load and smooth everything, pool pixels for one shared palette.
    log.info("Loading %d image(s)", len(images))
    loaded, samples = [], []
    per_image = max(2_000, min(SAMPLES_PER_IMAGE, MAX_SAMPLES // len(images)))
    for path in images:
        try:
            rgb = quantize.smooth(quantize.load_image(path, args.work_size))
        except Exception as exc:
            log.warning("skipping %s: %s", path.name, exc)
            continue
        loaded.append((path, rgb))
        samples.append(quantize.sample_pixels(quantize.to_lab(rgb), per_image, rng))
    if not loaded:
        log.error("none of the images could be read")
        return 1

    palette_lab = quantize.fit_palette(np.concatenate(samples), k, args.merge_delta, args.seed)
    base_colors = len(palette_lab)

    # Second pass for small, distinct colors (eyes, markings) K-Means skipped.
    residual = []
    for _, rgb in loaded:
        lab = quantize.to_lab(rgb)
        _, err = quantize.assign(lab, palette_lab)
        missed = cv2.erode((err > RESIDUAL_DELTA).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        residual.append(quantize.sample_pixels(lab[missed], RESIDUAL_PER_IMAGE, rng))
    palette_lab = quantize.add_detail_colors(palette_lab, np.concatenate(residual), min_pixels=40,
                                             min_delta=max(args.merge_delta, 12.0), seed=args.seed)
    palette_rgb = quantize.lab_to_rgb(palette_lab)
    log.info("Shared palette: %d colors (%d from K-Means with k=%d, %d added for small details)",
             len(palette_lab), base_colors, k, len(palette_lab) - base_colors)

    # Pass 2: per-image regions, outlines and numbers, once for each level of
    # detail (page sizes that print the image at about the same scale).
    pages = {spec.key: [] for spec in specs}
    report = []
    for path, rgb in loaded:
        h, w = rgb.shape[:2]
        try:
            base_labels, err = quantize.assign(quantize.to_lab(rgb), palette_lab)
        except Exception as exc:
            log.warning("skipping %s: %s", path.name, exc)
            continue
        mean_de = float(err.mean())
        groups = detail_groups(specs, w, h, args.auto_rotate)
        # Which specks count as details is a property of the picture, not the
        # page: measure the size cap on the smallest page so every PDF keeps
        # the same eyes and markings.
        detail_max_px = DETAIL_MAX_AREA_MM2 / MM2_PER_PT2 / groups[0][0] ** 2
        for scale, group in groups:
            t0 = time.time()
            sizes = "+".join(s.key for s in group)
            try:
                labels, region_ids, n, dist, changed, detail_map = regions.cleanup(
                    base_labels, palette_lab,
                    min_area_mm2 / MM2_PER_PT2 / scale ** 2, preset.min_radius_pt / scale,
                    DETAIL_MIN_AREA_MM2 / MM2_PER_PT2 / scale ** 2, detail_max_px,
                    max(2.0, DETAIL_MIN_RADIUS_PT / scale),
                    detail_delta=np.inf if args.details == "off" else 25.0)
                markers = regions.place_numbers(labels, region_ids, n, dist, preset.number_spacing_pt / scale)
                outlines = regions.trace_outlines(labels)
                details = [(palette_rgb[c], polys) for c, polys in regions.trace_details(detail_map)]
            except Exception as exc:
                log.warning("skipping %s (%s): %s", path.name, sizes, exc)
                continue

            reference = palette_rgb[labels]
            reference[detail_map >= 0] = palette_rgb[detail_map[detail_map >= 0]]
            used = sorted(int(c) for c in np.unique(labels))
            flags = quality_flags(mean_de, changed, n, preset.max_regions)
            report.append((f"{path.name} [{sizes}]", n, len(markers), len(used), mean_de, changed,
                           sum(len(p) for _, p in details), flags))
            stem = f"{path.stem}_{group[0].key}"
            preview.save_png(preview_dir / f"{stem}_lineart.png",
                             preview.render_lineart(labels.shape, outlines, markers, details, args.details))
            preview.save_png(preview_dir / f"{stem}_colored.png", reference)
            log.info("%-30s %-10s %5d regions  %4d details  %2d colors  %.1fs  %s", path.name, sizes, n,
                     sum(len(p) for _, p in details), len(used), time.time() - t0, "FLAGGED" if flags else "ok")
            for f in flags:
                log.info("    - %s", f)
            if flags and args.skip_poor:
                continue
            for spec in group:
                pages[spec.key].append(BookPage(name=path.stem, width=w, height=h, outlines=outlines,
                                                markers=markers, used=list(used), reference=reference,
                                                details=details, detail_style=args.details))

    if not any(pages.values()):
        log.error("no pages to build")
        return 1
    palette_rgb = prune_palette([p for book in pages.values() for p in book], palette_rgb)
    log.info("Colors used in the book: %d", len(palette_rgb))

    slug = slugify(args.title)
    for spec in specs:
        if not pages[spec.key]:
            continue
        out = args.output / f"{slug}_{spec.key}.pdf"
        build_pdf(out, spec, pages[spec.key], palette_rgb, args.title,
                  auto_rotate=args.auto_rotate, blank_backs=not args.no_blank_backs)
        log.info("Wrote %s (%.1f MB)", out, out.stat().st_size / 1e6)

    write_report(args.output / "report.txt", args, report, palette_rgb)
    return 0


def prune_palette(pages, palette):
    """Drop colors no page uses (lost in cleanup) and renumber the rest without gaps."""
    keep = sorted({c for page in pages for c in page.used})
    new_index = {old: new for new, old in enumerate(keep)}
    remapped = set()  # page sizes at the same detail level share one marker list
    for page in pages:
        page.used = [new_index[c] for c in page.used]
        if id(page.markers) in remapped:
            continue
        remapped.add(id(page.markers))
        for m in page.markers:
            m.color = new_index[m.color]
    return palette[keep]


def write_report(path, args, rows, palette):
    lines = [f"Title: {args.title}", f"Difficulty: {args.difficulty}", f"Palette: {len(palette)} colors", ""]
    for name, n, numbers, used, de, changed, details, flags in rows:
        lines.append(f"{name}: {n} regions, {numbers} numbers, {used} colors, {details} pre-printed details, "
                     f"mean color error {de:.1f}, detail merged {changed:.0%}")
        lines += [f"    FLAG: {f}" for f in flags]
    lines += ["", "Palette:"]
    lines += [f"  {i + 1:>2}  #{r:02X}{g:02X}{b:02X}  RGB {r}, {g}, {b}" for i, (r, g, b) in enumerate(palette)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    if not args.input.is_dir():
        log.error("input folder not found: %s", args.input)
        return 1
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
