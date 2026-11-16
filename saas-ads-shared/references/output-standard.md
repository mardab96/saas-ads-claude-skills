# Output standard

Every output separates supplied evidence from an explanation. A missing export, screenshot, or setting becomes `needs_data`; it never becomes a made-up fact.

## Evidence tags

- `ads_export`
- `search_terms_export`
- `billing_export`
- `crm_export`
- `analytics_export`
- `tag_export`
- `screenshot`
- `page_text`
- `change_log`
- `hypothesis`
- `needs_data`

## Verdict vocabulary

Use only these labels for a finding or recommendation:

| Label | Meaning |
|---|---|
| `confirmed` | Direct supplied evidence establishes the finding. |
| `likely` | The pattern fits and stronger alternatives were checked, but no direct confirmation exists. |
| `possible` | The pattern is compatible with more than one explanation. |
| `needs_data` | A required source, setting, date range, or denominator is missing. |
| `monitor` | The evidence is mature enough to watch, but does not justify an action. |
| `hold` | Do not advance a live change until a stated prerequisite is met. |
| `approval_needed` | The recommendation is ready for a named human decision. |

Severity is `low`, `medium`, `high`, or `critical`. Confidence is `low`, `medium`, or `high`. Business impact is `spend`, `signups`, `paying_customers`, `revenue`, `profit`, `measurement`, or `client_trust`.

## Required decision table

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

## Failure modes

Reject an output that treats platform conversions as paying customers, calls tracking broken from cost alone, counts trial signups that have not had time to convert, compares unmatched reporting sources, uses revenue where gross margin belongs, or promises a live result. Recommendations stop at an approval-ready action.
