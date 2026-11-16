---
name: google-ads-conversion-audit-saas-ads
description: Audits conversion actions in a SaaS Google Ads account, covering what each campaign bids on, primary versus secondary status, count setting, value, window, duplicates, and page-view actions that inflate results. Use when someone types "what is Google Ads optimizing for", "too many conversion actions", "conversions doubled overnight", or "are we counting signups or payments". Not for choosing the bid event; use bid-target-picker-saas-ads.
---

# Google Ads Conversion Audit

## Use this skill when

A buyer needs to know what Google Ads counts and what each campaign bids on. This skill lists every conversion action with its role and flags settings that inflate results.

Common requests:

- "What is Google Ads bidding on?"
- "Too many conversion actions. Which ones matter?"
- "Conversions doubled overnight, signups did not."
- "Are we counting signups or payments?"

Send these jobs to another skill:

- One signup event firing wrongly: `signup-event-audit-saas-ads`.
- Offline import errors or match rates: `paid-event-import-check-saas-ads`.
- Choosing the bid event: `bid-target-picker-saas-ads`.
- Meta Pixel or Conversions API: `meta-pixel-capi-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Conversions summary listing each action's category, primary or secondary status, count setting, value, window, and status.
- Conversion goals for each campaign, showing whether they are account default or campaign specific.
- Tag source per action: Google tag, GTM, GA4 import, or offline import.
- Change history for conversion settings over the audit window.
- Backend signups and billing-confirmed new paying customers for the same dates and timezone.

### Optional

- Days from click to paid.
- Daily conversions by action and daily clicks, for a spike.

Export route:

1. In Google Ads, open Goals, then Conversions, then Summary.
2. Include secondary and inactive actions, then download or screenshot the table.
3. Capture the Goals section of each campaign's settings.
4. Open Change history and export entries that touch conversions.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. List one row per action with source, role, count, value, window, status, and the campaigns using it. Primary actions feed bidding. Secondary actions only report.
2. Map each campaign to the primary actions it bids on. Campaign-specific goals override account defaults.
3. Flag primary page views and button clicks. They inflate conversions and pull bidding toward cheap actions.
4. Check that the paid or deepest valuable event is primary wherever it has T17 volume.
5. Check count settings. One suits signups and leads, and every suits repeat purchases. Mark mismatches as settings to verify.
6. Find the same event from two sources, such as a Google tag and a GA4 import. Test their combined count against backend signups with T20: a ratio above 1.20 points to double counting.
7. Check values and currency, then test each window against time to paid with T15.
8. Match count shifts to change history. A spike with no settings edit goes to T12 and T04 first.
9. Compare the bidding action with billing-confirmed paying customers using T04.
10. Performance Max and Advantage+ caveat: a Performance Max campaign bids on its campaign-level conversion goals, and asset or placement attribution is not visible in these exports. Report its bidding goal only. Meta Advantage+ campaigns are outside this skill, so route them to `meta-pixel-capi-check-saas-ads`.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels: `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Page view or click action is primary | `confirmed` | `approval_needed` to set secondary |
| Paid event meets T17 but is secondary | `likely` | `bid-target-picker-saas-ads` |
| Paid event below T17 | `needs_data` | Bid on the deepest event that meets T17 |
| Two sources for one event give a T20 ratio above 1.20 | `likely` | `gtm-container-review-saas-ads` |
| Count set to every on a signup | `possible` | Verify as a setting |
| Window fails T15 | `possible` | `attribution-window-fit-saas-ads` |
| Count shift matches a dated edit | `confirmed` | Restate trend from the edit date |
| Spike with no edit | `needs_data` | T12 and T04 checks, `signup-event-audit-saas-ads` |
| Performance Max campaign | `needs_data` for asset-level attribution | Report campaign-level goals only |
| Bidding action fails T04 | `possible` | `paid-event-import-check-saas-ads` |

A setting read from a screenshot is `confirmed`. A cause for a count move needs a dated entry or a tag capture.

## Output format

```markdown
## Conversion audit: [account], [currency], [timezone]
Window: [dates] | Evidence: [tags]

### Action inventory
| Action | Source | Role | Count | Value | Window | Status | Used by |
|---|---|---|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Settings to verify
[count, value, currency, window items]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative numbers only, made up for this example. One 30-day window shows 400 backend trial signups and 40 billing-confirmed new paying customers.

| Action | Source | Role | Count | Conv | Verdict |
|---|---|---|---|---|---|
| Trial signup | Google tag | Primary | One | 400 | `confirmed`, keep |
| sign_up | GA4 import | Primary | One | 380 | `likely` duplicate |
| Pricing page view | Google tag | Primary | Every | 2,950 | `approval_needed`, set secondary |
| Contact button click | GTM | Primary | Every | 610 | `approval_needed`, set secondary |
| Demo request | GTM | Secondary | One | 52 | `monitor` |
| Paid subscription | Offline import | Secondary | One | 38 | `likely` misplaced |

Primary actions report 4,340 conversions against 400 backend signups. Google tag and GA4 signups combine to 780, a ratio of 1.95 to backend, above the T20 line of 1.20. Paid subscription shows 38 against 40 billing customers, a ratio of 0.95, inside T04. It meets T17, so it goes to `bid-target-picker-saas-ads` as a primary candidate. Window fit stays `needs_data` until click-to-paid timing arrives.

## Common failure modes

- Reading the summary and missing campaign-specific goals.
- Counting secondary actions or page views as results.
- Treating a GA4 import and a Google tag signup as two signups.
- Calling a spike a gain before T12 and T04 are checked.
- Promoting the paid event without T17 volume.

## Route to next

Bid event choice: `bid-target-picker-saas-ads`. Offline paid import: `paid-event-import-check-saas-ads`. Signup firing: `signup-event-audit-saas-ads`. Window length: `attribution-window-fit-saas-ads`. Tag duplicates: `gtm-container-review-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent counts, values, or windows. Missing inputs stay `needs_data`.
- End in an approval-ready recommendation for a named human decision.
- Do not move an action between primary and secondary. Propose the move for approval.
- Do not call a duplicate confirmed until dates, timezone, and definitions match.
- Do not read a conversion spike as growth before the T12 and T04 checks.
- Do not report platform conversions as paying customers.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
