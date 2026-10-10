import datetime as dt


def add_months(d, n):
    """Add n months to date d, clamping the day to the end of the target month."""
    y, m = divmod(d.month - 1 + n, 12)
    return d.replace(year=d.year + y, month=m + 1)


def billing_periods(start, count):
    """Return `count` monthly (start, end) periods; end is the day before the next start."""
    out = []
    for i in range(count):
        s = add_months(start, i)
        e = add_months(start, i + 1) - dt.timedelta(days=1)
        out.append((s, e))
    return out
