---
name: bid-target-picker-saas-ads
description: Picks the event each Google Ads or Meta Ads campaign in a SaaS account should bid on, plus a target cost range built from affordable cost per paying customer, the T17 volume floor, and matured event-to-paid rates. Use when someone types "what should my target CPA be", "switch to paid event bidding", "tROAS or tCPA for SaaS", or "which event should Meta deliver for". Not for checking that the paid event reaches the platform; use paid-event-import-check-saas-ads.
---

# Bid Target Picker

## Use this skill when

A campaign needs a bid event and a target that both tie back to paying customers. This skill walks an event ladder and checks volume and learning. It then turns an affordable cost per paying customer into a per-event target range.

Common requests:

- "What should my target CPA be?"
- "Can we switch to paid event bidding?"
- "tROAS or tCPA for SaaS?"
- "Which event should Meta deliver for?"

Send these jobs to another skill:

- Computing payback: `payback-period-check-saas-ads`.
- Checking whether the paid event is imported: `paid-event-import-check-saas-ads`.
- Auditing Google conversion actions: `google-ads-conversion-audit-saas-ads`.
- Approving a budget increase: `scale-or-hold-decision-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Bid strategy, current target, and learning state for each campaign or ad set (screenshot).
- Conversions by action for the last 30 days.
- Cost per paying customer from `cost-per-paying-customer-saas-ads`.
- Payback result from `payback-period-check-saas-ads`.
- Average monthly revenue per account (ARPA) and gross margin as a fraction, with the finance source, so T21 can set the affordable cost.
- Matured event-to-paid rates by signup cohort (T02).
- Event list from `paid-event-import-check-saas-ads`.

### Optional

- Change log for the last 30 days.
- Monthly churn as a fraction, which lets T21 use its churn formula.
- Conversion value settings, if tROAS is in question.

Export route:

1. In Google Ads, open Goals, then Conversions, then Summary. Next, segment Campaigns by conversion action for the last 30 days. Screenshot each campaign's Bidding settings.
2. In Meta Ads Manager, open the Ad sets view. Add Results by event and the Delivery column for the last 30 days.
3. Pull a billing export of paying customers by signup cohort.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. List each campaign or ad set with its strategy, target, bid event, and learning state.
2. Remove any ladder event that fails the import check.
3. Walk the ladder deepest first: paid, qualified trial, signup. Pick the deepest event that meets T17. If paid is not picked, track it separately.
4. For Meta ad sets, check that the picked event can also clear T06 per ad set. If it cannot, step one rung shallower or propose consolidating ad sets.
5. Set the affordable cost per paying customer under T21: ARPA times gross margin gives monthly margin, and the affordable cost is that margin times 12 months, never above 18 months of margin. With churn, use the T21 churn formula. A missing ARPA or gross margin returns `needs_data` for the target. Show the 12 month figure as the central cost and the 18 month cap as the ceiling.
6. Multiply that cost by the matured event-to-paid rate from T02 cohorts. Use the lowest and the highest recent cohort rate, and show every input.
7. Pick tCPA or tROAS. Schedule one change per campaign, spaced per T18, and set a measurement window.

## Decision rules

Thresholds sit in `../saas-ads-shared/references/thresholds.md`. Labels follow `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Paid meets T17 and imports cleanly | `approval_needed` | Bid on paid, with the affordable cost range as the target |
| Paid below T17, qualified trial meets T17 | `approval_needed` | Bid on qualified trial and track paid |
| Only signup meets T17 | `approval_needed` | Bid on signup and track deeper events |
| No event meets T17 | `needs_data` | Keep current setup until volume builds |
| Meta ad set below T06 at the picked event | `possible` | Step shallower or consolidate, then recheck |
| No T02 cohorts for the rate | `needs_data` | Set no per-event target yet |
| ARPA or gross margin missing | `needs_data` | Request the finance figures, set no target |
| Payback missing or past the T05 hold point | `hold` | `payback-period-check-saas-ads` |
| Paid event missing from import | `needs_data` | `paid-event-import-check-saas-ads` |
| Values tied to billed revenue or margin, and paid meets T17 | `possible` | Test tROAS after checking values against billing |
| Values that are static or guessed | `approval_needed` | Use tCPA |
| Recent edit inside the T18 interval | `hold` | Schedule the change after the interval |

Every target is a range with its assumptions shown. Switching events resets learning. Make one change and stack no target or budget edits on it.

## Output format

```markdown
## Bid target plan: [account], [currency], [timezone]
Window: [dates] | Cost per paying customer: [value, source] | Payback: [result, T05 status]

### Event ladder
| Campaign or ad set | Paid 30d | Qualified trial 30d | Signup 30d | Learning | Picked event |
|---|---|---|---|---|---|

### Target range
| Campaign or ad set | Affordable cost | Event-to-paid rate (low, high) | Target range | Strategy |
|---|---|---|---|---|

### Decisions
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Change schedule
[one change per campaign, date, edits on hold, measurement window]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative, made-up numbers. One Google Ads campaign runs tCPA and bids on signup. Last 30 days: 240 signups, 64 qualified trials, 18 paid conversions. ARPA is 40 USD a month and gross margin is 0.75.

Paid has 18, which is under the T17 line of 30. Qualified trial has 64, which meets T17, so it becomes the bid event. Paid is tracked separately.

Under T21, monthly gross margin per customer is 40 times 0.75, which is 30.00 USD. Affordable cost per paying customer is 30.00 times 12, which is 360.00 USD, below the 18 month cap of 540.00. Matured qualified-trial-to-paid rate is 30% across T02 cohorts, ranging from 25% to 35%.

```text
central: 360 * 0.30 = 108.00 USD per qualified trial
low:     360 * 0.25 =  90.00 USD
high:    360 * 0.35 = 126.00 USD
```

Recommendation: `approval_needed` for tCPA on qualified trial, with a range of 90.00 to 126.00 USD and a start at 108.00. Make no other edit until learning settles and the T18 interval passes. Measure paid customers once the first cohort after the switch matures under T02.

## Common failure modes

- Bidding on paid below T17.
- Setting the affordable cost from revenue instead of gross margin.
- Using rates from immature cohorts (T02).
- Giving one number without its range and assumptions.
- Changing event, target, and budget in the same week.
- Reading platform conversions as paying customers.

## Route to next

For payback inputs, use `payback-period-check-saas-ads`. For event import gaps, use `paid-event-import-check-saas-ads`. For Google conversion action setup, use `google-ads-conversion-audit-saas-ads`. For budget changes after the switch settles, use `scale-or-hold-decision-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers. A missing input becomes `needs_data`.
- End in an approval-ready recommendation with a measurement window.
- Do not pick a bid event that fails import or lacks T17 volume.
- Do not derive a target from immature cohorts or from revenue.
- Do not stack an event switch with target or budget edits (T18).
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
