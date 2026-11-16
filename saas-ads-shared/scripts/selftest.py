#!/usr/bin/env python3
"""Self-test for the saas-ads-shared helpers.

Runs every helper on the sample CSVs and on edge cases, and checks the output.
Needs only the Python 3 standard library. Writes temporary files only in the
system temp folder.
"""
import csv
import datetime
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "examples", "data")
TEMPLATES = os.path.join(HERE, "..", "templates")


def run(script, *args):
    result = subprocess.run(
        [sys.executable, os.path.join(HERE, script), *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def sample(name):
    return os.path.join(DATA, name)


def temp_csv(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    handle.write(text)
    handle.close()
    return handle.name


FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print(f"ok   {name}")
    else:
        print(f"FAIL {name} {detail}")
        FAILURES.append(name)


def example_block(skill):
    path = os.path.join(HERE, "..", "..", skill, "SKILL.md")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    section = text.split("## Practical example", 1)[1]
    start = section.index("```text") + len("```text")
    return section[start:section.index("```", start)].splitlines()


def new_checks():
    small = sample("small_account.csv")
    pool = "meta_prospecting=meta_prospecting_a,meta_prospecting_b"
    window = ["--window-days", "90", "--as-of", "2026-11-16"]
    code, out, _ = run("cac.py", small, *window, "--pool", pool)
    check(
        "cac pool and window",
        code == 0
        and "window:\t2026-08-19..2026-11-16 (90 days)" in out
        and "meta_prospecting\t8400.00\t23\t365.22\t75.7%\t33.8%\tpooled" in out
        and "meta_retargeting\t1500.00\t14\t107.14\t13.5%\t20.6%\tinsufficient_volume" in out
        and "pool:\tmeta_prospecting = meta_prospecting_a, meta_prospecting_b" in out,
        out,
    )
    code, out, _ = run("cac.py", small, *window)
    check("cac without a pool leaves ad sets thin", code == 0 and "meta_prospecting_a\t4300.00\t11\t390.91" in out and "pooled" not in out, out)
    check("cac pool across platforms rejected", run("cac.py", small, "--pool", "x=meta_prospecting_a,google_search_brand")[0] == 2)
    check("cac pool with an unknown member rejected", run("cac.py", small, "--pool", "x=meta_prospecting_a,nope")[0] == 2)
    check("cac pool of one member rejected", run("cac.py", small, "--pool", "x=meta_prospecting_a")[0] == 2)
    check("cac pool with a member in two pools rejected", run("cac.py", small, "--pool", "x=meta_prospecting_a,meta_prospecting_b", "--pool", "y=meta_prospecting_b,meta_retargeting")[0] == 2)
    path = temp_csv("channel,spend,new_paying_customers\ngoogle_search_brand,100,30\ngoogle_search_nonbrand,500,25\n")
    check("cac pool mixing brand with non-brand rejected", run("cac.py", path, "--pool", "x=google_search_brand,google_search_nonbrand")[0] == 2)

    path = temp_csv("Channel;Spend;New Paying Customers\nsearch;1200;25\nmeta;500;10\n")
    code, out, _ = run("cac.py", path)
    check("cac semicolon file and spaced headers", code == 0 and "search\t1200.00\t25\t48.00" in out and "blended_media\t1700.00\t35\t48.57" in out, out)
    code, out, err = run("cac.py", temp_csv("foo,bar\n1,2\n"))
    check("cac error lists the headers found", code == 2 and "headers found" in err and "foo" in err, err)
    path = temp_csv("channel,spend,new_paying_customers,date\na,100,5,10/01/2026\n")
    check("cac US date needs the flag", run("cac.py", path, "--window-days", "30", "--as-of", "2026-11-16")[0] == 2)
    code, out, _ = run("cac.py", path, "--window-days", "60", "--as-of", "2026-11-16", "--us-dates")
    check("cac accepts US dates with the flag", code == 0 and "a\t100.00\t5\t20.00" in out, out)
    code, out, _ = run("cac_recovery.py", "--cac", "480", "--arpa", "79", "--gross-margin", "80%", "--monthly-churn", "4%")
    check("recovery accepts percent inputs", code == 0 and "churn_adjusted_payback_months:\t8.9" in out and "T21_affordable_cost_12m:\t611.92" in out and "T21_affordable_cost_18m:\t822.23" in out, out)

    rows = "campaign,signup_date,paid_date\n" + "".join(f"meta_a,2026-09-01,{'2026-09-05' if i < 6 else ''}\n" for i in range(20))
    rows += "".join(f"meta_b,2026-09-02,{'2026-09-06' if i < 6 else ''}\n" for i in range(20))
    path = temp_csv(rows)
    base = ["--trial-days", "14", "--as-of", "2026-11-16"]
    code, out, _ = run("trial_to_paid.py", path, *base, "--pool", "meta=meta_a,meta_b")
    check("trial pool label and pool line", code == 0 and "meta\t40\t40\t0\t12\t30.0%" in out and "\tpooled" in out and "pool:\tmeta = meta_a, meta_b" in out, out)
    code, out, _ = run("trial_to_paid.py", path, *base)
    check("trial without a pool is insufficient_volume", code == 0 and "meta_a\t20\t20\t0\t6\t30.0%" in out and "insufficient_volume" in out, out)
    code, out, _ = run("trial_to_paid.py", path, *base, "--window-days", "90")
    check("trial window rule line", code == 0 and "window_rule:" in out, out)
    check("trial pool of unknown member rejected", run("trial_to_paid.py", path, *base, "--pool", "meta=meta_a,nope")[0] == 2)
    path = temp_csv("campaign,signup_date,paid_date\na,10/01/2026,10/05/2026\n")
    check("trial US date needs the flag", run("trial_to_paid.py", path, *base)[0] == 2)
    code, out, _ = run("trial_to_paid.py", path, *base, "--us-dates")
    check("trial accepts US dates with the flag", code == 0 and "a\t1\t1\t0\t1\t100.0%" in out, out)

    lag = sample("lag_customers.csv")
    code, out, _ = run("lag.py", lag, "--as-of", "2026-11-16", "--window-days", "7", "--spend", sample("lag_monthly_spend.csv"))
    check(
        "lag sample",
        code == 0
        and "median_click_to_paid_days:\t5" in out
        and "p80_click_to_paid_days:\t26" in out
        and "cohort_customers:\t144" in out
        and "censoring:\tlag percentiles and T15 use only clicks dated on or before 2026-08-18 (as-of minus 90 days), 144 of 231 customers" in out
        and "T15_later_than_window:\t57 of 144" in out
        and "T15_verdict:\twindow_too_short" in out
        and "2026-05\t8200.00\t38\t215.79" in out
        and "2026-10\t7600.00\t32\tn/a\t2026-11-26\timmature" in out
        and "mature_months_total\t43800.00\t199\t220.10" in out,
        out,
    )
    path = temp_csv("click_date,paid_date\n2026-10-10,2026-10-01\n")
    check("lag paid before click rejected", run("lag.py", path, "--as-of", "2026-11-16")[0] == 2)
    path = temp_csv("click_date,paid_date\n2026-10-10,2026-12-01\n")
    check("lag paid after as-of rejected", run("lag.py", path, "--as-of", "2026-11-16")[0] == 2)
    path = temp_csv("click_date,paid_date\n" + "".join("2026-07-01,2026-07-03\n" for _ in range(5)))
    code, out, _ = run("lag.py", path, "--as-of", "2026-11-16", "--window-days", "7")
    check("lag below 20 customers needs_data", code == 0 and "T15_verdict:\tneeds_data" in out, out)
    code, out, err = run("lag.py", lag, "--as-of", "2026-11-16", "--cohort-cutoff-days", "400")
    check("lag with a cut-off older than every click exits 2", code == 2 and "no click dated on or before" in err, err)
    code, out, _ = run("lag.py", lag, "--as-of", "2026-11-16", "--cohort-cutoff-days", "0")
    check("lag cut-off 0 uses every click", code == 0 and "cohort_customers:\t231" in out, out)
    meta_style = temp_csv("Campaign name,Signup date,Paid date\na,2026-09-01,2026-09-05\na,2026-09-02,\n")
    google_style = temp_csv("Campaign,Cost\na,100\n")
    code, out, err = run("trial_to_paid.py", meta_style, "--trial-days", "14", "--as-of", "2026-11-16", "--spend", google_style)
    check(
        "header synonyms: Meta campaign name and Google cost are mapped and reported",
        code == 0 and "header_mapping:\t" in err and "Campaign name -> campaign" in err and "Cost -> spend" in err and "header_mapping" not in out,
        err,
    )
    code, out, err = run("lag.py", lag, "--as-of", "2026-11-16", "--spend", temp_csv("Month,Amount spent (USD)\n2026-05,8200\n"))
    check(
        "header synonyms: Meta amount spent with a unit is mapped",
        code == 0 and "Amount spent (USD) -> spend" in err and "2026-05\t8200.00\t38" in out,
        err,
    )
    code, out, err = run("lag.py", lag, "--as-of", "2026-11-16", "--spend", temp_csv("Month,Spend (USD)\n2026-05,8200\n"))
    check("header synonyms: a unit in brackets is stripped and reported", code == 0 and "Spend (USD) -> spend" in err, err)
    code, out, err = run("lag.py", lag, "--as-of", "2026-11-16", "--spend", temp_csv("month,spend,cost\n2026-05,8200,1\n"))
    check("header synonyms: an exact spend column wins over cost", code == 0 and "header_mapping" not in err and "2026-05\t8200.00" in out, err)
    code, _, err = run("lag.py", lag, "--as-of", "2026-11-16", "--spend", temp_csv("month,budget\n2026-05,8200\n"))
    check("header synonyms: an unknown spend header still lists the headers found", code == 2 and "headers found: month, budget" in err, err)

    margin = sample("marginal_cac_periods.csv")
    window = ["--days-before", "28", "--days-after", "28", "--affordable", "611.92", "--after-end", "2026-10-26", "--as-of", "2026-11-16", "--trial-days", "14"]
    code, out, _ = run("marginal_cac.py", margin, *window)
    check(
        "marginal sample",
        code == 0
        and "google_search_nonbrand\t6000.00\t7200.00\t20\t24\t20.0%\t300.00\twithin_affordable" in out
        and "meta_prospecting\t8000.00\t9600.00\t18\t20\t20.0%\t800.00\tover_affordable" in out
        and "meta_retargeting\t1200.00\t1300.00\t20\t21\t8.3%\tn/a\tneeds_data" in out
        and "account\t15200.00\t18100.00\t58\t65\t19.1%\t414.29\twithin_affordable" in out,
        out,
    )
    check("marginal unequal periods rejected", run("marginal_cac.py", margin, "--days-before", "28", "--days-after", "14", "--affordable", "600", "--after-end", "2026-10-26", "--as-of", "2026-11-16", "--trial-days", "14")[0] == 2)
    check("marginal periods under 14 days rejected", run("marginal_cac.py", margin, "--days-before", "10", "--days-after", "10", "--affordable", "600", "--after-end", "2026-10-26", "--as-of", "2026-11-16", "--trial-days", "14")[0] == 2)
    check(
        "marginal prints the period dates, the maturity rule, and the seasonality caveat",
        "periods:\tbefore 2026-09-01..2026-09-28 (28 days), after 2026-09-29..2026-10-26 (28 days)" in out
        and "maturity_rule:\tcustomers are counted by signup date and every signup in both periods is matured (T02): 2026-11-16 is on or after 2026-11-16 (21 lag days = 14 trial days + 7 billing lag days)" in out
        and "ignores seasonality" in out
        and "not incrementality" in out,
        out,
    )
    young = [a if a != "2026-11-16" else "2026-11-10" for a in window]
    code, _, err = run("marginal_cac.py", margin, *young)
    check("marginal stops while the after period is immature", code == 2 and "mature on 2026-11-16" in err, err)
    lag_only = [a for a in window if a not in ("--trial-days", "14")]
    code, out, _ = run("marginal_cac.py", margin, *lag_only, "--lag-days", "7")
    check("marginal accepts --lag-days instead of trial days", code == 0 and "(7 lag days)" in out, out)
    check("marginal needs a lag rule", run("marginal_cac.py", margin, *lag_only)[0] == 2)
    design = ["--design", "--affordable", "611.92", "--trial-days", "14", "--start", "2026-12-01"]
    code, out, _ = run("marginal_cac.py", *design, "--daily-spend", "400", "--current-cac", "150")
    check(
        "marginal design for a fast channel",
        code == 0
        and "step:\traise daily spend from 400.00 to 480.00 on 2026-12-01" in out
        and "period_days:\t14 before and 14 after" in out
        and "before_period:\t2026-11-17..2026-11-30" in out
        and "after_period:\t2026-12-01..2026-12-14" in out
        and "minimum_spend_after:\t6720.00" in out
        and "extra_spend:\t1120.00" in out
        and "extra_customers_needed:\t1.8 or more" in out
        and "check_date:\t2027-01-04" in out
        and "not incrementality" in out,
        out,
    )
    code, out, _ = run("marginal_cac.py", *design, "--daily-spend", "100", "--current-cac", "400")
    check(
        "marginal design for a slow channel needs more days",
        code == 0
        and "period_days:\t67 before and 67 after" in out
        and "after_period:\t2026-12-01..2027-02-05" in out
        and "check_date:\t2027-02-26" in out
        and "extra_customers_needed:\t2.2 or more" in out,
        out,
    )
    code, out, _ = run("marginal_cac.py", *design, "--daily-spend", "100", "--current-cac", "700")
    check("marginal design warns when the current cost is above affordable", code == 0 and "T27_note:" in out, out)
    check("marginal design needs its inputs", run("marginal_cac.py", "--design", "--affordable", "611.92", "--trial-days", "14")[0] == 2)

    path = temp_csv("channel,spend,new_paying_customers\nsearch,1000,25\n,0,7\n")
    code, out, _ = run("cac.py", path)
    check(
        "cac blank channel becomes unattributed with the T26 note",
        code == 0
        and "unattributed\t0.00\t7\tn/a\t0.0%\t21.9%\tunattributed" in out
        and "blended_excl_unattributed\t1000.00\t25\t40.00" in out
        and "T26:\tunattributed customers are at least 10% of the total" in out,
        out,
    )
    path = temp_csv("channel,spend,new_paying_customers\nsearch,1000,25\n,200,3\n")
    code, out, _ = run("cac.py", path)
    check("cac blank channel with spend prints n/a", code == 0 and "unattributed\t200.00\t3\tn/a" in out and "\tunattributed" in out, out)
    path = temp_csv("channel,spend,new_paying_customers\nsearch,1000,25\n,0,1\n")
    code, out, _ = run("cac.py", path)
    check("cac small unattributed share has no T26 note", code == 0 and "unattributed\t0.00\t1\tn/a" in out and "T26:" not in out, out)
    rows = "campaign,signup_date,paid_date\n" + "".join(f"a,2026-09-01,{'2026-09-05' if i < 10 else ''}\n" for i in range(30))
    rows += "".join(f",2026-09-01,{'2026-09-05' if i < 5 else ''}\n" for i in range(10))
    path = temp_csv(rows)
    spend_path = temp_csv("campaign,spend\na,300\n")
    code, out, _ = run("trial_to_paid.py", path, *base, "--spend", spend_path)
    check(
        "trial blank campaign becomes unattributed with the T26 note and no spend row needed",
        code == 0
        and "unattributed\t10\t10\t0\t5\t50.0%\t4\tunattributed" in out
        and "unattributed\t0.00\t10\t5\tn/a\tn/a\tunattributed" in out
        and "T26:\tunattributed customers are at least 10% of the total" in out,
        out,
    )

    path = temp_csv("channel;spend;new_paying_customers\nsearch;1.200,50;25\nmeta;500,00;10\n")
    code, out, _ = run("cac.py", path)
    check("cac decimal comma turns on by itself in a semicolon file", code == 0 and "search\t1200.50\t25\t48.02" in out and "meta\t500.00\t10\t50.00" in out, out)
    path = temp_csv("channel;spend;new_paying_customers\nsearch;1,200;25\n")
    code, out, _ = run("cac.py", path)
    check("cac semicolon file with 1,200 stays a thousands comma", code == 0 and "search\t1200.00\t25\t48.00" in out, out)
    path = temp_csv('channel,spend,new_paying_customers\nsearch,"1.200,50",25\n')
    code, out, _ = run("cac.py", path, "--decimal-comma")
    check("cac --decimal-comma works on a comma file", code == 0 and "search\t1200.50\t25\t48.02" in out, out)
    code, out, _ = run("brand_split.py", temp_csv("segment;spend;paying_customers\nbrand;1.800,00;45\nnon_brand;16.200,00;64\n"))
    check("brand_split decimal comma", code == 0 and "brand\t1800.00\t45\t40.00" in out and "non_brand\t16200.00\t64\t253.12" in out, out)
    code, out, _ = run("cac_recovery.py", "--cac", "1.200,50", "--arpa", "79,00", "--gross-margin", "80%", "--monthly-churn", "4%", "--decimal-comma")
    check("recovery decimal comma flag", code == 0 and "simple_payback_months:\t19.0" in out, out)
    check("recovery decimal comma needs the flag", run("cac_recovery.py", "--cac", "1.200,50", "--arpa", "79", "--gross-margin", "80%")[0] == 2)
    path = temp_csv("channel;period;spend;new_paying_customers\nsearch;before;5.000,00;20\nsearch;after;6.000,00;25\n")
    code, out, _ = run("marginal_cac.py", path, *window)
    check("marginal decimal comma", code == 0 and "search\t5000.00\t6000.00\t20\t25\t20.0%\t200.00\twithin_affordable" in out, out)
    code, out, _ = run("lag.py", lag, "--as-of", "2026-11-16", "--spend", temp_csv("month;spend\n2026-05;8.200,00\n"))
    check("lag spend decimal comma", code == 0 and "2026-05\t8200.00\t38\t215.79" in out, out)
    code, out, _ = run("cac_recovery.py", "--cac", "480", "--arpa", "79", "--gross-margin", "0.8")
    check("recovery prints the excludes line without churn", code == 0 and "excludes:\texpansion revenue, annual prepay cash timing" in out, out)
    code, out, _ = run("cac_recovery.py", "--arpa", "79", "--gross-margin", "80%", "--churn-by-source", sample("churn_by_source.csv"))
    check("recovery prints the excludes line by source", code == 0 and "excludes:\texpansion revenue, annual prepay cash timing" in out, out)

    out_file = temp_csv("")
    code, out, err = run("stripe_join.py", sample("stripe_customers.csv"), sample("stripe_payments.csv"), "--campaign-field", "campaign")
    check(
        "stripe_join prints the three columns with no email",
        code == 0
        and out.splitlines()[0] == "campaign,signup_date,paid_date"
        and "@" not in out
        and "unattributed" in out
        and "customers: 40; paid: 24; unattributed: 10 (25.0%)" in err,
        out + err,
    )
    code, _, _ = run("stripe_join.py", sample("stripe_customers.csv"), sample("stripe_payments.csv"), "--campaign-field", "campaign", "--out", out_file)
    with open(out_file, encoding="utf-8") as handle:
        written = handle.read()
    check("stripe_join --out writes the file", code == 0 and written == out, written)
    code, joined, _ = run("trial_to_paid.py", out_file, "--trial-days", "14", "--as-of", "2026-11-16")
    check("stripe_join output feeds trial_to_paid", code == 0 and "unattributed" in joined, joined)
    check("stripe_join unknown campaign field rejected", run("stripe_join.py", sample("stripe_customers.csv"), sample("stripe_payments.csv"), "--campaign-field", "nope")[0] == 2)

    pipe = sample("lead_pipeline.csv")
    code, out, _ = run("lead_to_won.py", pipe, "--as-of", "2026-11-16", "--spend", sample("pipeline_spend.csv"))
    check(
        "lead_to_won sample",
        code == 0
        and "sales_cycle_days:\t58" in out
        and "linkedin_abm\t70\t53\t17\t27\t50.9%\t10\t37.0%\t40\t111000.00\tok" in out
        and "account\t48000.00\t166\t81\t25\t592.59\t1920.00\tok" in out,
        out,
    )
    path = temp_csv("campaign,lead_date,meeting_date,won_date\na,2026-01-01,,2026-02-01\n")
    check("lead_to_won won without a meeting rejected", run("lead_to_won.py", path, "--as-of", "2026-11-16", "--sales-cycle-days", "30")[0] == 2)

    churn = sample("churn_by_source.csv")
    code, out, _ = run("cac_recovery.py", "--arpa", "79", "--gross-margin", "80%", "--churn-by-source", churn)
    check(
        "recovery churn by source",
        code == 0
        and "google_search_nonbrand\t300.00\t0.0300\t4.7\t5.0\t644.97\tok" in out
        and "meta_prospecting\t500.00\t0.0900\t7.9\t13.2\t475.77\treview" in out
        and "meta_retargeting\t55.00\tn/a\t0.9\tn/a\tn/a\tneeds_churn" in out,
        out,
    )
    check("recovery churn flags are exclusive", run("cac_recovery.py", "--arpa", "79", "--gross-margin", "0.8", "--churn-by-source", churn, "--monthly-churn", "0.04")[0] == 2)
    path = temp_csv("source,monthly_churn\nx,3%\n")
    check("recovery churn by source needs a cac", run("cac_recovery.py", "--arpa", "79", "--gross-margin", "0.8", "--churn-by-source", path)[0] == 2)

    for name in ["lag_customers.csv", "lag_monthly_spend.csv", "marginal_cac_periods.csv", "churn_by_source.csv", "lead_pipeline.csv"]:
        with open(os.path.join(TEMPLATES, name), newline="", encoding="utf-8") as handle:
            template_rows = list(csv.reader(handle))
        with open(sample(name), newline="", encoding="utf-8") as handle:
            sample_header = next(csv.reader(handle))
        check(f"template {name} is header-only and matches the sample header", len(template_rows) == 1 and template_rows[0] == sample_header, str(template_rows))

    examples = {
        "cost-per-paying-customer-saas-ads": ("cac.py", [sample("cac_channels.csv"), "--extra-cost", "2400"]),
        "trial-to-paid-by-campaign-saas-ads": (
            "trial_to_paid.py",
            [sample("trial_to_paid.csv"), "--trial-days", "14", "--as-of", "2026-11-16", "--spend", sample("campaign_spend.csv")],
        ),
        "brand-nonbrand-split-saas-ads": ("brand_split.py", [sample("brand_split.csv")]),
        "payback-period-check-saas-ads": ("cac_recovery.py", ["--cac", "480", "--arpa", "79", "--gross-margin", "0.8", "--monthly-churn", "0.04"]),
    }
    for skill, (script, args) in examples.items():
        code, out, _ = run(script, *args)
        block = example_block(skill)
        missing = [line for line in out.splitlines() if line.strip() and line not in block]
        check(f"{skill} example block matches the {script} output", code == 0 and not missing, str(missing))


def main():
    code, out, _ = run("cac.py", sample("cac_channels.csv"), "--extra-cost", "2400")
    check("cac sample blended", code == 0 and "blended_media\t18000.00\t109\t165.14" in out, out)
    check("cac sample extra cost", "blended_with_extra_cost\t20400.00\t109\t187.16" in out, out)
    check("cac thin channel flagged", "meta_prospecting\t6000.00\t12\t500.00\t33.3%\t11.0%\tinsufficient_volume" in out, out)
    path = temp_csv("channel,spend,new_paying_customers\nzero,500,0\n")
    code, out, _ = run("cac.py", path)
    check("cac zero customers prints n/a", code == 0 and "zero\t500.00\t0\tn/a" in out and "no_paying_customers" in out, out)
    path = temp_csv("channel,spend,new_paying_customers\nblank,500,\n")
    check("cac blank cell is missing", run("cac.py", path)[0] == 2)
    path = temp_csv("channel,spend,new_paying_customers\nnan,nan,5\n")
    check("cac NaN rejected", run("cac.py", path)[0] == 2)
    path = temp_csv("channel,spend,new_paying_customers\ndash,--,5\n")
    check("cac double dash rejected", run("cac.py", path)[0] == 2)
    path = temp_csv(
        "channel,spend,new_paying_customers\n"
        'search,"1,200.50",25\n'
        "meta,\u20ac500,10\n"
        "zl,500 z\u0142,2\n"
        "pln,PLN 300,3\n"
        'usd,"$2 000.00 USD",4\n'
    )
    code, out, _ = run("cac.py", path)
    check(
        "cac money formats parse",
        code == 0
        and "search\t1200.50\t25\t48.02" in out
        and "meta\t500.00\t10\t50.00" in out
        and "zl\t500.00\t2\t250.00" in out
        and "pln\t300.00\t3\t100.00" in out
        and "usd\t2000.00\t4\t500.00" in out,
        out,
    )
    path = temp_csv('channel,spend,new_paying_customers\nsearch,"1.200,50",25\n')
    check("cac European decimal comma rejected", run("cac.py", path)[0] == 2)
    path = temp_csv("channel,spend,new_paying_customers\nsearch,1000,25\nunattributed,0,7\n")
    code, out, _ = run("cac.py", path)
    check(
        "cac unattributed prints n/a and its label",
        code == 0
        and "unattributed\t0.00\t7\tn/a\t0.0%\t21.9%\tunattributed" in out
        and "blended_excl_unattributed\t1000.00\t25\t40.00" in out,
        out,
    )

    code, out, _ = run("trial_to_paid.py", sample("trial_to_paid.csv"), "--trial-days", "14", "--as-of", "2026-11-16")
    check("trial sample weak campaign", code == 0 and "meta_lookalike\t43\t40\t3\t4\t10.0%\t16\tweak_paid_rate" in out, out)
    check("trial sample account rate", "account\t138\t130\t8\t34\t26.2%\t13\t-" in out, out)
    path = temp_csv("campaign,signup_date,paid_date\na,2026-11-01,2026-10-30\n")
    check("trial paid before signup rejected", run("trial_to_paid.py", path, "--trial-days", "14", "--as-of", "2026-11-16")[0] == 2)
    path = temp_csv("campaign,signup_date,paid_date\na,2026-11-20,\n")
    check("trial future signup rejected", run("trial_to_paid.py", path, "--trial-days", "14", "--as-of", "2026-11-16")[0] == 2)
    path = temp_csv(
        "campaign,signup_date,paid_date\n"
        "a,2026-10-01 09:30:00,2026-10-05T14:00:00\n"
        "a,2026-10-02T08:15,\n"
        "a,2026-10-03 10:00,2026-10-20 11:45:10\n"
    )
    code, out, _ = run("trial_to_paid.py", path, "--trial-days", "14", "--as-of", "2026-11-16T08:00:00")
    check("trial timestamps parse", code == 0 and "a\t3\t3\t0\t2\t66.7%\t" in out, out)
    path = temp_csv("campaign,signup_date,paid_date\na,2026-10-01 25:00,\n")
    check("trial invalid time rejected", run("trial_to_paid.py", path, "--trial-days", "14", "--as-of", "2026-11-16")[0] == 2)
    code, out, _ = run("trial_to_paid.py", sample("trial_to_paid.csv"), "--trial-days", "14", "--as-of", "2026-11-16", "--spend", sample("campaign_spend.csv"))
    check(
        "trial spend prints cost per signup and per paying customer",
        code == 0
        and "brand_search\t1200.00\t40\t16\t30.00\t75.00\tinsufficient_volume" in out
        and "nonbrand_search\t6300.00\t50\t14\t126.00\t450.00\tinsufficient_volume" in out
        and "meta_lookalike\t2800.00\t40\t4\t70.00\t700.00\tinsufficient_volume" in out
        and "account\t10300.00\t130\t34\t79.23\t302.94\tok" in out
        and "spend must cover only signup dates up to 2026-10-26" in out,
        out,
    )
    path = temp_csv("campaign,spend\nbrand_search,\"$1,200\"\n")
    check("trial spend missing a campaign needs_data", run("trial_to_paid.py", sample("trial_to_paid.csv"), "--trial-days", "14", "--as-of", "2026-11-16", "--spend", path)[0] == 2)

    code, out, _ = run("reconcile.py", sample("platform_vs_billing.csv"))
    check("reconcile labels", code == 0 and "google_ads\t62\t41\t1.51\tplatform_over" in out and "meta_retargeting\t20\t40\t0.50\tplatform_under" in out and "meta_prospecting\t30\t36\t0.83\twithin_band" in out, out)
    path = temp_csv("source,platform_reported,billing_count\nx,10,0\n")
    code, out, _ = run("reconcile.py", path)
    check("reconcile zero billing needs_data", code == 0 and "x\t10\t0\tn/a\tneeds_data" in out, out)
    path = temp_csv('source,platform_reported,billing_count\nx,"1,000",800\n')
    code, out, _ = run("reconcile.py", path)
    check("reconcile thousands comma parses", code == 0 and "x\t1000\t800\t1.25\twithin_band" in out, out)

    code, out, _ = run("cac_recovery.py", "--cac", "480", "--arpa", "79", "--gross-margin", "0.8", "--monthly-churn", "0.04")
    check("recovery sample", code == 0 and "simple_payback_months:\t7.6" in out and "churn_adjusted_payback_months:\t8.9" in out and "T05_verdict:\tok" in out, out)
    code, out, _ = run("cac_recovery.py", "--cac", "2000", "--arpa", "79", "--gross-margin", "0.8", "--monthly-churn", "0.04")
    check("recovery never pays back", code == 0 and "churn_adjusted_payback_months:\tnever" in out and "hold_scale" in out, out)
    check("recovery churn of 1 rejected", run("cac_recovery.py", "--cac", "100", "--arpa", "50", "--gross-margin", "0.8", "--monthly-churn", "1")[0] == 2)
    check("recovery margin above 1 rejected", run("cac_recovery.py", "--cac", "100", "--arpa", "50", "--gross-margin", "1.2")[0] == 2)
    code, out, _ = run("cac_recovery.py", "--cac", "480", "--arpa", "79", "--gross-margin", "0.8")
    check("recovery without churn needs_churn", code == 0 and "T05_verdict:\tneeds_churn" in out and "simple_payback_months:\t7.6" in out, out)
    code, out, _ = run("cac_recovery.py", "--cac", "2000", "--arpa", "79", "--gross-margin", "0.8")
    check("recovery without churn notes a past-hold simple payback", code == 0 and "T05_verdict:\tneeds_churn" in out and "past the 18 month hold line" in out, out)
    code, out, _ = run("cac_recovery.py", "--cac", "$4,400", "--acv", "6,000", "--gross-margin", "0.8", "--annual-churn", "0.2")
    check("recovery annual contract branch", code == 0 and "arpa_from_acv:\t500.00" in out and "simple_payback_months:\t11.0" in out and "monthly_churn_from_annual:\t0.0184" in out and "T05_verdict:\t" in out and "needs_churn" not in out, out)
    check("recovery arpa and acv together rejected", run("cac_recovery.py", "--cac", "100", "--arpa", "50", "--acv", "600", "--gross-margin", "0.8")[0] == 2)

    code, out, _ = run("brand_split.py", sample("brand_split.csv"))
    check("brand sample", code == 0 and "blended\t18000.00\t109\t165.14" in out and "non_brand\t16200.00\t64\t253.12" in out and "T09_verdict:\treport_split" in out, out)
    path = temp_csv("segment,spend,paying_customers\nbrand,100,5\n")
    check("brand needs both segments", run("brand_split.py", path)[0] == 2)
    path = temp_csv("segment,spend,paying_customers\nbrand,100,5\nother,100,5\n")
    check("brand rejects other segment", run("brand_split.py", path)[0] == 2)
    path = temp_csv('segment,spend,paying_customers\nbrand,"$1,800",45\nnon_brand,\u20ac16 200,64\n')
    code, out, _ = run("brand_split.py", path)
    check("brand money formats parse", code == 0 and "brand\t1800.00\t45\t40.00" in out and "non_brand\t16200.00\t64\t253.12" in out, out)

    code, out, _ = run("fatigue.py", sample("fatigue_daily.csv"))
    check(
        "fatigue labels",
        code == 0
        and "Tired angle\t7886\t7790\t1.23%\t0.90%\t1.11\t1.45\tfatigue_candidate" in out
        and "Steady angle\t8748\t8074\t1.26%\t1.25%\t1.14\t1.19\tno_signal" in out
        and "Small angle\t2386\t2267\t1.30%\t1.32%\t1.08\t1.12\tinsufficient_window" in out
        and "Thin angle\t-\t-\t-\t-\t-\t-\tinsufficient_window" in out
        and "note:\tDaily-row frequency near 1.0 to 1.2 is normal" in out,
        out,
    )
    path = temp_csv("date,ad,impressions,clicks,frequency\n2026-11-01,a,100,1,1.0\n2026-11-01,a,100,1,1.0\n")
    check("fatigue duplicate rows rejected", run("fatigue.py", path)[0] == 2)
    start = datetime.date(2026, 11, 1)
    stamped = "date,ad,impressions,clicks,frequency\n" + "".join(
        f"{(start + datetime.timedelta(days=i)).isoformat()}T0{i % 10}:30:00,a,600,7,\"1.1\"\n" for i in range(14)
    )
    code, out, _ = run("fatigue.py", temp_csv(stamped))
    check("fatigue timestamps parse", code == 0 and "prior 2026-11-01..2026-11-07" in out and "no_signal" in out, out)

    new_checks()

    helper_inputs = {
        "cac.py": "cac_channels.csv",
        "trial_to_paid.py": "trial_to_paid.csv",
        "reconcile.py": "platform_vs_billing.csv",
        "brand_split.py": "brand_split.csv",
        "fatigue.py": "fatigue_daily.csv",
    }
    for helper, name in helper_inputs.items():
        template = os.path.join(TEMPLATES, name)
        with open(template, newline="", encoding="utf-8") as handle:
            template_rows = list(csv.reader(handle))
        with open(sample(name), newline="", encoding="utf-8") as handle:
            sample_header = next(csv.reader(handle))
        check(f"template {name} is header-only and matches the sample header", len(template_rows) == 1 and template_rows[0] == sample_header, str(template_rows))
        extra = ["--trial-days", "14", "--as-of", "2026-11-16"] if helper == "trial_to_paid.py" else []
        code, _, err = run(helper, template, *extra)
        check(f"{helper} on an empty template says needs_data", code == 2 and "no data rows" in err, err)
    with open(os.path.join(TEMPLATES, "campaign_spend.csv"), newline="", encoding="utf-8") as handle:
        spend_template = list(csv.reader(handle))
    check("template campaign_spend.csv is header-only", spend_template == [["campaign", "spend"]], str(spend_template))

    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("PASS: all helper self-tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
