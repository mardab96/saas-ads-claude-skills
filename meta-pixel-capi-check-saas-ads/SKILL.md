---
name: meta-pixel-capi-check-saas-ads
description: Reviews a SaaS Meta Pixel plus Conversions API setup from Events Manager screenshots, covering browser and server events, deduplication, the event match quality label, diagnostics, and the paid-event path. Use when someone types "Meta events duplicated", "is CAPI working", "event match quality low", or "pixel and CAPI both fire for one signup". Not for platform versus billing gaps; use ad-platform-vs-billing-check-saas-ads.
---

# Meta Pixel And CAPI Check

## Use this skill when

A SaaS team sends events to Meta from the browser Pixel, the Conversions API (CAPI), or both. This skill checks two things for each primary event: whether Meta counts it once, and whether the paid event arrives.

Common requests:

- "Meta events look duplicated."
- "Is CAPI working?"
- "Event match quality is low. Does it matter?"
- "Pixel and CAPI both fire for one signup."

Send these jobs to another skill:

- Signup event definition: `signup-event-audit-saas-ads`.
- Tag firing in the container: `gtm-container-review-saas-ads`.
- Consent loss across channels: `consent-signal-loss-check-saas-ads`.
- Meta reporting more signups than the backend, or full billing reconciliation: `ad-platform-vs-billing-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Events Manager screenshots: data source overview, event list with browser and server counts, diagnostics, event match quality label as shown, and the test events view.
- Site URL and the event names treated as primary.
- Server route: partner integration, gateway, or custom code.
- Backend signup count and billing count of new paying customers for the same dates and timezone.

### Optional

- Ad clicks for the same dates.
- Share of paid signups with a stored `fbclid`.

Export route:

1. In Events Manager, open the dataset and set the backend date range.
2. Screenshot Overview with the browser and server columns visible.
3. Open each primary event. Screenshot its detail and match quality label.
4. Screenshot Diagnostics.
5. In Test events, fire one signup and screenshot what arrives.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. List each primary event with its intended sources (browser, server, or both). Flag any intended source that shows zero events.
2. In the test view, check that both sides send the same event name and event ID. Meta deduplicates only on that match (T13).
3. Divide the browser plus server count by the backend count for the same dates. Then apply T13.
4. Record each diagnostics warning and the event it names. Treat warnings as signals to test.
5. Quote the match quality label exactly as Meta shows it. Never estimate a score.
6. Confirm the paid event leaves the server with click or browser IDs (`fbc`, `fbp`). Test stored click IDs against T11. T10 does not apply to Meta.
7. Run three more tests. Check drops with steady clicks against T12. Check reported results against billing with T04. Check low browser counts against consent with T14.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels and tags: `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Total meets T13, test view shows an event ID mismatch | `likely` duplication | Seek approval to align event IDs, then recount |
| Total meets T13, no test view supplied | `possible` | Capture test events |
| Intended source shows zero events | `confirmed` source gap | `gtm-container-review-saas-ads` |
| Event drop meets T12 | `possible` tracking fault | `signup-event-audit-saas-ads` |
| Paid event is browser only, lacks IDs, or click IDs fall below T11 | `possible` weak match | `paid-event-import-check-saas-ads` |
| Reported versus billing falls outside T04 | `possible` | `ad-platform-vs-billing-check-saas-ads` |
| Browser counts fall short on consent-gated pages (T14) | `possible` | `consent-signal-loss-check-saas-ads` |
| Warning with no count effect | `monitor` | Recheck after the next release |

Count arithmetic is `confirmed` when screenshots and backend counts cover the same dates. Causes stay `possible` or `likely` until a test capture or a dated change shows them.

## Output format

```markdown
## Meta Pixel and CAPI check: [dataset], [site], [timezone]
Dates: [range] | Server route: [route] | Primary events: [names]

| Event | Browser | Server | Backend | Total/backend | Same name and ID | Match quality label |
|---|---|---|---|---|---|---|

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

Diagnostics: [warnings as shown]
Approval-ready fixes: [ordered, with holds]
Data gaps: [input, verdict it would firm up]
```

## Practical example

Illustrative, made-up numbers. Over one week, Meta received 160 browser and 150 server signup events, 310 in total. Backend records show 120 signups for the same dates.

310 / 120 = 2.58, which is above the T13 line. Both sides send the event, so test for a missing or mismatched event ID first. Without a test events capture, this finding stays `possible`.

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|
| Signup over-counted | `screenshot`, `crm_export` | `possible` | high | medium | measurement | Capture test events, then seek approval to align event IDs |

Hold bid changes on this event until a recount clears T13.

## Common failure modes

- Calling duplication `confirmed` from counts alone.
- Turning the match quality label into a number.
- Reading diagnostics warnings as proof.
- Comparing counts across different dates or timezones.
- Applying T10 to Meta.
- Treating Meta signups as paying customers.

## Route to next

Event definition: `signup-event-audit-saas-ads`. Tag firing: `gtm-container-review-saas-ads`. Consent: `consent-signal-loss-check-saas-ads`. Paid event path: `paid-event-import-check-saas-ads`. Billing gap: `ad-platform-vs-billing-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers. Mark gaps `needs_data`.
- End every output with an approval-ready recommendation.
- Never report a match quality score that Meta did not show.
- Never call duplication `confirmed` without a test events capture.
- Never recommend bidding on an event that fails T13 or T04.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
