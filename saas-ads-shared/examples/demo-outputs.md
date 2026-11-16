# Demo outputs

Synthetic samples only. Every block below is a real run of a helper against the files in `examples/data/`, from the pack root. The commands show the repository path. Inside an installed skill, the form is `python3 "<skill-dir>/../saas-ads-shared/scripts/<name>.py" "<absolute path to your CSV>"`.

## Cost Per Paying Customer

```bash
python3 saas-ads-shared/scripts/cac.py saas-ads-shared/examples/data/cac_channels.csv --extra-cost 2400
```

```text
channel	spend	paying	cost_per_paying	share_of_spend	share_of_paying	T01_label
google_search_nonbrand	9000.00	30	300.00	50.0%	27.5%	ok
google_search_brand	1800.00	45	40.00	10.0%	41.3%	ok
meta_prospecting	6000.00	12	500.00	33.3%	11.0%	insufficient_volume
meta_retargeting	1200.00	22	54.55	6.7%	20.2%	ok
blended_media	18000.00	109	165.14	100.0%	100.0%	ok
blended_with_extra_cost	20400.00	109	187.16	-	-	ok
read:	Cost per paying customer uses billing-confirmed customers. Platform conversions are not customers.
```

Meta prospecting has 12 paying customers, under the T01 floor of 20, so its 500.00 is arithmetic only and returns `needs_data`. The blend of 165.14 hides a 300.00 non-brand search line.

## Small account: fewer than 20 paying customers per channel

Two Meta prospecting ad sets have 11 and 12 paying customers, and retargeting has 14. Pool the two prospecting ad sets, which share a platform and an intent (T24), and use the last 90 days:

```bash
python3 saas-ads-shared/scripts/cac.py saas-ads-shared/examples/data/small_account.csv --window-days 90 --as-of 2026-11-16 --pool meta_prospecting=meta_prospecting_a,meta_prospecting_b
```

```text
window:	2026-08-19..2026-11-16 (90 days)
channel	spend	paying	cost_per_paying	share_of_spend	share_of_paying	T01_label
meta_prospecting	8400.00	23	365.22	75.7%	33.8%	pooled
meta_retargeting	1500.00	14	107.14	13.5%	20.6%	insufficient_volume
google_search_brand	1200.00	31	38.71	10.8%	45.6%	ok
blended_media	11100.00	68	163.24	100.0%	100.0%	ok
pool:	meta_prospecting = meta_prospecting_a, meta_prospecting_b. A pooled line cannot be split back out (T24).
read:	Cost per paying customer uses billing-confirmed customers. Platform conversions are not customers.
```

Verdict: the pooled prospecting line has 23 paying customers at 365.22 and may be compared. Retargeting has 14 and stays `needs_data`. Only the pooled prospecting line and brand can be ranked. Brand at 38.71 shows existing demand, not what new demand costs. Before the pool, neither ad set could be judged, and a row dated before the window was left out.

## Trial To Paid By Campaign

```bash
python3 saas-ads-shared/scripts/trial_to_paid.py saas-ads-shared/examples/data/trial_to_paid.csv --trial-days 14 --as-of 2026-11-16 --spend saas-ads-shared/examples/data/campaign_spend.csv
```

```text
campaign	signups	matured	immature	paid	paid_rate	median_days_to_paid	label
brand_search	43	40	3	16	40.0%	12	ok
nonbrand_search	52	50	2	14	28.0%	12	ok
meta_lookalike	43	40	3	4	10.0%	16	weak_paid_rate
account	138	130	8	34	26.2%	13	-
maturity_rule:	age >= 14 trial days + 7 billing lag days as of 2026-11-16
campaign	spend	matured	paid	cost_per_signup	cost_per_paying	T01_label
brand_search	1200.00	40	16	30.00	75.00	insufficient_volume
nonbrand_search	6300.00	50	14	126.00	450.00	insufficient_volume
meta_lookalike	2800.00	40	4	70.00	700.00	insufficient_volume
account	10300.00	130	34	79.23	302.94	ok
spend_rule:	spend must cover only signup dates up to 2026-10-26, the same signups counted as matured. Spend dates cannot be checked by this helper.
read:	Paid rate counts only matured signups. Immature signups are not failures yet.
```

Meta lookalike pays 10.0% against an account rate of 26.2%. Eight young signups are excluded, not counted as failures. No campaign reaches 20 paying customers, so only the account row carries a cost per paying customer. The campaign rows are arithmetic only.

## Stripe export to trial-to-paid file

`stripe_join.py` joins a Customers export and a Payments export. It writes the three-column CSV for `trial_to_paid.py` without any email, and prints a summary on the error stream.

```bash
python3 saas-ads-shared/scripts/stripe_join.py saas-ads-shared/examples/data/stripe_customers.csv saas-ads-shared/examples/data/stripe_payments.csv --campaign-field campaign --out trial_to_paid_from_stripe.csv
```

```text
customers: 40; paid: 24; unattributed: 10 (25.0%)
payments skipped (not paid or not above zero): 7; payments for unknown customers: 0; payments dated before signup: 0
T26: unattributed customers are at least 10% of the total, so they can change a channel ranking. Start capturing the campaign at signup.
```

A quarter of the customers carry no campaign, so any channel ranking from this file is provisional. See "No campaign stored in Stripe yet" in `references/getting-your-data.md`.

## Ad Platform vs Billing Check

```bash
python3 saas-ads-shared/scripts/reconcile.py saas-ads-shared/examples/data/platform_vs_billing.csv
```

```text
source	platform_reported	billing_count	platform_to_billing	T04_label
google_ads	62	41	1.51	platform_over
meta_prospecting	30	36	0.83	within_band
meta_retargeting	20	40	0.50	platform_under
all_sources	112	117	0.96	within_band
read:	Confirm dates, timezone, event definition, and attribution window match before acting on a label.
```

The total reads 0.96 and looks fine. Two sources sit outside the band and offset each other.

## Payback Period Check

```bash
python3 saas-ads-shared/scripts/cac_recovery.py --cac 480 --arpa 79 --gross-margin 0.8 --monthly-churn 0.04
```

```text
monthly_gross_margin_per_account:	63.20
simple_payback_months:	7.6
lifetime_gross_margin_per_account:	1580.00
churn_adjusted_payback_months:	8.9
T05_verdict:	ok
T21_affordable_cost_12m:	611.92
T21_affordable_cost_18m:	822.23
excludes:	expansion revenue, annual prepay cash timing
read:	Gross-margin payback. Check that CAC comes from billing-confirmed customers.
```

Gross margin per account is 79 times 0.8, which is 63.20. 480 divided by 63.20 is 7.6 months before churn. The T21 lines say what a customer may cost: 611.92 to repay in 12 months (central), 822.23 in 18 (ceiling).

With no churn supplied, the helper does not guess:

```bash
python3 saas-ads-shared/scripts/cac_recovery.py --cac 480 --arpa 79 --gross-margin 0.8
```

```text
monthly_gross_margin_per_account:	63.20
simple_payback_months:	7.6
churn_adjusted_payback_months:	n/a (no churn supplied)
T05_verdict:	needs_churn
T05_note:	simple payback is a lower bound; supply churn for a verdict
excludes:	expansion revenue, annual prepay cash timing
read:	Gross-margin payback. Check that CAC comes from billing-confirmed customers.
```

For a sales-led account, give annual contract value and annual churn instead:

```bash
python3 saas-ads-shared/scripts/cac_recovery.py --cac 4500 --acv 6000 --gross-margin 0.8 --annual-churn 0.2
```

```text
arpa_from_acv:	500.00
monthly_gross_margin_per_account:	400.00
monthly_churn_from_annual:	0.0184
simple_payback_months:	11.2
lifetime_gross_margin_per_account:	21711.44
churn_adjusted_payback_months:	12.5
T05_verdict:	review
T21_affordable_cost_12m:	4342.29
T21_affordable_cost_18m:	6176.00
excludes:	expansion revenue, annual prepay cash timing
read:	Gross-margin payback. Check that CAC comes from billing-confirmed customers.
```

## Payback per channel

When channels churn differently, give one churn per source. Gross margin may be a percent.

```bash
python3 saas-ads-shared/scripts/cac_recovery.py --arpa 79 --gross-margin 80% --churn-by-source saas-ads-shared/examples/data/churn_by_source.csv
```

```text
monthly_gross_margin_per_account:	63.20
source	cac	monthly_churn	simple_payback_months	churn_adjusted_payback_months	T21_affordable_cost_12m	T05_verdict
google_search_nonbrand	300.00	0.0300	4.7	5.0	644.97	ok
meta_prospecting	500.00	0.0900	7.9	13.2	475.77	review
meta_retargeting	55.00	n/a	0.9	n/a	n/a	needs_churn
excludes:	expansion revenue, annual prepay cash timing
read:	Payback per source uses that source's churn and this gross margin. A source with no churn row cannot be judged.
```

Meta prospecting looks fine on simple payback (7.9 months) and is under review once its 9% monthly churn is applied (13.2 months). Retargeting has no churn row, so it gets `needs_churn`, not a guess.

## Next-dollar cost

Two equal 28-day periods around a budget change. Customers are counted by signup date, and every signup in both periods must be matured, so the helper needs the last day of the after period, the export date, and the trial length. The affordable cost is the 12-month T21 figure from the payback helper above.

```bash
python3 saas-ads-shared/scripts/marginal_cac.py saas-ads-shared/examples/data/marginal_cac_periods.csv --days-before 28 --days-after 28 --after-end 2026-10-26 --as-of 2026-11-16 --trial-days 14 --affordable 611.92
```

```text
periods:	before 2026-09-01..2026-09-28 (28 days), after 2026-09-29..2026-10-26 (28 days)
maturity_rule:	customers are counted by signup date and every signup in both periods is matured (T02): 2026-11-16 is on or after 2026-11-16 (21 lag days = 14 trial days + 7 billing lag days)
T21_affordable_cost:	611.92
channel	spend_before	spend_after	paying_before	paying_after	spend_change	incremental_cac	T27_verdict
google_search_nonbrand	6000.00	7200.00	20	24	20.0%	300.00	within_affordable
meta_prospecting	8000.00	9600.00	18	20	20.0%	800.00	over_affordable
meta_retargeting	1200.00	1300.00	20	21	8.3%	n/a	needs_data
account	15200.00	18100.00	58	65	19.1%	414.29	within_affordable
read:	Incremental CAC is the cost of the extra customers only. It compares two periods, so it ignores seasonality, offer, and tracking changes, and it is not incrementality. A retargeting or brand channel can look cheap without adding customers.
```

Each channel stepped up by 20% or less, the T18 cap. The extra 1600.00 on Meta prospecting bought 2 more customers, 800.00 each, above the 611.92 it can afford. Google non-brand paid 300.00 for each added customer. Retargeting spend rose 8.3%, under the 10% T27 minimum, so it gets `needs_data`.

## Next-dollar measurement step

When no clean budget change exists, `--design` prints a plan for one channel instead of a bare `needs_data`. Illustrative numbers: 400.00 a day on a channel that costs 150.00 per paying customer, step on 2026-12-01.

```bash
python3 saas-ads-shared/scripts/marginal_cac.py --design --daily-spend 400 --current-cac 150 --start 2026-12-01 --trial-days 14 --affordable 611.92
```

```text
design:	one channel, one budget step of 20% (T18), read with T27
step:	raise daily spend from 400.00 to 480.00 on 2026-12-01
period_days:	14 before and 14 after
before_period:	2026-11-17..2026-11-30
after_period:	2026-12-01..2026-12-14
minimum_spend_after:	6720.00
paying_customers_to_read:	20 or more in the after period (T01); about 45 expected at the current cost
extra_spend:	1120.00
extra_customers_needed:	1.8 or more over the before period, or the extra spend reads as over_affordable
check_date:	2027-01-04 (21 lag days = 14 trial days + 7 billing lag days after the last signup in the after period)
hold_still:	make no other budget change on this channel from 2026-11-17 to 2026-12-14, and leave at least 7 days before any next step (T18)
read:	This plan reads one before and after step. It ignores seasonality and is not incrementality; a holdout or geo split is the proof.
```

Run the step, wait for the check date, then run the compare command above on the two periods. A before and after read is a signal, not proof.

## Click-to-paid lag

```bash
python3 saas-ads-shared/scripts/lag.py saas-ads-shared/examples/data/lag_customers.csv --as-of 2026-11-16 --window-days 7 --spend saas-ads-shared/examples/data/lag_monthly_spend.csv
```

```text
customers:	231
cohort_customers:	144
median_click_to_paid_days:	5
p80_click_to_paid_days:	26
censoring:	lag percentiles and T15 use only clicks dated on or before 2026-08-18 (as-of minus 90 days), 144 of 231 customers. Recent clicks have had less time to pay, so counting them would understate the lag.
T15_window_days:	7
T15_later_than_window:	57 of 144
T15_share_later:	39.6%
T15_verdict:	window_too_short
click_month	spend	customers	lagged_cac	mature_on	T25_label
2026-05	8200.00	38	215.79	2026-06-26	ok
2026-06	9100.00	41	221.95	2026-07-26	ok
2026-07	7800.00	36	216.67	2026-08-26	ok
2026-08	9800.00	44	222.73	2026-09-26	ok
2026-09	8900.00	40	222.50	2026-10-26	ok
2026-10	7600.00	32	n/a	2026-11-26	immature
mature_months_total	43800.00	199	220.10	-	ok
maturity_rule:	month end + 26 days (80th percentile click-to-paid) <= 2026-11-16
read:	Lagged CAC divides spend by customers whose click fell in the same month. A month younger than the lag is not a result yet.
```

Of the 144 customers with a click at least 90 days old, 39.6% paid after 7 days, so a 7-day click window loses credit for many of them. Newer clicks are left out of the lag because customers who will still pay are not in the file yet (right-censoring). Lagged CAC divides each month's spend by the customers who clicked that month, and October is left out because it is younger than the 26-day lag.

## Lead to won (demo-led or sales-led)

```bash
python3 saas-ads-shared/scripts/lead_to_won.py saas-ads-shared/examples/data/lead_pipeline.csv --as-of 2026-11-16 --spend saas-ads-shared/examples/data/pipeline_spend.csv
```

```text
sales_cycle_days:	58 (80th percentile of 27 won leads)
campaign	leads	matured	immature	meetings	show_rate	won	close_rate	median_days_lead_to_won	acv_won	T28_label
linkedin_abm	70	53	17	27	50.9%	10	37.0%	40	111000.00	ok
google_search_nonbrand	90	68	22	39	57.4%	13	33.3%	43	162000.00	ok
meta_lead_form	60	45	15	15	33.3%	2	13.3%	39	30000.00	ok
account	220	166	54	81	48.8%	25	30.9%	41	303000.00	-
maturity_rule:	lead age >= 58 sales cycle days as of 2026-11-16
campaign	spend	matured	meetings	won	cost_per_meeting	cost_per_won	T01_label
linkedin_abm	21000.00	53	27	10	777.78	2100.00	insufficient_volume
google_search_nonbrand	18000.00	68	39	13	461.54	1384.62	insufficient_volume
meta_lead_form	9000.00	45	15	2	600.00	4500.00	insufficient_volume
account	48000.00	166	81	25	592.59	1920.00	ok
spend_rule:	spend must cover only lead dates up to 2026-09-19, the same leads counted as matured. Spend dates cannot be checked by this helper.
read:	Rates count only matured leads. A lead younger than the sales cycle is not a loss yet.
```

Rates use only leads at least one sales cycle (58 days) old. The rate table carries only the T28_label (30 matured leads), and the cost table carries only the T01_label (20 won deals), so each campaign has one label per question. Meta lead form meets 30 matured leads but shows 2 won deals, so its cost per won deal is arithmetic only. Only the account row has 20 won deals.

## Brand vs Non-Brand Split

```bash
python3 saas-ads-shared/scripts/brand_split.py saas-ads-shared/examples/data/brand_split.csv
```

```text
segment	spend	paying	cost_per_paying	share_of_spend	share_of_paying	volume
brand	1800.00	45	40.00	10.0%	41.3%	ok
non_brand	16200.00	64	253.12	90.0%	58.7%	ok
blended	18000.00	109	165.14	100.0%	100.0%	-
T09_verdict:	report_split
read:	Brand demand already exists. Judge new-demand campaigns on the non_brand line.
```

Brand holds 41.3% of paying customers on 10.0% of spend. New demand costs 253.12, about 53% above the blended 165.14.

## Meta Creative Fatigue Check

```bash
python3 saas-ads-shared/scripts/fatigue.py saas-ads-shared/examples/data/fatigue_daily.csv
```

```text
windows:	prior 2026-11-02..2026-11-08	recent 2026-11-09..2026-11-15
ad	prior_impr	recent_impr	prior_ctr	recent_ctr	prior_freq	recent_freq	T07_label
Small angle	2386	2267	1.30%	1.32%	1.08	1.12	insufficient_window
Steady angle	8748	8074	1.26%	1.25%	1.14	1.19	no_signal
Tired angle	7886	7790	1.23%	0.90%	1.11	1.45	fatigue_candidate
Thin angle	-	-	-	-	-	-	insufficient_window
read:	A candidate is a prompt to review the ad, not a verdict. Check audience size, edits, and seasonality first.
note:	Daily-row frequency near 1.0 to 1.2 is normal. A 25% rise on that base is small in absolute terms, so confirm it with window-level frequency in Ads Manager.
```

Tired angle shows frequency up 30.6% and CTR down 26.8%. Small angle is under the impressions floor, and Thin angle is missing days, so neither gets a call.
