"""Bulk discount rules for the B2B price book.

Every rule takes (qty, unit) in won and returns the payable amount in won.
- "whole" rules: discount = qty * unit * pct // 100 once qty reaches the threshold.
- "marginal" rules: discount = (qty - threshold) * unit * pct // 100, i.e. only units above the threshold.
- Discounts are floored to the won. When a rule has a cap, the discount (not the price) is capped.
"""


def _base(qty, unit):
    if qty < 0 or unit < 0:
        raise ValueError("negative input")
    return qty * unit


def price_rule_01(qty, unit):
    """Rule 01 (marginal): 10% off at 50+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 10 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_02(qty, unit):
    """Rule 02 (whole): 2% off at 20+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 2 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_03(qty, unit):
    """Rule 03 (whole): 2% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 2 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_04(qty, unit):
    """Rule 04 (marginal): 12% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 12 // 100
        return base - disc
    return base


def price_rule_05(qty, unit):
    """Rule 05 (marginal): 3% off at 30+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 3 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_06(qty, unit):
    """Rule 06 (marginal): 3% off at 20+ units."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = (qty - 20) * unit * 3 // 100
        return base - disc
    return base


def price_rule_07(qty, unit):
    """Rule 07 (marginal): 2% off at 5+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 2 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_08(qty, unit):
    """Rule 08 (whole): 2% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 2 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_09(qty, unit):
    """Rule 09 (whole): 3% off at 20+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = min(base, 30000) * 3 // 100
        return base - disc
    return base


def price_rule_10(qty, unit):
    """Rule 10 (marginal): 12% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 13 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_11(qty, unit):
    """Rule 11 (marginal): 5% off at 12+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_12(qty, unit):
    """Rule 12 (marginal): 3% off at 5+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 3 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_13(qty, unit):
    """Rule 13 (marginal): 5% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 5 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_14(qty, unit):
    """Rule 14 (whole): 2% off at 20+ units."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 2 // 100
        return base - disc
    return base


def price_rule_15(qty, unit):
    """Rule 15 (whole): 10% off at 5+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if not qty < 5:
        disc = base * 10 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_16(qty, unit):
    """Rule 16 (whole): 7% off at 100+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_17(qty, unit):
    """Rule 17 (marginal): 12% off at 30+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 12 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_18(qty, unit):
    """Rule 18 (marginal): 3% off at 50+ units."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 3 // 100
        return base - disc
    return base


def price_rule_19(qty, unit):
    """Rule 19 (whole): 10% off at 100+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 10 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_20(qty, unit):
    """Rule 20 (whole): 8% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 8 // 100
        return base - disc
    return base


def price_rule_21(qty, unit):
    """Rule 21 (whole): 10% off at 100+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 10 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_22(qty, unit):
    """Rule 22 (marginal): 8% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if 10 <= qty:
        disc = (qty - 10) * unit * 8 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_23(qty, unit):
    """Rule 23 (marginal): 7% off at 20+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = (qty - 20) * unit * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_24(qty, unit):
    """Rule 24 (marginal): 7% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 7 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_25(qty, unit):
    """Rule 25 (whole): 10% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 10 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_26(qty, unit):
    """Rule 26 (whole): 15% off at 5+ units."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 15 // 100
        return base - disc
    return base


def price_rule_27(qty, unit):
    """Rule 27 (marginal): 10% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 10 // 100
        return base - disc
    return base


def price_rule_28(qty, unit):
    """Rule 28 (marginal): 10% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 10 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_29(qty, unit):
    """Rule 29 (whole): 12% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 13 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_30(qty, unit):
    """Rule 30 (whole): 7% off at 20+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_31(qty, unit):
    """Rule 31 (whole): 3% off at 12+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 3 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_32(qty, unit):
    """Rule 32 (whole): 5% off at 20+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 5 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_33(qty, unit):
    """Rule 33 (marginal): 10% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 10 // 100
        return base - disc
    return base


def price_rule_34(qty, unit):
    """Rule 34 (whole): 2% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 2 // 100
        return base - disc
    return base


def price_rule_35(qty, unit):
    """Rule 35 (whole): 12% off at 30+ units."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 12 // 100
        return base - disc
    return base


def price_rule_36(qty, unit):
    """Rule 36 (whole): 12% off at 100+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 12 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_37(qty, unit):
    """Rule 37 (whole): 8% off at 12+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 8 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_38(qty, unit):
    """Rule 38 (whole): 12% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 12 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_39(qty, unit):
    """Rule 39 (marginal): 8% off at 30+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 9 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_40(qty, unit):
    """Rule 40 (whole): 8% off at 100+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 9 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_41(qty, unit):
    """Rule 41 (marginal): 10% off at 12+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 10 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_42(qty, unit):
    """Rule 42 (whole): 7% off at 5+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 7 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_43(qty, unit):
    """Rule 43 (whole): 7% off at 100+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_44(qty, unit):
    """Rule 44 (whole): 7% off at 30+ units."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 7 // 100
        return base - disc
    return base


def price_rule_45(qty, unit):
    """Rule 45 (marginal): 15% off at 20+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = (qty - 20) * unit * 15 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_46(qty, unit):
    """Rule 46 (marginal): 10% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 10 // 100
        if disc > 30000:
            disc = 30000
        return base - disc
    return base


def price_rule_47(qty, unit):
    """Rule 47 (whole): 7% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 7 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_48(qty, unit):
    """Rule 48 (whole): 8% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 8 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_49(qty, unit):
    """Rule 49 (whole): 8% off at 20+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if not qty < 20:
        disc = base * 8 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_50(qty, unit):
    """Rule 50 (marginal): 5% off at 20+ units."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = (qty - 20) * unit * 5 // 100
        return base - disc
    return base


def price_rule_51(qty, unit):
    """Rule 51 (whole): 12% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = min(base, 30000) * 12 // 100
        return base - disc
    return base


def price_rule_52(qty, unit):
    """Rule 52 (whole): 10% off at 20+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 10 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_53(qty, unit):
    """Rule 53 (whole): 15% off at 50+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 15 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_54(qty, unit):
    """Rule 54 (whole): 15% off at 100+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if 100 <= qty:
        disc = base * 15 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_55(qty, unit):
    """Rule 55 (whole): 2% off at 5+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 2 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_56(qty, unit):
    """Rule 56 (marginal): 10% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 10 // 100
        return base - disc
    return base


def price_rule_57(qty, unit):
    """Rule 57 (whole): 2% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 2 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_58(qty, unit):
    """Rule 58 (whole): 5% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 5 // 100
        return base - disc
    return base


def price_rule_59(qty, unit):
    """Rule 59 (whole): 8% off at 30+ units."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 8 // 100
        return base - disc
    return base


def price_rule_60(qty, unit):
    """Rule 60 (whole): 3% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 3 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_61(qty, unit):
    """Rule 61 (whole): 12% off at 30+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 12 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_62(qty, unit):
    """Rule 62 (whole): 2% off at 50+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 2 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_63(qty, unit):
    """Rule 63 (whole): 8% off at 12+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = min(base, 30000) * 8 // 100
        return base - disc
    return base


def price_rule_64(qty, unit):
    """Rule 64 (whole): 12% off at 20+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 12 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_65(qty, unit):
    """Rule 65 (whole): 5% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 5 // 100
        return base - disc
    return base


def price_rule_66(qty, unit):
    """Rule 66 (whole): 7% off at 20+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_67(qty, unit):
    """Rule 67 (whole): 15% off at 5+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 6:
        disc = base * 15 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_68(qty, unit):
    """Rule 68 (whole): 10% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 10 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_69(qty, unit):
    """Rule 69 (whole): 5% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_70(qty, unit):
    """Rule 70 (whole): 5% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 101:
        disc = base * 5 // 100
        return base - disc
    return base


def price_rule_71(qty, unit):
    """Rule 71 (whole): 10% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 10 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_72(qty, unit):
    """Rule 72 (whole): 7% off at 100+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = base * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_73(qty, unit):
    """Rule 73 (marginal): 2% off at 5+ units."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 2 // 100
        return base - disc
    return base


def price_rule_74(qty, unit):
    """Rule 74 (whole): 15% off at 12+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 15 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_75(qty, unit):
    """Rule 75 (marginal): 8% off at 30+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 8 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_76(qty, unit):
    """Rule 76 (whole): 3% off at 12+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 3 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_77(qty, unit):
    """Rule 77 (whole): 8% off at 5+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 8 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_78(qty, unit):
    """Rule 78 (marginal): 5% off at 50+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 5 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_79(qty, unit):
    """Rule 79 (marginal): 10% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 10 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_80(qty, unit):
    """Rule 80 (whole): 3% off at 50+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 3 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_81(qty, unit):
    """Rule 81 (marginal): 5% off at 30+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_82(qty, unit):
    """Rule 82 (whole): 7% off at 50+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_83(qty, unit):
    """Rule 83 (whole): 2% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 2 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_84(qty, unit):
    """Rule 84 (whole): 3% off at 50+ units."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 3 // 100
        return base - disc
    return base


def price_rule_85(qty, unit):
    """Rule 85 (marginal): 8% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = (qty - 20) * unit * 8 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_86(qty, unit):
    """Rule 86 (whole): 5% off at 10+ units."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 5 // 100
        return base - disc
    return base


def price_rule_87(qty, unit):
    """Rule 87 (marginal): 10% off at 30+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 10 // 100
        if disc > 100000:
            disc = 100000
        return base - disc
    return base


def price_rule_88(qty, unit):
    """Rule 88 (marginal): 12% off at 100+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 12 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_89(qty, unit):
    """Rule 89 (marginal): 8% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 8 // 100
        return base - disc
    return base


def price_rule_90(qty, unit):
    """Rule 90 (whole): 3% off at 12+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 3 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_91(qty, unit):
    """Rule 91 (marginal): 8% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 8 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_92(qty, unit):
    """Rule 92 (marginal): 5% off at 30+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if 30 <= qty:
        disc = (qty - 30) * unit * 5 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_93(qty, unit):
    """Rule 93 (whole): 15% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 15 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_94(qty, unit):
    """Rule 94 (whole): 12% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 12 // 100
        return base - disc
    return base


def price_rule_95(qty, unit):
    """Rule 95 (whole): 10% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 10 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_96(qty, unit):
    """Rule 96 (whole): 5% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 5 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_97(qty, unit):
    """Rule 97 (whole): 5% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 5 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_98(qty, unit):
    """Rule 98 (whole): 5% off at 5+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 5 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_99(qty, unit):
    """Rule 99 (whole): 5% off at 20+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 5 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_100(qty, unit):
    """Rule 100 (marginal): 10% off at 20+ units."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = round((qty - 20) * unit * 10 / 100)
        return base - disc
    return base


def price_rule_101(qty, unit):
    """Rule 101 (whole): 12% off at 10+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 12 // 100
        if disc > 10000:
            disc = 10000
        return base - disc
    return base


def price_rule_102(qty, unit):
    """Rule 102 (whole): 3% off at 50+ units."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 3 // 100
        return base - disc
    return base


def price_rule_103(qty, unit):
    """Rule 103 (marginal): 7% off at 50+ units."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 7 // 100
        return base - disc
    return base


def price_rule_104(qty, unit):
    """Rule 104 (marginal): 3% off at 12+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 3 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_105(qty, unit):
    """Rule 105 (marginal): 10% off at 5+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 10 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_106(qty, unit):
    """Rule 106 (marginal): 10% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 10 // 100
        return base - disc
    return base


def price_rule_107(qty, unit):
    """Rule 107 (whole): 10% off at 30+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 10 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_108(qty, unit):
    """Rule 108 (marginal): 10% off at 10+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 10 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_109(qty, unit):
    """Rule 109 (marginal): 2% off at 50+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 2 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_110(qty, unit):
    """Rule 110 (whole): 8% off at 10+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 8 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_111(qty, unit):
    """Rule 111 (marginal): 3% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 3 // 100
        if disc > 30000:
            disc = 30000
        return base - disc
    return base


def price_rule_112(qty, unit):
    """Rule 112 (marginal): 2% off at 20+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = (qty - 20) * unit * 2 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_113(qty, unit):
    """Rule 113 (whole): 10% off at 50+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 10 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_114(qty, unit):
    """Rule 114 (whole): 10% off at 10+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 10 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_115(qty, unit):
    """Rule 115 (marginal): 10% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 10 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_116(qty, unit):
    """Rule 116 (marginal): 5% off at 30+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_117(qty, unit):
    """Rule 117 (marginal): 10% off at 30+ units."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 10 // 100
        return base - disc
    return base


def price_rule_118(qty, unit):
    """Rule 118 (whole): 15% off at 30+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 15 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_119(qty, unit):
    """Rule 119 (whole): 5% off at 50+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_120(qty, unit):
    """Rule 120 (marginal): 2% off at 5+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 2 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_121(qty, unit):
    """Rule 121 (marginal): 15% off at 100+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 15 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_122(qty, unit):
    """Rule 122 (whole): 5% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 5 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_123(qty, unit):
    """Rule 123 (whole): 5% off at 20+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 5 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_124(qty, unit):
    """Rule 124 (whole): 12% off at 20+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 12 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_125(qty, unit):
    """Rule 125 (marginal): 5% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 5 // 100
        return base - disc
    return base


def price_rule_126(qty, unit):
    """Rule 126 (whole): 7% off at 10+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_127(qty, unit):
    """Rule 127 (whole): 10% off at 12+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if not qty < 12:
        disc = base * 10 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_128(qty, unit):
    """Rule 128 (marginal): 3% off at 50+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 3 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_129(qty, unit):
    """Rule 129 (whole): 5% off at 10+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if 10 <= qty:
        disc = base * 5 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_130(qty, unit):
    """Rule 130 (marginal): 8% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 8 // 100
        return base - disc
    return base


def price_rule_131(qty, unit):
    """Rule 131 (whole): 3% off at 20+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 20:
        disc = base * 3 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_132(qty, unit):
    """Rule 132 (marginal): 8% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 8 // 100
        return base - disc
    return base


def price_rule_133(qty, unit):
    """Rule 133 (marginal): 12% off at 12+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = (qty - 12) * unit * 12 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_134(qty, unit):
    """Rule 134 (marginal): 12% off at 100+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 12 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_135(qty, unit):
    """Rule 135 (whole): 10% off at 12+ units."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 10 // 100
        return base - disc
    return base


def price_rule_136(qty, unit):
    """Rule 136 (whole): 15% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 15 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_137(qty, unit):
    """Rule 137 (marginal): 10% off at 5+ units."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 10 // 100
        return base - disc
    return base


def price_rule_138(qty, unit):
    """Rule 138 (whole): 8% off at 50+ units."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 8 // 100
        return base - disc
    return base


def price_rule_139(qty, unit):
    """Rule 139 (marginal): 15% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = (qty - 10) * unit * 15 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_140(qty, unit):
    """Rule 140 (whole): 7% off at 10+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_141(qty, unit):
    """Rule 141 (whole): 2% off at 12+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 12:
        disc = base * 2 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_142(qty, unit):
    """Rule 142 (whole): 5% off at 5+ units, discount capped at 30,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = base * 5 // 100
        disc = min(disc, 30000)
        return base - disc
    return base


def price_rule_143(qty, unit):
    """Rule 143 (marginal): 8% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = (qty - 50) * unit * 8 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_144(qty, unit):
    """Rule 144 (marginal): 7% off at 30+ units, discount capped at 50,000 won."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = (qty - 30) * unit * 7 // 100
        disc = min(disc, 50000)
        return base - disc
    return base


def price_rule_145(qty, unit):
    """Rule 145 (whole): 10% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = round(base * 10 / 100)
        return base - disc
    return base


def price_rule_146(qty, unit):
    """Rule 146 (whole): 7% off at 30+ units."""
    base = _base(qty, unit)
    if qty >= 30:
        disc = base * 7 // 100
        return base - disc
    return base


def price_rule_147(qty, unit):
    """Rule 147 (whole): 7% off at 50+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 50:
        disc = base * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


def price_rule_148(qty, unit):
    """Rule 148 (marginal): 5% off at 100+ units."""
    base = _base(qty, unit)
    if qty >= 100:
        disc = (qty - 100) * unit * 5 // 100
        return base - disc
    return base


def price_rule_149(qty, unit):
    """Rule 149 (whole): 12% off at 10+ units, discount capped at 100,000 won."""
    base = _base(qty, unit)
    if qty >= 10:
        disc = base * 12 // 100
        disc = min(disc, 100000)
        return base - disc
    return base


def price_rule_150(qty, unit):
    """Rule 150 (marginal): 7% off at 5+ units, discount capped at 10,000 won."""
    base = _base(qty, unit)
    if qty >= 5:
        disc = (qty - 5) * unit * 7 // 100
        disc = min(disc, 10000)
        return base - disc
    return base


RULES = {i: globals()[f"price_rule_{i:02d}"] for i in range(1, 151)}


def quote(rule_id, qty, unit):
    """Return payable amount for a rule id; unknown ids raise KeyError."""
    return RULES[rule_id](qty, unit)
