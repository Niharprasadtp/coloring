"""Rate candidate pictures for color-by-code: how many spaces get a problem, how many come pre-colored,
how many colors. Writes ../output/learn_color/scores.tsv and a contact sheet of the answer keys.

    ../.venv/Scripts/python.exe score_pictures.py
"""
from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import color_by_code as cbc

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "learn_color"
IB = ROOT / "input_books"
CANDIDATES = (
    [IB / "book1" / f for f in ("01_snowman", "02_christmas_wreath", "03_sleepy_puppy_stocking", "04_red_vintage_truck",
                                "05_santa_sleigh", "11_penguin_hot_cocoa", "12_two_red_cardinals",
                                "13_mug_hot_cocoa_mitten", "14_husky_puppy_snow", "16_polar_bear_mother_cub",
                                "17_children_building_snowman")]
    + [IB / "book2" / f for f in ("21_baby_fawn_wildflowers", "22_red_squirrel_acorn", "23_chipmunk_autumn_leaves",
                                  "24_red_panda_maple_branch", "25_kingfisher_forest_stream", "26_raccoon_hollow_log",
                                  "31_golden_retriever_puppy", "32_fluffy_white_kitten_basket", "33_pug_knitted_sweater",
                                  "34_two_kittens_yarn", "35_corgi_among_tulips", "37_beagle_puppy_bicycle_basket",
                                  "40_black_cat_pumpkins_porch")]
    + [IB / "book3" / f for f in ("42_bumblebee_pink_peony", "58_treehouse_hideaway")]
    + [IB / "cars" / f for f in ("01_split_window_camper_van", "02_classic_bubble_car", "03_little_london_city_car",
                                 "04_1950s_christmas_pickup", "05_safari_offroader")]
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    W, H = letter
    rows, thumbs = [], []
    for stem in CANDIDATES:
        path = stem.with_suffix(".png")
        if not path.exists():
            print("missing", path)
            continue
        pic = cbc.prepare(path, W, H)
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        st = cbc.worksheet(c, pic, "add10", 1, W, H, "test")
        c.showPage()
        cbc.answer_picture(c, pic, 0, 0, W, H)
        c.showPage()
        c.save()
        doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
        thumbs.append((path.stem, st, Image.open(io.BytesIO(doc[1].get_pixmap(dpi=28).tobytes("png"))).convert("RGB"),
                       Image.open(io.BytesIO(doc[0].get_pixmap(dpi=28).tobytes("png"))).convert("RGB")))
        row = (path.parent.name + "/" + path.stem, st["spaces"], st["prefill"], len(st["coded"]), st["problems"])
        rows.append(row)
        print("\t".join(map(str, row)), flush=True)
    (OUT / "scores.tsv").write_text("picture\tspaces\tprefilled\tcolors\tproblems\n" +
                                    "\n".join("\t".join(map(str, r)) for r in rows), encoding="utf-8")
    tw, th = thumbs[0][2].size
    cols = 6
    sheet = Image.new("RGB", (cols * tw * 2, ((len(thumbs) + cols - 1) // cols) * (th + 24)), "white")
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("arial.ttf", 13)
    for k, (name, st, key, ws) in enumerate(thumbs):
        x, y = (k % cols) * tw * 2, (k // cols) * (th + 24)
        sheet.paste(key, (x, y + 20))
        sheet.paste(ws, (x + tw, y + 20))
        d.text((x + 3, y + 2), f"{k + 1}. {name[:22]} s{st['spaces']} p{st['prefill']} c{len(st['coded'])}", fill="black", font=f)
    sheet.save(OUT / "scores_sheet.jpg", quality=85)
    print("done", OUT / "scores.tsv")


if __name__ == "__main__":
    main()
