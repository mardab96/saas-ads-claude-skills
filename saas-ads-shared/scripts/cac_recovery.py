#!/usr/bin/env python3
"""Payback Period Check helper (thresholds T05, T21).

Arguments: --cac (cost per paying customer), one of --arpa (average monthly
revenue per account) or --acv (annual contract value, used as acv / 12),
--gross-margin (0 to 1, or a percent such as 80%), and optionally one of
--monthly-churn, --annual-churn (each 0 to 1 or a percent, annual converted to
a monthly rate), or --churn-by-source <csv>.
--churn-by-source reads columns source, monthly_churn (and an optional cac
column that replaces --cac for that source) and prints payback per source. A
blank churn prints needs_churn for that source.
Simple payback = cac / (arpa * gross_margin) months.
With churn, margin arrives only from accounts that are still paying:
cumulative margin after n months = m * (1 - (1 - c)^n) / c, where m is monthly
gross margin per account and c is monthly churn. If cac is at least m / c, the
customer never pays back. Payback always uses gross margin, never revenue.
T21 affordable cost per paying customer is that cumulative margin at n = 12
months (central) and n = 18 months (ceiling).
Without churn the verdict is needs_churn, because churn can only lengthen
simple payback. Money may carry thousands commas and a currency symbol. Add
--decimal-comma when money is written 1.200,50 (a semicolon file with such a
cell turns it on by itself).
The output ends with an excludes line: expansion revenue and the cash timing
of annual prepay are not in this arithmetic.
"""
import argparse
import math
import sys

sys.dont_write_bytecode = True
from saas_ads_common import frac, money_mode, num, read_table  # noqa: E402

REVIEW_MONTHS = 12  # T05, T21 central
HOLD_MONTHS = 18    # T05, T21 ceiling
EXCLUDES = "excludes:\texpansion revenue, annual prepay cash timing"


def positive(value, name):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite number above zero")


def months_to_repay(cac, margin, churn):
    """Return months, or None when the customer never pays back."""
    if not churn:
        return cac / margin
    if cac >= margin / churn:
        return None
    return math.log(1 - cac * churn / margin) / math.log(1 - churn)


def affordable(margin, churn, months):
    if not churn:
        return margin * months
    return margin * (1 - (1 - churn) ** months) / churn


def verdict(months):
    if months is None or months > HOLD_MONTHS:
        return "hold_scale"
    if months > REVIEW_MONTHS:
        return "review"
    return "ok"


def churn_fraction(value, name, decimal_comma=False):
    churn = frac(value, decimal_comma)
    if not 0 <= churn < 1:
        raise ValueError(f"{name} is a fraction from 0 up to, not including, 1")
    return churn


def by_source(path, default_cac, margin, flag):
    rows = read_table(path, ["source", "monthly_churn"])
    dc = money_mode(rows, flag, ["cac", "monthly_churn"])
    print("source\tcac\tmonthly_churn\tsimple_payback_months\tchurn_adjusted_payback_months\tT21_affordable_cost_12m\tT05_verdict")
    for row in rows:
        name = (row["source"] or "").strip()
        if not name:
            raise ValueError("blank source")
        cac_text = (row.get("cac") or "").strip()
        cac = num(cac_text, dc) if cac_text else default_cac
        if cac is None:
            raise ValueError(f"no cac for {name}: pass --cac or add a cac column")
        positive(cac, "cac")
        simple = cac / margin
        churn_text = (row["monthly_churn"] or "").strip()
        if not churn_text:
            print(f"{name}\t{cac:.2f}\tn/a\t{simple:.1f}\tn/a\tn/a\tneeds_churn")
            continue
        churn = churn_fraction(churn_text, "monthly_churn", dc)
        months = months_to_repay(cac, margin, churn)
        shown = "never" if months is None else f"{months:.1f}"
        print(f"{name}\t{cac:.2f}\t{churn:.4f}\t{simple:.1f}\t{shown}\t{affordable(margin, churn, REVIEW_MONTHS):.2f}\t{verdict(months)}")
    print(EXCLUDES)
    print("read:\tPayback per source uses that source's churn and this gross margin. A source with no churn row cannot be judged.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cac")
    rev = parser.add_mutually_exclusive_group(required=True)
    rev.add_argument("--arpa")
    rev.add_argument("--acv")
    parser.add_argument("--gross-margin", required=True)
    churn_group = parser.add_mutually_exclusive_group()
    churn_group.add_argument("--monthly-churn", default=None)
    churn_group.add_argument("--annual-churn", default=None)
    churn_group.add_argument("--churn-by-source", help="CSV with columns source, monthly_churn")
    parser.add_argument("--decimal-comma", action="store_true", help="money is written 1.200,50")
    args = parser.parse_args()
    try:
        dc = args.decimal_comma
        cac = None if args.cac is None else num(args.cac, dc)
        acv = None if args.acv is None else num(args.acv, dc)
        arpa = num(args.arpa, dc) if args.arpa is not None else acv / 12
        gross_margin = frac(args.gross_margin, dc)
        if cac is None and not args.churn_by_source:
            raise ValueError("--cac is required")
        if cac is not None:
            positive(cac, "cac")
        positive(arpa, "arpa or acv")
        positive(gross_margin, "gross-margin")
        if gross_margin > 1:
            raise ValueError("gross-margin is a fraction from 0 to 1")
        churn = None
        if args.monthly_churn is not None:
            churn = churn_fraction(args.monthly_churn, "monthly-churn", dc)
        if args.annual_churn is not None:
            annual = churn_fraction(args.annual_churn, "annual-churn", dc)
            churn = 1 - (1 - annual) ** (1 / 12)
    except ValueError as error:
        print(f"ERROR: needs_data: {error}", file=sys.stderr)
        return 2
    margin = arpa * gross_margin
    if acv is not None:
        print(f"arpa_from_acv:\t{arpa:.2f}")
    print(f"monthly_gross_margin_per_account:\t{margin:.2f}")
    if args.churn_by_source:
        try:
            by_source(args.churn_by_source, cac, margin, dc)
        except (OSError, ValueError) as error:
            print(f"ERROR: needs_data: {error}", file=sys.stderr)
            return 2
        return 0
    if args.annual_churn is not None:
        print(f"monthly_churn_from_annual:\t{churn:.4f}")
    simple = cac / margin
    print(f"simple_payback_months:\t{simple:.1f}")
    if churn is None:
        print("churn_adjusted_payback_months:\tn/a (no churn supplied)")
        print("T05_verdict:\tneeds_churn")
        if simple > HOLD_MONTHS:
            note = f"simple payback is already past the {HOLD_MONTHS} month hold line, and churn can only lengthen it"
        elif simple > REVIEW_MONTHS:
            note = f"simple payback is already past the {REVIEW_MONTHS} month review line, and churn can only lengthen it"
        else:
            note = "simple payback is a lower bound; supply churn for a verdict"
        print(f"T05_note:\t{note}")
        print(EXCLUDES)
        print("read:\tGross-margin payback. Check that CAC comes from billing-confirmed customers.")
        return 0
    months = months_to_repay(cac, margin, churn)
    if churn:
        print(f"lifetime_gross_margin_per_account:\t{margin / churn:.2f}")
    print("churn_adjusted_payback_months:\t" + ("never" if months is None else f"{months:.1f}"))
    print(f"T05_verdict:\t{verdict(months)}")
    print(f"T21_affordable_cost_12m:\t{affordable(margin, churn, REVIEW_MONTHS):.2f}")
    print(f"T21_affordable_cost_18m:\t{affordable(margin, churn, HOLD_MONTHS):.2f}")
    print(EXCLUDES)
    print("read:\tGross-margin payback. Check that CAC comes from billing-confirmed customers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
