"""Command line interface: single planner or --batch-all variants for one device."""

from __future__ import annotations

import argparse
import itertools
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

from .builder import build
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


def main(argv=None) -> int:
    a = parse_args(argv)
    base = Options(DEVICES[a.device], a.orientation, a.week_start, a.handedness, a.color_mode,
                   a.daily_style)
    out = Path(a.output)
    if base.device.grayscale_only and a.color_mode == "eink_color":
        print(f"note: {base.device.label} is grayscale-only; using the high-contrast palette.")

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
    if a.zip:
        for _, path in jobs:
            folder = Path(path).parent
            archive = shutil.make_archive(str(folder), "zip", folder)
            print(f"zipped {archive}")
    print(f"{len(jobs)} variants in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
