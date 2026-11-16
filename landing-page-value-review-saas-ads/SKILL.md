---
name: landing-page-value-review-saas-ads
description: Reviews a SaaS landing page that gets Google Ads or Meta Ads traffic for audience, promise, proof, objections, call to action, and mobile first screen. Use when someone types "review our landing page", "why does the page not convert", "is the value clear", or "what is missing above the fold". Not for ad wording versus page wording; use ad-to-page-promise-match-saas-ads.
---

# Landing Page Value Review

## Use this skill when

A buyer needs to know whether a stranger arriving from an ad can tell who the page serves, what it does, and what happens next. Each fix is returned as a hypothesis to test.

Common requests:

- "Review our landing page."
- "Why does the page not convert?"
- "Is the value clear?"
- "What is missing above the fold?"

Send these jobs to another skill:

- Ad wording versus page wording: `ad-to-page-promise-match-saas-ads`.
- Form fields and signup steps: `signup-form-friction-review-saas-ads`.
- Plans and prices: `pricing-page-review-saas-ads`.
- Choosing between a trial and a demo: `trial-or-demo-path-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Full-page screenshots on desktop and on mobile.
- Page text in page order, with button labels.
- Ad that sends the traffic.
- Product described in one sentence.
- Proof the business can show: customer names with permission, numbers with a source.
- Main objection that sales hears.

### Optional

- Weekly signups and paid customers for the page, from analytics and billing exports.
- Trial length, if the page leads to a trial.

Export route:

1. Copy the final URL from the ad in Google Ads or Meta Ads.
2. Open the URL and capture full-page screenshots at desktop width and at phone width.
3. Copy the page text and the ad text.
4. See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Read the ad, then read only the mobile first screen. As a stranger, answer three questions: who is it for, what job does it do, and what happens after the click?
2. Repeat on desktop and note anything the mobile screen lacks.
3. Match every claim on the page to supplied proof. Mark each unsourced claim as unsupported.
4. Check whether the page answers the main objection, and where.
5. Check each call to action. Does it name the next step, repeat after each major section, and keep one label?
6. Compare page length with the size of the decision. A self-serve trial and an annual contract need different amounts of reading.
7. Sort each finding into clarity, proof, or friction. State each finding as a hypothesis. Measure it on signups first, then on paid rate in cohorts matured under T02.
8. Rewrite page lines only from supplied facts. Mark any line that needs a missing fact as `needs_data`.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels and tags: `../saas-ads-shared/references/output-standard.md`. What a screenshot shows is `confirmed`. Any effect on signups stays `possible` until a test measures it.

| Pattern | Fix type | Verdict | Next step |
|---|---|---|---|
| Mobile first screen lacks audience, job, or next step | clarity | `possible` | Rewrite headline from supplied facts |
| Claim without a supplied source | proof | `needs_data` | Remove it, or supply source and permission |
| Supplied proof absent or buried | proof | `possible` | Place it near the first call to action |
| Main objection unanswered | proof | `possible` | Answer it in the buyer's words |
| Call to action labels conflict | friction | `possible` | Use one label that names the next step |
| Signups rose, paid cohorts immature under T02 | test | `monitor` | Wait for matured cohorts |
| Signups rose, matured paid rate fell | test | `hold` | Recheck audience and promise |
| Signups and matured paid rate both rose | test | `approval_needed` | Present to the page owner |

## Output format

```markdown
## Landing page review: [URL], [traffic source]
Ad: [headline] | Product: [sentence] | Proof supplied: [list]
Mobile first screen: who [yes/no], job [yes/no], next step [yes/no]

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Rewrites from supplied facts
Current: [line] | Proposed: [line] | Source: [fact]

### Test plan
[hypothesis, fix type, metric: signups then paid rate per T02]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative only: the page, ad, and facts below are made up. Product: "Shift scheduling software for clinics with 5 to 50 staff." Proof supplied: Clinic A, named with permission, reports that weekly schedule building fell from 6 hours to 2.

1. Clarity: the mobile first screen shows "Work smarter, together" and a photo, with no button. `screenshot`, `possible`.
2. Proof: "Trusted by thousands of teams" has no supplied source. `page_text`, `needs_data`.
3. Friction: the buttons read "Get started" twice and "Talk to us" once. `page_text`, `possible`.

Headline rewrite, using supplied facts only: "Shift scheduling for clinics with 5 to 50 staff. Clinic A cut weekly schedule building from 6 hours to 2." That is 4 hours saved per week. Test the rewrite on signups, then on paid rate in cohorts matured under T02.

## Common failure modes

- Quoting conversion rates or benchmarks that nobody supplied.
- Writing proof the business cannot show.
- Judging the mobile page from a desktop screenshot.
- Reviewing the page without the ad that sends the traffic.
- Calling a rise in signups a win before paid cohorts mature under T02.

## Route to next

Ad and page mismatch: `ad-to-page-promise-match-saas-ads`. Form friction: `signup-form-friction-review-saas-ads`. Price questions: `pricing-page-review-saas-ads`. Trial or demo path: `trial-or-demo-path-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, customer names, quotes, or proof.
- End every review in an approval-ready recommendation for the page owner.
- Never quote conversion statistics, benchmarks, or expected lifts.
- Never use a customer name without supplied permission, or a number without a supplied source.
- Never call a page finding a cause until a test has measured signups and matured paid cohorts (T02).
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
