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

  # --- 5. ABILITIES_REF: pin a tag on an EXISTING checkout ------------------
  # Build a file:// remote fixture with two tags, clone it (lands on the tip),
  # then re-run bootstrap with ABILITIES_REF pointing at the OLDER tag. The
  # existing-checkout path must fetch the tag ref and check it out (exit 0).
  fixroot=$(mktemp -d)   # no spaces: file:// URLs and spaces don't mix
  fixture="$fixroot/remote"
  mkdir -p "$fixture"
  (
    cd "$fixture"
    git init --quiet
    git config user.email smoke@example.invalid
    git config user.name smoke
    cp "$REPO_ROOT/bootstrap.sh" .
    printf '# fixture v1\n' >README.md
    mkdir -p agents skills
    printf 'placeholder\n' >agents/.keep
    printf 'placeholder\n' >skills/.keep
    git add -A
    git commit --quiet -m 'fixture: first release'
    git tag v9.9.8-test
    printf '# fixture v2\n' >README.md
    git commit --quiet -am 'fixture: second release'
    git tag v9.9.9-test
  )
  pin_target="$work/pin target"
  git clone --quiet "file://$fixture" "$pin_target" 2>/dev/null
  out5="$work/out5.txt"
  if (cd "$work" && ABILITIES_REPO="file://$fixture" ABILITIES_REF=v9.9.8-test \
        "$shell" "$REPO_ROOT/bootstrap.sh" "$pin_target" >"$out5" 2>"$work/err5.txt"); then
    pass "$shell: tag pin on existing checkout exits 0"
  else
    fail "$shell: tag pin on existing checkout failed (see $work/err5.txt)"
  fi
  want=$(git -C "$fixture" rev-parse "v9.9.8-test^{commit}")
  got=$(git -C "$pin_target" rev-parse HEAD 2>/dev/null || echo none)
  if [ "$got" = "$want" ]; then
    pass "$shell: existing checkout is pinned at the requested tag"
  else
    fail "$shell: HEAD is $got, expected tag commit $want"
  fi
  if grep -q 'Pinned to ref: v9.9.8-test' "$work/err5.txt"; then
    pass "$shell: pin confirmation logged to stderr"
  else
    fail "$shell: no pin confirmation in stderr (see $work/err5.txt)"
  fi
  check_output "$shell/tag-pin" "$out5"

  # --- 6. locally-resolvable ref + NO_UPDATE: zero network needed -----------
  # Delete the fixture remote so any fetch/pull would fail, then re-pin the
  # same tag with ABILITIES_NO_UPDATE=1. The ref resolves locally, so the
  # run must succeed entirely offline.
  rm -rf "$fixture"
  out6="$work/out6.txt"
  if (cd "$work" && ABILITIES_NO_UPDATE=1 ABILITIES_REF=v9.9.8-test \
        "$shell" "$REPO_ROOT/bootstrap.sh" "$pin_target" >"$out6" 2>"$work/err6.txt"); then
    pass "$shell: local-ref pin succeeds with remote gone (no fetch)"
  else
    fail "$shell: local-ref pin failed offline (see $work/err6.txt)"
  fi
  if grep -q 'resolved locally, no fetch' "$work/err6.txt"; then
    pass "$shell: local-ref pin skipped the network"
  else
    fail "$shell: no local-resolution confirmation in stderr"
  fi
  check_output "$shell/local-pin" "$out6"
  rm -rf "$fixroot"

  # --- 7. tampered target (bootstrap.sh present, agents/skills missing) -----
  bad_target="$work/tampered target"
  mkdir -p "$bad_target"
  cp "$REPO_ROOT/bootstrap.sh" "$bad_target/"
  if (cd "$work" && "$shell" "$REPO_ROOT/bootstrap.sh" "$bad_target" \
        >"$work/out7.txt" 2>"$work/err7.txt"); then
    fail "$shell: tampered target was accepted (should die)"
  else
    pass "$shell: tampered target rejected"
  fi
  if grep -q 'missing agents/ and/or skills/' "$work/err7.txt"; then
    pass "$shell: tampered target error names the missing dirs"
  else
    fail "$shell: tampered-target error message missing (see $work/err7.txt)"
  fi
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
