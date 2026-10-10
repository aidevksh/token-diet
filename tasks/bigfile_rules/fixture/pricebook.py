"""Bulk discount rules for the 2025 B2B price book.

Every rule takes (qty, unit) in won and returns the payable amount in won.
Discount = base * pct // 100 (floored), applied only when qty reaches the threshold.
When a rule has a cap, the discount (not the price) is capped.
"""


def _base(qty, unit):
    if qty < 0 or unit < 0:
        raise ValueError("negative input")
    return qty * unit


def price_rule_01(qty, unit):
    """Rule 01: 15% off at 20+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 15 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_02(qty, unit):
    """Rule 02: 7% off at 30+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_03(qty, unit):
    """Rule 03: 15% off at 100+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 15 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_04(qty, unit):
    """Rule 04: 5% off at 100+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty > 100:
        disc = base * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_05(qty, unit):
    """Rule 05: 8% off at 20+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 8 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_06(qty, unit):
    """Rule 06: 2% off at 5+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 2 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_07(qty, unit):
    """Rule 07: 15% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 15 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_08(qty, unit):
    """Rule 08: 5% off at 50+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 5 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_09(qty, unit):
    """Rule 09: 3% off at 5+ units."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 3 // 100
        return base - disc
    return base


def price_rule_10(qty, unit):
    """Rule 10: 7% off at 5+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_11(qty, unit):
    """Rule 11: 2% off at 30+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 2 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_12(qty, unit):
    """Rule 12: 15% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 15 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_13(qty, unit):
    """Rule 13: 7% off at 100+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 8 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_14(qty, unit):
    """Rule 14: 8% off at 10+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 8 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_15(qty, unit):
    """Rule 15: 3% off at 5+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 3 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_16(qty, unit):
    """Rule 16: 8% off at 50+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 8 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_17(qty, unit):
    """Rule 17: 3% off at 30+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 3 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_18(qty, unit):
    """Rule 18: 7% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 7 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_19(qty, unit):
    """Rule 19: 2% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 2 // 100
        return base - disc
    return base


def price_rule_20(qty, unit):
    """Rule 20: 3% off at 30+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 3 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_21(qty, unit):
    """Rule 21: 8% off at 5+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 8 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_22(qty, unit):
    """Rule 22: 2% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 2 // 100
        return base - disc
    return base


def price_rule_23(qty, unit):
    """Rule 23: 7% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 7 // 100
        return base - disc
    return base


def price_rule_24(qty, unit):
    """Rule 24: 12% off at 20+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 12 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_25(qty, unit):
    """Rule 25: 3% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 3 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_26(qty, unit):
    """Rule 26: 7% off at 50+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 7 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_27(qty, unit):
    """Rule 27: 3% off at 12+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 3 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_28(qty, unit):
    """Rule 28: 2% off at 12+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 2 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_29(qty, unit):
    """Rule 29: 3% off at 100+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = min(base, 10000) * 3 // 100
        return base - disc
    return base


def price_rule_30(qty, unit):
    """Rule 30: 3% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 3 // 100
        return base - disc
    return base


def price_rule_31(qty, unit):
    """Rule 31: 15% off at 5+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 15 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_32(qty, unit):
    """Rule 32: 7% off at 10+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_33(qty, unit):
    """Rule 33: 7% off at 30+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_34(qty, unit):
    """Rule 34: 12% off at 20+ units."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 12 // 100
        return base - disc
    return base


def price_rule_35(qty, unit):
    """Rule 35: 12% off at 20+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 12 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_36(qty, unit):
    """Rule 36: 8% off at 5+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 8 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_37(qty, unit):
    """Rule 37: 2% off at 12+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = round(base * 2 / 100)
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_38(qty, unit):
    """Rule 38: 12% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 12 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_39(qty, unit):
    """Rule 39: 3% off at 50+ units."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 3 // 100
        return base - disc
    return base


def price_rule_40(qty, unit):
    """Rule 40: 7% off at 10+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


RULES = {i: globals()[f"price_rule_{i:02d}"] for i in range(1, 41)}


def quote(rule_id, qty, unit):
    """Return payable amount for a rule id; unknown ids raise KeyError."""
    return RULES[rule_id](qty, unit)
