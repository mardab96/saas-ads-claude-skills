# Changelog

## [1.2.3] - 2026-11-16

### Fixed

- `verify_install.sh` failed on every install from a clone with `FAIL: decoy resolved`: it searched the installed `saas-ads-shared` folder for the word `decoy`, and its own text, shipped in that folder, contains it. The decoy now carries a marker built at run time.
- `validate-skills.py` crashed in an installed copy (`~/.claude/skills`), because it read `AGENTS.md`, which stays in the clone. It now prints a note and runs the `AGENTS.md` checks only in the cloned pack.

## [1.2.2] - 2026-11-18

### Added

- Column headers from ad exports are understood by every helper that reads a file: a unit in brackets is dropped (`Spend (USD)`), `cost` and `amount_spent` read as `spend`, `campaign_name` as `campaign`, `channel_name` as `channel`. An exact column name always wins, and each rename prints a `header_mapping` line on stderr.
- `lag.py --cohort-cutoff-days` (default 90) and a `censoring:` line, with a `cohort_customers` count.

### Changed

- T27 now reads a channel when spend rose at least 10% (was 20%), so one T18 step of 10% to 20% always qualifies. Gate 5 text, the `--design` plan notes, and the sample `marginal_cac_periods.csv` follow it: every sample step is 20% or less, and the demo numbers changed.
- `lag.py` takes the median, the 80th percentile, and the T15 share only from clicks at least 90 days old, because the file lists paying customers only and recent clicks look faster than they are (right-censoring). Cost Per Paying Customer (step 9) and Attribution Window Fit carry the caveat.
- Scale Or Hold Decision: a payback inside the T05 review band passes gate 4 with a recorded caveat, and a channel is labelled `scale` only when its verdict is `approval_needed`. `monitor` is gone from the verdict table.
- `lead_to_won.py` names its labels by question: `T28_label` in the rate table and `T01_label` in the cost table, one label each per campaign.

### Fixed

- T27 required a spend rise of 20% while T18 capped a step at 20%, which left no margin.

## [1.2.1] - 2026-11-18

### Added

- `--decimal-comma` in every helper that reads money. It turns on by itself for a semicolon file with cells such as `1.200,50`.
- `marginal_cac.py --design`: a measurement step plan (one 20% step, days, minimum spend and customers, check date) for when no clean budget change exists. Scale Or Hold Decision gate 5 now returns that plan beside `needs_data`.
- `cac_recovery.py` prints `excludes: expansion revenue, annual prepay cash timing`.
- README FAQ: LinkedIn Ads spend can be fed through the spend CSVs.

### Changed

- `marginal_cac.py` counts customers by signup date and refuses periods that are not matured (T02, T27). New flags: `--after-end`, `--as-of`, `--trial-days`, `--billing-lag-days`, `--lag-days`. Existing commands need the first three.
- `marginal_cac.py` states that before and after ignores seasonality and is not incrementality.

### Fixed

- A blank channel in `cac.py` and a blank campaign in `trial_to_paid.py` are now read as `unattributed` (T26) instead of raising an error. A T26 line prints when unattributed customers reach 10%.

## [1.2.0] - 2026-11-18

### Added

- Click-to-paid lag helper, `lag.py` (T25, T15): median and 80th percentile days, the share paying later than a click window, and lagged CAC by click month. Wired into Cost Per Paying Customer (step 9) and Attribution Window Fit.
- Small account mode in the helpers: `--pool` and `--window-days` in `cac.py` and `trial_to_paid.py` (T24), a `pooled` label, and a worked small-account demo that ends in a verdict.
- `marginal_cac.py` (T27): incremental cost of the next dollar from two equal periods, compared with the T21 affordable cost. Scale Or Hold Decision gains a next-dollar gate and a "Where the next budget goes" cut, hold, or scale table, plus a retargeting holdout caveat.
- Payback per channel: `cac_recovery.py --churn-by-source`. T21 is stated at n = 12 months (central) and 18 (ceiling), and the helper prints both.
- Data onboarding: `stripe_join.py`, a "No campaign stored in Stripe yet" fallback, churn-by-source, next-dollar, lag, and pipeline recipes in the data guide.
- `lead_to_won.py` (T28), a pipeline template, and wiring in Trial Or Demo Path Check for demo-led accounts.
- A one-page Monday routine in the copy-paste prompts, linked from the README and Weekly SaaS Ads Readout.
- Header-only templates for the new file inputs, synthetic sample data, and demo outputs for every new helper.
- Self-tests for every new helper and flag, and a check that each skill's worked example block equals the helper output on its sample file.

### Changed

- Common reader: semicolon or comma files, header normalisation, percent fractions, `--us-dates`, headers listed in errors, and zero-spend rows with customers treated as unattributed. `cac.py` prints `blended_excl_unattributed`, and Cost Per Paying Customer names it the headline.
- Scale Or Hold Decision now runs eight gates. Gate 2 needs the T02 floor and a paid rate that is not weak. Gate 3 also compares platform signups with CRM signups when the platform bids on signups. Every gate states its verdict when it fails and when it cannot be evaluated.
- Trial To Paid By Campaign uses one wording: `insufficient_volume` means `needs_data`.
- Every helper prints a final `read:` line, and `cac_recovery.py` accepts percent inputs and `--churn-by-source`.

### Documented

- Thresholds T27 (Marginal CAC) and T28 (Sales-Cycle Maturity). T01 now covers both.

## [1.1.0] - 2026-11-17

### Changed

- Every skill description claims only phrases it owns and ends with a `Not for X; use Y.` clause. Overlaps are resolved: affordability to Scale Or Hold Decision, cheap signups to Trial To Paid By Campaign, platform versus billing disagreement to Ad Platform vs Billing Check, brand terms to Brand vs Non-Brand Split, and duplicate events split by layer (GTM container, Meta pixel and CAPI, GA4 and product events).
- Every skill carries the same missing-input rule: stop that finding, name the missing input, return `needs_data`, do not estimate. T01 is the one volume-floor verdict, cited by every skill, and each skill reads the threshold register before step 1.
- Every skill carries the personal-data guardrail and the scope guardrail for ecommerce and lead-gen accounts.
- Decision rules are numeric: Cost Per Paying Customer, Scale Or Hold Decision (T22, T23), Bid Target Picker (T21, T17), Funnel Bottleneck Finder (T19), Signup Event Audit (T20).
- Search Term Intent Filter example now matches its own table.
- Helper commands use `python3 "<skill-dir>/../saas-ads-shared/scripts/<name>.py" "<absolute path to your CSV>"`.
- README, AGENTS.md, and the blog lead with the problems a scaling SaaS meets and name founders, marketers, and agencies together.

### Added

- Thresholds T19 to T26, and a rewritten register with T01 as the canonical volume verdict.
- Shared helper module that reads `1,200.50`, `€500`, and timestamps. `cac.py` prints `n/a` and the label `unattributed` for zero-spend unattributed rows. `cac_recovery.py` prints `needs_churn` when churn is missing and accepts contract value and annual churn. `trial_to_paid.py` takes `--spend` for cost per signup and per paying customer.
- Header-only CSV templates for the six helpers, a column-mapping table, and a Stripe export recipe.
- Small account mode (T24). Weekly SaaS Ads Readout defaults to it when T01 fails.
- Lagged-CAC cohort step (T25) in Cost Per Paying Customer and a contract-value branch in Payback Period Check for sales-led accounts.
- Performance Max and Advantage+ caveats in Search Term Intent Filter and Google Ads Conversion Audit, and a README FAQ.
- Frequency caveat in Meta Creative Fatigue Check.
- A copy-paste prompt for each of the 25 skills.
- Validator checks for duplicate trigger phrases, the `Not for` clause, description length, the shared guardrails, command form, and prompt coverage.

### Documented

- Supported surface is Claude Code on macOS and Linux, with a Windows note. A single skill folder uploaded to claude.ai breaks the shared helpers.
- The maths is trial-first. Demo-led accounts use the lagged-CAC path.

## [1.0.0] - 2026-11-17

Initial release.

### Added

- Twenty-five data-first skills for the person who runs Google Ads and Meta Ads for a SaaS company.
- Shared evidence standard, data-export guide, and single-home threshold register.
- Six Python standard-library helpers: cost per paying customer, trial-to-paid cohorts, ad platform versus billing reconciliation, payback period, brand versus non-brand split, and Meta creative fatigue.
- Copy-paste prompts, synthetic sample data, real script output demos, a validator, self-tests, and an install verification script.

### Correctness checks

- Pack-specific shared paths prevent collisions with other installed skill packs.
- Zero paying customers produce an undefined cost, never an apparent improvement.
- Trial cohorts count only signups older than the trial length plus the billing lag.
- Reported platform conversions stay separate from billing counts and from profit.

### Guardrails

- No live platform access is required.
- No skill changes ads, budgets, bids, tracking, pages, or pricing. Every output stops at a recommendation a human approves.
