"""Color-by-code math bundle: the same 10 pictures at 4 skill levels, so a teacher can give the whole
class the same picture at different levels.

    ../.venv/Scripts/python.exe make_bundle.py        # -> ../output/learn_color/bundle/

Each skill PDF: teacher page, 10 worksheets, answer keys (4 per page). Letter PDFs plus an A4 zip.
Every worksheet is verified while it is drawn (color_by_code.worksheet raises on any wrong answer).
"""
from __future__ import annotations

import zipfile
from pathlib import Path

from reportlab.lib.colors import Color, black
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas

import color_by_code as cbc

ROOT = Path(__file__).resolve().parent.parent
IB = ROOT / "input_books"
OUT = ROOT / "output" / "learn_color" / "bundle"
BRAND = "SpellbindinTreasures"

# Chosen with score_pictures.py: bold shapes, 25-70 spaces, few pre-colored bits, kid-friendly subjects.
PICTURES = [IB / p for p in (
    "book1/11_penguin_hot_cocoa.png", "book2/22_red_squirrel_acorn.png", "cars/01_split_window_camper_van.png",
    "book1/01_snowman.png", "book3/42_bumblebee_pink_peony.png", "book2/23_chipmunk_autumn_leaves.png",
    "cars/04_1950s_christmas_pickup.png", "book1/12_two_red_cardinals.png", "cars/02_classic_bubble_car.png",
    "book1/03_sleepy_puppy_stocking.png")]
# Left out: muted autumn scenes (raccoon, corgi, beagle, black cat) turn into brown-and-tan mush once
# snapped to crayon colors.

LEVELS = [  # skill, file name, grade line
    ("add10", "Addition_to_10", "Kindergarten - Grade 1"),
    ("sub10", "Subtraction_within_10", "Kindergarten - Grade 1"),
    ("mult", "Multiplication", "Grades 3 - 4"),
    ("div", "Division", "Grades 3 - 4"),
]
GREY = Color(0.45, 0.45, 0.45)


def teacher_page(c, W, H, skill, grade, n):
    name = cbc.SKILLS[skill]
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W / 2, H - 110, "Color by Code")
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(W / 2, H - 145, f"{name}  ·  {n} Mystery Pictures")
    c.setFont("Helvetica", 14)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, H - 170, grade)
    c.setFillColor(black)
    lines = [
        "HOW IT WORKS",
        "Every space in the picture holds a math problem. Students solve it, find the answer",
        "in the color key at the bottom of the page and color the space with that crayon.",
        "The picture only comes out right when the answers are right, so the sheet checks itself.",
        "",
        "WHAT YOU NEED",
        "Plain crayons or colored pencils. Every color is a standard crayon color, and its",
        "name is printed in the key (RED, ORANGE, BROWN, LIGHT BLUE ...).",
        "",
        "TIPS",
        "- Small parts that are too tiny to hold a problem are already colored in.",
        "- Spaces without a problem stay white.",
        "- The same 10 pictures come in 4 levels: Addition to 10, Subtraction within 10,",
        "  Multiplication and Division. Give the whole class the same picture at different levels.",
        "- Answer keys (the finished pictures) are at the end of this file.",
        "- Use them for early finishers, math centers, homework, sub plans or a calm Friday.",
        "",
        "TERMS OF USE",
        "For use in your own classroom or home. Copy as many as you need for your students.",
        "Please don't share the file, upload it to other sites or resell it.",
    ]
    y = H - 230
    for ln in lines:
        bold = ln.isupper() and ln
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 13 if bold else 12)
        c.drawString(72, y, ln)
        y -= 26 if bold else 19
    c.setFont("Helvetica", 10)
    c.setFillColor(GREY)
    c.drawCentredString(W / 2, 40, f"© {BRAND} on Etsy")
    c.setFillColor(black)


def answer_pages(c, W, H, pics, stats, name):
    per = 4
    for start in range(0, len(pics), per):
        c.setFont("Helvetica-Bold", 22)
        c.drawString(36, H - 56, f"Answer Keys: {name}")
        c.setLineWidth(0.8)
        c.line(36, H - 66, W - 36, H - 66)
        cell_w, cell_h = (W - 72) / 2, (H - 120) / 2
        for k, idx in enumerate(range(start, min(start + per, len(pics)))):
            col, row = k % 2, k // 2
            x = 36 + col * cell_w
            y = H - 80 - (row + 1) * cell_h
            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x + 8, y + cell_h - 16, f"Picture {idx + 1}")
            cbc.answer_picture(c, pics[idx], x + 8, y + 40, cell_w - 16, cell_h - 62)
            c.setFillColor(black)            # answer_picture leaves the last crayon color set
            st = stats[idx]
            key = "   ".join(f"{st['answers'][ci]} = {cbc.CRAYONS[ci][0]}"
                             for ci in sorted(st["coded"], key=lambda ci: st["answers"][ci]))
            c.setFont("Helvetica", cbc.fit_font(key, "Helvetica", cell_w - 16, 9))
            c.drawString(x + 8, y + 22, key)
        c.showPage()


def build_level(skill, fname, grade, size_name, pagesize, folder):
    W, H = pagesize
    pics = [cbc.prepare(p, W, H) for p in PICTURES]
    name = cbc.SKILLS[skill]
    pdf = folder / f"Color_by_Code_{fname}_{size_name}.pdf"
    c = canvas.Canvas(str(pdf), pagesize=pagesize)
    c.setTitle(f"Color by Code: {name}")
    c.setAuthor(BRAND)
    teacher_page(c, W, H, skill, grade, len(pics))
    c.showPage()
    stats = []
    for i, pic in enumerate(pics, 1):
        stats.append(cbc.worksheet(c, pic, skill, i, W, H, f"Color by Code: {name}",
                                   page_label=f"Mystery Picture {i} of {len(pics)}  ·  {grade}"))
        c.showPage()
    answer_pages(c, W, H, pics, stats, name)
    c.save()
    probs = sum(s["problems"] for s in stats)
    print(f"{pdf.name}: {len(pics)} worksheets, {probs} problems, all verified "
          f"({pdf.stat().st_size / 1e6:.1f} MB)", flush=True)
    return pdf


def main():
    assert len(PICTURES) == 10, "pick the 10 pictures first (score_pictures.py)"
    OUT.mkdir(parents=True, exist_ok=True)
    a4_dir = OUT / "a4"
    a4_dir.mkdir(exist_ok=True)
    for skill, fname, grade in LEVELS:
        build_level(skill, fname, grade, "Letter", letter, OUT)
    a4 = [build_level(skill, fname, grade, "A4", A4, a4_dir) for skill, fname, grade in LEVELS]
    z = OUT / "Color_by_Code_All_4_Levels_A4.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in a4:
            zf.write(p, p.name)
    print(f"{z.name} ({z.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
