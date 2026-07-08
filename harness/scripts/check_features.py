#!/usr/bin/env python3
"""Validate a features.json project-state file and run the milestone gate.

features.json (see harness/context-management.md §6) is the machine-readable
definition of done for a project: an array of
{id, title, acceptance, passes, evidence[, milestone]}. The orchestrator
creates it; workers may only flip `passes` and fill `evidence`. This script
makes the two enforcement points from the docs runnable:

  shape + evidence  every entry matches harness/schemas/features.schema.json
                    (hand-rolled, no jsonschema dependency), and every
                    feature claiming `passes: true` carries evidence path(s)
                    that exist on disk and are non-empty. A pass without
                    proof is a claim, not a result.

  --gate            the milestone gate from harness/project-lifecycle.md §2:
                    additionally FAIL if any in-scope feature has
                    `passes: false`. Scope with --milestone to gate one
                    milestone at a time; without it, the whole file gates
                    (the release check).

  --against BASE    the tamper check from context-management.md §6: compare
                    against the orchestrator's baseline copy and FAIL if any
                    feature was removed or added, or if `id`, `title`, or
                    `acceptance` changed. Workers flipping their own success
                    criteria is a known failure mode; QA runs this before
                    trusting any flipped `passes`.

Usage:
    python3 check_features.py <features.json> [--base DIR] [--gate]
                              [--milestone M] [--against BASELINE]

    --base DIR   directory against which relative evidence paths are
                 resolved (default: the features.json's own directory)

Prints one line per check ("ok: ..." / "FAIL: ..."). Exit code 0 when all
checks pass, 1 when any fail, 2 on usage error. Stdlib only.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9]+([-_.][a-z0-9]+)*$")
REQUIRED_FIELDS = ("id", "title", "acceptance", "passes")
FROZEN_FIELDS = ("id", "title", "acceptance")


class Checker:
    def __init__(self):
        self.failures = 0

    def check(self, ok, label):
        if ok:
            print(f"ok: {label}")
        else:
            print(f"FAIL: {label}")
            self.failures += 1
        return ok


def load_features(path):
    """Load a features.json file. Returns (data, error_string)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path} is not readable JSON ({exc})"
    if not isinstance(data, list):
        return None, f"{path} top level must be an array of feature objects"
    return data, None


def evidence_paths(entry):
    """Normalize the evidence field to a list of strings."""
    evidence = entry.get("evidence")
    if evidence is None:
        return []
    if isinstance(evidence, str):
        return [evidence] if evidence else []
    if isinstance(evidence, list):
        return [item for item in evidence if isinstance(item, str) and item]
    return []


def check_shape(features, c):
    """Validate every entry against the pinned shape."""
    seen = set()
    for i, entry in enumerate(features):
        label = entry.get("id") if isinstance(entry, dict) else None
        name = label if isinstance(label, str) and label else f"entry #{i}"
        if not c.check(isinstance(entry, dict), f"{name}: is an object"):
            continue
        for field in REQUIRED_FIELDS:
            c.check(field in entry, f"{name}: required field '{field}' present")
        for field in ("id", "title", "acceptance"):
            if field in entry:
                ok = isinstance(entry[field], str) and entry[field].strip()
                c.check(ok, f"{name}: field '{field}' is a non-empty string")
        if isinstance(entry.get("id"), str) and entry["id"]:
            c.check(
                bool(ID_RE.match(entry["id"])),
                f"{name}: id is a lowercase slug",
            )
            if c.check(entry["id"] not in seen, f"{name}: id is unique"):
                seen.add(entry["id"])
        if "passes" in entry:
            c.check(
                isinstance(entry["passes"], bool),
                f"{name}: field 'passes' is a boolean",
            )
        if "evidence" in entry and entry["evidence"] is not None:
            ok = isinstance(entry["evidence"], str) or (
                isinstance(entry["evidence"], list)
                and all(isinstance(item, str) for item in entry["evidence"])
            )
            c.check(ok, f"{name}: evidence is a string or list of strings")
        if "milestone" in entry and entry["milestone"] is not None:
            c.check(
                isinstance(entry["milestone"], str),
                f"{name}: field 'milestone' is a string",
            )


def check_evidence(features, base, c):
    """Every passes:true feature needs evidence that exists and is non-empty."""
    for i, entry in enumerate(features):
        if not isinstance(entry, dict) or entry.get("passes") is not True:
            continue
        name = entry.get("id") or f"entry #{i}"
        paths = evidence_paths(entry)
        if not c.check(bool(paths), f"{name}: passes:true has evidence attached"):
            continue
        for raw in paths:
            path = Path(raw)
            if not path.is_absolute():
                path = base / path
            if not c.check(path.exists(), f"{name}: evidence path exists: {raw}"):
                continue
            if not c.check(
                path.is_file() or path.is_dir(),
                f"{name}: evidence path is a regular file or directory: {raw}",
            ):
                continue
            if path.is_file():
                ok = path.stat().st_size > 0
            else:
                ok = any(path.iterdir())
            c.check(ok, f"{name}: evidence path is non-empty: {raw}")


def check_gate(features, milestone, c):
    """The milestone gate: every in-scope feature passes."""
    scope = [
        e
        for e in features
        if isinstance(e, dict)
        and (milestone is None or e.get("milestone") == milestone)
    ]
    where = f"milestone '{milestone}'" if milestone else "the project"
    if not c.check(bool(scope), f"gate: {where} has at least one feature"):
        return
    for entry in scope:
        name = entry.get("id") or "entry"
        c.check(entry.get("passes") is True, f"gate: {name} passes")


def check_against(features, baseline, c):
    """Tamper check: id/title/acceptance frozen; no additions or removals."""
    current = {
        e["id"]: e
        for e in features
        if isinstance(e, dict) and isinstance(e.get("id"), str)
    }
    base = {
        e["id"]: e
        for e in baseline
        if isinstance(e, dict) and isinstance(e.get("id"), str)
    }
    for fid, base_entry in base.items():
        if not c.check(fid in current, f"baseline: {fid} still present"):
            continue
        for field in FROZEN_FIELDS:
            c.check(
                current[fid].get(field) == base_entry.get(field),
                f"baseline: {fid} field '{field}' unchanged",
            )
    for fid in current:
        c.check(fid in base, f"baseline: {fid} existed in baseline")


def main(argv):
    parser = argparse.ArgumentParser(
        prog="check_features.py",
        description="Validate features.json and run the milestone gate.",
    )
    parser.add_argument("features", help="path to the features.json file")
    parser.add_argument(
        "--base",
        help="base directory for relative evidence paths "
        "(default: the features.json's directory)",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="also FAIL if any in-scope feature has passes:false",
    )
    parser.add_argument(
        "--milestone",
        help="limit --gate to features tagged with this milestone",
    )
    parser.add_argument(
        "--against",
        help="orchestrator baseline features.json to diff frozen fields against",
    )
    args = parser.parse_args(argv[1:])

    if args.milestone is not None and not args.gate:
        print("error: --milestone requires --gate", file=sys.stderr)
        return 2
    features_path = Path(args.features)
    if not features_path.is_file():
        print(f"error: no such file: {features_path}", file=sys.stderr)
        return 2
    base = Path(args.base) if args.base else features_path.resolve().parent
    if not base.is_dir():
        print(f"error: --base is not a directory: {base}", file=sys.stderr)
        return 2

    features, err = load_features(features_path)
    if err:
        print(f"FAIL: {err}")
        print("\n1 feature check(s) failed", file=sys.stderr)
        return 1

    c = Checker()
    c.check(bool(features), "feature list is non-empty")
    check_shape(features, c)
    check_evidence(features, base, c)
    if args.gate:
        check_gate(features, args.milestone, c)
    if args.against:
        baseline_path = Path(args.against)
        if not baseline_path.is_file():
            print(f"error: no such file: {baseline_path}", file=sys.stderr)
            return 2
        baseline, err = load_features(baseline_path)
        if err:
            print(f"FAIL: {err}")
            c.failures += 1
        else:
            check_against(features, baseline, c)

    if c.failures:
        print(f"\n{c.failures} feature check(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
