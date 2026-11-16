#!/usr/bin/env python3
"""Lead to won deal helper for demo-led accounts (thresholds T28, T01).

Input CSV columns: campaign, lead_date, meeting_date, won_date, and an optional
acv column. meeting_date is blank when no meeting happened, won_date is blank
when the lead is not won, and a won lead needs a meeting date. Headers are
case-insensitive, and a semicolon delimiter works. Dates may carry a time;
MM/DD/YYYY needs --us-dates. Money (acv, spend) that writes decimals with a
comma ("1.200,50") needs --decimal-comma; a semicolon file with such a cell
turns it on by itself.
A lead is matured when its age on --as-of is at least the sales cycle. The
sales cycle is --sales-cycle-days when given, otherwise the 80th percentile
(nearest rank) of lead-to-won days, which needs at least 10 won leads.
Show rate = meetings / matured leads. Close rate = won / meetings, on matured
leads only. Optional --spend <csv with columns campaign, spend> adds cost per
meeting and cost per won deal on matured leads.
The rate table carries only the T28_label (30 matured leads per campaign); the
cost table carries only the T01_label (20 won deals per campaign). Each
campaign gets one label per question, never a mixed status.
The input files are left unchanged.
"""
import argparse
import datetime
import math
import statistics
import sys

sys.dont_write_bytecode = True
from saas_ads_common import money_mode, num, parse_day, read_table  # noqa: E402

MIN_MATURED = 30      # T28, matured leads per campaign
MIN_WON_FOR_CYCLE = 10  # T28, won leads to derive the sales cycle
MIN_WON = 20          # T01, won deals per campaign for a cost per won deal


def nearest_rank(values, share):
    ordered = sorted(values)
    return ordered[max(math.ceil(share * len(ordered)) - 1, 0)]


def pct(value):
    return "n/a" if value is None else f"{value:.1%}"


def money(value):
    return "n/a" if value is None else f"{value:.2f}"


def won_label(won):
    if won == 0:
        return "no_won_deals"
    return "insufficient_volume" if won < MIN_WON else "ok"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_file")
    parser.add_argument("--as-of", required=True, help="export date, YYYY-MM-DD")
    parser.add_argument("--sales-cycle-days", type=int)
    parser.add_argument("--spend", help="CSV with columns campaign, spend")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    parser.add_argument("--decimal-comma", action="store_true", help="money is written 1.200,50")
    args = parser.parse_args()
    if args.sales_cycle_days is not None and args.sales_cycle_days < 0:
        print("ERROR: sales-cycle-days must be zero or more", file=sys.stderr)
        return 2
    try:
        as_of = parse_day(args.as_of, args.us_dates)
        rows = read_table(args.csv_file, ["campaign", "lead_date", "meeting_date", "won_date"])
        leads = []
        acv_dc = money_mode(rows, args.decimal_comma, ["acv"])
        for row in rows:
            name = (row["campaign"] or "").strip()
            if not name:
                raise ValueError("blank campaign")
            lead = parse_day(row["lead_date"], args.us_dates)
            meeting_text = (row["meeting_date"] or "").strip()
            won_text = (row["won_date"] or "").strip()
            meeting = parse_day(meeting_text, args.us_dates) if meeting_text else None
            won = parse_day(won_text, args.us_dates) if won_text else None
            if won and not meeting:
                raise ValueError("won lead without a meeting date")
            if lead > as_of or (meeting and (meeting < lead or meeting > as_of)):
                raise ValueError("meeting date outside lead..as-of")
            if won and (won < meeting or won > as_of):
                raise ValueError("won date outside meeting..as-of")
            acv_text = (row.get("acv") or "").strip()
            acv = num(acv_text, acv_dc) if acv_text else None
            leads.append((name, lead, meeting, won, acv))
        if args.sales_cycle_days is not None:
            cycle, source = args.sales_cycle_days, "stated"
        else:
            days = [(won - lead).days for _, lead, _, won, _ in leads if won]
            if len(days) < MIN_WON_FOR_CYCLE:
                raise ValueError(f"fewer than {MIN_WON_FOR_CYCLE} won leads, so the sales cycle cannot be derived; pass --sales-cycle-days")
            cycle, source = nearest_rank(days, 0.80), f"80th percentile of {len(days)} won leads"
        spend_by = None
        if args.spend:
            spend_by = {}
            spend_rows = read_table(args.spend, ["campaign", "spend"])
            dc = money_mode(spend_rows, args.decimal_comma, ["spend"])
            for row in spend_rows:
                name = (row["campaign"] or "").strip()
                if not name:
                    raise ValueError("blank campaign in spend file")
                spend_by[name] = spend_by.get(name, 0.0) + num(row["spend"], dc)
            missing = sorted({lead[0] for lead in leads} - set(spend_by))
            if missing:
                raise ValueError("no spend row for campaign: " + ", ".join(missing))
    except (OSError, ValueError) as error:
        print(f"ERROR: needs_data: {error}", file=sys.stderr)
        return 2
    stats = {}
    for name, lead, meeting, won, acv in leads:
        entry = stats.setdefault(name, {"leads": 0, "matured": 0, "meetings": 0, "won": 0, "days": [], "acv": 0.0, "acv_rows": 0})
        entry["leads"] += 1
        if (as_of - lead).days >= cycle:
            entry["matured"] += 1
            if meeting:
                entry["meetings"] += 1
            if won:
                entry["won"] += 1
                entry["days"].append((won - lead).days)
                if acv is not None:
                    entry["acv"] += acv
                    entry["acv_rows"] += 1
    print(f"sales_cycle_days:\t{cycle} ({source})")
    print("campaign\tleads\tmatured\timmature\tmeetings\tshow_rate\twon\tclose_rate\tmedian_days_lead_to_won\tacv_won\tT28_label")
    totals = {"leads": 0, "matured": 0, "meetings": 0, "won": 0, "days": [], "acv": 0.0, "acv_rows": 0}

    def show(name, v, tag):
        show_rate = v["meetings"] / v["matured"] if v["matured"] else None
        close_rate = v["won"] / v["meetings"] if v["meetings"] else None
        median = f"{statistics.median(v['days']):.0f}" if v["days"] else "n/a"
        acv_text = f"{v['acv']:.2f}" if v["acv_rows"] else "n/a"
        print(f"{name}\t{v['leads']}\t{v['matured']}\t{v['leads'] - v['matured']}\t{v['meetings']}\t{pct(show_rate)}\t{v['won']}\t{pct(close_rate)}\t{median}\t{acv_text}\t{tag}")

    for name, v in stats.items():
        show(name, v, "insufficient_volume" if v["matured"] < MIN_MATURED else "ok")
        for key in ("leads", "matured", "meetings", "won", "acv_rows"):
            totals[key] += v[key]
        totals["days"] += v["days"]
        totals["acv"] += v["acv"]
    show("account", totals, "-")
    line = as_of - datetime.timedelta(days=cycle)
    print(f"maturity_rule:\tlead age >= {cycle} sales cycle days as of {as_of.isoformat()}")
    if spend_by is not None:
        print("campaign\tspend\tmatured\tmeetings\twon\tcost_per_meeting\tcost_per_won\tT01_label")
        spend_total = 0.0
        for name, v in stats.items():
            spend = spend_by[name]
            spend_total += spend
            per_meeting = spend / v["meetings"] if v["meetings"] else None
            per_won = spend / v["won"] if v["won"] else None
            print(f"{name}\t{spend:.2f}\t{v['matured']}\t{v['meetings']}\t{v['won']}\t{money(per_meeting)}\t{money(per_won)}\t{won_label(v['won'])}")
        per_meeting = spend_total / totals["meetings"] if totals["meetings"] else None
        per_won = spend_total / totals["won"] if totals["won"] else None
        print(f"account\t{spend_total:.2f}\t{totals['matured']}\t{totals['meetings']}\t{totals['won']}\t{money(per_meeting)}\t{money(per_won)}\t{won_label(totals['won'])}")
        print(f"spend_rule:\tspend must cover only lead dates up to {line.isoformat()}, the same leads counted as matured. Spend dates cannot be checked by this helper.")
    print("read:\tRates count only matured leads. A lead younger than the sales cycle is not a loss yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
