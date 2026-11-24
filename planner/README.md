# 2027 E-Ink Digital Planner Generator

A Python CLI that builds a Hobonichi-inspired digital planner PDF for E-Ink tablets. It
spans **December 2026 through December 2027**, is drawn entirely in vectors with
ReportLab, and has every section linked internally. A companion QA script audits every
link and exports PNG previews for Etsy listings.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# One planner
python make_planner.py --device remarkable_pro --orientation portrait \
    --week-start mon --handedness right --color-mode eink_color --daily-style minimal

# Every week-start × handedness × color variant for one device
python make_planner.py --device remarkable_move --batch-all --zip -o output

# The complete Etsy download set for one device: START-HERE.pdf + 4 ZIPs
# (portrait/landscape × minimal/ADHD), checked against Etsy's 5 files / 20 MB limits
python make_planner.py --device remarkable_pro --etsy -o output

# Etsy listing images (4:3 PNGs from the real pages) + listing.md (title, tags, description)
python etsy_assets.py --device remarkable_pro -o etsy

# Audit + 300-DPI previews (builds a minimal and an ADHD planner first)
python verify_and_preview.py --build --device remarkable_pro --previews previews

# Audit existing PDFs (files or folders)
python verify_and_preview.py output/ --no-previews
```

| Flag | Values | Notes |
|---|---|---|
| `--device` | see [Devices](#devices) | page size = native pixels |
| `--orientation` | `portrait`, `landscape` | |
| `--week-start` | `mon`, `sun` | |
| `--handedness` | `right`, `left` | month rail goes on the opposite side |
| `--color-mode` | `eink_color`, `bw` | grayscale-only screens always use `bw` |
| `--daily-style` | `minimal`, `adhd` | ADHD adds time-block bar, energy/focus check, brain dump |
| `--batch-all` | | 8 variants (4 on grayscale-only screens) in `<Device>_<Orientation>_<Style>/<Variant>/`, plus START-HERE.pdf |
| `--zip` | | with `--batch-all`, zip each variant folder |
| `--etsy` | | every orientation × style × variant, packed as Etsy's 5 downloadable files |

A full planner has 540–560 pages and 15–16k links, takes about 3 s to build, and
comes out at about 5–6 MB (about 2 MB zipped).

## Devices

| Preset | Device | Page (pt = px) | PPI | Color | Notes |
|---|---|---|---|---|---|
| `remarkable_pro` | reMarkable Paper Pro | 1620 × 2160 | 229 | yes | |
| `remarkable_move` | reMarkable Paper Pro Move | 954 × 1696 | 264 | yes | compact layouts |
| `remarkable_2` | reMarkable 2 | 1404 × 1872 | 226 | no | |
| `kindle_scribe` | Kindle Scribe 11-inch (2025) | 1980 × 2640 | 300 | no | |
| `kindle_scribe_colorsoft` | Kindle Scribe Colorsoft | 1980 × 2640 | 300 | yes | color shows at 150 ppi |
| `kindle_scribe_10` | Kindle Scribe 10.2-inch (2022/2024) | 1860 × 2480 | 300 | no | |
| `supernote_manta` | Supernote Manta | 1920 × 2560 | 300 | no | |
| `supernote_nomad` | Supernote Nomad | 1404 × 1872 | 300 | no | compact layouts |

Each page is as many PDF points wide as the screen has pixels, so on the tablet one
page unit is one screen pixel. Everything physical is converted with the PPI: tap
targets and grid spacing in mm, type in pt. Tap targets are 9.5 mm (8 mm on compact
screens) and never below 8 mm.

Device quirks the layout handles:

- **reMarkable** draws its round toolbar button in the top corner on the side away from
  the writing hand, which is the month rail's side. The rail starts 14 mm lower so no
  tab sits under the button. Links only work when the PDF is opened as a document.
- **Tall, narrow screens** (Move, Nomad in portrait) get a second top-bar row for Q1–Q4
  instead of squeezing the month rail into two columns.
- Nav keeps 2.5–3 mm clear of the screen edge, where taps are unreliable on some tablets.
- Color E-Ink (Gallery 3, Kaleido 3) shows colors paler than a monitor, so the color
  palette is a little more saturated than it looks on screen.

## What's inside

1. **Cover**, **Home dashboard** and a **How to use** page. Home links to the year, the
   quarters, all 13 months, the workspace sections and every week. Dec 2026 and
   Dec 2027 both have weeks 49–52, so Home labels the two years apart.
2. **Year at a Glance**: every month name links to its monthly page and every date to
   its daily page. It runs to 3 pages on Pro/Scribe and 7 on Move, because every date
   keeps a full-size tap target.
3. **Quarterly (Q1–Q4 2027)**: an overview calendar (dates → daily, week numbers →
   weekly) and a Goals & Review page.
4. **13 monthly pages**: week numbers → weekly pages, dates → daily pages, plus a
   Monthly Focus and Habit Tracker sidebar. On the Move the sidebar is a second page.
5. **57 weekly pages**: one page per week with each day linked, Weekly Priorities and a
   Habit Tracker.
6. **396 daily pages**: hourly timeline (6 AM–10 PM), Top 3 Priorities, To-Do,
   fine-grid Notes, prev/next day, month and week links.
7. **Brain Dump**: 5 grid, dot and blank pages.
8. **Projects**: an index and 10 hubs, each with Plan, Timeline/Kanban and Meeting Notes
   pages.
9. **Template library**: 23 duplicate-ready templates (Lined, Narrow Lined, Dot Grid,
   Fine Graph, Isometric, Cornell, Meeting Minutes, Priority Matrix, Pomodoro, Daily
   Routine, Habit Tracker, Reading Log, Monthly Budget, Bill Tracker, Debt Payoff,
   Savings, Meal Planner, Workout Log, Gratitude, Goal Planner, To-Do, Storyboard,
   Blank Sketch).

Every page carries the quick-jump bar: **Home | Year | Q1–Q4 | Brain Dump | Projects |
Templates** along the top and **Dec '26, Jan–Dec '27** on the side rail. On the Move in
portrait the top bar can't fit all nine items at 8 mm, so the quarter tabs move into
the rail. The PDF outline (bookmarks) mirrors the same structure.

ISO week numbers come from `datetime.isocalendar()`. Sunday-start weeks carry the ISO
number of their Monday. 2026 has 53 ISO weeks, so December 28, 2026 is in W53.

## Quality guarantees

The generator refuses to write a PDF that breaks the tap-target rules. `Ink.link()`
raises `LayoutError` if a target is under 8 mm on either side, overlaps another target
on the same page, or points to a page that doesn't exist.

`verify_and_preview.py` re-checks the finished PDF with PyMuPDF:

- 0 broken links: every link is an internal GoTo to an existing page
- 0 overlapping tap targets and 0 under the minimum size
- every page except the cover can be reached from another page
- calendar checked against `datetime`: 396 contiguous days, the correct weekday name,
  ISO week and day number printed on each, 13 monthly and 57 weekly pages
- each monthly page links every one of its dates; each daily page links prev/next day
  and its month; Year at a Glance covers every day and month

Repeated content (the nav chrome, grids and ruled lines) is written once as a PDF form
XObject and reused, which keeps a 540-page planner around 5–6 MB and quick to page
through on older tablets. The PDF itself stays a plain classic-xref file for maximum
reader compatibility.

Previews are written to `previews/`: cover, home, year at a glance, monthly, weekly,
daily (minimal and ADHD), project hub and template index. DPI is **physical**,
measured on the tablet's real screen, so 300 DPI on the reMarkable Paper Pro gives
2123 × 2830 px. That's the right size for listing mockups. Rendering at 300 DPI of the
nominal page size would give 60-megapixel images.

## Layout

```
make_planner.py          CLI entry
verify_and_preview.py    QA audit + previews
etsy_assets.py           Etsy listing images + listing copy
eink_planner/
  devices.py             presets, Options, Metrics (mm/pt → page units)
  theme.py               eink_color / bw palettes
  calendar_model.py      date span, weeks, ISO numbers, month matrices
  geometry.py            Rect slicing helpers
  ink.py                 drawing primitives, checked links
  chrome.py              top quick-jump strip + handed side rail
  widgets.py             headers, buttons, month blocks, tables, habit grids
  builder.py             page plan (keys, outline, nav state) → render
  cli.py                 flags, batch mode, zipping
  pages/                 calendar_pages, weekly, daily, workspace, templates,
                         guide (How to use page, START-HERE.pdf)
tests/
```

Every page is planned before anything is drawn, so links can point forward and unknown
destinations are caught. Layouts are composed from physical sizes and adapt to the
space available. For example, the Project Index and Template Library flow into more
columns, and the daily timeline wraps into two columns when the page is short.

Run the tests with `python -m pytest tests`.

## Selling on Etsy

1. `python make_planner.py --device <preset> --etsy -o output`: upload the 5 files in
   `output/Etsy_<Device>/` as the listing's digital files.
2. `python etsy_assets.py --device <preset> -o etsy`: upload the 8 PNGs as listing
   photos and paste the title, tags and description from `listing.md`.
3. Before the first sale on a device, load one planner onto the real tablet and tap
   through it. The audit proves every link is correct in the file; only a real device
   shows how its reader handles taps. Supernote firmware differs on whether a finger or
   pen tap follows a link, which the START HERE guide covers.
4. Keep brand names out of the listing except to say which device it is for
   ("for reMarkable Paper Pro"), and check Etsy's current creativity and AI disclosure
   rules for digital downloads when you publish.
