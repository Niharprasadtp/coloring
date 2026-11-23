"""Calendar math for the Dec 2026 - Dec 2027 span. Everything derives from datetime."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

START = date(2026, 12, 1)
END = date(2027, 12, 31)
YEAR = 2027

MONTHS: list[tuple[int, int]] = [(2026, 12)] + [(YEAR, m) for m in range(1, 13)]
MONTH_NAMES = list(calendar.month_name)          # ['', 'January', ...]
MONTH_ABBR = list(calendar.month_abbr)           # ['', 'Jan', ...]
DAY_NAMES = list(calendar.day_name)              # Monday first
DAY_ABBR = list(calendar.day_abbr)


def in_range(d: date) -> bool:
    return START <= d <= END


def all_days() -> list[date]:
    return [START + timedelta(days=i) for i in range((END - START).days + 1)]


def week_start(d: date, first_weekday: int) -> date:
    return d - timedelta(days=(d.weekday() - first_weekday) % 7)


def all_weeks(first_weekday: int) -> list[date]:
    out, s = [], week_start(START, first_weekday)
    while s <= END:
        out.append(s)
        s += timedelta(days=7)
    return out


def week_days(start: date) -> list[date]:
    return [start + timedelta(days=i) for i in range(7)]


def iso_week(start: date, first_weekday: int) -> tuple[int, int]:
    """ISO (year, week) of the row. Sunday-start rows are labelled by their Monday."""
    monday = start if first_weekday == 0 else start + timedelta(days=1)
    iso = monday.isocalendar()
    return iso[0], iso[1]


def weekday_order(first_weekday: int) -> list[int]:
    return [(first_weekday + i) % 7 for i in range(7)]


def month_rows(year: int, month: int, first_weekday: int, fixed: int | None = None) -> list[date]:
    """Start dates of the week rows that cover the month (optionally padded to `fixed`)."""
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    rows, s = [], week_start(first, first_weekday)
    while s <= last:
        rows.append(s)
        s += timedelta(days=7)
    while fixed and len(rows) < fixed:
        rows.append(rows[-1] + timedelta(days=7))
    return rows


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def quarter_of(year: int, month: int) -> int:
    """Quarter 1-4 (December 2026 is Q4 of 2026, which shares Q4's accent)."""
    return (month - 1) // 3 + 1


def quarter_months(q: int) -> list[tuple[int, int]]:
    return [(YEAR, m) for m in range(3 * q - 2, 3 * q + 1)]


def month_label(year: int, month: int, short: bool = False) -> str:
    if short:
        return f"{MONTH_ABBR[month]} '{year % 100:02d}"
    return f"{MONTH_NAMES[month]} {year}"


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def day_of_year(d: date) -> int:
    return d.timetuple().tm_yday
