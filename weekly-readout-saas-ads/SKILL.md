---
name: weekly-readout-saas-ads
description: Writes a weekly paid-ads readout for a SaaS team or client in business language, covering paying customers, cost per paying customer, matured trial-to-paid, spend, tracking health, account changes, up to three owned actions, and data gaps. Use when someone types "write the weekly report", "client update for Monday", "what do I tell the founder about ads", or "summarize last week's paid". Not for a deep cost split by campaign; use cost-per-paying-customer-saas-ads.
---

# Weekly SaaS Ads Readout

## Use this skill when

A founder, team, or client needs a short weekly answer about paid ads. This skill leads with paying customers and their cost, labels thin numbers, and ends with at most three owned actions.

Common requests:

- "Write the weekly report for Google and Meta."
- "Client update for Monday, keep it short."
- "What do I tell the founder about ads this week?"
- "Summarize last week's paid in plain words."

Send these jobs to another skill:

- Deep cost per paying customer split by campaign: `cost-per-paying-customer-saas-ads`.
- Cohort paid rates by campaign: `trial-to-paid-by-campaign-saas-ads`.
- Platform counts disagree with billing: `ad-platform-vs-billing-check-saas-ads`.
- Deciding whether to raise budget: `scale-or-hold-decision-saas-ads`.

## Required input

Work from pasted exports and screenshots; no live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Week dates, comparison week dates, timezone, currency.
- Google Ads and Meta Ads export by campaign: cost, clicks, platform conversions.
- Billing export of new paying customers with source, signup date, first payment date.
- CRM signups with source and campaign.
- Change log for the week.
- Goal for cost per paying customer or payback.

### Optional

- Tracking notes or screenshots of conversion diagnostics.
- Trial length and gross margin.

Export route:

1. Google Ads: open Campaigns, set both date ranges, download the campaign table.
2. Meta Ads Manager: open Campaigns, set the same dates, export the table.
3. Billing tool: export new paying customers for both weeks.
4. CRM: export signups with source fields.
5. Each platform's change history for the week.

See `../saas-ads-shared/references/getting-your-data.md`. For a repeatable weekly run, follow the "Monday routine" in `../saas-ads-shared/examples/copy-paste-prompts.md`: exports in a fixed order, then one prompt.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm dates, timezone, and currency match across every export. Mark any mismatched line `needs_data`.
2. Count new paying customers per platform from billing. Divide platform spend by that count. When a source fails the T01 floor, label it `insufficient_volume`, return `needs_data` for it, and default to small account mode (T24): lead with a rolling 90-day line pooled by platform and intent, and show the weekly figure only as context.
3. Compute trial-to-paid only on cohorts mature under T02. Report younger signups as an immature count.
4. Compare each line with the previous week as a value and a percent change.
5. Match each dated change log entry to the line it touched. Write "no logged change" when a moved line has no entry.
6. Write one tracking line: T12 result on the primary signup event, plus T04 per platform when dates and definitions match.
7. Pick at most three actions, each with an owner, a due date, and the approval it needs.
8. List data gaps and the line each gap blocks.
9. Replace terms the reader has not used with plain descriptions.

## Decision rules

Threshold values live in `../saas-ads-shared/references/thresholds.md`.

| Pattern | Verdict | Readout wording | Next step |
|---|---|---|---|
| Source meets T01 floor | `confirmed` for the count | Report cost per paying customer | `cost-per-paying-customer-saas-ads` for detail |
| Source below T01 floor | `needs_data` | Weekly figure as context only, lead with the T24 pooled line | Pool per T24, widen the window |
| Signups younger than T02 maturity | `needs_data` | Immature count, excluded from rate | `trial-to-paid-by-campaign-saas-ads` later |
| T12 pattern met | `possible` | "Tracking under review" | `signup-event-audit-saas-ads` |
| T04 ratio outside range, inputs matched | `possible` | "Platform and billing disagree" | `ad-platform-vs-billing-check-saas-ads` |
| T04 inputs unmatched | `needs_data` | No ratio printed | Request matched exports |
| Line moved, dated edit in that line | `possible` | Name the edit | Watch next week |
| Reader wants more budget | `hold` | No scaling call here | `scale-or-hold-decision-saas-ads` |
| Only platform ROAS supplied | `needs_data` | Shown as platform-reported only | Request billing export |

## Output format

Labels follow `../saas-ads-shared/references/output-standard.md`.

```markdown
## Weekly paid ads readout: [account], [week], [currency], [timezone]
Compared with: [previous week dates]

### Scorecard
| Line | This week | Last week | Change | Source and label |
|---|---|---|---|---|

### Tracking health
[one line: T12 result, T04 per platform or needs_data]

### What changed
[dated change log entries and the line each touched]

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Actions (max three)
| # | Action | Owner | Due | Approval needed |
|---|---|---|---|---|

### Data gaps
[missing input and the line it blocks]
```

## Practical example

Illustrative only: every number below is made up.

| Line | This week | Last week | Change | Source and label |
|---|---|---|---|---|
| Paying customers, total | 40 | 30 | +33.3% | `billing_export` |
| Google Ads | 30 | 22 | +8 | meets T01 |
| Meta Ads | 10 | 8 | +2 | `insufficient_volume`, context only |
| Meta Ads, rolling 90 days (pooled, T24) | 34 | n/a | n/a | meets T01 |
| Cost per paying customer, total | 250.00 | 300.00 | -16.7% | |
| Google Ads | 200.00 | 250.00 | -20.0% | |
| Meta Ads | 400.00 | 437.50 | context only | `needs_data` this week |
| Meta Ads, rolling 90 days (pooled, T24) | 411.76 | n/a | n/a | 14,000 spend over 34 customers |
| Matured trial-to-paid | 12.0% (48/400) | 11.0% (44/400) | +1.0 pt | T02 cohorts |
| Spend | 10,000 | 9,000 | +11.1% | Google 6,000, Meta 4,000 |

Tracking health: T12 not met. Google reported 34 against 30 billed (1.13). Meta reported 16 against 10 billed (1.60), outside T04: `possible`.

What changed: Tuesday, Google non-brand budget went from 400 to 460 per day. Thursday, two new Meta ads launched.

| # | Action | Owner | Due | Approval needed |
|---|---|---|---|---|
| 1 | Run Meta platform vs billing check | Tracking lead | Wed | None, analysis only |
| 2 | Hold Meta budget until action 1 reports | Paid media manager | Fri | Founder sign-off |
| 3 | Bring Google non-brand to scale or hold review | Head of growth | Two weeks | Founder, before any budget change |

Data gaps: gross margin missing, so payback is `needs_data`. CRM lacks a campaign field, so signups by campaign are `needs_data`.

## Common failure modes

- Leading with spend or clicks when the reader asked about customers.
- Copying platform ROAS or platform conversions into the scorecard as results.
- Printing a thin cost per paying customer without the T01 label.
- Leading with a weekly figure that fails T01 instead of the T24 line.
- Counting this week's trials in trial-to-paid (T02).
- Explaining a move when the change log is silent.
- Listing more than three actions, or actions with no owner.

## Route to next

Cost detail: `cost-per-paying-customer-saas-ads`. Cohort rates: `trial-to-paid-by-campaign-saas-ads`. Count disagreement: `ad-platform-vs-billing-check-saas-ads`. Budget decision: `scale-or-hold-decision-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers; a missing figure becomes `needs_data`.
- End in an approval-ready recommendation with a named approver.
- Never present platform ROAS or platform conversions as paying customers or revenue.
- Never add a fourth action or an action without owner, date, and approval.
- Never fill a data gap with an estimate to make the week look complete.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
