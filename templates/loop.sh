#!/bin/sh
# Single-agent loop (harness v4). Usage: AGENT_CMD='claude -p' ./loop.sh [1..1000]
# Requires Python 3.9+, Git with an initial commit, and the filled project files.
# Exit: 0 complete; 1 repeated failure; 2 stalled; 3 setup; 4 cap (iterations or
#       minutes); 5 approval required; 6 check/ledger integrity; 7 operator stop.
# Environment (all optional except AGENT_CMD):
#   AGENT_CMD      command + args that reads the brief on stdin (never shell source)
#   EVALUATOR_CMD  optional read-only fresh-context reviewer, run AFTER the agent
#   SANDBOX_CMD    optional prefix (e.g. ./sandbox.sh) wrapping agent/evaluator runs
#   ITER_TIMEOUT   wall-clock seconds per agent/evaluator run (default 3600; 0 = none)
#   MAX_MINUTES    total run budget in minutes (default 0 = iterations only)
#   OUTPUT_CAP     max bytes of captured agent output per run (default 5000000)
# Never put credentials in AGENT_CMD, briefs, or project files.

set -eu
MAX_ITER="${1:-20}"
PYTHON="${PYTHON:-python3}"
AGENT_CMD="${AGENT_CMD:-}"
EVALUATOR_CMD="${EVALUATOR_CMD:-}"
SANDBOX_CMD="${SANDBOX_CMD:-}"
ITER_TIMEOUT="${ITER_TIMEOUT:-3600}"
MAX_MINUTES="${MAX_MINUTES:-0}"
OUTPUT_CAP="${OUTPUT_CAP:-5000000}"

setup_error() {
    echo "SETUP ERROR: $1" >&2
    exit 3
}
is_uint() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
    esac
    [ "${#1}" -le 9 ]
}
is_uint "$MAX_ITER" || setup_error "iteration cap must be 1..1000"
if [ "$MAX_ITER" -lt 1 ] || [ "$MAX_ITER" -gt 1000 ]; then setup_error "iteration cap must be 1..1000"; fi
is_uint "$ITER_TIMEOUT" || setup_error "ITER_TIMEOUT must be a whole number of seconds"
is_uint "$MAX_MINUTES" || setup_error "MAX_MINUTES must be a whole number"
is_uint "$OUTPUT_CAP" || setup_error "OUTPUT_CAP must be a whole number of bytes"
if [ -z "$AGENT_CMD" ] || ! command -v "$PYTHON" >/dev/null 2>&1; then
    setup_error "AGENT_CMD and Python are required"
fi
tmo=""
if [ "$ITER_TIMEOUT" -gt 0 ]; then
    if command -v timeout >/dev/null 2>&1; then
        tmo="timeout -k 30 $ITER_TIMEOUT"
    else
        setup_error "timeout(1) is unavailable; set ITER_TIMEOUT=0 to run without a wall-clock cap"
    fi
fi
for file in AGENTS.md PROJECT.md PROMPT.md progress.md features.json verify.sh check_features.py; do
    [ -f "$file" ] || setup_error "required project input missing"
done
if [ -n "$EVALUATOR_CMD" ] && [ ! -f EVALUATOR.md ]; then
    setup_error "EVALUATOR_CMD requires EVALUATOR.md"
fi
if [ ! -x ./verify.sh ] ||
   [ "$(git rev-parse --is-inside-work-tree 2>/dev/null || :)" != true ] ||
   ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    setup_error "executable verifier and initialized Git repository required"
fi

umask 077
# Single-writer lease with stale-lock reconciliation (durable state, no double runs).
mkdir -p .harness/runs
if ! mkdir .harness/lock 2>/dev/null; then
    old_pid=$(cat .harness/lock/pid 2>/dev/null || :)
    if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
        setup_error "another loop holds .harness/lock (pid $old_pid)"
    fi
    rm -rf .harness/lock
    mkdir .harness/lock || setup_error "cannot take .harness/lock"
    stale_lock=1
else
    stale_lock=0
fi
echo "$$" > .harness/lock/pid
run_dir=""
trap '[ -n "$run_dir" ] && rm -rf "$run_dir"; rm -rf .harness/lock' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
run_dir=$(mktemp -d "${TMPDIR:-/tmp}/single-agent-loop.XXXXXXXX") || exit 3
run_id="run-$(date -u +%Y%m%dT%H%M%SZ)-$$"
ledger=".harness/runs/$run_id.jsonl"
export HARNESS_RUN_ID="$run_id"
export HARNESS_ITERATION=0
export HARNESS_SANDBOX_REPORT="$run_dir/sandbox-mode"
# Execute a trusted run-local copy: an agent editing the project checker cannot
# cause the next integrity check to run the edited code.
cp ./check_features.py "$run_dir/check_features.py"
checker="$run_dir/check_features.py"
baseline="$run_dir/baseline.json"

ev() {
    # Hash-chained, append-only run ledger; fields are short key=value pairs.
    "$PYTHON" "$checker" event --log "$ledger" --type "$@"
}
log() {
    printf '%s\n' "$1" >> progress.md
}
ev run_start cap="$MAX_ITER" iter_timeout="$ITER_TIMEOUT" max_minutes="$MAX_MINUTES" \
    stale_lock_reclaimed="$stale_lock" sandbox="${SANDBOX_CMD:-none}" evaluator="$([ -n "$EVALUATOR_CMD" ] && echo yes || echo no)"

# Phase 1 (setup): init.sh may use the network and install dependencies. It runs
# once, unsandboxed, before the check baseline is frozen and before any agent.
if [ -f ./init.sh ]; then
    [ -x ./init.sh ] || setup_error "init.sh must be executable"
    if ./init.sh >"$run_dir/init-output" 2>&1; then
        ev init_ok
    else
        ev init_failed status="$?"
        setup_error "init.sh failed"
    fi
fi
if ! "$PYTHON" "$checker" snapshot --output "$baseline"; then exit 3; fi
if ! trusted_hooks=$("$PYTHON" "$checker" hooks); then setup_error "hooks.lock is invalid or a trusted hook changed"; fi
ev baseline_frozen

start_epoch=$(date +%s)
verify() {
    # Private, run-local transcript; never print/refeed raw agent/check output.
    if ./verify.sh >"$run_dir/verify-output" 2>&1; then
        verify_status=0
    else
        verify_status=$?
    fi
    ev verify status="$verify_status"
}
guard() {
    if ! "$PYTHON" "$checker" integrity --baseline "$baseline"; then
        ev integrity_violation
        log "- FAILED: frozen check/spec integrity changed; human review required."
        exit 6
    fi
}
done_check() {
    [ "$verify_status" -eq 0 ] && [ "$verdict" != NEEDS_WORK ] &&
        "$PYTHON" "$checker" complete --baseline "$baseline" --run-id "$run_id" >/dev/null 2>&1
}
run_hook() {
    # Codex-style trust: a hook runs only when hooks.lock pins its current hash.
    hook_status=0
    [ -e "hooks/$1" ] || return 0
    case "
$trusted_hooks
" in
        *"
hooks/$1
"*)
            if "./hooks/$1" >"$run_dir/hook-output" 2>&1; then hook_status=0; else hook_status=$?; fi
            ev hook name="$1" status="$hook_status" ;;
        *) ev hook_skipped name="$1" reason=untrusted ;;
    esac
}
operator_stop() {
    if [ -e AGENT_STOP ]; then
        ev operator_stop
        log "- STOPPED: operator placed AGENT_STOP."
        echo "STOPPED — AGENT_STOP present" >&2
        exit 7
    fi
}
budget_check() {
    if [ "$MAX_MINUTES" -gt 0 ] && [ $(( $(date +%s) - start_epoch )) -ge $(( MAX_MINUTES * 60 )) ]; then
        ev budget_exhausted
        log "- INCOMPLETE: wall-clock budget reached."
        echo "INCOMPLETE — wall-clock budget reached" >&2
        exit 4
    fi
}
run_model() {
    # $1 = brief file, $2 = output file. Word splitting is intentional; no eval.
    # shellcheck disable=SC2086
    if $tmo $SANDBOX_CMD $3 <"$1" >"$2" 2>&1; then
        model_status=0
    else
        model_status=$?
    fi
    size=$(wc -c <"$2" | tr -d ' ')
    if [ "$size" -gt "$OUTPUT_CAP" ]; then
        model_status=125
    fi
}

verdict=""
verify
guard
if done_check; then
    echo "VERIFIED green — checks and all feature evidence pass"
    log "- VERIFIED: already complete; verifier and feature evidence passed."
    ev complete iteration=0
    exit 0
fi
last_verify_status=$verify_status
stall=0
failures=0
i=0
failure=""
findings=""
while [ "$i" -lt "$MAX_ITER" ]; do
    operator_stop
    budget_check
    i=$((i + 1))
    export HARNESS_ITERATION="$i"
    echo "=== iteration $i/$MAX_ITER ==="
    rm -f report.json evaluation.json
    cp ./PROMPT.md "$run_dir/brief"
    if [ -f STEER.md ]; then
        # Operator steering: surfaced once, then consumed.
        printf '\nOperator steering for this iteration:\n' >>"$run_dir/brief"
        cat STEER.md >>"$run_dir/brief"
        mv STEER.md "$run_dir/steer-$i.md"
        ev steer_consumed iteration="$i"
    fi
    if [ "$failures" -eq 1 ]; then
        printf '\nPrevious failure (verbatim status): %s\n' "$failure" >>"$run_dir/brief"
        printf 'This is the only retry. Diagnose it; do not repeat blindly.\n' >>"$run_dir/brief"
    fi
    if [ -n "$findings" ]; then
        printf '\nIndependent evaluator findings to resolve first:\n' >>"$run_dir/brief"
        cat "$findings" >>"$run_dir/brief"
    fi
    before=$("$PYTHON" "$checker" fingerprint) || exit 3
    ev iteration_start iteration="$i" fingerprint="$before"
    run_hook pre_iteration
    if [ "$hook_status" -ne 0 ]; then
        failure="pre_iteration hook exited with status $hook_status"
    else
        run_model "$run_dir/brief" "$run_dir/agent-output" "$AGENT_CMD"
        ev agent_exit iteration="$i" status="$model_status" sandbox_mode="$(cat "$run_dir/sandbox-mode" 2>/dev/null || echo unknown)"
        guard
        if [ "$model_status" -eq 124 ]; then
            failure="agent command timed out after $ITER_TIMEOUT seconds"
        elif [ "$model_status" -eq 125 ]; then
            failure="agent output exceeded the $OUTPUT_CAP byte cap"
        elif [ "$model_status" -ne 0 ]; then
            failure="agent command exited with status $model_status"
        elif ! "$PYTHON" "$checker" report --approval-file APPROVAL_REQUESTED.md >"$run_dir/report-summary" 2>/dev/null; then
            failure="iteration report missing or invalid"
        else
            mv report.json "$run_dir/report-$i.json"
            failure=""
        fi
    fi
    if [ -z "$failure" ] && grep -q '^approvals=[1-9]' "$run_dir/report-summary"; then
        ev approval_requested iteration="$i"
        log "- Iteration $i HALTED: agent requested approval; see APPROVAL_REQUESTED.md."
        echo "APPROVAL REQUIRED — see APPROVAL_REQUESTED.md" >&2
        exit 5
    fi
    if [ -z "$failure" ]; then
        verify
        guard
        if [ "$verify_status" -ne 0 ]; then
            failure="verification command exited with status $verify_status"
        fi
    fi
    if [ -z "$failure" ]; then
        run_hook post_iteration
        [ "$hook_status" -eq 0 ] || failure="post_iteration hook exited with status $hook_status"
    fi
    if [ -z "$failure" ] && [ -n "$EVALUATOR_CMD" ]; then
        # Sequential, fresh-context, read-only review. Not a subagent: nothing runs
        # in parallel and the evaluator may not change the project.
        cp ./EVALUATOR.md "$run_dir/eval-brief"
        printf '\nValidated iteration report (JSON):\n' >>"$run_dir/eval-brief"
        cat "$run_dir/report-$i.json" >>"$run_dir/eval-brief"
        pre_eval=$("$PYTHON" "$checker" fingerprint) || exit 3
        run_model "$run_dir/eval-brief" "$run_dir/evaluator-output" "$EVALUATOR_CMD"
        ev evaluator_exit iteration="$i" status="$model_status"
        guard
        post_eval=$("$PYTHON" "$checker" fingerprint) || exit 3
        if [ "$pre_eval" != "$post_eval" ]; then
            ev integrity_violation reason=evaluator_wrote_to_project
            log "- FAILED: evaluator modified the project; human review required."
            echo "INTEGRITY — evaluator modified the project" >&2
            exit 6
        fi
        if [ "$model_status" -ne 0 ]; then
            failure="evaluator command exited with status $model_status"
        elif ! "$PYTHON" "$checker" evaluation --findings-file "$run_dir/findings" >"$run_dir/eval-summary" 2>/dev/null; then
            failure="evaluator verdict missing or invalid"
        else
            mv evaluation.json "$run_dir/evaluation-$i.json"
        fi
    fi
    if [ -n "$failure" ]; then
        failures=$((failures + 1))
        echo "FAILED: $failure"
        log "- Iteration $i FAILED: $failure."
        ev iteration_failed iteration="$i" failure="$failure"
        if [ "$failures" -ge 2 ]; then
            echo "FAILED twice — stopping for descope or human review" >&2
            exit 1
        fi
        continue
    fi
    failures=0
    verdict=""
    findings=""
    if [ -n "$EVALUATOR_CMD" ]; then
        verdict=$(sed -n 's/^verdict=//p' "$run_dir/eval-summary")
        ev evaluator_verdict iteration="$i" verdict="$verdict"
        if [ "$verdict" = NEEDS_WORK ]; then
            findings="$run_dir/findings"
        fi
    fi
    if grep -q '^status=complete' "$run_dir/report-summary"; then
        echo "agent reports complete — checking independent completion gate"
    fi
    if done_check; then
        echo "VERIFIED green — checks and all feature evidence pass"
        log "- Iteration $i VERIFIED: verifier and all feature evidence passed."
        ev complete iteration="$i"
        exit 0
    fi
    after=$("$PYTHON" "$checker" fingerprint) || exit 3
    if [ "$before" = "$after" ] && [ "$last_verify_status" -eq "$verify_status" ]; then
        stall=$((stall + 1))
    else
        stall=0
    fi
    last_verify_status=$verify_status
    log "- Iteration $i: checks pass, features incomplete; stall count $stall."
    ev iteration_end iteration="$i" fingerprint="$after" stall="$stall"
    if [ "$stall" -ge 2 ]; then
        echo "STALLED — no project-content or check-status delta for two iterations" >&2
        exit 2
    fi
done
log "- INCOMPLETE: hard iteration cap reached."
ev cap_reached iteration="$i"
echo "INCOMPLETE — hard iteration cap reached" >&2
exit 4
