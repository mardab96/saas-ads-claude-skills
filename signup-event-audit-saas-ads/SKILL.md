---
name: signup-event-audit-saas-ads
description: Audits whether the SaaS signup and trial-start events that Google Ads and Meta count are defined, fired once, and named consistently in GA4 and the product, then checks the count against CRM signups. Use when someone types "is our signup event firing", "sign_up counted twice in GA4", "GA4 key event setup", "signup events look inflated against the CRM", or "are trial starts and signups the same event". Not for container hygiene; use gtm-container-review-saas-ads.
---

# Signup Event Audit

## Use this skill when

A buyer needs to know whether the signup count feeding Google Ads and Meta reflects real account creation. This skill defines the success moment, traces each firing path, and checks names, parameters, and key event marks against CRM signups.

Common requests:

- "Is our signup event firing?"
- "sign_up is counted twice in GA4."
- "Can you check our GA4 key event setup?"
- "Signup events look inflated against the CRM."
- "Are trial start and signup the same event?"

Send these jobs to another skill:

- Container hygiene beyond signup tags: `gtm-container-review-saas-ads`.
- Google Ads conversion action settings and goals: `google-ads-conversion-audit-saas-ads`.
- Meta Pixel and Conversions API deduplication: `meta-pixel-capi-check-saas-ads`.
- Offline paid event uploads: `paid-event-import-check-saas-ads`.
- Platform conversions against paying customers: `ad-platform-vs-billing-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- GTM container export (JSON), or screenshots of every tag and trigger that touches signup.
- GA4 event list and key event screenshot.
- GA4 DebugView or Tag Assistant capture of one real signup, start to finish.
- Signup flow in steps: form, email verify, first product screen.
- Event names the business treats as primary, plus the names imported into Google Ads and Meta.

### Optional

- CRM signup count by day for the same dates, with timezone stated.
- Page source showing any hardcoded tracking snippet.
- Click counts for comparable windows, for a drop check.

Export route:

1. In GTM, open Admin, choose Export Container, and save the JSON.
2. In GA4, open Admin, then Events and Key events, and screenshot both lists.
3. Open DebugView or Tag Assistant, complete one real signup, and capture every event in order.
4. Pull CRM signups for matching dates and timezone.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Define the success moment in writing: account created, never form viewed or button clicked. Record which screen or server response proves it.
2. List every tag that sends a signup or trial event, with trigger type and firing page.
3. Read the capture. Count how often each signup event fires for one signup, and at which step.
4. Confirm the event fires on success. A trigger on submit click also counts failed and abandoned attempts.
5. Check parameters on the event, at least plan and signup method.
6. Search page source and GTM for each event name. A hardcoded snippet plus a GTM tag sending one name is a double count risk, and container cleanup goes to `gtm-container-review-saas-ads`.
7. Confirm signup, trial start, and activated are separate events with separate names.
8. Check key event marking in GA4. Match event names, case included, against Google Ads and Meta imports.
9. Compare event count with CRM signups for the same dates. Apply T20: trace the firing paths when the ratio is above 1.20 or below 0.80. Apply T12 when the event drops while clicks hold.
10. Fill the decision table and write an ordered fix list for approval.

## Decision rules

Threshold values live in `../saas-ads-shared/references/thresholds.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| More than one fire per signup in the capture | `confirmed` | Remove one path, `gtm-container-review-saas-ads` |
| Trigger on click or submit with no success check | `confirmed` | Move trigger to success screen or server response |
| Snippet and GTM tag send one name | `likely` until a capture shows both fires | `gtm-container-review-saas-ads` |
| Event to CRM ratio outside the T20 range | `possible` | Trace firing paths before naming a cause |
| Event drop meets T12 while clicks hold | `possible` | Check releases and tag edits, `google-ads-conversion-audit-saas-ads` |
| GA4 name differs from imported name | `confirmed` | `google-ads-conversion-audit-saas-ads` or `meta-pixel-capi-check-saas-ads` |
| Signup and trial start share one event | `confirmed` | Split events before any bid target change |
| Wrong event marked as key event | `confirmed` | Correct marking, `approval_needed` |
| No signup capture supplied | `needs_data` | Request one real signup capture |
| Only ad cost moved | `needs_data` | Request event and CRM counts, make no tracking claim |

Every fix ends as `approval_needed` for a named owner. Bid or import edits that rely on an unverified event stay `hold`.

## Output format

Use labels and tags from `../saas-ads-shared/references/output-standard.md`.

```markdown
## Signup event audit: [site], [timezone], [dates]
Success moment: [definition] | Primary events: [names] | Capture: [DebugView or Tag Assistant]

### Firing paths
| Event | Tag | Trigger | Fires per signup | Parameters | Key event | Imported as |
|---|---|---|---|---|---|---|

### Count check
Event count: [n] | CRM signups: [n] | Ratio: [x] | T20 read: [label] | T12 read: [label]

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Ordered fixes and holds
[fix order, owner, prerequisite for each hold]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative findings with made-up numbers. Over seven days GA4 recorded 240 `sign_up` events and the CRM recorded 120 signups. 240 divided by 120 gives a ratio of 2.00, above the T20 line of 1.20, so the firing paths need tracing.

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|
| `sign_up` fires on Create account click and again on /welcome | `screenshot` (DebugView capture) | `confirmed` | high | high | measurement | Remove click trigger, keep success trigger, `approval_needed` |
| Double fire explains the 2.00 ratio | `analytics_export`, `crm_export` | `likely` | high | medium | measurement | Re-count one week after fix |
| `trial_start` lacks a plan parameter | `screenshot` | `confirmed` | medium | high | measurement | Add parameter, `approval_needed` |
| Google Ads imports `sign_up` as primary | `needs_data` | `hold` | high | low | spend | Hold bid target edits, `google-ads-conversion-audit-saas-ads` |

## Common failure modes

- Treating a form submit as an account creation.
- Calling tracking broken from ad cost alone.
- Reading an event to CRM ratio as truth. It flags where to look.
- Merging signup, trial start, and activated into one event.
- Checking GA4 names without checking the names Google Ads and Meta import.
- Testing with a fake form fill that never creates an account.
- Comparing counts across mismatched dates or timezones.

## Route to next

Container cleanup: `gtm-container-review-saas-ads`. Google Ads conversion actions: `google-ads-conversion-audit-saas-ads`. Meta browser and server events: `meta-pixel-capi-check-saas-ads`. Paid event uploads: `paid-event-import-check-saas-ads`. Platform against billing: `ad-platform-vs-billing-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent counts, ratios, or event names. Mark gaps `needs_data`.
- End in an approval-ready recommendation with a named owner.
- Never confirm a double fire without a capture of one real signup.
- Never call tracking broken from ad cost alone.
- Never approve bid target changes on an event that fires before account creation.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
