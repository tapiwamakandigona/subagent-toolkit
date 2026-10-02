#!/bin/sh
# Keeps the harness itself lean: HARNESS.md budget, README token claim, template sizes,
# and a can-fail self-test of templates/check_budget.sh.
set -eu
cd "$(dirname "$0")/.."
fail=0
harness=$(wc -c < HARNESS.md)
max=8000
echo "HARNESS.md: $harness bytes (~$((harness / 4)) tokens), max $max"
if [ "$harness" -gt "$max" ]; then echo "FAIL HARNESS.md over budget"; fail=1; fi

claim=$(sed -n 's/.*HARNESS.md` (~\([0-9.]*\)k tokens).*/\1/p' README.md | head -n 1)
if [ -z "$claim" ]; then
  echo "FAIL README has no 'HARNESS.md\` (~N.Nk tokens)' claim"; fail=1
else
  actual=$((harness / 4))
  lo=$(awk "BEGIN{print int($claim*1000*0.8)}")
  hi=$(awk "BEGIN{print int($claim*1000*1.2)}")
  echo "README claims ~${claim}k tokens; actual ~$actual"
  if [ "$actual" -lt "$lo" ] || [ "$actual" -gt "$hi" ]; then echo "FAIL README token claim off by >20%"; fail=1; fi
fi

lines=$(wc -l < templates/AGENTS.md)
if [ "$lines" -gt 100 ]; then echo "FAIL templates/AGENTS.md has $lines lines"; fail=1; fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf 'small\n' > "$tmp/AGENTS.md"
if ! (cd "$tmp" && sh "$OLDPWD/templates/check_budget.sh" AGENTS.md >/dev/null); then
  echo "FAIL check_budget rejected a small boot set"; fail=1
fi
head -c 40000 /dev/zero | tr '\0' 'x' > "$tmp/AGENTS.md"
if (cd "$tmp" && sh "$OLDPWD/templates/check_budget.sh" AGENTS.md >/dev/null); then
  echo "FAIL check_budget accepted a 40 KB boot set"; fail=1
fi
if [ "$fail" -eq 0 ]; then echo "harness_budget: ok"; fi
exit "$fail"
