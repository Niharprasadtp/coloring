"""Split the 46-design collection into three themed sets of 15 and build their listing photos.

    python make_sets.py -i input -c output/collection -o output/sets --inputs input_sets
Left out on purpose: design 33 (the only low-resolution image, upscaled from 896x1200).
"""

import argparse
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import make_listing_images as L
from make_listing_images import (CORAL, H, INK, MUSTARD, PLUM, TEAL, W, background, banner, cover_crop, font,
                                 shadowed, starburst, tag_zones, text_c, text_l)

SETS = {
    "Set1_Cozy_Cottage_Winter": dict(
        title="COZY COTTAGE", tag="Cozy  •  Seasonal  •  Homey", sub="Reading nooks, greenhouses, winter villages",
        designs=[5, 7, 19, 20, 23, 24, 25, 26, 27, 28, 32, 36, 38, 44, 45],
        feat=([25, 26, 45], [28, 24, 19]), ipad=26, styles=28),
    "Set2_Wildlife_Scenic_Nature": dict(
        title="WILDLIFE & NATURE", tag="Animals  •  Florals  •  Wild", sub="Foxes, owls, wolves, flowers and wild landscapes",
        designs=[1, 2, 3, 6, 8, 21, 22, 34, 35, 37, 39, 40, 41, 42, 46],
        feat=([1, 8, 46], [37, 40, 6]), ipad=8, styles=1),
    "Set3_Sunsets_Travel": dict(
        title="SUNSETS & TRAVEL", tag="Sunsets  •  Coasts  •  Cities", sub="Pixel-art sunsets and sun-drenched getaways",
        designs=[4, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 29, 30, 31, 43],
        feat=([31, 30, 43], [11, 13, 15]), ipad=11, styles=31),
}

NAMES = {5: "Antique Desk", 7: "Glass Greenhouse", 19: "Christmas Fireplace", 20: "Cat in the Garden Window",
         23: "Witch's Apothecary", 24: "Winter Village", 25: "Gingerbread Land", 26: "Reading Nook",
         27: "Autumn Cottage", 28: "Garden Greenhouse", 32: "Snowy Christmas Cabin", 36: "Tea by the Window",
         38: "Cat & Herbs", 44: "Fruit & Copper Kettle", 45: "Old Library",
         1: "Red Fox in Snow", 2: "Fishing Harbor", 3: "Stone Bridge", 6: "Highland Cattle", 8: "Barn Owl",
         21: "Koi Pond", 22: "Roses & Robin", 34: "Fox & Mushroom", 35: "Hummingbird", 37: "Alpine Lake Cabin",
         39: "Horses at Dawn", 40: "Wild Butterflies", 41: "Stormy Lighthouse", 42: "Bamboo Path", 46: "Grey Wolf",
         4: "Flower Market", 9: "Forest Sunset", 10: "Desert Sunset", 11: "Northern Lights", 12: "Cherry Blossom Pagoda",
         13: "Lighthouse Moon", 14: "Jungle Waterfall", 15: "Meadow Fox", 16: "Camping Night", 17: "Safari Sunset",
         18: "Shooting Stars", 29: "Amalfi Coast", 30: "Paris Cafe", 31: "Greek Alley & Cat", 43: "Tuscan Vineyard"}
L.NAMES.update(NAMES)


def cover(col, ns, c, out):
    img = background(1)
    cw, ch, gap, cols = 555, 740, 34, 3
    x0 = W - 90 - (cols * cw + (cols - 1) * gap)
    text_c(img, c["title"] + " COLLECTION", W / 2, 26, font("georgiab", 112), PLUM)
    tiles = col.tiles(ns, (cw, ch))
    for i, n in enumerate(ns):
        r, cc = divmod(i, cols)
        x, y = x0 + cc * (cw + gap), 200 + r * (ch + gap + 14)
        shadowed(img, tiles[n], (x, y), border=12)
        tag_zones(col, img, n, x, y, cw)
    starburst(img, 410, 480, 300, CORAL)
    text_c(img, "15", 410, 330, font("impact", 250), "white")
    text_c(img, "PAGES", 410, 590, font("segoeuib", 100), "white")
    for i, (line, f_, color, size) in enumerate([(c["tag"], "segoeuib", PLUM, 52),
                                                 ("Procreate iPad", "georgiab", CORAL, 78),
                                                 ("+ Printable", "georgiab", CORAL, 78)]):
        text_c(img, line, 410, 880 + i * 105 - (20 if i else 0), font(f_, size), color)
    for i, ln in enumerate(["6 PNG styles per page", "PDF  +  SVG  +  .swatches", "Up to 34 colors each"]):
        text_c(img, ln, 410, 1260 + i * 80, font("segoeui", 48), INK)
    banner(img, "INSTANT DOWNLOAD  •  PNG  PDF  SVG  •  PROCREATE PALETTE INCLUDED", H - 118)
    return L.save_jpg(img, out)


def overview(col, ns, c, out):
    img = background(15)
    text_c(img, f"ALL 15 PAGES: {c['title']}", W / 2, 24, font("georgiab", 100), PLUM)
    cols, rows, cw, ch, gap = 5, 3, 470, 470, 30
    x0 = (W - (cols * cw + (cols - 1) * gap)) // 2
    for i, n in enumerate(ns):
        r, cc = divmod(i, cols)
        x, y = x0 + cc * (cw + gap), 190 + r * (ch + gap + 62)
        shadowed(img, cover_crop(col.art(n), cw, ch), (x, y), border=10)
        text_c(img, NAMES[n], x + cw / 2 + 10, y + ch + 24, font("segoeuib", 38), PLUM)
    banner(img, "15 DESIGNS  •  EACH WITH ITS OWN NUMBERED COLOR PALETTE", H - 118)
    return L.save_jpg(img, out)


def build_listing(col, c, out):
    ns = c["designs"]
    out.mkdir(parents=True, exist_ok=True)
    col.count = 15
    hero = ns[:0] + c["feat"][0] + c["feat"][1]
    plan = {
        "01_cover.jpg": lambda o: cover(col, hero, c, o),
        "02_all_15_pages.jpg": lambda o: overview(col, ns, c, o),
        "03_featured_1.jpg": lambda o: L.featured_image(col, c["feat"][0], c["title"], c["sub"], o, seed=21),
        "04_featured_2.jpg": lambda o: L.featured_image(col, c["feat"][1], c["title"], c["sub"], o, seed=22),
        "05_before_after.jpg": lambda o: L.before_after(col, c["ipad"], o),
        "06_ipad.jpg": lambda o: L.ipad_image(col, c["ipad"], o),
        "07_six_styles.jpg": lambda o: L.styles_image(col, c["styles"], o),
        "08_included.jpg": lambda o: L.included_image(col, c["styles"], o),
        "09_how_it_works.jpg": lambda o: L.howto_image(col, c["styles"], o),
        "10_palette.jpg": lambda o: L.palette_image(col, c["styles"], o),
        "11_good_to_know.jpg": lambda o: L.terms_image(o),
    }
    for name, fn in plan.items():
        fn(out / name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-c", "--collection", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path)
    p.add_argument("--inputs", required=True, type=Path, help="where the three source-image folders go")
    a = p.parse_args()
    col = L.Collection(a.input, a.collection)
    used = sorted(n for c in SETS.values() for n in c["designs"])
    assert len(used) == len(set(used)) == 45 and 33 not in used
    for name, c in SETS.items():
        # 1) the 15 source images
        src = a.inputs / name
        src.mkdir(parents=True, exist_ok=True)
        for i, n in enumerate(c["designs"], 1):
            shutil.copy(col.files[n - 1], src / f"{i:02d}_{NAMES[n].replace(' ', '_').replace('&', 'and')}.png")
        # 2) the built files, renumbered 01..15
        pack = a.output / name / "Files"
        for i, n in enumerate(c["designs"], 1):
            d = pack / f"Design_{i:02d}"
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(a.collection / f"Design_{n:02d}", d, ignore=shutil.ignore_patterns(
                "report.txt", "preview_colored.png"))
            old = d / "PDF" / f"Design_{n:02d}_A4.pdf"
            old.rename(d / "PDF" / f"Design_{i:02d}_A4.pdf")
        # 3) listing photos
        build_listing(col, c, a.output / name / "listing")
        print(name, "done")


if __name__ == "__main__":
    sys.exit(main())
