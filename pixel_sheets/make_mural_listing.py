"""Etsy listing for the Winter Class Mystery Mural bundle.

    python make_mural_listing.py photos | text | video | upload | update
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import hero as HR
import make_listing as L
import make_mural as MM
import mural as M
import mural_designs as MD
import mural_render as MR
import questions as Q
import render as R

OUT = MM.OUT / "listing"
PHOTOS = OUT / "photos"
W, H = L.W, L.H
RED, GREEN, GOLD, INK, SOFT, NAVY = L.RED, L.GREEN, L.GOLD, L.INK, L.SOFT, (27, 42, 74)
PRICE = 899
f = R.font


def fit_up(img, w, h, pixel=False):
    """Scale to fit inside w x h, enlarging if needed."""
    k = min(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))),
                      Image.NEAREST if pixel else Image.LANCZOS)


def mural(name="winter_cabin", skill="Multiplication"):
    return MM.murals()[(name, skill)]


def window(content, tab):
    return R.sheets_window(content, "Class Mural - Winter Cabin Night", tab, labels=MR.TABS)


def laptop_mural(frac, width, absent=(24,), name="winter_cabin"):
    m = mural(name)
    rev = None if frac >= 1 else MR.class_progress(m, frac, absent=absent)
    return R.laptop(window(MR.mural_tab(m, rev), 0), width)


def mural_card(name, w, frac=None, label=None):
    m = mural(name)
    rev = None if frac is None else MR.class_progress(m, frac)
    pic = L.fit(MR.image(m, rev, cell=16, gap=1), w - 40, w)
    hh = pic.height + 40 + (70 if label else 0)
    c = Image.new("RGB", (w, hh), "white")
    c.paste(pic, ((w - pic.width) // 2, 20))
    if label:
        ImageDraw.Draw(c).text((w / 2, hh - 45), label, font=f("sb", 40), fill=INK, anchor="mm")
    return c


# ------------------------------------------------------------------ photos

def p01_hero(out):
    im = HR.wood_desk(seed=9)
    HR.fairy_lights(im, seed=4)
    HR.ornament(im, 120, 1780, 170, (190, 20, 40), blur=7)
    HR.ornament(im, 380, 1930, 110, (214, 170, 60), blur=8)
    HR.ornament(im, W - 150, 1760, 180, (30, 110, 60), blur=7)
    for name, ang, x, y in [("penguin_party", -8, 2010, 520), ("forest_friends", 7, 2080, 960)]:
        c = mural_card(name, 520).convert("RGBA").rotate(ang, expand=True, resample=Image.BICUBIC)
        R.shadow(im, c, (x, y), blur=18, offset=(8, 16), alpha=0.4)
    lap = laptop_mural(0.62, 1800)
    lx, ly = (W - lap.width) // 2, 430
    R.shadow(im, lap, (lx, ly), blur=34, offset=(0, 34), alpha=0.5)
    d = ImageDraw.Draw(im)
    rib = Image.new("RGBA", (1700, 330), (255, 249, 240, 255))
    R.shadow(im, rib, ((W - 1700) // 2, 60), blur=20, offset=(0, 14), alpha=0.35, radius=60)
    d.text((W // 2, 98), "CLASS MYSTERY MURAL", font=f("bl", 128), fill=RED, anchor="mt")
    d.text((W // 2, 276), "Winter Math for the Whole Class", font=f("b", 80), fill=INK, anchor="mt")
    # zoom bubble: three dashboard rows
    rows = [("Ava", 14), ("Liam", 11), ("Mia", 16)]
    bw, rh = 640, 104
    b = Image.new("RGB", (bw, rh * 3 + 30), "white")
    bd = ImageDraw.Draw(b)
    for k, (nm, sc) in enumerate(rows):
        y = 15 + k * rh
        bd.text((26, y + rh // 2), nm, font=f("b", 58), fill=INK, anchor="lm")
        bd.rounded_rectangle([190, y + rh // 2 - 18, 190 + 260, y + rh // 2 + 18], 10, fill=(228, 232, 238))
        bd.rounded_rectangle([190, y + rh // 2 - 18, 190 + int(260 * sc / 16), y + rh // 2 + 18], 10, fill=GREEN)
        bd.text((bw - 26, y + rh // 2), f"{sc}/16", font=f("b", 52), fill=GREEN, anchor="rm")
    m_ = Image.new("L", b.size, 0)
    ImageDraw.Draw(m_).rounded_rectangle([0, 0, b.width - 1, b.height - 1], 40, fill=255)
    bub = Image.new("RGBA", (b.width + 24, b.height + 24), (0, 0, 0, 0))
    ImageDraw.Draw(bub).rounded_rectangle([0, 0, bub.width - 1, bub.height - 1], 52, fill=NAVY + (255,))
    bb = b.convert("RGBA"); bb.putalpha(m_)
    bub.paste(bb, (12, 12), bb)
    bx, by = HR.SAFE_X0 + 10, 980
    R.shadow(im, bub, (bx, by), blur=22, offset=(0, 18), alpha=0.45, radius=52)
    d = ImageDraw.Draw(im)
    HR.curved_arrow(d, (bx + bub.width - 40, by - 10), (bx + bub.width + 60, by - 250),
                    (bx + bub.width + 320, by - 230), (255, 200, 40), width=24)
    txt = "Google Sheets  •  Self-Checking  •  Up to 30 Students"
    tw = d.textlength(txt, font=f("b", 56))
    px0, py0 = (W - tw) / 2 - 60, 1600
    d.rounded_rectangle([px0, py0, px0 + tw + 120, py0 + 116], 58, fill=GREEN, outline="white", width=6)
    d.text((W // 2, py0 + 58), txt, font=f("b", 56), fill="white", anchor="mm")
    im.save(out, quality=93)


def p02_overview(out):
    im = L.bg(21)
    d = ImageDraw.Draw(im)
    L.ctext(d, 80, "30 Students. 1 Mystery Picture.", 118, RED)
    L.ctext(d, 245, "Every right answer reveals part of a giant winter mural on your board", 56, INK, "sb")
    for i, name in enumerate(MM.DESIGNS):
        c = mural_card(name, 760, label=MD.MURALS[name]()["title"])
        L.card(im, (130 + i * 820, 420, 130 + i * 820 + c.width, 420 + c.height))
        im.paste(c, (130 + i * 820, 420))
    y = 1240
    for t in ["One shared Google Sheet for the class", "Teacher Dashboard with live scores",
              "Instant check marks for every answer"]:
        L.check_bullet(d, 200, y, t, size=52); y += 120
    y = 1240
    for t in ["3 winter murals x 4 skills = 12 activities", "Absent students? One click fills their tile",
              "Answer keys for every student"]:
        L.check_bullet(d, 1420, y, t, size=52); y += 120
    x = 560
    for s in Q.GENERATORS:
        x = L.pill(d, x, 1650, s, L.SKILL_COL[s], size=48) + 26
    im.save(out, quality=92)


def p03_how(out):
    im = L.bg(22)
    d = ImageDraw.Draw(im)
    L.ctext(d, 80, "How the Class Mural Works", 116, RED)
    m = mural()
    s_idx = 13
    typed = [a if i < 12 else None for i, (_, a) in enumerate(m.questions[s_idx])]
    typed[4] = str(int(m.questions[s_idx][4][1]) + 1)
    st = MR.student_tab(m, s_idx, typed, row=40)
    panels = [("1", "Each student solves", st.crop((0, 140, 480, st.height - 20))),
              ("2", "Their piece fills in", st.crop((495, 140, 1045, 712))),
              ("3", "The class mural appears!", MR.image(m, MR.class_progress(m, 0.7, absent=(24,)), cell=14, gap=1))]
    cw, gap = 770, 60
    x0 = (W - (3 * cw + 2 * gap)) // 2
    for i, (num, head, img) in enumerate(panels):
        x = x0 + i * (cw + gap)
        L.card(im, (x, 330, x + cw, 1800))
        d.ellipse([x + cw / 2 - 60, 280, x + cw / 2 + 60, 400], fill=[RED, GOLD, GREEN][i])
        d.text((x + cw / 2, 340), num, font=f("bl", 80), fill="white", anchor="mm")
        d.text((x + cw / 2, 470), head, font=f("b", 64), fill=INK, anchor="mm")
        img = fit_up(img, cw - 70, 1150, pixel=(i == 2))
        im.paste(img, (int(x + (cw - img.width) / 2), 580 + (1150 - img.height) // 2))
    im.save(out, quality=92)


def p04_progress(out):
    im = L.bg(23)
    d = ImageDraw.Draw(im)
    L.ctext(d, 90, "Watch Your Class Build It Together", 110, RED)
    L.ctext(d, 250, "Every correct answer anywhere in the room adds more of the picture", 56, INK, "sb")
    m = mural()
    rng = np.random.default_rng(2)
    order = [(s, q) for s in range(M.STUDENTS) for q in range(M.NQ)]
    order = [order[i] for i in rng.permutation(len(order))]
    cw, gap = 470, 40
    x0 = (W - (5 * cw + 4 * gap)) // 2
    for i, fr in enumerate([0.1, 0.3, 0.55, 0.8, 1.0]):
        x = x0 + i * (cw + gap)
        rev = set(order[: round(fr * len(order))])
        pic = L.fit(MR.image(m, rev, cell=10, gap=1), cw - 40, 600)
        L.card(im, (x, 560, x + cw, 560 + pic.height + 160), radius=30)
        im.paste(pic, (x + 20, 580))
        d.text((x + cw / 2, 560 + pic.height + 90), f"{round(fr * 100)}%", font=f("b", 64),
               fill=GREEN if fr == 1 else INK, anchor="mm")
    L.ctext(d, 1300, "The class progress line keeps everyone cheering:", 54, INK, "sb")
    L.ctext(d, 1400, "Class progress: 264 / 480 correct answers (55%)", 70, GREEN, "b")
    L.ctext(d, 1600, "Wrong answers reveal nothing, so the picture only grows with real understanding.", 46, SOFT, "sb")
    im.save(out, quality=92)


def p05_dashboard(out):
    im = L.bg(24)
    d = ImageDraw.Draw(im)
    L.ctext(d, 80, "Teacher Dashboard", 120, RED)
    L.ctext(d, 245, "See every student's progress live, no grading needed", 56, INK, "sb")
    m = mural()
    rev = MR.class_progress(m, 0.6, absent=(24,))
    dash = MR.dashboard_tab(rev, absent={24}, rows=30)
    rh = 28
    top = dash.crop((0, 0, dash.width, 100 + rh * 15 + 6))
    absent_row = dash.crop((0, 100 + rh * 25, dash.width, 100 + rh * 26 + 4))
    shot = Image.new("RGB", (dash.width, top.height + absent_row.height + 30), "white")
    shot.paste(top, (0, 0))
    ImageDraw.Draw(shot).text((dash.width // 2, top.height + 6), "...", font=f("b", 20), fill=SOFT, anchor="mt")
    shot.paste(absent_row, (0, top.height + 30))
    shot = fit_up(shot, 1900, 1050)
    x0 = (W - shot.width) // 2
    L.card(im, (x0 - 30, 380, x0 + shot.width + 30, 410 + shot.height + 30))
    im.paste(shot, (x0, 410))
    y = 1560
    xs = [180, 980, 1780]
    for i, t in enumerate(["Live names & scores", "Absent? Type Y", "Y = reveal whole mural"]):
        L.check_bullet(d, xs[i], y, t, size=50)
    L.ctext(d, 1720, "Fewer than 30 students? Type Y next to the empty tabs and their tiles fill in.", 46, SOFT, "sb")
    im.save(out, quality=92)


def p06_murals(out):
    im = L.bg(25)
    d = ImageDraw.Draw(im)
    L.ctext(d, 90, "3 Winter Murals", 120, RED)
    L.ctext(d, 250, "Use one in December, one in January, one in February, or one per class", 54, INK, "sb")
    big = mural_card("winter_cabin", 1240, label="Winter Cabin Night")
    L.card(im, (120, 400, 120 + big.width, 400 + big.height)); im.paste(big, (120, 400))
    for i, name in enumerate(["penguin_party", "forest_friends"]):
        c = mural_card(name, 1100, label=MD.MURALS[name]()["title"])
        x, y = 1440, 400 + i * (c.height + 50)
        L.card(im, (x, y, x + c.width, y + c.height)); im.paste(c, (x, y))
    im.save(out, quality=92)


def p07_student(out):
    im = L.bg(26)
    d = ImageDraw.Draw(im)
    d.text((140, 110), "Every Student Has a Tab", font=f("bl", 112), fill=RED)
    d.text((140, 265), "16 questions, instant checks and a live view of their own piece", font=f("sb", 56), fill=INK)
    m = mural()
    s_idx = 6
    typed = [a if i < 13 else None for i, (_, a) in enumerate(m.questions[s_idx])]
    typed[2] = str(int(m.questions[s_idx][2][1]) + 2)
    st = MR.student_tab(m, s_idx, typed, row=52)
    st = fit_up(st, 2300, 1420)
    L.card(im, ((W - st.width) // 2 - 30, 400, (W + st.width) // 2 + 30, 430 + st.height + 30))
    im.paste(st, ((W - st.width) // 2, 430))
    im.save(out, quality=92)


def p08_setup(out):
    im = L.bg(27)
    d = ImageDraw.Draw(im)
    L.ctext(d, 90, "Ready in 3 Minutes", 120, RED)
    steps = [("Make a copy", "Click your link in the\nTeacher Guide and choose\n\"Make a copy\""),
             ("Share with the class", "In Google Classroom pick\n\"Students can edit file\"\n(one shared sheet)"),
             ("Project the mural", "Each student opens their\nown tab. Watch the picture\nappear on the board!")]
    cw, gap = 720, 80
    x0 = (W - (3 * cw + 2 * gap)) // 2
    for i, (head, sub) in enumerate(steps):
        x = x0 + i * (cw + gap)
        L.card(im, (x, 330, x + cw, 1270))
        d.ellipse([x + cw / 2 - 95, 400, x + cw / 2 + 95, 590], fill=[RED, GOLD, GREEN][i])
        d.text((x + cw / 2, 495), str(i + 1), font=f("bl", 120), fill="white", anchor="mm")
        d.text((x + cw / 2, 700), head, font=f("b", 64), fill=INK, anchor="mm")
        d.multiline_text((x + cw / 2, 960), sub, font=f("sb", 48), fill=SOFT, anchor="mm", align="center", spacing=18)
    L.card(im, (300, 1420, W - 300, 1780), fill=(232, 245, 234))
    L.ctext(d, 1470, "Works in Microsoft Excel too", 64, GREEN)
    L.ctext(d, 1580, "Save the .xlsx to OneDrive or Teams so the class can edit it together", 48, INK, "sb")
    L.ctext(d, 1665, "Step-by-step guide included", 44, SOFT, "sb")
    im.save(out, quality=92)


def p09_included(out):
    im = L.bg(28)
    d = ImageDraw.Draw(im)
    L.ctext(d, 90, "What's Included", 120, RED)
    L.card(im, (300, 320, W - 300, 1730))
    rows = [("xlsx", f"{s}: 3 class murals", "30 student tabs each, 16 questions per student") for s in Q.GENERATORS]
    rows += [("pdf", "Teacher Guide (18 pages)", "Setup steps, 12 Google Sheets links, answer keys for every student"),
             ("link", "12 Google Sheets \"Make a copy\" links", "Inside the Teacher Guide")]
    y = 390
    for kind, head, sub in rows:
        L.file_icon(d, 400, y, kind)
        d.text((570, y + 45), head, font=f("b", 58), fill=INK, anchor="lm")
        d.text((570, y + 115), sub, font=f("sb", 42), fill=SOFT, anchor="lm")
        y += 215
    L.ctext(d, 1800, "Instant digital download  •  Nothing will be shipped", 52, GREEN, "b")
    im.save(out, quality=92)


def p10_teacher(out):
    im = L.bg(29)
    d = ImageDraw.Draw(im)
    L.ctext(d, 80, "Make Math a Class Event", 120, RED)
    L.ctext(d, 250, "Change the way your class practices math this winter", 60, INK, "pr")
    benefits = [("Everyone matters", "Every student's piece\nis needed to finish it"),
                ("No grading", "The sheet checks every\nanswer for you"),
                ("Real teamwork", "Kids cheer each other\non to complete the mural"),
                ("Zero prep", "Copy, share, project.\nThat's it.")]
    cw, chh = 1100, 470
    for i, (head, sub) in enumerate(benefits):
        x, y = 190 + (i % 2) * (cw + 87), 430 + (i // 2) * (chh + 60)
        L.card(im, (x, y, x + cw, y + chh))
        col = [RED, GREEN, GOLD, (47, 111, 214)][i]
        d.ellipse([x + 60, y + 70, x + 200, y + 210], fill=col)
        d.text((x + 130, y + 142), "✓", font=f("sym", 96), fill="white", anchor="mm")
        d.text((x + 250, y + 140), head, font=f("b", 70), fill=INK, anchor="lm")
        d.multiline_text((x + 250, y + 250), sub, font=f("sb", 50), fill=SOFT, spacing=16)
    d.rounded_rectangle([330, 1540, W - 330, 1800], 60, fill=RED)
    L.ctext(d, 1585, "Be the teacher they remember!", 84, (255, 255, 255), "pr")
    L.ctext(d, 1710, "The winter math activity your whole class will talk about", 46, (255, 236, 236), "sb")
    im.save(out, quality=92)


def p11_guide(out):
    im = L.bg(30)
    d = ImageDraw.Draw(im)
    L.ctext(d, 90, "18-Page Teacher Guide", 116, RED)
    L.ctext(d, 250, "Setup steps, all 12 links, and an answer key for every student", 54, INK, "sb")
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(MM.OUT / "Teacher_Guide_Class_Mystery_Mural.pdf"))
    pages = [pdf[i].render(scale=1.2).to_pil().convert("RGB") for i in (2, 5, 0)]
    for pg, ang, x, y in zip(pages, [7, -7, 0], [230, 1560, 900], [560, 560, 420]):
        pg = L.fit(pg, 820, 1060).convert("RGBA").rotate(ang, expand=True, resample=Image.BICUBIC)
        R.shadow(im, pg, (x, y), blur=22, offset=(0, 18), alpha=0.3)
    im.save(out, quality=92)


def p12_uses(out):
    im = L.bg(31)
    d = ImageDraw.Draw(im)
    L.ctext(d, 90, "Perfect For", 120, RED)
    uses = ["Last day before winter break", "Fun Friday math", "Fact fluency review", "Indoor recess",
            "Sub plans", "Back-to-school in January", "Computer lab time", "Whole-class rewards"]
    cw, chh = 1050, 230
    for i, u in enumerate(uses):
        x, y = 230 + (i % 2) * (cw + 110), 360 + (i // 2) * (chh + 60)
        L.card(im, (x, y, x + cw, y + chh), radius=40)
        d.ellipse([x + 50, y + chh / 2 - 45, x + 140, y + chh / 2 + 45], fill=[RED, GREEN, GOLD, (47, 111, 214)][i % 4])
        d.text((x + 95, y + chh / 2 + 2), "✓", font=f("sym", 60), fill="white", anchor="mm")
        d.text((x + 180, y + chh / 2), u, font=f("b", 60), fill=INK, anchor="lm")
    L.ctext(d, 1560, "Grades 2-5  •  Up to 30 students  •  Google Sheets & Excel", 52, INK, "sb")
    L.ctext(d, 1660, "Digital download. A free Google account or Microsoft Excel is needed.", 46, SOFT, "sb")
    im.save(out, quality=92)


PHOTO_FUNCS = [p01_hero, p02_overview, p03_how, p04_progress, p05_dashboard, p06_murals, p07_student,
               p08_setup, p09_included, p10_teacher, p11_guide, p12_uses]


def photos(only=None):
    PHOTOS.mkdir(parents=True, exist_ok=True)
    for i, fn in enumerate(PHOTO_FUNCS, 1):
        if only and str(i) not in only:
            continue
        o = PHOTOS / f"{i:02d}_{fn.__name__.split('_', 1)[1]}.jpg"
        fn(o)
        print(o.name, flush=True)


if __name__ == "__main__" and sys.argv[1:2] == ["photos"]:
    photos(sys.argv[2:])


# ------------------------------------------------------------------ text

TITLE = ("Class Mystery Mural, Winter Math Activity for the Whole Class, Self Checking Google Sheets, "
         "Multiplication Division Addition Subtraction")
TAGS = ["class mystery mural", "winter math", "google sheets math", "collaborative math", "whole class activity",
        "mystery picture", "pixel art math", "multiplication game", "division practice", "self checking math",
        "google classroom", "teacher resources", "math centers"]

DESCRIPTION = """Be the teacher they remember this winter!

Turn math practice into a whole-class event. Every student solves their own questions, and every correct answer reveals part of ONE giant winter mural on your board. The class can only finish the picture together, so everyone keeps going and cheers each other on.

★ HOW IT WORKS
• One shared Google Sheet for the whole class (up to 30 students)
• Each student opens their own tab and answers 16 questions
• Green ✓ = correct, and that student's piece of the mural appears
• Red ✗ = try again. Nothing is revealed until the answer is right
• Project the Class Mural tab and watch the winter picture appear live

★ TEACHER DASHBOARD
• Every student's name, score and progress bar, updating live
• Absent student or fewer than 30 in your class? Type Y and that tile fills in
• Type Y in "Reveal whole mural" for the grand finale
• No grading: the sheet checks every answer for you

★ WHAT'S INCLUDED
• 3 winter murals: Winter Cabin Night, Penguin Ice Party and Snowy Forest Friends
• 4 skills for each mural = 12 class activities:
  Multiplication (facts 2-12), Division (up to 144 ÷ 12), Addition (2-digit, totals to 99), Subtraction (2-digit, no negatives)
• 480 questions per activity (16 different questions for each of the 30 student tabs)
• 18-page Teacher Guide with setup steps, 12 Google Sheets "Make a copy" links and an answer key for every student
• Excel files (.xlsx) for every activity

★ WHY TEACHERS LOVE IT
• Everyone matters: every student's piece is needed to finish the mural
• Real teamwork and excitement, without noise or chaos
• Instant feedback, so students fix mistakes right away
• Zero prep: make a copy, share it, project it

★ PERFECT FOR
Last day before winter break, Fun Friday, fact fluency review, indoor recess, sub plans, January back-to-school and whole-class rewards. Best for grades 2-5.

★ HOW TO USE
1. Open the Teacher Guide (PDF) and click the Google Sheets link you want, then "Make a copy"
2. In Google Classroom, attach your copy and choose "Students can edit file" (one shared sheet for the whole class)
3. Give every student a number (Student 1, Student 2, ...) and project the Class Mural tab
Using Excel? Save the .xlsx to OneDrive or Teams so the class can edit it together.

★ GOOD TO KNOW
• This is a DIGITAL DOWNLOAD. Nothing will be shipped
• You need a free Google account (Google Sheets) or Microsoft Excel with OneDrive/Teams
• Works on Chromebooks, laptops and desktops. No add-ons or extensions
• Every activity was checked square by square: correct answers always rebuild the full mural
• Answers are stored in coded form on a hidden tab
• Pixel art and puzzles were made by our shop with the help of digital and AI-assisted tools

★ TERMS OF USE
For one teacher in their own classroom, including Google Classroom and other platforms where access is limited to your students. Please do not share, resell or post the files or links publicly.

Questions? Send me a message on Etsy. I'm happy to help!"""


def text():
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(TITLE) <= 140, len(TITLE)
    assert len(TAGS) == 13 and all(len(t) <= 20 for t in TAGS), [t for t in TAGS if len(t) > 20]
    (OUT / "listing.json").write_text(json.dumps({"title": TITLE, "tags": TAGS, "description": DESCRIPTION,
                                                  "price": PRICE}, indent=2, ensure_ascii=False), encoding="utf-8")
    print("title", len(TITLE), "chars; tags ok")


# ------------------------------------------------------------------ video

def video():
    import subprocess
    import imageio_ffmpeg
    import make_video as V
    VW, VH, FPS, FADE = V.VW, V.VH, V.FPS, V.FADE
    m = mural()
    rng = np.random.default_rng(5)
    order = [(s_, q) for s_ in range(M.STUDENTS) for q in range(M.NQ)]
    order = [order[i] for i in rng.permutation(len(order))]
    bgimg = V.base(6)
    steps = 48
    cache = {}

    def mural_frame(k):
        if k not in cache:
            rev = set(order[: round(k / steps * len(order))])
            lap = R.laptop(window(MR.mural_tab(m, rev), 0), 1500)
            im = bgimg.copy()
            R.shadow(im, lap, ((VW - lap.width) // 2, 140), blur=22, offset=(0, 20), alpha=0.3)
            cache[k] = im
        return cache[k]

    def fill_scene(duration):
        def render(t):
            k = min(steps, int(steps * min(1, t / (duration - 1.0))))
            im = mural_frame(k).copy()
            d = ImageDraw.Draw(im)
            msg = ("30 students solve their own questions..." if t < 2.4 else
                   "...every right answer adds to ONE class picture" if k < steps else "The whole class did it!")
            tw = d.textlength(msg, font=f("b", 54))
            d.rounded_rectangle([(VW - tw) / 2 - 40, 30, (VW + tw) / 2 + 40, 118], 44, fill=RED)
            d.text((VW // 2, 74), msg, font=f("b", 54), fill="white", anchor="mm")
            return np.asarray(im)
        return render

    def murals_scene(duration):
        bg2 = V.base(7)
        cards = [mural_card(n, 560, label=MD.MURALS[n]()["title"]) for n in MM.DESIGNS]

        def render(t):
            im = bg2.copy()
            d = ImageDraw.Draw(im)
            d.text((VW // 2, 60), "3 winter murals x 4 skills = 12 class activities", font=f("b", 64), fill=RED, anchor="mt")
            for i, c in enumerate(cards):
                k = V.ease((t - i * 0.25) / 0.35)
                if k <= 0:
                    continue
                x, y = 70 + i * 610, 230 + int(50 * (1 - k))
                cc = L.fit(c, 560, 700)
                im.paste(cc, (x + (560 - cc.width) // 2, y))
            return np.asarray(im)
        return render

    def end_scene(duration):
        bg3 = V.base(8)

        def render(t):
            im = bg3.copy()
            d = ImageDraw.Draw(im)
            d.text((VW // 2, 190), "Class Mystery Mural", font=f("bl", 120), fill=RED, anchor="mt")
            d.text((VW // 2, 360), "Winter math for the whole class", font=f("b", 76), fill=INK, anchor="mt")
            d.text((VW // 2, 500), "Be the teacher they remember!", font=f("pr", 64), fill=RED, anchor="mt")
            d.text((VW // 2, 660), "Google Sheets  •  Teacher Dashboard  •  Up to 30 students", font=f("sb", 50),
                   fill=GREEN, anchor="mt")
            d.text((VW // 2, 750), "Self-checking  •  Answer keys  •  Instant download", font=f("sb", 50),
                   fill=INK, anchor="mt")
            return np.asarray(im)
        return render

    out = OUT / "video" / "class_mystery_mural.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    scenes = [(7.6, fill_scene(7.6)), (2.8, murals_scene(2.8)), (2.4, end_scene(2.4))]
    starts, t0 = [], 0.0
    for dur, _ in scenes:
        starts.append(t0)
        t0 += dur - FADE
    total = starts[-1] + scenes[-1][0]
    n = round(total * FPS)
    proc = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart",
                             str(out)], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for fr in range(n):
        T = fr / FPS
        i = max(k for k, s0 in enumerate(starts) if s0 <= T)
        dur, rend = scenes[i]
        frame = rend(min(T - starts[i], dur)).astype(np.float32)
        if i > 0 and T - starts[i] < FADE:
            pd, pr = scenes[i - 1]
            a = V.ease((T - starts[i]) / FADE)
            frame = pr(min(T - starts[i - 1], pd)) * (1 - a) + frame * a
        proc.stdin.write(np.ascontiguousarray(frame.astype(np.uint8)).tobytes())
    proc.stdin.close(); proc.wait()
    print(out, f"{total:.1f} s, {out.stat().st_size / 1e6:.1f} MB")


# ------------------------------------------------------------------ upload

def upload():
    e = L.etsy()
    sid = e.get_token()["shop_id"]
    state = OUT / "uploaded.json"
    if state.exists():
        sys.exit(f"already uploaded: {state.read_text()}")
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    sections = {x["title"]: x["shop_section_id"] for x in e.request("GET", f"/shops/{sid}/sections")["results"]}
    listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
        "quantity": 999, "title": t["title"], "description": t["description"], "price": t["price"],
        "who_made": "i_did", "when_made": "2020_2026", "taxonomy_id": L.TAXONOMY, "type": "download",
        "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(t["tags"]),
        "shop_section_id": sections[L.SECTION]})
    lid = listing["listing_id"]
    state.write_text(json.dumps({"listing_id": lid}, indent=2))
    print("draft", lid, flush=True)
    for rank, p in enumerate(sorted(PHOTOS.glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    print("photos uploaded", flush=True)
    files = MM.OUT / "etsy_files"
    order = ["Teacher_Guide_Class_Mystery_Mural.pdf"] + [f"Class_Mystery_Mural_{s}.zip" for s in Q.GENERATORS]
    for rank, name in enumerate(order, 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": name},
                  files={"file": files / name})
    print("5 download files uploaded", flush=True)
    v = OUT / "video" / "class_mystery_mural.mp4"
    e.request("POST", f"/shops/{sid}/listings/{lid}/videos", form={"name": "class mystery mural"}, files={"video": v})
    print("video uploaded", flush=True)
    print(f"https://www.etsy.com/your/shops/me/listing-editor/edit/{lid}")


if __name__ == "__main__" and sys.argv[1:2] != ["photos"]:
    {"text": text, "video": video, "upload": upload}[sys.argv[1]]()
