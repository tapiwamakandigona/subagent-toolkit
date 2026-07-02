#!/usr/bin/env python3
"""Print a JSON manifest of the subagent-toolkit ability pack.

Walks a toolkit checkout and emits skills, agent roles, and prompt templates
with their names and descriptions, suitable for orchestrators building
skill-routing tables. Doubles as a lint: items with missing/invalid
frontmatter are listed under "warnings".

Usage:
    python3 manifest.py [TOOLKIT_ROOT]      # default: repo root above this script

Stdlib only. Exit code 0 on success (even with warnings), 1 on bad root.
"""

import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text):
    """Parse simple single-line 'key: value' YAML frontmatter. Returns dict."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith((" ", "\t", "#")):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def first_prose_line(text):
    """First non-heading, non-empty line of a markdown file (for prompts)."""
    body = FRONTMATTER_RE.sub("", text, count=1)
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


def collect_skills(root, warnings):
    skills = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return skills
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
        rel = skill_md.relative_to(root)
        name = fm.get("name", "")
        desc = fm.get("description", "")
        if not name or not desc:
            warnings.append(f"{rel}: missing 'name' or 'description' in frontmatter")
        if name and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            warnings.append(f"{rel}: name {name!r} is not lowercase-hyphens")
        if len(name) > 64:
            warnings.append(f"{rel}: name exceeds 64 chars")
        if len(desc) > 1024:
            warnings.append(f"{rel}: description exceeds 1024 chars")
        entry = {
            "name": name or skill_md.parent.name,
            "description": desc,
            "path": str(rel),
        }
        refs = sorted(
            str(p.relative_to(root))
            for p in skill_md.parent.rglob("*")
            if p.is_file() and p.name != "SKILL.md"
        )
        if refs:
            entry["resources"] = refs
        skills.append(entry)
    return skills


def collect_agents(root, warnings):
    agents = []
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return agents
    for md in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        rel = md.relative_to(root)
        if not fm.get("name") or not fm.get("description"):
            warnings.append(f"{rel}: missing 'name' or 'description' in frontmatter")
        agents.append(
            {
                "name": fm.get("name", md.stem),
                "description": fm.get("description", ""),
                "recommended_capability_profile": fm.get(
                    "recommended_capability_profile", ""
                ),
                "recommended_model": fm.get("recommended_model", ""),
                "path": str(rel),
            }
        )
    return agents


def collect_prompts(root):
    prompts = []
    prompts_dir = root / "prompts"
    if not prompts_dir.is_dir():
        return prompts
    for md in sorted(prompts_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        prompts.append(
            {
                "name": md.stem,
                "description": first_prose_line(text),
                "path": str(md.relative_to(root)),
            }
        )
    return prompts


def main(argv):
    if len(argv) > 1:
        root = Path(argv[1]).resolve()
    else:
        root = Path(__file__).resolve().parent.parent.parent
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    warnings = []
    manifest = {
        "toolkit": "subagent-toolkit",
        "root": str(root),
        "skills": collect_skills(root, warnings),
        "agents": collect_agents(root, warnings),
        "prompts": collect_prompts(root),
    }
    if warnings:
        manifest["warnings"] = warnings
    json.dump(manifest, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
