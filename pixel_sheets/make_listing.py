"""Etsy listing for the Christmas Math Mystery Pictures bundle.

    python make_listing.py photos     -> output/christmas_math_bundle/listing/photos/*.jpg
    python make_listing.py text       -> listing/listing.json (title, tags, description, price)
    python make_listing.py upload     -> Etsy DRAFT with photos, 5 download files, video
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import designs as D
import make_bundle as B
import questions as Q
import render as R

OUT = B.OUT / "listing"
PHOTOS = OUT / "photos"
W, H = 2667, 2000
CREAM = (255, 247, 238)
RED, DRED, GREEN, GOLD, INK, SOFT = (200, 16, 46), (150, 18, 38), (30, 123, 58), (242, 182, 50), (43, 45, 66), (92, 96, 112)
SKILL_COL = {"Multiplication": (200, 16, 46), "Division": (31, 122, 116), "Addition": (30, 123, 58),
             "Subtraction": (122, 70, 160)}
PRICE = 599
TAXONOMY = 12471          # Paper & Party Supplies > Paper > Stationery > Design & Templates > Worksheets
SECTION = "Teacher Resources"
f = R.font


def bg(seed=0):
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(seed)
    for _ in range(90):                                # soft snow dots
        x, y, r = rng.integers(0, W), rng.integers(0, H), int(rng.integers(5, 14))
        col = [(250, 222, 214), (220, 236, 222), (248, 234, 205)][int(rng.integers(0, 3))]
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    d.rectangle([0, 0, W, 26], fill=RED)
    d.rectangle([0, H - 26, W, H], fill=GREEN)
    return im


def ctext(d, y, text, size, fill=INK, style="b", x=W // 2):
    d.text((x, y), text, font=f(style, size), fill=fill, anchor="mt")


def card(im, box, fill=(255, 255, 255), radius=36):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), fill + (255,))
    R.shadow(im, layer, (x0, y0), blur=18, offset=(0, 12), alpha=0.18, radius=radius)


def pill(d, x, y, text, fill, fg="white", size=46, anchor="l"):
    tw = d.textlength(text, font=f("b", size))
    w, h = tw + size * 1.2, size * 1.7
    if anchor == "c":
        x -= w / 2
    d.rounded_rectangle([x, y, x + w, y + h], h / 2, fill=fill)
    d.text((x + w / 2, y + h / 2), text, font=f("b", size), fill=fg, anchor="mm")
    return x + w


def check_bullet(d, x, y, text, size=50, col=GREEN):
    r = size * 0.55
    d.ellipse([x, y, x + 2 * r, y + 2 * r], fill=col)
    d.text((x + r, y + r + 2), "✓", font=f("sym", int(size * 0.8)), fill="white", anchor="mm")
    d.text((x + 2 * r + 26, y + r), text, font=f("sb", size), fill=INK, anchor="lm")


def fit(img, w, h):
    img = img.copy()
    img.thumbnail((w, h), Image.LANCZOS)
    return img


def puzzles(topic="Multiplication"):
    return B.puzzles_for(topic)


def revealed(p, frac, seed=4):
    n = len(p.questions)
    return set(np.random.default_rng(seed).permutation(n)[: round(frac * n)])


def laptop_with(p, k, width, topic="Multiplication", wrong=None, tab=0, cursor=None):
    s = R.sheet(p, R.typed_upto(p, k, wrong), f"Christmas {topic} Mystery Picture", cursor=cursor)
    return R.laptop(R.sheets_window(s, f"Christmas {topic} Mystery Pictures", active_tab=tab), width)


def thumb_card(im, name, x, y, w, h, label=None):
    card(im, (x, y, x + w, y + h), radius=26)
    p = B.P.Puzzle("x", D.DESIGNS[name], [("1 + 1 =", "2")])
    pic = fit(R.picture(p, {0}, cell=24, gap=2), w - 40, h - (100 if label else 40))
    im.paste(pic, (x + (w - pic.width) // 2, y + 20 + (h - (100 if label else 40) - pic.height) // 2))
    if label:
        ImageDraw.Draw(im).text((x + w / 2, y + h - 52), label, font=f("sb", 40), fill=INK, anchor="mm")


# ------------------------------------------------------------------ photos

def p00_hero(out):
    import hero
    hero.make(out)


def p01_overview(out):
    im = bg(1)
    d = ImageDraw.Draw(im)
    d.text((110, 90), "CHRISTMAS MATH", font=f("bl", 150), fill=RED)
    d.text((110, 260), "Mystery Pictures", font=f("b", 132), fill=INK)
    d.text((116, 430), "40 Self-Checking Pixel Art Activities", font=f("sb", 62), fill=GREEN)
    d.text((116, 520), "Be the teacher they remember!", font=f("pr", 58), fill=RED)
    p = puzzles()[0]
    lap = laptop_with(p, 16, 1520, cursor=16)
    R.shadow(im, lap, (1090, 560), blur=30, offset=(0, 30), alpha=0.35)
    y = 660
    for t in ["Google Sheets + Excel", "Instant right / wrong feedback", "Google Classroom ready",
              "Answer keys included", "Grades 2-4, no prep"]:
        check_bullet(d, 120, y, t, size=52)
        y += 122
    # seal
    cx, cy, r = 2440, 250, 175
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD)
    d.ellipse([cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14], outline="white", width=6)
    d.text((cx, cy - 30), "40", font=f("bl", 150), fill=INK, anchor="mm")
    d.text((cx, cy + 82), "ACTIVITIES", font=f("b", 40), fill=INK, anchor="mm")
    # skill pills
    x = 120
    for s in Q.GENERATORS:
        x = pill(d, x, 1310, s, SKILL_COL[s], size=40) + 18
    # thumbnails
    tw, gap = 228, 24
    x0 = (W - (10 * tw + 9 * gap)) // 2
    for i, name in enumerate(B.ORDER):
        thumb_card(im, name, x0 + i * (tw + gap), 1560, tw, 300)
    im.save(out, quality=92)


def p02_how(out):
    im = bg(2)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "How It Works", 120, RED)
    ctext(d, 250, "Students solve, the sheet checks, the picture appears!", 58, INK, "sb")
    p = puzzles()[5]
    full = R.sheet(p, R.typed_upto(p, 15, wrong={3: "47"}), "Christmas Multiplication Mystery Picture", row=60)
    cw, ch, gap = 760, 1380, 70
    x0 = (W - (3 * cw + 2 * gap)) // 2
    y0 = 420
    steps = [("1", "Solve", "Type the answer in the yellow box"),
             ("2", "Check", "Green check = correct, red X = try again"),
             ("3", "Reveal!", "Each right answer shows\nmore of the picture")]
    s = 2
    crops = [full.crop((30 * s, 105 * s, 318 * s, (130 + 30 * 10) * s)),
             full.crop((50 * s, 105 * s, 356 * s, (130 + 30 * 10) * s)),
             R.picture(p, set(range(15)) - {3}, cell=30, gap=2)]
    for i, ((num, head, sub), cr) in enumerate(zip(steps, crops)):
        x = x0 + i * (cw + gap)
        card(im, (x, y0, x + cw, y0 + ch))
        d.ellipse([x + cw / 2 - 60, y0 - 50, x + cw / 2 + 60, y0 + 70], fill=[RED, GOLD, GREEN][i])
        d.text((x + cw / 2, y0 + 10), num, font=f("bl", 80), fill="white", anchor="mm")
        d.text((x + cw / 2, y0 + 130), head, font=f("b", 84), fill=INK, anchor="mm")
        img = fit(cr, cw - 60, 900)
        im.paste(img, (int(x + (cw - img.width) / 2), y0 + 220 + (900 - img.height) // 2))
        d.multiline_text((x + cw / 2, y0 + ch - 110), sub.replace(", ", ",\n", 1) if len(sub) > 30 else sub,
                         font=f("sb", 44), fill=SOFT, anchor="mm", align="center")
    im.save(out, quality=92)


def p02_teacher(out):
    im = bg(12)
    d = ImageDraw.Draw(im)
    ctext(d, 80, "Teach Smarter, Not Harder", 120, RED)
    ctext(d, 250, "Change the way your class practices math this Christmas", 60, INK, "pr")
    benefits = [("No grading", "The sheet checks every\nanswer for you"),
                ("Every student engaged", "Kids keep going to see\nthe mystery picture"),
                ("Instant feedback", "Mistakes are fixed right\naway, not practiced"),
                ("Zero prep", "Make a copy, assign it,\nand you're done")]
    cw, chh = 1100, 470
    for i, (head, sub) in enumerate(benefits):
        x, y = 190 + (i % 2) * (cw + 87), 430 + (i // 2) * (chh + 60)
        card(im, (x, y, x + cw, y + chh))
        col = [RED, GREEN, GOLD, (47, 111, 214)][i]
        d.ellipse([x + 60, y + 70, x + 200, y + 210], fill=col)
        d.text((x + 130, y + 142), "✓", font=f("sym", 96), fill="white", anchor="mm")
        d.text((x + 250, y + 140), head, font=f("b", 70), fill=INK, anchor="lm")
        d.multiline_text((x + 250, y + 250), sub, font=f("sb", 50), fill=SOFT, spacing=16)
    d.rounded_rectangle([330, 1540, W - 330, 1800], 60, fill=RED)
    ctext(d, 1585, "Be the teacher they remember!", 84, (255, 255, 255), "pr")
    ctext(d, 1710, "The fun Christmas math activity your students will talk about", 46, (255, 236, 236), "sb")
    im.save(out, quality=92)


def p03_sequence(out):
    im = bg(3)
    d = ImageDraw.Draw(im)
    ctext(d, 110, "Watch the Mystery Picture Appear", 110, RED)
    ctext(d, 270, "Every correct answer reveals another piece", 58, INK, "sb")
    p = puzzles()[1]
    fr = [0, .25, .5, .75, 1]
    cw, gap = 440, 70
    x0 = (W - (5 * cw + 4 * gap)) // 2
    order = list(np.random.default_rng(8).permutation(len(p.questions)))
    for i, fr_ in enumerate(fr):
        x = x0 + i * (cw + gap)
        card(im, (x, 560, x + cw, 1500), radius=30)
        pic = fit(R.picture(p, set(order[: round(fr_ * 20)]), cell=30, gap=2), cw - 50, 760)
        im.paste(pic, (x + (cw - pic.width) // 2, 600 + (760 - pic.height) // 2))
        d.text((x + cw / 2, 1430), f"{round(fr_ * 20)} / 20", font=f("b", 56), fill=GREEN if fr_ == 1 else INK, anchor="mm")
        if i < 4:
            ax = x + cw + gap / 2
            d.polygon([(ax - 22, 1010), (ax + 22, 1030), (ax - 22, 1050)], fill=RED)
    ctext(d, 1640, "Nothing is revealed until the answer is right, so students can't guess their way through.",
          46, SOFT, "sb")
    im.save(out, quality=92)


def p04_pictures(out):
    im = bg(4)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "10 Christmas Mystery Pictures", 116, RED)
    ctext(d, 250, "Tabs are named Picture 1-10, so the picture stays a secret until it's solved", 50, INK, "sb")
    cw, chh, gx, gy = 440, 690, 50, 50
    x0 = (W - (5 * cw + 4 * gx)) // 2
    for i, name in enumerate(B.ORDER):
        x, y = x0 + (i % 5) * (cw + gx), 400 + (i // 5) * (chh + gy)
        thumb_card(im, name, x, y, cw, chh, label=D.DESIGNS[name]["title"])
    im.save(out, quality=92)


def p05_skills(out):
    im = bg(5)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "4 Skills x 10 Pictures = 40 Activities", 104, RED)
    ctext(d, 240, "20 questions per picture, 800 questions in total", 56, INK, "sb")
    info = {"Multiplication": "Facts 2-12", "Division": "Facts up to 144 ÷ 12",
            "Addition": "2-digit numbers, totals to 99", "Subtraction": "2-digit numbers, no negatives"}
    cw, chh = 1150, 720
    for i, s in enumerate(Q.GENERATORS):
        x, y = 150 + (i % 2) * (cw + 67), 400 + (i // 2) * (chh + 60)
        card(im, (x, y, x + cw, y + chh))
        d.rounded_rectangle([x, y, x + cw, y + 150], 36, fill=SKILL_COL[s])
        d.rectangle([x, y + 110, x + cw, y + 150], fill=SKILL_COL[s])
        d.text((x + 50, y + 75), s, font=f("b", 76), fill="white", anchor="lm")
        d.text((x + cw - 50, y + 75), info[s], font=f("sb", 40), fill="white", anchor="rm")
        qs = B.puzzles_for(s)[0].questions[:8]
        for j, (q, a) in enumerate(qs):
            qx, qy = x + 70 + (j // 4) * 540, y + 210 + (j % 4) * 120
            d.text((qx, qy + 40), q, font=f("r", 58), fill=INK, anchor="lm")
            bx = qx + 300
            d.rectangle([bx, qy, bx + 160, qy + 80], fill=R.YELLOW, outline=R.BORDER, width=3)
    im.save(out, quality=92)


def p06_feedback(out):
    im = bg(6)
    d = ImageDraw.Draw(im)
    d.text((150, 120), "Self-Checking", font=f("bl", 130), fill=RED)
    d.text((150, 290), "Instant feedback on every answer", font=f("sb", 64), fill=INK)
    p = puzzles()[4]
    full = R.sheet(p, R.typed_upto(p, 9, wrong={2: "24", 6: "57"}), "Christmas Multiplication Mystery Picture", row=80)
    s = 80 / 30
    crop = full.crop((int(10 * s), int(68 * s), int(375 * s), int((130 + 30 * 9) * s)))
    crop = fit(crop, 1250, 1450)
    card(im, (150, 470, 150 + crop.width + 80, 470 + crop.height + 80))
    im.paste(crop, (190, 510))
    y = 620
    for t, col in [("Green check = correct", GREEN), ("Red X = try again", (192, 38, 45)),
                   ("Live score: Correct 7 / 20", GREEN), ("Wrong answers reveal nothing", INK),
                   ("No add-ons or extensions", INK), ("Works on Chromebooks", INK)]:
        check_bullet(d, 1560, y, t, size=54, col=col if col != INK else GOLD)
        y += 175
    im.save(out, quality=92)


def p07_classroom(out):
    im = bg(7)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "Ready for Google Classroom", 116, RED)
    ctext(d, 250, "Set up in under 2 minutes, no prep, no printing", 58, INK, "sb")
    steps = [("Open your link", "Each skill has its own\nGoogle Sheets link in\nthe Teacher Guide"),
             ("Make a copy", "Click \"Make a copy\".\nThe sheet is saved to\nyour Google Drive"),
             ("Assign it", "Attach in Classroom with\n\"Make a copy for\neach student\"")]
    cw, gap = 700, 90
    x0 = (W - (3 * cw + 2 * gap)) // 2
    for i, (head, sub) in enumerate(steps):
        x = x0 + i * (cw + gap)
        card(im, (x, 430, x + cw, 1330))
        d.ellipse([x + cw / 2 - 95, 500, x + cw / 2 + 95, 690], fill=[RED, GOLD, GREEN][i])
        d.text((x + cw / 2, 595), str(i + 1), font=f("bl", 120), fill="white", anchor="mm")
        d.text((x + cw / 2, 800), head, font=f("b", 72), fill=INK, anchor="mm")
        d.multiline_text((x + cw / 2, 1040), sub, font=f("sb", 48), fill=SOFT, anchor="mm", align="center", spacing=18)
    card(im, (380, 1480, W - 380, 1760), fill=(232, 245, 234))
    ctext(d, 1545, "Prefer Microsoft Excel?", 64, GREEN)
    ctext(d, 1650, "The .xlsx files are included and work the same way", 50, INK, "sb")
    im.save(out, quality=92)


def guide_pages(pages, scale=1.2):
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(B.OUT / "Teacher_Guide_and_Answer_Keys.pdf"))
    return [pdf[i].render(scale=scale).to_pil().convert("RGB") for i in pages]


def p08_guide(out):
    im = bg(8)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "24-Page Teacher Guide", 116, RED)
    ctext(d, 250, "How-to steps, Google Sheets links, and answer keys with every finished picture", 52, INK, "sb")
    pages = guide_pages([1, 4, 0])
    for k, (pg, ang, x, y) in enumerate(zip(pages, [7, -7, 0], [230, 1560, 900], [560, 560, 420])):
        pg = fit(pg, 820, 1060)
        pg = pg.convert("RGBA").rotate(ang, expand=True, resample=Image.BICUBIC)
        R.shadow(im, pg, (x, y), blur=22, offset=(0, 18), alpha=0.3)
    im.save(out, quality=92)


def file_icon(d, x, y, kind):
    col, label = {"xlsx": ((16, 124, 65), "XLSX"), "pdf": ((200, 16, 46), "PDF"), "link": ((15, 157, 88), "LINK")}[kind]
    d.rounded_rectangle([x, y, x + 120, y + 150], 14, fill=col)
    d.polygon([(x + 80, y), (x + 120, y + 40), (x + 80, y + 40)], fill=(255, 255, 255))
    d.text((x + 60, y + 100), label, font=f("b", 32), fill="white", anchor="mm")


def p09_included(out):
    im = bg(9)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "What's Included", 120, RED)
    card(im, (330, 330, W - 330, 1700))
    rows = [("xlsx", "Christmas Multiplication Mystery Pictures", "10 pictures, 200 questions"),
            ("xlsx", "Christmas Division Mystery Pictures", "10 pictures, 200 questions"),
            ("xlsx", "Christmas Addition Mystery Pictures", "10 pictures, 200 questions"),
            ("xlsx", "Christmas Subtraction Mystery Pictures", "10 pictures, 200 questions"),
            ("pdf", "Teacher Guide and Answer Keys (24 pages)", "Instructions, finished pictures, all answers"),
            ("link", "Google Sheets \"Make a copy\" links", "Inside the Teacher Guide")]
    y = 400
    for kind, head, sub in rows:
        file_icon(d, 430, y, kind)
        d.text((600, y + 45), head, font=f("b", 56), fill=INK, anchor="lm")
        d.text((600, y + 115), sub, font=f("sb", 42), fill=SOFT, anchor="lm")
        y += 215
    ctext(d, 1790, "Instant digital download  •  Nothing will be shipped", 52, GREEN, "b")
    im.save(out, quality=92)


def p10_reveal(out):
    im = bg(10)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "Students Love the Big Reveal!", 116, RED)
    p = puzzles("Addition")[8]
    lap = laptop_with(p, 20, 2100, topic="Addition", tab=8)
    R.shadow(im, lap, ((W - lap.width) // 2, 330), blur=30, offset=(0, 30), alpha=0.35)
    rng = np.random.default_rng(3)
    for _ in range(70):                                     # confetti
        x, y = int(rng.integers(60, W - 60)), int(rng.integers(260, 1900))
        if 300 < x < W - 300 and 330 < y < 1680:
            continue
        col = [RED, GOLD, GREEN, (47, 111, 214)][int(rng.integers(0, 4))]
        d.rectangle([x, y, x + 26, y + 14], fill=col)
    im.save(out, quality=92)


def p11_uses(out):
    im = bg(11)
    d = ImageDraw.Draw(im)
    ctext(d, 90, "Perfect For", 120, RED)
    uses = ["Math centers", "Early finishers", "Holiday party days", "Sub plans", "Fact fluency practice",
            "Homework", "Computer lab time", "Last week before break"]
    cw, chh = 1050, 230
    for i, u in enumerate(uses):
        x, y = 230 + (i % 2) * (cw + 110), 360 + (i // 2) * (chh + 60)
        card(im, (x, y, x + cw, y + chh), radius=40)
        d.ellipse([x + 50, y + chh / 2 - 45, x + 140, y + chh / 2 + 45], fill=[RED, GREEN, GOLD, (47, 111, 214)][i % 4])
        d.text((x + 95, y + chh / 2 + 2), "✓", font=f("sym", 60), fill="white", anchor="mm")
        d.text((x + 180, y + chh / 2), u, font=f("b", 64), fill=INK, anchor="lm")
    ctext(d, 1560, "Grades 2-4  •  Google Sheets & Excel  •  Chromebooks, laptops and desktops", 52, INK, "sb")
    ctext(d, 1660, "Digital download. A free Google account or Microsoft Excel is needed.", 46, SOFT, "sb")
    im.save(out, quality=92)


PHOTO_FUNCS = [p00_hero, p01_overview, p02_teacher, p02_how, p03_sequence, p04_pictures, p05_skills, p06_feedback,
               p07_classroom, p08_guide, p09_included, p10_reveal, p11_uses]


def photos(only=None):
    PHOTOS.mkdir(parents=True, exist_ok=True)
    if not only:
        for old in PHOTOS.glob("*.jpg"):
            old.unlink()
    for i, fn in enumerate(PHOTO_FUNCS, 1):
        if only and str(i) not in only:
            continue
        out = PHOTOS / f"{i:02d}_{fn.__name__.split('_', 1)[1]}.jpg"
        fn(out)
        print(out.name, flush=True)


# ------------------------------------------------------------------ text

TITLE = ("Christmas Math Mystery Pictures, 40 Self Checking Pixel Art Activities, Google Sheets, "
         "Multiplication Division Addition Subtraction")
TAGS = ["math mystery picture", "pixel art math", "google sheets math", "christmas math", "multiplication game",
        "division practice", "addition subtraction", "self checking math", "google classroom", "teacher resources",
        "3rd grade math", "math centers", "christmas activity"]

DESCRIPTION = """Be the teacher they remember this Christmas!

Change the way your class practices math. Instead of another worksheet, give your students a mystery to solve: every correct answer reveals part of a hidden Christmas pixel art picture, so they keep going, check their own work and ask for "just one more!"

★ WHY TEACHERS LOVE IT
• No grading: the sheet checks every answer for you
• Every student engaged, from strugglers to early finishers
• Instant feedback: students fix mistakes right away instead of practicing them
• Zero prep: make a copy, assign it, done
• More time for what matters: teaching, encouraging and celebrating progress

40 self-checking digital activities: 10 Christmas mystery pictures for each of 4 skills.

★ HOW IT WORKS
• Students type the answer in the yellow box and press Enter
• Green ✓ = correct, and that part of the picture appears
• Red ✗ = try again. Nothing is revealed until the answer is right
• A live score shows progress: "Correct: 14 / 20"

★ WHAT'S INCLUDED
• Christmas Multiplication Mystery Pictures: 10 pictures, facts 2-12
• Christmas Division Mystery Pictures: 10 pictures, facts up to 144 ÷ 12
• Christmas Addition Mystery Pictures: 10 pictures, 2-digit numbers, totals up to 99
• Christmas Subtraction Mystery Pictures: 10 pictures, 2-digit numbers, no negative answers
• 24-page Teacher Guide with Google Sheets "Make a copy" links, step-by-step instructions, and answer keys with every finished picture
• 20 questions per picture, 800 questions in total

★ THE 10 MYSTERY PICTURES
Christmas tree, snowman, gift box, gingerbread man, Santa hat, reindeer, candy cane, stocking, ornament and hot cocoa. The tabs are named Picture 1 to Picture 10, so the picture stays a secret until it is solved.

★ PERFECT FOR
Math centers, early finishers, fact fluency practice, sub plans, holiday party days, homework and the last week before winter break. Best for grades 2-4 (multiplication and division also work well for grade 5 review).

★ HOW TO USE
1. Download the files after purchase and open the Teacher Guide (PDF)
2. Click the Google Sheets link for a skill and choose "Make a copy"
3. In Google Classroom, attach your copy and choose "Make a copy for each student"
Prefer Excel? Open the .xlsx files directly. They work the same way.

★ GOOD TO KNOW
• This is a DIGITAL DOWNLOAD. Nothing will be shipped
• You need a free Google account (Google Sheets) or Microsoft Excel
• Works on Chromebooks, laptops and desktops. No add-ons or extensions
• Every puzzle was checked square by square: correct answers always rebuild the full picture
• The answers are stored on a hidden tab. Students can type answers but should not unhide sheets
• Pixel art and puzzles were made by our shop with the help of digital and AI-assisted tools

★ TERMS OF USE
For use by one teacher in their own classroom, including Google Classroom and other platforms where access is limited to your students. Please do not share, resell or post the files or links publicly.

Questions? Send me a message on Etsy. I'm happy to help!"""


def text():
    OUT.mkdir(parents=True, exist_ok=True)
    assert len(TITLE) <= 140, len(TITLE)
    assert len(TAGS) == 13 and all(len(t) <= 20 for t in TAGS), [t for t in TAGS if len(t) > 20]
    data = {"title": TITLE, "tags": TAGS, "description": DESCRIPTION, "price": PRICE}
    (OUT / "listing.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("title", len(TITLE), "chars; tags ok")


# ------------------------------------------------------------------ upload

def etsy():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # coloring/etsy_api.py (read-only reuse)
    import etsy_api
    return etsy_api


def upload():
    e = etsy()
    sid = e.get_token()["shop_id"]
    state_file = OUT / "uploaded.json"
    if state_file.exists():
        sys.exit(f"already uploaded: {state_file.read_text()}")
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    sections = {s["title"]: s["shop_section_id"] for s in e.request("GET", f"/shops/{sid}/sections")["results"]}
    if SECTION not in sections:
        sections[SECTION] = e.request("POST", f"/shops/{sid}/sections", form={"title": SECTION})["shop_section_id"]
    listing = e.request("POST", f"/shops/{sid}/listings", retry=False, form={
        "quantity": 999, "title": t["title"], "description": t["description"], "price": t["price"],
        "who_made": "i_did", "when_made": "2020_2026", "taxonomy_id": TAXONOMY, "type": "download",
        "is_supply": "false", "should_auto_renew": "true", "tags": ",".join(t["tags"]),
        "shop_section_id": sections[SECTION],
    })
    lid = listing["listing_id"]
    state_file.write_text(json.dumps({"listing_id": lid}, indent=2))
    print("draft", lid, flush=True)
    for rank, p in enumerate(sorted(PHOTOS.glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    print("photos uploaded", flush=True)
    files = [B.OUT / "Teacher_Guide_and_Answer_Keys.pdf"] + [B.workbook_path(s) for s in Q.GENERATORS]
    for rank, p in enumerate(files, 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/files", form={"rank": rank, "name": p.name}, files={"file": p})
    print("5 download files uploaded", flush=True)
    video = OUT / "video" / "christmas_math_mystery_pictures.mp4"
    if video.exists():
        e.request("POST", f"/shops/{sid}/listings/{lid}/videos", form={"name": "christmas math mystery pictures"},
                  files={"video": video})
        print("video uploaded", flush=True)
    print(f"https://www.etsy.com/your/shops/me/listing-editor/edit/{lid}")


def update():
    e = etsy()
    sid = e.get_token()["shop_id"]
    lid = json.loads((OUT / "uploaded.json").read_text())["listing_id"]
    t = json.loads((OUT / "listing.json").read_text(encoding="utf-8"))
    e.request("PATCH", f"/shops/{sid}/listings/{lid}", form={"title": t["title"], "description": t["description"],
                                                            "tags": ",".join(t["tags"])})
    print("text updated", flush=True)
    # Etsy: max 20 images and at least 1 at all times -> keep one old image, upload the new set, delete it last
    old = [im["listing_image_id"] for im in e.request("GET", f"/listings/{lid}/images")["results"]]
    for image_id in old[1:]:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
    for rank, p in enumerate(sorted(PHOTOS.glob("*.jpg")), 1):
        e.request("POST", f"/shops/{sid}/listings/{lid}/images", form={"rank": rank}, files={"image": p})
    for image_id in old[:1]:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/images/{image_id}")
    print("photos replaced", flush=True)
    video = OUT / "video" / "christmas_math_mystery_pictures.mp4"
    for v in e.request("GET", f"/listings/{lid}/videos")["results"]:
        e.request("DELETE", f"/shops/{sid}/listings/{lid}/videos/{v['video_id']}")
    e.request("POST", f"/shops/{sid}/listings/{lid}/videos", form={"name": "christmas math mystery pictures"},
              files={"video": video})
    print("video replaced", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "photos"
    {"photos": lambda: photos(sys.argv[2:]), "text": text, "upload": upload, "update": update}[cmd]()
