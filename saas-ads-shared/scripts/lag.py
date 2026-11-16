#!/usr/bin/env python3
"""Click-to-paid lag helper (thresholds T15, T25, T01).

Input CSV columns: click_date, paid_date (one row per paying customer; a
customer needs both dates, and paid_date must not be after --as-of). Headers
are case-insensitive, and a semicolon delimiter works. Dates may carry a time;
MM/DD/YYYY needs --us-dates. A spend file that writes decimals with a comma
("1.200,50") needs --decimal-comma; a semicolon file with such a cell turns it
on by itself.
Prints the median and 80th-percentile (nearest rank) click-to-paid days.
--window-days N adds the T15 check: the share of paying customers who paid
later than N days after the click, and a verdict.
The file lists paying customers only, so recent clicks look faster than they
are: customers who will pay later are not in it yet (right-censoring). The
median, the 80th percentile, and the T15 share therefore use only clicks dated
on or before --as-of minus --cohort-cutoff-days (default 90). A censoring line
reports how many customers that leaves.
--spend <csv with columns month, spend> adds the T25 lagged-CAC table: spend in
click month M divided by paying customers whose click date falls in month M.
A month is mature only when its last day plus the 80th-percentile lag is on or
before --as-of; a younger month is immature and prints n/a.
The input files are left unchanged.
"""
import argparse
import calendar
import datetime
import math
import re
import statistics
import sys

sys.dont_write_bytecode = True
from saas_ads_common import money_mode, num, parse_day, read_table  # noqa: E402

MIN_CUSTOMERS = 20  # T01
LATE_SHARE = 0.20   # T15
PERCENTILE = 0.80   # T25


def nearest_rank(values, share):
    ordered = sorted(values)
    return ordered[max(math.ceil(share * len(ordered)) - 1, 0)]


def month_key(day):
    return f"{day.year:04d}-{day.month:02d}"


def month_end(key):
    year, month = int(key[:4]), int(key[5:7])
    return datetime.date(year, month, calendar.monthrange(year, month)[1])


def money(value):
    return "n/a" if value is None else f"{value:.2f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    parser.add_argument("--as-of", required=True, help="export date, YYYY-MM-DD")
    parser.add_argument("--window-days", type=int, help="attribution window to test (T15)")
    parser.add_argument("--spend", help="CSV with columns month, spend (T25)")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    parser.add_argument("--decimal-comma", action="store_true", help="spend is written 1.200,50")
    parser.add_argument("--cohort-cutoff-days", type=int, default=90, help="use only clicks at least this many days old for the lag percentiles and T15")
    args = parser.parse_args()
    if args.window_days is not None and args.window_days < 0:
        print("ERROR: window-days must be zero or more", file=sys.stderr)
        return 2
    try:
        as_of = parse_day(args.as_of, args.us_dates)
        rows = read_table(args.csv_file, ["click_date", "paid_date"])
        customers = []
        for row in rows:
            click = parse_day(row["click_date"], args.us_dates)
            paid_text = (row["paid_date"] or "").strip()
            if not paid_text:
                raise ValueError("blank paid_date: list paying customers only")
            paid = parse_day(paid_text, args.us_dates)
            if paid < click:
                raise ValueError("paid date before click date")
            if paid > as_of:
                raise ValueError("paid date after as-of date")
            customers.append((click, paid))
        spend_by = None
        if args.spend:
            spend_by = {}
            spend_rows = read_table(args.spend, ["month", "spend"])
            dc = money_mode(spend_rows, args.decimal_comma, ["spend"])
            for row in spend_rows:
                text = (row["month"] or "").strip()
                if not re.match(r"^\d{4}-\d{2}", text):
                    raise ValueError("month must be YYYY-MM, got %r" % text)
                spend_by[text[:7]] = spend_by.get(text[:7], 0.0) + num(row["spend"], dc)
    except (OSError, ValueError) as error:
        print(f"ERROR: needs_data: {error}", file=sys.stderr)
        return 2
    cutoff = as_of - datetime.timedelta(days=args.cohort_cutoff_days)
    cohort = [(click, paid) for click, paid in customers if click <= cutoff]
    if not cohort:
        print(f"ERROR: needs_data: no click dated on or before {cutoff.isoformat()} (as-of minus {args.cohort_cutoff_days} days)", file=sys.stderr)
        return 2
    lags = [(paid - click).days for click, paid in cohort]
    p80 = nearest_rank(lags, PERCENTILE)
    print(f"customers:\t{len(customers)}")
    print(f"cohort_customers:\t{len(lags)}")
    print(f"median_click_to_paid_days:\t{statistics.median(lags):.0f}")
    print(f"p80_click_to_paid_days:\t{p80}")
    print(f"censoring:\tlag percentiles and T15 use only clicks dated on or before {cutoff.isoformat()} (as-of minus {args.cohort_cutoff_days} days), {len(lags)} of {len(customers)} customers. Recent clicks have had less time to pay, so counting them would understate the lag.")
    if args.window_days is not None:
        later = sum(1 for lag in lags if lag > args.window_days)
        share = later / len(lags)
        if len(lags) < MIN_CUSTOMERS:
            verdict = "needs_data"
        elif share > LATE_SHARE:
            verdict = "window_too_short"
        else:
            verdict = "window_fits"
        print(f"T15_window_days:\t{args.window_days}")
        print(f"T15_later_than_window:\t{later} of {len(lags)}")
        print(f"T15_share_later:\t{share:.1%}")
        print(f"T15_verdict:\t{verdict}")
    if spend_by is not None:
        counts = {}
        for click, _ in customers:
            counts[month_key(click)] = counts.get(month_key(click), 0) + 1
        months = sorted(set(counts) | set(spend_by))
        print("click_month\tspend\tcustomers\tlagged_cac\tmature_on\tT25_label")
        mature_spend = 0.0
        mature_customers = 0
        for key in months:
            spend = spend_by.get(key)
            got = counts.get(key, 0)
            mature_on = month_end(key) + datetime.timedelta(days=p80)
            if mature_on > as_of:
                tag, cac = "immature", None
            elif spend is None:
                tag, cac = "needs_data", None
            elif got == 0:
                tag, cac = "no_paying_customers", None
            else:
                cac = spend / got
                tag = "ok" if got >= MIN_CUSTOMERS else "insufficient_volume"
                mature_spend += spend
                mature_customers += got
            shown = "n/a" if spend is None else f"{spend:.2f}"
            print(f"{key}\t{shown}\t{got}\t{money(cac)}\t{mature_on.isoformat()}\t{tag}")
        if mature_customers:
            total_tag = "ok" if mature_customers >= MIN_CUSTOMERS else "insufficient_volume"
            print(f"mature_months_total\t{mature_spend:.2f}\t{mature_customers}\t{money(mature_spend / mature_customers)}\t-\t{total_tag}")
        else:
            print("mature_months_total\tn/a\t0\tn/a\t-\tneeds_data")
        print(f"maturity_rule:\tmonth end + {p80} days (80th percentile click-to-paid) <= {as_of.isoformat()}")
    print("read:\tLagged CAC divides spend by customers whose click fell in the same month. A month younger than the lag is not a result yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
