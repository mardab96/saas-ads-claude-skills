---
name: meta-creative-fatigue-check-saas-ads
description: Flags SaaS Meta ads whose frequency rose and CTR fell between two full 7-day windows with the fatigue.py helper, then checks saturation, learning resets, budget, seasonality, and downstream quality before suggesting a refresh. Use when someone types "is this creative tired", "CTR dropped on Meta", "frequency is climbing", or "when do I refresh ads". Not for signup quality by ad; use meta-downstream-quality-saas-ads.
---

# Meta Creative Fatigue Check

## Use this skill when

A SaaS team suspects a Meta ad has worn out. This skill applies T07 to each ad and then tests other explanations before any refresh. A `fatigue_candidate` label opens a review and never proves the cause.

Common requests:

- "Is this creative tired?"
- "CTR dropped on Meta. Is it the ad?"
- "Frequency is climbing on our trial campaign."
- "When do I refresh ads?"

Send these jobs to another skill:

- Pixel or Conversions API setup: `meta-pixel-capi-check-saas-ads`.
- Lead or trial quality: `meta-downstream-quality-saas-ads`.
- Click to paid drop-off: `funnel-bottleneck-finder-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Daily CSV with `date`, `ad`, `impressions`, `clicks`, `frequency`. Use one row per ad per day, ISO dates, and at least 14 days ending on the latest date.
- Edit history, budget changes, and learning status for those days.

### Optional

- Audience size per ad set.
- Seasonality notes such as launches, holidays, or price changes.
- Signups or trials per ad for both windows.

Export route:

1. In Meta Ads Manager, open Ads, pick the last 14 full days, and choose Breakdown, By Time, Day.
2. Add impressions, one click column, and frequency. Export CSV and rename headers to the five required names.
3. Screenshot Activity history for the same dates.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm 14 complete days, no partial day, and one click column throughout.
2. Run `python3 "<skill-dir>/../saas-ads-shared/scripts/fatigue.py" "<absolute path to your CSV>"`.
3. Record window dates and labels. Log each `insufficient_window` ad as `needs_data`. Frequency caveat: daily-row frequency near 1.0 to 1.2 is normal, so a 25% rise on that base is small in absolute terms. Read the helper's `note:` line and confirm any candidate with window-level frequency in Ads Manager before acting.
4. Saturation: if every ad in an ad set gains frequency against a small audience, suspect reach limits.
5. Learning: an edit inside either window may have reset learning (T06), which can move CTR without creative decay.
6. Budget and seasonality: a budget change or an account-wide CTR drop points away from one creative.
7. Peers and downstream: check whether ad set peers held, then check signups per ad with `meta-downstream-quality-saas-ads`.
8. Queue refreshes, keep one control ad live, and mark each item `approval_needed`.

## Decision rules

Thresholds live in `../saas-ads-shared/references/thresholds.md`.

Script contract: one argument, the CSV path, with columns `date`, `ad`, `impressions`, `clicks`, `frequency`. Dates may be ISO days or timestamps. Duplicate ad and date rows, blanks, or NaN exit with code 2. An ad missing any of the 14 days, or under T07 impressions in either window, prints `insufficient_window`. Others print `fatigue_candidate` or `no_signal`. Window frequency is an impressions-weighted approximation.

| Label | Verdict | Next step |
|---|---|---|
| `fatigue_candidate` | `possible` | Workflow steps 4 to 7 |
| `no_signal` | `monitor` | Re-run next week |
| `insufficient_window` | `needs_data` | Collect full days or wait for volume |
| Exit code 2 | `needs_data` | Fix duplicates, blanks, or NaN |

| Pattern with a candidate | Verdict | Next step |
|---|---|---|
| Edit inside a window (T06) | `hold` | Re-run once learning clears |
| Budget change inside a window | `possible` | Re-run on post-change windows |
| Whole ad set rising, small audience | `likely` saturation | Audience review, `approval_needed` |
| Isolated to one ad, no edit or budget change | `likely` fatigue | Refresh queue, `approval_needed` |
| CTR down, signups steady | `monitor` | `meta-downstream-quality-saas-ads` |

Arithmetic is `confirmed`. A cause needs a dated edit, budget log, or downstream export. Without one it stays `possible` or `likely`.

## Output format

Follow `../saas-ads-shared/references/output-standard.md`.

```markdown
## Meta fatigue check: [account], [timezone]
Windows: [prior dates] | [recent dates] | Click column: [name]
Command run: [exact command]
Script output: [pasted text]

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

Refresh queue (approval_needed): [ad, reason, control ad, approver]
Data gaps: [missing input, verdict it would firm up]
```

## Practical example

Illustrative only. These numbers are made up and come from the synthetic sample `examples/data/fatigue_daily.csv`, saved as `daily.csv`.

```text
python3 "<skill-dir>/../saas-ads-shared/scripts/fatigue.py" "<absolute path to your CSV>"
windows:	prior 2026-11-02..2026-11-08	recent 2026-11-09..2026-11-15
ad	prior_impr	recent_impr	prior_ctr	recent_ctr	prior_freq	recent_freq	T07_label
Small angle	2386	2267	1.30%	1.32%	1.08	1.12	insufficient_window
Steady angle	8748	8074	1.26%	1.25%	1.14	1.19	no_signal
Tired angle	7886	7790	1.23%	0.90%	1.11	1.45	fatigue_candidate
Thin angle	-	-	-	-	-	-	insufficient_window
```

Tired angle: frequency rose from 1.11 to 1.45, up 30.6%. CTR fell from 1.23% to 0.90%, down 26.8%. Both pass T07, which needs a frequency rise of at least 25% and a CTR fall of at least 20%. Small angle is `needs_data` because its impressions sit under the T07 floor in both windows. Thin angle is `needs_data` because it is missing days. Steady angle rose 4.4% in frequency with flat CTR.

Per the helper's note, frequency near 1.1 is normal, so the 30.6% rise is small in absolute terms and needs window-level frequency from Ads Manager before anyone acts.

These moves are `confirmed` arithmetic (`ads_export`). Fatigue stays `possible` until edit history, budget log, and signups arrive. If none explain it, Tired angle goes to the refresh queue as `approval_needed`, with Steady angle as control.

## Common failure modes

- Treating `fatigue_candidate` as proof.
- Reading weighted frequency as exact reach-based frequency.
- Missing a T06 learning reset from an edit inside a window.
- Blaming one creative for an account-wide CTR drop.
- Refreshing every ad at once and losing the control.

## Route to next

Downstream quality: `meta-downstream-quality-saas-ads`. Budget after a refresh: `scale-or-hold-decision-saas-ads`. Ad and page message: `ad-to-page-promise-match-saas-ads`. Click to paid drop-off: `funnel-bottleneck-finder-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, audience sizes, or edit dates.
- End in an approval-ready recommendation. Every refresh is `approval_needed`.
- Do not call fatigue `likely` before checking saturation, T06 edits, budget, and seasonality.
- Keep at least one control ad running through any refresh.
- Do not diagnose an `insufficient_window` ad.
- Do not treat a CTR drop as lost paying customers without downstream data.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
