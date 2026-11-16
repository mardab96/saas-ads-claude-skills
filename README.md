# SaaS Ads Claude Skills

Twenty-five Claude Skills for the most common problems of a SaaS that wants to scale paid acquisition:

- Ads count trials that never pay.
- Cost per paying customer is unknown by campaign.
- Tracking and conversion data are broken.
- Nobody can say whether to scale or hold.
- Landing and pricing pages leak the click.

Each skill reads an export from your ad account, your CRM, or your billing tool, and says what to fix. None of them changes anything. Every output ends in a recommendation that a human approves.

**Who this is for:** founders, in-house marketers, and agencies or freelancers. The skills and thresholds are the same for all three.

Open source, MIT licensed. No live account access is needed.

The maths is trial-first: it judges signups on whether they pay after the trial. Demo-led and sales-led accounts use the lagged-CAC path (T25) in Cost Per Paying Customer, the lead-to-won helper in Trial Or Demo Path Check, and the contract-value branch in Payback Period Check.

If you have fewer than 20 paying customers per channel, you get: a 90-day window, same-platform and same-intent campaigns pooled into one line labeled `pooled` (T24), and `needs_data` on any line still below the floor. A pooled line that clears 20 paying customers may be compared and ranked. Weekly SaaS Ads Readout leads with it.

## What is inside

- 25 skills, one folder each, named `<job>-saas-ads`.
- 10 Python helpers (standard library only, no network) for the jobs where a model should not eyeball arithmetic: cost per paying customer, trial-to-paid cohorts, platform versus billing, payback (also per channel), brand versus non-brand, Meta creative fatigue, click-to-paid lag, the cost of the next dollar, a Stripe export join, and lead-to-won for demo-led accounts.
- One shared folder, `saas-ads-shared`, with the threshold register, the evidence standard, the data-export guide, sample data, and copy-paste prompts.

## Install

```bash
git clone https://github.com/mardab96/saas-ads-claude-skills.git
mkdir -p ~/.claude/skills
cp -r saas-ads-claude-skills/*saas-ads saas-ads-claude-skills/saas-ads-shared ~/.claude/skills/
```

Restart Claude Code. The skills call their helpers through `../saas-ads-shared/`, so copy the shared folder with them.

Supported surface: Claude Code on macOS and Linux. On Windows, use WSL. Native Windows is untested: use `python` or `py -3` for `python3`, and `%USERPROFILE%\.claude\skills` for the skills folder. Uploading a single skill folder to claude.ai breaks the shared helpers and threshold reads, because each skill looks for `../saas-ads-shared/`.

To check the install end to end in a throwaway home folder, run `sh saas-ads-claude-skills/saas-ads-shared/scripts/verify_install.sh saas-ads-claude-skills 25`. It prints a line that starts with PASS.

## How to use a skill

1. Export the data the skill asks for. `saas-ads-shared/references/getting-your-data.md` shows where each export lives.
2. Attach the file to Claude and name the skill, for example: "Use Cost Per Paying Customer. Attached: channel spend and new paying customers for October."
3. Read the verdict labels. `confirmed` means supplied evidence settles it. `needs_data` means something is missing, and the skill tells you what.

Ready-made prompts for all 25 skills are in `saas-ads-shared/examples/copy-paste-prompts.md`, which ends with a one-page Monday routine: exports in a fixed order, then one prompt. Blank CSV headers for the helpers that read a file are in `saas-ads-shared/templates/`. The data guide has a column-mapping table, a Stripe export recipe, and a fallback for when Stripe holds no campaign.

## Start here

| # | Skill | You give it | It tells you |
|---|---|---|---|
| 1 | Cost Per Paying Customer | Spend and new paying customers by channel (CSV) | What each channel pays for one customer, blended and per channel |
| 2 | Trial To Paid By Campaign | Signups with signup and paid dates (CSV) | Which campaigns bring trials that pay, on matured signups only |
| 3 | Ad Platform vs Billing Check | Platform conversions and billing customers by source (CSV) | Where the two numbers disagree and why |
| 4 | Payback Period Check | CAC, revenue per account, gross margin, churn | Months until a customer repays acquisition cost |
| 5 | Funnel Bottleneck Finder | Stage counts for two periods | The one stage that lost the most |
| 6 | Scale Or Hold Decision | Outputs of skills 1 to 4 plus tracking health | Whether a budget increase is supported |
| 7 | Weekly SaaS Ads Readout | A week of exports and the change log | A readout for the founder or the client, in small account mode when volume is thin |
| 8 | Signup Event Audit | GTM and GA4 captures | Whether signup events fire once and correctly |
| 9 | Paid Event Import Check | Customer sample with click IDs, import diagnostics | Whether paid outcomes reach Google Ads and Meta |
| 10 | Google Ads Conversion Audit | Conversion settings screenshots | What each campaign actually bids on |
| 11 | Bid Target Picker | Conversions by action, CAC, payback | Which event to bid on and a target range |
| 12 | Meta Pixel And CAPI Check | Events Manager screenshots | Duplicates, missing server events, match issues |
| 13 | GTM Container Review | Container export (JSON) | Duplicate tags, orphans, weak signup triggers |
| 14 | Consent Signal Loss Check | Clicks, sessions, consent settings | How much paid traffic measurement may be missing |
| 15 | UTM And Click ID Check | 20 signup rows and your URL setup | Where source and click IDs die |
| 16 | Attribution Window Fit | Click-to-paid delays, window settings | Whether the window is shorter than your sales cycle |
| 17 | Ad To Page Promise Match | Ad text and landing page text | Broken promises between ad and page |
| 18 | Landing Page Value Review | Page screenshots and text | Clarity, proof, and friction findings |
| 19 | Signup Form Friction Review | Form and path screenshots | Fields and steps to cut or test |
| 20 | Pricing Page Review | Pricing page text, plans, billing data | Gaps between the ad, the page, and the plan bought |
| 21 | Trial Or Demo Path Check | Path description, CRM dates | Whether the path fits the product and price |
| 22 | Search Term Intent Filter | Search terms export | Intent classes and negative keyword candidates |
| 23 | Brand vs Non-Brand Split | Spend and paying customers by segment (CSV) | What new demand really costs |
| 24 | Meta Creative Fatigue Check | Daily ad rows (CSV) | Which ads show fatigue and what else to rule out |
| 25 | Meta Downstream Quality Check | Ad export plus CRM or billing outcomes | Which ads bring customers, not only cheap signups |

All 25 work from a pasted export, a screenshot, or page text. None needs live access to an account.

## Quick start packs

- **Is paid working?** Run 1, 2, 3, then 4. If Stripe holds no campaign on your customers, per-campaign results will say `unattributed`. Use blended cost per paying customer as the headline, and start storing the campaign at signup (run 15). The data guide has the steps.
- **Fix measurement.** Run 8, 9, 10, 12, 13, then 15.
- **Fix the page.** Run 17, 18, 19, 20, then 21.
- **Weekly rhythm.** Run 7 on Monday (the Monday routine in the prompts file), 5 when the numbers move, 6 before any budget change.

## What they do not do

- They do not change campaigns, budgets, bids, tags, pages, prices, or forms.
- They do not promise results.
- They do not treat a platform conversion as a paying customer or as profit.
- They do not give legal advice on consent.

## Thresholds

Every numeric rule lives in `saas-ads-shared/references/thresholds.md`, with a unit and a tag: `[heuristic]` is this pack's working rule, `[platform guidance]` is a number the platform documents. Skills cite a T-ID, so you change a rule in one place.

## FAQ

**Does it work for Performance Max or Advantage+?** Partly. Those campaign types hide search terms and placements, so Search Term Intent Filter and Google Ads Conversion Audit mark that spend `needs_data` and do not estimate it. Cost per paying customer by campaign still works.

**Does it work for ecommerce or lead-gen accounts?** No. A skill says so and stops.

**What if I have few customers?** Below 20 new paying customers per channel (T01) a skill returns `needs_data`. Small account mode (T24) widens to 90 days and pools same-platform, same-intent campaigns with `--pool` and `--window-days`. Weekly SaaS Ads Readout uses it by default.

**Is a low retargeting cost real?** Not on its own. Retargeting and brand lines reach people who were already likely to buy, so they can look cheap without adding customers. Scale Or Hold Decision will not rank or scale one on its cost alone. Leave a random share of the audience out as a holdout, and compare paying customers between the exposed and held-out groups.

**Can I use it for LinkedIn Ads?** Spend can be fed through the spend CSVs like any other channel. The pack has no LinkedIn-specific checks.

**What if sales are demo-led?** Use the lagged-CAC cohort (T25) in Cost Per Paying Customer, and give contract value to Payback Period Check.

**Windows?** See the install note above.

## Next step

These skills judge a snapshot you export by hand. Lumy is an AI agent that manages your ad campaigns in Slack. He works on the same areas: your site and offer, tracking, Google Ads, and Meta Ads. He connects to your Google Ads and Meta Ads accounts, checks them every 30 minutes, 24/7, and every change needs your approval.

Start Lumy for $10 for 7 days: https://app.adlume.co

## License

MIT. See `LICENSE`. Changes are in `CHANGELOG.md`. Notes for agents are in `AGENTS.md`.
