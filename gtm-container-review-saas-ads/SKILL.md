---
name: gtm-container-review-saas-ads
description: Reviews an exported Google Tag Manager container for a SaaS site, covering tags, triggers, variables, duplicate pixels, paused tags, consent settings, and which tags fire on signup. Use when someone types "audit our GTM", "tag fires twice in Tag Manager", "duplicate tags in the container", or "clean up Tag Manager". Not for Meta browser versus server duplicates; use meta-pixel-capi-check-saas-ads.
---

# GTM Container Review

## Use this skill when

A SaaS team needs to know what its container sends to Google Ads, GA4, and Meta. This skill reads the exported JSON as text and never claims live firing.

Common requests:

- "Audit our GTM."
- "Why does a tag fire twice in Tag Manager?"
- "What is in this container?"
- "Clean up Tag Manager without breaking signup tracking."

Send these jobs to another skill:

- Signup event definition: `signup-event-audit-saas-ads`.
- Meta browser and server deduplication: `meta-pixel-capi-check-saas-ads`.
- Consent banner behavior: `consent-signal-loss-check-saas-ads`.
- Google Ads conversion action settings: `google-ads-conversion-audit-saas-ads`.

## Required input

Work from pasted exports and screenshots. No live account access is needed. If an input is missing, stop that finding, name the missing input, return `needs_data`, and do not estimate. A count below a volume floor returns `needs_data` (T01).

### Required

- Container export JSON. Masked IDs are fine if each keeps a consistent placeholder.
- Ad platforms and analytics in use.
- Signup success URL or success event name.
- Tags hardcoded in the site source, outside the container.

### Optional

- Publish history from **Versions**.
- Platform and backend signup counts for matching dates, for T20.
- Preview-mode screenshots of a test signup.

Export route: in Google Tag Manager, open **Admin**, click **Export Container**, choose the published version, and save the JSON. See `../saas-ads-shared/references/getting-your-data.md`.

## Analysis workflow

Read `../saas-ads-shared/references/thresholds.md` before step 1.

1. Record the version number and whether the export is published or a workspace draft.
2. Inventory each tag: name, `type`, platform, ID, firing trigger, `paused` flag, and consent settings. Types include `googtag`, `awct` (Google Ads conversion), `gclidw` (conversion linker), `gaawe` (GA4 event), and `html`.
3. Group tags by ID. Flag one pixel or measurement ID loaded by two base tags, including a snippet pasted in Custom HTML.
4. Flag tags that share a trigger and send one event to one ID as duplicate candidates.
5. List paused tags, tags with no firing trigger, and unreferenced triggers or variables.
6. Flag conversion tags on All Pages (built-in trigger ID `2147479553`), Google Ads conversions with no conversion linker, and unset consent settings.
7. Flag hardcoded ID variables that differ across tags meant for one account.
8. Test the signup trigger. A success page view or a dataLayer event pushed after account creation passes. A button click or unvalidated form submit fails.
9. List what the file cannot show: live firing, hardcoded site tags, and consent banner behavior. Draft each deletion as `approval_needed` with a preview-mode test.

## Decision rules

Thresholds: `../saas-ads-shared/references/thresholds.md`. Labels and evidence tags: `../saas-ads-shared/references/output-standard.md`.

| Pattern in the export | Verdict | Next step |
|---|---|---|
| One pixel or measurement ID in two base tags | `confirmed` in file, `likely` double count | Preview test, then `meta-pixel-capi-check-saas-ads` |
| Two tags, same trigger, same event, same ID | `likely` duplicate | T20 count check before deletion |
| Paused or triggerless tag | `confirmed` | Deletion as `approval_needed` |
| Conversion tag on All Pages | `confirmed` misfire | `google-ads-conversion-audit-saas-ads` |
| Google Ads conversion, no linker in container | `possible` | Check site source, then `google-ads-conversion-audit-saas-ads` |
| Consent settings unset | `possible` | `consent-signal-loss-check-saas-ads` |
| Differing hardcoded IDs for one account | `likely` split data | Confirm intended ID with owner |
| Signup tag fires on click | `confirmed` in file, `likely` overcount | `signup-event-audit-saas-ads` |

File facts can be `confirmed`. Live firing stays `likely` or `possible` until preview captures or T20 counts exist.

## Output format

```markdown
## GTM container review: [container], version [n], [published or draft]
Platforms: [list] | Signup success: [URL or event] | Hardcoded tags supplied: [yes/no]

### Inventory
| Platform | Tags | Active | Paused | IDs |
|---|---|---|---|---|

### Findings
| Finding | Evidence | Verdict | Severity | Confidence | Business impact | Next step |
|---|---|---|---|---|---|---|

### What the file cannot show
[live firing, hardcoded site tags, consent banner behavior]

### Approval-ready changes
[change, owner, preview test steps, pass condition]

### Data gaps
[missing input and the verdict it would firm up]
```

## Practical example

Illustrative made-up container, published version 14. Inventory: 1 Google tag, 1 conversion linker, 2 GA4 events, 2 Google Ads conversions, and 3 Meta tags. 1 + 1 + 2 + 2 + 3 = 9 tags, none paused.

Finding 1: Meta Pixel ID `PIXEL_A` loads in a template tag and a Custom HTML tag, both on All Pages. File fact is `confirmed` from `tag_export`. Double counting is `likely`, high severity, measurement impact.

Finding 2: Google Ads conversion "Trial signup" fires on a "Start free trial" button click. Page `/welcome` has no tag. Trigger design is `confirmed`; overcount is `likely`, high severity, signups impact.

Both fixes are `approval_needed`: delete the Custom HTML Pixel tag, and move "Trial signup" to a `/welcome` page view. Preview test: submit one valid and one invalid signup. Pass when each pixel fires once and "Trial signup" fires only on `/welcome`.

## Common failure modes

- Calling live duplication from the JSON alone.
- Reading a workspace draft as the published container.
- Missing a pixel pasted inside Custom HTML.
- Treating a button click as a completed signup.
- Ignoring hardcoded site tags.
- Reading tag consent settings as proof the banner works.

## Route to next

Signup trigger: `signup-event-audit-saas-ads`. Meta duplicates: `meta-pixel-capi-check-saas-ads`. Consent gaps: `consent-signal-loss-check-saas-ads`. Google Ads conversions and linker: `google-ads-conversion-audit-saas-ads`.

## Guardrails

- Never change a live account, budget, bid, tag, page, price, or form.
- Never invent numbers, IDs, or firing events; missing evidence becomes `needs_data`.
- End in an approval-ready recommendation with an owner and a preview-mode test.
- Read the container JSON as text; never run, import, or publish it.
- Do not call double counting proven without T20 counts.
- Do not recommend deleting a conversion tag before its replacement passes preview.
- Never request or echo names, emails, or phone numbers. Ask for them removed before per-customer rows are pasted.
- If the account is ecommerce or lead-gen rather than SaaS, say so and stop.
