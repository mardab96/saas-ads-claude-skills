---
name: attribution-window-fit-saas-ads
description: Compares the click-attribution windows set in Google Ads and Meta Ads with the measured delay between click and first payment in a SaaS sales cycle, using matured cohorts only. Use when someone types "trial takes 3 weeks to convert, are we losing credit", "what attribution window should we use", "conversion window shorter than our sales cycle", or "Meta 7 day click versus our cycle". Not for choosing the bid event; use bid-target-picker-saas-ads.
---

# Attribution Window Fit

## Use this skill when

A SaaS buyer suspects the platform window closes before customers pay. This skill measures days from click to first payment per customer and compares that delay with each click window (T15). It returns a window recommendation and a measurement note.

Common requests:

- "Trial takes 3 weeks to convert. Are we losing credit?"
- "What attribution window should we use?"
- "Our conversion window is shorter than our sales cycle."
- "Meta 7 day click versus our cycle."

Send these jobs to another skill:

- Choosing a bid event from volume alone: `bid-target-picker-saas-ads`.
- Auditing Google Ads conversion actions and counting settings: `google-ads-conversion-audit-saas-ads`.
- Comparing platform conversions with billing counts: `ad-platform-vs-billing-check-saas-ads`.
- Checking whether offline paid events reach the platform: `paid-event-import-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Billing or CRM export, one row per recent customer, with click date (or first touch date), signup date, and first payment date.
- Screenshot of the conversion window and attribution setting for each Google Ads conversion action in scope.
- Screenshot of the attribution setting for each Meta Ads ad set in scope.
- Trial length in days.
- Reporting dates and timezone.

### Optional

- Source column per customer (Google Ads or Meta Ads), so each platform gets its own share.
- Counts of an earlier in-product event, such as activation, for the T17 check.
- Dated change log of past window or attribution edits.

Export route:

1. In the billing tool, export customers with first payment date for the reporting dates.
2. In the CRM, join each customer to the stored click date or first touch date.
3. In Google Ads, open Goals, then Conversions, then each action's settings, and screenshot the click-through window.
4. In Meta Ads Manager, open each ad set and screenshot its attribution setting.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. List each window by conversion action or ad set, tagged click or view. Set view-based windows aside, since they never enter a click comparison.
2. Keep only customers from matured signup cohorts (T02). Report younger signups as immature and exclude them.
3. Compute days from click to first payment per customer in one timezone. Flag rows that use first touch date as a proxy. Build a CSV with `click_date` and `paid_date` for paying customers only, then run once per click window in scope, for example 7 and 30 days. For a per-platform answer, use one file per platform:
   `python3 "<skill-dir>/../saas-ads-shared/scripts/lag.py" "<absolute path to your customers CSV>" --as-of <YYYY-MM-DD> --window-days 7`
4. Report customer count, `cohort_customers`, `median_click_to_paid_days`, `p80_click_to_paid_days`, and the share paying later than each click window (`T15_share_later`), per platform file when you split them. Quote the `censoring:` line. A file of paying customers makes recent clicks look faster than they are (right-censoring). For that reason the helper uses only clicks at least 90 days old for the percentiles and T15 (`--cohort-cutoff-days` changes the cut-off). Fewer than 20 such customers returns `needs_data`.
5. Compare each share with T15. `T15_verdict` in the helper output applies it: `window_too_short`, `window_fits`, or `needs_data` below 20 paying customers (T01). Label a `needs_data` share directional.
6. If a share exceeds T15, state that the window under-reports and bidding learns from partial data. Check T17 for a deeper earlier event that lands inside the window.
7. Write the recommendation: keep the window, lengthen it where the platform allows, or move bidding to an earlier event. Lengthening alone still leaves bidding slow to learn.
8. Write the measurement note. A window change alters reported counts only, and customer behavior stays unchanged. Record the planned change date so later readouts split before and after.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`.

Script contract for `lag.py`: columns `click_date` and `paid_date` for paying customers only, `--as-of`, optional `--window-days`, optional `--cohort-cutoff-days` (default 90), optional `--spend` (CSV with `month`, `spend`) and `--us-dates`. A paid date before the click or after `--as-of`, or a blank `paid_date`, exits with code 2, and so does a file with no click older than the cut-off. Output prints `customers`, `cohort_customers`, `median_click_to_paid_days`, `p80_click_to_paid_days`, a `censoring:` line, then the T15 lines with `--window-days`, and a cohort table with `--spend`.

| Pattern | Verdict | Next step |
|---|---|---|
| `T15_verdict: window_fits`, at least 20 paying customers | `monitor` | Keep window, re-run next reporting period |
| `T15_verdict: window_too_short` | `likely` window too short | Run T17 check |
| Share above T15, earlier event meets T17 | `approval_needed` | `bid-target-picker-saas-ads` with change-date note |
| Share above T15, no earlier event meets T17 | `hold` on bid event change | Keep current event, revisit when an event meets T17 |
| Cohort immature, or `T15_verdict: needs_data` | `needs_data` | Widen dates or wait for maturity |
| Window screenshot missing | `needs_data` | Request screenshot |
| Click and view windows mixed in one figure | `needs_data` | Separate by window type and recompute |
| Paid count inside window still short of billing | `possible` import gap | `paid-event-import-check-saas-ads`, `ad-platform-vs-billing-check-saas-ads` |

A share computed from a supplied export is `confirmed` arithmetic. A claim that bidding suffers stays `likely` until a controlled test exists.

## Output format

Labels and tags follow `../saas-ads-shared/references/output-standard.md`.

```markdown
## Attribution window fit: [account], [timezone]
Reporting dates: [dates] | Trial length: [days] | Matured customers: [n] | Immature excluded: [n]

### Windows in scope
| Platform | Action or ad set | Window type | Window length | Evidence |
|---|---|---|---|---|

### Delay result
| Platform | Customers | Median days | Later than window | Share | T15 result |
|---|---|---|---|---|---|

### Decision table
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### Window recommendation
[keep, lengthen, or earlier bid event per T17; approval owner]

### Measurement note
[reported counts shift on change date [date]; customer behavior unchanged]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative, made-up numbers. Trial length is 14 days. Google Ads paid action uses a 30-day click window. Meta ad sets use 7-day click. No source column was supplied, so shares are pooled.

Forty matured customers meet T02. Twelve paid more than 30 days after the click: 12 / 40 = 30%, above T15. Median delay is 19 days.

With 40 customers, a median of 19 means customers ranked 21 to 40 all paid on day 19 or later. So at least 20 of 40, or 50%, paid outside the Meta 7-day click window.

Findings: Google Ads window is `likely` too short, from `billing_export` and `screenshot`. Meta window is `likely` too short. Activation counts were missing, so T17 is `needs_data`. Recommendation: `hold` any bid event change, then route to `bid-target-picker-saas-ads` once activation counts arrive.

Run the helper on the synthetic sample `examples/data/lag_customers.csv` against a 7-day click window.

```text
customers:	231
cohort_customers:	144
median_click_to_paid_days:	5
p80_click_to_paid_days:	26
censoring:	lag percentiles and T15 use only clicks dated on or before 2026-08-18 (as-of minus 90 days), 144 of 231 customers. Recent clicks have had less time to pay, so counting them would understate the lag.
T15_window_days:	7
T15_later_than_window:	57 of 144
T15_share_later:	39.6%
T15_verdict:	window_too_short
read:	Lagged CAC divides spend by customers whose click fell in the same month. A month younger than the lag is not a result yet.
```

Here 57 of the 144 customers with a click at least 90 days old paid later than 7 days, 39.6%, above the T15 line of 20%. Newer clicks (87 customers) are left out, because customers who will still pay are not in the file yet. A p80 of 26 days means a 7-day click window loses credit for many paying customers.

## Common failure modes

- Including signups younger than T02, which shrinks measured delay.
- Mixing click-based and view-based windows in one share.
- Reading a higher count after a window change as better performance.
- Treating first touch date as click date without flagging it.
- Lengthening a window and skipping the T17 check.
- Pooling platforms and calling the result platform-specific.

## Route to next

Bid event choice: `bid-target-picker-saas-ads`. Conversion action settings: `google-ads-conversion-audit-saas-ads`. Platform against billing gap: `ad-platform-vs-billing-check-saas-ads`. Offline paid event delivery: `paid-event-import-check-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers. Missing inputs become `needs_data`.
- End in an approval-ready recommendation with a named owner.
- Never compare click-based and view-based windows in one figure.
- Never compute shares from immature cohorts.
- Always record the planned change date with any window recommendation.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
