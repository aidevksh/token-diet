import datetime as dt
import pytest
from ledger.money import parse_amount, split_evenly, apply_discount
from ledger.tax import vat_breakdown
from ledger.periods import add_months, billing_periods


def test_parse_parentheses_negative():
    assert parse_amount("(1,000)") == -1000
    assert parse_amount(" ₩(2,500) ") == -2500 or parse_amount("(₩2,500)") == -2500
    with pytest.raises(ValueError):
        parse_amount("12a")


@pytest.mark.parametrize("total,n", [(10000, 3), (10, 4), (7, 7), (5, 8), (100001, 6), (-10, 3)])
def test_split_sum_and_order(total, n):
    s = split_evenly(total, n)
    assert len(s) == n and sum(s) == total
    assert max(s) - min(s) <= 1
    assert s == sorted(s, reverse=True)


def test_vat():
    assert vat_breakdown(11000) == (10000, 1000)
    assert vat_breakdown(10000) == (9091, 909)
    assert vat_breakdown(55) == (50, 5)
    s, v = vat_breakdown(1234567)
    assert s + v == 1234567 and s == 1122334


def test_add_months_clamp():
    assert add_months(dt.date(2024, 1, 31), 1) == dt.date(2024, 2, 29)
    assert add_months(dt.date(2025, 3, 31), -1) == dt.date(2025, 2, 28)
    assert add_months(dt.date(2025, 8, 31), 1) == dt.date(2025, 9, 30)
    assert add_months(dt.date(2025, 11, 30), 3) == dt.date(2026, 2, 28)


def test_billing_month_end_anchor():
    p = billing_periods(dt.date(2025, 1, 31), 3)
    assert p[0] == (dt.date(2025, 1, 31), dt.date(2025, 2, 27))
    assert p[1][0] == dt.date(2025, 2, 28)
    assert p[2] == (dt.date(2025, 3, 31), dt.date(2025, 4, 29))


def test_discount():
    assert apply_discount(999, 33) == 669
    assert apply_discount(1000, 0) == 1000
