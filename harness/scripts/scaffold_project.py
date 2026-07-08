#!/usr/bin/env python3
"""Scaffold the project-state files for a full-project run.

The project state protocol (harness/context-management.md §6) requires a
fixed file set at the project root — PROJECT.md, features.json, progress.md,
init.sh, checkpoints/ — created in the Foundation phase
(harness/project-lifecycle.md §1). The templates live in
prompts/artifacts/project-state.md; this script instantiates them so a
foundation run starts from a valid, self-consistent state directory instead
of hand-copied fragments.

What it creates under <dir>:

  PROJECT.md     goal paragraph + artifact pointers (orchestrator fills in
                 the spec/architecture paths and standing decisions)
  features.json  from --features SEED (validated with check_features.py
                 before anything is written), or a single placeholder entry
                 with passes:false so the milestone gate cannot pass until
                 real features replace it
  progress.md    append-only log, seeded with one dated scaffold line
  init.sh        executable stub that exits non-zero until replaced, so a
                 cold-start can never be reported green by accident
  checkpoints/   empty, plus features.baseline.json — the orchestrator's
                 tamper-check snapshot for check_features.py --against

Refuses to touch a directory where any of these already exist: scaffolding
is for new runs, not for repairing live state (exit 1, nothing written).
After writing, it re-validates features.json via the sibling
check_features.py from the target directory (relative evidence paths must
resolve there); on failure it removes everything it wrote, so a failed run
never leaves partial state behind.

Usage:
    python3 scaffold_project.py <dir> --name NAME --goal GOAL
                                [--features SEED.json]

Prints one line per step ("ok: ..." / "FAIL: ..."). Exit code 0 on success,
1 on failure, 2 on usage error. Stdlib only.
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

STATE_FILES = ("PROJECT.md", "features.json", "progress.md", "init.sh")
CHECK_FEATURES = Path(__file__).resolve().parent / "check_features.py"

PROJECT_MD = """\
# {name}
{goal}

Spec: TODO(path)   Architecture: TODO(path)   Task list: TODO(path)
Features: ./features.json   Progress: ./progress.md   Env: ./init.sh

## Standing decisions
- (none yet)
"""

PLACEHOLDER_FEATURES = [
    {
        "id": "replace-me-first-feature",
        "title": "Placeholder written by scaffold_project.py",
        "acceptance": (
            "Replace this entry with real features from the approved spec; "
            "the milestone gate fails until you do"
        ),
        "passes": False,
        "evidence": None,
        "milestone": "m1",
    }
]

INIT_SH = """\
#!/bin/sh
# init.sh — bring the dev environment up from cold (install, migrate, run,
# smoke-test). Keep it true: whoever changes the environment updates it.
# It must exit non-zero on any failure so "environment is up" stays
# machine-checkable (prompts/artifacts/project-state.md).
echo "init.sh: not implemented yet — replace this stub" >&2
exit 1
"""


def fail(msg):
    print(f"FAIL: {msg}")
    print("\n1 check(s) failed", file=sys.stderr)
    return 1


def usage_error(msg):
    print(f"error: {msg}", file=sys.stderr)
    return 2


def validate_seed(seed_path):
    """Run check_features.py (shape + evidence only, no gate) on the seed."""
    proc = subprocess.run(
        [sys.executable, str(CHECK_FEATURES), str(seed_path)],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


def _clean_up(root, created_root):
    """Remove everything the scaffolder wrote so a failed run leaves no state."""
    for name in STATE_FILES:
        (root / name).unlink(missing_ok=True)
    (root / "checkpoints" / "features.baseline.json").unlink(missing_ok=True)
    checkpoints = root / "checkpoints"
    if checkpoints.is_dir() and not any(checkpoints.iterdir()):
        checkpoints.rmdir()
    if created_root and root.is_dir() and not any(root.iterdir()):
        root.rmdir()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scaffold project-state files for a full-project run."
    )
    parser.add_argument("dir", help="project state directory to scaffold")
    parser.add_argument("--name", required=True, help="project name")
    parser.add_argument(
        "--goal",
        required=True,
        help="one-paragraph goal: what exists when this is done, for whom",
    )
    parser.add_argument(
        "--features",
        metavar="SEED",
        help="seed features.json (validated before anything is written)",
    )
    args = parser.parse_args(argv)

    if not args.name.strip() or not args.goal.strip():
        parser.error("--name and --goal must be non-empty")

    root = Path(args.dir)
    if root.exists() and not root.is_dir():
        return usage_error(f"{root} exists and is not a directory")
    existing = [p for p in (*STATE_FILES, "checkpoints") if (root / p).exists()]
    if existing:
        return fail(
            f"{root} already has state file(s): {', '.join(existing)} — "
            "scaffolding is for new runs; refusing to overwrite"
        )

    if args.features:
        seed_path = Path(args.features)
        if not seed_path.is_file():
            return usage_error(f"no such seed file: {seed_path}")
        ok, output = validate_seed(seed_path)
        if not ok:
            sys.stdout.write(output)
            return fail(f"seed {seed_path} fails check_features.py — nothing written")
        features_text = seed_path.read_text(encoding="utf-8")
        print(f"ok: seed {seed_path} passes check_features.py")
    else:
        features_text = json.dumps(PLACEHOLDER_FEATURES, indent=2) + "\n"

    created_root = not root.exists()
    root.mkdir(parents=True, exist_ok=True)
    (root / "checkpoints").mkdir()

    (root / "PROJECT.md").write_text(
        PROJECT_MD.format(name=args.name.strip(), goal=args.goal.strip()),
        encoding="utf-8",
    )
    (root / "features.json").write_text(features_text, encoding="utf-8")
    shutil.copyfile(root / "features.json", root / "checkpoints" / "features.baseline.json")

    today = datetime.date.today().isoformat()
    (root / "progress.md").write_text(
        "# Progress — append only, never rewrite history\n"
        f"{today} orchestrator: state files scaffolded"
        " (scaffold_project.py); baseline snapshot at"
        " checkpoints/features.baseline.json\n",
        encoding="utf-8",
    )

    init_sh = root / "init.sh"
    init_sh.write_text(INIT_SH, encoding="utf-8")
    init_sh.chmod(init_sh.stat().st_mode | 0o111)

    for name in STATE_FILES:
        print(f"ok: wrote {root / name}")
    print(f"ok: wrote {root / 'checkpoints' / 'features.baseline.json'}")

    ok, output = validate_seed(root / "features.json")
    if not ok:
        sys.stdout.write(output)
        _clean_up(root, created_root)
        return fail(
            "written features.json fails check_features.py from the target dir "
            "(relative evidence paths must resolve there) — cleaned up, "
            "nothing left behind"
        )
    print("ok: features.json validates against check_features.py")
    print(f"scaffolded {root} — next: fill PROJECT.md pointers, replace init.sh stub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
