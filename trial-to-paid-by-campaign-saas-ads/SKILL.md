---
name: trial-to-paid-by-campaign-saas-ads
description: Computes the SaaS trial-to-paid rate for each Google Ads and Meta Ads campaign from a CRM or billing signup export, counting only signups old enough to have converted, and prints cost per signup and cost per paying customer per campaign when spend is supplied, with the trial_to_paid.py helper. Use when someone types "which campaign brings trials that pay", "cheap signups but nobody pays", "trial to paid by campaign", or "are these signups just tire kickers". Not for channel-level cost per customer; use cost-per-paying-customer-saas-ads.
---

# Trial To Paid By Campaign

## Use this skill when

A campaign looks cheap per signup, and the buyer needs to know whether those signups pay. This skill counts only matured signups (T02), compares campaigns above the T02 volume floor, and flags weak paid rates by T03. It reports rates and never decides a pause.

Common requests:

- "Which campaign brings trials that pay?"
- "Cheap signups but nobody pays. Which source?"
- "Trial to paid by campaign for last quarter."
- "Are these Meta signups just tire kickers?"

Send these jobs to another skill:

- Cost per paying customer by channel: `cost-per-paying-customer-saas-ads`.
- Platform conversions versus billing counts: `ad-platform-vs-billing-check-saas-ads`.
- Missing UTM campaign values on signups: `utm-click-id-check-saas-ads`.
- Months to recover acquisition cost: `payback-period-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- CSV with columns `campaign`, `signup_date`, `paid_date`, one row per signup, ISO dates. Leave `paid_date` blank when the signup never paid.
- Campaign names that match the UTM campaign stored on each signup.
- Trial length in days.
- Export date, passed as `--as-of`.
- Billing lag in days. Script default follows T02; supply a longer value when billing confirms payment later.

### Optional

- Spend per campaign for the same signup dates, as a CSV with columns `campaign`, `spend`, passed as `--spend`. It adds cost per signup and cost per paying customer per campaign.
- Plan, offer, or trial type per signup.
- Dated notes on launches, audience edits, or offer changes.
- A founder on Stripe with no CRM: the Stripe Customers and Payments CSV exports, joined by `stripe_join.py` into the three-column file (step 3).

Export route:

1. Open the signup or customer list in the CRM or billing tool.
2. Filter to signups created in the review window and include the stored UTM campaign field.
3. Add the first paid date from billing. A payment processor date beats a CRM stage when they disagree.
4. Export as CSV and rename columns to `campaign`, `signup_date`, `paid_date`.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Record trial length, export date, billing lag, and the timezone of the date fields in the output header.
2. Check campaign names against the ad platform export. Merge spelling variants only after the user confirms them. List unmatched names as `needs_data`.
3. Run the helper:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/trial_to_paid.py" "<absolute path to your CSV>" --trial-days <days> --as-of <YYYY-MM-DD> --spend "<absolute path to your spend CSV>"`
   Add `--billing-lag-days <days>` when billing confirms later than the default. Drop `--spend` when no spend was supplied. Dates may be `YYYY-MM-DD`, `YYYY-MM-DD HH:MM[:SS]`, or use a `T` separator; `MM/DD/YYYY` needs `--us-dates`.
   When the only source is Stripe, build the CSV first:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/stripe_join.py" "<absolute path to your Stripe customers CSV>" "<absolute path to your Stripe payments CSV>" --campaign-field <metadata header> --out "<absolute path to your joined CSV>"`
   A blank campaign becomes `unattributed`. If Stripe stores no campaign at all, stop: read the "No campaign stored in Stripe yet" section of `../saas-ads-shared/references/getting-your-data.md`, and report blended cost per paying customer instead of a per-campaign paid rate.
4. Read the maturity rule line. Signups younger than trial length plus billing lag are immature and excluded from both matured and paid counts (T02).
5. Read each label. `insufficient_volume` sits below the T02 floor and means `needs_data` for any ranking: show that rate as arithmetic only. For a small account, rerun with `--window-days 90` and `--pool name=campaign_a,campaign_b` (T24) for campaigns of the same platform and intent. A pooled row at or above the T02 floor is labelled `pooled`, and it cannot be split back out.
6. Compare `ok` and `weak_paid_rate` rows with the account row. A `weak_paid_rate` label applies T03.
7. Read `median_days_to_paid` to set the next review date. A median close to the maturity age suggests late payers may still arrive.
8. For each weak campaign, list checks for ad promise, audience, offer, landing page, and trial path, each routed to its skill.
9. When `--spend` was used, read the second table. Spend must cover only the signup dates counted as matured, which the `spend_rule` line states. A campaign with fewer than 20 paying customers carries the `insufficient_volume` label (T01), so its cost per paying customer returns `needs_data`. Its account row can still stand when it meets T01.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Verdicts and tags follow `../saas-ads-shared/references/output-standard.md`.

Script contract: arguments are the CSV path, `--trial-days`, `--as-of`, optional `--billing-lag-days`, optional `--spend` (CSV with `campaign`, `spend`), and for small accounts `--pool` (repeatable) and `--window-days`. Headers are case-insensitive, and a comma or semicolon delimiter is detected. A future signup date, a paid date before signup, or a paid date after the export date exits with code 2, and so does a campaign missing from the spend file, a pool that mixes brand with non-brand, or a pool that crosses platforms. Output prints per campaign `signups`, `matured`, `immature`, `paid`, `paid_rate`, `median_days_to_paid`, `label`, then an account row and the maturity rule. Labels are `ok`, `weak_paid_rate`, `pooled`, and `insufficient_volume`, which means `needs_data`. With `--spend` it adds a second table with `spend`, `matured`, `paid`, `cost_per_signup`, `cost_per_paying`, `T01_label` and a `spend_rule` line.

A blank campaign is read as `unattributed`. Its line is labeled `unattributed`, is never ranked, and needs no row in the spend file. When unattributed paying customers reach 10% of all paying customers the helper prints a T26 line, and per-campaign comparisons are provisional. A spend file that writes decimals with a comma ("1.200,50") needs `--decimal-comma`; a semicolon file with such a cell turns it on by itself.

| Pattern | Verdict | Next step |
|---|---|---|
| Label `ok` or `pooled` | `monitor` | Re-run when the next cohort matures |
| Label `weak_paid_rate` (T03) | `likely` weak paid rate, cause unknown | Check promise, audience, offer, page |
| Low cost per signup but high cost per paying customer (needs `--spend`) | `likely` cheap signups that do not pay, when the campaign meets T01 | Check promise, audience, offer, page |
| Label `insufficient_volume` (T02) | `needs_data` | Widen the window or wait for maturity |
| Most signups immature | `needs_data` | Re-run after median days to paid has passed |
| Script exit code 2 | `needs_data` | Fix the flagged dates in the export |
| Names do not match UTM values | `needs_data` | `utm-click-id-check-saas-ads` |

| Evidence beside a weak campaign | Area to test | Next step |
|---|---|---|
| Meta weak, search fine | Audience and event quality | `meta-downstream-quality-saas-ads` |
| Ad claim differs from page or plan | Ad promise | `ad-to-page-promise-match-saas-ads` |
| Signups stall before first product use | Trial path | `trial-or-demo-path-check-saas-ads` |
| Every campaign low | Funnel stage | `funnel-bottleneck-finder-saas-ads` |

Rates computed from `billing_export` are `confirmed` arithmetic. A cause stays `possible` until a dated change, page capture, or segment export supports it.

## Output format

```markdown
## Trial to paid: [account], as of [date], [timezone]
Trial length: [days] | Billing lag: [days] | Source: [billing_export or crm_export]
Command run: [exact command]

### Campaign paid rates
| Campaign | Signups | Matured | Immature | Paid | Paid rate | Median days to paid | Label |
|---|---|---|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Immature cohort
[count per campaign, date each cohort matures]

### Checks for weak campaigns
[promise, audience, offer, page, trial path, with routed skill]

### Data gaps
[unmatched names, missing lag, missing spend, verdict each would firm up]

### Approval-ready recommendation
[one action, owner, prerequisite]
```

## Practical example

Illustrative numbers from the synthetic sample `examples/data/trial_to_paid.csv`, with a 14 day trial. Nothing here describes a real account.

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

Meta lookalike paid 4 of 40 matured signups, 10.0%. Account rate is 34 of 130, 26.2%. Half of that is 13.1%, so T03 flags meta_lookalike. Each campaign has at least 30 matured signups, so T02 allows comparison of paid rates. Eight young signups are excluded as immature, never counted as failures. Meta lookalike is cheapest per signup after brand search (70.00) yet costs 700.00 per paying customer. Each campaign has fewer than 20 paying customers, so those cost lines return `needs_data` under T01. Only the account row of 302.94 is firm.

Finding: meta_lookalike weak paid rate, `billing_export`, `likely`, high severity, medium confidence, `paying_customers`. Its median of 16 days sits near the 21 day maturity age, so a later re-run may add payers. Cause is `needs_data`. Recommendation for approval: run `meta-downstream-quality-saas-ads` and `ad-to-page-promise-match-saas-ads`, holding budget edits until then.

## Common failure modes

- Counting immature signups as unpaid, which drags down new campaigns.
- Comparing campaigns below the T02 floor.
- Reading `weak_paid_rate` as an instruction to pause.
- Using platform conversions in place of billing paid dates.
- Merging campaign names without user confirmation.
- Setting the next review date without reading median days to paid.

## Route to next

Cost per paying customer: `cost-per-paying-customer-saas-ads`. Meta signup quality: `meta-downstream-quality-saas-ads`. Ad promise: `ad-to-page-promise-match-saas-ads`. Funnel stage: `funnel-bottleneck-finder-saas-ads`. Trial path: `trial-or-demo-path-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, paid dates, or campaign mappings.
- End every run in an approval-ready recommendation for a named human.
- Never call an immature signup a failure or include it in either count.
- Never compare campaigns below the T02 volume floor.
- Never recommend a pause from a T03 flag alone.
- Never treat platform-reported conversions as paying customers.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
