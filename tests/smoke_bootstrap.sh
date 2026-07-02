#!/bin/sh
# smoke_bootstrap.sh — end-to-end smoke test for bootstrap.sh.
#
# Runs bootstrap under sh AND dash (when available) inside a temp dir whose
# path contains spaces, using the local repo as the clone source (no network).
# Asserts: exit 0, the context-primer sentinel appears on stdout, stdout has
# no git noise, and an explicitly passed TARGET_DIR is honored even when the
# script runs from inside a checkout.
#
# Usage: sh tests/smoke_bootstrap.sh

set -eu

# shellcheck disable=SC1007

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FAILURES=0

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  FAILURES=$((FAILURES + 1))
}

pass() {
  printf 'ok: %s\n' "$*"
}

check_output() { # $1=label $2=stdout-file
  if grep -q '=== CONTEXT PRIMER' "$2"; then
    pass "$1: primer sentinel on stdout"
  else
    fail "$1: primer sentinel missing from stdout"
  fi
  if grep -Eq 'Already up to date|Cloning into|Updating [0-9a-f]+\.\.|Fast-forward' "$2"; then
    fail "$1: git noise leaked to stdout"
  else
    pass "$1: no git noise on stdout"
  fi
}

run_suite() { # $1=shell
  shell="$1"
  work=$(mktemp -d)/"dir with spaces"
  mkdir -p "$work"

  # --- 1. explicit target honored even though script runs from a checkout ---
  target="$work/custom target"
  out="$work/out1.txt"
  if (cd "$work" && ABILITIES_REPO="file://$REPO_ROOT" \
        "$shell" "$REPO_ROOT/bootstrap.sh" "$target" >"$out" 2>"$work/err1.txt"); then
    pass "$shell: explicit-target run exits 0"
  else
    fail "$shell: explicit-target run failed (see $work/err1.txt)"
  fi
  if [ -f "$target/README.md" ] && [ -d "$target/agents" ]; then
    pass "$shell: explicit target directory was used"
  else
    fail "$shell: explicit target '$target' was NOT populated"
  fi
  if grep -q "custom target" "$out"; then
    pass "$shell: primer points at the explicit target"
  else
    fail "$shell: primer does not mention the explicit target"
  fi
  check_output "$shell/explicit-target" "$out"

  # --- 2. re-run against the existing checkout (update path) ---------------
  out2="$work/out2.txt"
  if (cd "$work" && ABILITIES_REPO="file://$REPO_ROOT" \
        "$shell" "$REPO_ROOT/bootstrap.sh" "$target" >"$out2" 2>"$work/err2.txt"); then
    pass "$shell: re-run (update path) exits 0"
  else
    fail "$shell: re-run failed (see $work/err2.txt)"
  fi
  check_output "$shell/update" "$out2"

  # --- 3. ABILITIES_NO_UPDATE=1 skips the pull ------------------------------
  out3="$work/out3.txt"
  if (cd "$work" && ABILITIES_NO_UPDATE=1 \
        "$shell" "$REPO_ROOT/bootstrap.sh" "$target" >"$out3" 2>"$work/err3.txt"); then
    pass "$shell: ABILITIES_NO_UPDATE run exits 0"
  else
    fail "$shell: ABILITIES_NO_UPDATE run failed"
  fi
  if grep -q 'update skipped' "$work/err3.txt"; then
    pass "$shell: ABILITIES_NO_UPDATE skipped the update"
  else
    fail "$shell: ABILITIES_NO_UPDATE did not skip the update"
  fi
  check_output "$shell/no-update" "$out3"

  # --- 4. no explicit target, run from checkout: uses the checkout ---------
  out4="$work/out4.txt"
  if (cd "$work" && "$shell" "$REPO_ROOT/bootstrap.sh" >"$out4" 2>"$work/err4.txt"); then
    pass "$shell: run-from-checkout exits 0"
  else
    fail "$shell: run-from-checkout failed"
  fi
  if grep -q "$REPO_ROOT" "$out4"; then
    pass "$shell: run-from-checkout primer points at the checkout"
  else
    fail "$shell: run-from-checkout primer does not point at the checkout"
  fi
  check_output "$shell/self-dir" "$out4"
}

run_suite sh
if command -v dash >/dev/null 2>&1; then
  run_suite dash
else
  printf 'skip: dash not installed\n'
fi

if [ "$FAILURES" -gt 0 ]; then
  printf '\n%s smoke-test failure(s)\n' "$FAILURES" >&2
  exit 1
fi
printf '\nall bootstrap smoke tests passed\n'
