"""The PDF Etsy delivers to buyers: thank-you page with the download link, what's inside, how to use, terms.

    python make_delivery_pdf.py --url <drive link> -i input -c output/collection -o output/delivery
"""

import argparse
import sys
import tempfile
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

from make_listing_images import Collection, cover_crop

W, H = A4
FONTS = Path("C:/Windows/Fonts")
for name, file in (("Seg", "segoeui.ttf"), ("SegB", "segoeuib.ttf"), ("GeoB", "georgiab.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))

CREAM, TEAL, CORAL, MUSTARD, PLUM, INK = ((1, .965, .914), (.122, .478, .455), (.91, .333, .243),
                                          (.949, .714, .196), (.294, .18, .353), (.17, .17, .17))
GREEN, BLUE = (.353, .588, .353), (.235, .431, .667)
HERO = [5, 1, 8, 31, 37, 6]


def background(c, seed=0):
    c.setFillColorRGB(*CREAM)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    for i, (color, x, y, r) in enumerate([(TEAL, 60, 760, 150), (CORAL, 540, 610, 170), (MUSTARD, 90, 120, 160),
                                          (CORAL, 520, 60, 130), (TEAL, 300, 420, 120)]):
        c.setFillColorRGB(*color, alpha=0.10)
        c.circle(x + seed * 25, y, r, stroke=0, fill=1)
    c.setFillAlpha(1)


def text_c(c, text, y, font, size, color, x=None):
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    c.drawCentredString(W / 2 if x is None else x, y, text)


def paragraph(c, text, x, y, width, font="Seg", size=11.5, color=INK, leading=None):
    leading = leading or size * 1.45
    c.setFont(font, size)
    c.setFillColorRGB(*color)
    for line in simpleSplit(text, font, size, width):
        c.drawString(x, y, line)
        y -= leading
    return y


def header(c, title, sub=None):
    text_c(c, title, H - 78, "GeoB", 30, PLUM)
    if sub:
        text_c(c, sub, H - 104, "SegB", 13, CORAL)


def footer(c, page, total):
    c.setStrokeColorRGB(.85, .8, .72)
    c.line(50, 44, W - 50, 44)
    c.setFont("Seg", 9)
    c.setFillColorRGB(.4, .4, .4)
    c.drawString(50, 28, "Paint by Number Collection  •  Instant digital download  •  Personal use only")
    c.drawRightString(W - 50, 28, f"{page} / {total}")


def qr(c, url, x, y, size):
    widget = QrCodeWidget(url)
    x0, y0, x1, y1 = widget.getBounds()
    d = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    d.add(widget)
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(x - 8, y - 8, size + 16, size + 16, 8, stroke=0, fill=1)
    renderPDF.draw(d, c, x, y)


def page_link(c, url, tiles, subtitle="for your Paint by Number Collection"):
    background(c, 0)
    text_c(c, "THANK YOU!", H - 92, "GeoB", 52, PLUM)
    text_c(c, subtitle, H - 126, "SegB", 17, CORAL)

    # six featured designs
    tw, th, gap = 80, 107, 9
    x0 = (W - (6 * tw + 5 * gap)) / 2
    for i, img in enumerate(tiles):
        x = x0 + i * (tw + gap)
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(x - 3, H - 262 - 3, tw + 6, th + 6, 5, stroke=0, fill=1)
        c.drawImage(str(img), x, H - 262, tw, th)

    # the button
    bw, bh = 400, 84
    bx, by = (W - bw) / 2, H - 392
    c.setFillColorRGB(*TEAL)
    c.roundRect(bx, by, bw, bh, 18, stroke=0, fill=1)
    text_c(c, "DOWNLOAD YOUR FILES", by + 46, "SegB", 25, (1, 1, 1))
    text_c(c, "Tap or click here", by + 22, "Seg", 13, (.88, .96, .94))
    c.linkURL(url, (bx, by, bx + bw, by + bh), relative=0, thickness=0)

    text_c(c, "Button not working? Copy this link into your browser:", by - 34, "Seg", 11, INK)
    c.setFont("Seg", 9)
    c.setFillColorRGB(*BLUE)
    lines = simpleSplit(url, "Seg", 9, 470)
    yy = by - 52
    for line in lines:
        c.drawCentredString(W / 2, yy, line)
        yy -= 13
    c.linkURL(url, (W / 2 - 235, yy, W / 2 + 235, by - 42), relative=0, thickness=0)

    # QR + tips
    qy = 150
    qr(c, url, 70, qy, 120)
    text_c(c, "Scan with your phone", qy - 24, "SegB", 11, TEAL, x=130)
    paragraph(c, "Download tips", 235, qy + 112, 300, "GeoB", 17, PLUM)
    tips = ["Click the button, then use the Download button in Google Drive.",
            "The collection is large. Use Wi-Fi, and give it a few minutes.",
            "If it arrives as a ZIP, unzip it first (on iPad: tap it in the Files app).",
            "Need help? Message me on Etsy and I'll sort it out quickly."]
    y = qy + 84
    for t in tips:
        c.setFillColorRGB(*CORAL)
        c.circle(241, y + 4, 2.6, stroke=0, fill=1)
        y = paragraph(c, t, 252, y, 290, "Seg", 11, INK, 15) - 6
    footer(c, 1, 4)


def badge(c, x, y, label, color, size=40):
    c.setFillColorRGB(*color)
    c.roundRect(x, y, size, size, 9, stroke=0, fill=1)
    c.setFont("SegB", 12 if len(label) > 3 else 15)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(x + size / 2, y + size / 2 - 5, label)


def page_inside(c, count):
    background(c, 1)
    header(c, "WHAT'S INSIDE", "Everything you need, in one download")
    rows = [("PNG", TEAL, f"{count} designs, 6 PNG styles each",
             "4961 x 7016 px (A4 at 600 DPI): dark numbered, light numbered, shadow guide, color map, "
             "page with palette, and a clean contour without numbers."),
            ("PDF", CORAL, "A4 print-ready PDF for every design",
             "Dark, light, shadow and palette pages, ready to print at home or at a print shop."),
            ("SVG", PLUM, "Scalable vector files",
             "Numbered dark and light versions that stay sharp at any size."),
            (".SW", MUSTARD, "Procreate palette (.swatches)",
             "One-tap import. Colors are in number order. Designs with more than 30 colors have a second "
             "palette file for the extra colors."),
            ("PAL", GREEN, "Printable color palette sheet",
             "PNG and SVG with every color number and hex code."),
            ("HEX", BLUE, "Hex code list",
             "A simple text list for any other painting app.")]
    y = H - 160
    for badge_label, color, head, sub in rows:
        badge(c, 56, y - 36, badge_label, color)
        c.setFont("SegB", 14)
        c.setFillColorRGB(*INK)
        c.drawString(112, y - 6, head)
        paragraph(c, sub, 112, y - 24, W - 170, "Seg", 11, (.3, .3, .3), 14.5)
        y -= 88
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(56, 96, W - 112, 78, 14, stroke=0, fill=1)
    paragraph(c, "Every design comes with its own palette, so the colors you paint with always match the "
                 "numbers on that page. Every number on every page was checked against its color.",
              76, 152, W - 152, "SegB", 11.5, TEAL, 16)
    footer(c, 2, 4)


def step(c, x, y, num, text, width, color):
    c.setFillColorRGB(*color)
    c.circle(x + 13, y + 4, 13, stroke=0, fill=1)
    c.setFont("SegB", 14)
    c.setFillColorRGB(1, 1, 1)
    c.drawCentredString(x + 13, y - 1, str(num))
    return paragraph(c, text, x + 38, y + 2, width - 38, "Seg", 12.5, INK, 17) - 24


def page_howto(c):
    background(c, 2)
    header(c, "HOW TO USE", "Paint on your iPad, or print and paint on paper")
    colw = (W - 130) / 2
    lx, rx = 50, 50 + colw + 30
    for x, title, color in ((lx, "On your iPad (Procreate)", TEAL), (rx, "On paper (printed)", CORAL)):
        c.setFillColorRGB(*color)
        c.roundRect(x, H - 160, colw, 30, 8, stroke=0, fill=1)
        c.setFont("SegB", 13)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(x + 12, H - 151, title)
    ipad = ["Download your files and unzip them in the Files app.",
            "Open Procreate and import a PNG line art file (Gallery, then Import, or Actions > Add > Insert a file).",
            "Tap the .swatches file to add the numbered color palette to Procreate.",
            "Set the line art layer to Multiply, add a new layer below it, and paint there.",
            "Pick the swatch with the same number as the region. Drag a color into the region or use a brush.",
            "Zoom in for small regions. Numbers and lines stay sharp."]
    paper = ["Open a PDF from the Design folder you like.",
             "Print at 100% (Actual size) on A4 paper. Thicker paper works best with paint.",
             "Use the palette sheet or the palette page to match each number to a color.",
             "Start with the large areas, then do the small details.",
             "Lighter lines are included too if you want them to disappear under paint.",
             "Print the same page again and again, as often as you like."]
    for x, items, color in ((lx, ipad, TEAL), (rx, paper, CORAL)):
        y = H - 195
        for i, t in enumerate(items, 1):
            y = step(c, x, y, i, t, colw, color)
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(50, 100, W - 100, 118, 14, stroke=0, fill=1)
    paragraph(c, "Tips for the best result", 70, 196, 400, "GeoB", 15, PLUM)
    y = 172
    for t in ["Pick the page by its zone count: lower numbers are relaxing, higher numbers are an expert challenge.",
              "On the light-line and shadow versions the artwork shows through, so it is easy to see what each area becomes.",
              "Not sure which color? The color map style shows the finished picture with the numbers on top."]:
        y = paragraph(c, "•  " + t, 70, y, W - 140, "Seg", 10.5, INK, 14) - 3
    footer(c, 3, 4)


def page_terms(c):
    background(c, 3)
    header(c, "GOOD TO KNOW", "A few quick things")
    items = [("Instant digital download", "No item is shipped. Your files are available right after purchase.", TEAL),
             ("For personal use only", "Print and paint as often as you like for yourself. Please do not share, "
                                       "resell or redistribute the files or the download link.", CORAL),
             ("Colors on screen vs. paper", "Screens and printers show colors slightly differently. The palette "
                                            "sheet gives the exact hex codes.", MUSTARD),
             ("Digital items are not returnable", "Because these are digital files, Etsy does not allow returns. "
                                                  "If anything is wrong with your download, message me and I will fix it.", PLUM),
             ("Questions or problems?", "Send me a message on Etsy. I am happy to help with downloads, "
                                        "importing the palette, or printing.", GREEN)]
    y = H - 160
    for head, body, color in items:
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(50, y - 70, W - 100, 82, 12, stroke=0, fill=1)
        c.setFillColorRGB(*color)
        c.roundRect(50, y - 70, 8, 82, 4, stroke=0, fill=1)
        c.setFont("SegB", 13.5)
        c.setFillColorRGB(*INK)
        c.drawString(76, y - 18, head)
        paragraph(c, body, 76, y - 38, W - 150, "Seg", 11, (.3, .3, .3), 14.5)
        y -= 96
    text_c(c, "Thank you so much for your purchase!", 150, "GeoB", 22, PLUM)
    text_c(c, "If you enjoy your pages, a review on Etsy helps a small shop a lot.", 124, "Seg", 12, CORAL)
    text_c(c, "Happy painting!", 98, "SegB", 15, TEAL)
    footer(c, 4, 4)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("-i", "--input", required=True, type=Path)
    p.add_argument("-c", "--collection", required=True, type=Path)
    p.add_argument("-o", "--output", required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    col = Collection(a.input, a.collection)
    count = len(col.files)
    out = a.output / "Download_Your_Files.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        tiles = []
        for n in HERO:
            path = Path(tmp) / f"tile_{n}.jpg"
            cover_crop(col.art(n), 480, 640).save(path, quality=88)
            tiles.append(path)
        c = rl_canvas.Canvas(str(out), pagesize=A4)
        c.setTitle("Your Paint by Number download")
        c.setAuthor("Paint by Number Collection")
        page_link(c, a.url, tiles)
        c.showPage()
        page_inside(c, count)
        c.showPage()
        page_howto(c)
        c.showPage()
        page_terms(c)
        c.showPage()
        c.save()
    print(f"{out} ({out.stat().st_size / 1e3:.0f} KB)")


if __name__ == "__main__":
    sys.exit(main())
