import calendar as _cal
from datetime import date, timedelta


def is_eligible(member: dict, d: date) -> bool:
    start = date.fromisoformat(member["start_date"])
    end = date.fromisoformat(member["end_date"])
    if not (start <= d <= end):
        return False
    if not member["include_weekends"] and d.weekday() >= 5:
        return False
    return True


def count_eligible_days(member: dict) -> int:
    start = date.fromisoformat(member["start_date"])
    end = min(date.fromisoformat(member["end_date"]), date.today())
    if start > end:
        return 0
    count = 0
    d = start
    while d <= end:
        if member["include_weekends"] or d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return count


def get_month_weeks(year: int, month: int):
    """Returns list of weeks; each week = [Sun, Mon, ..., Sat] with 0 for padding."""
    cal = _cal.Calendar(firstweekday=6)  # Sunday first
    return cal.monthdayscalendar(year, month)


def adj_month(year: int, month: int, delta: int):
    m = month + delta
    if m < 1:
        return year - 1, 12
    if m > 12:
        return year + 1, 1
    return year, m
