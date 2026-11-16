---
name: payback-period-check-saas-ads
description: Calculates how many months of gross margin repay one SaaS customer's acquisition cost, with and without churn and with an annual-contract branch, using the cac_recovery.py helper, then labels the result against T05. Use when someone asks "is our CAC payback too long", "what is payback with 4% churn", "does this channel ever pay back", or "payback on annual contracts". Not for budget go or no-go calls; use scale-or-hold-decision-saas-ads.
---

# Payback Period Check

## Use this skill when

A channel has a cost per paying customer, and someone needs to know how long gross margin takes to repay it. This skill computes simple payback, lifetime gross margin per account, and churn-adjusted payback, then applies T05. It never uses revenue in place of gross margin.

Common requests:

- "Is our CAC payback too long?"
- "Payback on annual contracts worth 6000 a year."
- "What is payback with 4% monthly churn?"
- "Does this channel ever pay back?"
- "Finance wants payback by channel before the budget meeting."

Send these jobs to another skill:

- Building the cost per paying customer: `cost-per-paying-customer-saas-ads`.
- Deciding a budget step: `scale-or-hold-decision-saas-ads`.
- Platform counts versus billing counts: `ad-platform-vs-billing-check-saas-ads`.
- Trial cohorts that have not matured: `trial-to-paid-by-campaign-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Cost per paying customer per channel, from `cost-per-paying-customer-saas-ads`, with its window and new paying customer count.
- Average monthly revenue per account (ARPA) for those same customers, in one currency.
- Gross margin as a fraction, with its finance source and date. A guessed margin is `needs_data`.
- Plan mix those customers bought: plan names, billing interval, and counts.

### Optional

- Monthly churn as a fraction, measured on paying accounts. Per source, a CSV with columns `source`, `monthly_churn`, and an optional `cac` (see `../saas-ads-shared/references/getting-your-data.md`).
- Annual prepay share and discount.
- For annual contracts: annual contract value (ACV) per account, and annual churn as the share of accounts that do not renew.

Export route:

1. In the billing tool, export new paying customers for the window with plan, billing interval, and monthly recurring revenue.
2. Divide that revenue by the account count to get ARPA.
3. Ask finance for gross margin and its calculation date.
4. Export churned paying accounts by month to get monthly churn.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Check that the channel CAC meets T01. Below its floor, payback returns `needs_data` and the arithmetic is shown only.
2. Use the channel CAC when channels differ. A blended CAC can hide a channel that never pays back.
3. Confirm ARPA or ACV comes from the same customers as the CAC. Pick the branch: monthly plans use `--arpa`, annual contracts use `--acv`, and the helper divides ACV by 12 and prints `arpa_from_acv`.
4. Run the helper. Monthly plans:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/cac_recovery.py" --cac 480 --arpa 79 --gross-margin 0.8 --monthly-churn 0.04`
   Annual contracts:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/cac_recovery.py" --cac 4500 --acv 6000 --gross-margin 0.8 --annual-churn 0.2`
   Payback per source, when channels churn differently:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/cac_recovery.py" --arpa 79 --gross-margin 0.8 --churn-by-source "<absolute path to your churn CSV>"`
5. Read simple payback: CAC divided by monthly gross margin per account, which is ARPA times gross margin.
6. Read churn-adjusted payback. Margin arrives only from accounts still paying, so this figure is longer. Lifetime gross margin equals monthly margin divided by churn. When CAC exceeds it, payback is `never`. For annual contracts the helper turns annual churn into an equivalent monthly rate, which is conservative because an annual contract cannot churn mid-term.
7. Apply T05 to the churn-adjusted figure. Without churn the helper prints `T05_verdict: needs_churn`. Return `needs_data`, report simple payback as a lower bound, and request churn. If simple payback already passes the T05 hold line, the verdict is `hold`.
8. Read the T21 lines. `T21_affordable_cost_12m` is the cost per paying customer that gross margin repays in 12 months, the central figure, and `T21_affordable_cost_18m` is the ceiling. With `--churn-by-source` the helper prints payback and the 12-month figure per source, and a source with no churn row gets `needs_churn`, never a guess.
9. If the plan mix includes annual prepay, state the cash timing as a separate note: cash arrives at signing, before the monthly view shows it. Do not recompute payback silently.
10. Fill the decision table and route any scale question to `scale-or-hold-decision-saas-ads`. Pass the per-source payback to that skill, since it reads one value per channel.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Labels follow `../saas-ads-shared/references/output-standard.md`.

Script contract: every input must be finite and above zero, gross margin at most 1 (a percent such as `80%` is accepted), and churn from 0 up to but not including 1. Money may carry commas and a currency symbol. Anything else exits with code 2. Exactly one of `--arpa` or `--acv` is required, and one of `--monthly-churn`, `--annual-churn`, or `--churn-by-source` is optional. Without churn it prints simple payback, `churn_adjusted_payback_months: n/a`, and `T05_verdict: needs_churn`. `--churn-by-source` takes a CSV with `source`, `monthly_churn`, and optional `cac`, and prints one row per source with `T05_verdict`.

| Pattern | Verdict | Next step |
|---|---|---|
| `T05_verdict: ok` | `monitor` | Pass to `scale-or-hold-decision-saas-ads` for its other gates |
| `T05_verdict: review`, beyond the T05 review line | `monitor`, channel under review | Check plan mix and price: `pricing-page-review-saas-ads` |
| `T05_verdict: hold_scale`, beyond the T05 hold line or `never` | `hold` | Block scale steps until CAC, ARPA, or churn improves |
| CAC below the T01 floor | `needs_data` | Widen the window in `cost-per-paying-customer-saas-ads` |
| Margin guessed, or revenue used as margin | `needs_data` | Request the finance figure |
| `T05_verdict: needs_churn`, no churn supplied | `needs_data`, simple payback is a lower bound | Request churn, or `hold` if simple payback already passes the T05 hold line |
| One source `review` or `hold_scale` while the blend is `ok` | `likely` that the blend hides a channel to cut or fix | Pass that source's value to `scale-or-hold-decision-saas-ads` |
| Long payback on a channel bidding on signups | `possible` | `bid-target-picker-saas-ads` |
| Annual prepay in plan mix | `confirmed` arithmetic, cash note added | State cash timing separately |
| Annual contracts, ACV supplied | `confirmed` arithmetic from `--acv`, conservative on churn | Report the annual-churn conversion beside the result |

Arithmetic from supplied inputs is `confirmed`. A cause of long payback needs evidence, otherwise it stays `possible` or `likely`.

## Output format

```markdown
## Payback check: [channel], [currency]
Window: [dates] | New paying customers: [n] | T01: [meets / insufficient_volume]
Plan mix: [plans, monthly vs annual counts]
Gross margin source: [finance document, date] | Churn source: [billing export, months]
Command run: [exact command]

### Result
| Metric | Value | Evidence tag |
|---|---|---|
| CAC | | |
| ARPA | | |
| Monthly gross margin per account | | |
| Simple payback (months) | | |
| Lifetime gross margin per account | | |
| Churn-adjusted payback (months) | | |
| T05 label | | |

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Cash timing note
[annual prepay share and its effect on cash timing, no recomputed payback]

### Data gaps
[missing input, assumption used, verdict it would firm up]

### Recommendation
[approval-ready action with named approver, or hold with prerequisite]
```

## Practical example

Illustrative numbers, made up for this example. One channel on monthly plans has CAC 480, ARPA 79 per month, gross margin 0.8, and monthly churn 0.04.

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

Monthly margin is 79 times 0.8, which is 63.20. Simple payback is 480 divided by 63.20, about 7.6 months. Lifetime margin is 63.20 divided by 0.04, which is 1580.00. Churn stretches payback to 8.9 months, inside the T05 review line. Verdict: `monitor`, then route to `scale-or-hold-decision-saas-ads`.

A second run with `--cac 2000` and the same other inputs prints `churn_adjusted_payback_months: never` and `T05_verdict: hold_scale`. Lifetime margin per account is 1580.00, below the 2000 cost. Simple payback alone would read about 31.6 months and hide that the channel never repays. Verdict: `hold`.

A third run uses annual contracts, with CAC 4500, ACV 6000, gross margin 0.8, and annual churn 0.2.

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

Churn-adjusted payback of 12.5 months passes the 12 month T05 review line, so the channel goes under review. It does not pass the 18 month hold line. Cash for annual prepay arrives at signing, so state that timing separately.

Run with `--cac 480 --arpa 79 --gross-margin 0.8` and no churn, the helper prints `T05_verdict: needs_churn`. Simple payback of 7.6 months is a lower bound, so the result is `needs_data` until churn arrives.

A fourth run reads churn per source from the synthetic sample `examples/data/churn_by_source.csv`, with ARPA 79 and gross margin 80%.

```text
monthly_gross_margin_per_account:	63.20
source	cac	monthly_churn	simple_payback_months	churn_adjusted_payback_months	T21_affordable_cost_12m	T05_verdict
google_search_nonbrand	300.00	0.0300	4.7	5.0	644.97	ok
meta_prospecting	500.00	0.0900	7.9	13.2	475.77	review
meta_retargeting	55.00	n/a	0.9	n/a	n/a	needs_churn
excludes:	expansion revenue, annual prepay cash timing
read:	Payback per source uses that source's churn and this gross margin. A source with no churn row cannot be judged.
```

Simple payback of 7.9 months would pass Meta prospecting. Its 9% monthly churn stretches payback to 13.2 months, past the 12 month review line, and its CAC of 500.00 sits above the 475.77 it can afford in 12 months. Google non-brand pays back in 5.0 months. Meta retargeting has no churn row, so it returns `needs_data`. A blended payback would hide all three differences.

## Common failure modes

- Dividing CAC by revenue instead of gross margin.
- Reporting simple payback as final when churn data exists.
- Using a blended CAC when channels differ.
- Pairing ARPA from all customers with a channel CAC.
- Recomputing payback for annual prepay without saying so.
- Treating platform-reported conversions as paying customers inside CAC.
- Reading `ok` as approval to scale. T05 is one gate among several.

## Route to next

CAC inputs: `cost-per-paying-customer-saas-ads`. Budget decision: `scale-or-hold-decision-saas-ads`. Bid event depth: `bid-target-picker-saas-ads`. Price and plan mix: `pricing-page-review-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers. Missing inputs become `needs_data`.
- End in an approval-ready recommendation, labelled `approval_needed` or `hold`.
- Never compute payback from revenue, and never accept a guessed gross margin.
- Never present a blended payback as a channel result.
- Never adjust payback for annual prepay silently. State cash timing as a separate note.
- Never report payback as a finding when CAC sits below the T01 floor.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
