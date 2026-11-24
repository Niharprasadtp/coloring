"""Buyer guidance: the in-planner "How to use" page and the START HERE PDF.

Install steps and tips depend on the device family. Wording is deliberately
careful where devices differ (for example whether a link follows a finger or pen
tap) so the instructions stay true on every firmware.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfgen import canvas

from ..devices import Metrics, Options
from ..geometry import Rect
from ..ink import BOLD, REGULAR, Ink
from ..theme import theme_for
from ..widgets import page_header

INSTALL = {
    "remarkable": [
        ("Unzip the download", "Do this on your computer or phone first."),
        ("Add it to your tablet",
         "Drag the PDF into the reMarkable desktop app or my.remarkable.com, or use the "
         "mobile app. It syncs to your tablet."),
        ("Open it as a document",
         "Don't add it as a custom template: links only work when the PDF is a document."),
        ("Hide the toolbar",
         "Tap the round button in the top corner to close the toolbar so the month tabs "
         "underneath are free to tap."),
        ("Tap links with your finger", "The Marker writes; a fingertip follows links."),
    ],
    "kindle": [
        ("Unzip the download", "Do this on your computer or phone first."),
        ("Send it to your Kindle",
         "Open amazon.com/sendtokindle, sign in with the account on your Scribe and upload "
         "the PDF."),
        ("Keep it a PDF",
         "Don't pick any convert option. Converting reflows the pages and breaks the links."),
        ("Open it from your Library",
         "Give it a minute on Wi-Fi to arrive, then write on any page with the pen."),
        ("Tap links with your finger", "The pen writes; a fingertip follows links."),
    ],
    "supernote": [
        ("Unzip the download", "Do this on your computer or phone first."),
        ("Copy it to your Supernote",
         "Connect by USB, or use Supernote Partner or your cloud drive, and put the PDF in "
         "the Document folder."),
        ("Open it from Document", "Write on any page with your pen."),
        ("Tap a link to jump",
         "Use your fingertip. If a fingertip tap does nothing on your firmware, tap the "
         "link with the pen instead."),
    ],
}

TIP = {
    "remarkable": "Closed toolbar = every month tab within reach.",
    "kindle": "Write with the pen, navigate with your finger.",
    "supernote": "Every tab and date is at least 8 mm, easy to hit with a fingertip or pen.",
}

NAV = [
    ("Top bar", "Home, Year, Q1–Q4, Brain Dump, Projects and Templates, on every page."),
    ("Side tabs", "Every month from Dec '26 to Dec '27. The current month is highlighted."),
    ("Dates", "Tap any date on a year, quarter, month or week page to open that day."),
    ("Week numbers", "Tap W01–W52 to open that week's page."),
    ("Arrows", "The arrow buttons step to the previous or next month, week or day."),
    ("Home", "Shortcuts to every month, quarter, section and week."),
]

CHOOSE = [
    ("Mon-Start / Sun-Start", "Which day your weeks begin on."),
    ("Right-Hand / Left-Hand",
     "Your writing hand. The month tabs sit on the other side so your hand never covers "
     "them."),
    ("Color / BW", "Soft colors for color screens, or high-contrast black and white."),
    ("Minimal / ADHD",
     "ADHD daily pages add a time-block bar, an energy and focus check and a brain dump "
     "box."),
]


def _wrap(s: str, size: float, font: str, w: float) -> list[str]:
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if Ink.width(trial, size, font) <= w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _para(ink: Ink, x: float, y: float, w: float, s: str, size: float, font=REGULAR,
          color=None) -> float:
    """Wrapped paragraph from top y. Returns the y below it."""
    lead = size * 1.32
    for line in _wrap(s, size, font, w):
        y -= lead
        ink.text(x, y + size * 0.25, line, size, font, color)
    return y


def _items(ink: Ink, r: Rect, items, numbered: bool, title_size, body_size) -> float:
    """Title + description rows with a number badge or bullet. Returns final y."""
    m, t = ink.m, ink.t
    y = r.top
    badge = m.mm(5.2 if not m.compact else 4.4)
    tx = r.x + badge + m.mm(3)
    for i, (title, body) in enumerate(items, 1):
        cy = y - title_size * 0.75
        if numbered:
            ink.circle(r.x + badge / 2, cy, badge / 2, fill=t.accent)
            ink.text(r.x + badge / 2, cy - title_size * 0.32, str(i), title_size * 0.9, BOLD,
                     t.active_text, "center")
        else:
            ink.box(Rect(r.x + badge / 2 - m.mm(0.8), cy - m.mm(0.8), m.mm(1.6), m.mm(1.6)),
                    fill=t.accent)
        y = _para(ink, tx, y, r.right - tx, title, title_size, BOLD, t.ink)
        y = _para(ink, tx, y + body_size * 0.1, r.right - tx, body, body_size, REGULAR, t.soft)
        y -= m.mm(3.2 if not m.compact else 2.4)
    return y


def _variant_line(o: Options) -> str:
    return " · ".join([
        o.device.label, o.orientation.capitalize(),
        "Monday start" if o.week_start == "mon" else "Sunday start",
        "Right-handed" if o.handedness == "right" else "Left-handed",
        "Color" if o.effective_color_mode == "eink_color" else "Black & white",
        "ADHD daily pages" if o.daily_style == "adhd" else "Minimal daily pages",
    ])


def _two_cols(r: Rect, m: Metrics, landscape: bool) -> tuple[Rect, Rect | None]:
    if landscape:
        a, b = r.cols(2, m.space * 2.5)
        return a, b
    return r, None


def usage_page(P, spec) -> None:
    """In-planner page linked from Home."""
    ink, m, t, o = P.ink, P.m, P.t, P.opts
    body = page_header(ink, P.content, "How to use", "Finding your way around")
    ts, bs = m.fs_h, m.fs_body
    a, b = _two_cols(body, m, o.landscape)
    y = a.top - ink.label(a.x, a.top, "Navigation")
    y = _items(ink, Rect(a.x, a.y, a.w, y - a.y), NAV, False, ts, bs)
    col = b or Rect(a.x, a.y, a.w, y - m.space - a.y)
    y = col.top - ink.label(col.x, col.top, "Good to know")
    family = o.device.family
    tips = [
        ("Follow links", INSTALL[family][-1][1]),
        ("Your tablet", TIP[family]),
        ("Templates", "Blank layouts for anything the planner doesn't cover. If your tablet "
                      "can duplicate pages, copy one and keep the original clean."),
        ("This file", _variant_line(o)),
    ]
    _items(ink, Rect(col.x, col.y, col.w, y - col.y), tips, False, ts, bs)


def build_start_here(opts: Options, path: str | Path) -> str:
    """One-page buyer guide shipped next to the planners (no internal links)."""
    m, t = Metrics(opts), theme_for(opts.effective_color_mode)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=(m.W, m.H), pageCompression=1, invariant=1)
    c.setTitle("Start here: 2027 Digital Planner")
    c.setAuthor("")
    c.setCreator("eink_planner")
    ink = Ink(c, m, t, set())
    ink.start_page("start-here")
    r = Rect(m.margin, m.margin, m.W - 2 * m.margin, m.H - 2 * m.margin)
    ink.text(r.x, r.top - m.fs_label, "START HERE", m.fs_label, BOLD, t.muted,
             tracking=m.fs_label * 0.3)
    y = r.top - m.fs_label - m.mm(3)
    y = _para(ink, r.x, y, r.w, "Your 2027 Digital Planner", m.fs_title, BOLD, t.ink)
    y = _para(ink, r.x, y, r.w, f"December 2026 – December 2027 · made for {opts.device.label}",
              m.fs_body, REGULAR, t.soft)
    y -= m.space * 1.5
    ink.line(r.x, y, r.right, y, t.rule, m.lw_rule)
    y -= m.space * 1.5
    ts, bs = m.fs_h, m.fs_body
    a, b = _two_cols(Rect(r.x, r.y, r.w, y - r.y), m, opts.landscape)
    ya = a.top - ink.label(a.x, a.top, "Set up in a few minutes")
    ya = _items(ink, Rect(a.x, a.y, a.w, ya - a.y), INSTALL[opts.device.family], True, ts, bs)
    col = b or Rect(a.x, a.y, a.w, ya - m.space - a.y)
    yb = col.top - ink.label(col.x, col.top, "Pick your file")
    yb = _para(ink, col.x, yb, col.w,
               "Every combination is included. File names tell you which is which:",
               bs, REGULAR, t.soft) - m.mm(2.5)
    choose = [c for c in CHOOSE
              if not (opts.device.grayscale_only and c[0].startswith("Color"))]
    yb = _items(ink, Rect(col.x, col.y, col.w, yb - col.y), choose, False, ts, bs)
    for title, text in (
            ("Inside the planner", "Open the planner and tap Home, then How to use, for a "
                                   "one-page guide to the tabs, links and templates."),
            ("Need help?", "Send a message through Etsy. If a link or file doesn't behave "
                           "on your tablet, I'll help you sort it out.")):
        yb -= m.space
        yb -= ink.label(col.x, yb, title)
        yb = _para(ink, col.x, yb + bs * 0.3, col.w, text, bs, REGULAR, t.soft)
    c.showPage()
    c.save()
    return str(path)
