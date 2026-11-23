"""Plan every page (key, outline entries, nav state) up front, then render in order.

Because every destination key is known before the first page is drawn, links can
point forward and `Ink.link` can reject a link to a page that does not exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from reportlab.pdfgen import canvas

from . import calendar_model as cal
from .chrome import Chrome, month_key
from .devices import Metrics, Options
from .geometry import Rect
from .ink import Ink
from .theme import theme_for
from .widgets import day_key, week_key

N_BRAIN_DUMP = 5
N_PROJECTS = 10


@dataclass
class PageSpec:
    key: str
    render: Callable
    outline: list[tuple[str, int]]
    section: str | None = None
    month: tuple[int, int] | None = None
    data: dict = field(default_factory=dict)


class Planner:
    def __init__(self, opts: Options):
        self.opts = opts
        self.m = Metrics(opts)
        self.t = theme_for(opts.effective_color_mode)
        self.chrome = Chrome(opts, self.m, self.t)
        self.content: Rect = self.chrome.content
        self.fw = opts.first_weekday
        self.weeks = cal.all_weeks(self.fw)
        self.week_keys = {week_key(w) for w in self.weeks}
        self.ink: Ink | None = None
        self.specs = self._plan()
        self.keys = {s.key for s in self.specs}

    @property
    def body(self) -> Rect:
        """Area below a standard page header."""
        return self.content.pad(top=self.m.tap + self.m.space)

    # --- plan --------------------------------------------------------------
    def _plan(self) -> list[PageSpec]:
        from .pages import calendar_pages as cp
        from .pages import daily, templates, weekly, workspace

        specs: list[PageSpec] = []

        def add(key, render, outline, section=None, month=None, **data):
            specs.append(PageSpec(key, render, outline, section, month, data))

        add("cover", cp.cover, [("Cover", 0)])
        add("home", cp.home, [("Home", 0)], "home")

        chunks = cp.year_chunks(self)
        for i, months in enumerate(chunks):
            outline = [("Year at a Glance", 0)] if i == 0 else []
            if len(chunks) > 1:
                outline.append((f"Year at a Glance {i + 1}/{len(chunks)}", 1))
            add(f"year-{i + 1}", cp.year_page, outline, "year", months=months, index=i,
                count=len(chunks))

        for q in range(1, 5):
            pages = cp.quarter_plan(self, q)
            for j, (mode, months) in enumerate(pages):
                outline = []
                if q == 1 and j == 0:
                    outline.append(("Quarterly Planning", 0))
                if j == 0:
                    outline.append((f"Q{q} 2027 Overview", 1))
                key = f"q{q}" if j == 0 else f"q{q}-{j + 1}"
                add(key, cp.quarter_page, outline, f"q{q}", q=q, mode=mode, months=months,
                    index=j, count=len(pages))
            add(f"q{q}-goals", cp.quarter_goals, [(f"Q{q} 2027 Goals & Review", 1)], f"q{q}", q=q)

        for i, (y, mo) in enumerate(cal.MONTHS):
            outline = ([("Monthly", 0)] if i == 0 else []) + [(cal.month_label(y, mo), 1)]
            add(month_key(y, mo), cp.month_page, outline, None, (y, mo), year=y, mon=mo)
            if self.m.compact:
                add(month_key(y, mo) + "-h", cp.month_habits,
                    [(f"{cal.month_label(y, mo)} Focus & Habits", 2)], None, (y, mo), year=y, mon=mo)

        for i, start in enumerate(self.weeks):
            wk = cal.iso_week(start, self.fw)[1]
            outline = ([("Weekly", 0)] if i == 0 else [])
            outline.append((f"Week {wk:02d} · {weekly.range_label(start)}", 1))
            add(week_key(start), weekly.week_page, outline, None, weekly.nav_month(start),
                start=start, index=i)

        for d in cal.all_days():
            outline = [("Daily", 0)] if d == cal.START else []
            if d.day == 1:
                outline.append((cal.month_label(d.year, d.month), 1))
            outline.append((f"{cal.DAY_NAMES[d.weekday()]}, {cal.MONTH_NAMES[d.month]} {d.day}, {d.year}", 2))
            add(day_key(d), daily.day_page, outline, None, (d.year, d.month), day=d)

        for i in range(1, N_BRAIN_DUMP + 1):
            outline = ([("Brain Dump", 0)] if i == 1 else []) + [(f"Brain Dump {i}", 1)]
            add(f"bd-{i}", workspace.brain_dump, outline, "braindump", index=i)

        add("projects", workspace.project_index, [("Projects", 0), ("Project Index", 1)], "projects")
        for i in range(1, N_PROJECTS + 1):
            name = f"Project {i:02d}"
            add(f"p{i}-plan", workspace.project_plan, [(name, 1), (f"{name} · Plan", 2)],
                "projects", n=i)
            add(f"p{i}-board", workspace.project_board, [(f"{name} · Timeline & Board", 2)],
                "projects", n=i)
            add(f"p{i}-notes", workspace.project_notes, [(f"{name} · Meeting Notes", 2)],
                "projects", n=i)

        add("templates", templates.template_index, [("Templates", 0), ("Template Library", 1)],
            "templates")
        for slug, title, _ in templates.TEMPLATES:
            add(f"t-{slug}", templates.template_page, [(title, 1)], "templates", slug=slug)
        return specs

    # --- render ------------------------------------------------------------
    def build(self, path: str | Path) -> dict:
        o, m = self.opts, self.m
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(path), pagesize=(m.W, m.H), pageCompression=1, invariant=1)
        c.setTitle("2027 Digital Planner")
        c.setAuthor("")
        c.setSubject(f"{o.device.label} · {o.orientation} · Dec 2026 – Dec 2027")
        c.setCreator("eink_planner")
        c.setKeywords(";".join([
            f"device={o.device.key}", f"ppi={m.ppi}", f"tap_min_mm={m.tap_min_mm}",
            f"orientation={o.orientation}", f"week_start={o.week_start}",
            f"handedness={o.handedness}", f"color_mode={o.effective_color_mode}",
            f"daily_style={o.daily_style}"]))
        self.ink = Ink(c, m, self.t, self.keys)
        for spec in self.specs:
            self.ink.start_page(spec.key)
            c.bookmarkPage(spec.key, fit="Fit")
            for n, (title, level) in enumerate(spec.outline):
                # ReportLab identifies outline entries by key, so group headings that
                # start on this page get their own bookmark name.
                k = spec.key if n == len(spec.outline) - 1 else f"{spec.key}~{n}"
                if k != spec.key:
                    c.bookmarkPage(k, fit="Fit")
                c.addOutlineEntry(title, k, level, closed=True)
            self.chrome.draw(self.ink, spec.section, spec.month)
            spec.render(self, spec)
            c.showPage()
        c.save()
        return {"path": str(path), "pages": len(self.specs), "links": self.ink.link_count}


def build(opts: Options, path: str | Path) -> dict:
    return Planner(opts).build(path)
