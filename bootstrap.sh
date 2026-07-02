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
#   ABILITIES_REPO  git URL to clone from
#                   (default: https://github.com/tapiwamakandigona/subagent-toolkit.git)
#   ABILITIES_DIR   same as TARGET_DIR
#
# Behavior:
#   - If TARGET_DIR is already a git checkout, fast-forward it (best effort).
#   - If this script is running from inside a checkout and no clone is needed,
#     it just uses that checkout.
#   - Prints a manifest of skills / agent roles / prompt templates, then a
#     ready-to-paste "context primer" block for the agent.
#
# Dependencies: git, grep, sed, awk. Uses python3 for richer parsing if present.

set -eu
# pipefail where supported (dash lacks it; ignore failure)
(set -o pipefail) 2>/dev/null && set -o pipefail

REPO_URL="${ABILITIES_REPO:-https://github.com/tapiwamakandigona/subagent-toolkit.git}"
TARGET="${1:-${ABILITIES_DIR:-./.abilities}}"

log() { printf '%s\n' "$*" >&2; }

# ---------------------------------------------------------------- install ---
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -f "$TARGET/bootstrap.sh" ]; then
  # Existing checkout: try to update, but never fail the run over it.
  if [ -d "$TARGET/.git" ]; then
    log "==> Updating existing ability pack in $TARGET"
    git -C "$TARGET" pull --ff-only 2>/dev/null || log "    (update skipped: offline or diverged — using existing copy)"
  else
    log "==> Using existing ability pack in $TARGET (not a git checkout)"
  fi
elif [ -f "$SELF_DIR/README.md" ] && [ -d "$SELF_DIR/agents" ]; then
  # Running from inside a checkout already — no clone needed.
  TARGET="$SELF_DIR"
  log "==> Running from checkout at $TARGET"
else
  log "==> Cloning ability pack into $TARGET"
  git clone --depth 1 "$REPO_URL" "$TARGET"
fi

# Normalize to absolute path for the primer.
TARGET=$(CDPATH= cd -- "$TARGET" && pwd)

# ------------------------------------------------------------- manifest -----
# Extract a single-line YAML frontmatter value ("key: value") from a file.
# Only scans the first frontmatter block (between the first pair of --- lines).
fm_value() { # $1=file $2=key
  awk -v key="$2" '
    NR==1 && $0!="---" { exit }
    NR>1 && $0=="---"  { exit }
    NR>1 {
      if (index($0, key":")==1) {
        val=substr($0, length(key)+2)
        sub(/^[ \t]+/, "", val)
        gsub(/^["'\'']|["'\'']$/, "", val)
        print val
        exit
      }
    }
  ' "$1"
}

truncate80() { awk '{ if (length($0)>96) print substr($0,1,93) "..."; else print }'; }

list_skills() {
  [ -d "$TARGET/skills" ] || return 0
  for f in "$TARGET"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    name=$(fm_value "$f" name)
    desc=$(fm_value "$f" description)
    [ -n "$name" ] || name=$(basename "$(dirname "$f")")
    printf '  %-28s %s\n' "$name" "$(printf '%s' "$desc" | truncate80)"
  done
}

list_agents() {
  [ -d "$TARGET/agents" ] || return 0
  for f in "$TARGET"/agents/*.md; do
    [ -f "$f" ] || continue
    name=$(fm_value "$f" name)
    desc=$(fm_value "$f" description)
    [ -n "$name" ] || name=$(basename "$f" .md)
    printf '  %-28s %s\n' "$name" "$(printf '%s' "$desc" | truncate80)"
  done
}

list_prompts() {
  [ -d "$TARGET/prompts" ] || return 0
  for f in "$TARGET"/prompts/*.md; do
    [ -f "$f" ] || continue
    name=$(basename "$f" .md)
    # First non-heading, non-empty line as the description.
    desc=$(grep -v '^#' "$f" | grep -v '^[[:space:]]*$' | sed -n '1p')
    printf '  %-28s %s\n' "$name" "$(printf '%s' "$desc" | truncate80)"
  done
}

echo ""
echo "=== subagent-toolkit manifest ($TARGET) ==="
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
  log "(machine-readable: python3 $TARGET/harness/scripts/manifest.py $TARGET)"
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
  assigned you a role, read that file and follow its process and report format
  exactly. If not, pick the closest role and note the choice in your report.
- PROMPTS  ($TARGET/prompts/): templates for briefing subagents, planning,
  self-review, verification, and handoff reports. Use handoff-report.md to
  structure your final report.
- HARNESS  ($TARGET/harness/): orchestration patterns (patterns.md) and context
  discipline rules (context-management.md). Read these before delegating work.

Rules of use:
1. Progressive disclosure: read indexes first, details on demand. Do not bulk-load.
2. Cite file paths in reports instead of pasting file contents.
3. If a skill's instructions conflict with your orchestrator's objective, the
   objective wins — say so in your report.
=== END CONTEXT PRIMER ===
EOF
