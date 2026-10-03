#!/bin/sh
# New-profile local gate. Upstream legacy Git integration tests remain in CI.
set -eu
cd "$(dirname "$0")"
python3 -m unittest tests.test_autonomous_loop -v
sh tests/harness_budget.sh
sh check_budget.sh templates/AGENTS.md templates/PROJECT.md templates/features.json templates/AUTONOMY.md templates/PROMPT.md
for script in templates/loop.sh templates/check_budget.sh templates/high_autonomy_loop.sh verify.sh; do
  sh -n "$script"
done
