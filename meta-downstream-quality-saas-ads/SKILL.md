---
name: meta-downstream-quality-saas-ads
description: Judges each Meta ad or ad set in a SaaS account by paying customers and matured trial-to-paid rate instead of cheap signups, by joining the Ads Manager export with CRM or billing outcomes and running the trial_to_paid.py helper per ad. Use when someone types "which Meta ad brings real customers", "quality by creative", "cost per lead is great but sales says leads are bad", or "rank my Meta ads by paying customers". Not for campaign-level paid rates across channels; use trial-to-paid-by-campaign-saas-ads.
---

# Meta Downstream Quality Check

## Use this skill when

A Meta ad wins on cost per signup, and nobody knows whether those signups pay. This skill joins Ads Manager spend with CRM or billing outcomes. It runs the trial-to-paid helper per ad and ranks ads by paying customers. It judges only matured cohorts.

Common requests:

* "Rank my Meta ads by paying customers."
* "Which Meta ad brings real customers?"
* "Cost per lead is great but sales says leads are bad."
* "Show me quality by creative."

Send these jobs to another skill:

* Paid rate by campaign across channels: `trial-to-paid-by-campaign-saas-ads`.
* Channel-level cost per paying customer: `cost-per-paying-customer-saas-ads`.
* Frequency and CTR decay on one ad: `meta-creative-fatigue-check-saas-ads`.
* Missing or broken utm_content or fbclid capture: `utm-click-id-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

* Ads Manager export at ad level with ad name, ad set name, spend, and results for a fixed date range.
* CRM or billing export with one row per signup. It needs signup date, paid date (blank if unpaid), and the stored utm_content or ad name in a `campaign` column.
* Trial length in days and the export date.
* Written match rule between utm_content and ad name, such as exact match, lower case match, or a lookup table.

### Optional

* Ad set learning status and recent edit dates.
* Angle or theme label per ad, for grouping.
* Refund or churn flags on paid rows.

Export route:

1. In Ads Manager, open the Ads level and set a date range whose signups have all matured.
2. Add spend and results columns, then export as CSV with ad name and ad set name.
3. From the CRM or billing tool, export signups for the same dates with signup date, paid date, and the stored ad identifier.
4. Follow `../saas-ads-shared/references/getting-your-data.md` for field details.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm date range, timezone, currency, and trial length. Mark any signup younger than the T02 maturity age as immature.
2. Apply the match rule and join each signup to an ad. Report unmatched signups as a count and a share, tagged `needs_data`.
3. Run the helper with the ad name in the `campaign` column and an ad spend file whose `campaign` column holds the same ad names:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/trial_to_paid.py" "<absolute path to your CSV>" --trial-days 14 --as-of 2026-11-16 --spend "<absolute path to your spend CSV>"`
   Contract: one CSV path, `--trial-days` for trial length, `--as-of` for the export date, `--spend` for a CSV with `campaign` and `spend`. Each `campaign` value is one cohort, and the helper prints cost per signup and cost per paying customer per ad.
4. Check each ad against the T02 matured-signup floor and the T01 floor of paying customers. Group ads below a floor by angle or ad set and rerun. A group still below a floor returns `needs_data`.
5. Read cost per signup and cost per paying customer side by side from the helper. Spend must cover only dates whose signups have matured.
6. Compute the account paid rate from matched matured signups. Flag any ad or group at or below the T03 line.
7. Mark ads in ad sets still in Meta's learning phase (T06), or edited during the range, as `monitor`.
8. Sort the rest into keep, test, and review, each as `approval_needed`.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Labels follow `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Signups younger than T02 maturity | `needs_data` | Exclude, rerun after maturity |
| Ad below T02 or T01 volume | `needs_data` | Group by angle or ad set |
| Group still below T02 or T01 | `needs_data` | Widen date range |
| Paid rate at or below T03 line, meets T02 | `approval_needed` (review) | Propose budget cut for owner approval |
| Lowest cost per paying customer, meets T02, no T03 flag | `approval_needed` (keep) | Hold budget, send increases to `scale-or-hold-decision-saas-ads` |
| Strong paid rate with high signup cost | `approval_needed` (test) | Propose a variant on the same angle |
| Ad set in learning (T06) or edited in range | `monitor` | Rerun after learning ends |
| Unmatched signups could change a verdict if assigned to one ad | `needs_data` | `utm-click-id-check-saas-ads` |

## Output format

```markdown
## Meta downstream quality: [account], [currency], [timezone]
Spend range: [dates] | Trial: [days] | As of: [date] | Match rule: [rule]
Command run: [exact command]
Signups: [n] | Matched: [n] | Unmatched: [n, share] `needs_data` | Immature excluded: [n]

### Side by side
| Ad or group | Spend | Matured signups | Paid | Paid rate | Cost per signup | Cost per paying customer | T03 flag |
|---|---|---|---|---|---|---|---|
Account paid rate: [%]

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Keep, test, review (approval_needed)
[ad, action, named approver]

### Monitor
[ads below T02 or in learning (T06)]

### Data gaps
[missing exports and the verdict each would firm up]
```

## Practical example

Illustrative, made-up numbers. Trial is 14 days, export date 2026-11-16, spend range 2026-09-01 to 2026-09-30, so every signup has matured. Of 1,108 signups, 48 did not match an ad (4.3%, `needs_data`).

```text
python3 "<skill-dir>/../saas-ads-shared/scripts/trial_to_paid.py" "<absolute path to your CSV>" --trial-days 14 --as-of 2026-11-16 --spend "<absolute path to your spend CSV>"
```

| Ad | Spend (USD) | Matured signups | Paid | Paid rate | Cost per signup | Cost per paying customer |
|---|---|---|---|---|---|---|
| A | 12,000 | 600 | 20 | 3.33% | 20.00 | 600.00 |
| B | 12,000 | 300 | 36 | 12.00% | 40.00 | 333.33 |
| C | 9,600 | 160 | 24 | 15.00% | 60.00 | 400.00 |

Account paid rate is 80 of 1,060, or 7.55%. Each ad clears the T02 floor of 30 matured signups and the T01 floor of 20 paying customers. Half the account rate is 3.77% (T03), so ad A is flagged. Ad A has the cheapest signup and the most expensive paying customer.

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|
| Ad A paid rate at T03 line | `ads_export`, `billing_export` | `approval_needed` (review) | medium | medium | paying_customers | Propose budget cut to owner |
| Ad B lowest cost per paying customer | `ads_export`, `billing_export` | `approval_needed` (keep) | low | medium | paying_customers | Hold budget |
| Ad C strongest paid rate | `ads_export`, `billing_export` | `approval_needed` (test) | low | low | paying_customers | Propose a variant on C's angle |

Paid counts are small, so confidence stays medium or low.

## Common failure modes

* Ranking ads by cost per signup or Meta results alone.
* Judging ads whose signups are inside the trial and billing lag.
* Comparing single ads below T02 volume instead of grouping them.
* Hiding unmatched signups or assigning them to an ad by guess.
* Using spend from dates with immature signups, which inflates cost per paying customer.
* Reading an ad set in learning (T06) as a settled result.

## Route to next

Campaign paid rate: `trial-to-paid-by-campaign-saas-ads`. Channel cost per paying customer: `cost-per-paying-customer-saas-ads`. Ad decay: `meta-creative-fatigue-check-saas-ads`. Unmatched or missing ad identifiers: `utm-click-id-check-saas-ads`.

## Guardrails

* Never change a live account, budget, bid, tag, page, price, or form.
* Never invent numbers, matches, or paid dates. Mark gaps `needs_data`.
* End in an approval-ready recommendation with a named approver.
* Never judge an ad on immature signups or below T02 volume.
* Never fill unmatched signups by guessing the ad.
* Never use Meta results as a stand-in for paying customers.
* Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
* If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
