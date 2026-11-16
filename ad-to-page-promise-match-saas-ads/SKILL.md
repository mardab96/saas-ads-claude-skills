---
name: ad-to-page-promise-match-saas-ads
description: Compares what a SaaS Google Ads or Meta ad promises with the landing page first screen and CTA, then ranks broken promises in offer, audience, price, trial terms, and wording. Use when someone types "ad clicks but nobody signs up", "message match", "does the page match the ad", or "high CTR low signup rate". Not for page quality with no ad to compare; use landing-page-value-review-saas-ads.
---

# Ad To Page Promise Match

## Use this skill when

A paid click lands on a page that may say something different from the ad. This skill builds a promise list from the ad and checks each promise against the first screen and CTA. Every mismatch is a hypothesis for a test. None proves a cause.

Common requests:

- "Ads get clicks but nobody signs up."
- "Check message match on our trial campaign."
- "Does the page match the ad?"
- "High CTR, low signup rate on Meta. Is it the page?"

Send these jobs to another skill:

- Whole-page value review with no ad to compare: `landing-page-value-review-saas-ads`.
- Field count or form steps: `signup-form-friction-review-saas-ads`.
- Plan and price layout: `pricing-page-review-saas-ads`.
- Signups that do not become paying customers: `trial-to-paid-by-campaign-saas-ads`.
- Signups missing from reports: `signup-event-audit-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Exact ad text. Google Ads: every headline and description. Meta: primary text, headline, description, and text on the creative.
- Targeting. Google Ads: the ad group keywords. Meta: the audience definition and the ad's angle.
- Final URL for each ad.
- Full-page screenshots of that URL on desktop and mobile, dated.
- Page text exactly as copied from the live page.
- Offer terms: trial length, price, and whether a card is needed.

### Optional

- Ad-level clicks and signups for the same dates.
- Campaign paid rates for the T03 check.
- Dated page releases and ad edits.

Export route:

1. Google Ads: open Ads, filter to the campaign, and download headlines, descriptions, and final URL.
2. Google Ads: open Keywords for the same ad groups and download.
3. Meta: in Ads Manager, export ad-level text and destination URL, then copy each ad set's audience.
4. Open each final URL in a clean browser window and capture desktop and mobile.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. List each ad with its final URL. Group ads that share a URL.
2. Build a promise list per ad: audience, offer, price or trial terms, key words, and proof. Quote the ad exactly.
3. Add targeting context: keyword theme for Google Ads, audience and angle for Meta.
4. Mark the first screen on each device as the content visible before scrolling. Record headline, subhead, CTA label, terms, and proof shown there.
5. Check each promise against the first screen and CTA. Mark it `match`, `changed`, or `absent`, quoting page text as supplied.
6. Flag different offer wording, a missing keyword theme, differing trial terms, a different audience, a different CTA verb, and ad proof absent from the page.
7. Rank mismatches by notice order. Within a rank, list the ad with more clicks first when click data exists.
8. When paid rates are supplied, check T03 and note any trial or price mismatch on a flagged campaign.
9. Write each mismatch as a test: page or ad change, measure to watch, and owner.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Labels and tags follow `../saas-ads-shared/references/output-standard.md`.

Notice order, a working rule of this skill:

| Rank | Mismatch type | Severity |
|---|---|---|
| 1 | Trial length, card, or price differs | high |
| 2 | Offer differs (trial versus demo) | high |
| 3 | Audience differs | medium |
| 4 | Keyword theme or angle missing | medium |
| 5 | CTA verb differs | medium |
| 6 | Ad proof absent from page | low |

| Pattern | Verdict | Next step |
|---|---|---|
| Both quotes supplied and they contradict | `confirmed` mismatch, effect `possible` | Test, `approval_needed` |
| Promise sits below the fold on one device | `likely` mismatch on that device | Test moving it up |
| Screenshot, page text, or ad export missing | `needs_data` | Request it |
| T03 flag plus differing trial or price terms | `possible` link | `trial-to-paid-by-campaign-saas-ads` |
| Page price differs from ad price | `confirmed` mismatch | `pricing-page-review-saas-ads` |
| All promises match, signups still low | `monitor` | `landing-page-value-review-saas-ads` |

## Output format

```markdown
## Promise match: [campaign], [platform], [capture date]
Final URL: [url] | Targeting: [keyword theme or audience and angle] | Terms: [trial, price, card]

### Promise list
| Ad | Promise type | Ad text (exact) | First screen text (exact) | Device | Status |
|---|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Ranked test hypotheses
[mismatch, change to test, measure to watch, approval owner]

### Data gaps
[missing input and the finding it would firm up]
```

## Practical example

Illustrative only: made-up ad and page text for a fictional invoicing tool.

Google Ads keyword theme: "invoice software". Headlines: "Invoice Software For Freelancers", "Free 14-Day Trial, No Card", "Award-Winning Invoicing". Description CTA: "Start your free trial."

Desktop and mobile first screen: headline "Invoice Software For Finance Teams", subhead "7-day trial. Card required.", button "Start free trial". Page text mentions no award.

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|
| Trial is 7 days shorter, card required | `ads_export`, `screenshot`, `page_text` | `confirmed` mismatch | high | high | signups | Owner decides which terms are correct, `approval_needed` |
| Audience shifts to finance teams | `ads_export`, `page_text` | `confirmed` mismatch | medium | high | signups | Test a freelancer headline |
| Award claim absent | `ads_export`, `page_text` | `confirmed` mismatch | low | medium | client_trust | Verify claim or remove it |

Keyword theme and CTA verb match. Effect on signups stays `possible` until a test reads out.

## Common failure modes

- Paraphrasing ad or page text instead of quoting it.
- Reviewing the whole page when the visitor decides on the first screen.
- Skipping the mobile capture.
- Calling a mismatch the cause of low signups.
- Comparing an ad with a page released after the ad's dates.
- Reading high CTR as proof the page is wrong.

## Route to next

Page value and proof: `landing-page-value-review-saas-ads`. Form steps: `signup-form-friction-review-saas-ads`. Paid rate by campaign: `trial-to-paid-by-campaign-saas-ads`. Price and plans: `pricing-page-review-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, quotes, claims, or results.
- End in an approval-ready recommendation for a named owner.
- Quote ad and page text exactly as supplied.
- Never present a mismatch as a proven cause of low signups.
- Never choose trial, card, or price terms. Flag the gap and route the decision.
- Never judge an ad against a capture from a different date without a `change_log` note.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
