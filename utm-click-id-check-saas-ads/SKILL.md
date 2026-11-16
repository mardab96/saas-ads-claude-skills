---
name: utm-click-id-check-saas-ads
description: Checks that every paid SaaS click from Google Ads and Meta ads arrives with consistent UTM tags and a click ID, and that those values survive signup and reach CRM and billing. Use when someone types "billing has no source", "UTMs are a mess", "gclid missing in CRM", or "marketing site to app domain loses params". Not for sending paid events back to the platforms; use paid-event-import-check-saas-ads.
---

# UTM And Click ID Check

## Use this skill when

Paid signups reach CRM or billing without a source, campaign, or click ID. This skill scores sample rows, traces parameters through the signup path, and names where values die.

Common requests:

- "Billing has no source for new customers."
- "UTMs are a mess."
- "gclid missing in CRM."
- "Marketing site to app domain loses params."

Send these jobs to another skill:

- Sending paid events back to the platforms: `paid-event-import-check-saas-ads`.
- Platform conversions versus billing customers: `ad-platform-vs-billing-check-saas-ads`.
- Form length and field friction: `signup-form-friction-review-saas-ads`.
- Tag triggers and container logic: `gtm-container-review-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- 20 recent paid signup rows from CRM or billing with source, medium, campaign, content, and click ID fields.
- Google Ads tracking template, final URL suffix, and auto-tagging status.
- Meta URL parameters for live ads.
- Signup path from marketing site to app, with every redirect.

### Optional

- Form hidden field names, CRM field mapping, and how billing links to the signup record.

Export route:

1. In CRM or billing, export the 20 most recent paid signups with attribution fields.
2. In Google Ads, copy auto-tagging status and URL options at account, campaign, and ad level.
3. In Meta Ads Manager, copy each live ad's URL parameters field.
4. Open a landing URL with test parameters and screenshot the address bar at each hop.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm every row came from a paid click. List and exclude organic or direct rows.
2. Score each row: UTM present, naming consistent (case, spelling, separators), campaign value matches a platform campaign name, click ID stored (T11).
3. Compute the share of rows with source, with a click ID, and with consistent naming. Compare the click ID share with T11.
4. Split failing rows by signup domain, form, and ad platform. A failure that follows one path marks a candidate break point.
5. Trace parameters hop by hop: redirect, cross-domain hop, form hidden fields, CRM field mapping, billing link to the signup record. Name the first hop where values disappear.
6. If auto-tagging and manual tags both exist, check that the tracking template, suffix, or URL parameters do not overwrite each other.
7. Write each fix as `approval_needed` with an owner and a retest step.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`. Verdicts and evidence tags follow `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Click ID share below T11 | `confirmed` capture gap | Find break point, then `paid-event-import-check-saas-ads` |
| Click ID share meets T11 | `monitor` | Recheck after site or form releases |
| Too few rows to show a pattern, or unclear paid origin | `needs_data` | Request a cleaner export |
| Screenshots show parameters vanish after a redirect or domain hop | `confirmed` | `gtm-container-review-saas-ads` |
| Parameters reach the form page, CRM fields empty | `likely` hidden field or mapping gap | `signup-form-friction-review-saas-ads` |
| One value in several spellings or cases | `confirmed` naming drift | Naming fix, `approval_needed` |
| Signup record tagged, billing record untagged | `likely` record link gap | `ad-platform-vs-billing-check-saas-ads` |
| Auto-tagging and manual tags set the same value | `possible` overwrite | Retest with screenshots |

Row scores come straight from the export and are `confirmed`. A break point needs a screenshot, page text, or mapping export; otherwise it stays `possible` or `likely`.

## Output format

```markdown
## UTM and click ID check: [account], [dates], [CRM or billing]
Rows: [n] | Auto-tagging: [on/off/unknown] | Path: [hops]

| Share | Rows | Percent |
|---|---|---|
| With source | | |
| With click ID (T11) | | |
| Consistent naming | | |

Break point: [hop, evidence tag]

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

Approval-ready fixes: [change, owner, retest]
Data gaps: [input, verdict it would firm up]
```

## Practical example

Illustrative numbers only, made up for this synthetic sample of 20 paid signup rows from CRM.

- Click ID: 11 of 20 rows, 55%, under the T11 line.
- Source: 11 of 20 rows, 55%.
- Naming: 8 of 11 tagged rows consistent, 73%. Three use "Google" where others use "google".

All 11 tagged rows signed up on the marketing site form. All 9 untagged rows signed up on the app domain. Screenshots show the query string present on the marketing site and empty after the hop. Cross-domain hop drops parameters: `confirmed` from `screenshot`, severity `high`, confidence `high`, impact `measurement`. Billing link was not supplied, so billing coverage is `needs_data`.

Fix, `approval_needed`: carry parameters across the hop into hidden form fields, then retest. Hold click ID import work until capture meets T11.

## Common failure modes

- Scoring organic or direct signups as paid rows.
- Treating a present `utm_source` as proof the click ID survived.
- Blaming the ad platform when a CRM field is unmapped.
- Naming a break point from row patterns without a test visit.

## Route to next

Click ID import: `paid-event-import-check-saas-ads`. Billing gaps: `ad-platform-vs-billing-check-saas-ads`. Form fields: `signup-form-friction-review-saas-ads`. Cross-domain tags: `gtm-container-review-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, row counts, or field names.
- End in an approval-ready recommendation with an owner and a retest step.
- Never edit tracking templates, URL parameters, or auto-tagging; describe the change for approval.
- Never mark a break point `confirmed` without a screenshot, page text, or mapping export.
- Never copy personal data from CRM rows into the output; cite rows by number.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
