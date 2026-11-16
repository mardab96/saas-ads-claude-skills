#!/usr/bin/env python3
"""Meta Creative Fatigue Check helper (threshold T07).

Input CSV columns: date, ad, impressions, clicks, frequency (one row per ad per
day; dates may be YYYY-MM-DD or carry a time, and MM/DD/YYYY works with
--us-dates). Headers are case-insensitive, and a semicolon delimiter works.
The latest date in the file ends the recent 7-day window; the
7 days before it form the prior window. An ad needs all 14 days, each window
at least 3,000 impressions, or it is labeled insufficient_window.
Window frequency is the impressions-weighted mean of daily frequency, a
practical approximation because unique reach cannot be summed across days.
The input file is left unchanged.
"""
import argparse
import datetime
import sys

sys.dont_write_bytecode = True
from saas_ads_common import num, parse_day, read_table  # noqa: E402

MIN_IMPRESSIONS = 3000  # T07, per window
FREQ_RISE = 0.25        # T07
CTR_FALL = 0.20         # T07
WINDOW = 7


def summarize(days, ordered):
    impressions = sum(days[d][0] for d in ordered)
    clicks = sum(days[d][1] for d in ordered)
    weighted = sum(days[d][0] * days[d][2] for d in ordered)
    ctr = clicks / impressions if impressions else None
    freq = weighted / impressions if impressions else None
    return impressions, ctr, freq


def pct(value):
    return "n/a" if value is None else f"{value:.2%}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    args = parser.parse_args()
    try:
        rows = read_table(args.csv_file, ["date", "ad", "impressions", "clicks", "frequency"])
    except (OSError, ValueError) as error:
        print("ERROR: needs_data:", error, file=sys.stderr)
        return 2
    ads = {}
    try:
        for row in rows:
            name = (row["ad"] or "").strip()
            if not name:
                raise ValueError("blank ad")
            day = parse_day(row["date"], args.us_dates)
            days = ads.setdefault(name, {})
            if day in days:
                raise ValueError("duplicate ad and date")
            days[day] = (num(row["impressions"]), num(row["clicks"]), num(row["frequency"]))
    except ValueError as error:
        print(f"ERROR: needs_data: invalid row ({error})", file=sys.stderr)
        return 2
    end = max(d for days in ads.values() for d in days)
    recent = [end - datetime.timedelta(days=i) for i in range(WINDOW)]
    prior = [end - datetime.timedelta(days=WINDOW + i) for i in range(WINDOW)]
    print(f"windows:\tprior {min(prior).isoformat()}..{max(prior).isoformat()}\trecent {min(recent).isoformat()}..{max(recent).isoformat()}")
    print("ad\tprior_impr\trecent_impr\tprior_ctr\trecent_ctr\tprior_freq\trecent_freq\tT07_label")
    for name, days in ads.items():
        complete = all(d in days for d in recent) and all(d in days for d in prior)
        if not complete:
            print(f"{name}\t-\t-\t-\t-\t-\t-\tinsufficient_window")
            continue
        p_impr, p_ctr, p_freq = summarize(days, prior)
        r_impr, r_ctr, r_freq = summarize(days, recent)
        row = f"{name}\t{p_impr:.0f}\t{r_impr:.0f}\t{pct(p_ctr)}\t{pct(r_ctr)}\t{p_freq:.2f}\t{r_freq:.2f}\t"
        if p_impr < MIN_IMPRESSIONS or r_impr < MIN_IMPRESSIONS:
            print(row + "insufficient_window")
        elif p_freq and p_ctr and r_freq / p_freq - 1 >= FREQ_RISE and r_ctr / p_ctr - 1 <= -CTR_FALL:
            print(row + "fatigue_candidate")
        else:
            print(row + "no_signal")
    print("read:\tA candidate is a prompt to review the ad, not a verdict. Check audience size, edits, and seasonality first.")
    print("note:\tDaily-row frequency near 1.0 to 1.2 is normal. A 25% rise on that base is small in absolute terms, so confirm it with window-level frequency in Ads Manager.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
