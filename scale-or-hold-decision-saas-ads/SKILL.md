---
name: scale-or-hold-decision-saas-ads
description: Decides whether a SaaS Google Ads or Meta Ads budget increase is supported by evidence, checking volume, trial quality, reconciliation, payback, next-dollar cost, tracking health, learning state and step size in order, then returns hold, needs_data or approval_needed, and ranks channels for where the next budget goes. Use when someone types "can we afford to scale", "can I raise the budget", "should we scale this campaign", or "is it safe to scale". Not for computing payback months; use payback-period-check-saas-ads.
---

# Scale Or Hold Decision

## Use this skill when

A buyer wants more budget on a Google Ads or Meta Ads campaign or channel and needs a gated answer. This skill reads upstream skill outputs plus tracking and learning evidence, then runs eight gates in order. A hold is a normal outcome. When several channels compete for the same budget, it also ranks them cut, hold, or scale.

Common requests:

- "Can I raise the budget on this campaign?"
- "Should we scale this campaign next week?"
- "Can we afford to scale?"
- "Is it safe to scale Google non-brand search?"
- "Leadership wants more trials. Can paid take more money?"
- "Where should the next budget go?"

Send these jobs to another skill:

- Computing cost per paying customer: `cost-per-paying-customer-saas-ads`.
- Building paid-rate cohorts: `trial-to-paid-by-campaign-saas-ads`.
- Reconciling platform conversions with billing: `ad-platform-vs-billing-check-saas-ads`.
- Calculating payback: `payback-period-check-saas-ads`.
- Choosing the bid event: `bid-target-picker-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Output of `cost-per-paying-customer-saas-ads` for the campaign or channel and window.
- Output of `trial-to-paid-by-campaign-saas-ads`, with campaign and account paid rates.
- Output of `ad-platform-vs-billing-check-saas-ads` with the matched ratio. For a campaign that bids on signups, also the platform signup count and the CRM signup count for the same dates.
- Output of `payback-period-check-saas-ads`, gross-margin based, churn applied, with one value per channel when channels churn differently.
- Spend and new paying customers per channel for two equal periods of at least 14 days around the last budget change, for the next-dollar gate.
- Tracking health note: primary event and click counts for the comparable windows T12 describes.
- Learning state: Meta ad set delivery screenshot or Google bid strategy status screenshot.
- Last budget change date and proposed budget step as a percentage.

### Optional

- Brand and non-brand split of paying customers for the channel.
- Change log since the last budget change.
- Conversion lag for the paid event.
- A holdout result for a retargeting line.

Export route:

1. In Google Ads, screenshot the campaign row with bid strategy status visible.
2. In Meta Ads Manager, screenshot the ad set row with the Delivery column visible.
3. Open each platform's change history and note the date of the last budget edit.
4. Paste the upstream skill outputs as text.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Name the campaign or channel, platform, window dates, currency, timezone and proposed step. A missing step or last change date is `needs_data`.
2. Confirm all upstream outputs cover the same campaign and dates. Mismatched windows are `needs_data`.
3. Run the next-dollar helper on the two periods around the last budget change. Use the 12-month figure from the payback helper as `--affordable` (T21; 12 months is the central figure and 18 months the ceiling). New paying customers are counted by signup date, and every signup in both periods must be matured (T02). Give `--after-end` (last day of the after period), `--as-of` (export date), and `--trial-days` (or `--lag-days`; the default lag is trial days plus 7 billing lag days). While the after period is immature the helper stops and prints the date to rerun:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/marginal_cac.py" "<absolute path to your before and after CSV>" --days-before 28 --days-after 28 --after-end <YYYY-MM-DD> --as-of <YYYY-MM-DD> --trial-days <days> --affordable <T21 cost>`
4. Run gates 1 to 7 in order and record each result with its evidence tag. Record every gate, yet let the first failure set the verdict and name the prerequisite. A gate that cannot be evaluated is not a pass. Its verdict is in the "cannot evaluate" column of the gate table.
5. Run the brand check for any channel that carries brand campaigns. Results rest on brand demand under T23, and T09 decides whether the brand split is reported.
6. If gates 1 to 7 and the brand check pass, apply gate 8: cap the step at T18 and confirm spacing since the last budget change.
7. Apply the retargeting check. A retargeting or brand line can show a low cost per paying customer without adding any customer, because it reaches people who were already likely to buy. Never rank or scale a retargeting line on its own cost. Ask for a holdout: leave a random share of the retargeting audience out, then compare paying customers between exposed and held-out groups.
8. When several channels compete for budget, fill the "Where the next budget goes" table from pooled (T24) or marginal (T27) numbers, never from blended ones.
9. Set a check date after the paid event's conversion lag has cleared from the step date. Never phrase it as an expected result.
10. Fill the decision table and write either a hold with its prerequisite or an approval-ready step for a named approver.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. No single threshold approves a budget change.

| Gate | Pass condition | If failed | If it cannot be evaluated | Next step |
|---|---|---|---|---|
| 1 Volume | Paying customers meet T01, or the pooled line meets it under T24 | `needs_data` | `needs_data` (no cost output) | Wait for volume or pool; `cost-per-paying-customer-saas-ads` |
| 2 Trial quality | Campaign meets the T02 floor and is not weak under T03 | `hold` (weak under T03) | `needs_data` (below the T02 floor, or no paid-rate output) | Pool under T24, or fix trial quality; `trial-to-paid-by-campaign-saas-ads` |
| 3 Reconciliation | Billing ratio inside the T04 band. For a campaign that bids on signups, platform signups against CRM signups also inside the T04 band | `hold` | `needs_data` (a count or definition is missing) | Resolve the T04 gap; `ad-platform-vs-billing-check-saas-ads` |
| 4 Payback | This channel's payback is below the T05 hold level. A payback in the T05 review band (12 to 18 months) passes, with the caveat recorded beside the approval | `hold` (above the hold level, or never reached once churn is applied) | `needs_data` (`needs_churn`, or no value for this channel) | Improve payback; `payback-period-check-saas-ads` with `--churn-by-source` |
| 5 Next dollar | Incremental CAC is within the T21 12-month cost (T27 `within_affordable`) | `hold` (`over_affordable`) | `needs_data` (no matured periods, spend up under 10%, or under 20 paying customers), plus a measurement step plan | Record the next step as a test; `marginal_cac.py` (`--design` for the plan) |
| 6 Tracking | No T12 drop pattern | `hold` | `needs_data` (primary event or click counts missing) | Clear tracking; `signup-event-audit-saas-ads` |
| 7 Learning | Out of learning under T22 (Meta also T06) | `hold` | `needs_data` (screenshot or edit date missing) | Wait, since an edit during learning resets it |
| 8 Step | Step within T18 size and spacing | `hold` | `needs_data` (step or last change date missing) | Resize the step or wait for spacing |

Gate 5 with no clean budget change in the last 90 days has nothing to measure, so it returns `needs_data`. Average cost is not a substitute. Do not stop at the bare `needs_data`. Add a measurement step plan from the design mode. It names one channel, one step of 20% (T18) on a named date, the minimum spend and paying customers to read it, and the check date:
`python3 "<skill-dir>/../saas-ads-shared/scripts/marginal_cac.py" --design --daily-spend <current daily spend> --current-cac <current cost per paying customer> --start <YYYY-MM-DD> --trial-days <days> --affordable <T21 cost>`
Hold every other budget change on that channel until the check date. Before and after ignores seasonality, offer changes, and tracking changes, and it is not incrementality, so call the result a signal and keep a holdout or geo split as the proof. If a named human chooses to proceed anyway, record that as a decision on a T18-sized test, never as a pass.

Where the next budget goes. Label each channel from the same numbers:

| Channel evidence | Label | Action for a named human |
|---|---|---|
| Verdict is `approval_needed`: gates 1 to 8 and the brand check pass, and payback is `ok`, or `review` with its caveat recorded | `scale` | Rank scale channels by lowest incremental CAC, then step by T18 |
| Gate 5 `over_affordable` and payback is `review` or `hold_scale` | `cut` | Review a smaller budget for that channel; the cut is a recommendation, not an action |
| Any other result: a gate `needs_data` or `hold`, or a retargeting line with no holdout | `hold` | Keep the budget; fetch the named missing input |

| Pattern | Verdict | Next step |
|---|---|---|
| Upstream output or screenshot missing | `needs_data` | Request it; that gate counts as unpassed |
| Payback inside the T05 review band (12 to 18 months) | `approval_needed` if every other gate passes | Gate 4 passes; record the caveat beside the approval |
| Results rest on brand demand under T23 | `hold` | `brand-nonbrand-split-saas-ads` |
| Retargeting cost looks low, no holdout | `hold` | Run a holdout; low cost is not proof of added customers |
| Meta frequency rising while CTR falls | `hold` | `meta-creative-fatigue-check-saas-ads`; confirm fatigue before any step |
| All gates and brand check pass | `approval_needed` | Step within T18, check date after lag, named approver |

## Output format

Labels follow `../saas-ads-shared/references/output-standard.md`.

```markdown
## Scale or hold: [campaign or channel], [platform], [currency], [timezone]
Window: [dates] | Last budget change: [date] | Proposed step: [%] | Lag: [days]

### Gate table
| Gate | Threshold | Evidence | Tag | Result (pass / failed / cannot evaluate) |
|---|---|---|---|---|

Brand check (T09, T23): [pass, fail, or not applicable, with reason]
Verdict: [hold / approval_needed / needs_data]
Prerequisite or approved step: [text] | Check date: [date] | Approver: [name]

### Where the next budget goes
| Channel | Incremental CAC | T21 12-month cost | Payback | Label (scale / hold / cut) |
|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Data gaps
[missing inputs and the gate each would settle]
```

## Practical example

Illustrative numbers from the synthetic samples `examples/data/marginal_cac_periods.csv` and `examples/data/churn_by_source.csv`, plus made-up reconciliation counts. Meta prospecting campaign, proposed step 15%, last budget change 12 days ago, T21 12-month cost 611.92.

| Gate | Evidence | Result |
|---|---|---|
| 1 Volume (T01) | 20 new paying customers in the after period, floor 20 | pass |
| 2 Trial quality (T02, T03) | 400 matured signups, floor 30; 36 / 400 = 9.0%; account 12.0%; ratio 0.75, floor 0.50 | pass |
| 3 Reconciliation (T04) | 33 Meta-reported / 20 billing-confirmed = 1.65; band 0.75 to 1.25 | failed |
| 4 Payback (T05) | 13.2 months, churn applied; review line 12, hold line 18 | pass, review-band caveat recorded beside the approval |
| 5 Next dollar (T27, T21) | Spend 8000.00 to 9600.00 (+20%, the T18 cap), paying 18 to 20; incremental CAC 800.00 against 611.92 | failed |
| 6 Tracking (T12) | Primary event down 4%, clicks down 2% | pass |
| 7 Learning (T22) | No learning label, last edit 12 days ago, 71 optimization events in 7 days against 50 | pass |
| 8 Step (T18) | Evaluated only after gates 1 to 7 pass | not reached |

Brand check: not applicable, no brand campaign in this channel.

Verdict: `hold`. Gate 3 is the first failure, and gate 5 also failed. Prerequisite: resolve the T04 gap. Meta reports more conversions than billing confirms, so cost on platform numbers looks better than reality. Route to `ad-platform-vs-billing-check-saas-ads`, then `meta-pixel-capi-check-saas-ads`. Re-run this skill once the ratio sits inside the band.

Where the next budget goes, from the same samples:

| Channel | Incremental CAC | T21 12-month cost | Payback | Label |
|---|---|---|---|---|
| google_search_nonbrand | 300.00 | 611.92 | 5.0 months, `ok` | `scale` |
| meta_prospecting | 800.00 | 611.92 | 13.2 months, `review` | `cut` |
| meta_retargeting | needs_data (spend rose 8.3%, under the 10% T27 minimum) | 611.92 | `needs_churn` | `hold` |

Google non-brand is `scale` only because its verdict would be `approval_needed`: its gates 1 to 8 and the brand check also pass (made-up for this example). A `review` payback such as Meta prospecting's 13.2 months does not block that verdict on its own; it passes gate 4 with the caveat written beside the approval. Meta prospecting is `cut` because gate 5 failed with a `review` payback. Meta retargeting costs 55.00 per paying customer, the lowest line, yet that proves nothing about added customers. Ask for a holdout before it gets a single extra dollar.

## Common failure modes

- Treating five passed gates as approval while one gate fails.
- Counting a missing upstream output as a pass.
- Using platform conversions as paying customers in gate 1.
- Using revenue payback where gross margin belongs.
- Using a blended payback where channels churn differently.
- Editing a Meta ad set still in learning, which resets learning.
- Approving a step larger than T18 because results look strong.
- Scaling a channel whose paying customers come from brand demand.
- Ranking a retargeting line by its cost per paying customer.
- Writing a check date as a forecast.
- Calling a campaign out of learning because the label is missing, without the edit date and event volume.

## Route to next

Volume: `cost-per-paying-customer-saas-ads`. Trial quality: `trial-to-paid-by-campaign-saas-ads`. Reconciliation: `ad-platform-vs-billing-check-saas-ads`. Payback: `payback-period-check-saas-ads`. Brand dependence: `brand-nonbrand-split-saas-ads`. Meta fatigue: `meta-creative-fatigue-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price or form.
- Never invent numbers; missing evidence becomes `needs_data`.
- End in an approval-ready recommendation for a named human, or a hold with its prerequisite.
- Never skip a gate or reorder gates to reach approval.
- Never approve a step beyond T18 size or spacing.
- Never promise a result from a budget increase; state only a check date.
- Treat a hold as a normal, complete answer.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
