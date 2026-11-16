---
name: search-term-intent-filter-saas-ads
description: Classifies a Google Ads search terms export for a SaaS product into buyer intent, alternatives research, existing customers, learning or free-seekers, and irrelevant, then lists negative keyword candidates with evidence for approval. Use when someone types "clean search terms", "what should I add as negatives", "junk traffic in search", or "which search terms waste money". Not for brand-heavy budget questions; use brand-nonbrand-split-saas-ads.
---

# Search Term Intent Filter

## Use this skill when

Search spend needs sorting by intent before anyone adds negatives. This skill gives each term an intent class with a one-line reason and separates brand terms. It applies T08 to find waste candidates and returns negative keyword candidates for approval. It never adds them.

Common requests:

- "Clean search terms for last month."
- "What should I add as negatives?"
- "There is junk traffic in search. Where is it coming from?"
- "Which search terms waste money?"
- "Are the free and template searches worth keeping?"

Send these jobs to another skill:

- Brand terms taking budget, or brand versus non-brand reporting: `brand-nonbrand-split-saas-ads`.
- Checking which conversion action counts a signup: `google-ads-conversion-audit-saas-ads`.
- Checking whether the ad promise matches the landing page: `ad-to-page-promise-match-saas-ads`.
- Cost per paying customer by channel: `cost-per-paying-customer-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Search terms export with term, match type, campaign, impressions, clicks, cost, conversions, and conversion action.
- Target cost per signup and currency.
- Product category, plus what the product does not do (for example no free plan, no on-premise version, industries it does not serve).
- Own brand terms and competitor names.
- Conversion lag in days, from click to signup.
- Which campaigns are Performance Max, since their term-level detail is limited.

### Optional

- Billing export or CRM export with paid status per signup, keyed to campaign or search term.
- Current negative keyword lists and the campaigns they cover.
- Trial length.

Export route:

1. Open Google Ads and select the search campaigns.
2. Open the search terms report.
3. Set a date range that ends at least one conversion lag before today.
4. Add the columns above and segment by conversion action.
5. Download as CSV. Export shared negative lists from the shared library.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm dates, currency, and conversion lag. Exclude days inside the lag from waste checks. If the lag is unknown, mark every T08 check `needs_data`. Performance Max and Advantage+ caveat: Performance Max reports search terms in a limited form that differs from a Search campaign export, and Meta Advantage+ has no search terms. List that spend as `needs_data` for term-level findings and draft no negatives from it.
2. Confirm which conversion action counts a signup. Split out demo requests, newsletter signups, or other actions before reading conversions.
3. Tag brand terms from the supplied list and move them to a brand block. Any brand negative for non-brand campaigns is decided in `brand-nonbrand-split-saas-ads`.
4. Classify each non-brand term into one class with a one-line reason: buyer intent, alternatives research, existing customers, learning or free-seekers, or irrelevant.
5. Check these SaaS patterns: free, open source, template, tutorial, jobs, login or support, student, competitor alternatives, integration questions, and wrong audience. Compare each term with the list of what the product does not do.
6. Apply T08 to every term after the lag. Terms that meet T08 become waste candidates. Terms below the T08 floor, and terms inside the lag, return `needs_data`, whatever their class.
7. For terms with conversions, check billing outcomes under T02 before calling any term good. Cheap signups from a free-seeking term often do not pay. Without billing or CRM data, mark `needs_data`.
8. Draft each negative candidate with exact text, match type, scope (one campaign or a shared list), and evidence row. Confirm it would not block a buyer intent term in the same export.
9. Fill the decision table, list unclassified terms with reasons, and stop at approval.

## Decision rules

Thresholds come from `../saas-ads-shared/references/thresholds.md`. Verdicts and evidence tags follow `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Irrelevant, wrong-audience, or jobs term meets T08 | `approval_needed` | Negative candidate |
| Free, open source, template, tutorial, or student term meets T08 | `approval_needed` | Negative candidate, checked against "free trial" buyer terms |
| Existing customer term (login, support) meets T08 | `approval_needed` | Negative candidate in non-brand campaigns only |
| Any term below T08 floor or inside the lag | `needs_data` | Re-run after the lag clears or the clicks build |
| Converting term, no billing or CRM data | `needs_data` | `cost-per-paying-customer-saas-ads` |
| Converting term, cohort immature or below T02 volume | `needs_data` | Wait for matured signups |
| Converting term, matured T02 cohort with paying customers | `confirmed` | Keep, no negative |
| Buyer intent term meets T08 | `possible` | `ad-to-page-promise-match-saas-ads` before any negative |
| Conversions logged on an unexpected action | `needs_data` | `google-ads-conversion-audit-saas-ads` |
| Brand term | `monitor` | `brand-nonbrand-split-saas-ads` |
| Spend in Performance Max or Advantage+ | `needs_data` for term-level findings | Report it as its own line, with no negative candidates |

| Negative situation | Match type | Scope |
|---|---|---|
| One query, no repeating modifier | exact | campaign |
| Modifier repeats across campaigns (jobs, student) | phrase | shared list |
| Word never fits the product in any order | broad | shared list, after a buyer term check |

## Output format

```markdown
## Search term intent review: [account or campaigns], [currency]
Dates: [start to end] | Lag: [days], cleared [yes/no] | Target cost per signup: [value] | Signup action: [name]

### Term classes
| Term | Campaign | Class | Reason | Clicks | Cost | Signups | T08 met | Evidence tag |
|---|---|---|---|---|---|---|---|---|

### Brand block (for brand-nonbrand-split-saas-ads)
[brand terms with clicks, cost, signups]

### Negative keyword candidates (not applied)
| Text | Match type | Scope | Evidence row | Buyer terms checked |
|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Data gaps
[missing billing data, lag, conversion action, and the verdict each would firm up]
```

## Practical example

Illustrative, made-up numbers. A team scheduling SaaS with no free plan. Target cost per signup 40 USD, lag 7 days and cleared. T08 floor here: at least 30 clicks, zero signups, and cost at least 80 USD, which is twice the target.

| Term | Campaign | Class | Reason | Clicks | Cost | Signups | T08 met | Evidence tag |
|---|---|---|---|---|---|---|---|---|
| team scheduling software | nonbrand_search | buyer intent | category plus "software" | 120 | 360.00 | 9 | no, has signups | `ads_export` |
| [competitor] alternative | nonbrand_search | alternatives research | comparing a named competitor | 45 | 180.00 | 2 | no, has signups | `ads_export` |
| [own brand] login | brand_search | brand, existing customers | on brand list, moved to brand block | 60 | 30.00 | 0 | not tested, brand block | `ads_export` |
| free scheduling app | nonbrand_search | free-seekers | product has no free plan | 52 | 104.00 | 0 | yes | `ads_export` |
| shift schedule template printable | nonbrand_search | learning or free-seekers | wants a template | 38 | 95.00 | 0 | yes | `ads_export` |
| scheduler jobs remote | nonbrand_search | irrelevant | job search | 34 | 61.20 | 0 | no, cost under 80 | `ads_export` |
| how to make a staff rota | nonbrand_search | learning | tutorial intent | 22 | 33.00 | 0 | no, under 30 clicks | `ads_export` |
| scheduling api integration | nonbrand_search | buyer intent | integration question | 15 | 48.00 | 1 | no, has a signup | `ads_export` |

Negative candidates, both `approval_needed`:

| Text | Match type | Scope | Evidence row | Buyer terms checked |
|---|---|---|---|---|
| free scheduling app | exact | campaign | 52 clicks, zero signups, 104.00 USD | "free trial" terms checked first |
| shift schedule template printable | exact | campaign | 38 clicks, zero signups, 95.00 USD | no buyer term contains "template" |

Together the two candidates cost 104.00 + 95.00 = 199.00 USD. Each is one query with no repeating modifier, so exact match at campaign scope applies. "scheduler jobs remote" returns `needs_data` because 61.20 USD is under 80 USD. "how to make a staff rota" returns `needs_data` at 22 clicks. "team scheduling software" costs 40.00 USD per signup, but its paid status is `needs_data` until billing data arrives.

## Common failure modes

- Calling a converting term good before checking billing outcomes under T02.
- Flagging waste inside the conversion lag.
- Adding a broad "free" negative that blocks "free trial" buyer searches.
- Negating competitor alternative terms that bring paying customers.
- Mixing brand terms into non-brand totals.
- Treating Performance Max spend as if it came with Search term rows.
- Reading demo or newsletter conversions as signups.

## Route to next

Brand terms: `brand-nonbrand-split-saas-ads`. Conversion action questions: `google-ads-conversion-audit-saas-ads`. Buyer intent terms with no signups: `ad-to-page-promise-match-saas-ads`. Paid outcome by term or campaign: `cost-per-paying-customer-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, terms, or billing outcomes.
- End in an approval-ready recommendation for a named human.
- Never add a negative keyword; list candidates only.
- Never flag waste outside T08 or inside the conversion lag.
- Never decide brand negatives here; route them to `brand-nonbrand-split-saas-ads`.
- Never call a converting term good without billing evidence under T02.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
