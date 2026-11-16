---
name: ad-platform-vs-billing-check-saas-ads
description: Compares conversions each ad platform reports with billing-confirmed paying customers per source for a SaaS account, using the reconcile.py helper, and lists the likeliest reasons for each gap in order. Use when someone types "Google Ads shows 62 but Stripe shows 41", "platform says 8 dollars per signup but finance disagrees", "which number do I trust", or "reported conversions do not match customers". Not for duplicate Meta events; use meta-pixel-capi-check-saas-ads.
---

# Ad Platform vs Billing Check

## Use this skill when

Platform conversions and billing customers disagree, or a platform cost per signup disagrees with finance. You need to know which gap is real before any bid, budget, or reporting decision. This skill matches definitions first, applies T04 per source, and orders likely reasons. T04 is a triage signal only. Once the counts agree, route the cost view to `cost-per-paying-customer-saas-ads`.

Common requests:

- "Google Ads shows 62 but Stripe shows 41."
- "Platform says 8 dollars per signup but finance disagrees."
- "Which number do I trust for the monthly report?"
- "Reported conversions do not match customers."
- "Total looks fine, but finance says one channel is off."

Send these jobs to another skill:

- Cost per paying customer by channel: `cost-per-paying-customer-saas-ads`.
- Paid rate by campaign: `trial-to-paid-by-campaign-saas-ads`.
- Event setup review with no count question: `signup-event-audit-saas-ads`.
- Offline paid event upload faults: `paid-event-import-check-saas-ads`.
- Budget decisions: `scale-or-hold-decision-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- CSV with columns `source`, `platform_reported`, `billing_count`, one row per source, same dates on both sides.
- Platform conversion definition: which action or event counts, and its count setting where one exists.
- Attribution window and model per platform.
- Timezone and currency for each ad account and for billing.
- Billing export of paying customers with the stored acquisition source.

### Optional

- Share of paid signups carrying a stored click ID.
- Weekly event and click counts for two comparable windows.
- GA4 paid sessions and ad clicks for the same dates.
- Signup date and first payment date per customer.

Export route:

1. In Google Ads, open the campaign report and segment the Conversions column by conversion action.
2. In Meta Ads Manager, add a results column per event and note the attribution setting.
3. From billing, export paying customers for the same dates with the stored source field.
4. Sum each side by source into `recon.csv`.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Match dates. Convert both sides to one timezone and print the window.
2. Match the definition. Confirm whether the platform action records a payment, a signup, or a trial start.
3. Match attribution. Record window and model per platform, and which date billing uses for each customer.
4. If any match fails, stop. Report the mismatch as the explanation and request matched exports.
5. Run `python3 "<skill-dir>/../saas-ads-shared/scripts/reconcile.py" "<absolute path to your CSV>"`.
6. Read each source label. Never use the `all_sources` row as a verdict, since sources can offset.
7. For `platform_over`, test in order: non-payment events counted, view-through or cross-device credit, then double counting (T13).
8. For `platform_under`, test in order: billing source not carried (T11), tracking drop (T12), delayed payments, then consent loss (T14).
9. Fill the decision table with one approval-ready next step per source.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Labels follow `../saas-ads-shared/references/output-standard.md`.

Script contract: one argument, the CSV path. It needs columns `source`, `platform_reported`, `billing_count`, and counts may carry thousands commas. A blank or NaN value exits with code 2. It prints each source plus `all_sources`, with `platform_to_billing` and `T04_label`.

| `T04_label` | Meaning | Verdict | Next step |
|---|---|---|---|
| `platform_over` | Ratio above T04 band | `possible` until a reason is shown | Work the over list |
| `platform_under` | Ratio below T04 band | `possible` until a reason is shown | Work the under list |
| `within_band` | Inside T04 band | `monitor` | Re-run next period |
| `needs_data` | `billing_count` is zero, ratio prints `n/a` | `needs_data` | Confirm billing stores this source |
| `no_activity` | Both counts zero | `monitor` | Confirm the source ran in the window |

| Pattern | Area | Verdict without direct evidence | Next step |
|---|---|---|---|
| Dates, timezone, definition, or window differ | Match failure | `confirmed` once both settings are shown | Re-export matched data |
| Counted action is a signup or trial start | Event definition | `likely` | `signup-event-audit-saas-ads` |
| View-through or cross-device credit | Attribution | `possible` | `attribution-window-fit-saas-ads` |
| Browser plus server count meets T13 | Duplicates | `possible` | `meta-pixel-capi-check-saas-ads` |
| Click ID capture meets T11 | Source loss | `possible` | `utm-click-id-check-saas-ads` |
| Event and click pattern meets T12 | Tracking drop | `possible` | `paid-event-import-check-saas-ads` |
| Payments land after the window | Lag | `possible` | `attribution-window-fit-saas-ads` |
| Session and click pattern meets T14 | Consent | `possible` | `consent-signal-loss-check-saas-ads` |
| Total within band, sources outside | Offset | `confirmed` as arithmetic | Report every source row |

A ratio is arithmetic and can be `confirmed`. A cause needs a setting capture, export, or dated change.

## Output format

```markdown
## Platform vs billing: [account], [dates], [timezone], [currency]
Match check: dates [yes/no] | timezone [yes/no] | definition [yes/no] | window [yes/no]
Command run: [exact command]

### Reconciliation
| Source | Platform | Billing | Ratio | T04 label |
|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Offsets hidden in the total
[sources whose gaps cancel in all_sources]

### Approval-ready recommendation
[action, owner, prerequisite]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative sample from `examples/data/platform_vs_billing.csv`. All numbers are synthetic.

```text
source	platform_reported	billing_count	platform_to_billing	T04_label
google_ads	62	41	1.51	platform_over
meta_prospecting	30	36	0.83	within_band
meta_retargeting	20	40	0.50	platform_under
all_sources	112	117	0.96	within_band
```

Google Ads reports 21 more conversions than billing (62 against 41). Meta retargeting reports 20 fewer (20 against 40). Meta prospecting reports 6 fewer and stays within band. Net difference is 21 minus 20 minus 6, which is minus 5, so `all_sources` reads 0.96.

Reading only that total would call both platforms accurate. Google Ads goes to the definition check first. If its counted action is a trial start, that finding is `likely`. Meta retargeting goes to T11 capture first, then T12. Both rows stay `possible` until settings and capture rates arrive.

## Common failure modes

- Trusting the `all_sources` row when source rows sit outside the band.
- Running the ratio before dates, timezone, definition, and window match.
- Treating platform conversions as paying customers.
- Calling tracking broken from the ratio alone.
- Treating `platform_under` as fine because billing looks higher.
- Comparing a billing export by signup date with a platform export by click date.

## Route to next

Click ID or source loss: `utm-click-id-check-saas-ads`. Event definition: `signup-event-audit-saas-ads`. Offline paid import: `paid-event-import-check-saas-ads`. Window or lag: `attribution-window-fit-saas-ads`. Consent: `consent-signal-loss-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, settings, or customer counts. Missing inputs stay `needs_data`.
- End in an approval-ready recommendation for a named human decision.
- Never average or net a source label away in the total.
- Never declare either side correct before the four match checks pass.
- Hold bid or budget recommendations while any source sits outside the T04 band without a shown reason.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
