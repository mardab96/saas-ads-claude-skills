#!/usr/bin/env python3
"""Ad Platform vs Billing Check helper (threshold T04).

Input CSV columns: source, platform_reported, billing_count. Headers are
case-insensitive, and a semicolon delimiter works.
platform_reported is the conversion count the ad platform shows for the paid
event. billing_count is billing-confirmed new paying customers for the same
source over the same dates, timezone, and attribution window.
The script prints the ratio and a triage label. It cannot match dates or
definitions for you. The input file is left unchanged.
"""
import argparse
import sys

sys.dont_write_bytecode = True
from saas_ads_common import num, read_table  # noqa: E402

HIGH = 1.25  # T04
LOW = 0.75   # T04


def classify(platform, billing):
    if billing == 0:
        return None, "needs_data" if platform else "no_activity"
    ratio = platform / billing
    if ratio > HIGH:
        return ratio, "platform_over"
    if ratio < LOW:
        return ratio, "platform_under"
    return ratio, "within_band"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    args = parser.parse_args()
    try:
        rows = read_table(args.csv_file, ["source", "platform_reported", "billing_count"])
    except (OSError, ValueError) as error:
        print("ERROR: needs_data:", error, file=sys.stderr)
        return 2
    totals = {}
    try:
        for row in rows:
            name = (row["source"] or "").strip()
            if not name:
                raise ValueError("blank source")
            entry = totals.setdefault(name, [0.0, 0.0])
            entry[0] += num(row["platform_reported"])
            entry[1] += num(row["billing_count"])
    except ValueError as error:
        print(f"ERROR: needs_data: invalid or missing source or count ({error})", file=sys.stderr)
        return 2
    print("source\tplatform_reported\tbilling_count\tplatform_to_billing\tT04_label")
    for name, (platform, billing) in totals.items():
        ratio, tag = classify(platform, billing)
        shown = "n/a" if ratio is None else f"{ratio:.2f}"
        print(f"{name}\t{platform:.0f}\t{billing:.0f}\t{shown}\t{tag}")
    platform_all = sum(v[0] for v in totals.values())
    billing_all = sum(v[1] for v in totals.values())
    ratio, tag = classify(platform_all, billing_all)
    shown = "n/a" if ratio is None else f"{ratio:.2f}"
    print(f"all_sources\t{platform_all:.0f}\t{billing_all:.0f}\t{shown}\t{tag}")
    print("read:\tConfirm dates, timezone, event definition, and attribution window match before acting on a label.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
