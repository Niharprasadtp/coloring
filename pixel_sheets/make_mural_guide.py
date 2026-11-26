"""Teacher guide PDF for the Winter Class Mystery Mural bundle."""
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import make_guide as G            # fonts, header/footer/paragraph/draw_img helpers
import make_mural as MM
import mural as M
import mural_designs as MD
import mural_render as MR
import questions as Q

W, H = letter
INK, SOFT, RED, GREEN, BLUE = G.INK, G.SOFT, G.RED, G.GREEN, HexColor("#1A5FD0")
OUT = MM.OUT / "Teacher_Guide_Class_Mystery_Mural.pdf"
IMG = MM.OUT / "previews"


def footer(c, n):
    c.setFillColor(SOFT); c.setFont("Arial", 8)
    c.drawCentredString(W / 2, 24, f"Winter Class Mystery Mural  •  for classroom use only  •  page {n}")


def mural_png(name, frac=None, tiles=False):
    IMG.mkdir(parents=True, exist_ok=True)
    p = IMG / f"{name}_{'full' if frac is None else int(frac * 100)}{'_tiles' if tiles else ''}.png"
    if not p.exists():
        m = MM.murals()[(name, "Multiplication")]
        rev = None if frac is None else MR.class_progress(m, frac)
        MR.image(m, rev, cell=20, tiles=tiles).save(p)
    return p


def main():
    links = json.loads((MM.OUT / "links.json").read_text())
    murals = MM.murals()
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Winter Class Mystery Mural - Teacher Guide")
    n = 1

    # cover
    c.setFillColor(HexColor("#EAF2FB")); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(HexColor("#1B2A4A")); c.rect(0, H - 130, W, 130, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF")); c.setFont("ArialB", 30)
    c.drawCentredString(W / 2, H - 66, "Winter Class Mystery Mural")
    c.setFont("Arial", 14)
    c.drawCentredString(W / 2, H - 98, "A whole-class, self-checking math activity for Google Sheets")
    G.draw_img(c, mural_png("winter_cabin"), 70, H - 470, W - 140, 320)
    for i, name in enumerate(["penguin_party", "forest_friends"]):
        G.draw_img(c, mural_png(name), 70 + i * 245, H - 615, 225, 145)
    c.setFillColor(INK); c.setFont("ArialB", 12)
    c.drawString(70, 140, "What's inside")
    G.paragraph(c, "• 3 winter murals x 4 skills (multiplication, division, addition, subtraction) = 12 class workbooks\n"
                   "• Up to 30 students per mural, 16 questions each (480 questions per mural)\n"
                   "• Teacher Dashboard with names, live scores and progress bars\n"
                   "• Answer keys for every student in every workbook (this guide)", 70, 122, W - 140, size=10.5, lead=15)
    footer(c, n); c.showPage(); n += 1

    # how it works
    G.header(c, "How the Class Mural works", "Everyone solves their own questions. The whole class builds one picture.")
    G.draw_img(c, mural_png("winter_cabin", tiles=True), 50, H - 390, 250, 260)
    G.paragraph(c, "The mural is split into 30 tiles, one per student (red lines). Student 1 owns the top-left "
                   "tile, Student 30 the bottom-right one.\n\nEvery correct answer reveals part of that student's "
                   "tile on the Class Mural tab, which you show on the board. Wrong answers reveal nothing.\n\n"
                   "Students see a green check or a red X, their own score, and a live preview of their tile on "
                   "their own tab.", 320, H - 150, W - 370, size=10.5, lead=15)
    c.setFillColor(RED); c.setFont("ArialB", 13); c.drawString(50, H - 420, "The tabs in each workbook")
    c.setFillColor(INK)
    G.paragraph(c, "• Class Mural: the big picture and the class progress. Project this tab.\n"
                   "• Teacher Dashboard: student names, scores, progress bars and the reveal switches.\n"
                   "• Student 1 to Student 30: one tab per student with 16 questions.\n"
                   "• A hidden tab stores the answers in coded form. Please keep it hidden.",
                50, H - 440, W - 100, size=10.5, lead=16)
    footer(c, n); c.showPage(); n += 1

    # setup
    G.header(c, "Set up in 3 minutes", "Important: the whole class shares ONE spreadsheet")
    y = H - 120
    steps = [
        ("1. Make your copy", "Open a link from the Links pages and click \"Make a copy\". Use a fresh copy for every "
                              "class and every time you run the activity."),
        ("2. Share it with the class", "In Google Classroom, attach your copy and choose \"Students can edit file\". "
                                       "Do NOT choose \"Make a copy for each student\": the mural only fills in when "
                                       "everyone works in the same spreadsheet. (Or click Share and give your students "
                                       "edit access.)"),
        ("3. Give every student a number", "Each student opens their own tab (Student 1, Student 2, ...), types their "
                                           "name in the yellow box at the top, and starts answering."),
        ("4. Show the Class Mural", "Project the Class Mural tab and watch the winter picture appear as answers come in."),
        ("Absent students or fewer than 30?", "On the Teacher Dashboard, type Y in the Reveal column next to any unused "
                                              "tab. That tile is revealed so the mural can still be finished."),
        ("The grand finale", "Type Y in \"Reveal whole mural\" on the Teacher Dashboard to show the full picture."),
        ("Something changed by mistake?", "Use File > Version history in Google Sheets to restore an earlier version."),
        ("Microsoft Excel", "The .xlsx files work in Excel too. For a whole class at once, save the file to OneDrive "
                            "or Teams so students can edit it together."),
    ]
    for title, text in steps:
        c.setFillColor(RED); c.setFont("ArialB", 12.5); c.drawString(50, y, title); y -= 17
        c.setFillColor(INK); y = G.paragraph(c, text, 50, y, W - 100, size=10.5, lead=14) - 10
    footer(c, n); c.showPage(); n += 1

    # links (two pages)
    for skills in (list(Q.GENERATORS)[:2], list(Q.GENERATORS)[2:]):
        G.header(c, "Your Google Sheets links", "Click a link, then \"Make a copy\"")
        y = H - 125
        for skill in skills:
            c.setFillColor(INK); c.setFont("ArialB", 15); c.drawString(50, y, skill); y -= 24
            for name in MM.DESIGNS:
                title = MD.MURALS[name]()["title"]
                url = links[f"{name}|{skill}"]
                c.setFillColor(INK); c.setFont("ArialB", 11.5); c.drawString(66, y, title)
                c.setFillColor(BLUE); c.setFont("Arial", 11.5); c.drawString(250, y, "Make your copy")
                c.linkURL(url, (250, y - 4, 345, y + 12), relative=0)
                c.setFillColor(SOFT); c.setFont("Arial", 7.5); c.drawString(66, y - 13, url)
                y -= 42
            y -= 18
        c.setFillColor(SOFT); c.setFont("Arial", 9.5)
        c.drawString(50, 60, "Excel files: Class_Mural_<Mural>_<Skill>.xlsx in the skill zip files of your download.")
        footer(c, n); c.showPage(); n += 1

    # answer keys: one page per workbook
    for (name, skill), m in murals.items():
        title = MD.MURALS[name]()["title"]
        G.header(c, f"Answer Key: {title}", f"{skill}  •  answers in question order (Q1 to Q16) for each student tab")
        y = H - 112
        c.setFont("ArialB", 8.5); c.setFillColor(SOFT)
        c.drawString(40, y, "Tab")
        for q in range(M.NQ):
            c.drawRightString(118 + q * 30, y, f"Q{q + 1}")
        y -= 4
        for s in range(M.STUDENTS):
            y -= 19.5
            if s % 2 == 0:
                c.setFillColor(HexColor("#F2F4F8")); c.rect(36, y - 5, W - 72, 19.5, stroke=0, fill=1)
            c.setFillColor(INK); c.setFont("ArialB", 8.5); c.drawString(40, y, f"Student {s + 1}")
            c.setFont("Arial", 9)
            for q, (_, a) in enumerate(m.questions[s]):
                c.drawRightString(118 + q * 30, y, a)
        footer(c, n); c.showPage(); n += 1

    # terms
    G.header(c, "Terms of use")
    G.paragraph(c, "Thank you for your purchase! This resource is for one teacher in their own classroom (including "
                   "Google Classroom and other platforms where access is limited to your students). Please do not "
                   "share, resell or post the files or links publicly.\n\nQuestions? Message me on Etsy. A review "
                   "would mean a lot!", 50, H - 110, W - 100)
    footer(c, n); c.showPage()
    c.save()
    print(OUT, n, "pages")


if __name__ == "__main__":
    main()
