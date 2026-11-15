"""Paint-by-number books from output/books_build: printable PDF, color guide, Procreate kit, photos, listing text.

    .venv/Scripts/python make_books.py build  [product ...]   # local files only (default: every product)
    .venv/Scripts/python make_books.py upload [product ...]   # create Etsy DRAFT listings

Every product is delivered directly by Etsy: at most 5 files, each under 20 MB. Pages are sorted by zone count
(easiest first). Output: output/books/<product>/ (files/, photos/, listing.json).
"""

import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

import make_combined_pdf as CP
import make_listing_images as L
from build_collection import clean_image
from make_listing_images import (CORAL, INK, MUSTARD, PLUM, TEAL, H, W, background, banner, cover_crop, font,
                                 shadowed, starburst, tag_zones, text_c, text_l)

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent
BUILT = ROOT / "output" / "books_build"
SRC = ROOT / "input_books"
OUT = ROOT / "output" / "books"
MAX_FILE = 19_500_000
SECTION_PBN = 61351078
CHRISTMAS_SECTION = "Christmas & Winter"
CORE_TAGS = ["paint by number", "color by number", "procreate coloring", "adult coloring book"]


def nums(folder, *ranges):
    return [(folder, n) for a, b in ranges for n in range(a, b + 1)]


SCENE = {"M": [1, 2, 7, 8, 13, 14, 19, 20, 25, 26], "S": [3, 4, 9, 10, 15, 16, 21, 22, 27, 28],
         "T": [5, 6, 11, 12, 17, 18, 23, 24, 29, 30]}

PRODUCTS = {
    "christmas_magic": dict(
        name="Christmas Magic", items=nums("book1", (1, 10)), price=299, christmas=True,
        title="Christmas Paint by Number Book, 10 Cozy Christmas Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten cozy Christmas scenes to paint this holiday season: a snowman, a festive wreath, Santa's sleigh across the moon, a Christmas market, Santa's workshop and more.",
        tags=["christmas coloring", "christmas printable", "holiday coloring", "cozy christmas", "gift for mom",
              "stocking stuffer", "gift for her", "ipad coloring page", "christmas gift idea"]),
    "winter_wonderland": dict(
        name="Winter Wonderland", items=nums("book1", (11, 20)), price=299, christmas=True,
        title="Winter Paint by Number Book, 10 Cozy Winter Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten snowy winter scenes to paint by the fire: a penguin with hot cocoa, red cardinals, snow monkeys in a hot spring, a horse-drawn sleigh, a frozen waterfall and more.",
        tags=["winter coloring page", "stocking stuffer", "winter printable", "cozy coloring pages",
              "christmas coloring", "gift for mom", "gift for her", "ipad coloring page", "penguin coloring"]),
    "hygge_christmas_winter": dict(
        name="Hygge Christmas & Winter", items=nums("book1", (1, 20)), price=449, christmas=True,
        title="Christmas Paint by Number Book, 20 Hygge Christmas and Winter Color by Number Pages for Adults, Procreate iPad Printable PDF",
        blurb="Twenty cozy Scandinavian-style Christmas and winter scenes in cranberry red, pine green and warm gold: festive wreaths, Santa's sleigh, a Christmas market, snowy villages, winter animals and more.",
        tags=["christmas coloring", "hygge coloring", "winter coloring page", "gift for mom", "stocking stuffer",
              "cozy christmas", "gift for her", "ipad coloring page", "christmas gift idea"]),
    "woodland_wildlife": dict(
        name="Woodland Wildlife", items=nums("book2", (21, 30)), price=299,
        title="Woodland Animals Paint by Number Book, 10 Forest Animal Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten woodland animals in warm earthy colors: a baby fawn, a red squirrel, a red panda, a kingfisher, a brown bear catching salmon, a moose at dawn and more.",
        tags=["animal coloring book", "woodland animals", "forest coloring", "wildlife coloring", "red panda coloring",
              "deer coloring page", "coloring book pdf", "ipad coloring page", "nature lover gift"]),
    "cats_and_dogs": dict(
        name="Cats & Dogs", items=nums("book2", (31, 40)), price=299,
        title="Cats and Dogs Paint by Number Book, 10 Cute Pet Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten adorable cats and dogs to paint: a golden retriever puppy, a fluffy kitten, a pug in a sweater, a corgi in the tulips, a beagle in a bike basket, a black cat on an autumn porch and more.",
        tags=["dog coloring pages", "cat coloring pages", "pet coloring book", "puppy coloring", "kitten coloring",
              "dog lover gift", "cat lover gift", "coloring book pdf", "ipad coloring page"]),
    "woodland_furry_friends": dict(
        name="Woodland & Furry Friends", items=nums("book2", (21, 40)), price=449,
        title="Animal Paint by Number Book, 20 Woodland Animals, Cats and Dogs Color by Number Pages for Adults, Procreate iPad Printable PDF",
        blurb="Twenty animals in a warm vintage nature-journal style: woodland wildlife like a fawn, red panda and moose, plus puppies, kittens and cozy pets.",
        tags=["animal coloring book", "dog coloring pages", "cat coloring pages", "woodland animals", "wildlife coloring",
              "pet lover gift", "coloring book pdf", "ipad coloring page", "cozy coloring pages"]),
    "cottage_garden": dict(
        name="Cottage Garden", items=nums("book3", (41, 50)), price=299,
        title="Cottagecore Paint by Number Book, 10 Cottage Garden Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten soft cottagecore garden scenes in sage, dusty rose and butter yellow: a wisteria door, a vintage bicycle, a garden tea party, beehives, a lavender field and more.",
        tags=["cottagecore coloring", "garden coloring", "flower coloring page", "cottage garden art", "floral coloring",
              "spring coloring", "coloring book pdf", "ipad coloring page", "cozy coloring pages"]),
    "cozy_hideaways": dict(
        name="Cozy Hideaways", items=nums("book3", (51, 60)), price=299,
        title="Cozy Paint by Number Book, 10 Cottagecore Hideaway Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten dreamy little hideaways: a cottage in a jar, a narrowboat home, a secret garden gate, a bakery with a cat, a treehouse, a rainy-day café and an attic art studio.",
        tags=["cozy coloring pages", "cottagecore coloring", "cozy coloring book", "bakery coloring", "treehouse coloring",
              "cottage coloring", "coloring book pdf", "ipad coloring page", "hygge coloring"]),
    "soft_cottagecore_dreams": dict(
        name="Soft Cottagecore Dreams", items=nums("book3", (41, 60)), price=449,
        title="Cottagecore Paint by Number Book, 20 Soft Cottage Garden and Cozy Color by Number Pages for Adults, Procreate iPad Printable PDF",
        blurb="Twenty soft, dreamy cottagecore scenes: flower-filled cottage gardens, wisteria doors and tea parties, plus cozy hideaways like a bakery, a treehouse and a rainy-day café.",
        tags=["cottagecore coloring", "cozy coloring pages", "garden coloring", "flower coloring page", "cottage coloring",
              "spring coloring", "coloring book pdf", "ipad coloring page", "floral coloring"]),
    "cozy_collection_60": dict(
        name="The Cozy Collection", items=nums("book1", (1, 20)) + nums("book2", (21, 40)) + nums("book3", (41, 60)),
        price=799,
        title="60 Paint by Number Pages for Adults, Christmas, Animals and Cottagecore Color by Number Book, Procreate iPad and Printable PDF",
        blurb="All three cozy books in one: 20 hygge Christmas and winter scenes, 20 woodland animals, cats and dogs, and 20 soft cottagecore gardens and hideaways.",
        tags=["christmas coloring", "animal coloring book", "cottagecore coloring", "cozy coloring pages",
              "coloring bundle", "coloring book pdf", "ipad coloring page", "dog coloring pages", "holiday coloring"]),
    "mountains_nature": dict(
        name="Mountains & Nature", items=[("scenery", n) for n in SCENE["M"]], price=299,
        title="Mountain Landscape Paint by Number Book, 10 Scenic Nature Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten breathtaking landscapes from around the world: Mount Fuji at sunrise, an Icelandic waterfall, Bali rice terraces, a Norwegian fjord, Yosemite, the Swiss Alps and Machu Picchu.",
        tags=["landscape coloring", "mountain coloring", "nature coloring", "scenery coloring", "travel coloring",
              "waterfall coloring", "coloring book pdf", "ipad coloring page", "nature lover gift"]),
    "seas_shores": dict(
        name="Seas & Shores", items=[("scenery", n) for n in SCENE["S"]], price=299,
        title="Beach and Ocean Paint by Number Book, 10 Coastal Scenery Color by Number Pages for Adults, Procreate iPad and Printable PDF",
        blurb="Ten dreamy coastal scenes: a wooden pier at sunset, Maldives bungalows, the Algarve cliffs, Lake Como, a coral reef with sea turtles, a Santorini sunset and a tropical island bay.",
        tags=["beach coloring pages", "ocean coloring", "coastal coloring", "landscape coloring", "travel coloring",
              "summer coloring", "coloring book pdf", "ipad coloring page", "scenery coloring"]),
    "villages_cities": dict(
        name="Villages & Cities", items=[("scenery", n) for n in SCENE["T"]], price=299,
        title="Travel Paint by Number Book, 10 European Village and City Color by Number Pages for Adults, Procreate iPad Printable PDF",
        blurb="Ten charming places to paint: a Santorini chapel, a Dutch windmill, Amsterdam canals, Venice, an alpine lake village, Prague rooftops, a Kyoto street and a Moroccan market.",
        tags=["travel coloring", "city coloring page", "europe coloring", "venice coloring", "landscape coloring",
              "village coloring", "coloring book pdf", "ipad coloring page", "travel lover gift"]),
    "around_the_world_30": dict(
        name="Around the World", items=[("scenery", n) for n in range(1, 31)], price=549,
        title="Travel Paint by Number Book, 30 Scenic Landscape Color by Number Pages for Adults, World Travel, Procreate iPad Printable PDF",
        blurb="Thirty beautiful places in a dreamy travel-poster style: mountains, lakes and waterfalls, beaches and coasts, and charming villages and cities from Japan to Morocco.",
        tags=["travel coloring", "landscape coloring", "scenery coloring", "world travel gift", "mountain coloring",
              "beach coloring pages", "coloring book pdf", "ipad coloring page", "travel lover gift"]),
}

NAME_FIX = {"santas": "Santa's", "and": "and", "of": "of", "in": "in", "on": "on", "with": "with"}


# ---------- designs ----------

def design_dir(folder, n):
    hits = [d for d in (BUILT / folder).glob(f"{n:02d}_*") if (d / "report.txt").exists()]
    if not hits:
        raise SystemExit(f"{folder} design {n:02d} is not built yet")
    return hits[0]


def pretty(stem):
    words = re.sub(r"^\d+_([MST]_)?((EXTRA_HARD|EASY|MEDIUM|HARD|EXPERT)_)?", "", stem).split("_")
    out = [NAME_FIX.get(w, w.capitalize()) for w in words]
    out[0] = out[0][0].upper() + out[0][1:]
    return " ".join(out)


def stats(d):
    m = re.search(r"(\d+) regions, \d+ numbers, (\d+) colors", (d / "report.txt").read_text(encoding="utf-8"))
    return int(m.group(1)), int(m.group(2))


def level(regions):
    return "Easy" if regions < 150 else "Medium" if regions < 400 else "Challenging"


class BookCollection(L.Collection):
    """make_listing_images.Collection over arbitrary built design folders (numbered 1..N in book order)."""

    def __init__(self, dirs, meta_root):
        self.dirs = dirs
        self.files = [SRC / d.parent.name / f"{d.name}.png" for d in dirs]
        self.root = meta_root
        self.stats = {i: stats(d) for i, d in enumerate(dirs, 1)}
        self.names = {i: pretty(d.name) for i, d in enumerate(dirs, 1)}
        self.count = len(dirs)
        self._art = {}
        for i, d in enumerate(dirs, 1):          # palette_image reads <root>/Design_NN/Hex_Codes.txt
            (meta_root / f"Design_{i:02d}").mkdir(parents=True, exist_ok=True)
            shutil.copy(d / "Hex_Codes.txt", meta_root / f"Design_{i:02d}" / "Hex_Codes.txt")

    def art(self, n):
        if n not in self._art:
            img, _ = clean_image(self.files[n - 1], sparkle=False)
            self._art[n] = L.pil_from_bgr(img)
        return self._art[n]

    def render(self, n, style):
        import cv2
        import numpy as np
        path = self.dirs[n - 1] / "PNG" / f"{style}.png"
        return cv2.imdecode(np.fromfile(str(path), np.uint8), cv2.IMREAD_COLOR)


def ordered_dirs(p):
    dirs = [design_dir(f, n) for f, n in p["items"]]
    return sorted(dirs, key=lambda d: stats(d)[0])


# ---------- delivery files ----------

def chunk(items, size_of, limit=MAX_FILE):
    parts, cur, total = [], [], 0
    for it in items:
        s = size_of(it)
        if cur and total + s > limit:
            parts.append(cur)
            cur, total = [], 0
        cur.append(it)
        total += s
    return parts + ([cur] if cur else [])


def build_files(p, dirs, d):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    base = p["name"].replace("&", "and").replace(" ", "_")
    names = [pretty(x.name) for x in dirs]
    files = []

    # 1) printable book: palette pages, A4 300 DPI indexed PNG streams
    pages = [CP.page_image(x / "PNG" / "Palette_Numbered.png") for x in dirs]
    sizes = [len(CP.png_parts(pg)[2]) + 2000 for pg in pages]
    parts = chunk(list(range(len(pages))), lambda i: sizes[i])
    for k, idx in enumerate(parts, 1):
        suffix = f"_Part_{k}" if len(parts) > 1 else ""
        out = d / f"1_{base}_Printable_Book{suffix}.pdf"
        CP.write_pdf((pages[i] for i in idx), out, f"{p['name']} - Paint by Number")
        files.append(out)

    # 2) color guide: the full-color number maps, 150 DPI JPEG pages
    guide = []
    for x in dirs:
        im = Image.open(x / "PNG" / "Navigation_Map.png").convert("RGB")
        guide.append(im.resize((1240, 1754), Image.LANCZOS))
    # Big books would need more than Etsy's 5 files: their color guide goes into the kit, one JPEG per design.
    guide_in_kit = len(dirs) > 40
    if not guide_in_kit:
        out = d / f"2_{base}_Color_Guide.pdf"
        guide[0].save(out, save_all=True, append_images=guide[1:], resolution=150, quality=82)
        files.append(out)

    # 3) Procreate kit: numbered PNG (A4 300 DPI) + swatches + palette per design
    entries = []
    for i, (x, nm) in enumerate(zip(dirs, names), 1):
        folder = f"{i:02d}_{nm.replace(' ', '_').replace(chr(39), '')}"
        buf = io.BytesIO()
        CP.page_image(x / "PNG" / "Light_Numbered.png").save(buf, "PNG", optimize=True)
        items = [(f"{folder}/{folder}_Numbered.png", buf.getvalue())]
        for sw in sorted(x.glob("*.swatches")):
            items.append((f"{folder}/{sw.name}", sw.read_bytes()))
        items.append((f"{folder}/Color_Palette.png", (x / "Color_Palette.png").read_bytes()))
        items.append((f"{folder}/Hex_Codes.txt", (x / "Hex_Codes.txt").read_bytes()))
        if guide_in_kit:
            g = io.BytesIO()
            guide[i - 1].resize((1000, 1414), Image.LANCZOS).save(g, "JPEG", quality=78)
            items.append((f"{folder}/{folder}_Color_Guide.jpg", g.getvalue()))
        entries.append(items)
    kits = chunk(entries, lambda items: sum(len(b) for _, b in items) + 4000)
    for k, group in enumerate(kits, 1):
        suffix = f"_Part_{k}" if len(kits) > 1 else ""
        out = d / f"3_{base}_Procreate_Kit{suffix}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("READ_ME.txt", README)
            for items in group:
                for name, data in items:
                    z.writestr(name, data)
        files.append(out)

    for f in files:
        if f.stat().st_size > 20_000_000:
            raise SystemExit(f"{f.name} is {f.stat().st_size / 1e6:.1f} MB (Etsy limit 20 MB)")
    if len(files) > 5:
        raise SystemExit(f"{p['name']}: {len(files)} files, Etsy allows 5")
    return files


README = """HOW TO USE YOUR PAINT BY NUMBER BOOK

PRINTING
Open the Printable Book PDF and print it on A4 paper (for US Letter choose "Fit to page").
Every page has its own numbered color palette at the bottom. Pages go from easiest to hardest.
Small details such as eyes and ornaments are already printed in color, so you only paint the numbered areas.

PROCREATE (iPad)
1. Import a design's Numbered PNG into Procreate.
2. Tap its .swatches file to add the numbered palette (designs with more than 30 colors have two files).
3. Set the line art layer to Multiply, add a layer underneath and paint.

COLOR GUIDE
The Color Guide shows every page fully colored, so you can check any number
(a PDF, or for the 60-page collection a Color_Guide JPEG inside each design's folder).

For personal use only. Thank you for your purchase, and happy painting!
"""


# ---------- photos ----------

def cover_book(col, p, out):
    img = background(1)
    ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
    picks = [ranked[round(k * (len(ranked) - 1) / 5)] for k in range(6)]
    cw, ch, gap, cols = 555, 740, 34, 3
    x0 = W - 90 - (cols * cw + (cols - 1) * gap)
    text_c(img, p["name"].upper(), W / 2, 26, font("georgiab", 112), PLUM)
    tiles = col.tiles(picks, (cw, ch))
    for i, n in enumerate(picks):
        r, cc = divmod(i, cols)
        x, y = x0 + cc * (cw + gap), 200 + r * (ch + gap + 14)
        shadowed(img, tiles[n], (x, y), border=12)
    starburst(img, 410, 480, 300, CORAL)
    text_c(img, str(col.count), 410, 330, font("impact", 250), "white")
    text_c(img, "PAGES", 410, 590, font("segoeuib", 100), "white")
    for i, (line, f_, color, size) in enumerate([("Paint by Number", "segoeuib", PLUM, 60),
                                                 ("Procreate iPad", "georgiab", CORAL, 78),
                                                 ("+ Printable", "georgiab", CORAL, 78)]):
        text_c(img, line, 410, 880 + i * 105 - (20 if i else 0), font(f_, size), color)
    for i, ln in enumerate(["Easy to challenging", "Own palette on every page", "PDF  +  PNG  +  .swatches"]):
        text_c(img, ln, 410, 1260 + i * 80, font("segoeui", 48), INK)
    banner(img, "INSTANT DOWNLOAD  •  PRINT AT HOME OR PAINT ON YOUR iPAD", H - 118)
    return L.save_jpg(img, out)


def overview(col, p, out):
    img = background(15)
    n = col.count
    cols = {10: 5, 20: 5, 30: 6, 60: 10}.get(n, 5)
    rows = -(-n // cols)
    gap = 26 if n <= 30 else 14
    label = n <= 20
    cw = min((W - 160 - (cols - 1) * gap) // cols, int((H - 330 - rows * (gap + (52 if label else 0))) / rows / 1.333))
    ch = int(cw * 1.333)
    text_c(img, f"ALL {n} PAGES, EASY TO CHALLENGING", W / 2, 24, font("georgiab", 96), PLUM)
    x0 = (W - (cols * cw + (cols - 1) * gap)) // 2
    row_h = ch + gap + (52 if label else 0)
    y0 = 175 + max(0, (H - 140 - 175 - rows * row_h) // 2)
    for i in range(1, n + 1):
        r, cc = divmod(i - 1, cols)
        x, y = x0 + cc * (cw + gap), y0 + r * row_h
        shadowed(img, cover_crop(col.art(i), cw, ch), (x, y), border=8 if n <= 30 else 5)
        if label:
            text_c(img, col.names[i], x + cw / 2 + 8, y + ch + 14, font("segoeuib", 32), PLUM)
    banner(img, "EVERY PAGE WITH ITS OWN NUMBERED COLOR PALETTE", H - 118)
    return L.save_jpg(img, out)


def page_preview(col, p, out):
    """The real printable page next to its finished painting."""
    img = background(3)
    ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
    n = ranked[len(ranked) // 2]
    page = Image.open(col.dirs[n - 1] / "PNG" / "Palette_Numbered.png").convert("RGB")
    ch = 1450
    cw = round(ch * page.width / page.height)
    xl, xr = 200, W - 200 - cw - 28
    text_c(img, "PRINT IT AND PAINT IT", W / 2, 24, font("georgiab", 110), PLUM)
    shadowed(img, page.resize((cw, ch), Image.LANCZOS), (xl, 190))
    shadowed(img, cover_crop(col.art(n), cw, ch), (xr, 190))
    text_c(img, "YOUR PRINTABLE PAGE", xl + cw / 2 + 14, 1700, font("segoeuib", 50), TEAL)
    text_c(img, "FINISHED PAINTING", xr + cw / 2 + 14, 1700, font("segoeuib", 50), TEAL)
    banner(img, "A4 PRINTABLE  •  PALETTE ON EVERY PAGE  •  PRINT AS OFTEN AS YOU LIKE", H - 118)
    return L.save_jpg(img, out)


import make_cover_bs as CB

CB.THEMES.update({  # light top, light bottom, dark accent
    "christmas": ((252, 236, 232), (234, 200, 196), (150, 32, 44)),
    "rose": ((251, 240, 242), (234, 212, 222), (150, 70, 104)),
})
COVER_THEME = {"christmas_magic": "christmas", "winter_wonderland": "christmas", "hygge_christmas_winter": "christmas",
               "woodland_wildlife": "wild", "woodland_furry_friends": "wild", "cats_and_dogs": "cozy",
               "cottage_garden": "rose", "cozy_hideaways": "rose", "soft_cottagecore_dreams": "rose",
               "cozy_collection_60": "cozy", "mountains_nature": "teal", "seas_shores": "teal",
               "villages_cities": "sunset", "around_the_world_30": "sunset"}


def cover_bs(col, p, key, out):
    """Best-seller cover (same design as the 15-design sets): ribbon headline, hero iPad, fanned tablets."""
    ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
    hero = ranked[int(len(ranked) * 0.7)]
    rest = [n for n in ranked if n != hero]
    others = [rest[round(k * (len(rest) - 1) / 5)] for k in range(6)]
    return CB.make(col, hero, others, col.count, p["name"], list(col.stats), out, COVER_THEME.get(key, "cozy"))


def build_photos(col, p, d, key=""):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
    mid, hard = ranked[len(ranked) // 2], ranked[-1]
    feat = [ranked[int(len(ranked) * f)] for f in (0.45, 0.75, 0.95)]
    n = col.count
    included = [("PDF", CORAL, f"Printable book: {n} pages", "A4, palette on every page, easiest first"),
                ("MAP", PLUM, "Color guide PDF", "Every page fully colored, check any number"),
                ("PNG", TEAL, "6 PNG styles per design", "600 DPI, ready for Procreate (full pack)"),
                ("SVG", (60, 110, 170), "Scalable vector line art", "Numbered dark & light, any size"),
                (".SW", MUSTARD, "Procreate palettes (.swatches)", "One-tap import, colors in number order"),
                ("PAL", (90, 150, 90), "Palette sheets + hex codes", "For markers, paint or other apps")]
    howto = [("1", "Download", "Book on Etsy, full pack from the link in the PDF."),
             ("2", "Print or open on iPad", "Print the A4 book, or import a PNG into Procreate."),
             ("3", "Load the palette", "Tap the .swatches file to add the numbered colors."),
             ("4", "Paint by number", "Match each number to its color. Relax and enjoy!")]
    terms = [("1", "Instant digital download", "No waiting. Your files are ready right after checkout."),
             ("2", "Book + full pack link", "Print right away; get the full pack from the PDF link."),
             ("3", "Print at home or at a print shop", "A4 print-ready. Print again and again for yourself."),
             ("4", "Paint digitally on your iPad", "Works great in Procreate. Palettes included."),
             ("5", "For personal use only", "No physical item is shipped. Files are not for resale."),
             ("6", "Questions? Just message me", "Happy to help with downloads and file questions.")]
    L.NAMES.update(col.names)
    plan = {
        "01_cover.jpg": lambda o: cover_bs(col, p, key, o),
        "02_all_pages.jpg": lambda o: overview(col, p, o),
        "03_featured.jpg": lambda o: L.featured_image(col, feat, p["name"].upper(), "Featured pages from this book",
                                                      o, seed=21),
        "04_print_and_paint.jpg": lambda o: page_preview(col, p, o),
        "05_before_after.jpg": lambda o: L.before_after(col, hard, o),
        "06_ipad.jpg": lambda o: L.ipad_image(col, mid, o),
        "07_six_styles.jpg": lambda o: L.styles_image(col, mid, o),
        "08_included.jpg": lambda o: L.included_image(col, mid, o, rows=included),
        "09_palette.jpg": lambda o: L.palette_image(col, hard, o),
        "10_how_it_works.jpg": lambda o: L.howto_image(col, mid, o, steps=howto),
        "11_good_to_know.jpg": lambda o: L.terms_image(o, rows=terms),
    }
    for name, fn in plan.items():
        fn(d / name)


# ---------- listing text ----------

def listing_text(p, dirs, files):
    tags = CORE_TAGS + p["tags"]
    assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), (p["name"], tags)
    assert len(p["title"]) <= 140, (p["name"], len(p["title"]))
    regions = [stats(x)[0] for x in dirs]
    names = "\n".join(f"{i}. {pretty(x.name)} ({level(r)})" for i, (x, r) in enumerate(zip(dirs, regions), 1))
    file_lines = "\n".join(f"- {f.name.split('_', 1)[1].replace('_', ' ').rsplit('.', 1)[0]} ({f.suffix[1:].upper()})"
                           for f in files)
    kit = any("Procreate_Kit" in f.name for f in files)
    pack = any("Download_Full_Pack" in f.name for f in files)
    extras = ""
    if kit:
        extras += "\n- Procreate kit: a numbered PNG and a .swatches palette for every design, plus palette sheets and hex codes"
    if pack:
        extras += ("\n- FULL PACK (download link inside the PDF): for every design an A4 PDF with dark, light, shadow guide "
                   "and palette pages, 6 PNG styles at 600 DPI (4961 x 7016 px), scalable SVG line art, Procreate "
                   ".swatches palettes, palette sheets and hex codes")
    desc = f"""{p['blurb']}

{len(dirs)} paint by number pages to print at home or paint on your iPad in Procreate. Pages go from easy to challenging (about {min(regions)} to {max(regions)} numbered zones), so it's relaxing for beginners and still fun for experienced painters. Small details like eyes and ornaments come already colored, so you only paint the numbered areas.

WHAT YOU GET (INSTANT DOWNLOAD)
{file_lines}

- Printable book: A4 pages at 300 DPI, each with its own numbered color palette, easiest first
- Color guide: every page fully colored, so you can check any number{extras}

THE PAGES
{names}

HOW TO PAINT IN PROCREATE
- Import a numbered PNG
- Tap its .swatches file to load the numbered colors
- Set the line art layer to Multiply and paint on a layer underneath

PRINTING
Print on A4 paper at home or at a print shop. For US Letter paper, choose "Fit to page".

PLEASE NOTE
- This is a digital download. No physical item will be shipped.
- Colors can look slightly different on screens and printers.
- For personal use only. Please don't share or resell the files.

Questions? Send me a message any time."""
    return dict(title=p["title"], tags=tags, description=desc, price=p["price"], christmas=p.get("christmas", False))


# ---------- commands ----------

def build(keys):
    for key in keys:
        p = PRODUCTS[key]
        d = OUT / key
        dirs = ordered_dirs(p)
        files = build_files(p, dirs, d / "files")
        col = BookCollection(dirs, d / "_meta")
        build_photos(col, p, d / "photos", key)
        (d / "listing.json").write_text(json.dumps(listing_text(p, dirs, files), indent=2, ensure_ascii=False),
                                        encoding="utf-8")
        print(f"built {key}: {len(dirs)} pages | " + ", ".join(f"{f.name} {f.stat().st_size / 1e6:.1f}MB" for f in files),
              flush=True)


def upload(keys):
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state_file = OUT / "uploaded.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    sections = {s["title"]: s["shop_section_id"] for s in e.request("GET", f"/shops/{sid}/sections")["results"]}
    for key in keys:
        d = OUT / key
        if key in state:                         # resume: add whatever photos/files are missing
            lid = state[key]
            have_imgs = len(e.request("GET", f"/listings/{lid}/images")["results"])
            photos_ = sorted((d / "photos").glob("*.jpg"))
            if have_imgs < len(photos_):
                replace_photos([key])
            have = {f["filename"] for f in e.request("GET", f"/shops/{sid}/listings/{lid}/files")["results"]}
            for rank, f in enumerate(sorted((d / "files").iterdir()), 1):
                if f.name not in have:
                    e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": f.name},
                              files={"file": f})
            print(f"checked {key} ({lid}): photos and files complete", flush=True)
            continue
        text = json.loads((d / "listing.json").read_text(encoding="utf-8"))
        listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
            "quantity": 999, "title": text["title"], "description": text["description"], "price": text["price"],
            "who_made": "i_did", "when_made": "2020_2026", "taxonomy_id": 339, "type": "download",
            "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(text["tags"]),
            "shop_section_id": sections.get(CHRISTMAS_SECTION, SECTION_PBN) if text["christmas"] else SECTION_PBN,
        })
        lid = listing["listing_id"]
        state[key] = lid
        state_file.write_text(json.dumps(state, indent=2))
        for rank, f in enumerate(sorted((d / "photos").glob("*.jpg")), 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": f})
        for rank, f in enumerate(sorted((d / "files").iterdir()), 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": f.name},
                      files={"file": f})
        print(f"uploaded {key} -> draft {lid}", flush=True)


MINIS = ["christmas_magic", "winter_wonderland", "woodland_wildlife", "cats_and_dogs", "cottage_garden",
         "cozy_hideaways", "mountains_nature", "seas_shores", "villages_cities"]
DRIVE = ROOT / "output" / "drive_zips"

FULL_README = """YOUR PAINT BY NUMBER FULL PACK

INSIDE
- Printable_Book.pdf: every page on A4 with its own numbered palette, easiest first
- Color_Guide.pdf: every page fully colored, so you can check any number
- Designs/: one folder per design, numbered from easiest to hardest, each with
    PDF/   A4 print-ready PDF (dark, light, shadow guide and palette pages)
    PNG/   6 styles at 4961 x 7016 px (A4 at 600 DPI): dark numbered, light numbered,
           shadow guide, full-color number map, page with palette, clean contour
    SVG/   scalable numbered line art (dark and light)
    .swatches  Procreate palette(s), colors in number order
    Color_Palette.png / .svg, Hex_Codes.txt, Color_Reference.png

PROCREATE (iPad)
1. Import a Light or Dark Numbered PNG.
2. Tap the .swatches file to add the numbered colors (more than 30 colors = two files).
3. Set the line art layer to Multiply, add a layer underneath and paint.

PRINTING
Print on A4 (for US Letter choose "Fit to page"). Small details like eyes and ornaments are
already printed in color, so you only paint the numbered areas.

For personal use only. Please don't share or resell the files. Happy painting!
"""


def zips(keys):
    import zipfile as zf
    DRIVE.mkdir(parents=True, exist_ok=True)
    for key in keys or MINIS:
        p = PRODUCTS[key]
        d = OUT / key
        if not (d / "files").exists():
            build([key])
        dirs = ordered_dirs(p)
        base = p["name"].replace("&", "and").replace(" ", "_")
        out = DRIVE / f"{base}_Paint_by_Number_Full_Pack.zip"
        with zf.ZipFile(out, "w") as z:
            z.writestr("READ_ME.txt", FULL_README, compress_type=zf.ZIP_DEFLATED)
            for f in sorted((d / "files").glob("*.pdf")):
                z.write(f, f.name.split("_", 1)[1], compress_type=zf.ZIP_STORED)
            for i, x in enumerate(dirs, 1):
                nm = pretty(x.name).replace(" ", "_").replace("'", "")
                folder = f"Designs/{i:02d}_{nm}"
                for f in sorted(x.rglob("*")):
                    if not f.is_file() or f.name == "report.txt":
                        continue
                    rel = f.relative_to(x).as_posix()
                    if f.name.endswith("_A4.pdf"):
                        rel = f"PDF/{nm}_A4.pdf"
                    elif f.name == "preview_colored.png":
                        rel = "Color_Reference.png"
                    small = f.suffix.lower() in (".svg", ".txt", ".swatches")
                    z.write(f, f"{folder}/{rel}", compress_type=zf.ZIP_DEFLATED if small else zf.ZIP_STORED)
        print(f"zip {out.name}: {len(dirs)} designs, {out.stat().st_size / 1e6:.0f} MB", flush=True)


LINKS_FILE = DRIVE / "links.json"   # mini key -> Google Drive link of its full-pack zip


def minis_of(key):
    items = set(PRODUCTS[key]["items"])
    return [m for m in MINIS if set(PRODUCTS[m]["items"]) <= items]


def page_links(c, D, links, tiles, subtitle):
    """Thank-you page with one download button per full-pack part."""
    from reportlab.lib.utils import simpleSplit
    D.background(c, 0)
    D.text_c(c, "THANK YOU!", D.H - 92, "GeoB", 52, D.PLUM)
    D.text_c(c, subtitle, D.H - 126, "SegB", 17, D.CORAL)
    tw, th, gap = 80, 107, 9
    x0 = (D.W - (6 * tw + 5 * gap)) / 2
    for i, img in enumerate(tiles):
        x = x0 + i * (tw + gap)
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(x - 3, D.H - 262 - 3, tw + 6, th + 6, 5, stroke=0, fill=1)
        c.drawImage(str(img), x, D.H - 262, tw, th)
    D.text_c(c, f"Your full pack comes in {len(links)} parts. Download each one:", D.H - 300, "SegB", 13, D.INK)
    bw, bh, step = 420, 50, 78 if len(links) <= 4 else 70
    y = D.H - 370
    for k, (name, url) in enumerate(links, 1):
        bx = (D.W - bw) / 2
        c.setFillColorRGB(*D.TEAL)
        c.roundRect(bx, y, bw, bh, 14, stroke=0, fill=1)
        D.text_c(c, f"DOWNLOAD PART {k}: {name.upper()}", y + 19, "SegB", 15, (1, 1, 1))
        c.linkURL(url, (bx, y, bx + bw, y + bh), relative=0, thickness=0)
        c.setFont("Seg", 7.5)
        c.setFillColorRGB(*D.BLUE)
        c.drawCentredString(D.W / 2, y - 11, simpleSplit(url, "Seg", 7.5, 480)[0])
        c.linkURL(url, (bx, y - 14, bx + bw, y - 4), relative=0, thickness=0)
        y -= step
    tips = "Click a button, then use Download in Google Drive. Each part is a large ZIP: use Wi-Fi and unzip it " \
           "first (on iPad: tap it in the Files app). Need help? Message me on Etsy."
    D.paragraph(c, tips, 70, max(y + 30, 75), D.W - 140, "Seg", 10, D.INK, 14)
    D.footer(c, 1, 4)


def delivery(keys):
    import tempfile
    import make_delivery_pdf as D
    from reportlab.pdfgen import canvas as rl_canvas
    links = json.loads(LINKS_FILE.read_text()) if LINKS_FILE.exists() else {}
    for key in keys:
        parts = minis_of(key)
        if not parts or any(m not in links for m in parts):
            print(f"skip {key}: waiting for links of {[m for m in parts if m not in links]}")
            continue
        p = PRODUCTS[key]
        d = OUT / key
        if not (d / "files").exists():
            build([key])
        dirs = ordered_dirs(p)
        col = BookCollection(dirs, d / "_meta")
        base = p["name"].replace("&", "and").replace(" ", "_")
        out = d / "files" / f"0_{base}_Download_Full_Pack.pdf"
        ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
        hero = [ranked[round(k * (len(ranked) - 1) / 5)] for k in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            tiles = []
            for n in hero:
                t = Path(tmp) / f"t{n}.jpg"
                cover_crop(col.art(n), 480, 640).save(t, quality=88)
                tiles.append(t)
            c = rl_canvas.Canvas(str(out), pagesize=D.A4)
            c.setTitle(f"Your {p['name']} Paint by Number download")
            sub = f"for your {p['name']} Paint by Number book"
            if len(parts) == 1:
                D.page_link(c, links[parts[0]], tiles, subtitle=sub)
            else:
                page_links(c, D, [(PRODUCTS[m]["name"], links[m]) for m in parts], tiles, sub)
            c.showPage()
            D.page_inside(c, len(dirs))
            c.showPage()
            D.page_howto(c)
            c.showPage()
            D.page_terms(c)
            c.showPage()
            c.save()
        files = sorted((d / "files").iterdir())
        if len(files) > 5:                       # the full pack already has the Procreate kit
            for f in [f for f in files if "Procreate_Kit" in f.name]:
                f.unlink()
            files = sorted((d / "files").iterdir())
        (d / "listing.json").write_text(json.dumps(listing_text(p, dirs, files), indent=2, ensure_ascii=False),
                                        encoding="utf-8")
        print(f"delivery {key}: {len(parts)} link(s) | files: " + ", ".join(f.name for f in files), flush=True)


def photos(keys):
    """Rebuild only the listing photos."""
    for key in keys:
        p = PRODUCTS[key]
        dirs = ordered_dirs(p)
        build_photos(BookCollection(dirs, OUT / key / "_meta"), p, OUT / key / "photos", key)
        print(f"photos {key}: {len(list((OUT / key / 'photos').glob('*.jpg')))} images", flush=True)


def replace_photos(keys):
    """Swap the photos of already-uploaded listings for the current photos/ folder."""
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state = json.loads((OUT / "uploaded.json").read_text())
    for key in keys:
        if key not in state:
            continue
        lid = state[key]
        old = [im["listing_image_id"] for im in e.request("GET", f"/listings/{lid}/images")["results"]]
        new = sorted((OUT / key / "photos").glob("*.jpg"))
        # Etsy allows 20 images and refuses to delete the last one: trim old ones to make room, add new, then drop the rest
        while old and len(old) + len(new) > 20 and len(old) > 1:
            e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{old.pop()}")
        for rank, f in enumerate(new, 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": f})
        for image_id in old:
            e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
        print(f"replaced photos on {key} ({lid}): {len(new)} images", flush=True)


def videos(keys):
    """14.5 s coloring time-lapse of the cover's hero design, attached to the uploaded listing."""
    import make_coloring_video as V
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state = json.loads((OUT / "uploaded.json").read_text())
    for key in keys:
        p = PRODUCTS[key]
        col = BookCollection(ordered_dirs(p), OUT / key / "_meta")
        L.NAMES.update(col.names)
        V.NAMES.update(col.names)
        ranked = sorted(col.stats, key=lambda i: col.stats[i][0])
        hero = ranked[int(len(ranked) * 0.7)]                      # same design as the cover's iPad
        out = OUT / key / "video" / "paint_by_number_video.mp4"
        if not out.exists():
            V.build(col, hero, out.parent, pages=col.count, out_name=out.name)
        lid = state.get(key)
        if not lid:
            continue
        if e.request("GET", f"/listings/{lid}/videos")["count"]:
            print(f"{key}: listing already has a video")
            continue
        e.request("POST", f"/shops/{sid}/listings/{lid}/videos", form={"name": f"{p['name']} paint by number"},
                  files={"video": out})
        print(f"video uploaded to {key} ({lid})", flush=True)


def setlink(args):
    links = json.loads(LINKS_FILE.read_text()) if LINKS_FILE.exists() else {}
    key, url = args
    assert key in MINIS, key
    links[key] = url
    DRIVE.mkdir(parents=True, exist_ok=True)
    LINKS_FILE.write_text(json.dumps(links, indent=2))
    print(f"link saved for {key}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    keys = sys.argv[2:] or (MINIS if cmd == "zips" else list(PRODUCTS))
    {"build": build, "upload": upload, "zips": zips, "delivery": delivery, "setlink": setlink,
     "photos": photos, "replace_photos": replace_photos, "videos": videos}[cmd](keys)
