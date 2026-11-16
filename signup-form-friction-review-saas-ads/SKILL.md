---
name: signup-form-friction-review-saas-ads
description: Reviews a SaaS signup or trial form and the steps after it for fields, verification, and card requests that block paid-click visitors, then ranks cuts and a test plan. Use when someone says "signup form too long", "people start but do not finish the trial form", "do we need a card", or "work email requirement". Not for choosing demo versus trial; use trial-or-demo-path-check-saas-ads.
---

# Signup Form Friction Review

## Use this skill when

Paid clicks reach the signup form and too few become accounts. This skill counts required fields against T16, checks how each field is used in the first week, and finds the largest relative step drop. It ranks cuts and plans a test. It edits nothing.

Common requests:

- "Our signup form is too long. What can we cut?"
- "People start but do not finish the trial form."
- "Do we need a card to start the trial?"
- "Is the work email requirement costing signups?"

Send these jobs to another skill:

- Choosing between a trial and a demo path: `trial-or-demo-path-check-saas-ads`.
- Page message before the form: `landing-page-value-review-saas-ads`.
- Click IDs lost at submit: `utm-click-id-check-saas-ads`.
- Signup event firing: `signup-event-audit-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Desktop and mobile screenshots of every screen from ad click to first product screen.
- Field list, with each field marked required or optional.
- Verification step, and whether access waits on it.
- Card requirement, and the step where it appears.

### Optional

- Counts for form view, form start, form submit, and verified account, all for the same dates and timezone.
- Owner notes on which fields are used in the first week.
- Signups with signup date and paid status, for T02.

Export route:

1. In analytics, filter to paid traffic.
2. Export daily counts for each form step.
3. From billing, export signups with paid status.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Map each screen from click to first product screen and tag it `screenshot`.
2. Count required fields before the first product screen, including required checkboxes. Compare the count with T16.
3. Record who uses each field in the first week. A field with no user is a cut candidate, tagged `hypothesis` until the owner confirms.
4. Review email verification before access, password rules, social login, phone, card, company size questions, and work email blocks.
5. Trigger error states on desktop and mobile. Check that each message names the field and that entries survive. Check that email and phone fields open the right keyboard.
6. If step counts exist, compute relative drop as one minus the next count divided by the current count. Name the step with the largest drop.
7. Rank cuts by first-week use, position at that drop, and risk to lead quality.
8. Draft a test plan. Shorter forms can raise signups and lower paid rate, so judge the test on matured paid rate per T02.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Verdicts and tags: `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Required fields above T16 | `confirmed` | Rank cuts by first-week use |
| Field with no named first-week use | `likely` cut candidate | Confirm with owner |
| Access waits on verification, or card required | `possible` friction | Test it, judged on T02 paid rate |
| Largest relative drop at a step with friction | `likely` bottleneck | Test that step first |
| Error state clears entries or names no field | `confirmed` | Report as a fix ahead of field tests |
| No step counts supplied | `needs_data` | Rank from field review only |
| Signups up, paid cohort immature under T02 | `hold` | Wait for maturity |
| Test plan with named owner | `approval_needed` | Hand to form owner |

## Output format

```markdown
## Signup form review: [product], [dates], [timezone]
Screens: [n] | Required fields: [n] vs T16 | Card: [none/optional/required] | Verification: [before/after access]

### Field inventory
| Screen | Field | Required | First-week use | Evidence tag |
|---|---|---|---|---|

### Step drop
| Step | Count | Relative drop |
|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Ranked cuts and test plan
[field, reason, risk; primary metric matured paid rate per T02; approval owner]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative, made-up numbers. A trial form has 8 required fields: work email, password, first name, last name, company name, company size, phone, and role. T16 flags more than 5, so the count is `confirmed` above it.

Counts: view 2,000, start 1,200, submit 540, verified 405. Relative drops: view to start 40%, start to submit 55%, submit to verified 25%. Start to submit is the largest drop, and that is where the fields sit.

Owner notes give no first-week use for phone, company size, or role, so these are the 3 cut candidates. Phone ranks first because the mobile screenshot shows a text keyboard on it. Cutting all 3 leaves 5 fields, within T16.

Test: current form as control, 3 fields removed in the variant, judged on matured paid rate per T02. Verdict: `approval_needed` for the form owner. No result is claimed.

## Common failure modes

- Declaring a win on signup lift before T02 maturity.
- Reviewing desktop only when mobile adds screens.
- Cutting a field that sales or billing uses in week one.
- Comparing step counts across different dates or traffic filters.
- Blaming the form when lost click IDs leave signups uncounted.

## Route to next

Trial versus demo: `trial-or-demo-path-check-saas-ads`. Page before the form: `landing-page-value-review-saas-ads`. Click ID capture: `utm-click-id-check-saas-ads`. Paid rate after a test: `trial-to-paid-by-campaign-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent field usage, step counts, or results. Missing inputs become `needs_data`.
- End in an approval-ready recommendation for a named owner.
- Do not treat a signup lift as a paying customer lift.
- Do not remove a field with a named first-week use without owner sign-off.
- Do not bundle card and field changes in one variant, since their effects cannot be separated.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
