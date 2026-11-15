"""Coloring time-lapse listing video for each 15-design set (uses the cover's hero design).

    python make_set_videos.py
"""

import sys
from pathlib import Path

import make_sets  # noqa: F401  (adds the design names, e.g. "Reading Nook", to the shared NAMES table)
from make_coloring_video import build
from make_listing_images import Collection

HEROES = {"Set1_Cozy_Cottage_Winter": 26, "Set2_Wildlife_Scenic_Nature": 1, "Set3_Sunsets_Travel": 29}


def main():
    col = Collection(Path("input"), Path("output/collection"))
    only = sys.argv[1:]
    for name, hero in HEROES.items():
        if only and not any(o in name for o in only):
            continue
        build(col, hero, Path("output/sets") / name / "listing_video", pages=15,
              out_name="paint_by_number_coloring_video.mp4")


if __name__ == "__main__":
    sys.exit(main())
