#!/bin/sh
# Installs the pack into a throwaway HOME and checks it end to end.
# usage: verify_install.sh <repo-url-or-local-path> <count>
set -eu
source=${1:?usage: verify_install.sh <repo-url-or-local-path> <count>}
expected=${2:?count}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if [ -d "$source" ]; then cp -R "$source" "$tmp/saas-ads-claude-skills"; else git clone "$source" "$tmp/saas-ads-claude-skills"; fi
# A decoy shared folder proves the skills resolve their own pack folder, not a neighbor.
mkdir -p "$tmp/home/.claude/skills/references"
echo decoy > "$tmp/home/.claude/skills/references/thresholds.md"
(cd "$tmp" && HOME="$tmp/home" sh -c 'mkdir -p ~/.claude/skills; cp -r saas-ads-claude-skills/*saas-ads saas-ads-claude-skills/saas-ads-shared ~/.claude/skills/')
i="$tmp/home/.claude/skills"
count=$(find "$i" -mindepth 1 -maxdepth 1 -type d -name '*saas-ads' -exec test -f '{}/SKILL.md' \; -print | wc -l | tr -d ' ')
[ "$count" = "$expected" ] || { echo "FAIL: found $count skill folders, expected $expected"; exit 1; }
paths=0
for s in "$i"/*saas-ads/SKILL.md; do
  for r in $(grep -Eo '\.\./saas-ads-shared/(scripts|references)/[A-Za-z0-9_.-]+' "$s" | sort -u); do
    test -e "$(dirname "$s")/$r" || { echo "FAIL: $s points at missing $r"; exit 1; }
    paths=$((paths+1))
  done
done
if grep -R 'decoy' "$i/saas-ads-shared" >/dev/null; then echo "FAIL: decoy resolved"; exit 1; fi
python3 "$i/saas-ads-shared/scripts/validate-skills.py" --expect "$expected"
python3 "$i/saas-ads-shared/scripts/selftest.py"
d="$i/saas-ads-shared/examples/data"
python3 "$i/saas-ads-shared/scripts/cac.py" "$d/cac_channels.csv" >/dev/null
python3 "$i/saas-ads-shared/scripts/trial_to_paid.py" "$d/trial_to_paid.csv" --trial-days 14 --as-of 2026-11-16 >/dev/null
python3 "$i/saas-ads-shared/scripts/reconcile.py" "$d/platform_vs_billing.csv" >/dev/null
python3 "$i/saas-ads-shared/scripts/cac_recovery.py" --cac 480 --arpa 79 --gross-margin 0.8 --monthly-churn 0.04 >/dev/null
python3 "$i/saas-ads-shared/scripts/brand_split.py" "$d/brand_split.csv" >/dev/null
python3 "$i/saas-ads-shared/scripts/fatigue.py" "$d/fatigue_daily.csv" >/dev/null
python3 "$i/saas-ads-shared/scripts/lag.py" "$d/lag_customers.csv" --as-of 2026-11-16 --window-days 7 >/dev/null
python3 "$i/saas-ads-shared/scripts/marginal_cac.py" "$d/marginal_cac_periods.csv" --days-before 28 --days-after 28 --after-end 2026-10-26 --as-of 2026-11-16 --trial-days 14 --affordable 611.92 >/dev/null
python3 "$i/saas-ads-shared/scripts/stripe_join.py" "$d/stripe_customers.csv" "$d/stripe_payments.csv" --campaign-field campaign >/dev/null 2>&1
python3 "$i/saas-ads-shared/scripts/lead_to_won.py" "$d/lead_pipeline.csv" --as-of 2026-11-16 >/dev/null
echo "PASS: installed $count skill folders; checked $paths shared paths; decoy collision did not resolve; ran 10 installed helpers"
