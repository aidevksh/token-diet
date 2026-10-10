import datetime as dt
from ledger.money import parse_amount, split_evenly, apply_discount
from ledger.periods import add_months, billing_periods


def test_parse_amount():
    assert parse_amount("₩1,234") == 1234
    assert parse_amount("1,234원") == 1234
    assert parse_amount("-500") == -500


def test_split_evenly():
    assert split_evenly(10000, 3) == [3334, 3333, 3333]
    assert sum(split_evenly(10, 4)) == 10


def test_apply_discount():
    assert apply_discount(10000, 15) == 8500


def test_add_months():
    assert add_months(dt.date(2025, 1, 15), 1) == dt.date(2025, 2, 15)
    assert add_months(dt.date(2025, 1, 31), 1) == dt.date(2025, 2, 28)


def test_billing_periods():
    p = billing_periods(dt.date(2025, 1, 10), 2)
    assert p == [(dt.date(2025, 1, 10), dt.date(2025, 2, 9)), (dt.date(2025, 2, 10), dt.date(2025, 3, 9))]
