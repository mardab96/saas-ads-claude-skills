# Getting your data

Interface labels change. Paths below are practical starting points and do not promise that every account sees the same menu. Export the widest date range that still matches the question, and keep the date range in the filename. Never paste customer personal data: strip names, emails, and phone numbers before you share a file.

Blank CSV files with the right headers for the helpers that read a file sit in `saas-ads-shared/templates/`. Copy one, fill it from the exports below, and keep the header row unchanged. Money columns may carry commas, spaces, and a currency symbol, such as `1,200.50` or `€500`. Fractions may be written as a percent, such as `80%`. Date columns may be a date or a timestamp; US dates written `MM/DD/YYYY` need the `--us-dates` flag. Files separated by semicolons are read as they are, and headers are matched without regard to case, spaces, or dashes, so `New Paying Customers` works. When a required column is missing the error lists the headers it found. A row with zero spend and some customers is treated as unattributed, never as free customers.
Decimal commas are handled too. A file that writes `1.200,50` needs the `--decimal-comma` flag on the helper. When the file is separated by semicolons and a money cell looks like `1.200,50`, the helper turns the flag on by itself. A comma-separated file never turns it on by itself, because `1,200` is then ambiguous. A blank campaign or channel is read as `unattributed`.

## Column mapping

Export header names vary by tool, language, and version. Treat this table as a starting point, and rename the columns in your copy to the helper's names.

| Helper column | Google Ads | Meta Ads Manager | Stripe | Chargebee |
|---|---|---|---|---|
| `campaign` or `channel` | Campaign | Campaign name | A metadata field where you store the campaign | A custom or UTM field where you store the campaign |
| `spend` | Cost | Amount spent | not applicable | not applicable |
| `impressions` | Impr. | Impressions | not applicable | not applicable |
| `clicks` | Clicks | Link clicks | not applicable | not applicable |
| `frequency` | not applicable | Frequency | not applicable | not applicable |
| `date` | Day | Day | not applicable | not applicable |
| `ad` | not applicable | Ad name | not applicable | not applicable |
| `signup_date` | not applicable | not applicable | Customer created date (UTC) | Subscription created at |
| `paid_date` | not applicable | not applicable | First successful payment date (UTC) | Subscription activated at, or first paid invoice date |
| customer key | not applicable | not applicable | Customer ID | Subscription ID |

Chargebee also exports a trial end date. It helps check trial length, and it is not a payment date. A trial that ended without a payment is not a paying customer.

## Google Ads

For campaign, ad group, keyword, and search-term performance, open **Reports** or the campaign table, set the date range, add cost, clicks, impressions, conversions, conversion value, and the conversion action column, then download CSV. For search terms, use the **Search terms** view under Insights and reports. For conversion settings, capture a screenshot of **Goals**, then **Conversions**, then **Summary**, showing each action's category, primary or secondary status, count setting, value, and conversion window. For bidding, capture the campaign's bid strategy and target. Performance Max campaigns show search categories rather than full search terms, so note which campaigns are Performance Max.

## Meta Ads

For campaign, ad set, and ad performance, open **Ads Manager**, set the date range and the attribution setting, add spend, impressions, reach, frequency, link clicks, results, and cost per result, then export CSV. For daily creative work, use the **Breakdowns** menu and choose **By time**, **Day**. For pixel and Conversions API checks, open **Events Manager**, select the data source, and capture the overview, event list, diagnostics, and match-quality view. Screenshots are enough. Advantage+ campaigns hide some placement and audience detail, so note which campaigns use Advantage+.

## Tag Manager and analytics

For a Google Tag Manager review, open the container, choose **Admin**, then **Export Container**, and share the JSON file after removing any private IDs you do not want to share. In GA4 use **Reports**, **Acquisition**, **Traffic acquisition** for sessions by source and medium, and **Admin**, **Events** for the event list. For each event, note whether it is marked as a key event.

## Billing and CRM

This is the source that makes SaaS paid work honest. From the payment processor or billing tool, export new paying customers with signup date, first payment date, plan, monthly price, and the stored source, medium, campaign, and click ID if you capture them. From the CRM, export the lead or signup stage with created date, source fields, and stage change dates. A payment processor export beats a CRM stage when the two disagree.

### Stripe recipe: signups with a paid date

Use this to build the file for `trial_to_paid.py`. Fast path: `python3 saas-ads-shared/scripts/stripe_join.py customers.csv payments.csv --campaign-field campaign --out trial_to_paid.csv` does steps 2 to 5 for you. It prints the three-column CSV with no emails, and a one-line summary of customers, paid, and unattributed. The manual steps follow.

1. Export Customers with the customer ID, the created date, and the metadata field that holds the campaign. Delete the name and email columns before you do anything else. Keep the customer ID.
2. Export Payments for the same period with the customer ID, the created date, the amount, and the status. Keep only rows where the status is succeeded and the amount is above zero.
3. For each customer, take the earliest of those payments as `paid_date`. Join on the customer ID. A customer with no such payment has a blank `paid_date`.
4. Rename the campaign field to `campaign`, and the customer created date to `signup_date`. Write `unattributed` for a blank campaign. Do not guess a campaign for those rows.
5. Drop the customer ID column, since the helper does not need it. Save as CSV with the header `campaign,signup_date,paid_date`.

A three-row result looks like this (synthetic):

```text
campaign,signup_date,paid_date
brand_search,2026-10-01 09:30:00,2026-10-04
meta_prospecting,2026-10-02,
unattributed,2026-10-03T14:05:00Z,2026-10-20
```

The same join works for Chargebee: use the subscription ID as the key, the subscription created date as `signup_date`, and the first paid invoice date as `paid_date`.

For `cac_channels.csv`, count the customers with a `paid_date` by campaign or channel, then add the spend from your ad exports. `cac_recovery.py` takes values on the command line, or churn per source from a file (see the next recipe).

### No campaign stored in Stripe yet

If the campaign field is empty for most customers, `stripe_join.py` prints the share as unattributed and the helpers will say so. Do not guess a campaign. Use these fallbacks, in this order:

1. Blended CAC. Total ad spend divided by all new paying customers. In `cac.py` add one row with the channel `unattributed` and zero spend; the helper prints `blended_excl_unattributed` as the headline and keeps the rest as context.
2. GA4 first-touch. In GA4 open **Reports**, **Acquisition**, **User acquisition**, and export new users by first user source and medium. It is a signup count by first touch, not a paying-customer count, so label it `directional`.
3. Start capture. Store the campaign on the customer at signup, then follow `utm-click-id-check-saas-ads`. Customers created after capture starts are attributable; older ones stay unattributed.

### Churn by source recipe

Use this for `cac_recovery.py --churn-by-source`.

1. From billing, list the customers who paid in the period, by source, and note how many of them cancelled in the same period.
2. Monthly churn for a source is cancelled accounts divided by paying accounts at the start of the month, averaged over three or more months. Write it as a fraction (`0.03`) or a percent (`3%`).
3. Save a CSV with the header `source,monthly_churn,cac`. The `cac` column is optional; add it from `cac.py` when you want one row per source. Leave a blank churn for a source with fewer than a few months of history, and the helper prints `needs_churn` for it.

### Next-dollar cost recipe

Use this for `marginal_cac.py`. Pick two equal periods of at least 14 days that sit either side of the last budget change, with no other big change in them. Keep the change within one T18 step (at most 20%); the helper reads a channel only when its spend rose at least 10% (T27). For each channel save `channel,period,spend,new_paying_customers`, with `before` or `after` in the `period` column. Count customers by signup date, not payment date. Check the header against `saas-ads-shared/templates/marginal_cac_periods.csv`. The helper also needs `--after-end` (the last day of the after period), `--as-of` (the export date), and `--trial-days`, or `--lag-days` instead. Every signup in both periods must be matured (T02), so it stops until the export date is on or after the last day of the after period plus the lag.

Design a measurement step. With no clean budget change, run `marginal_cac.py --design` with the daily spend, the current cost per paying customer, and a start date. It prints one step of 20%, the days to wait, the minimum spend and paying customers, and the date to rerun the helper. Before and after ignores seasonality and is not incrementality.

### Click-to-paid lag recipe

Use this for `lag.py`. For each paying customer save `click_date` and `paid_date`. The click date comes from the stored click or first touch. For a per-platform answer, save one file per platform. For the lagged cohort table add a spend file with `month,spend`. The file lists paying customers only, so recent clicks look faster than they are (right-censoring). The helper takes the lag percentiles from clicks at least 90 days old (`--cohort-cutoff-days` changes this), so export at least four months of history. Header names from ad exports work in every helper: a unit in brackets is dropped, and `cost` or `amount_spent` reads as `spend`, `campaign_name` as `campaign`, `channel_name` as `channel`. The helper prints each rename in a `header_mapping` line on stderr.

### Lead pipeline recipe

Use this for `lead_to_won.py`, on demo-led or sales-led accounts. From the CRM export one row per lead with `campaign`, `lead_date`, `meeting_date`, `won_date`, and an optional `acv`. Leave dates blank for steps the lead never reached.

## Small accounts

When fewer than 20 customers pay in a channel in the normal window, the volume floor (T01) stops a per-channel cost. Use small account mode (T24): export a rolling 90 days ending on the last matured date, and pool campaigns of the same platform and intent into one line labeled `pooled`. In the helpers that is `--window-days 90` and one `--pool name=member_a,member_b` per pool. Never pool brand with non-brand or one platform with another. If the pooled line still has fewer than 20 paying customers, the answer is `needs_data`, and the number stays arithmetic only.

## Pages

Take a full-page screenshot on desktop and on mobile, and paste the visible text of the page. For an ad-to-page check, also paste the exact ad headline, description, and offer. For the signup path, record each screen from the ad click to the first product screen.

## A useful habit

Export with a clear date range every time. If the same dates, timezone, conversion definition, and attribution settings cannot be established, the output says `needs_data` and does not present a comparison as fact.
