---
name: cost-per-paying-customer-saas-ads
description: Works out what a SaaS company pays for one billing-confirmed new paying customer, per ad channel and blended, with the cac.py helper and the T01 volume floor, and gives demo-led accounts a lagged-CAC path. Use when someone types "what does a customer cost us", "CAC by channel", "Google or Meta, which is cheaper per paying customer", or "lagged CAC for our demo-led account". Not for platform-versus-billing gaps; use ad-platform-vs-billing-check-saas-ads.
---

# Cost Per Paying Customer

## Use this skill when

A buyer needs the cost of one new paying customer per channel, counted from billing. This skill divides channel spend by billing-confirmed new paying customers for matching dates. It applies T01 as a volume floor and shows which channel carries the blended number.

Common requests:

- "What does a customer cost us?"
- "CAC by channel for last quarter."
- "Google or Meta, which is cheaper per paying customer?"
- "Lagged CAC for our demo-led account."

Send these jobs to another skill:

- Paid rate of trial signups by campaign: `trial-to-paid-by-campaign-saas-ads`.
- Platform and finance disagree on signups or customers: `ad-platform-vs-billing-check-saas-ads`.
- Months to recover acquisition cost: `payback-period-check-saas-ads`.
- Brand and non-brand reporting: `brand-nonbrand-split-saas-ads`.
- A budget decision: `scale-or-hold-decision-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- CSV with columns `channel`, `spend`, `new_paying_customers`. Customers are billing-confirmed new paying customers for the same dates as spend.
- Date range, currency, and whether spend includes tax.
- Count of new paying customers whose source is unknown.
- Lead path: self-serve trial, or demo-led with a sales call before payment.

### Optional

- Non-media cost such as agency fee, tools, or contractor time, passed as `--extra-cost`.
- Campaign-level split, for example brand and non-brand search.
- For a demo-led account: the click date and paid date of each paying customer (customers CSV with `click_date`, `paid_date`) and spend per month (`month`, `spend`), so customers can be grouped by click month.

Export route:

1. In Google Ads, export cost per campaign for the date range.
2. In Meta Ads Manager, export amount spent per campaign for the same dates.
3. From the payment processor, export first successful payments from new customers for the same dates.
4. Join each customer to a channel by stored UTM or by the billing tool's source field.
5. Map campaigns to channel names and build the CSV.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. State date range, currency, tax treatment, and customer definition. If spend and customer dates or currencies differ, stop with `needs_data`.
2. Confirm every customer count comes from billing. A platform conversion is never a paying customer.
3. Add unknown-source customers as an `unattributed` row with zero spend. Never spread them across channels. Its helper row prints `n/a`, since a cost has no meaning there.
4. Run the helper:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/cac.py" "<absolute path to your CSV>" --extra-cost 2400`
   Drop `--extra-cost` when no non-media cost was supplied.
5. Read each channel's cost per paying customer and its T01 label. A line labelled `insufficient_volume` returns `needs_data` under T01: show its arithmetic, and do not rank it or estimate it. When most channels fail T01, rerun in small account mode (T24): add a `date` column to the CSV, then add `--window-days 90` and `--pool name=channel_a,channel_b` for channels of the same platform and intent. A pooled line is labelled `pooled` and cannot be split back out.
6. Compare share of paying customers with share of spend. A channel carries the blend when its customer share exceeds its spend share by at least the T26 margin. Report that channel on its own line.
7. Apply T09. When brand campaigns hold the T09 share of paying customers, route to `brand-nonbrand-split-saas-ads`.
8. Apply T26 to the `unattributed` row. At or above the T26 share, per-channel lines return `needs_data` for ranking.
9. For a demo-led or sales-led account, add the lagged-CAC step. Spend in one month produces customers in later months, so same-window division misstates cost. Build a customers CSV with `click_date` and `paid_date` per paying customer and a monthly spend CSV, then run:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/lag.py" "<absolute path to your customers CSV>" --spend "<absolute path to your monthly spend CSV>" --as-of 2026-11-16`
   Report `mature_months_total` as lagged CAC beside the same-window figure. A click month younger than the 80th-percentile lag prints `immature` and returns `needs_data` (T25). A file of paying customers makes recent clicks look faster than they are (right-censoring). For that reason the percentile comes from clicks at least 90 days old (`--cohort-cutoff-days`), and the `censoring:` line says how many customers that leaves. Quote that line beside the lagged CAC.
10. Report `blended_excl_unattributed` as the headline when the helper prints it, because it leaves out customers with no known source. Show `blended_media` and the line with extra cost beside it.
11. Fill the decision table and route each open question.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`.

Script contract: inputs are the CSV path, optional `--extra-cost`, and for small accounts `--pool` (repeatable) and `--window-days`. Required columns are `channel`, `spend`, `new_paying_customers`, and several rows per channel are summed. Headers are case-insensitive, and a comma or semicolon delimiter is detected. Money may carry thousands commas, spaces, and a currency symbol or code ($ € £ zł PLN USD EUR GBP). A blank cell, `NaN`, `--`, or a European decimal comma exits with code 2, and a column error lists the headers found. Output columns are `channel`, `spend`, `paying`, `cost_per_paying`, `share_of_spend`, `share_of_paying`, `T01_label`, with `blended_media`, `blended_excl_unattributed` (only when unattributed customers exist), and `blended_with_extra_cost` lines. A channel with zero paying customers prints `n/a`, never 0. Any row with zero spend and paying customers prints `n/a` and the label `unattributed`, never 0.00.

A blank channel is read as `unattributed` and printed with `n/a` and the `unattributed` label. When unattributed customers reach 10% of all paying customers the helper prints a T26 line, and per-channel rankings are provisional. A file that writes decimals with a comma ("1.200,50") needs `--decimal-comma`; a semicolon file with such a cell turns it on by itself.

| T01 label | Meaning | Verdict | Next step |
|---|---|---|---|
| `ok` | Channel meets the T01 floor | `confirmed` as arithmetic | Compare spend share and customer share |
| `insufficient_volume` | Channel sits below the T01 floor | `needs_data`, arithmetic only | Widen the window or use T24 before comparing |
| `no_paying_customers` | Zero billing customers, cost prints `n/a` | `needs_data` | Check the source join, then billing |
| `unattributed` | Zero-spend row for customers with no known source | `needs_data` for its cost | Apply T26, then `utm-click-id-check-saas-ads` |
| `pooled` | Same-platform, same-intent channels summed under T24, at or above the T01 floor | `confirmed` as arithmetic | Report as one line; it cannot be split back out |

| Pattern | Verdict | Next step |
|---|---|---|
| Spend and customer dates or currency differ | `needs_data` | Re-export matched windows |
| Customer counts come from an ad platform | `needs_data` | Replace with billing counts |
| Platform cost per signup disagrees with billing cost per customer | `possible` | `ad-platform-vs-billing-check-saas-ads` |
| Brand holds the T09 share of paying customers | `likely` that the blend hides costlier lines | `brand-nonbrand-split-saas-ads` |
| Unattributed customers reach the T26 share | `needs_data` for per-channel lines | `utm-click-id-check-saas-ads` |
| A channel's customer share beats its spend share by the T26 margin | `confirmed` as arithmetic that it carries the blend | Report that channel on its own line |
| Demo-led account and the click month is younger than T25 allows | `needs_data` | Wait, or drop that month from the lagged line |
| Question moves to spending more | `hold` until payback is known | `payback-period-check-saas-ads`, then `scale-or-hold-decision-saas-ads` |

A cost per paying customer from matched billing data is `confirmed` arithmetic. Any reason one channel costs more stays `hypothesis` until evidence supports it.

## Output format

Use labels and tags from `../saas-ads-shared/references/output-standard.md`.

```markdown
## Cost per paying customer: [account], [currency], [dates], tax [included/excluded]
Customer source: [billing tool] | Join: [UTM or source field] | Unattributed: [count]
Command run: [exact command]

### Per channel
| Channel | Spend | Paying | Cost per paying | Share of spend | Share of paying | T01 label |
|---|---|---|---|---|---|---|

Blended media: [value] | Blended with extra cost: [value] | Extra cost items: [list]

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Data gaps
[missing exports or settings, and the verdict each would firm up]

### Approval-ready recommendation
[one action, its owner, and its prerequisite]
```

## Practical example

Illustrative only: numbers come from the synthetic sample `examples/data/cac_channels.csv`, with 2400 of made-up extra cost.

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

Meta prospecting has 12 paying customers, under the T01 floor of 20, so it returns `needs_data` and its 500.00 stays arithmetic. Google brand holds 45 of 109 paying customers, 41.3%, above the T09 line of 40%, on 10.0% of spend. Its customer share beats its spend share by 31.3 points, over the T26 margin of 15, so brand carries the blend. A blend of 165.14 hides a 300.00 non-brand search line. Without brand, media cost per paying customer is 16200 / 64 = 253.12. Extra cost lifts the blend to 20400 / 109 = 187.16. Recommendation: report brand separately and route to `brand-nonbrand-split-saas-ads`.

## Common failure modes

- Counting platform conversions or trial signups as paying customers.
- Printing 0 for a channel with no paying customers.
- Spreading unattributed customers across channels by spend share.
- Ranking channels on a line labelled `insufficient_volume`.
- Quoting the blended number while brand carries most customers.
- Mixing dates, currencies, or tax treatment between spend and billing.
- Quoting same-window CAC for a demo-led account whose sales cycle spans months.

## Route to next

Paid rate by campaign: `trial-to-paid-by-campaign-saas-ads`. Platform versus billing gap: `ad-platform-vs-billing-check-saas-ads`. Payback: `payback-period-check-saas-ads`. Brand blend: `brand-nonbrand-split-saas-ads`. Budget decision: `scale-or-hold-decision-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers. Missing data becomes `needs_data`.
- End in an approval-ready recommendation for a named human decision.
- Never use a platform-reported conversion as a paying customer.
- Never present an `insufficient_volume` line as a finding.
- Never present cost per paying customer as profit or payback.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
