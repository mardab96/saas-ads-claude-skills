---
name: trial-or-demo-path-check-saas-ads
description: Checks whether the SaaS conversion path after the ad click, self-serve trial or demo request, fits the product and price. Traces steps, time to first value and follow-up speed from CRM data, then flags the largest delay. Use when someone types "should we offer a demo or a trial", "demo requests do not close", "trial users never activate", or "leads wait days for a call". Not for form fields and steps; use signup-form-friction-review-saas-ads.
---

# Trial Or Demo Path Check

## Use this skill when

A paid click lands on a trial or demo path and the buyer needs to know where leads stall. This skill maps each step, times the gaps, splits results by campaign, and compares the path with price level.

Common requests:

- "Should we offer a demo or a trial?"
- "Demo requests from Google Ads do not close."
- "Trial users from Meta never activate."
- "Leads wait days for a call."

Send these jobs to another skill:

- Signup form fields: `signup-form-friction-review-saas-ads`.
- Paid rate by campaign alone: `trial-to-paid-by-campaign-saas-ads`.
- Plan and price presentation: `pricing-page-review-saas-ads`.
- Unknown stall point across the funnel: `funnel-bottleneck-finder-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Path description from ad click to first value, listing every screen, email, and call.
- CRM export per lead or signup: campaign, created date, first contact date, stage dates, outcome.
- Product activation definition as one observable event.
- Price level as average revenue per account, with currency.
- Team capacity for calls per week.

### Optional

- Billing export with paid status and gross margin.
- Meeting booked and meeting held flags.
- Pipeline CSV with columns `campaign`, `lead_date`, `meeting_date`, `won_date`, and an optional `acv`, one row per lead, for `lead_to_won.py`.

Export route:

1. In the CRM, filter paid-campaign leads and signups created in the window.
2. Export campaign, dates, stages, and outcome.
3. From billing, export paid status for the same accounts.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Write the path as numbered steps and mark each as self-serve or human.
2. Compute the median time between consecutive steps from CRM dates. Count rows with missing dates and set them aside.
3. For demo paths, compute time from request to first contact from CRM dates. For show rate, close rate, and lead-to-won days by campaign, run the helper. It counts only leads at least one sales cycle old (T28), and compares campaigns at 30 matured leads or more:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/lead_to_won.py" "<absolute path to your pipeline CSV>" --as-of <YYYY-MM-DD> --spend "<absolute path to your spend CSV>"`
   Drop `--spend` when no spend was supplied. Add `--sales-cycle-days <days>` when the cycle is known; otherwise the helper derives it from at least 10 won leads. Cost per won deal needs 20 won deals (T01).
4. For trial paths, compute activation rate and median time to first value. Compute paid rate on matured signups only (T02).
5. Split every rate by campaign and flag weak campaigns under T03.
6. Compare path cost with price level using billing data and gross margin payback (T05).
7. Name the largest delay: the longest median gap or the steepest drop.
8. Propose one path test with a primary metric and a sample need per arm under T02.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Labels follow `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Matured cohort below T02 floor | `needs_data` | Widen dates; report no rate as a finding |
| Long first-contact gap, show rate lower in slower rows | `possible` | Size a contact-speed test with T02 |
| Close rate weak in one campaign (T03) | `possible` | `trial-to-paid-by-campaign-saas-ads` |
| Trial activation low, signups steady | `possible` | `funnel-bottleneck-finder-saas-ads` |
| Drop concentrated at the form | `possible` | `signup-form-friction-review-saas-ads` |
| Human call in path, payback past T05 review line | `likely` mismatch | Propose a self-serve trial arm |
| No first contact date in CRM | `needs_data` | Request the field; make no speed claim |
| Test has metric, cohort rule, owner | `approval_needed` | Named owner signs off |
| Campaign below 30 matured leads (T28) | `needs_data` | Widen dates; report no rate as a finding |
| Won deals below 20, so cost per won deal rests on too few (T01) | `needs_data` | Show the arithmetic only |

A rate is `confirmed` when CRM rows support it. A cause stays `possible` until dated evidence supports it. No response-time benchmark exists in this pack.

Script contract for `lead_to_won.py`: columns `campaign`, `lead_date`, `meeting_date`, `won_date`, optional `acv`, plus `--as-of`, optional `--sales-cycle-days`, `--spend`, and `--us-dates`. A won lead without a meeting date, or a date out of order, exits with code 2. Output prints per campaign leads, matured, meetings, `show_rate`, won, `close_rate`, median lead-to-won days, and `T28_label` (30 matured leads), then an `account` row, a `maturity_rule` line, and with `--spend` cost per meeting, cost per won deal, and a `T01_label` (20 won deals). Each table carries only its own label.

## Output format

```markdown
## Path check: [account], [trial or demo], [currency]
Window: [dates] | Activation event: [name] | ARPA: [value] | Call capacity: [per week]

### Path map
| Step | Self-serve or human | Median gap to next | Drop to next |
|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Largest delay
[step, median gap, evidence tag]

### Path test proposal
[arms, metric, cohort rule, sample need, approver]

### Data gaps
[missing fields and the verdict each would firm up]
```

## Practical example

Illustrative numbers, made up for this file. One Google Ads campaign produced 50 demo requests.

- Median time from request to first contact: 2 days.
- Meetings held: 20 of 50, a 40% show rate.
- Contacted within 1 day: 20 requests, 14 showed (70%).
- Contacted later: 30 requests, 6 showed (20%).

Check: 14 + 6 = 20 held, and 20 / 50 = 40%.

Finding: request to first contact is the largest delay. Verdict `possible`, severity high, confidence medium, impact `signups`, evidence `crm_export`. Faster-contacted leads may differ in intent, so speed is unproven as the cause. Payback is `needs_data` because no billing export was supplied. Next step: an `approval_needed` contact-speed test sized under T02.

## Common failure modes

- Quoting an outside response-time benchmark.
- Reading paid rate on signups younger than the T02 cohort age.
- Reading a blended show rate when one campaign drags it down (T03).
- Keeping a sales call that price level cannot pay back (T05).
- Counting meetings booked as meetings held.
- Using revenue where gross margin belongs.

## Route to next

Form friction: `signup-form-friction-review-saas-ads`. Paid rate: `trial-to-paid-by-campaign-saas-ads`. Pricing: `pricing-page-review-saas-ads`. Stall point: `funnel-bottleneck-finder-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, benchmarks, or response-time targets.
- End in an approval-ready recommendation with a named approver.
- Do not propose a test that exceeds stated call capacity.
- Do not switch a path from one campaign's result; split by campaign first.
- Do not treat a speed pattern as proof that speed caused shows.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
