#!/usr/bin/env python3
"""Brand vs Non-Brand Split helper (thresholds T01, T09).

Input CSV columns: segment, spend, paying_customers. segment is exactly
`brand` or `non_brand` (your own labeling of campaigns or search terms).
Headers are case-insensitive, and a semicolon delimiter works. A file that
writes decimals with a comma ("1.200,50") needs --decimal-comma; a semicolon
file with such a cell turns it on by itself.
Several rows per segment are summed. The script prints cost per paying customer
per segment and the blend, then labels the blend when brand holds at least
the T09 share of paying customers. The input file is left unchanged.
"""
import argparse
import sys

sys.dont_write_bytecode = True
from saas_ads_common import money_mode, num, read_table  # noqa: E402

BRAND_SHARE = 0.40  # T09
MIN_PAYING = 20     # T01


def cost_text(spend, paying):
    return f"{spend / paying:.2f}" if paying else "n/a"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    parser.add_argument("--decimal-comma", action="store_true", help="money is written 1.200,50")
    args = parser.parse_args()
    try:
        rows = read_table(args.csv_file, ["segment", "spend", "paying_customers"])
    except (OSError, ValueError) as error:
        print("ERROR: needs_data:", error, file=sys.stderr)
        return 2
    dc = money_mode(rows, args.decimal_comma, ["spend"])
    totals = {"brand": [0.0, 0.0], "non_brand": [0.0, 0.0]}
    try:
        for row in rows:
            segment = (row["segment"] or "").strip().lower()
            if segment not in totals:
                raise ValueError("segment must be brand or non_brand")
            totals[segment][0] += num(row["spend"], dc)
            totals[segment][1] += num(row["paying_customers"], dc)
    except ValueError as error:
        print(f"ERROR: needs_data: invalid segment, spend, or customer count ({error})", file=sys.stderr)
        return 2
    seen = {(r["segment"] or "").strip().lower() for r in rows}
    if seen != {"brand", "non_brand"}:
        print("ERROR: needs_data: both brand and non_brand rows are required", file=sys.stderr)
        return 2
    spend_all = sum(v[0] for v in totals.values())
    paying_all = sum(v[1] for v in totals.values())
    print("segment\tspend\tpaying\tcost_per_paying\tshare_of_spend\tshare_of_paying\tvolume")
    for name, (spend, paying) in totals.items():
        share_spend = f"{spend / spend_all:.1%}" if spend_all else "n/a"
        share_paying = f"{paying / paying_all:.1%}" if paying_all else "n/a"
        volume = "ok" if paying >= MIN_PAYING else "insufficient_volume"
        print(f"{name}\t{spend:.2f}\t{paying:.0f}\t{cost_text(spend, paying)}\t{share_spend}\t{share_paying}\t{volume}")
    print(f"blended\t{spend_all:.2f}\t{paying_all:.0f}\t{cost_text(spend_all, paying_all)}\t100.0%\t100.0%\t-")
    brand_paying = totals["brand"][1]
    if paying_all == 0:
        verdict = "needs_data"
    elif brand_paying / paying_all >= BRAND_SHARE:
        verdict = "report_split"
    else:
        verdict = "blend_acceptable"
    print(f"T09_verdict:\t{verdict}")
    print("read:\tBrand demand already exists. Judge new-demand campaigns on the non_brand line.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
