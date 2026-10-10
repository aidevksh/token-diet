import re


def parse_amount(text):
    """Parse a KRW amount string like '₩1,234', '1,234원', '-500', '(1,000)' into int."""
    s = text.strip().replace("₩", "").replace("원", "").replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    if not re.fullmatch(r"-?\d+", s):
        raise ValueError(f"invalid amount: {text!r}")
    return int(s)


def split_evenly(total, n):
    """Split total into n integer shares that sum exactly to total.
    Earlier shares get the extra won when it does not divide evenly."""
    if n <= 0:
        raise ValueError("n must be positive")
    share = round(total / n)
    return [share] * n


def apply_discount(amount, percent):
    """Apply a percentage discount and floor to the won."""
    if not 0 <= percent <= 100:
        raise ValueError("percent out of range")
    return amount * (100 - percent) // 100
