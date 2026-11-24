"""Command line interface: single planner or --batch-all variants for one device."""

from __future__ import annotations

import argparse
import itertools
import shutil
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

from .builder import build
from .pages.guide import build_start_here
from .devices import (COLOR_MODES, DAILY_STYLES, DEVICES, HANDS, ORIENTATIONS, WEEK_STARTS,
                      Options)


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="make_planner.py",
        description="Generate a hyperlinked Dec 2026 - Dec 2027 digital planner PDF for E-Ink tablets.")
    p.add_argument("--device", choices=sorted(DEVICES), default="remarkable_pro")
    p.add_argument("--orientation", choices=ORIENTATIONS, default="portrait")
    p.add_argument("--week-start", choices=WEEK_STARTS, default="mon")
    p.add_argument("--handedness", choices=HANDS, default="right",
                   help="writing hand; the month rail goes on the other side")
    p.add_argument("--color-mode", choices=COLOR_MODES, default="eink_color")
    p.add_argument("--daily-style", choices=DAILY_STYLES, default="minimal")
    p.add_argument("--batch-all", action="store_true",
                   help="build every week-start x handedness x color combination for --device")
    p.add_argument("--zip", action="store_true", help="with --batch-all, also zip each variant folder")
    p.add_argument("--etsy", action="store_true",
                   help="build the complete Etsy download set for --device: every orientation x "
                        "daily style x variant, packed into at most 5 files under 20 MB")
    p.add_argument("-o", "--output", default="output", help="output folder (default: output)")
    p.add_argument("-j", "--jobs", type=int, default=0,
                   help="parallel builds in batch mode (default: CPU count)")
    return p.parse_args(argv)


def _variant_dir(o: Options) -> str:
    return "_".join([
        "Mon-Start" if o.week_start == "mon" else "Sun-Start",
        "Right-Hand" if o.handedness == "right" else "Left-Hand",
        "Color" if o.effective_color_mode == "eink_color" else "BW",
    ])


def _build_one(args: tuple[Options, str]) -> dict:
    opts, path = args
    t0 = time.time()
    info = build(opts, path)
    info["seconds"] = time.time() - t0
    return info


def batch_variants(base: Options) -> list[Options]:
    colors = ["bw"] if base.device.grayscale_only else list(COLOR_MODES)
    return [replace(base, week_start=ws, handedness=h, color_mode=c)
            for ws, h, c in itertools.product(WEEK_STARTS, HANDS, colors)]


ETSY_MAX_FILES = 5
ETSY_MAX_BYTES = 20 * 1024 * 1024


def _style_name(o: Options) -> str:
    return "ADHD" if o.daily_style == "adhd" else "Minimal"


def etsy_package(base: Options, out: Path, workers: int | None) -> int:
    """Every variant for one device, as Etsy's 5 downloadable files.

    One zip per orientation x daily style (8 planners each, 4 on grayscale-only
    devices) plus START-HERE.pdf. Fails loudly if a file breaks Etsy's limits.
    """
    root = out / f"Etsy_{base.device.slug}"
    build_dir = root / "_build"
    groups: dict[str, list[tuple[Options, str]]] = {}
    for orient, style in itertools.product(ORIENTATIONS, DAILY_STYLES):
        g = replace(base, orientation=orient, daily_style=style)
        name = f"Planner-2027_{base.device.slug}_{orient.capitalize()}_{_style_name(g)}"
        groups[name] = [(o, str(build_dir / name / f"{o.file_stem()}.pdf"))
                        for o in batch_variants(g)]
    jobs = [j for js in groups.values() for j in js]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for info in pool.map(_build_one, jobs):
            print(f"wrote {Path(info['path']).name}  ({info['pages']} pages, {info['links']} links)")
    files = [Path(build_start_here(base, root / "START-HERE.pdf"))]
    for name, js in groups.items():
        archive = root / f"{name}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for _, path in js:
                z.write(path, Path(path).name)
        files.append(archive)
    shutil.rmtree(build_dir)
    ok = len(files) <= ETSY_MAX_FILES
    for f in files:
        size = f.stat().st_size
        flag = "" if size <= ETSY_MAX_BYTES else "  <-- over Etsy's 20 MB limit"
        ok &= size <= ETSY_MAX_BYTES
        print(f"  {f.name:70s} {size / 1e6:6.1f} MB{flag}")
    print(f"{len(jobs)} planners in {len(files)} files -> {root}")
    if not ok:
        print("error: the download set does not fit Etsy's limits", file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    a = parse_args(argv)
    base = Options(DEVICES[a.device], a.orientation, a.week_start, a.handedness, a.color_mode,
                   a.daily_style)
    out = Path(a.output)
    if base.device.grayscale_only and a.color_mode == "eink_color":
        print(f"note: {base.device.label} is grayscale-only; using the high-contrast palette.")

    if a.etsy:
        return etsy_package(base, out, a.jobs or None)

    if not a.batch_all:
        info = _build_one((base, str(out / f"{base.file_stem()}.pdf")))
        print(f"wrote {info['path']}  ({info['pages']} pages, {info['links']} links, "
              f"{info['seconds']:.1f}s)")
        return 0

    root = out / f"{base.device.slug}_{base.orientation.capitalize()}_" \
                 f"{'ADHD' if base.daily_style == 'adhd' else 'Minimal'}"
    jobs = []
    for o in batch_variants(base):
        folder = root / _variant_dir(o)
        jobs.append((o, str(folder / f"{o.file_stem()}.pdf")))
    workers = a.jobs or None
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for info in pool.map(_build_one, jobs):
            print(f"wrote {info['path']}  ({info['pages']} pages, {info['links']} links, "
                  f"{info['seconds']:.1f}s)")
    build_start_here(base, root / "START-HERE.pdf")
    if a.zip:
        for _, path in jobs:
            folder = Path(path).parent
            archive = shutil.make_archive(str(folder), "zip", folder)
            print(f"zipped {archive}")
    print(f"{len(jobs)} variants in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
