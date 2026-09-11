#!/bin/sh
# Best-effort isolation prefix for agent/evaluator runs: SANDBOX_CMD=./sandbox.sh
# Imports the Codex model: capability (what the process CAN touch) is separate
# from approval (when it must ASK). This script handles capability only.
#   - environment allowlist: tokens/secrets in the parent env are not inherited
#   - network off unless HARNESS_NET=1 (Codex default: network disabled)
#   - filesystem: bubblewrap when available (project read-write, rest read-only)
# Honest limits: without bubblewrap or user namespaces this is NOT a security
# boundary. The mode actually used is exported as HARNESS_SANDBOX and, when
# HARNESS_SANDBOX_REPORT names a file, written there for the run ledger.
# Usage: ./sandbox.sh <command> [args...]   (stdin/stdout/stderr pass through)

set -eu
[ "$#" -ge 1 ] || { echo "sandbox.sh: missing command" >&2; exit 3; }
project=$(pwd -P)
net="${HARNESS_NET:-0}"
mode=none
runner=""
if command -v bwrap >/dev/null 2>&1 && bwrap --ro-bind / / --dev /dev --proc /proc true 2>/dev/null; then
    mode=bwrap
    runner="bwrap --die-with-parent --new-session --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --bind $project $project --chdir $project"
    [ "$net" = 1 ] || runner="$runner --unshare-net"
elif [ "$net" != 1 ] && command -v unshare >/dev/null 2>&1 && unshare -rn true 2>/dev/null; then
    mode=netns
    runner="unshare -rn"
fi
if [ "$mode" = none ] && [ "${HARNESS_REQUIRE_SANDBOX:-0}" = 1 ]; then
    echo "sandbox.sh: no isolation mechanism available and HARNESS_REQUIRE_SANDBOX=1" >&2
    exit 3
fi
if [ -n "${HARNESS_SANDBOX_REPORT:-}" ]; then
    printf '%s\n' "$mode" >"$HARNESS_SANDBOX_REPORT"
fi
case "$project" in *" "*|*"	"*) echo "sandbox.sh: project path must not contain whitespace" >&2; exit 3 ;; esac
# SANDBOX_KEEP: space-separated extra variable NAMES to pass through (never
# credentials; give the agent a credential file path, not a token value).
value=""
for name in ${SANDBOX_KEEP:-}; do
    case "$name" in *[!A-Za-z0-9_]*|[0-9]*) echo "sandbox.sh: bad SANDBOX_KEEP name" >&2; exit 3 ;; esac
    if eval "[ -n \"\${$name+set}\" ]"; then
        eval "value=\$$name"
        set -- "$name=$value" "$@"
    fi
done
# ${VAR+VAR="$VAR"} passes each allowlisted variable as one word only when set.
# shellcheck disable=SC2086
exec $runner env -i \
    ${PATH+PATH="$PATH"} ${HOME+HOME="$HOME"} ${LANG+LANG="$LANG"} ${LC_ALL+LC_ALL="$LC_ALL"} \
    ${TERM+TERM="$TERM"} ${TMPDIR+TMPDIR="$TMPDIR"} \
    ${HARNESS_RUN_ID+HARNESS_RUN_ID="$HARNESS_RUN_ID"} \
    ${HARNESS_ITERATION+HARNESS_ITERATION="$HARNESS_ITERATION"} \
    HARNESS_SANDBOX="$mode" HARNESS_NET="$net" "$@"
