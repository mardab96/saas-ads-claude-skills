# Copy-paste prompts

One prompt for each of the 25 skills. Run them in Claude Code after the documented install. Replace the bracketed parts, and attach the files or give an absolute path, such as `~/.claude/skills/saas-ads-shared/examples/data/cac_channels.csv`.

Helpers run from the skill's own folder. Each `SKILL.md` gives the command in this form, where `<skill-dir>` is the folder that holds that `SKILL.md`:

```text
python3 "<skill-dir>/../saas-ads-shared/scripts/cac.py" "<absolute path to your CSV>"
```

Quote every path, so folders with spaces still work. Remove names, emails, and phone numbers from every file before you attach it. If a prompt says "run the helper", the skill supplies the exact command. Money columns may carry commas and a currency symbol, fractions may be percents, date columns may carry a time, and files separated by semicolons are read as they are. Money written with a decimal comma ("1.200,50") needs the `--decimal-comma` flag, and a semicolon file with such a cell turns it on by itself.

Blank CSV templates for the helpers that read a file are in `saas-ads-shared/templates/`. The weekly routine is the last section, "Monday routine".

## Cost Per Paying Customer

```text
Use Cost Per Paying Customer for SaaS ads.
Attached: CSV with channel, spend, new_paying_customers for [dates], currency [USD].
Extra non-media cost for the period: [amount or none].
Unknown-source customers: [count or none]. I know about [sales-led deals or none].
Run the helper and return cost per paying customer per channel and blended, the volume labels, and what to check next. If a channel has fewer than 20 paying customers, use a 90-day window and pool same-platform, same-intent campaigns (small account mode), and say what is pooled.
```

## Trial To Paid By Campaign

```text
Use Trial To Paid By Campaign for SaaS ads.
Attached: CSV with campaign, signup_date, paid_date, one row per signup, and a spend CSV with campaign, spend.
Trial length: [days]. Export date: [YYYY-MM-DD]. Billing lag: [days].
Run the helper with --trial-days, --as-of, and --spend.
Return paid rate on matured signups per campaign, cost per signup and per paying customer, the immature count, and weak campaigns with the checks to run before any change.
```

## Ad Platform vs Billing Check

```text
Use Ad Platform vs Billing Check.
Attached: CSV with source, platform_reported, billing_count for the same dates, timezone [tz], event [name], window [setting].
Run the helper.
Return each source's label, the likeliest reasons in order, and what data would confirm them.
```

## Payback Period Check

```text
Use Payback Period Check.
Cost per paying customer: [amount]. Monthly revenue per account: [amount], or annual contract value: [amount]. Gross margin: [fraction]. Monthly churn: [fraction], or annual churn: [fraction].
Run the helper with those values.
Return simple and churn-adjusted payback, the T05 verdict, and which input to verify first. If churn is missing, say so and stop that finding.
```

## Scale Or Hold Decision

```text
Use Scale Or Hold Decision for [campaign].
Attached: outputs from Cost Per Paying Customer, Trial To Paid By Campaign, Ad Platform vs Billing Check, and Payback Period Check, plus a screenshot of the campaign's learning or bid status.
Proposed budget step: [percent]. Last budget change: [date].
Return the gate table, the first failed gate, and an approval-ready step or a hold with its prerequisite.
```

## Funnel Bottleneck Finder

```text
Use Funnel Bottleneck Finder.
Attached: counts for clicks, sessions, signups, activated accounts, and paying customers for [current dates] and [previous dates], same timezone.
Trial length: [days].
Return the one stage with the largest material drop under T19, the runner-up, the measurement check to run first, and the skill to route to.
```

## Signup Event Audit

```text
Use Signup Event Audit.
Attached: GA4 event list with key event marks, the signup success screen or response, GTM captures if any, and CRM signup counts for [dates].
Return whether signup, trial start, and activation are separate events, whether each fires once on success, and the event to CRM ratio against T20.
```

## Paid Event Import Check

```text
Use Paid Event Import Check.
Attached: a sample of 20 recent paying customers with order ID, signup and paid times, timezone, stored click IDs, and email hash yes or no (no raw emails), plus Google Ads import diagnostics and Meta Events Manager screenshots.
Return the click ID capture share against T11, the import path per platform, and what blocks paid-outcome bidding.
```

## Google Ads Conversion Audit

```text
Use Google Ads Conversion Audit.
Attached: screenshots of Goals, Conversions, Summary, the campaign list with conversion goals, and the change history for conversion settings.
Say which campaigns are Performance Max.
Return each action's role, duplicates, count setting questions, and which action each campaign bids on.
```

## Bid Target Picker

```text
Use Bid Target Picker.
Attached: conversions by action for [dates] with counts per 30 days, cost per paying customer [amount], average revenue per account [amount], gross margin [fraction], monthly churn [fraction].
Return the event to bid on under T17, the affordable cost under T21, and a target range with step size under T18.
```

## Meta Pixel And CAPI Check

```text
Use Meta Pixel And CAPI Check.
Attached: Events Manager screenshots (overview, event list with browser and server counts, diagnostics, test events), the backend signup count for the same dates.
Return duplicate risk against T13, missing server events, and what to test first.
```

## GTM Container Review

```text
Use GTM Container Review.
Attached: the exported container JSON (published version), the ad platforms in use, the signup success URL, and any tags hardcoded in the site source.
Return duplicate or paused tags, weak signup triggers, and an approval-ready change list with preview tests.
```

## Consent Signal Loss Check

```text
Use Consent Signal Loss Check.
Attached: daily Google Ads and Meta clicks, daily GA4 sessions by source and medium for [dates], the consent mode settings screenshot, and the dated banner change log.
Return the sessions-to-clicks ratio per source against T14, whether it fell near a banner change, and review items for the tag owner.
```

## UTM And Click ID Check

```text
Use UTM And Click ID Check.
Attached: 20 recent paid signup rows with source, medium, campaign, content, and click ID (no names or emails), the Google Ads tracking template and URL suffix, the Meta URL parameters, and the signup path with every redirect.
Return the share of rows with a source and a click ID, the first hop where values disappear, and approval-ready fixes.
```

## Attribution Window Fit

```text
Use Attribution Window Fit.
Attached: billing or CRM export with click date, signup date, and first payment date per customer, screenshots of each conversion window and Meta attribution setting, trial length [days].
Return days from click to first payment, the share paying later than each window against T15, and a window recommendation with a change date.
```

## Ad To Page Promise Match

```text
Use Ad To Page Promise Match.
Attached: exact ad text for [campaign], the targeting, the final URL, dated desktop and mobile full-page screenshots, and the page text as copied.
Offer terms: trial length [days], price [amount], card needed [yes or no].
Return a promise list marked match, changed, or absent, ranked mismatches, and a test for each.
```

## Landing Page Value Review

```text
Use Landing Page Value Review.
Attached: desktop and mobile full-page screenshots of [URL], the page text in order, the ad that sends traffic, a one-sentence product description, the proof I can show, and the main objection sales hears.
Return clarity, proof, and friction findings as hypotheses, with rewrites from supplied facts only.
```

## Signup Form Friction Review

```text
Use Signup Form Friction Review.
Attached: desktop and mobile screenshots from ad click to first product screen, the field list with required or optional, the verification step, and the card requirement.
Counts if I have them: form view [n], start [n], submit [n], verified [n].
Return required fields against T16, ranked cuts, and a test plan judged on matured paid rate.
```

## Pricing Page Review

```text
Use Pricing Page Review.
Attached: pricing page screenshots in each billing toggle state, the page text including FAQ, the plan list, the active ad terms, trial terms, and billing export of new paying customers by plan.
Gross margin: [fraction]. Cost per paying customer: [amount].
Return ad-to-page term gaps, the plan paid traffic actually buys, and owner questions. Do not recommend a price.
```

## Trial Or Demo Path Check

```text
Use Trial Or Demo Path Check.
Attached: the path from ad click to first value, CRM export per lead with campaign, created date, first contact date, stage dates, and outcome, the activation event, average revenue per account, and call capacity per week.
Return the largest delay, rates split by campaign, and one path test with a sample need.
```

## Search Term Intent Filter

```text
Use Search Term Intent Filter.
Attached: Google Ads search terms export for [dates] with term, match type, campaign, impressions, clicks, cost, conversions, and conversion action.
Target cost per signup: [amount]. What the product does not do: [list]. Brand terms: [list]. Conversion lag: [days]. Performance Max campaigns: [names or none].
Return intent classes, negative keyword candidates for approval with evidence, and spend listed as needs_data where term-level detail is missing.
```

## Brand vs Non-Brand Split

```text
Use Brand vs Non-Brand Split.
Attached: CSV with segment (brand or non_brand), spend, paying_customers. My brand terms: [list]. Competitor terms are labeled non_brand.
Run the helper.
Return cost per paying customer per segment, the T09 verdict, whether results rest on brand demand under T23, and what the blend hides.
```

## Meta Creative Fatigue Check

```text
Use Meta Creative Fatigue Check.
Attached: daily CSV with date, ad, impressions, clicks, frequency for at least 14 days.
Also: audience size, edits, budget changes, learning status.
Run the helper.
Return T07 labels, the frequency caveat, other explanations to rule out, a retained control ad, and an approval-ready refresh queue.
```

## Meta Downstream Quality Check

```text
Use Meta Downstream Quality Check.
Attached: Ads Manager ad-level export with spend, a CRM or billing export with signup date, paid date, and the stored ad name, and the match rule between utm_content and ad name.
Trial length: [days]. Export date: [YYYY-MM-DD].
Run the helper with --spend.
Return paid rate, cost per signup, and cost per paying customer per ad, unmatched signups, and keep, test, review calls for approval.
```

## Weekly SaaS Ads Readout

```text
Use Weekly SaaS Ads Readout.
Week: [dates]. Comparison: [dates]. Timezone: [tz]. Goal: [cost per paying customer or payback target].
Attached: Google Ads and Meta Ads exports, billing export of new paying customers by source, the change log, tracking notes.
Write a founder-ready or client-ready readout: scorecard, what changed, three actions with owners, and data gaps. Use small account mode when a source is below the T01 floor.
```

## Monday routine

One page, about thirty minutes. Pull the exports in this order, with the same dates, timezone, and currency for every file. Then paste one prompt.

1. Billing tool: new paying customers for last week and the week before, with signup date, first payment date, and the stored campaign. Remove names and emails.
2. CRM: signups or leads for the same two weeks, with source, campaign, and stage dates.
3. Google Ads: campaign table for both weeks (cost, clicks, conversions).
4. Meta Ads Manager: campaign table for both weeks, with the attribution setting visible.
5. Each platform's change history for the week.
6. Optional, once a month: churn by source, and two equal periods around your last budget change.

Then run this one prompt:

```text
Use Weekly SaaS Ads Readout for [account], week [dates], compared with [dates], timezone [tz], currency [USD].
Attached: the exports above in that order, and the change log.
First run Cost Per Paying Customer and Trial To Paid By Campaign on the attached files. Use small account mode for any channel under 20 paying customers.
Then write the readout: scorecard, tracking health, what changed, at most three actions with owners, and data gaps.
If I want more budget this week, stop and run Scale Or Hold Decision instead, using the optional files from item 6.
```
