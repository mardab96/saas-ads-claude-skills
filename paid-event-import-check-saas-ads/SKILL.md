---
name: paid-event-import-check-saas-ads
description: Checks whether SaaS paying-customer and qualified-trial events reach Google Ads and Meta from billing or CRM with click IDs, valid timing, and a stable match for bidding. Use when someone types "send Stripe payments to Google Ads", "offline conversion import not matching", "Meta Conversions API for paid events", or "import shows low match rate". Not for click ID capture on the site; use utm-click-id-check-saas-ads.
---

# Paid Event Import Check

## Use this skill when

This skill traces paying customers from billing or CRM to Google Ads and Meta, then picks an import path for paid-outcome bidding.

Common requests:

- "Send Stripe payments to Google Ads."
- "Offline conversion import is not matching."
- "Meta Conversions API for paid events."
- "Import shows a low match rate."

Send these jobs to another skill:

- Click ID capture: `utm-click-id-check-saas-ads`.
- Conversion action settings: `google-ads-conversion-audit-saas-ads`.
- Pixel and CAPI setup: `meta-pixel-capi-check-saas-ads`.
- Choosing the bid event: `bid-target-picker-saas-ads`.
- Account-wide billing gap: `ad-platform-vs-billing-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Sample of 20 recent paying customers: order ID, signup and paid times, timezone, stored `gclid`, `gbraid`, `wbraid`, `fbclid`, email hash (yes or no), value, currency.
- Google Ads screenshots: conversion action (source, import type) and upload diagnostics with match status.
- Meta Events Manager screenshot for server events.
- Current import cadence.

### Optional

- Click dates from the ads export; browser event ID settings.

Export route:

1. Billing or CRM: export recent paying customers with the fields above.
2. Google Ads: **Goals**, then **Conversions**; capture the import action and its diagnostics.
3. Meta: **Events Manager**; capture server events and diagnostics.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Convert all timestamps to the ad account timezone; mixed timezones get `needs_data`.
2. Record each customer's stored click ID and compare capture with T11.
3. Check each click ID's paid time is after the click and inside the T10 click-ID window.
4. Without a click ID, check email hash and the T10 user-data window; with neither, mark unmatchable.
5. Check value, currency, and one upload per customer event, keyed on order ID.
6. On Meta, confirm server events share the browser event name and event ID (T13). List user data parameters as shown.
7. Compare imported conversions with billing customers for matched dates and definition (T04).
8. Pick click-ID import, enhanced conversions for leads, or CAPI per platform. Google recommends enhanced conversions for leads for new setups; verify on its current help page.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels: `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Click ID capture below T11 | `confirmed` | `utm-click-id-check-saas-ads` |
| Paid after the T10 click-ID window | `confirmed` unimportable | Import an earlier qualified-trial event |
| No click ID, email hash present | `possible` match | Enhanced conversions for leads or CAPI |
| Duplicate upload, or missing value or currency | `confirmed` | `google-ads-conversion-audit-saas-ads` |
| Server event lacks browser event name or ID (T13) | `possible` double count | `meta-pixel-capi-check-saas-ads` |
| Imported to billing ratio outside T04 | `possible` gap | `ad-platform-vs-billing-check-saas-ads` |
| All checks pass | `approval_needed` | `bid-target-picker-saas-ads` |

## Output format

```markdown
## Paid event import check: [account], [timezone], [cadence]
Capture: [x of n] vs T11 | Imported vs billing: [ratio] vs T04

### Trace
| Group (n) | Click ID | Click to paid | Verdict |
|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Path, holds, and data gaps
[path per platform; holds with prerequisite; missing sources]
```

## Practical example

Illustrative made-up sample: 20 paying customers, Google Ads click-ID import. T10 at writing: 90 days for click IDs, 63 for user data.

| Group (n) | Click ID | Click to paid | Verdict |
|---|---|---|---|
| A (9) | gclid or gbraid | Under 90 days | `confirmed` importable |
| B (2) | gclid | Under 90 days | `confirmed` duplicate |
| C (3) | gclid | Over 90 days | `confirmed` outside T10 |
| D (4) | None | Unknown | `possible`, email hash yes |
| E (2) | None | Unknown | `confirmed` unmatchable |

Capture is 14 of 20, or 70%, under the T11 line of 80%. Google accepted 13 rows: 9 from A, plus 4 from the 2 B customers uploaded twice. Imported to billing is 13 / 20 = 0.65, below the T04 floor of 0.75. Only 11 customers matched; 9 are missing. Meta server Purchase events carry no event ID beside browser Purchase events, so double counting is `possible` (T13).

For approval: dedupe by order ID, test enhanced conversions for leads for group D, and import a qualified-trial event. Hold bid event changes until capture clears T11.

## Common failure modes

- Reading match rate as paying customers.
- Mixing timezones in timing checks.
- Trusting a T04 ratio near 1 while duplicates offset misses.
- Sending server events without the browser event ID.

## Route to next

Click IDs: `utm-click-id-check-saas-ads`. Setup: `google-ads-conversion-audit-saas-ads`, `meta-pixel-capi-check-saas-ads`. Bid event: `bid-target-picker-saas-ads`. Billing gap: `ad-platform-vs-billing-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, match rates, or customer records.
- End in an approval-ready recommendation.
- Never run an upload or send a server event.
- Never request raw emails or phone numbers.
- Verify T10 windows on the current Google help page.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
