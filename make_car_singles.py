"""Single-car Etsy listings from the Dream Garage car book (output/books_build/cars).

    .venv/Scripts/python make_car_singles.py build  [stem ...]   # local files: photos, 5 files, video, listing.json
    .venv/Scripts/python make_car_singles.py upload [stem ...]   # create Etsy DRAFT listings (+ video)

Output: output/car_singles/<stem>/. Uploaded listing ids go to output/car_singles/uploaded.json.
No brand or model names anywhere (titles, tags, descriptions, file names): car makers file IP takedowns.
"""

import json
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import make_books as MB
import make_listing_images as L
import make_single_listings as SL
from make_listing_images import (CORAL, INK, MUSTARD, PLUM, TEAL, H, W, background, banner, cover_crop, font,
                                 save_jpg, shadowed, text_c, text_l, wrap)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "car_singles"
PRICE = 199
BOOK_URL = "https://www.etsy.com/listing/4621027114"   # Dream Garage, 22 cars
CORE = SL.CORE_TAGS

PICKS = {
    "19_jdm_night_car_meet": dict(
        title="JDM Car Meet Paint by Number Procreate, Neon Garage Color by Number for Adults, Car Lover Gift, Printable PDF",
        blurb="Three 90s Japanese sports cars in orange, blue and red, lined up in a neon-lit parking garage while friends hang out at a late-night car meet.",
        tags=["jdm car art", "car meet art", "car lover gift", "gift for him", "car coloring page", "neon car art",
              "car guy gift"]),
    "13_tokyo_rain_jdm": dict(
        title="JDM Car Paint by Number Procreate, Tokyo Rain Street Color by Number for Adults, Neon Lanterns, Car Lover Gift, Printable PDF",
        blurb="A blue 90s Japanese performance coupe on a rainy Tokyo side street, with glowing paper lanterns and vending machines reflected in the wet road.",
        tags=["jdm car art", "tokyo street art", "car lover gift", "gift for him", "car coloring page", "japan coloring",
              "car guy gift"]),
    "12_neon_jdm_coupe": dict(
        title="JDM Sports Car Paint by Number Procreate, Neon City Night Color by Number for Adults, Car Lover Gift, Printable PDF",
        blurb="An orange 90s Japanese sports coupe with a big rear wing, parked in a rain-soaked lot under pink and cyan neon signs.",
        tags=["jdm car art", "neon car art", "car lover gift", "gift for him", "car coloring page", "synthwave art",
              "car guy gift"]),
    "14_cherry_blossom_sports_car": dict(
        title="JDM Sports Car Paint by Number Procreate, Cherry Blossom Mountain Road Color by Number for Adults, Car Lover Gift, PDF",
        blurb="A red pop-up headlight Japanese sports car on a winding mountain road at sunset, framed by pink cherry blossom trees.",
        tags=["jdm car art", "cherry blossom art", "car lover gift", "gift for him", "car coloring page",
              "mountain road art", "car guy gift"]),
    "16_miami_night_supercar": dict(
        title="80s Supercar Paint by Number Procreate, Neon Beach Night Color by Number for Adults, Retro Car Lover Gift, Printable PDF",
        blurb="A white 80s wedge supercar with its doors up, parked by the beach under palm trees, a neon hotel sign and a hot pink synthwave sky.",
        tags=["supercar art", "retro 80s art", "synthwave art", "car lover gift", "gift for him", "car coloring page",
              "neon car art"]),
    "17_neon_city_supercar": dict(
        title="Supercar Paint by Number Procreate, Neon City Rain Color by Number for Adults, Lime Green Sports Car, Car Lover Gift, PDF",
        blurb="A lime green angular supercar on a rainy city street at night, with skyscrapers and neon lights reflected in the puddles.",
        tags=["supercar art", "neon car art", "car lover gift", "gift for him", "car coloring page", "city night art",
              "car guy gift"]),
    "22_city_lights_supercar": dict(
        title="Sports Car Paint by Number Procreate, Las Vegas Night Color by Number for Adults, Blue Supercar, Car Lover Gift, PDF",
        blurb="A bright blue mid-engine sports car on a glittering city strip at night, with casino lights and palm trees reflected on the street.",
        tags=["supercar art", "sports car art", "car lover gift", "gift for him", "car coloring page", "las vegas art",
              "car guy gift"]),
    "06_1960s_fastback_hill_street": dict(
        title="Classic Muscle Car Paint by Number Procreate, 1960s Fastback Color by Number for Adults, Car Lover Gift, Printable PDF",
        blurb="A dark green 1960s American fastback parked on a steep San Francisco-style hill street lined with Victorian houses.",
        tags=["muscle car gift", "classic car gift", "car lover gift", "gift for him", "gift for dad",
              "car coloring page", "vintage car art"]),
    "04_1950s_christmas_pickup": dict(
        title="Christmas Truck Paint by Number Procreate, Vintage Red Pickup Color by Number for Adults, Easy, Christmas Gift, PDF",
        blurb="A vintage red 1950s pickup truck carrying a Christmas tree home along a snowy road under a starry night sky. An easy, relaxing design.",
        tags=["christmas truck", "christmas coloring", "red truck art", "stocking stuffer", "easy paint by number",
              "holiday coloring", "gift for dad"]),
    "20_christmas_chalet_suv": dict(
        title="Christmas Car Paint by Number Procreate, Snowy Chalet Color by Number for Adults, Off-Road SUV, Car Lover Gift, PDF",
        blurb="A black boxy off-road SUV with a Christmas tree on the roof, parked outside a snowy alpine chalet glowing with Christmas lights.",
        tags=["christmas coloring", "christmas car art", "car lover gift", "stocking stuffer", "gift for him",
              "winter coloring page", "holiday coloring"]),
}


def level(regions):
    return "Beginner" if regions < 150 else "Easy" if regions < 300 else "Medium" if regions < 550 else "Expert"


def collection():
    """All 22 book designs in file order, so the 'get the book' grid can show the others."""
    dirs = [MB.design_dir("cars", n) for n in range(1, 23)]
    col = MB.BookCollection(dirs, OUT / "_meta")
    L.NAMES.update(col.names)
    return col


def num(col, stem):
    return MB.pick(col, stem)


# ---------- photos ----------

def cover(col, n, out):
    """Single-design cover: half numbered, half painted, with zones, colors and level."""
    img = background(50 + n)
    cw, ch = 1230, 1640
    colored = cover_crop(col.art(n), cw, ch)
    line = cover_crop(col.style_img(n, "Dark_Numbered", col.rect(n)), cw, ch)
    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).polygon([(0, 0), (int(cw * 0.66), 0), (int(cw * 0.46), ch), (0, ch)], fill=255)
    shadowed(img, Image.composite(colored, line, mask.filter(ImageFilter.GaussianBlur(3))), (110, 120), border=18)
    x, d = 1480, ImageDraw.Draw(img)
    text_l(img, "PAINT BY NUMBER", x, 140, font("segoeuib", 70), CORAL)
    name_f = font("georgiab", 120)
    lines = wrap(d, col.names[n], name_f, 1110)
    for i, ln in enumerate(lines):
        text_l(img, ln, x, 240 + i * 138, name_f, PLUM)
    y = 240 + 138 * len(lines) + 50
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
    for i, ln in enumerate(["Procreate iPad + Printable", "Gift for car lovers"]):
        text_l(img, ln, x, y + i * 85, font("segoeuib" if i == 0 else "segoeui", 56), INK)
    banner(img, "INSTANT DOWNLOAD  •  ONE DESIGN  •  OWN NUMBERED COLOR PALETTE", H - 118)
    return save_jpg(img, out)


def print_and_paint(col, n, out):
    img = background(3 + n)
    page = Image.open(col.dirs[n - 1] / "PNG" / "Palette_Numbered.png").convert("RGB")
    ch = 1450
    cw = round(ch * page.width / page.height)
    xl, xr = 200, W - 200 - cw - 28
    text_c(img, "PRINT IT AND PAINT IT", W / 2, 24, font("georgiab", 110), PLUM)
    shadowed(img, page.resize((cw, ch), Image.LANCZOS), (xl, 190))
    shadowed(img, cover_crop(col.art(n), cw, ch), (xr, 190))
    text_c(img, "YOUR PRINTABLE PAGE", xl + cw / 2 + 14, 1700, font("segoeuib", 50), TEAL)
    text_c(img, "FINISHED PAINTING", xr + cw / 2 + 14, 1700, font("segoeuib", 50), TEAL)
    banner(img, "LIGHT GRAY NUMBERS THAT DISAPPEAR UNDER YOUR PAINT", H - 118)
    return save_jpg(img, out)


def build_photos(col, n, stem, d):
    d.mkdir(parents=True, exist_ok=True)
    others = [num(col, s) for s in PICKS if s != stem][:7]
    plan = {
        "01_cover.jpg": lambda o: cover(col, n, o),
        "02_before_after.jpg": lambda o: L.before_after(col, n, o),
        "03_print_and_paint.jpg": lambda o: print_and_paint(col, n, o),
        "04_ipad.jpg": lambda o: L.ipad_image(col, n, o),
        "05_closeup.jpg": lambda o: L.closeup_image(col, n, o),
        "06_included.jpg": lambda o: L.included_image(col, n, o, rows=SL.INCLUDED_ROWS),
        "07_palette.jpg": lambda o: L.palette_image(col, n, o),
        "08_how_it_works.jpg": lambda o: L.howto_image(col, n, o, steps=SL.HOWTO_STEPS),
        "09_get_the_book.jpg": lambda o: L.grid_image(col, [n] + others, "LOVE THIS CAR?",
                                                      "Get it with 21 more in the Dream Garage book", o, seed=60 + n),
        "10_good_to_know.jpg": lambda o: L.terms_image(o, rows=SL.TERMS_ROWS),
    }
    for name, fn in plan.items():
        fn(d / name)


# ---------- files and text ----------

def build_files(col, n, d):
    """Same 5 files as the other singles: PDF, 3 numbered PNGs and a Procreate kit ZIP."""
    src = col.dirs[n - 1]
    base = col.names[n].replace(" ", "_").replace("'", "")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    out = [d / f"1_{base}_A4_Print.pdf", d / f"2_{base}_Dark_Numbered.png",
           d / f"3_{base}_Light_Numbered.png", d / f"4_{base}_With_Palette.png", d / f"5_{base}_Procreate_Kit.zip"]
    shutil.copy(next((src / "PDF").glob("*_A4.pdf")), out[0])
    shutil.copy(src / "PNG" / "Dark_Numbered.png", out[1])
    shutil.copy(src / "PNG" / "Light_Numbered.png", out[2])
    shutil.copy(src / "PNG" / "Palette_Numbered.png", out[3])
    tmp = d / "_contour.png"
    Image.open(src / "PNG" / "Contour.png").convert("L").save(tmp, optimize=True)
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
        z.writestr("READ_ME.txt", SL.README)
    tmp.unlink()
    for f in out:
        if f.stat().st_size > SL.MAX_FILE:
            raise SystemExit(f"{f.name} is {f.stat().st_size / 1e6:.1f} MB, over Etsy's 20 MB limit")
    return out


def listing_text(col, n, stem):
    info = PICKS[stem]
    regions, colors = col.stats[n]
    tags = CORE + info["tags"]
    assert len(tags) == 13 and len(set(tags)) == 13 and all(len(t) <= 20 for t in tags), (stem, tags)
    assert len(info["title"]) <= 140, (stem, len(info["title"]))
    desc = f"""{info['blurb']}

Paint this {col.names[n]} design on your iPad in Procreate, or print it at home and paint with markers, colored pencils or paint. Level: {level(regions)}, with about {round(regions, -1):,} numbered zones and {colors} colors. The numbers and lines are light gray, so they disappear under your paint. Tiny details like headlights, taillights and chrome trim come already colored.

A great gift for a car lover, a dad, a boyfriend or anyone who loves cars.

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

LOVE IT? GET THE WHOLE GARAGE
This car is part of my Dream Garage book: 22 JDM, muscle, classic and supercar paint by number pages from beginner to expert.
{BOOK_URL}

PLEASE NOTE
- This is a digital download. No physical item will be shipped.
- Colors can look slightly different on screens and printers.
- For personal use only. Please don't share or resell the files.

Questions? Send me a message any time."""
    return dict(title=info["title"], tags=tags, description=desc, price=PRICE)


# ---------- commands ----------

def build(stems):
    import make_coloring_video as V
    col = collection()
    V.NAMES.update(col.names)
    for stem in stems:
        n = num(col, stem)
        d = OUT / stem
        text = listing_text(col, n, stem)
        files = build_files(col, n, d / "files")
        build_photos(col, n, stem, d / "photos")
        video = d / "video" / "paint_by_number_video.mp4"
        if not video.exists():
            V.build(col, n, video.parent, pages=1, out_name=video.name)
        (d / "listing.json").write_text(json.dumps(text, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"built {stem}: " + ", ".join(f"{f.stat().st_size / 1e6:.1f}MB" for f in files), flush=True)


def upload(stems):
    import etsy_api as e
    sid = e.get_token()["shop_id"]
    state_file = OUT / "uploaded.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    sections = {s["title"]: s["shop_section_id"] for s in e.request("GET", f"/shops/{sid}/sections")["results"]}
    section_id = sections[MB.CAR_SECTION]
    for stem in stems:
        d = OUT / stem
        if stem in state:
            print(f"skip {stem}: already uploaded as {state[stem]}")
            continue
        text = json.loads((d / "listing.json").read_text(encoding="utf-8"))
        listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
            "quantity": 999, "title": text["title"], "description": text["description"], "price": text["price"],
            "who_made": "i_did", "when_made": "2020_2026", "taxonomy_id": 339, "type": "download",
            "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(text["tags"]),
            "shop_section_id": section_id,
        })
        lid = listing["listing_id"]
        state[stem] = lid
        state_file.write_text(json.dumps(state, indent=2))
        for rank, p in enumerate(sorted((d / "photos").glob("*.jpg")), 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
        for rank, p in enumerate(sorted((d / "files").iterdir()), 1):
            e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": p.name},
                      files={"file": p})
        e.request("POST", f"/shops/{sid}/listings/{lid}/videos", form={"name": "paint by number video"},
                  files={"video": d / "video" / "paint_by_number_video.mp4"})
        print(f"uploaded {stem} -> draft {lid}", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    stems = sys.argv[2:] or list(PICKS)
    {"build": build, "upload": upload}[cmd](stems)
