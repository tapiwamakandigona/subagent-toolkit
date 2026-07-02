#!/bin/sh
# bootstrap.sh — install the subagent-toolkit ability pack and print a context primer.
#
# Usage:
#   sh bootstrap.sh [TARGET_DIR]
#
#   TARGET_DIR   where to clone/find the repo (default: ./.abilities,
#                override with arg 1 or $ABILITIES_DIR)
#
# Environment:
#   ABILITIES_REPO       git URL to clone from
#                        (default: https://github.com/tapiwamakandigona/subagent-toolkit.git)
#   ABILITIES_DIR        same as TARGET_DIR
#   ABILITIES_REF        git tag/branch/commit to check out after clone/update
#                        (pin a version for reproducible fan-outs)
#   ABILITIES_NO_UPDATE  set to 1 to skip the auto `git pull` on existing checkouts
#
# Behavior:
#   - If TARGET_DIR is already a git checkout, fast-forward it (best effort,
#     unless ABILITIES_NO_UPDATE=1).
#   - If this script is running from inside a checkout and no target was
#     explicitly given, it just uses that checkout.
#   - Prints a manifest of skills / agent roles / prompt templates, then a
#     ready-to-paste "context primer" block for the agent.
#
# Dependencies: git (for clone/update), grep, sed, awk. Uses python3 for
# richer parsing if present.

set -eu
# pipefail where supported (dash lacks it; ignore failure)
# shellcheck disable=SC3040
(set -o pipefail) 2>/dev/null && set -o pipefail

REPO_URL="${ABILITIES_REPO:-https://github.com/tapiwamakandigona/subagent-toolkit.git}"
REF="${ABILITIES_REF:-}"
NO_UPDATE="${ABILITIES_NO_UPDATE:-}"

# Track whether the user explicitly chose a target (arg 1 or $ABILITIES_DIR).
EXPLICIT_TARGET=1
if [ "$#" -ge 1 ] && [ -n "$1" ]; then
  TARGET="$1"
elif [ -n "${ABILITIES_DIR:-}" ]; then
  TARGET="$ABILITIES_DIR"
else
  TARGET="./.abilities"
  EXPLICIT_TARGET=0
fi

log() { printf '%s\n' "$*" >&2; }

die() {
  log "error: $*"
  exit 1
}

require_git() {
  command -v git >/dev/null 2>&1 || die "git is required to install the ability pack but was not found in PATH.
       Install git, or point at an existing copy: sh bootstrap.sh /path/to/checkout"
}

checkout_ref() { # $1=dir
  [ -n "$REF" ] || return 0
  require_git
  # Make the ref resolvable locally. A bare `git fetch origin <ref>` only
  # updates FETCH_HEAD (no local tag/branch ref), so try explicit refspecs
  # first: tag, then branch, then a plain fetch (covers commit SHAs and
  # servers that reject refspec fetches), then a full fetch as last resort.
  fetched=0
  if git -C "$1" fetch --depth 1 origin \
       "refs/tags/$REF:refs/tags/$REF" >/dev/null 2>&1; then
    fetched=1
  elif git -C "$1" fetch --depth 1 origin \
         "refs/heads/$REF:refs/remotes/origin/$REF" >/dev/null 2>&1; then
    fetched=1
  elif git -C "$1" fetch --depth 1 origin "$REF" >/dev/null 2>&1; then
    fetched=1
  else
    git -C "$1" fetch origin >/dev/null 2>&1 || true
  fi
  if git -C "$1" checkout --quiet "$REF" 2>/dev/null; then
    log "==> Pinned to ref: $REF"
    return 0
  fi
  # The plain-fetch path may have left the ref only in FETCH_HEAD.
  if [ "$fetched" -eq 1 ] \
       && git -C "$1" checkout --quiet FETCH_HEAD 2>/dev/null; then
    log "==> Pinned to ref: $REF (detached at FETCH_HEAD)"
    return 0
  fi
  die "could not check out ABILITIES_REF='$REF' in $1 (unknown ref, or offline?)"
}

# ---------------------------------------------------------------- install ---
# shellcheck disable=SC1007
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -f "$TARGET/bootstrap.sh" ]; then
  # Existing checkout: try to update, but never fail the run over it.
  if [ -d "$TARGET/.git" ]; then
    if [ "$NO_UPDATE" = "1" ]; then
      log "==> Using existing ability pack in $TARGET (ABILITIES_NO_UPDATE=1, update skipped)"
    else
      log "==> Updating existing ability pack in $TARGET"
      git -C "$TARGET" pull --ff-only >/dev/null 2>&1 \
        || log "    (update skipped: offline or diverged — using existing copy)"
    fi
    checkout_ref "$TARGET"
  else
    log "==> Using existing ability pack in $TARGET (not a git checkout)"
    if [ -n "$REF" ]; then
      log "    warning: ABILITIES_REF ignored: not a git checkout"
    fi
  fi
elif [ "$EXPLICIT_TARGET" -eq 0 ] && [ -f "$SELF_DIR/README.md" ] && [ -d "$SELF_DIR/agents" ]; then
  # Running from inside a checkout and no explicit target — no clone needed.
  TARGET="$SELF_DIR"
  log "==> Running from checkout at $TARGET"
else
  require_git
  if [ -e "$TARGET" ] && [ ! -d "$TARGET" ]; then
    die "target '$TARGET' exists and is not a directory"
  fi
  if [ -d "$TARGET" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
    die "target directory '$TARGET' exists and is not empty (and has no bootstrap.sh).
       Remove it, pick another directory, or point at an existing checkout."
  fi
  log "==> Cloning ability pack into $TARGET"
  if [ -n "$REF" ]; then
    git clone --depth 1 --branch "$REF" "$REPO_URL" "$TARGET" >/dev/null 2>&1 \
      || { git clone "$REPO_URL" "$TARGET" >/dev/null 2>&1 \
             || die "clone failed (offline? bad ref?). If you have a local copy, run: sh bootstrap.sh /path/to/checkout"
           checkout_ref "$TARGET"; }
  else
    git clone --depth 1 "$REPO_URL" "$TARGET" >/dev/null 2>&1 \
      || die "clone failed (offline?). If you have a local copy, run: sh bootstrap.sh /path/to/checkout"
  fi
fi

# Normalize to absolute path for the primer.
# shellcheck disable=SC1007
TARGET=$(CDPATH= cd -- "$TARGET" && pwd)

# Resolve the installed version/ref for the manifest header (best effort).
VERSION=""
if [ -d "$TARGET/.git" ] && command -v git >/dev/null 2>&1; then
  VERSION=$(git -C "$TARGET" describe --tags --always 2>/dev/null || true)
fi
[ -n "$VERSION" ] || VERSION="unknown"

# ------------------------------------------------------------- manifest -----
# Extract a single-line YAML frontmatter value ("key: value") from a file.
# Only scans the first frontmatter block (between the first pair of --- lines).
# Tolerates CRLF line endings; strips only symmetric surrounding quotes.
fm_value() { # $1=file $2=key
  awk -v key="$2" '
    { sub(/\r$/, "") }
    NR==1 && $0!="---" { exit }
    NR>1 && $0=="---"  { exit }
    NR>1 {
      if (index($0, key":")==1) {
        val=substr($0, length(key)+2)
        sub(/^[ \t]+/, "", val)
        sub(/[ \t]+$/, "", val)
        n=length(val)
        if (n>=2) {
          first=substr(val,1,1); last=substr(val,n,1)
          if ((first=="\"" && last=="\"") || (first=="\047" && last=="\047"))
            val=substr(val,2,n-2)
        }
        print val
        exit
      }
    }
  ' "$1"
}

# Truncate long description lines so the manifest stays scannable.
truncate_line() { awk '{ if (length($0)>96) print substr($0,1,93) "..."; else print }'; }

list_skills() {
  [ -d "$TARGET/skills" ] || return 0
  for f in "$TARGET"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    name=$(fm_value "$f" name)
    desc=$(fm_value "$f" description)
    [ -n "$name" ] || name=$(basename "$(dirname "$f")")
    printf '  %-28s %s\n' "$name" "$(printf '%s' "$desc" | truncate_line)"
  done
}

list_agents() {
  [ -d "$TARGET/agents" ] || return 0
  for f in "$TARGET"/agents/*.md; do
    [ -f "$f" ] || continue
    case "$f" in */README.md) continue ;; esac
    name=$(fm_value "$f" name)
    desc=$(fm_value "$f" description)
    [ -n "$name" ] || name=$(basename "$f" .md)
    printf '  %-28s %s\n' "$name" "$(printf '%s' "$desc" | truncate_line)"
  done
}

list_prompts() {
  [ -d "$TARGET/prompts" ] || return 0
  for f in "$TARGET"/prompts/*.md; do
    [ -f "$f" ] || continue
    name=$(basename "$f" .md)
    # First non-heading, non-empty line as the description.
    desc=$(grep -v '^#' "$f" | grep -v '^[[:space:]]*$' | sed -n '1p')
    printf '  %-28s %s\n' "$name" "$(printf '%s' "$desc" | truncate_line)"
  done
}

echo ""
echo "=== subagent-toolkit manifest ($TARGET, version: $VERSION) ==="
echo ""
echo "SKILLS (read skills/<name>/SKILL.md when description matches your task):"
list_skills
echo ""
echo "AGENT ROLES (agents/<name>.md — adopt as system prompt):"
list_agents
echo ""
echo "PROMPT TEMPLATES (prompts/<name>.md — fill {{placeholders}}):"
list_prompts
echo ""

# JSON manifest if python3 is available (optional, for orchestrators).
if command -v python3 >/dev/null 2>&1 && [ -f "$TARGET/harness/scripts/manifest.py" ]; then
  log "(machine-readable: python3 '$TARGET/harness/scripts/manifest.py' '$TARGET')"
fi

# --------------------------------------------------------- context primer ---
cat <<EOF
=== CONTEXT PRIMER — paste or keep this in working memory ===
You now have the subagent-toolkit ability pack at: $TARGET

What you gained:
- SKILLS   ($TARGET/skills/): proven procedures. Before starting any task, scan
  the skill list above; if a description matches your task, read that SKILL.md
  in full. Load its references/ files only when the SKILL.md directs you to.
- ROLES    ($TARGET/agents/): focused system prompts. If your orchestrator
  assigned you a role, read that file and follow its process exactly (its
  report format fills the handoff-report RESULT section). If not, pick the
  closest role and note the choice in your report.
- PROMPTS  ($TARGET/prompts/): templates for briefing subagents, planning,
  self-review, verification, and handoff reports. Use handoff-report.md as the
  envelope of your final report; an assigned role's report format fills its
  RESULT section.
- HARNESS  ($TARGET/harness/): orchestration patterns (patterns.md) and context
  discipline rules (context-management.md). Read these before delegating work.

Rules of use:
1. Progressive disclosure: read indexes first, details on demand. Do not bulk-load.
2. Cite file paths in reports instead of pasting file contents.
3. On conflict, precedence is: orchestrator objective > role file > prompt
   templates > skills. Whatever loses, note the conflict in your report.
=== END CONTEXT PRIMER ===
EOF
