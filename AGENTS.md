# Notes for agents

This pack holds 25 skills for the most common problems of a SaaS that wants to scale paid acquisition: ads that count trials that never pay, an unknown cost per paying customer by campaign, broken tracking, the question of whether to scale, and landing and pricing pages that leak. Read this file before you pick a skill.

Who this is for: founders, in-house marketers, and agencies or freelancers. Use the same skills and the same thresholds for all three.

## Composition

- Skill folders end in `-saas-ads`. Each holds one `SKILL.md`.
- `saas-ads-shared/` holds the helpers (`scripts/`), blank CSV headers (`templates/`), the threshold register and the evidence standard (`references/`), and the sample data and prompts (`examples/`).
- Skills resolve shared files as `../saas-ads-shared/...`. Install the shared folder next to the skills or the paths break.
- Every number that decides an action lives in `references/thresholds.md`. Cite the T-ID. Do not copy the number into an answer without the T-ID.
- Supported surface is Claude Code. A single skill folder uploaded alone to claude.ai loses the shared helpers and thresholds.

## Choosing a skill

| The user says | Start with |
|---|---|
| "What does a customer cost" | `cost-per-paying-customer-saas-ads` |
| "Which campaign brings customers that pay", "cheap signups that do not pay" | `trial-to-paid-by-campaign-saas-ads` |
| "The platform and billing disagree" | `ad-platform-vs-billing-check-saas-ads` |
| "Can we scale", "can we afford to scale" | `scale-or-hold-decision-saas-ads`, after skills 1 to 4 |
| "Brand terms are eating the budget" | `brand-nonbrand-split-saas-ads` |
| "Events are duplicated" in the Tag Manager container | `gtm-container-review-saas-ads` |
| "Events are duplicated" in Meta (pixel and CAPI) | `meta-pixel-capi-check-saas-ads` |
| "Events are duplicated" in GA4 or against the CRM, "events look wrong" | `signup-event-audit-saas-ads`, then the Meta or Google audit |
| "Clicks but no signups" | `ad-to-page-promise-match-saas-ads`, then the page skills |
| "We have very few customers", a small account | `weekly-readout-saas-ads`, which defaults to small account mode (T24); helpers take `--window-days 90` and `--pool` |
| "Our sales are demo-led" | `cost-per-paying-customer-saas-ads` (lagged CAC, T25), `trial-or-demo-path-check-saas-ads` (`lead_to_won.py`), then `payback-period-check-saas-ads` with ACV |
| "Weekly report" | `weekly-readout-saas-ads`, following the Monday routine in `saas-ads-shared/examples/copy-paste-prompts.md` |
| "Where should the next budget go", "what does the next dollar cost" | `scale-or-hold-decision-saas-ads` (`marginal_cac.py`, T27; `--design` plans a measurement step when no clean budget change exists) |
| "Which channel pays back" | `payback-period-check-saas-ads` with `--churn-by-source` |
| "Stripe has no campaign on customers" | `saas-ads-shared/references/getting-your-data.md`, then `utm-click-id-check-saas-ads` |

When the request does not map to one skill, run `funnel-bottleneck-finder-saas-ads` first and follow its route.

## Judging a SaaS account

- The unit of success is a paying customer confirmed by billing. A platform conversion, a signup, and a lead are earlier events, not outcomes.
- A SaaS trial has a lag. Count a signup in a paid rate only when it is old enough to have converted (T02). Recent signups are immature, not failed.
- The maths is trial-first. A demo-led or sales-led account uses lagged CAC (T25) and the ACV branch of the payback helper.
- Judge channels on cost per paying customer and payback, not on cost per signup.
- Brand search can hold a large share of customers (T09). Judge new demand on the non-brand line.
- Compare an account with its own history. This pack ships no outside benchmarks.
- An ecommerce account judges on revenue and margin per order, and a lead-gen account on qualified lead and close rate. Do not apply this pack's trial-to-paid logic to those. Say so and stop.
- Performance Max and Advantage+ campaigns hide term and placement detail. Mark that spend `needs_data` rather than estimating it.
- A low retargeting or brand cost can come with no added customers. Ask for a holdout before ranking or scaling those lines.
- When many customers have no stored campaign (T26), report `blended_excl_unattributed` as the headline and say how many customers are unattributed. A blank channel or campaign is read as `unattributed`.
- `marginal_cac.py` counts customers by signup date and needs matured periods (T02, T27): give `--after-end`, `--as-of`, and `--trial-days` or `--lag-days`. Before and after ignores seasonality and is not incrementality; say so.
- Helpers that read money take `--decimal-comma` for values like `1.200,50`; a semicolon file with such a cell turns it on by itself.

## Live-action boundary

- Never change a campaign, budget, bid, conversion action, tag, container, page, price, or form.
- Never upload conversions or send events.
- Never paste or request customer personal data. Ask for exports with names, emails, and phone numbers removed.
- Every recommendation ends in `approval_needed`, `hold`, `monitor`, or `needs_data`, as defined in `references/output-standard.md`.
- If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

## Using the helpers

- `<skill-dir>` means the folder that holds the `SKILL.md` you are following. Run a helper in this form, with every path quoted:
  `python3 "<skill-dir>/../saas-ads-shared/scripts/cac.py" "<absolute path to your CSV>"`
- Helpers use the standard library and no network, and they leave input files unchanged.
- Money columns may carry commas, spaces, and a currency symbol. Fractions may be percents such as `80%`. Date columns may carry a time; `MM/DD/YYYY` dates need `--us-dates`. Semicolon-separated files and differently cased headers are read as they are, and an error lists the headers it found.
- A missing, blank, or non-numeric value exits with code 2 and a `needs_data` message. Do not fill the gap with an assumption. Ask for the data.
- Blank CSV headers for each helper that reads a file are in `saas-ads-shared/templates/`. The ten helpers are `cac`, `trial_to_paid`, `reconcile`, `cac_recovery`, `brand_split`, `fatigue`, `lag`, `marginal_cac`, `stripe_join`, and `lead_to_won`.
- `scripts/validate-skills.py` checks the skills. `scripts/selftest.py` checks the helpers. `scripts/verify_install.sh` checks an install.

## Changing the pack

Add a skill by copying a folder, renaming it with the `-saas-ads` suffix, and updating the count in `README.md`, `CHANGELOG.md`, and the `verify_install.sh` call. Add its prompt to `saas-ads-shared/examples/copy-paste-prompts.md` under a heading that matches its title. Run the validator and the self-test before you commit.
