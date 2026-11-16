---
name: pricing-page-review-saas-ads
description: Reviews a SaaS pricing page that paid traffic reaches for plan clarity, price anchor, trial terms, billing toggle default, per-plan calls to action, hidden fees, and whether the plan promoted in ads is the plan the page features, then uses billing data to show which plan paid traffic buys. Use when someone types "review our pricing page", "ads send people to pricing, what is wrong", "monthly or annual default", or "which plan should ads promote". Not for ad copy against a non-pricing page; use ad-to-page-promise-match-saas-ads.
---

# Pricing Page Review

## Use this skill when

Paid clicks land on pricing, or reach it one step after the landing page. This skill compares ad terms with page terms, checks plan structure, and uses billing data to show which plan paid traffic buys. It never recommends a price.

Common requests:

- "Review our pricing page before we send more ad traffic to it."
- "Ads send people to pricing, what is wrong?"
- "Should the billing toggle default to monthly or annual?"
- "Which plan should ads promote?"
- "Ad says no card required. Does the page agree?"

Send these jobs to another skill:

- Ad copy against a non-pricing landing page: `ad-to-page-promise-match-saas-ads`.
- Headline and value on a landing page: `landing-page-value-review-saas-ads`.
- Trial or demo flow after the plan click: `trial-or-demo-path-check-saas-ads`.
- Channel payback math: `payback-period-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Desktop and mobile screenshots plus page text, including FAQ and footnotes, with the billing toggle in each position.
- Plan list: name, monthly price, annual price if offered, and what each plan includes.
- Ad terms from active ads reaching pricing: price, plan, trial length, and card wording.
- Trial terms: length, card requirement, and what happens at trial end.
- Average revenue per account by plan from billing, for customers acquired through paid traffic.

### Optional

- Cost per paying customer and gross margin, or a payback result.
- Plan-click events from GA4.

Export route:

1. In Google Ads and Meta Ads Manager, export active ads with final URL and ad text.
2. Capture the pricing page in each toggle state on desktop and mobile.
3. From billing, export new paying customers with plan and billing period, joined to signup source from the CRM.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. List every ad term about price, plan, trial, and card. Find each one on the page in the default view on both devices.
2. Name the plan ads lead with and the plan the page highlights through badge, position, or color. Record any mismatch.
3. Record the billing toggle default. Check whether the first price a buyer sees matches the ad price and states its billing period.
4. Compare plan names and feature lists with buyer words from the ads. Flag internal jargon and features listed without the job they do.
5. Check that each plan has its own call to action and note where it leads.
6. Search for costs outside the headline price: per-seat charges, setup fees, usage limits, minimum terms. Flag any shown only in footnotes.
7. State what happens after the trial: automatic charge, downgrade, or lockout. Flag it when the page leaves this open.
8. From billing, compute each plan's share of paid-traffic customers and blended average revenue per account.
9. If cost per paying customer and gross margin exist, divide cost by monthly gross margin per plan for simple payback before churn. Compare with T05.
10. Write findings, then test ideas and open questions for the page owner.

## Decision rules

Threshold values live in `../saas-ads-shared/references/thresholds.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Ad price, trial, or card term contradicted on the page | `confirmed` with screenshot | `ad-to-page-promise-match-saas-ads` |
| Ads promote one plan, page highlights another | `confirmed` | Test idea, `approval_needed` |
| Default toggle shows a price unlike the ad price, period unstated | `confirmed` | Test idea on default or label |
| Plan names or features miss buyer words | `possible` | `landing-page-value-review-saas-ads` |
| Plan lacks its own call to action, or it leads somewhere unexpected | `confirmed` | `trial-or-demo-path-check-saas-ads` |
| Fee or limit shown only in footnotes | `confirmed` | Owner question |
| After-trial terms absent | `confirmed` gap | Owner question |
| Main plan bought by paid traffic has simple payback past a T05 line | `likely`, since churn is not applied | `payback-period-check-saas-ads`, `hold` on scaling |
| No billing data by plan | `needs_data` | Request billing export |

## Output format

Use the labels in `../saas-ads-shared/references/output-standard.md`.

```markdown
## Pricing page review: [product], [page URL], [currency]
Window: [dates] | Devices: [list] | Toggle default: [monthly/annual]

### Ad terms versus page terms
| Ad term | Ad wording | Page wording | Device | Evidence | Match |
|---|---|---|---|---|---|

### Plan mix from billing
| Plan | Monthly price | Paid customers | Share | Simple payback before churn |
|---|---|---|---|---|
Blended ARPA: [value] | Cost per paying customer: [value or needs_data]

### Findings
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Open questions for the page owner
### Test ideas (approval_needed)
### Data gaps
```

## Practical example

Illustrative numbers, made up. Plans: Starter 29, Team 79, Business 199 USD per month. Ads say "Team plan, 79 USD a month, 14-day free trial, no card required."

Page view: a "Most popular" badge sits on Starter. Toggle defaults to annual, showing Team at 63 USD per month billed annually. FAQ says a card is required to start a trial.

Billing, 90 days, 40 paid-traffic customers: Starter 26, Team 12, Business 2. Monthly revenue: 754 + 948 + 398 = 2,100 USD. Blended ARPA is 52.50 USD. Starter holds 65%.

Supplied: cost per paying customer 600 USD, gross margin 80%. Simple payback before churn: Starter 600 / 23.20 = 25.9 months, Team 600 / 63.20 = 9.5 months, blended 600 / 42.00 = 14.3 months.

Findings: card claim contradicted by FAQ, `confirmed`, high severity, `client_trust`. Ad price differs from default view, `confirmed`. Badge on Starter while ads sell Team, `confirmed`. Starter payback sits past both T05 lines, `likely`; scaling stays on `hold`. Test idea, `approval_needed`: move the badge to Team for paid traffic. Owner question: is a card required, and what happens at trial end?

## Common failure modes

- Recommending a price or discount.
- Picking the promoted plan from preference instead of billing data.
- Checking desktop only while most paid clicks arrive on mobile.
- Using revenue instead of gross margin for payback.
- Reading platform conversions as paying customers.
- Missing terms hidden in FAQ or footnotes.

## Route to next

Payback: `payback-period-check-saas-ads`. Ad and page wording: `ad-to-page-promise-match-saas-ads`. Trial or demo flow: `trial-or-demo-path-check-saas-ads`. Page value: `landing-page-value-review-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers; missing inputs stay `needs_data`.
- End in an approval-ready recommendation, never a live change.
- Never recommend a price, discount, or plan structure; raise questions instead.
- Never call a plan unprofitable from revenue alone; apply T05 with gross margin.
- Never name the plan ads should promote without plan-level billing data.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
