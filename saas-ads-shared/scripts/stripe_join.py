#!/usr/bin/env python3
"""Stripe export join helper (feeds trial_to_paid.py).

Arguments: the Stripe Customers CSV, the Stripe Payments or Invoices CSV, and
--campaign-field, the header of the Customers column that holds the campaign
(a metadata key). Headers are matched case-insensitively with spaces read as
underscores, and a semicolon delimiter works.
Output columns: campaign, signup_date, paid_date. campaign is the value of the
campaign field, or unattributed when it is blank. paid_date is the date of the
customer's first successful payment above zero, or blank. Only the customer ID,
the created date, and the campaign field are read. Names and emails are never
copied. Without --out the CSV goes to standard output and the summary to
standard error. MM/DD/YYYY dates need --us-dates. An Amount column that writes
decimals with a comma ("49,00") needs --decimal-comma; a semicolon file with
such a cell turns it on by itself.
The input files are left unchanged.
"""
import argparse
import csv
import sys

sys.dont_write_bytecode = True
from saas_ads_common import money_mode, normalise_header, num, parse_day, read_table  # noqa: E402

CUSTOMER_ID = ["id", "customer_id"]
CUSTOMER_CREATED = ["created", "created_date", "created_at"]
PAYMENT_CUSTOMER = ["customer_id", "customer"]
PAYMENT_DATE = ["created_date", "created", "date"]
PAYMENT_AMOUNT = ["amount", "amount_paid", "total"]
PAID_STATUS = {"succeeded", "paid"}
UNATTRIBUTED = "unattributed"
T26_SHARE = 0.10


def pick(header, candidates, what):
    for name in candidates:
        if name in header:
            return name
    raise ValueError(f"no {what} column (looked for {', '.join(candidates)}); headers found: {', '.join(header)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("customers_csv")
    parser.add_argument("payments_csv")
    parser.add_argument("--campaign-field", required=True)
    parser.add_argument("--out", help="write the CSV here instead of standard output")
    parser.add_argument("--us-dates", action="store_true", help="read dates as MM/DD/YYYY")
    parser.add_argument("--decimal-comma", action="store_true", help="amounts are written 49,00")
    args = parser.parse_args()
    try:
        customers = read_table(args.customers_csv, [])
        payments = read_table(args.payments_csv, [])
        c_header = list(customers[0])
        p_header = list(payments[0])
        id_col = pick(c_header, CUSTOMER_ID, "customer ID")
        created_col = pick(c_header, CUSTOMER_CREATED, "customer created")
        field = normalise_header(args.campaign_field)
        if field not in c_header:
            raise ValueError(f"campaign field {args.campaign_field!r} not found in the Customers file; headers found: {', '.join(c_header)}")
        pay_customer = pick(p_header, PAYMENT_CUSTOMER, "payment customer")
        pay_date = pick(p_header, PAYMENT_DATE, "payment date")
        pay_amount = next((c for c in PAYMENT_AMOUNT if c in p_header), None)
        dc = money_mode(payments, args.decimal_comma, [pay_amount] if pay_amount else [])
        has_status = "status" in p_header
        people = {}
        for row in customers:
            key = (row[id_col] or "").strip()
            if not key:
                raise ValueError("blank customer ID in the Customers file")
            if key in people:
                raise ValueError(f"duplicate customer ID {key}")
            people[key] = [(row[field] or "").strip() or UNATTRIBUTED, parse_day(row[created_col], args.us_dates), None]
        skipped = unknown = before_signup = 0
        for row in payments:
            if has_status and (row["status"] or "").strip().lower() not in PAID_STATUS:
                skipped += 1
                continue
            if pay_amount:
                try:
                    if num(row[pay_amount], dc) <= 0:
                        skipped += 1
                        continue
                except ValueError:
                    skipped += 1
                    continue
            key = (row[pay_customer] or "").strip()
            if key not in people:
                unknown += 1
                continue
            when = parse_day(row[pay_date], args.us_dates)
            if when < people[key][1]:
                before_signup += 1
                continue
            if people[key][2] is None or when < people[key][2]:
                people[key][2] = when
    except (OSError, ValueError) as error:
        print(f"ERROR: needs_data: {error}", file=sys.stderr)
        return 2
    ordered = sorted(people.values(), key=lambda item: (item[1], item[0]))
    handle = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    try:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["campaign", "signup_date", "paid_date"])
        for campaign, signup, paid in ordered:
            writer.writerow([campaign, signup.isoformat(), paid.isoformat() if paid else ""])
    finally:
        if args.out:
            handle.close()
    total = len(ordered)
    unattributed = sum(1 for item in ordered if item[0] == UNATTRIBUTED)
    paid_total = sum(1 for item in ordered if item[2])
    out = sys.stdout if args.out else sys.stderr
    print(f"customers: {total}; paid: {paid_total}; unattributed: {unattributed} ({unattributed / total:.1%})", file=out)
    print(f"payments skipped (not paid or not above zero): {skipped}; payments for unknown customers: {unknown}; payments dated before signup: {before_signup}", file=out)
    if unattributed / total >= T26_SHARE:
        print("T26: unattributed customers are at least 10% of the total, so they can change a channel ranking. Start capturing the campaign at signup.", file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
