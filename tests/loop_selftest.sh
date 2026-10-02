#!/bin/sh
# loop_selftest.sh — behavioural check for templates/loop.sh (CI + local).
# Drives the loop with a scripted fake agent in throwaway git repos and
# asserts each guard's exit code. Usage: sh tests/loop_selftest.sh
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
LOOP="$ROOT/templates/loop.sh"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# Fake agent: behaviour from $SCENARIO, iteration count kept in .n.
cat >"$WORK/agent.sh" <<'AGENT'
#!/bin/sh
prompt=$(cat)
n=$(cat .n 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" >.n
case "$SCENARIO" in
  report_then_work)
    # Turn 1 ends with a progress report and no commit (Opus 5.5-style).
    if [ "$n" -eq 1 ]; then echo "Progress: scaffolded; next I'll do F1."; exit 0; fi
    printf '%s\n' "$prompt" | grep -q 'Still open in features.json: F1' ||
      { echo "nudge missing"; exit 0; }
    python3 -c 'import json; d = json.load(open("features.json")); d["features"][0]["passes"] = True; json.dump(d, open("features.json", "w"))'
    git add -A && git commit -qm "F1" && echo DONE_ALL ;;
  blocked) echo "BLOCKED: needs a credential from the operator" ;;
  mid_line) echo "I would print BLOCKED: if stuck."; date >>w; git add -A; git commit -qm "s$n"; echo DONE_ALL ;;
  stall) echo "Will continue later." ;;
  false_done) echo "All good. DONE_ALL" ;;
  bad_json) echo "{" >features.json; git add -A; git commit -qm bad; echo DONE_ALL ;;
esac
AGENT
chmod +x "$WORK/agent.sh"

fail=0
check() { # scenario expected_exit
  d="$WORK/$1"
  mkdir -p "$d" && cd "$d" || exit 1
  git init -q && git config user.email t@t && git config user.name t
  echo 'Read the state files, do ONE task, verify, commit.' >PROMPT.md
  echo '{"features":[{"id":"F1","passes":false}]}' >features.json
  echo '.n' >.gitignore
  git add -A && git commit -qm init
  SCENARIO="$1" AGENT_CMD="$WORK/agent.sh" sh "$LOOP" 5 >log 2>&1
  got=$?
  if [ "$got" -eq "$2" ]; then
    echo "ok   $1 (exit $got)"
  else
    echo "FAIL $1: expected exit $2, got $got"; tail -5 log; fail=1
  fi
  cd "$WORK" || exit 1
}

check report_then_work 0  # a text-only report is re-prompted with open ids
check blocked 3           # a BLOCKED: line stops for the human
check mid_line 1          # a mid-line mention is not a blocker; marker alone never passes
check stall 2             # two iterations without a commit halt
check false_done 1        # DONE_ALL with open features fails the final gate
check bad_json 1          # an unreadable features.json never passes
exit "$fail"
