#!/usr/bin/env python3
"""Fail if leftover {{placeholder}} tokens remain in the given files/dirs.

Prompt templates (prompts/) legitimately contain {{placeholders}} — do not
point this script at them. Everything else that ships to an agent (skills,
agents, harness docs, worked examples) must be fully filled in.

Placeholders inside fenced code blocks or `inline code` are treated as
examples, not unfilled slots, and are ignored.

Usage:
    python3 check_placeholders.py <file-or-dir> [more...]

Exit code 0 when clean, 1 when any placeholder is found (locations printed),
2 on usage error. Stdlib only.
"""

import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]*\}\}")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
TEXT_SUFFIXES = {".md", ".txt", ".sh", ".py", ".json", ".yaml", ".yml"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv"}


def iter_files(target: Path):
    if target.is_file():
        yield target
        return
    for p in sorted(target.rglob("*")):
        if p.is_file() and p.suffix in TEXT_SUFFIXES and not (
            set(p.parts) & SKIP_DIRS
        ):
            yield p


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    hits = 0
    for arg in argv[1:]:
        target = Path(arg)
        if not target.exists():
            print(f"error: no such path: {target}", file=sys.stderr)
            return 2
        for path in iter_files(target):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                print(f"error: cannot read {path}: {e}", file=sys.stderr)
                return 2
            in_fence = False
            for lineno, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    # code blocks show placeholders as examples, not slots
                    continue
                for m in PLACEHOLDER_RE.finditer(INLINE_CODE_RE.sub("", line)):
                    print(f"{path}:{lineno}: leftover placeholder {m.group(0)}")
                    hits += 1
    if hits:
        print(f"\n{hits} leftover placeholder(s) found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
