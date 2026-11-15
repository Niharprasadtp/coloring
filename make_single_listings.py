"""Single-design Etsy listings: photos, 5 delivery files and listing text, then upload as drafts.

    .venv/Scripts/python make_single_listings.py build  [designs...]   # local files only
    .venv/Scripts/python make_single_listings.py upload [designs...]   # create Etsy DRAFT listings

Output goes to output/singles/<NN>_<Name>/ (photos/, files/, listing.json).
Uploaded listing ids are recorded in output/singles/uploaded.json so a design is never uploaded twice.
Each listing gets 5 files under Etsy's 20 MB per-file limit: A4 PDF, 3 numbered PNGs, and a Procreate kit ZIP.
The shadow-guide and color-map PNGs stay exclusive to the 15-design sets.
"""

import json
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import make_listing_images as L
import make_sets as MS
from make_listing_images import (CORAL, INK, MUSTARD, PLUM, TEAL, H, W, background, banner, cover_crop, font,
                                 save_jpg, shadowed, text_c, text_l, wrap)

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent
COLLECTION = ROOT / "output" / "collection"
OUT = ROOT / "output" / "singles"
MAX_FILE = 19_500_000          # Etsy limit is 20 MB per file
PRICE = 199                    # INR
SECTION_PBN = 61351078         # "Paint by Numbers"
CHRISTMAS_SECTION_TITLE = "Christmas & Winter"  # Etsy caps section names at 24 characters

SET_INFO = {  # set folder -> (display name, bundle listing url)
    "Set1_Cozy_Cottage_Winter": ("Cozy Cottage & Winter", "https://www.etsy.com/listing/4617315630"),
    "Set2_Wildlife_Scenic_Nature": ("Wildlife & Nature", "https://www.etsy.com/listing/4617312754"),
    "Set3_Sunsets_Travel": ("Sunsets & Travel", "https://www.etsy.com/listing/4617296457"),
}

CORE_TAGS = ["paint by number", "procreate coloring", "color by number", "adult coloring page",
             "ipad coloring page", "procreate swatches"]

DESIGNS = {
    19: dict(christmas=True,
             title="Christmas Fireplace Paint by Number Procreate, Cozy Christmas Color by Number for Adults, Sleeping Cat, Printable PDF",
             blurb="A crackling stone fireplace hung with stockings, a glowing Christmas tree, wrapped presents and a ginger cat curled up asleep on the rug.",
             tags=["christmas coloring", "fireplace coloring", "cozy christmas", "christmas printable",
                   "cat coloring page", "holiday coloring", "christmas pbn"]),
    24: dict(christmas=True,
             title="Winter Village Paint by Number Procreate, Christmas Ice Skating Color by Number for Adults, Snowy Night, Printable PDF",
             blurb="A snowy village under a starry violet sky, with ice skaters on the frozen pond, a horse-drawn sleigh and warm lights in every window.",
             tags=["christmas coloring", "winter village", "ice skating art", "christmas printable",
                   "winter coloring page", "holiday coloring", "snowy village art"]),
    25: dict(christmas=True,
             title="Gingerbread House Paint by Number Procreate, Candy Christmas Color by Number for Adults, Printable PDF",
             blurb="A gingerbread house iced with sweets, surrounded by lollipops, candy canes and gingerbread men along a winding chocolate path.",
             tags=["gingerbread house", "candy coloring page", "christmas coloring", "christmas printable",
                   "gingerbread art", "holiday coloring", "sweet treats art"]),
    32: dict(christmas=True,
             title="Snowy Christmas Cabin Paint by Number Procreate, Snowman Winter Color by Number for Adults, Printable PDF",
             blurb="A snow-covered cottage glowing at night, with a jolly snowman, a decorated Christmas tree and a pile of presents.",
             tags=["christmas coloring", "snowman coloring", "winter cabin art", "christmas printable",
                   "winter coloring page", "holiday coloring", "cozy cottage art"]),
    1: dict(title="Red Fox Paint by Number Procreate, Winter Forest Fox Color by Number for Adults, Realistic Animal, Printable PDF",
            blurb="A red fox stands alert in a snowy birch forest, with every strand of its fur painted by number.",
            tags=["fox coloring page", "red fox art", "winter forest art", "animal coloring",
                  "realistic coloring", "wildlife coloring", "fox lover gift"]),
    8: dict(title="Barn Owl Paint by Number Procreate, Realistic Owl Color by Number for Adults, Woodland Forest, Printable PDF",
            blurb="A barn owl watches from its mossy oak hollow, framed by ferns and ivy.",
            tags=["owl coloring page", "barn owl art", "woodland coloring", "animal coloring",
                  "realistic coloring", "wildlife coloring", "owl lover gift"]),
    46: dict(title="Grey Wolf Paint by Number Procreate, Realistic Wolf Color by Number for Adults, Misty Forest, Printable PDF",
             blurb="A grey wolf walks through a misty pine forest, with ferns and fallen needles at its feet.",
             tags=["wolf coloring page", "grey wolf art", "forest coloring", "animal coloring",
                   "realistic coloring", "wildlife coloring", "wolf lover gift"]),
    29: dict(title="Amalfi Coast Paint by Number Procreate, Italy Travel Color by Number for Adults, Lemon Trees, Printable PDF",
             blurb="Colorful cliffside houses, lemon trees and a mint scooter above the turquoise Amalfi sea dotted with sailboats.",
             tags=["amalfi coast art", "italy coloring page", "travel coloring", "coastal coloring",
                   "lemon tree art", "italian summer", "landscape coloring"]),
    30: dict(title="Paris Cafe Paint by Number Procreate, Eiffel Tower Color by Number for Adults, French Street, Printable PDF",
             blurb="A Paris cafe with a striped awning, a flower cart and a bicycle, with the Eiffel Tower rising over the street.",
             tags=["paris coloring page", "eiffel tower art", "travel coloring", "french cafe art",
                   "paris lover gift", "city coloring page", "landscape coloring"]),
    11: dict(title="Northern Lights Paint by Number Procreate, Aurora Landscape Color by Number for Adults, Easy, Printable PDF",
             blurb="Green northern lights ripple over snowy peaks, a dark pine forest and a quiet lake with a canoe.",
             tags=["northern lights art", "aurora coloring", "easy paint by number", "landscape coloring",
                   "mountain coloring", "nature coloring", "beginner coloring"]),
}


def set_of(n):
    for name, cfg in MS.SETS.items():
        if n in cfg["designs"]:
            return name, cfg
    raise KeyError(n)


def level(regions):
    for limit, name in ((800, "Relaxing"), (1400, "Medium"), (2000, "Challenging")):
        if regions < limit:
            return name
    return "Expert"


def slug(n):
    return f"{n:02d}_" + MS.NAMES[n].replace(" ", "_").replace("&", "and").replace("'", "")


# ---------- photos ----------

def cover_single(col, n, out):
    img = background(50 + n)
    rect = col.rect(n)
    cw, ch = 1230, 1640
    colored = cover_crop(col.art(n), cw, ch)
    line = cover_crop(col.style_img(n, "Dark_Numbered", rect), cw, ch)
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (int(cw * 0.66), 0), (int(cw * 0.46), ch), (0, ch)], fill=255)
    composed = Image.composite(colored, line, mask.filter(ImageFilter.GaussianBlur(3)))
    shadowed(img, composed, (110, 120), border=18)
    x = 1480
    d = ImageDraw.Draw(img)
    text_l(img, "PAINT BY NUMBER", x, 140, font("segoeuib", 70), CORAL)
    name_f = font("georgiab", 128)
    lines = wrap(d, MS.NAMES[n], name_f, 1110)
    for i, ln in enumerate(lines):
        text_l(img, ln, x, 240 + i * 145, name_f, PLUM)
    y = 240 + 145 * len(lines) + 50
    regions, colors = col.stats[n]
    for j, (big, small, fill, fg) in enumerate([(f"{round(regions, -1):,}", "ZONES", MUSTARD, INK),
                                                (str(colors), "COLORS", TEAL, "white")]):
        bx = x + j * 370
        d.rounded_rectangle([bx, y, bx + 340, y + 210], 30, fill=fill)
        text_c(img, big, bx + 170, y + 16, font("impact", 112), fg)
        text_c(img, small, bx + 170, y + 140, font("segoeuib", 46), fg)
    y += 270
    d.rounded_rectangle([x, y, x + 710, y + 110], 55, fill=PLUM)
    text_c(img, f"Level: {level(regions)}", x + 355, y + 18, font("segoeuib", 58), "white")
    y += 170
    for i, ln in enumerate(["Procreate iPad + Printable", "PDF  •  PNG  •  SVG  •  .swatches"]):
        text_l(img, ln, x, y + i * 85, font("segoeuib" if i == 0 else "segoeui", 56), INK)
    banner(img, "INSTANT DOWNLOAD  •  ONE DESIGN  •  OWN NUMBERED COLOR PALETTE", H - 118)
    return save_jpg(img, out)


INCLUDED_ROWS = [("PDF", CORAL, "A4 print-ready PDF", "Dark, light, shadow guide & palette pages"),
                 ("PNG", TEAL, "3 numbered PNG styles", "Dark, light & with palette  •  4961 x 7016 px"),
                 ("SVG", PLUM, "Scalable vector line art", "Numbered dark & light, any size"),
                 (".SW", MUSTARD, "Procreate palette (.swatches)", "One-tap import, colors in number order"),
                 ("PAL", (90, 150, 90), "Palette sheet + hex codes", "PNG + SVG, for any painting app"),
                 ("REF", (60, 110, 170), "Contour + color reference", "No-number outline and the finished look")]
HOWTO_STEPS = [("1", "Download", "Get your 5 files from Etsy right after checkout."),
               ("2", "Print or open on iPad", "Print the A4 PDF, or import the PNG into Procreate."),
               ("3", "Load the palette", "Tap the .swatches file to add the numbered colors."),
               ("4", "Paint by number", "Match each number to its color. Relax and enjoy!")]
TERMS_ROWS = [("1", "Instant digital download", "No waiting. Your files are ready right after checkout."),
              ("2", "5 files, delivered by Etsy", "Find them under You > Purchases. Unzip the Procreate kit."),
              ("3", "Print at home or at a print shop", "A4 print-ready. Print again and again for yourself."),
              ("4", "Paint digitally on your iPad", "Works great in Procreate. Palette file included."),
              ("5", "For personal use only", "No physical item is shipped. Files are not for resale."),
              ("6", "Questions? Just message me", "Happy to help with downloads and file questions.")]


def build_photos(col, n, d):
    d.mkdir(parents=True, exist_ok=True)
    set_name, cfg = set_of(n)
    others = [m for m in cfg["designs"] if m != n and m != 33][:7]
    plan = {
        "01_cover.jpg": lambda o: cover_single(col, n, o),
        "02_before_after.jpg": lambda o: L.before_after(col, n, o),
        "03_ipad.jpg": lambda o: L.ipad_image(col, n, o),
        "04_closeup.jpg": lambda o: L.closeup_image(col, n, o),
        "05_included.jpg": lambda o: L.included_image(col, n, o, rows=INCLUDED_ROWS),
        "06_palette.jpg": lambda o: L.palette_image(col, n, o),
        "07_how_it_works.jpg": lambda o: L.howto_image(col, n, o, steps=HOWTO_STEPS),
        "08_get_the_set.jpg": lambda o: L.grid_image(col, [n] + others, "LOVE THIS DESIGN?",
                                                     f"Get it with 14 more in the {SET_INFO[set_name][0]} set",
                                                     o, seed=60 + n),
        "09_good_to_know.jpg": lambda o: L.terms_image(o, rows=TERMS_ROWS),
    }
    for name, fn in plan.items():
        fn(d / name)


# ---------- delivery files ----------

def build_files(n, d):
    src = COLLECTION / f"Design_{n:02d}"
    base = MS.NAMES[n].replace(" ", "_").replace("&", "and").replace("'", "")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    out = [d / f"1_{base}_A4_Print.pdf", d / f"2_{base}_Dark_Numbered.png",
           d / f"3_{base}_Light_Numbered.png", d / f"4_{base}_With_Palette.png", d / f"5_{base}_Procreate_Kit.zip"]
    shutil.copy(src / "PDF" / f"Design_{n:02d}_A4.pdf", out[0])
    shutil.copy(src / "PNG" / "Dark_Numbered.png", out[1])
    shutil.copy(src / "PNG" / "Light_Numbered.png", out[2])
    shutil.copy(src / "PNG" / "Palette_Numbered.png", out[3])
    tmp = d / "_contour.png"
    Image.open(src / "PNG" / "Contour.png").convert("L").save(tmp, optimize=True)  # grey only: lossless
    with zipfile.ZipFile(out[4], "w", zipfile.ZIP_DEFLATED) as z:
        for sw in sorted(src.glob("*.swatches")):
            z.write(sw, f"Procreate/{base}_{sw.name}")
        z.write(src / "Color_Palette.png", "Palette/Color_Palette.png")
        z.write(src / "Color_Palette.svg", "Palette/Color_Palette.svg")
        z.write(src / "Hex_Codes.txt", "Palette/Hex_Codes.txt")
        z.write(src / "SVG" / "Dark_Numbered.svg", "SVG/Dark_Numbered.svg")
        z.write(src / "SVG" / "Light_Numbered.svg", "SVG/Light_Numbered.svg")
        z.write(tmp, "Contour_No_Numbers.png")
        z.write(src / "preview_colored.png", "Color_Reference.png")
        z.writestr("READ_ME.txt", README)
    tmp.unlink()
    for f in out:
        size = f.stat().st_size
        if size > MAX_FILE:
            raise SystemExit(f"{f.name} is {size / 1e6:.1f} MB, over Etsy's 20 MB limit")
    return out


README = """HOW TO USE YOUR PAINT BY NUMBER

PROCREATE (iPad)
1. Open Procreate, tap + and import the Light or Dark Numbered PNG.
2. Open the Procreate folder in this ZIP and tap the .swatches file(s) to add the numbered palette.
   (Designs with more than 30 colors come with two .swatches files.)
3. Set the line art layer to Multiply, add a new layer underneath and paint.

PRINTING
Print the A4 PDF at home or at a print shop. For US Letter paper, choose "Fit to page".

OTHER APPS
Use Hex_Codes.txt or Color_Palette.png to set up your colors. The SVG files scale to any size.

Color_Reference.png shows the finished painting. Contour_No_Numbers.png is the clean outline.

For personal use only. Thank you for your purchase, and happy painting!
"""


# ---------- listing text ----------

def listing_text(col, n):
    info = DESIGNS[n]
    regions, colors = col.stats[n]
    set_name, _ = set_of(n)
    set_title, set_url = SET_INFO[set_name]
    tags = CORE_TAGS + info["tags"]
    assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), (n, tags)
    assert len(info["title"]) <= 140, (n, len(info["title"]))
    desc = f"""{info['blurb']}

Paint this {MS.NAMES[n]} design on your iPad in Procreate, or print it at home and paint with markers, colored pencils or paint. Level: {level(regions)}, with about {round(regions, -1):,} numbered zones and {colors} colors.

WHAT YOU GET (5 FILES, INSTANT DOWNLOAD)
1. A4 print-ready PDF: dark, light, shadow guide and palette pages
2. Dark numbered PNG, 4961 x 7016 px (A4 at 600 DPI)
3. Light numbered PNG, 4961 x 7016 px
4. PNG with the color palette printed under the artwork
5. Procreate kit (ZIP): .swatches palette in number order, printable palette sheet (PNG + SVG), hex code list, scalable SVG line art, a clean contour without numbers and a full-color reference image

HOW TO PAINT IN PROCREATE
- Import the light or dark numbered PNG
- Tap the .swatches file to load the numbered colors
- Set the line art layer to Multiply and paint on a layer underneath

PRINTING
Print the A4 PDF at home or at a print shop. For US Letter paper, choose "Fit to page" in your print settings.

LOVE IT? GET THE SET
This design is part of my {set_title} set: 15 paint by number designs, each with 6 PNG styles including a shadow guide and a full-color number map.
{set_url}

PLEASE NOTE
- This is a digital download. No physical item will be shipped.
- Colors can look slightly different on screens and printers.
- For personal use only. Please don't share or resell the files.

Questions? Send me a message any time."""
    return dict(title=info["title"], tags=tags, description=desc, price=PRICE, christmas=info.get("christmas", False))


# ---------- commands ----------

def build(ns):
    col = L.Collection(ROOT / "input", COLLECTION)
    for n in ns:
        d = OUT / slug(n)
        text = listing_text(col, n)
        files = build_files(n, d / "files")
        build_photos(col, n, d / "photos")
        (d / "listing.json").write_text(json.dumps(text, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"built {d.name}: " + ", ".join(f"{f.stat().st_size / 1e6:.1f}MB" for f in files), flush=True)


def upload(ns):
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state_file = OUT / "uploaded.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    sections = {s["title"]: s["shop_section_id"] for s in e.request("GET", f"/shops/{sid}/sections")["results"]}
    if CHRISTMAS_SECTION_TITLE not in sections:
        sections[CHRISTMAS_SECTION_TITLE] = e.request("POST", f"/shops/{sid}/sections",
                                                      form={"title": CHRISTMAS_SECTION_TITLE})["shop_section_id"]
    for n in ns:
        d = OUT / slug(n)
        if str(n) in state:
            print(f"skip {d.name}: already uploaded as {state[str(n)]}")
            continue
        text = json.loads((d / "listing.json").read_text(encoding="utf-8"))
        listing = e.request("POST", f"/shops/{sid}/listings", form={
            "quantity": 999, "title": text["title"], "description": text["description"], "price": text["price"],
            "who_made": "i_did", "when_made": "2020_2026", "taxonomy_id": 339, "type": "download",
            "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(text["tags"]),
            "shop_section_id": sections[CHRISTMAS_SECTION_TITLE] if text["christmas"] else SECTION_PBN,
        })
        lid = listing["listing_id"]
        state[str(n)] = lid
        state_file.write_text(json.dumps(state, indent=2))
        for rank, p in enumerate(sorted((d / "photos").glob("*.jpg")), 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
        for rank, p in enumerate(sorted((d / "files").iterdir()), 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": p.name},
                      files={"file": p})
        print(f"uploaded {d.name} -> draft {lid}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    ns = [int(x) for x in sys.argv[2:]] or list(DESIGNS)
    {"build": build, "upload": upload}[cmd](ns)
