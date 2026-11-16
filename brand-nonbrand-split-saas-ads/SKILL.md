---
name: brand-nonbrand-split-saas-ads
description: Separates brand from non-brand search in a SaaS Google Ads account and reports cost per paying customer for each with the brand_split.py helper, so a blended number cannot hide what new demand costs. Use when someone types "brand terms are eating the budget", "brand is flattering our CAC", "split brand and non-brand", or "what does new demand really cost". Not for sorting junk search terms; use search-term-intent-filter-saas-ads.
---

# Brand vs Non-Brand Split

## Use this skill when

A blended cost per paying customer can hide expensive new demand. This skill prices brand and non_brand search separately. Brand customers are existing demand, so they cannot show what new demand costs.

Common requests:

- "Brand is flattering our CAC."
- "Brand terms are eating the budget."
- "Blended CAC looks great. Is it real?"
- "What does new demand really cost?"

Send these jobs to another skill:

- Channel cost per paying customer: `cost-per-paying-customer-saas-ads`.
- Search term intent or waste: `search-term-intent-filter-saas-ads`.
- Platform conversions versus billing: `ad-platform-vs-billing-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- `split.csv` with `segment`, `spend`, `paying_customers`. Segments read exactly `brand` or `non_brand`, and both must appear.
- Your classification. Brand covers company name, product names, and misspellings. Non_brand covers the rest, including competitor terms, which you label non_brand and say so.
- Dates, currency, timezone.
- How billing customers were tied to campaigns or terms.

### Optional

- Search terms export, brand campaign auction insights, target cost per paying customer.

Export route:

1. In Google Ads, download cost by campaign and the Search terms report for one date range.
2. From billing, export paying customers with their campaign or click ID.
3. Classify and sum into one row per segment.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Write classification rules before viewing cost, and list every competitor term placed in non_brand.
2. Check search terms for generic queries in brand campaigns and brand queries in non-brand campaigns, then reclassify. Mark `needs_data` if customers exist only per campaign.
3. Confirm each customer counts once, on matching dates and timezone.
4. Run `python3 "<skill-dir>/../saas-ads-shared/scripts/brand_split.py" "<absolute path to your CSV>"`.
5. Read each segment's volume label against T01.
6. Read the T09 verdict. On `report_split`, judge new-demand campaigns on the non_brand line.
7. Check what brand spend buys. Competitors on brand terms suggest defence. No competitors suggests paying for clicks that would come free.
8. End with an approval-ready recommendation, such as a holdout test.

## Decision rules

Thresholds sit in `../saas-ads-shared/references/thresholds.md`. Labels follow `../saas-ads-shared/references/output-standard.md`.

Script contract: one argument, the CSV path. Columns are `segment`, `spend`, `paying_customers`, and money may carry commas and a currency symbol. Segments must read exactly `brand` or `non_brand`, and both are required. Invalid rows exit with code 2. Output gives cost per paying customer, shares, a T01 volume label per segment, and `T09_verdict` (`report_split` or `blend_acceptable`).

| Signal | Verdict | Next step |
|---|---|---|
| `report_split`, brand holds the T09 share | `confirmed` blend flatters | Judge new demand on non_brand |
| Brand holds 50% of customers, or non-brand costs 1.5 times the blend, and non_brand meets T01 (T23) | `confirmed` results rest on brand demand | Hold scaling, `scale-or-hold-decision-saas-ads` |
| `blend_acceptable` | `monitor` | Still show both lines |
| Segment below T01 | `needs_data` | Arithmetic only, widen dates or use T24, and never pool brand with non-brand |
| Competitor terms in brand | `possible` misclassified | Move to non_brand, rerun |
| Brand queries in non-brand campaigns | `likely` non_brand flattered | `search-term-intent-filter-saas-ads` |
| Competitors bid on brand terms | `possible` defence | Keep brand unchanged |
| No competitor presence | `possible` paying for free clicks | Holdout test plan, `approval_needed`, never a pause |
| Non_brand above target | `hold` scaling | `payback-period-check-saas-ads` |

## Output format

```markdown
## Brand vs non-brand split: [account], [dates], [currency], [timezone]
Customer tie: [method] | Competitor terms in non_brand: [list]
Command run: [command]

| Segment | Spend | Paying | Cost per paying | Spend share | Paying share | Volume |
|---|---|---|---|---|---|---|
T09 verdict: [label]

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

Approval-ready recommendation: [action, approver, prerequisite]
Data gaps: [missing input, verdict it would firm up]
```

## Practical example

Illustrative numbers from the synthetic sample `examples/data/brand_split.csv`.

```text
python3 "<skill-dir>/../saas-ads-shared/scripts/brand_split.py" "<absolute path to your CSV>"
segment	spend	paying	cost_per_paying	share_of_spend	share_of_paying	volume
brand	1800.00	45	40.00	10.0%	41.3%	ok
non_brand	16200.00	64	253.12	90.0%	58.7%	ok
blended	18000.00	109	165.14	100.0%	100.0%	-
T09_verdict:	report_split
read:	Brand demand already exists. Judge new-demand campaigns on the non_brand line.
```

Brand costs 40.00 per paying customer. Non_brand costs 253.12, which is 1.53 times the blended 165.14. Brand holds 41.3% of paying customers, above the 40% T09 share, so `report_split` applies. Non_brand cost is above 1.5 times the blend and meets T01, so under T23 results rest on brand demand. Both segments clear the T01 floor of 20. Judge non-brand campaigns at 253.12. Auction insights were missing, so what brand spend buys stays `needs_data`.

## Common failure modes

- Quoting the blend as the cost of new demand.
- Counting competitor terms as brand.
- Skipping the leakage check.
- Calling brand customers worthless.
- Treating an `insufficient_volume` line as a finding.

## Route to next

Channel cost: `cost-per-paying-customer-saas-ads`. Term intent: `search-term-intent-filter-saas-ads`. Budget decision: `scale-or-hold-decision-saas-ads`. Gross-margin payback: `payback-period-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers.
- End in an approval-ready recommendation.
- Never recommend pausing brand from this data alone.
- Always list competitor terms as non_brand.
- Never quote the blend without both segment lines.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
