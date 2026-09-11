#!/usr/bin/env python3
"""Fail-closed feature/evidence gate and run-local check-integrity guard.

Standard library only. Does not execute feature commands. The reviewed verify.sh
is the authoritative executable gate; evidence values are project-relative files.
This detects accidental check/spec changes, not a hostile same-user process.
"""

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path, PurePosixPath


FROZEN = ("id", "title", "acceptance", "verify")
CHECK_FILES = ("loop.sh", "verify.sh", "check_features.py")
CHECK_DIRS = ("tests", ".github/workflows")
EXCLUDE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}


class Invalid(Exception):
    pass


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Invalid("Required JSON file is missing or invalid.") from None


def regular(root, relative):
    parts = PurePosixPath(relative)
    if (
        not relative or relative != parts.as_posix() or parts.is_absolute()
        or "\\" in relative or any(part in {"", ".", "..", ".git"} for part in parts.parts)
        or any(ord(char) < 32 for char in relative)
    ):
        raise Invalid("A required file has an unsafe relative path.")
    path = root.joinpath(*parts.parts)
    for parent in [path, *path.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise Invalid("Symlinks are not allowed for checks or evidence.")
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise Invalid("A required file is missing or outside the project.")
    return path


def features(root):
    data = load_json(regular(root, "features.json"))
    rows = data.get("features") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise Invalid("features.json must contain a nonempty feature list.")
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise Invalid("Every feature must be an object.")
        for field in FROZEN:
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or "{{" in value or "}}" in value:
                raise Invalid("Feature definitions must be nonempty and contain no placeholders.")
        if row["id"] in ids:
            raise Invalid("Feature IDs must be unique.")
        ids.add(row["id"])
        if type(row.get("passes")) is not bool:
            raise Invalid("Feature passes must be a JSON boolean.")
        if not isinstance(row.get("evidence"), str):
            raise Invalid("Feature evidence must be a relative file path string.")
    return rows


def frozen_features(rows):
    return {row["id"]: {field: row[field] for field in FROZEN} for row in rows}


def check_files(root):
    paths = set(CHECK_FILES)
    for directory in CHECK_DIRS:
        location = root / directory
        if location.is_symlink():
            raise Invalid("Check directories must not be symlinks.")
        if location.exists():
            for parent, directories, filenames in os.walk(location, followlinks=False):
                directories[:] = sorted(d for d in directories if d not in EXCLUDE_DIRS)
                for dirname in directories:
                    if (Path(parent) / dirname).is_symlink():
                        raise Invalid("Check directories must not contain symlinks.")
                for filename in filenames:
                    if filename.endswith((".pyc", ".pyo")):
                        continue
                    paths.add(str((Path(parent) / filename).relative_to(root)))
    result = {}
    for rel in sorted(paths):
        path = regular(root, rel)
        result[rel] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mode": stat.S_IMODE(path.stat().st_mode),
        }
    return result


def snapshot(root):
    return {"features": frozen_features(features(root)), "checks": check_files(root)}


def integrity(root, baseline):
    current = snapshot(root)
    if current != load_json(baseline):
        raise Invalid("Frozen feature criteria or check files changed during this run.")


def complete(root):
    rows = features(root)
    if any(not row["passes"] for row in rows):
        raise Invalid("Features remain incomplete.")
    for row in rows:
        artifact = regular(root, row["evidence"])
        if artifact.stat().st_size == 0:
            raise Invalid("Completed features require nonempty evidence files.")


def fingerprint(root):
    """Content/mode delta, not commit-count or log-timestamp delta."""
    digest = hashlib.sha256()
    for parent, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            d for d in directories if d not in EXCLUDE_DIRS and not (Path(parent) / d).is_symlink()
        )
        for name in sorted(filenames):
            path = Path(parent) / name
            rel = str(path.relative_to(root))
            if rel == "progress.md" or name.endswith((".log", ".pyc")):
                continue
            if path.is_symlink():
                value = b"symlink:" + os.readlink(path).encode()
                mode = 0
            elif path.is_file():
                value = path.read_bytes()
                mode = stat.S_IMODE(path.stat().st_mode)
            else:
                continue
            digest.update(rel.encode() + b"\0" + str(mode).encode() + b"\0")
            digest.update(hashlib.sha256(value).digest())
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("snapshot", "integrity", "complete", "fingerprint"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "snapshot":
            if args.output is None:
                raise Invalid("snapshot requires --output.")
            if args.output.resolve().is_relative_to(root):
                raise Invalid("Integrity baseline must be outside the working project.")
            data = json.dumps(snapshot(root), sort_keys=True, indent=2)
            fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as handle:
                handle.write(data + "\n")
        elif args.command == "fingerprint":
            print(fingerprint(root))
        else:
            if args.baseline:
                integrity(root, args.baseline)
            elif args.command == "integrity":
                raise Invalid("integrity requires --baseline.")
            if args.command == "complete":
                complete(root)
        return 0
    except (Invalid, OSError, ValueError) as error:
        # No feature values, file contents, credentials, or external paths.
        message = str(error) if isinstance(error, Invalid) else "Required file operation failed."
        print("CHECK FAILED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
