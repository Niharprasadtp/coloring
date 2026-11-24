#!/usr/bin/env python3
"""Etsy listing images and listing copy for one device.

    python etsy_assets.py --device remarkable_pro -o etsy

Builds the planner variants it needs, renders real pages into generic tablet
mockups (no device branding), and writes 4:3 listing images plus listing.md with a
title, 13 tags and a description. Every number in the images and copy (pages,
links, templates) comes from the generated planner, so nothing is overstated.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from eink_planner.builder import N_BRAIN_DUMP, N_PROJECTS, build
from eink_planner.devices import DEVICES, Options
from eink_planner.pages.templates import TEMPLATES

W, H = 3000, 2250                      # 4:3, what Etsy search thumbnails show
BG = (244, 241, 236)
INK = (38, 38, 38)
SOFT = (92, 88, 82)
ACCENT = (78, 108, 142)
CHIP = (232, 227, 219)
BEZEL = (46, 46, 46)

_FONT_DIRS = ["/usr/share/fonts/truetype/noto", "/usr/share/fonts/truetype/liberation",
              "/usr/share/fonts/truetype/dejavu", "/Library/Fonts", "C:/Windows/Fonts"]
_FONT_NAMES = {False: ["NotoSans-Regular.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf",
                       "Arial.ttf", "arial.ttf"],
               True: ["NotoSans-Bold.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf",
                      "Arial Bold.ttf", "arialbd.ttf"]}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    for d in _FONT_DIRS:
        for n in _FONT_NAMES[bold]:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    sys.exit("error: no TrueType font found (install Noto Sans or Liberation Sans)")


# --- rendering ---------------------------------------------------------------------
class Planner:
    """A built planner PDF with page lookup by outline title."""

    def __init__(self, opts: Options, folder: Path):
        path = folder / f"{opts.file_stem()}.pdf"
        self.info = build(opts, path)
        self.doc = pymupdf.open(path)
        self.toc = {}
        for _, title, page in self.doc.get_toc():
            self.toc.setdefault(title, page - 1)

    def index(self, title: str) -> int:
        if title in self.toc:
            return self.toc[title]
        return next(v for k, v in self.toc.items() if k.startswith(title))

    def render(self, title: str, height: int) -> tuple[Image.Image, float, pymupdf.Page]:
        page = self.doc[self.index(title)]
        z = height / page.rect.height
        pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples), z, page


def shadowed(canvas: Image.Image, img: Image.Image, xy: tuple[int, int], radius: int,
             blur: int = 28, offset: int = 18) -> None:
    x, y = xy
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius, fill=255)
    sh = Image.new("RGBA", (img.width + blur * 4, img.height + blur * 4), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        (blur * 2, blur * 2, blur * 2 + img.width, blur * 2 + img.height), radius,
        fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(sh, (x - blur * 2, y - blur * 2 + offset), sh)
    canvas.paste(img, (x, y), mask)


def tablet(page: Image.Image) -> tuple[Image.Image, int]:
    """Generic tablet mockup: dark rounded bezel around the page. Returns (img, bezel)."""
    b = max(int(min(page.size) * 0.045), 18)
    img = Image.new("RGB", (page.width + 2 * b, page.height + 2 * b), BEZEL)
    img.paste(page, (b, b))
    return img, b


def fit_height(planner: Planner, box_w: int, box_h: int, bezel: bool = False) -> int:
    """Largest page height (px) whose page, optionally in a tablet, fits box_w x box_h."""
    r = planner.doc[0].rect
    aspect = r.width / r.height
    k = 1.09 if bezel else 1.0            # bezel adds ~4.5% each side
    return int(min(box_h / k, box_w / k / aspect))


def thumb(canvas, planner: Planner, title: str, height: int, xy) -> Image.Image:
    page, _, _ = planner.render(title, height)
    bordered = Image.new("RGB", (page.width + 4, page.height + 4), (205, 200, 192))
    bordered.paste(page, (2, 2))
    shadowed(canvas, bordered, xy, 6, blur=14, offset=8)
    return bordered


# --- text --------------------------------------------------------------------------
def wrap(d: ImageDraw.ImageDraw, text: str, f, width: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def para(d, xy, text, f, fill, width, gap=1.25) -> int:
    x, y = xy
    for line in wrap(d, text, f, width):
        d.text((x, y), line, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def chip(d, xy, text, f) -> int:
    x, y = xy
    w = int(d.textlength(text, font=f)) + 56
    h = int(f.size * 1.9)
    d.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=CHIP)
    d.text((x + 28, y + h / 2), text, font=f, fill=INK, anchor="lm")
    return y + h


def marker(d, cx, cy, n, r=34) -> None:
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT, outline="white", width=6)
    d.text((cx, cy + 1), str(n), font=font(int(r * 1.1), True), fill="white", anchor="mm")


def headline(d, text, sub=None, x=150, y=130, width=W - 300) -> int:
    y = para(d, (x, y), text, font(104, True), INK, width, 1.12)
    if sub:
        y = para(d, (x, y + 16), sub, font(48), SOFT, width) + 10
    return y


def new() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


# --- listing images ----------------------------------------------------------------
def img_hero(p: Planner, dev, out: Path) -> None:
    img, d = new()
    x = 150
    d.text((x, 190), "2027 DIGITAL PLANNER", font=font(46, True), fill=ACCENT)
    y = para(d, (x, 270), "Your whole year, one tap away", font(124, True), INK, 1250, 1.08)
    y = para(d, (x, y + 30), f"Made for {dev.label}", font(56), SOFT, 1250) + 50
    for t in (f"{p.info['pages']} hyperlinked pages", "Dec 2026 – Dec 2027",
              "Daily · Weekly · Monthly · Quarterly", "Minimal + ADHD-friendly daily pages",
              "Monday or Sunday start", "Right- or left-handed layout"):
        y = chip(d, (x, y), t, font(44)) + 26
    # Two overlapping tablets inside the right-hand area, back one higher.
    area_x, area_w, top, bottom = 1440, W - 1440 - 90, 120, H - 120
    shift, drop = int(area_w * 0.2), 140
    ph = fit_height(p, area_w - shift, bottom - top - drop, bezel=True)
    back, b = tablet(p.render("Home", ph)[0])
    front, _ = tablet(p.render("Friday, January 1", ph)[0])
    x0 = area_x + (area_w - shift - back.width) // 2
    y0 = top + (bottom - top - drop - back.height) // 2
    shadowed(img, back, (x0, y0), int(b * 1.6))
    shadowed(img, front, (x0 + shift, y0 + drop), int(b * 1.6))
    img.save(out)


def img_navigation(p: Planner, out: Path) -> None:
    img, d = new()
    headline(d, "Every page links everywhere",
             "Hyperlinked tabs and dates: tap with your finger, no scrolling.")
    ph = 1650
    title = "January 2027"
    x0, y0 = 170, 470
    page, z, src = p.render(title, ph)
    tab, b = tablet(page)
    shadowed(img, tab, (x0, y0), int(b * 1.6))
    d = ImageDraw.Draw(img)
    links = src.get_links()
    by_dest = {}
    for ln in links:
        by_dest.setdefault(ln.get("page"), []).append(ln["from"])
    home_p = p.index("Home")
    feb_p = p.index("February 2027")
    day_p = p.index("Wednesday, January 13")
    week_p = p.index("Week 02")

    def at(page_no):
        r = by_dest[page_no][0]
        return x0 + b + (r.x0 + r.x1) / 2 * z, y0 + b + (r.y0 + r.y1) / 2 * z

    items = [(home_p, "Top bar", "Home, Year at a Glance, Q1–Q4, Brain Dump, Projects and "
                                 "Templates, on every page."),
             (feb_p, "Month tabs", "Every month from Dec 2026 to Dec 2027, always on the side."),
             (day_p, "Every date", "Tap a date to open that day's page."),
             (week_p, "Week numbers", "Tap a week number to open the weekly spread.")]
    for n, (pg, _, _) in enumerate(items, 1):
        marker(d, *at(pg), n)
    tx = x0 + tab.width + 150
    y = 560
    for n, (_, head, body) in enumerate(items, 1):
        marker(d, tx + 34, y + 40, n)
        d.text((tx + 100, y), head, font=font(58, True), fill=INK)
        y = para(d, (tx + 100, y + 80), body, font(44), SOFT, W - tx - 250) + 70
    img.save(out)


def img_inside(p: Planner, out: Path) -> None:
    img, d = new()
    headline(d, "What's inside", f"{p.info['pages']} pages · {p.info['links']:,} links")
    pages = [("Year at a Glance", "Year at a Glance"), ("Q1 2027 Overview", "Quarterly"),
             ("January 2027", "13 Monthly"), ("Week 02", "Weekly"),
             ("Friday, January 1", "396 Daily"), ("Project 01 · Plan", f"{N_PROJECTS} Projects"),
             ("Template Library", f"{len(TEMPLATES)} Templates"), ("Brain Dump 1", "Brain Dump")]
    cols, gx = 4, 70
    tw = (W - 300 - gx * (cols - 1)) // cols
    probe, _, _ = p.render("Home", 400)
    th = int(tw * probe.height / probe.width)
    th = min(th, 760)
    tw2 = int(th * probe.width / probe.height)
    for i, (title, cap) in enumerate(pages):
        r, c = divmod(i, cols)
        x = 150 + c * (tw + gx) + (tw - tw2) // 2
        y = 420 + r * (th + 150)
        thumb(img, p, title, th, (x, y))
        ImageDraw.Draw(img).text((x + tw2 / 2, y + th + 30), cap, font=font(44, True),
                                 fill=INK, anchor="mt")
    img.save(out)


def img_daily(p_min: Planner, p_adhd: Planner, out: Path) -> None:
    img, d = new()
    headline(d, "Two daily styles included",
             "Minimal for a calm page, or ADHD-friendly with time blocks, an energy check "
             "and a brain dump.")
    ph = fit_height(p_min, W // 2 - 230, H - 560 - 190, bezel=True)
    for i, (pl, cap) in enumerate(((p_min, "Minimal"), (p_adhd, "ADHD-friendly"))):
        page, _, _ = pl.render("Friday, January 1", ph)
        tab, b = tablet(page)
        x = W // 2 - tab.width - 80 if i == 0 else W // 2 + 80
        shadowed(img, tab, (x, 560), int(b * 1.6))
        ImageDraw.Draw(img).text((x + tab.width / 2, 560 + tab.height + 40), cap,
                                 font=font(56, True), fill=INK, anchor="mt")
    img.save(out)


def img_options(variants: list[tuple], out: Path) -> None:
    """variants: (caption, planner, page title[, crop]); crop keeps the top fraction
    of the page so small details (weekday headers) stay readable."""
    img, d = new()
    headline(d, "Set up the way you plan", "Every combination is included in your download.")
    cols = 3
    rows = -(-len(variants) // cols)
    gx, gy, top = 90, 110, 420
    cw = (W - 300 - gx * (cols - 1)) // cols
    ch = (H - top - 90 - gy * (rows - 1)) // rows - 80      # 80 px for the caption
    for i, (title, pl, page_title, *crop) in enumerate(variants):
        r, c = divmod(i, cols)
        x = 150 + c * (cw + gx)
        y = top + r * (ch + 80 + gy)
        frac = crop[0] if crop else 1.0
        page, _, _ = pl.render(page_title, fit_height(pl, cw - 8, int((ch - 8) / frac)))
        if frac < 1:
            page = page.crop((0, 0, page.width, int(page.height * frac)))
        bordered = Image.new("RGB", (page.width + 4, page.height + 4), (205, 200, 192))
        bordered.paste(page, (2, 2))
        bx = x + (cw - bordered.width) // 2
        by = y + (ch - bordered.height) // 2
        shadowed(img, bordered, (bx, by), 6, blur=14, offset=8)
        ImageDraw.Draw(img).text((x + cw / 2, y + ch + 28), title, font=font(46, True),
                                 fill=INK, anchor="mt")
    img.save(out)


TEMPLATE_PICKS = ["Cornell Notes", "Meeting Minutes", "Priority Matrix", "Monthly Budget",
                  "Habit Tracker", "Meal Planner", "Workout Log", "Reading Log",
                  "Goal Planner", "Dot Grid"]


def img_templates(p: Planner, out: Path) -> None:
    img, d = new()
    headline(d, f"{len(TEMPLATES)} templates for everything else",
             "Notes, meetings, budgets, habits, meals, workouts, reading and more.")
    titles = {t[1] for t in TEMPLATES}
    picks = [t for t in TEMPLATE_PICKS if t in titles]
    cols, gx, gy, top = 5, 60, 90, 420
    rows = -(-len(picks) // cols)
    cw = (W - 300 - gx * (cols - 1)) // cols
    ch = (H - top - 80 - gy * (rows - 1)) // rows - 70
    th = fit_height(p, cw, ch)
    for i, title in enumerate(picks):
        r, c = divmod(i, cols)
        x = 150 + c * (cw + gx)
        y = top + r * (ch + 70 + gy)
        b = thumb(img, p, title, th, (x + (cw - int(th * p.doc[0].rect.width
                                                     / p.doc[0].rect.height)) // 2, y))
        ImageDraw.Draw(img).text((x + cw / 2, y + b.height + 24), title, font=font(40, True),
                                 fill=INK, anchor="mt")
    img.save(out)


def img_projects(p: Planner, out: Path) -> None:
    img, d = new()
    headline(d, f"{N_PROJECTS} project hubs",
             "A plan, a timeline and board, and meeting notes for each project.")
    titles = ["Project 01 · Plan", "Project 01 · Timeline", "Project 01 · Meeting Notes"]
    gap, top = 90, 440
    ph = fit_height(p, (W - 300 - gap * 2) // 3, H - top - 130, bezel=True)
    tabs = [tablet(p.render(t, ph)[0]) for t in titles]
    total = sum(t.width for t, _ in tabs) + gap * (len(tabs) - 1)
    x = (W - total) // 2
    y = top + (H - top - 130 - tabs[0][0].height) // 2
    for t, b in tabs:
        shadowed(img, t, (x, y), int(b * 1.6))
        x += t.width + gap
    img.save(out)


def img_included(dev, files: list[str], p: Planner, out: Path) -> None:
    img, d = new()
    headline(d, "What you get", "Instant digital download. Nothing is shipped.")
    y = 520
    x = 150
    d.text((x, y), "FILES", font=font(42, True), fill=ACCENT)
    y += 80
    for f in files:
        d.ellipse((x, y + 18, x + 22, y + 40), fill=ACCENT)
        y = para(d, (x + 50, y), f, font(46), INK, 1250) + 22
    x2 = 1650
    y2 = 520
    d.text((x2, y2), "GOOD TO KNOW", font=font(42, True), fill=ACCENT)
    y2 += 80
    notes = [f"Made for the {dev.label} screen size.",
             f"{p.info['pages']} pages, every one linked, checked automatically before "
             "release: 0 broken links.",
             "Tap targets are at least 8 mm, easy to hit with a fingertip.",
             "Links follow finger taps; write on every page with your pen.",
             "Step-by-step setup guide included (START HERE)."]
    for t in notes:
        d.ellipse((x2, y2 + 18, x2 + 22, y2 + 40), fill=ACCENT)
        y2 = para(d, (x2 + 50, y2), t, font(46), INK, W - x2 - 200) + 22
    img.save(out)


# --- listing copy --------------------------------------------------------------------
SHORT = {"remarkable_pro": "reMarkable Paper Pro", "remarkable_move": "reMarkable Paper Pro Move",
         "remarkable_2": "reMarkable 2", "kindle_scribe": "Kindle Scribe 11 inch",
         "kindle_scribe_colorsoft": "Kindle Scribe Colorsoft",
         "kindle_scribe_10": "Kindle Scribe 10.2 inch", "supernote_manta": "Supernote Manta",
         "supernote_nomad": "Supernote Nomad"}

DEVICE_TAGS = {
    "remarkable_pro": ["remarkable planner", "paper pro planner", "remarkable pro",
                       "remarkable template"],
    "remarkable_move": ["remarkable move", "paper pro move", "remarkable planner",
                        "move planner"],
    "remarkable_2": ["remarkable 2 planner", "remarkable planner", "remarkable 2",
                     "remarkable template"],
    "kindle_scribe": ["kindle scribe", "scribe planner", "kindle planner", "scribe template"],
    "kindle_scribe_colorsoft": ["scribe colorsoft", "kindle scribe", "colorsoft planner",
                                "kindle planner"],
    "kindle_scribe_10": ["kindle scribe", "scribe planner", "kindle planner",
                         "scribe template"],
    "supernote_manta": ["supernote manta", "supernote planner", "manta planner",
                        "supernote template"],
    "supernote_nomad": ["supernote nomad", "supernote planner", "nomad planner",
                        "supernote template"],
}
COMMON_TAGS = ["2027 digital planner", "hyperlinked planner", "eink planner",
               "adhd planner 2027", "minimalist planner", "2027 planner pdf",
               "daily planner 2027", "weekly planner 2027", "digital planner pdf"]


def listing_copy(dev, p: Planner, colors: bool) -> str:
    name = SHORT[dev.key]
    parts = [f"{name} Planner 2027", "Hyperlinked Digital Planner PDF", "Dec 2026 - Dec 2027",
             "Daily Weekly Monthly", "ADHD Planner", "Minimalist"]
    title = ""
    for part in parts:
        t = f"{title}, {part}" if title else part
        if len(t) <= 140:
            title = t
    tags = list(dict.fromkeys(DEVICE_TAGS[dev.key] + COMMON_TAGS))[:13]
    assert all(len(t) <= 20 for t in tags), tags
    n_variants = 8 if colors else 4
    color_line = ("- Color or black & white: soft colors for color screens, or high contrast"
                  if colors else "- High-contrast black & white, tuned for this screen")
    pages, links = p.info["pages"], p.info["links"]
    return f"""# Etsy listing: {dev.label}

## Title ({len(title)}/140)

{title}

## Tags (13, max 20 characters each)

{", ".join(tags)}

## Description

Plan all of 2027 on your {name}, with every page one tap away.

This hyperlinked planner is made for the {dev.label} screen: pages fill the
display edge to edge and every tab is at least 8 mm, so it's easy to hit with a
fingertip. It runs from December 2026 to December 2027, so you can set up your year
before it starts.

WHAT'S INSIDE ({pages} pages, {links:,} links)
- Home dashboard with shortcuts to every month, quarter and section
- Year at a Glance: every date links to its day
- Quarterly overview plus Goals & Review for Q1-Q4
- 13 monthly pages with a focus list and habit tracker
- Weekly pages with priorities and a habit tracker
- 396 daily pages: schedule, top 3 priorities, to-do and notes
- {N_BRAIN_DUMP} brain dump pages (grid, dot and blank)
- {N_PROJECTS} project hubs: plan, timeline and board, meeting notes
- {len(TEMPLATES)} templates: notes, Cornell, meeting minutes, priority matrix, budget,
  bill tracker, meal planner, workout log, reading log, habit tracker and more
- A "How to use" page inside the planner

NAVIGATION
- Top bar on every page: Home, Year, Q1-Q4, Brain Dump, Projects, Templates
- Month tabs down the side, on the side away from your writing hand
- Every date, week number and month name is a link

CHOOSE YOUR SETUP (all {n_variants * 4} versions are included)
- Monday or Sunday week start
- Right- or left-handed: the month tabs sit opposite your writing hand
{color_line}
- Portrait or landscape
- Minimal or ADHD-friendly daily pages (time blocks, energy and focus check,
  brain dump)

WHAT YOU GET
- START HERE guide with step-by-step setup for your tablet
- 4 ZIP files: Portrait Minimal, Portrait ADHD, Landscape Minimal, Landscape ADHD

PLEASE NOTE
- This is a digital download. Nothing will be shipped.
- Made for the {dev.label}. Other tablets may show it at a different size.
- Tap links with your finger; write with your pen.
- Questions or trouble with a file? Send me a message and I'll help.
"""


# --- main ----------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--device", choices=sorted(DEVICES), required=True)
    ap.add_argument("-o", "--output", default="etsy")
    a = ap.parse_args(argv)
    dev = DEVICES[a.device]
    out = Path(a.output) / dev.slug
    out.mkdir(parents=True, exist_ok=True)
    colors = not dev.grayscale_only
    base = Options(dev, color_mode="eink_color" if colors else "bw")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        p = Planner(base, tmp)
        p_adhd = Planner(replace(base, daily_style="adhd"), tmp)
        p_sun = Planner(replace(base, week_start="sun"), tmp)
        p_left = Planner(replace(base, handedness="left"), tmp)
        p_land = Planner(replace(base, orientation="landscape"), tmp)
        variants = [("Monday start", p, "January 2027", 0.42),
                    ("Sunday start", p_sun, "January 2027", 0.42),
                    ("Right-handed", p, "Home"), ("Left-handed", p_left, "Home")]
        if colors:
            variants.append(("Black & white", Planner(replace(base, color_mode="bw"), tmp),
                             "Home"))
        variants.append(("Landscape", p_land, "Home"))

        files = ["START-HERE.pdf: setup guide"]
        per = 8 if colors else 4
        for o in ("Portrait", "Landscape"):
            for s in ("Minimal", "ADHD"):
                files.append(f"{o} {s} (ZIP, {per} planners)")
        steps = [("01_hero", lambda f: img_hero(p, dev, f)),
                 ("02_navigation", lambda f: img_navigation(p, f)),
                 ("03_inside", lambda f: img_inside(p, f)),
                 ("04_daily_styles", lambda f: img_daily(p, p_adhd, f)),
                 ("05_options", lambda f: img_options(variants, f)),
                 ("06_templates", lambda f: img_templates(p, f)),
                 ("07_projects", lambda f: img_projects(p, f)),
                 ("08_whats_included", lambda f: img_included(dev, files, p, f))]
        for name, fn in steps:
            path = out / f"{name}.png"
            fn(path)
            print(f"wrote {path}")
        (out / "listing.md").write_text(listing_copy(dev, p, colors))
        print(f"wrote {out / 'listing.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
