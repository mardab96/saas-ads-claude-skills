#!/usr/bin/env python3
"""Next-dollar cost helper (thresholds T27, T21, T18, T02, T01).

Compare mode. Input CSV columns: channel, period, spend, new_paying_customers.
period is before or after a budget change. Several rows per channel and period
are summed. new_paying_customers counts customers by SIGNUP date: customers who
signed up in that period and have paid, not payments made in it. Headers are
case-insensitive, and a semicolon delimiter works. A file that writes decimals
with a comma needs --decimal-comma; a semicolon file with such a cell turns it
on by itself.
--days-before and --days-after give the length of each period; both must be
equal and at least 14 days. --after-end is the last day of the after period and
--as-of is the export date.
Maturity rule (T02): every signup in both periods must be matured. The lag is
--lag-days, or --trial-days plus --billing-lag-days (default 7) when it is not
given. If --as-of is earlier than --after-end plus the lag, the helper stops
and prints the date the after period matures.
--affordable is the T21 affordable cost per paying customer (the 12-month
figure that cac_recovery.py prints).
Incremental CAC = (spend after - spend before) / (paying after - paying before).
A channel is read only when spend rose at least 10% (T27; a T18 step is at most
20%, so one T18-compliant step can be read) and the after period has
at least 20 paying customers (T01). Otherwise the verdict is needs_data.
Extra spend that bought no extra customers prints n/a and over_affordable.
Before and after ignores seasonality, offer changes, and tracking changes, and
it is not incrementality.

Design mode (--design). When no clean budget change exists, print a plan for
one channel: one step of 20% (T18) on --start, the days needed to reach 20
paying customers after the step (never under 14), the minimum spend, the extra
customers needed to stay affordable, and the date to rerun this helper. Inputs:
--daily-spend, --current-cac, --start, --affordable, and the lag arguments.
The input file is left unchanged.
"""
import argparse
import datetime
import math
import sys

sys.dont_write_bytecode = True
from saas_ads_common import money_mode, num, parse_day, read_table  # noqa: E402

MIN_DAYS = 14        # T27, days per period
MIN_RISE = 0.10      # T27, relative spend change; below the T18 step cap
STEP = 0.20          # T18, largest budget step; the design plan uses it so the rise clears MIN_RISE
MIN_PAYING = 20      # T01, after period
MIN_GAP_DAYS = 7     # T18, days between steps
READ = (
    "read:\tIncremental CAC is the cost of the extra customers only. It compares two periods, so it ignores "
    "seasonality, offer, and tracking changes, and it is not incrementality. A retargeting or brand channel can "
    "look cheap without adding customers."
)


def judge(before, after, affordable):
    """Return (spend_change, incremental_cac, verdict) for ([spend, paying], [spend, paying])."""
    if before is None or after is None or before[0] <= 0:
        return None, None, "needs_data"
    change = (after[0] - before[0]) / before[0]
    if change < MIN_RISE - 1e-9 or after[1] < MIN_PAYING:
        return change, None, "needs_data"
    added = after[1] - before[1]
    if added <= 0:
        return change, None, "over_affordable"
    incremental = (after[0] - before[0]) / added
    return change, incremental, "within_affordable" if incremental <= affordable else "over_affordable"


def lag_rule(args):
    """Return (lag days, text) from --lag-days, or --trial-days plus --billing-lag-days."""
    if args.lag_days is not None:
        if args.lag_days < 0:
            raise ValueError("--lag-days must be zero or more")
        return args.lag_days, f"{args.lag_days} lag days"
    if args.trial_days is None:
        raise ValueError("give --trial-days (or --lag-days): customers are counted by signup date and must be matured (T02)")
    if args.trial_days < 0 or args.billing_lag_days < 0:
        raise ValueError("trial and billing lag days must be zero or more")
    total = args.trial_days + args.billing_lag_days
    return total, f"{total} lag days = {args.trial_days} trial days + {args.billing_lag_days} billing lag days"


def design(args, affordable, lag, lag_text, dc):
    if args.daily_spend is None or args.current_cac is None or not args.start:
        raise ValueError("--design needs --daily-spend, --current-cac, and --start")
    daily = num(args.daily_spend, dc)
    cac = num(args.current_cac, dc)
    if daily <= 0 or cac <= 0:
        raise ValueError("--daily-spend and --current-cac must be above zero")
    start = parse_day(args.start, args.us_dates)
    new_daily = daily * (1 + STEP)
    per_day = new_daily / cac
    days = max(MIN_DAYS, math.ceil(MIN_PAYING / per_day))
    after_end = start + datetime.timedelta(days=days - 1)
    before_end = start - datetime.timedelta(days=1)
    before_start = start - datetime.timedelta(days=days)
    extra = (new_daily - daily) * days
    check = after_end + datetime.timedelta(days=lag)
    print(f"design:\tone channel, one budget step of {STEP:.0%} (T18), read with T27")
    print(f"step:\traise daily spend from {daily:.2f} to {new_daily:.2f} on {start.isoformat()}")
    print(f"period_days:\t{days} before and {days} after")
    print(f"before_period:\t{before_start.isoformat()}..{before_end.isoformat()}")
    print(f"after_period:\t{start.isoformat()}..{after_end.isoformat()}")
    print(f"minimum_spend_after:\t{new_daily * days:.2f}")
    print(f"paying_customers_to_read:\t{MIN_PAYING} or more in the after period (T01); about {per_day * days:.0f} expected at the current cost")
    print(f"extra_spend:\t{extra:.2f}")
    print(f"extra_customers_needed:\t{extra / affordable:.1f} or more over the before period, or the extra spend reads as over_affordable")
    print(f"check_date:\t{check.isoformat()} ({lag_text} after the last signup in the after period)")
    print(f"hold_still:\tmake no other budget change on this channel from {before_start.isoformat()} to {after_end.isoformat()}, and leave at least {MIN_GAP_DAYS} days before any next step (T18)")
    if cac > affordable:
        print("T27_note:\tthe current average cost is already above the affordable cost, so a step up will rarely pass. Consider cut or hold first.")
    print("read:\tThis plan reads one before and after step. It ignores seasonality and is not incrementality; a holdout or geo split is the proof.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file", nargs="?")
    parser.add_argument("--days-before", type=int)
    parser.add_argument("--days-after", type=int)
    parser.add_argument("--affordable", required=True)
    parser.add_argument("--after-end", help="last day of the after period, YYYY-MM-DD")
    parser.add_argument("--as-of", help="export date, YYYY-MM-DD")
    parser.add_argument("--trial-days", type=int)
    parser.add_argument("--billing-lag-days", type=int, default=7)
    parser.add_argument("--lag-days", type=int, help="signup maturity lag; default trial days plus billing lag days")
    parser.add_argument("--design", action="store_true", help="print a measurement step plan instead of reading a file")
    parser.add_argument("--daily-spend", help="design: current daily spend on the channel")
    parser.add_argument("--current-cac", help="design: current cost per paying customer on the channel")
    parser.add_argument("--start", help="design: date of the budget step, YYYY-MM-DD")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    parser.add_argument("--decimal-comma", action="store_true", help="money is written 1.200,50")
    args = parser.parse_args()
    try:
        affordable = num(args.affordable, args.decimal_comma)
        if affordable <= 0:
            raise ValueError("--affordable must be above zero")
        lag, lag_text = lag_rule(args)
        if args.design:
            design(args, affordable, lag, lag_text, args.decimal_comma)
            return 0
        if not args.csv_file or args.days_before is None or args.days_after is None or not args.after_end or not args.as_of:
            raise ValueError("compare mode needs the CSV file, --days-before, --days-after, --after-end, and --as-of")
        if args.days_before != args.days_after or args.days_before < MIN_DAYS:
            raise ValueError(f"periods must be equal in length and at least {MIN_DAYS} days (T27)")
        after_end = parse_day(args.after_end, args.us_dates)
        as_of = parse_day(args.as_of, args.us_dates)
        mature_on = after_end + datetime.timedelta(days=lag)
        if as_of < mature_on:
            raise ValueError(
                f"the after period ended {after_end.isoformat()}, so its signups mature on {mature_on.isoformat()} ({lag_text}). "
                "Rerun on or after that date"
            )
        rows = read_table(args.csv_file, ["channel", "period", "spend", "new_paying_customers"])
        dc = money_mode(rows, args.decimal_comma, ["spend"])
        data = {}
        for row in rows:
            name = (row["channel"] or "").strip()
            period = (row["period"] or "").strip().lower()
            if not name:
                raise ValueError("blank channel")
            if period not in ("before", "after"):
                raise ValueError("period must be before or after, got %r" % period)
            entry = data.setdefault(name, {"before": None, "after": None})
            current = entry[period] or [0.0, 0.0]
            entry[period] = [current[0] + num(row["spend"], dc), current[1] + num(row["new_paying_customers"], dc)]
    except (OSError, ValueError) as error:
        print(f"ERROR: needs_data: {error}", file=sys.stderr)
        return 2
    days = args.days_after
    after_start = after_end - datetime.timedelta(days=days - 1)
    before_end = after_start - datetime.timedelta(days=1)
    before_start = before_end - datetime.timedelta(days=days - 1)
    print(f"periods:\tbefore {before_start.isoformat()}..{before_end.isoformat()} ({days} days), after {after_start.isoformat()}..{after_end.isoformat()} ({days} days)")
    print(f"maturity_rule:\tcustomers are counted by signup date and every signup in both periods is matured (T02): {as_of.isoformat()} is on or after {mature_on.isoformat()} ({lag_text})")
    print(f"T21_affordable_cost:\t{affordable:.2f}")
    print("channel\tspend_before\tspend_after\tpaying_before\tpaying_after\tspend_change\tincremental_cac\tT27_verdict")
    total_before, total_after = [0.0, 0.0], [0.0, 0.0]
    complete = True
    for name, entry in data.items():
        before, after = entry["before"], entry["after"]
        change, incremental, verdict = judge(before, after, affordable)
        b = before or [0.0, 0.0]
        a = after or [0.0, 0.0]
        if before is None or after is None:
            complete = False
        total_before = [total_before[0] + b[0], total_before[1] + b[1]]
        total_after = [total_after[0] + a[0], total_after[1] + a[1]]
        shown_change = "n/a" if change is None else f"{change:.1%}"
        shown_inc = "n/a" if incremental is None else f"{incremental:.2f}"
        print(f"{name}\t{b[0]:.2f}\t{a[0]:.2f}\t{b[1]:.0f}\t{a[1]:.0f}\t{shown_change}\t{shown_inc}\t{verdict}")
    if complete:
        change, incremental, verdict = judge(total_before, total_after, affordable)
    else:
        change, incremental, verdict = None, None, "needs_data"
    shown_change = "n/a" if change is None else f"{change:.1%}"
    shown_inc = "n/a" if incremental is None else f"{incremental:.2f}"
    print(f"account\t{total_before[0]:.2f}\t{total_after[0]:.2f}\t{total_before[1]:.0f}\t{total_after[1]:.0f}\t{shown_change}\t{shown_inc}\t{verdict}")
    print(READ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
