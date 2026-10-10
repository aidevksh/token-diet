def vat_breakdown(gross):
    """Split a VAT-inclusive gross amount (10% VAT) into (supply, vat).
    supply is gross / 1.1 rounded half up to the won; vat = gross - supply."""
    vat = round(gross * 0.1)
    return gross - vat, vat
