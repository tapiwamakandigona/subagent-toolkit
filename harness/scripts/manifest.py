#!/usr/bin/env python3
"""Print a JSON manifest of the subagent-toolkit ability pack.

Walks a toolkit checkout and emits skills, agent roles, and prompt templates
with their names and descriptions, suitable for orchestrators building
skill-routing tables. Doubles as a lint: items with missing/invalid
frontmatter are listed under "warnings" (and softer notes under "info").

Usage:
    python3 manifest.py [--check] [TOOLKIT_ROOT]   # default root: repo root above this script

    --check   strict lint mode: exit 1 when any warnings are present

Stdlib only. Exit code 0 on success (even with warnings, unless --check),
1 on bad root or (with --check) on warnings.
"""

import json
import re
import sys
from pathlib import Path

# Frontmatter: opening --- on the first line, closing --- possibly at EOF
# without a trailing newline. Tolerates CRLF line endings.
FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---[ \t]*\r?(?:\n|\Z)", re.DOTALL)

NAME_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]*\}\}")
BODY_TOKEN_BUDGET = 3000  # rough estimate: chars / 4
RESOURCE_JUNK_DIRS = {"__pycache__", ".pytest_cache", ".git"}
RESOURCE_JUNK_SUFFIXES = (".pyc", ".pyo", ".swp", ".swo", "~")


def parse_frontmatter(text, problems=None):
    """Parse simple YAML frontmatter into a dict.

    Supports single-line 'key: value' pairs plus one level of nesting
    (e.g. 'metadata:' followed by two-space-indented 'key: value' lines,
    which becomes a nested dict). Tolerates CRLF and a closing '---' at
    EOF without a trailing newline. Folded/literal scalars ('>' / '|')
    are not supported; if `problems` (a list) is given, a note is appended
    when one is detected.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    current_map = None  # name of the nested map we're inside, if any
    for raw in m.group(1).splitlines():
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line.startswith((" ", "\t"))
        if indented:
            if current_map is None:
                if problems is not None:
                    problems.append(
                        f"unexpected indented line in frontmatter: {line.strip()!r}"
                    )
                continue
            stripped = line.strip()
            if ":" not in stripped:
                if problems is not None:
                    problems.append(
                        f"unparseable line in nested map {current_map!r}: {stripped!r}"
                    )
                continue
            key, _, value = stripped.partition(":")
            fields[current_map][key.strip()] = _clean_value(value, key, problems)
            continue
        current_map = None
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if value.strip() == "":
            # Either an empty value or the start of a nested map; treat as a
            # nested map and let lint flag empty scalars separately.
            fields[key] = {}
            current_map = key
        else:
            fields[key] = _clean_value(value, key, problems)
    # Collapse nested maps that never received children back to empty string
    # (they were empty scalar values, e.g. 'description:').
    for key, val in list(fields.items()):
        if isinstance(val, dict) and not val:
            fields[key] = ""
    return fields


def _clean_value(value, key, problems):
    value = value.strip()
    if value in (">", "|") or value.startswith((">-", ">+", "|-", "|+")):
        if problems is not None:
            problems.append(
                f"key {key!r} uses a folded/literal scalar ({value!r}); "
                "only single-line values are supported"
            )
        return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def first_prose_line(text):
    """First non-heading, non-empty line of a markdown file (for prompts)."""
    body = FRONTMATTER_RE.sub("", text, count=1)
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


def _body_text(text):
    return FRONTMATTER_RE.sub("", text, count=1)


CODE_FENCE_RE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _strip_code(text):
    """Remove fenced code blocks and inline code spans (placeholders there
    are examples, not unfilled template slots)."""
    return INLINE_CODE_RE.sub("", CODE_FENCE_RE.sub("", text))


def _is_resource_junk(path):
    if any(part in RESOURCE_JUNK_DIRS for part in path.parts):
        return True
    return path.name.endswith(RESOURCE_JUNK_SUFFIXES) or path.name == ".DS_Store"


def _lint_common(rel, fm, text, warnings, info, problems):
    for p in problems:
        warnings.append(f"{rel}: {p}")
    name = fm.get("name", "")
    desc = fm.get("description")
    if "name" not in fm or not name:
        warnings.append(f"{rel}: missing or empty 'name' in frontmatter")
    if "description" not in fm:
        warnings.append(f"{rel}: missing 'description' in frontmatter")
    elif not desc:
        warnings.append(f"{rel}: 'description' is present but empty")
    if name and isinstance(name, str):
        if not NAME_RE.fullmatch(name):
            warnings.append(
                f"{rel}: name {name!r} is not lowercase-hyphens "
                "(no leading/trailing/consecutive hyphens)"
            )
        if len(name) > 64:
            warnings.append(f"{rel}: name exceeds 64 chars")
    if isinstance(desc, str) and len(desc) > 1024:
        warnings.append(f"{rel}: description exceeds 1024 chars")
    if "license" not in fm:
        info.append(f"{rel}: no 'license' key in frontmatter")
    metadata = fm.get("metadata")
    if not (isinstance(metadata, dict) and metadata.get("version")):
        info.append(f"{rel}: no 'metadata.version' in frontmatter")
    body = _body_text(text)
    est_tokens = len(body) // 4
    if est_tokens > BODY_TOKEN_BUDGET:
        warnings.append(
            f"{rel}: body is ~{est_tokens} tokens (budget {BODY_TOKEN_BUDGET}); "
            "move detail into references/"
        )
    prose = _strip_code(body)
    m = PLACEHOLDER_RE.search(prose)
    if m:
        warnings.append(
            f"{rel}: leftover template placeholder {m.group(0)!r} in body"
        )


def collect_skills(root, warnings, info):
    skills = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return skills
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        problems = []
        fm = parse_frontmatter(text, problems)
        rel = skill_md.relative_to(root)
        _lint_common(rel, fm, text, warnings, info, problems)
        name = fm.get("name", "")
        if name and isinstance(name, str) and name != skill_md.parent.name:
            warnings.append(
                f"{rel}: name {name!r} does not match directory "
                f"{skill_md.parent.name!r}"
            )
        entry = {
            "name": name or skill_md.parent.name,
            "description": fm.get("description", "") if isinstance(fm.get("description"), str) else "",
            "path": str(rel),
        }
        version = ""
        metadata = fm.get("metadata")
        if isinstance(metadata, dict):
            version = metadata.get("version", "")
        if version:
            entry["version"] = version
        refs = sorted(
            str(p.relative_to(root))
            for p in skill_md.parent.rglob("*")
            if p.is_file() and p.name != "SKILL.md" and not _is_resource_junk(p)
        )
        if refs:
            entry["resources"] = refs
        skills.append(entry)
    return skills


def collect_agents(root, warnings, info):
    agents = []
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return agents
    for md in sorted(agents_dir.glob("*.md")):
        if md.name == "README.md":  # index file, not a role
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        problems = []
        fm = parse_frontmatter(text, problems)
        rel = md.relative_to(root)
        _lint_common(rel, fm, text, warnings, info, problems)
        agents.append(
            {
                "name": fm.get("name", md.stem) or md.stem,
                "description": fm.get("description", "") if isinstance(fm.get("description"), str) else "",
                "recommended_capability_profile": fm.get(
                    "recommended_capability_profile", ""
                ),
                "recommended_model": fm.get("recommended_model", ""),
                "path": str(rel),
            }
        )
    return agents


def collect_prompts(root):
    # Prompt templates legitimately contain {{placeholders}} — no lint here.
    prompts = []
    prompts_dir = root / "prompts"
    if not prompts_dir.is_dir():
        return prompts
    for md in sorted(prompts_dir.rglob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        rel_name = md.relative_to(prompts_dir).with_suffix("")
        prompts.append(
            {
                "name": "/".join(rel_name.parts),
                "description": first_prose_line(text),
                "path": str(md.relative_to(root)),
            }
        )
    return prompts


def build_manifest(root):
    warnings = []
    info = []
    manifest = {
        "toolkit": "subagent-toolkit",
        "root": str(root),
        "skills": collect_skills(root, warnings, info),
        "agents": collect_agents(root, warnings, info),
        "prompts": collect_prompts(root),
    }
    if not (manifest["skills"] or manifest["agents"] or manifest["prompts"]):
        warnings.append(
            f"{root}: no skills/, agents/, or prompts/ content found — "
            "is this really a toolkit root?"
        )
    if warnings:
        manifest["warnings"] = warnings
    if info:
        manifest["info"] = info
    return manifest


def main(argv):
    args = [a for a in argv[1:] if a != "--check"]
    check = "--check" in argv[1:]
    if args:
        root = Path(args[0]).resolve()
    else:
        root = Path(__file__).resolve().parent.parent.parent
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1

    manifest = build_manifest(root)
    json.dump(manifest, sys.stdout, indent=2)
    print()
    if check and manifest.get("warnings"):
        print(
            f"check failed: {len(manifest['warnings'])} warning(s)", file=sys.stderr
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
