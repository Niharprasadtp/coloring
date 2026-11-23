#!/usr/bin/env python3
"""Audit planner PDFs and export high-resolution PNG previews for Etsy listings.

Audit (per PDF), fails with exit code 1 on any problem:
  * every link is an internal GoTo to an existing page        -> 0 broken links
  * no two tap targets on a page overlap                      -> 0 overlapping targets
  * every tap target is at least the minimum size (8 mm)      -> 0 undersized targets
  * every page except the cover is reachable from another page
  * calendar accuracy, checked against Python's datetime: 396 contiguous daily pages,
    the weekday and ISO week printed on each, 13 monthly and 57 weekly pages
  * link correctness: monthly pages link every date to its daily page, daily pages link
    to the previous/next day and their month, Year at a Glance covers all days and months

Previews: Cover, Home, Year at a Glance, Monthly, Weekly, Daily, Project Hub and Template
Index as PNGs. DPI is physical, measured on the tablet's real screen size (page units are
device pixels), so 300 DPI gives roughly 2100 x 2800 px for the reMarkable Paper Pro.

Usage:
  python verify_and_preview.py output/*.pdf                # audit + previews per PDF
  python verify_and_preview.py --build --device remarkable_pro   # build minimal + ADHD, then both
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import pymupdf

START, END = date(2026, 12, 1), date(2027, 12, 31)
PREVIEW_DATE = date(2027, 1, 13)
DAY_TITLE = "%A, %B %d, %Y"


# --- audit ---------------------------------------------------------------------------
@dataclass
class Report:
    pdf: str
    pages: int = 0
    links: int = 0
    broken: list = field(default_factory=list)
    overlaps: list = field(default_factory=list)
    small: list = field(default_factory=list)
    orphans: list = field(default_factory=list)
    calendar: list = field(default_factory=list)
    linking: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.broken or self.overlaps or self.small or self.orphans
                    or self.calendar or self.linking)

    def summary(self) -> str:
        rows = [
            ("pages", self.pages, None), ("links", self.links, None),
            ("broken links", len(self.broken), self.broken),
            ("overlapping tap targets", len(self.overlaps), self.overlaps),
            ("undersized tap targets", len(self.small), self.small),
            ("unreachable pages", len(self.orphans), self.orphans),
            ("calendar errors", len(self.calendar), self.calendar),
            ("link-target errors", len(self.linking), self.linking),
        ]
        out = [f"{'PASS' if self.ok else 'FAIL'}  {self.pdf}"]
        for name, n, items in rows:
            out.append(f"    {name:<26}{n}")
            for it in (items or [])[:5]:
                out.append(f"        - {it}")
            if items and len(items) > 5:
                out.append(f"        ... {len(items) - 5} more")
        return "\n".join(out)


def pdf_meta(doc) -> dict:
    kw = doc.metadata.get("keywords") or ""
    return dict(p.split("=", 1) for p in kw.split(";") if "=" in p)


def toc_index(doc) -> dict:
    """Map the outline into lookups: title -> page index, plus typed groups."""
    toc = doc.get_toc(simple=True)
    out = {"by_title": {}, "daily": {}, "monthly": {}, "weekly": [], "year": []}
    stack: list[str] = []
    for level, title, page in toc:
        stack[level - 1:] = [title]
        root = stack[0]
        pno = page - 1
        out["by_title"].setdefault(title, pno)
        if root == "Daily" and level == 3:
            out["daily"][title] = pno
        elif root == "Monthly" and level == 2:
            out["monthly"][title] = pno
        elif root == "Weekly" and level == 2:
            out["weekly"].append((title, pno))
        elif root == "Year at a Glance":
            out["year"].append(pno)
    out["year"] = sorted(set(out["year"]))
    return out


def audit(path: str | Path) -> Report:
    doc = pymupdf.open(str(path))
    rep = Report(str(path), pages=doc.page_count)
    md = pdf_meta(doc)
    k = float(md.get("ppi", 72)) / 25.4
    min_mm = float(md.get("tap_min_mm", 8))
    eps = (0.05 * k) ** 2
    targets_from: dict[int, set[int]] = {}
    reached: set[int] = set()

    for pno, page in enumerate(doc):
        rects, outs = [], set()
        for ln in page.get_links():
            rep.links += 1
            where = f"p{pno + 1}"
            if ln["kind"] == pymupdf.LINK_GOTO:
                tgt = ln.get("page", -1)
            elif ln["kind"] == pymupdf.LINK_NAMED:
                tgt = ln.get("page", -1)
            else:
                rep.broken.append(f"{where}: non-internal link {ln.get('uri') or ln['kind']}")
                continue
            if not (0 <= tgt < doc.page_count):
                rep.broken.append(f"{where}: link to missing page {tgt + 1}")
                continue
            outs.add(tgt)
            if tgt != pno:
                reached.add(tgt)
            r = ln["from"]
            w, h = r.width / k, r.height / k
            if min(w, h) < min_mm - 0.01:
                rep.small.append(f"{where}: {w:.1f} x {h:.1f} mm -> p{tgt + 1}")
            rects.append((r, tgt))
        for (a, ta), (b, tb) in itertools.combinations(rects, 2):
            inter = pymupdf.Rect(a) & b
            if not inter.is_empty and inter.width * inter.height > eps:
                rep.overlaps.append(f"p{pno + 1}: targets -> p{ta + 1} and p{tb + 1}")
        targets_from[pno] = outs
    rep.orphans = [f"p{p + 1}" for p in range(1, doc.page_count) if p not in reached]
    _audit_calendar(doc, md, rep, targets_from)
    return rep


def _expected_iso_week(d: date, week_start: str) -> int:
    # Sunday-start rows are labelled by their Monday, so a Sunday takes the next ISO week.
    if week_start == "sun" and d.weekday() == 6:
        d = d + timedelta(days=1)
    return d.isocalendar()[1]


def _audit_calendar(doc, md: dict, rep: Report, targets: dict[int, set[int]]) -> None:
    idx = toc_index(doc)
    week_start = md.get("week_start", "mon")
    days: dict[date, int] = {}
    for title, pno in idx["daily"].items():
        d = datetime.strptime(title, DAY_TITLE).date()
        # strptime ignores %A, so check the weekday name independently.
        if title.split(",")[0] != d.strftime("%A"):
            rep.calendar.append(f"{title}: weekday should be {d.strftime('%A')}")
        days[d] = pno
    expected = [START + timedelta(days=i) for i in range((END - START).days + 1)]
    if sorted(days) != expected:
        missing = sorted(set(expected) - set(days))[:3]
        rep.calendar.append(f"daily pages: {len(days)} found, expected {len(expected)}; missing {missing}")
    for d, pno in days.items():
        text = doc[pno].get_text()
        wk = _expected_iso_week(d, week_start)
        if d.strftime("%A") not in text:
            rep.calendar.append(f"{d}: weekday name not printed on its page")
        if not re.search(rf"\bW(?:eek )?{wk:02d}\b", text):
            rep.calendar.append(f"{d}: ISO week {wk:02d} label not found")
        if not re.search(rf"(?m)^{d.day}$", text):
            rep.calendar.append(f"{d}: day number not printed")
    if len(idx["monthly"]) != 13:
        rep.calendar.append(f"monthly pages: {len(idx['monthly'])}, expected 13")
    if len(idx["weekly"]) != 57:
        rep.calendar.append(f"weekly pages: {len(idx['weekly'])}, expected 57")

    # Link correctness against the calendar.
    months = {}
    for title, pno in idx["monthly"].items():
        dt = datetime.strptime(title, "%B %Y")
        months[(dt.year, dt.month)] = pno
    for (y, mo), pno in months.items():
        want = {p for d, p in days.items() if (d.year, d.month) == (y, mo)}
        if not want <= targets[pno]:
            rep.linking.append(f"{y}-{mo:02d}: monthly page misses {len(want - targets[pno])} day links")
    for d, pno in days.items():
        need = {months[(d.year, d.month)]}
        for other in (d - timedelta(days=1), d + timedelta(days=1)):
            if other in days:
                need.add(days[other])
        if not need <= targets[pno]:
            rep.linking.append(f"{d}: daily page misses prev/next/month links")
    yag = set().union(*(targets[p] for p in idx["year"])) if idx["year"] else set()
    if not set(days.values()) <= yag:
        rep.linking.append(f"Year at a Glance misses {len(set(days.values()) - yag)} day links")
    if not set(months.values()) <= yag:
        rep.linking.append("Year at a Glance misses month links")


# --- previews --------------------------------------------------------------------------
def preview_pages(doc) -> list[tuple[str, int]]:
    idx = toc_index(doc)
    md = pdf_meta(doc)
    by = idx["by_title"]
    style = md.get("daily_style", "minimal")
    week = next((p for t, p in idx["weekly"]
                 if p is not None and _week_contains(t, PREVIEW_DATE)), idx["weekly"][0][1])
    out = [
        ("01_cover", by.get("Cover")),
        ("02_home", by.get("Home")),
        ("03_year_at_a_glance", idx["year"][0] if idx["year"] else None),
        ("04_monthly", idx["monthly"].get("January 2027")),
        ("05_weekly", week),
        (f"06_daily_{style}", idx["daily"].get(PREVIEW_DATE.strftime(DAY_TITLE))),
        ("07_project_hub", by.get("Project 01 · Plan")),
        ("08_template_index", by.get("Template Library")),
    ]
    return [(n, p) for n, p in out if p is not None]


def _week_contains(title: str, d: date) -> bool:
    m = re.search(r"· (\w{3}) (\d+)(?:, (\d{4}))? – (?:(\w{3}) )?(\d+), (\d{4})", title)
    if not m:
        return False
    m1, d1, y1, m2, d2, y2 = m.groups()
    end = datetime.strptime(f"{m2 or m1} {d2} {y2}", "%b %d %Y").date()
    return end - timedelta(days=6) <= d <= end


def export_previews(path: str | Path, outdir: Path, dpi: int = 300, only: set[str] | None = None) -> list[Path]:
    doc = pymupdf.open(str(path))
    ppi = float(pdf_meta(doc).get("ppi", 72))
    zoom = dpi / ppi
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, pno in preview_pages(doc):
        if only and not any(name.startswith(o) for o in only):
            continue
        pix = doc[pno].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        pix.set_dpi(dpi, dpi)
        f = outdir / f"{name}.png"
        pix.save(str(f))
        written.append(f)
    return written


# --- CLI ----------------------------------------------------------------------------------
def _build_samples(a) -> list[Path]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from eink_planner import DEVICES, Options, build
    paths = []
    for style in ("minimal", "adhd"):
        o = Options(DEVICES[a.device], a.orientation, a.week_start, a.handedness, a.color_mode, style)
        p = Path(a.build_dir) / f"{o.file_stem()}.pdf"
        build(o, p)
        print(f"built {p}")
        paths.append(p)
    return paths


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="*", help="planner PDFs or folders to search")
    ap.add_argument("--previews", default="previews", help="preview output folder")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--no-previews", action="store_true")
    ap.add_argument("--build", action="store_true",
                    help="build a minimal and an ADHD planner first, then audit and preview both")
    ap.add_argument("--build-dir", default="output/samples")
    ap.add_argument("--device", default="remarkable_pro")
    ap.add_argument("--orientation", default="portrait")
    ap.add_argument("--week-start", default="mon")
    ap.add_argument("--handedness", default="right")
    ap.add_argument("--color-mode", default="eink_color")
    a = ap.parse_args(argv)

    pdfs: list[Path] = []
    for p in map(Path, a.pdfs):
        pdfs += sorted(p.rglob("*.pdf")) if p.is_dir() else [p]
    if a.build:
        built = _build_samples(a)
        pdfs += built
    if not pdfs:
        ap.error("no PDFs given (pass files/folders or use --build)")

    all_ok = True
    for pdf in pdfs:
        rep = audit(pdf)
        print(rep.summary())
        all_ok &= rep.ok

    if not a.no_previews:
        root = Path(a.previews)
        if a.build:
            # One flat folder: every page from the minimal build plus the ADHD daily page.
            files = export_previews(built[0], root, a.dpi)
            files += export_previews(built[1], root, a.dpi, only={"06_daily"})
        else:
            files = []
            for pdf in pdfs:
                files += export_previews(pdf, root / pdf.stem if len(pdfs) > 1 else root, a.dpi)
        for f in files:
            print(f"preview {f}")
    print("ALL CHECKS PASSED" if all_ok else "CHECKS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
