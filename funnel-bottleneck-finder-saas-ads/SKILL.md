---
name: funnel-bottleneck-finder-saas-ads
description: Finds the one SaaS funnel stage between ad click and paying customer that lost the most against the previous period, using click, session, signup, activation, and payment counts and a materiality floor. Use when someone types "where do we lose people", "traffic is fine but customers are down", "what broke in the funnel", or "which stage should I fix first". Not for paid rate by campaign; use trial-to-paid-by-campaign-saas-ads.
---

# Funnel Bottleneck Finder

## Use this skill when

Customers fell and the buyer needs to know which stage lost them. This skill compares stage conversion across two equal windows, checks measurement first, and names one bottleneck.

Common requests:

- "Where do we lose people?"
- "Traffic is fine but customers are down."
- "What broke in the funnel?"
- "Which stage should I fix first?"

Send these jobs to another skill:

- Paid rate by campaign: `trial-to-paid-by-campaign-saas-ads`.
- Platform against billing counts: `ad-platform-vs-billing-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Current and previous windows of equal length, both past the conversion lag, with identical dates and timezone in every source.
- Clicks from Google Ads and Meta Ads, using the same click metric in both windows.
- GA4 sessions from paid traffic.
- Signups and activated or qualified accounts from the CRM or product.
- Paying customers from billing by signup date, plus trial length.
- Written stage definitions.

### Optional

- Campaign split, and a dated change log for tags, consent, pages, and forms.

Export route:

1. Export clicks by campaign from Google Ads and Meta Ads.
2. Export GA4 sessions by source and medium.
3. Export signups, activations, and first payments by signup date.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm that windows, timezones, and stage definitions match across sources. If they do not, stop with `needs_data`.
2. List counts in order: clicks, sessions, signups, activated, paying.
3. For each stage, divide its count by the prior stage count to get the rate. Relative change is current rate divided by previous rate, minus 1.
4. Use only matured signups in the paying stage (T02).
5. Apply T19 to each stage: at least 100 entering and at least 30 reaching the stage in both windows. A stage below the count floor returns `needs_data`.
6. Rank only stages whose relative drop meets the T19 minimum. A smaller drop is not material and is not ranked. Name the largest material drop as the candidate, and the runner-up gets `monitor`.
7. Test measurement first when clicks hold steady. For a session drop, check T14 and consent edits. For a signup drop, check T12 and event edits.
8. With a campaign split, note whether the drop sits in one campaign or in all of them.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels: `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Stage counts below the T19 floor | `needs_data` | Widen both windows |
| Paying stage with immature signups (T02) | `needs_data` | Wait for maturity |
| Largest drop, measurement unchecked | `possible` | Run the check below |
| Largest drop, measurement clear | `likely` | Route by stage below |
| Runner-up drop | `monitor` | Re-run next period |
| No stage drop meets T19 | `monitor` | Review click volume |

| Stage | Measurement check first | Then route to |
|---|---|---|
| Sessions | T14: `consent-signal-loss-check-saas-ads` | `ad-to-page-promise-match-saas-ads` |
| Signups | T12: `signup-event-audit-saas-ads` | `landing-page-value-review-saas-ads`, `signup-form-friction-review-saas-ads` |
| Activated | CRM or product rule edits | `trial-or-demo-path-check-saas-ads` |
| Paying | Billing date match | `trial-to-paid-by-campaign-saas-ads` |

Rate arithmetic is `confirmed`. A cause needs a dated change, tag capture, or release date. Without one, it stays `possible` or `likely`.

## Output format

```markdown
## Funnel bottleneck: [account], [timezone]
Previous: [dates] | Current: [dates]

| Stage | Previous count | Current count | Previous rate | Current rate | Relative change |
|---|---|---|---|---|---|

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

Bottleneck: [stage, measurement result, route]
Runner-up (`monitor`): [stage, change]
Data gaps: [source, verdict it would firm up]
Approval-ready next step: [action, owner]
```

## Practical example

Illustrative only: made-up counts for two 7-day windows, trial length 14 days. Signups from both weeks are younger than T02 maturity, so paying is excluded.

| Stage | Previous count | Current count | Previous rate | Current rate | Relative change |
|---|---|---|---|---|---|
| Clicks | 5,000 | 5,000 | n/a | n/a | n/a |
| Sessions | 4,000 | 3,750 | 80.0% | 75.0% | down 6.25% |
| Signups | 400 | 300 | 10.0% | 8.0% | down 20.0% |
| Activated | 200 | 135 | 50.0% | 45.0% | down 10.0% |
| Paying | immature | immature | n/a | n/a | `needs_data` |

Every stage clears the T19 count floor of 100 entering and 30 reaching. Sessions fell 6.25%, under the T19 minimum drop of 10%, so sessions are not ranked. Signups carry the largest drop, so session to signup is the candidate. Activation fell exactly 10.0%, which meets T19, so it is the runner-up at `monitor`.

Clicks stayed flat while sessions held 75.0% of clicks, above the T14 review line. Signups fell 25.0%, short of T12 escalation.

No change log arrived, so an event edit is still possible. Verdict `possible`, severity high, impact signups, evidence `ads_export`, `analytics_export`, `crm_export`.

Approval-ready next step: once the change log clears, a page owner reviews the signup page and form.

## Common failure modes

- Comparing raw counts instead of stage rates.
- Calling a session drop a page problem before T14 checks.
- Putting immature signups in the paying stage (T02).
- Mixing dates, timezones, or click metrics across sources.
- Ranking a stage whose drop is below the T19 minimum.
- Naming several bottlenecks at once.

## Route to next

Consent: `consent-signal-loss-check-saas-ads`. Signup event: `signup-event-audit-saas-ads`. Page value: `landing-page-value-review-saas-ads`. Form: `signup-form-friction-review-saas-ads`. Ad and page mismatch: `ad-to-page-promise-match-saas-ads`. Paying stage: `trial-to-paid-by-campaign-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent counts, rates, or outside benchmarks. Missing inputs become `needs_data`.
- End in an approval-ready recommendation for a named owner.
- Name one bottleneck per run and list the runner-up as `monitor`.
- Never send a session drop to page work before T14 and consent checks clear.
- Never compute a paid rate from signups that fail T02.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
