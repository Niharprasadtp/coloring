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

# Every week-start × handedness × color variant for one device, zipped for Etsy
python make_planner.py --device remarkable_move --batch-all --zip -o output

# Audit + 300-DPI previews (builds a minimal and an ADHD planner first)
python verify_and_preview.py --build --device remarkable_pro --previews previews

# Audit existing PDFs (files or folders)
python verify_and_preview.py output/ --no-previews
```

| Flag | Values | Notes |
|---|---|---|
| `--device` | `remarkable_pro`, `remarkable_move`, `kindle_scribe` | page size = native pixels |
| `--orientation` | `portrait`, `landscape` | |
| `--week-start` | `mon`, `sun` | |
| `--handedness` | `right`, `left` | month rail goes on the opposite side |
| `--color-mode` | `eink_color`, `bw` | Kindle Scribe always uses `bw` |
| `--daily-style` | `minimal`, `adhd` | ADHD adds time-block bar, energy/focus check, brain dump |
| `--batch-all` | | 8 variants (4 on Kindle Scribe) in `<Device>_<Orientation>_<Style>/<Variant>/` |
| `--zip` | | with `--batch-all`, zip each variant folder |

A full planner has about 540 pages and 15–16k links, takes about 4 s to build, and
comes out at about 7 MB.

## Devices

| Preset | Page (pt = px) | PPI | Tap target | Notes |
|---|---|---|---|---|
| `remarkable_pro` | 1620 × 2160 | 229 | 9.5 mm | 4:3 |
| `remarkable_move` | 954 × 1696 | 264 | 8 mm | 16:9, compact layouts (not a shrunk 4:3 layout) |
| `kindle_scribe` | 1860 × 2480 | 300 | 9.5 mm | 4:3, high-contrast grayscale |

Each page is as many PDF points wide as the screen has pixels, so on the tablet one
page unit is one screen pixel. Everything physical is converted with the PPI: tap
targets and grid spacing in mm, type in pt. That keeps a 9 mm button 9 mm wide on
every device.

## What's inside

1. **Cover** and **Home dashboard**: links to the year, the quarters, all 13 months,
   the workspace sections and every week.
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

Previews are written to `previews/`: cover, home, year at a glance, monthly, weekly,
daily (minimal and ADHD), project hub and template index. DPI is **physical**,
measured on the tablet's real screen, so 300 DPI on the reMarkable Paper Pro gives
2123 × 2830 px. That's the right size for listing mockups. Rendering at 300 DPI of the
nominal page size would give 60-megapixel images.

## Layout

```
make_planner.py          CLI entry
verify_and_preview.py    QA audit + previews
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
  pages/                 calendar_pages, weekly, daily, workspace, templates
tests/
```

Every page is planned before anything is drawn, so links can point forward and unknown
destinations are caught. Layouts are composed from physical sizes and adapt to the
space available. For example, the Project Index and Template Library flow into more
columns, and the daily timeline wraps into two columns when the page is short.

Run the tests with `python -m pytest tests`.
