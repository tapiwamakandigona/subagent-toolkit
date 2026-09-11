#!/bin/sh
# Single-agent loop. Usage: AGENT_CMD='claude -p' ./loop.sh [1..1000]
# Requires Python 3.9+, Git with an initial commit, and the filled project files.
# Exit: 0 complete; 1 repeated failure; 2 stalled; 3 setup; 4 cap; 6 check tamper.
# AGENT_CMD is a command plus whitespace-separated args, not shell source.
# Use a wrapper executable for complex quoting. Never put credentials in it.

set -eu
MAX_ITER="${1:-20}"
PYTHON="${PYTHON:-python3}"
AGENT_CMD="${AGENT_CMD:-}"
case "$MAX_ITER" in
    ''|*[!0-9]*) echo "SETUP ERROR: iteration cap must be 1..1000" >&2; exit 3 ;;
esac
if [ "${#MAX_ITER}" -gt 4 ] || [ "$MAX_ITER" -lt 1 ] || [ "$MAX_ITER" -gt 1000 ]; then
    echo "SETUP ERROR: iteration cap must be 1..1000" >&2
    exit 3
fi
if [ -z "$AGENT_CMD" ] || ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "SETUP ERROR: AGENT_CMD and Python are required" >&2
    exit 3
fi
for file in AGENTS.md PROJECT.md PROMPT.md progress.md features.json verify.sh check_features.py; do
    if [ ! -f "$file" ]; then
        echo "SETUP ERROR: required project input missing" >&2
        exit 3
    fi
done
if [ ! -x ./verify.sh ] ||
   [ "$(git rev-parse --is-inside-work-tree 2>/dev/null || :)" != true ] ||
   ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "SETUP ERROR: executable verifier and initialized Git repository required" >&2
    exit 3
fi

umask 077
run_dir=$(mktemp -d "${TMPDIR:-/tmp}/single-agent-loop.XXXXXXXX") || exit 3
trap 'rm -rf "$run_dir"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
# Execute a trusted run-local copy: an agent editing the project checker cannot
# cause the next integrity check to run the edited code.
cp ./check_features.py "$run_dir/check_features.py"
checker="$run_dir/check_features.py"
baseline="$run_dir/baseline.json"
if ! "$PYTHON" "$checker" snapshot --output "$baseline"; then exit 3; fi

log() {
    printf '%s\n' "$1" >> progress.md
}
verify() {
    # Private, run-local transcript; never print/refeed raw agent/check output.
    if ./verify.sh >"$run_dir/verify-output" 2>&1; then
        verify_status=0
    else
        verify_status=$?
    fi
}
guard() {
    if ! "$PYTHON" "$checker" integrity --baseline "$baseline"; then
        log "- FAILED: frozen check/spec integrity changed; human review required."
        exit 6
    fi
}
done_check() {
    [ "$verify_status" -eq 0 ] &&
        "$PYTHON" "$checker" complete --baseline "$baseline" >/dev/null 2>&1
}

verify
guard
if done_check; then
    echo "VERIFIED green — checks and all feature evidence pass"
    log "- VERIFIED: already complete; verifier and feature evidence passed."
    exit 0
fi
last_verify_status=$verify_status
stall=0
failures=0
i=0
failure=""
while [ "$i" -lt "$MAX_ITER" ]; do
    i=$((i + 1))
    echo "=== iteration $i/$MAX_ITER ==="
    before=$("$PYTHON" "$checker" fingerprint) || exit 3
    cp ./PROMPT.md "$run_dir/brief"
    if [ "$failures" -eq 1 ]; then
        printf '\nPrevious failure (verbatim status): %s\n' "$failure" >>"$run_dir/brief"
        printf 'This is the only retry. Diagnose it; do not repeat blindly.\n' >>"$run_dir/brief"
    fi
    # Intentional word splitting; no eval and no shell interpretation.
    # shellcheck disable=SC2086
    if $AGENT_CMD <"$run_dir/brief" >"$run_dir/agent-output" 2>&1; then
        agent_status=0
    else
        agent_status=$?
    fi
    guard
    if [ "$agent_status" -ne 0 ]; then
        failure="agent command exited with status $agent_status"
    else
        verify
        guard
        if [ "$verify_status" -ne 0 ]; then
            failure="verification command exited with status $verify_status"
        else
            failure=""
        fi
    fi
    if [ -n "$failure" ]; then
        failures=$((failures + 1))
        echo "FAILED: $failure"
        log "- Iteration $i FAILED: $failure."
        if [ "$failures" -ge 2 ]; then
            echo "FAILED twice — stopping for descope or human review" >&2
            exit 1
        fi
        continue
    fi
    failures=0
    if grep -Fxq 'DONE_ALL' "$run_dir/agent-output"; then
        echo "completion marker seen — checking independent completion gate"
    fi
    if done_check; then
        echo "VERIFIED green — checks and all feature evidence pass"
        log "- Iteration $i VERIFIED: verifier and all feature evidence passed."
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
    if [ "$stall" -ge 2 ]; then
        echo "STALLED — no project-content or check-status delta for two iterations" >&2
        exit 2
    fi
done
log "- INCOMPLETE: hard iteration cap reached."
echo "INCOMPLETE — hard iteration cap reached" >&2
exit 4
