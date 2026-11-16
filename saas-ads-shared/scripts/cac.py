#!/usr/bin/env python3
"""Cost Per Paying Customer helper (thresholds T01, T24, T26).

Input CSV columns: channel, spend, new_paying_customers, plus an optional date
column. Headers are case-insensitive, and a semicolon delimiter works. Several
rows per channel are summed. Money may carry thousands commas and a currency
symbol or code ("1,200.50", "EUR 500"). A file that writes decimals with a
comma ("1.200,50") needs --decimal-comma; a semicolon file with such a cell
turns it on by itself. Optional --extra-cost adds non-media cost (agency fee,
tools, contractor time) to a second blended line.
A blank channel is read as unattributed (T26). Any row with zero spend and
paying customers is unattributed too: it prints n/a and the label
unattributed, never 0.00. Zero paying customers print n/a. When unattributed
customers are at least 10% of all paying customers, a T26 line says so.
Small account mode (T24): --window-days N keeps rows dated in the N days that
end on the latest date (or --as-of), and --pool name=a,b (repeatable) sums
channels of the same platform and intent into one line labeled pooled.
The input file is left unchanged.
"""
import argparse
import datetime
import sys

sys.dont_write_bytecode = True
from saas_ads_common import (  # noqa: E402
    UNATTRIBUTED,
    check_pool_members,
    money_mode,
    name_or_unattributed,
    num,
    parse_day,
    parse_pools,
    read_table,
    t26_line,
)

MIN_PAYING = 20  # T01, new paying customers per channel in the window


def money(value):
    return "n/a" if value is None else f"{value:.2f}"


def pct(value):
    return "n/a" if value is None else f"{value:.1%}"


def label(paying, pooled=False):
    if paying == 0:
        return "no_paying_customers"
    if paying < MIN_PAYING:
        return "insufficient_volume"
    return "pooled" if pooled else "ok"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    parser.add_argument("--extra-cost", default="0")
    parser.add_argument("--pool", action="append", default=[], help="name=channel_a,channel_b (T24)")
    parser.add_argument("--window-days", type=int, help="T24 window; needs a date column")
    parser.add_argument("--as-of", help="last date of the window, default the latest date in the file")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    parser.add_argument("--decimal-comma", action="store_true", help="money is written 1.200,50")
    args = parser.parse_args()
    try:
        rows = read_table(args.csv_file, ["channel", "spend", "new_paying_customers"])
        dc = money_mode(rows, args.decimal_comma, ["spend"])
        extra_cost = num(args.extra_cost, dc)
        pools = parse_pools(args.pool)
        check_pool_members(pools, [name_or_unattributed(r["channel"]) for r in rows])
    except (OSError, ValueError) as error:
        print("ERROR: needs_data:", error, file=sys.stderr)
        return 2
    window_line = None
    if args.window_days is not None:
        try:
            if args.window_days < 1:
                raise ValueError("window-days must be 1 or more")
            if "date" not in rows[0]:
                raise ValueError("--window-days needs a date column; headers found: " + ", ".join(rows[0]))
            days = [parse_day(r["date"], args.us_dates) for r in rows]
            end = parse_day(args.as_of, args.us_dates) if args.as_of else max(days)
            start = end - datetime.timedelta(days=args.window_days - 1)
            rows = [r for r, d in zip(rows, days) if start <= d <= end]
            if not rows:
                raise ValueError("no rows dated %s..%s" % (start.isoformat(), end.isoformat()))
            window_line = f"window:\t{start.isoformat()}..{end.isoformat()} ({args.window_days} days)"
        except ValueError as error:
            print("ERROR: needs_data:", error, file=sys.stderr)
            return 2
    totals = {}
    try:
        for row in rows:
            name = name_or_unattributed(row["channel"])
            entry = totals.setdefault(pools.get(name, name), [0.0, 0.0])
            entry[0] += num(row["spend"], dc)
            entry[1] += num(row["new_paying_customers"], dc)
    except ValueError as error:
        print(f"ERROR: needs_data: invalid or missing spend or customer count ({error})", file=sys.stderr)
        return 2
    pool_names = set(pools.values())
    spend_all = sum(v[0] for v in totals.values())
    paying_all = sum(v[1] for v in totals.values())
    if window_line:
        print(window_line)
    print("channel\tspend\tpaying\tcost_per_paying\tshare_of_spend\tshare_of_paying\tT01_label")
    unattributed_paying = 0.0
    for name, (spend, paying) in totals.items():
        share_spend = spend / spend_all if spend_all else None
        share_paying = paying / paying_all if paying_all else None
        if name == UNATTRIBUTED or (spend == 0 and paying > 0):
            cost, tag = None, UNATTRIBUTED
            unattributed_paying += paying
        else:
            cost, tag = (spend / paying if paying else None), label(paying, name in pool_names)
        print(f"{name}\t{spend:.2f}\t{paying:.0f}\t{money(cost)}\t{pct(share_spend)}\t{pct(share_paying)}\t{tag}")
    blended = spend_all / paying_all if paying_all else None
    print(f"blended_media\t{spend_all:.2f}\t{paying_all:.0f}\t{money(blended)}\t100.0%\t100.0%\t{label(paying_all)}")
    if unattributed_paying:
        attributed = paying_all - unattributed_paying
        excl = spend_all / attributed if attributed else None
        print(f"blended_excl_unattributed\t{spend_all:.2f}\t{attributed:.0f}\t{money(excl)}\t-\t-\t{label(attributed)}")
    if extra_cost:
        full = (spend_all + extra_cost) / paying_all if paying_all else None
        print(f"blended_with_extra_cost\t{spend_all + extra_cost:.2f}\t{paying_all:.0f}\t{money(full)}\t-\t-\t{label(paying_all)}")
    for member_pool in sorted(pool_names):
        members = [m for m, p in pools.items() if p == member_pool]
        print(f"pool:\t{member_pool} = {', '.join(members)}. A pooled line cannot be split back out (T24).")
    note = t26_line(unattributed_paying, paying_all)
    if note:
        print(note)
    print("read:\tCost per paying customer uses billing-confirmed customers. Platform conversions are not customers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
