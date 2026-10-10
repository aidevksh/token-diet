import sys
import csv


def main():
    if len(sys.argv) < 2:
        print("usage: report.py FILE.csv")
        sys.exit(1)
    path = sys.argv[1]
    f = open(path, encoding="utf-8")
    reader = csv.DictReader(f)
    rows = []
    for r in reader:
        rows.append(r)
    f.close()

    # region totals
    region_totals = {}
    region_counts = {}
    for r in rows:
        if r["status"] == "cancelled":
            continue
        try:
            q = int(r["qty"])
        except:
            q = 0
        try:
            p = int(r["unit_price"])
        except:
            p = 0
        amt = q * p
        if r.get("discount") and r["discount"].strip() != "":
            d = int(r["discount"])
            amt = amt - amt * d // 100
        k = r["region"].strip() or "UNKNOWN"
        if k not in region_totals:
            region_totals[k] = 0
            region_counts[k] = 0
        region_totals[k] = region_totals[k] + amt
        region_counts[k] = region_counts[k] + 1

    # product totals
    product_totals = {}
    product_counts = {}
    for r in rows:
        if r["status"] == "cancelled":
            continue
        try:
            q = int(r["qty"])
        except:
            q = 0
        try:
            p = int(r["unit_price"])
        except:
            p = 0
        amt = q * p
        if r.get("discount") and r["discount"].strip() != "":
            d = int(r["discount"])
            amt = amt - amt * d // 100
        k = r["product"].strip() or "UNKNOWN"
        if k not in product_totals:
            product_totals[k] = 0
            product_counts[k] = 0
        product_totals[k] = product_totals[k] + amt
        product_counts[k] = product_counts[k] + 1

    # month totals
    month_totals = {}
    month_counts = {}
    for r in rows:
        if r["status"] == "cancelled":
            continue
        try:
            q = int(r["qty"])
        except:
            q = 0
        try:
            p = int(r["unit_price"])
        except:
            p = 0
        amt = q * p
        if r.get("discount") and r["discount"].strip() != "":
            d = int(r["discount"])
            amt = amt - amt * d // 100
        k = r["date"][:7] if len(r["date"]) >= 7 else "UNKNOWN"
        if k not in month_totals:
            month_totals[k] = 0
            month_counts[k] = 0
        month_totals[k] = month_totals[k] + amt
        month_counts[k] = month_counts[k] + 1

    grand = 0
    for k in region_totals:
        grand = grand + region_totals[k]
    cancelled = 0
    for r in rows:
        if r["status"] == "cancelled":
            cancelled = cancelled + 1

    print("=== SALES REPORT ===")
    print("rows: " + str(len(rows)) + ", cancelled: " + str(cancelled))
    print("grand total: " + "{:,}".format(grand))
    print("")
    print("--- by region ---")
    for k in sorted(region_totals, key=lambda x: (-region_totals[x], x)):
        share = 0.0
        if grand != 0:
            share = region_totals[k] * 100.0 / grand
        print(k.ljust(12) + "{:>14,}".format(region_totals[k]) + "  " + str(region_counts[k]).rjust(4) + "  " + "{:5.1f}%".format(share))
    print("")
    print("--- by product ---")
    for k in sorted(product_totals, key=lambda x: (-product_totals[x], x)):
        share = 0.0
        if grand != 0:
            share = product_totals[k] * 100.0 / grand
        print(k.ljust(12) + "{:>14,}".format(product_totals[k]) + "  " + str(product_counts[k]).rjust(4) + "  " + "{:5.1f}%".format(share))
    print("")
    print("--- by month ---")
    for k in sorted(month_totals):
        share = 0.0
        if grand != 0:
            share = month_totals[k] * 100.0 / grand
        print(k.ljust(12) + "{:>14,}".format(month_totals[k]) + "  " + str(month_counts[k]).rjust(4) + "  " + "{:5.1f}%".format(share))


main()
