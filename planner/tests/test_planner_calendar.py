from datetime import date, timedelta

from eink_planner import calendar_model as cal


def test_span_and_counts():
    days = cal.all_days()
    assert days[0] == date(2026, 12, 1) and days[-1] == date(2027, 12, 31)
    assert len(days) == 396
    assert len(cal.MONTHS) == 13
    assert len(cal.all_weeks(0)) == 57 and len(cal.all_weeks(6)) == 57


def test_known_weekdays():
    assert date(2026, 12, 1).strftime("%A") == "Tuesday"
    assert date(2027, 1, 1).strftime("%A") == "Friday"


def test_weeks_cover_every_day_once():
    for fw in (0, 6):
        covered = [d for w in cal.all_weeks(fw) for d in cal.week_days(w) if cal.in_range(d)]
        assert covered == cal.all_days()
        assert all(w.weekday() == fw for w in cal.all_weeks(fw))


def test_iso_week_labels():
    # Monday-start rows carry their own ISO week; Sunday-start rows carry their Monday's.
    for w in cal.all_weeks(0):
        assert cal.iso_week(w, 0) == tuple(w.isocalendar()[:2])
    for w in cal.all_weeks(6):
        assert cal.iso_week(w, 6) == tuple((w + timedelta(days=1)).isocalendar()[:2])
    assert cal.iso_week(date(2026, 12, 28), 0) == (2026, 53)   # 2026 has 53 ISO weeks
    assert cal.iso_week(date(2027, 1, 4), 0) == (2027, 1)


def test_month_rows():
    rows = cal.month_rows(2027, 2, 0)   # Feb 2027 starts on a Monday and has 28 days
    assert rows[0] == date(2027, 2, 1) and len(rows) == 4
    assert len(cal.month_rows(2027, 2, 0, fixed=6)) == 6
