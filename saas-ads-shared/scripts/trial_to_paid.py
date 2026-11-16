#!/usr/bin/env python3
"""Trial To Paid By Campaign helper (thresholds T01, T02, T03, T24, T26).

Input CSV columns: campaign, signup_date, paid_date (paid_date blank when the
signup never paid). One row per signup. Headers are case-insensitive, and a
semicolon delimiter works. A blank campaign is read as unattributed (T26): its
line is labeled unattributed and never ranked. When unattributed customers are
at least 10% of all paying customers, a T26 line says so. Dates may be
YYYY-MM-DD or carry a time (YYYY-MM-DD HH:MM[:SS], a T separator, a trailing
Z); MM/DD/YYYY needs --us-dates. Ages are counted in whole days.
A signup is matured when its age on --as-of is at least --trial-days plus
--billing-lag-days (default 7). Immature signups are excluded from both the
numerator and the denominator and reported separately.
Optional --spend <csv with columns campaign, spend> adds a second table with
cost per signup and cost per paying customer per campaign, both on matured
signups. The spend file must cover the same signup dates as the maturity line
the helper prints; the helper cannot check spend dates. An unattributed line
needs no spend row and prints n/a for its cost. A spend file that writes
decimals with a comma ("1.200,50") needs --decimal-comma; a semicolon file
with such a cell turns it on by itself.
Small account mode (T24): --pool name=a,b (repeatable) merges campaigns of the
same platform and intent into one line labeled pooled, and --window-days N
keeps only signups in the N days that end on the last matured date.
The input files are left unchanged.
"""
import argparse
import datetime
import statistics
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

MIN_MATURED = 30   # T02, matured signups per campaign
WEAK_RATIO = 0.5   # T03, campaign rate at most half of the account rate
MIN_PAYING = 20    # T01, new paying customers per campaign for cost per paying customer


def rate_text(value):
    return "n/a" if value is None else f"{value:.1%}"


def money(value):
    return "n/a" if value is None else f"{value:.2f}"


def paying_label(name, paid, pooled=False):
    if name == UNATTRIBUTED:
        return UNATTRIBUTED
    if paid == 0:
        return "no_paying_customers"
    if paid < MIN_PAYING:
        return "insufficient_volume"
    return "pooled" if pooled else "ok"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    parser.add_argument("--trial-days", type=int, required=True)
    parser.add_argument("--as-of", required=True, help="export date, YYYY-MM-DD")
    parser.add_argument("--billing-lag-days", type=int, default=7)
    parser.add_argument("--spend", help="CSV with columns campaign, spend")
    parser.add_argument("--pool", action="append", default=[], help="name=campaign_a,campaign_b (T24)")
    parser.add_argument("--window-days", type=int, help="T24 window of signup dates ending on the last matured date")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    parser.add_argument("--decimal-comma", action="store_true", help="spend is written 1.200,50")
    args = parser.parse_args()
    if args.trial_days < 0 or args.billing_lag_days < 0:
        print("ERROR: trial and lag days must be zero or more", file=sys.stderr)
        return 2
    if args.window_days is not None and args.window_days < 1:
        print("ERROR: window-days must be 1 or more", file=sys.stderr)
        return 2
    try:
        as_of = parse_day(args.as_of, args.us_dates)
        rows = read_table(args.csv_file, ["campaign", "signup_date", "paid_date"])
        pools = parse_pools(args.pool)
        check_pool_members(pools, [name_or_unattributed(r["campaign"]) for r in rows])
    except (OSError, ValueError) as error:
        print("ERROR: needs_data:", error, file=sys.stderr)
        return 2
    cutoff = args.trial_days + args.billing_lag_days
    line = as_of - datetime.timedelta(days=cutoff)
    start = line - datetime.timedelta(days=args.window_days - 1) if args.window_days else None
    stats = {}
    try:
        for row in rows:
            raw_name = name_or_unattributed(row["campaign"])
            name = pools.get(raw_name, raw_name)
            signup = parse_day(row["signup_date"], args.us_dates)
            paid_text = (row["paid_date"] or "").strip()
            paid = parse_day(paid_text, args.us_dates) if paid_text else None
            if signup > as_of:
                raise ValueError("signup after as-of date")
            if paid and (paid < signup or paid > as_of):
                raise ValueError("paid date outside signup..as-of")
            if start is not None and not (start <= signup <= line):
                continue
            entry = stats.setdefault(name, {"signups": 0, "matured": 0, "paid": 0, "days": []})
            entry["signups"] += 1
            if (as_of - signup).days >= cutoff:
                entry["matured"] += 1
                if paid:
                    entry["paid"] += 1
                    entry["days"].append((paid - signup).days)
    except ValueError as error:
        print(f"ERROR: needs_data: invalid row ({error})", file=sys.stderr)
        return 2
    if not stats:
        print(f"ERROR: needs_data: no signups dated {start.isoformat()}..{line.isoformat()}", file=sys.stderr)
        return 2
    spend_by = None
    if args.spend:
        try:
            spend_rows = read_table(args.spend, ["campaign", "spend"])
            dc = money_mode(spend_rows, args.decimal_comma, ["spend"])
            spend_by = {}
            for row in spend_rows:
                raw_name = name_or_unattributed(row["campaign"])
                name = pools.get(raw_name, raw_name)
                spend_by[name] = spend_by.get(name, 0.0) + num(row["spend"], dc)
            missing = [name for name in stats if name not in spend_by and name != UNATTRIBUTED]
            if missing:
                raise ValueError("no spend row for campaign: " + ", ".join(missing))
        except (OSError, ValueError) as error:
            print(f"ERROR: needs_data: spend file ({error})", file=sys.stderr)
            return 2
    pool_names = set(pools.values())
    matured_all = sum(v["matured"] for v in stats.values())
    paid_all = sum(v["paid"] for v in stats.values())
    account_rate = paid_all / matured_all if matured_all else None
    print("campaign\tsignups\tmatured\timmature\tpaid\tpaid_rate\tmedian_days_to_paid\tlabel")
    for name, v in stats.items():
        rate = v["paid"] / v["matured"] if v["matured"] else None
        median = f"{statistics.median(v['days']):.0f}" if v["days"] else "n/a"
        if name == UNATTRIBUTED:
            tag = UNATTRIBUTED
        elif v["matured"] < MIN_MATURED:
            tag = "insufficient_volume"
        elif account_rate and rate <= WEAK_RATIO * account_rate:
            tag = "weak_paid_rate"
        else:
            tag = "pooled" if name in pool_names else "ok"
        print(f"{name}\t{v['signups']}\t{v['matured']}\t{v['signups'] - v['matured']}\t{v['paid']}\t{rate_text(rate)}\t{median}\t{tag}")
    total_signups = sum(v["signups"] for v in stats.values())
    all_days = [d for v in stats.values() for d in v["days"]]
    median_all = f"{statistics.median(all_days):.0f}" if all_days else "n/a"
    print(f"account\t{total_signups}\t{matured_all}\t{total_signups - matured_all}\t{paid_all}\t{rate_text(account_rate)}\t{median_all}\t-")
    print(f"maturity_rule:\tage >= {args.trial_days} trial days + {args.billing_lag_days} billing lag days as of {as_of.isoformat()}")
    if start is not None:
        print(f"window_rule:\tsignups dated {start.isoformat()}..{line.isoformat()} ({args.window_days} days, ending on the last matured date)")
    for pool in sorted(pool_names):
        members = [m for m, p in pools.items() if p == pool]
        print(f"pool:\t{pool} = {', '.join(members)}. A pooled line cannot be split back out (T24).")
    if spend_by is not None:
        names = list(stats) + [n for n in spend_by if n not in stats]
        print("campaign\tspend\tmatured\tpaid\tcost_per_signup\tcost_per_paying\tT01_label")
        spend_total = 0.0
        for name in names:
            v = stats.get(name, {"matured": 0, "paid": 0})
            spend = spend_by.get(name, 0.0)
            spend_total += spend
            if name == UNATTRIBUTED:
                per_signup = per_paying = None
            else:
                per_signup = spend / v["matured"] if v["matured"] else None
                per_paying = spend / v["paid"] if v["paid"] else None
            print(f"{name}\t{spend:.2f}\t{v['matured']}\t{v['paid']}\t{money(per_signup)}\t{money(per_paying)}\t{paying_label(name, v['paid'], name in pool_names)}")
        matured_cost = sum((stats.get(n) or {"matured": 0})["matured"] for n in names)
        paid_cost = sum((stats.get(n) or {"paid": 0})["paid"] for n in names)
        per_signup_all = spend_total / matured_cost if matured_cost else None
        per_paying_all = spend_total / paid_cost if paid_cost else None
        print(f"account\t{spend_total:.2f}\t{matured_cost}\t{paid_cost}\t{money(per_signup_all)}\t{money(per_paying_all)}\t{paying_label('account', paid_cost)}")
        covers = f"from {start.isoformat()} up to {line.isoformat()}" if start is not None else f"up to {line.isoformat()}"
        print(f"spend_rule:\tspend must cover only signup dates {covers}, the same signups counted as matured. Spend dates cannot be checked by this helper.")
    note = t26_line((stats.get(UNATTRIBUTED) or {"paid": 0})["paid"], paid_all)
    if note:
        print(note)
    print("read:\tPaid rate counts only matured signups. Immature signups are not failures yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
