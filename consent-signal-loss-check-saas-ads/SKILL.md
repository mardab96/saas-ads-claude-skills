---
name: consent-signal-loss-check-saas-ads
description: Estimates how much SaaS paid traffic may be invisible to measurement because of consent handling, by comparing Google Ads and Meta Ads clicks with GA4 sessions per source and reviewing consent settings and banner change dates. Use when someone types "GA4 sessions way below clicks", "conversions dropped after the cookie banner", "is consent mode set up", or "EU traffic does not convert in reports". Not for tag trigger problems; use gtm-container-review-saas-ads.
---

# Consent Signal Loss Check

## Use this skill when

Paid clicks and analytics sessions disagree, and the buyer needs to know how much of the gap consent handling may explain. This skill computes a sessions-to-clicks ratio per source, applies T14, and reviews consent settings. It produces review items. It does not produce a tracking rewrite or legal advice.

Common requests:

- "GA4 sessions are way below Google Ads clicks."
- "Conversions dropped after the cookie banner changed."
- "Is consent mode set up?"
- "EU traffic does not convert in reports."

Send these jobs to another skill:

- Tag triggers and firing order: `gtm-container-review-saas-ads`.
- Meta browser and server events: `meta-pixel-capi-check-saas-ads`.
- Platform conversions against billing: `ad-platform-vs-billing-check-saas-ads`.
- Missing UTMs or click IDs: `utm-click-id-check-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Daily ad clicks by campaign from Google Ads and Meta Ads. Use one click metric per platform throughout.
- Daily GA4 sessions by session source / medium for the same dates and timezone.
- Consent banner behavior, described or captured. Include what loads before a choice and what loads after a decline.
- Consent mode settings screenshot from GTM or the Google tag, showing the default state.
- Dated banner or CMP change log.

### Optional

- Clicks and sessions by country.
- Same ratio for earlier comparable windows.
- Daily primary signup event counts.

Export route:

1. In Google Ads, open Campaigns, segment by day, and download clicks.
2. In Meta Ads Manager, break down by day and export link clicks by campaign.
3. In GA4, open Traffic acquisition, show session source / medium by date, and export.
4. In GTM or the Google tag, screenshot the consent settings and default commands.

See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Confirm matched dates, matched timezones, and full days. If any of these differ, stop with `needs_data`.
2. Map each ad source to its GA4 source / medium row. Name any paid traffic that lands in unmapped rows.
3. Divide GA4 sessions by ad clicks per source, and per campaign where possible. Keep Google and Meta separate.
4. Compare each ratio with T14, then with its own history. Bots, accidental clicks, and slow pages explain part of any gap, so treat a stable low ratio as a baseline.
5. Split by country where consent rules differ. A gap concentrated in consent-required regions points at the banner.
6. Read the consent screenshot. Check that the default state is set before tags fire, that each signal is declared, and that an update is sent on choice.
7. Place banner change dates against the daily ratio and the primary event. Record whether a T12 drop starts near a change.
8. Quote modeled conversions only as the platform states them. Then write review items for the tag owner and the privacy owner.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels and tags: `../saas-ads-shared/references/output-standard.md`.

| Pattern | Verdict | Next step |
|---|---|---|
| Ratio under T14 and under its own history | `likely` consent or tagging loss | Country split, consent review |
| Ratio under T14, stable against history | `monitor` | Check page speed and click quality |
| Ratio under T14, no history supplied | `possible` | Request earlier windows |
| Ratio at or above T14 | `monitor` | No consent item |
| Gap concentrated in consent-required countries | `likely` banner effect | `gtm-container-review-saas-ads` |
| T12 drop starts near a dated banner change | `confirmed` date match, cause `likely` | Review item for tag owner |
| Default state missing or set after tags fire | `confirmed` from `screenshot` | `gtm-container-review-saas-ads` |
| Settings, change log, or matched dates missing | `needs_data` | Request inputs |
| Legal or privacy question | `hold` | Privacy owner |

## Output format

```markdown
## Consent signal check: [account], [timezone]
Window: [dates, n days] | Timezones matched: [yes/no] | Consent screenshot: [yes/no]

| Source | Clicks | GA4 sessions | Ratio | Prior ratio | Evidence tag |
|---|---|---|---|---|---|

Country split: [ratios or needs_data]
Consent settings: [default, signals, timing, banner behavior, change dates]

| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

Review items: [ordered, owner, approval_needed]
Data gaps: [missing input and the verdict it would firm up]
```

## Practical example

Illustrative, made-up numbers for one matched window.

| Source | Clicks | GA4 sessions | Ratio |
|---|---|---|---|
| Google Ads | 4,200 | 2,646 | 63.0% |
| Meta Ads | 3,000 | 2,400 | 80.0% |
| Blended | 7,200 | 5,046 | 70.1% |

Google sits under the T14 line of 70%. Meta sits above it. Blending gives 70.1%, which would hide the Google gap. Google leaves 1,554 clicks without a session, and Meta leaves 600.

No prior ratios were supplied. Google consent loss is therefore `possible`, with medium severity and `measurement` impact. Next step: request history, a country split, and the consent screenshot.

## Common failure modes

- Reading every missing session as consent loss.
- Blending sources, which hides one platform's gap.
- Judging a ratio without its own history.
- Naming a banner change as the cause from a date alone.
- Estimating modeled conversions instead of quoting the platform.

## Route to next

Consent defaults and tag timing: `gtm-container-review-saas-ads`. Meta event loss: `meta-pixel-capi-check-saas-ads`. Platform against billing: `ad-platform-vs-billing-check-saas-ads`. Session-to-signup drop: `funnel-bottleneck-finder-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers. Missing inputs become `needs_data`.
- End every run in an approval-ready recommendation.
- Never give legal advice. Refer privacy questions to the privacy owner.
- Output review items only, never a rewritten tag or consent setup.
- Never assign the whole click-session gap to consent without history and a country split.
- Never describe modeled conversions beyond what the platform states.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
