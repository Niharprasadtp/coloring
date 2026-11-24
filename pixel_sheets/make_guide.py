"""Teacher guide PDF for the Christmas Math Mystery Pictures bundle.

Links to the Google Sheets copies are read from output/christmas_math_bundle/links.json
({"Multiplication": "https://docs.google.com/spreadsheets/d/<id>/copy", ...}).
"""
import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import designs as D
import make_bundle as B
import pixelsheet as P
import questions as Q

pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("ArialB", "C:/Windows/Fonts/arialbd.ttf"))
W, H = letter
INK, SOFT, RED, GREEN = HexColor("#2B2D42"), HexColor("#5C6070"), HexColor("#C8102E"), HexColor("#1E7B3A")
OUT = B.OUT / "Teacher_Guide_and_Answer_Keys.pdf"
THUMBS = B.OUT / "previews"


def thumb(name: str) -> Path:
    p = THUMBS / f"design_{name}.png"
    if not p.exists():
        P.preview(P.Puzzle("x", D.DESIGNS[name], [("1 + 1 =", "2")]), p, 1.0, cell=20)
    return p


def draw_img(c, path, x, y, max_w, max_h):
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    s = min(max_w / iw, max_h / ih)
    c.drawImage(img, x + (max_w - iw * s) / 2, y + (max_h - ih * s) / 2, iw * s, ih * s)


def header(c, text, sub=None):
    c.setFillColor(RED); c.rect(0, H - 14, W, 14, stroke=0, fill=1)
    c.setFillColor(INK); c.setFont("ArialB", 22); c.drawString(50, H - 62, text)
    if sub:
        c.setFillColor(SOFT); c.setFont("Arial", 11); c.drawString(50, H - 80, sub)


def footer(c, n):
    c.setFillColor(SOFT); c.setFont("Arial", 8)
    c.drawCentredString(W / 2, 24, f"Christmas Math Mystery Pictures  •  for classroom use only  •  page {n}")


def paragraph(c, text, x, y, width, font="Arial", size=11, lead=15):
    c.setFont(font, size)
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            t = (line + " " + word).strip()
            if c.stringWidth(t, font, size) > width:
                c.drawString(x, y, line); y -= lead; line = word
            else:
                line = t
        c.drawString(x, y, line); y -= lead
    return y


def main():
    links = {}
    lp = B.OUT / "links.json"
    if lp.exists():
        links = json.loads(lp.read_text())
    c = canvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("Christmas Math Mystery Pictures - Teacher Guide and Answer Keys")
    page = 1

    # ---- cover
    c.setFillColor(HexColor("#FDF3E7")); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(RED); c.rect(0, H - 120, W, 120, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF")); c.setFont("ArialB", 30)
    c.drawCentredString(W / 2, H - 62, "Christmas Math")
    c.drawCentredString(W / 2, H - 98, "Mystery Pictures")
    c.setFillColor(INK); c.setFont("ArialB", 15)
    c.drawCentredString(W / 2, H - 155, "40 self-checking digital pixel art activities")
    c.setFont("Arial", 12); c.setFillColor(SOFT)
    c.drawCentredString(W / 2, H - 175, "Multiplication  •  Division  •  Addition  •  Subtraction   |   Google Sheets & Excel")
    tw, th = 96, 112
    for i, name in enumerate(B.ORDER):
        x = 50 + (i % 5) * (tw + 8)
        y = H - 330 - (i // 5) * (th + 14)
        c.setFillColor(HexColor("#FFFFFF")); c.roundRect(x, y, tw, th, 6, stroke=0, fill=1)
        draw_img(c, thumb(name), x + 6, y + 6, tw - 12, th - 12)
    c.setFillColor(INK); c.setFont("ArialB", 12)
    c.drawString(50, 300, "What's inside")
    paragraph(c, "• 4 workbooks (one per skill), 10 mystery pictures each, 20 questions per picture\n"
                 "• Students see a green check or red X right away, and a running score\n"
                 "• Every correct answer reveals part of a hidden Christmas picture\n"
                 "• Answer keys and finished pictures for every activity (this guide)",
              50, 280, W - 100, size=12, lead=19)
    footer(c, page); c.showPage(); page += 1

    # ---- how to use
    header(c, "How to use", "Ready in two minutes, no add-ons or extensions needed")
    y = H - 120
    steps = [
        ("Google Sheets / Google Classroom",
         "1. Open a link on the next page and click \"Make a copy\". The copy is saved in your Google Drive.\n"
         "2. In Google Classroom, create an assignment, attach your copy and choose \"Make a copy for each student\".\n"
         "3. Students type each answer in the yellow box and press Enter."),
        ("Microsoft Excel",
         "Open the .xlsx file for the skill you want. Each tab (Picture 1 to Picture 10) is one activity. "
         "Save a copy for each student or class."),
        ("What students see",
         "A green check mark means correct, and that part of the picture appears. A red X means try again: nothing is "
         "revealed until the answer is right. \"Correct: x / 20\" at the top shows progress."),
        ("Tips",
         "• Tab names do not give away the picture, so it stays a mystery until the end.\n"
         "• Answers are whole numbers. Spaces before or after the number are fine.\n"
         "• To reuse an activity, select the yellow answer boxes and press Delete.\n"
         "• The answers are stored on a hidden tab. Please do not share it with students."),
    ]
    for title, text in steps:
        c.setFillColor(RED); c.setFont("ArialB", 13); c.drawString(50, y, title); y -= 20
        c.setFillColor(INK); y = paragraph(c, text, 50, y, W - 100) - 14
    footer(c, page); c.showPage(); page += 1

    # ---- links
    header(c, "Your Google Sheets links", "Click a link, then \"Make a copy\"")
    y = H - 130
    for topic in Q.GENERATORS:
        c.setFillColor(INK); c.setFont("ArialB", 14); c.drawString(50, y, f"Christmas {topic} Mystery Pictures")
        url = links.get(topic)
        c.setFont("Arial", 11)
        if url:
            c.setFillColor(HexColor("#1A5FD0")); c.drawString(50, y - 18, "Click here to make your copy")
            c.linkURL(url, (50, y - 22, 260, y - 6), relative=0)
            c.setFillColor(SOFT); c.setFont("Arial", 8); c.drawString(50, y - 32, url)
        else:
            c.setFillColor(SOFT); c.drawString(50, y - 18, "Use the Excel file for this skill (included in your download).")
        y -= 60
    c.setFillColor(SOFT)
    paragraph(c, "Excel files are included in your download as well: Christmas_<Skill>_Mystery_Pictures.xlsx", 50, y, W - 100, size=10)
    footer(c, page); c.showPage(); page += 1

    # ---- answer keys: two pictures per page
    for topic in Q.GENERATORS:
        pz = B.puzzles_for(topic)
        for k in range(0, len(pz), 2):
            header(c, f"Answer Key: {topic}", f"Christmas {topic} Mystery Pictures")
            for j, p in enumerate(pz[k:k + 2]):
                top = H - 110 - j * 330
                c.setFillColor(INK); c.setFont("ArialB", 14)
                c.drawString(50, top - 10, f"{p.name}: {p.design['title']}")
                name = B.ORDER[pz.index(p)]
                draw_img(c, thumb(name), 50, top - 300, 190, 270)
                c.setFont("Arial", 11)
                for i, (q, a) in enumerate(p.questions):
                    col, row = divmod(i, 10)
                    x = 270 + col * 150
                    yy = top - 40 - row * 26
                    c.setFillColor(SOFT); c.drawRightString(x + 14, yy, f"{i + 1}.")
                    c.setFillColor(INK); c.drawString(x + 20, yy, q)
                    c.setFont("ArialB", 11); c.setFillColor(GREEN)
                    c.drawString(x + 20 + c.stringWidth(q + " ", "Arial", 11), yy, a)
                    c.setFont("Arial", 11)
            footer(c, page); c.showPage(); page += 1

    # ---- terms
    header(c, "Terms of use")
    paragraph(c, "Thank you for your purchase! This resource is for use by one teacher in their own classroom "
                 "(including Google Classroom and other learning platforms with access limited to your students). "
                 "Please do not share, resell or post the files or links publicly. Additional licenses are welcome "
                 "for colleagues.\n\nIf you have any questions, message me on Etsy. A review would mean a lot!",
              50, H - 110, W - 100)
    footer(c, page); c.showPage()
    c.save()
    print(OUT, page, "pages")


if __name__ == "__main__":
    main()
