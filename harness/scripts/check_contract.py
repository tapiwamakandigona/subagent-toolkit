#!/usr/bin/env python3
"""Validate a handoff sidecar (report.json) against the handoff contract.

Subagents write a report.json next to their handoff report (see
prompts/handoff-report.md); orchestrators run this script on each one before
accepting the work. It checks the sidecar against the shape pinned in
harness/schemas/handoff.schema.json — hand-rolled, no jsonschema dependency —
and then checks the evidence-of-done rule: every claimed artifact path must
exist on disk and be non-empty. A report over missing artifacts is a claim,
not a result.

Path resolution rule: relative paths in `artifacts` and `evidence` resolve
against the report.json's OWN directory — not the current working directory.
Write sidecar paths relative to the sidecar, or use absolute paths. Pass
--base DIR to resolve them against a different directory instead.

Usage:
    python3 check_contract.py <report.json> [--base DIR]

    --base DIR   directory against which relative artifact/evidence paths
                 are resolved (default: the report.json's own directory)

Prints one line per check ("ok: ..." / "FAIL: ..."). Exit code 0 when all
checks pass, 1 when any fail, 2 on usage error. Stdlib only.
"""

import argparse
import json
import sys
from pathlib import Path

STATUS_VALUES = ("complete", "partial", "blocked", "failed")
REQUIRED_FIELDS = ("run_id", "agent", "status", "artifacts")
STRING_FIELDS = ("run_id", "agent", "status", "notes")
LIST_FIELDS = ("artifacts", "verified", "assumed", "implicit_decisions", "evidence")


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


def check_fields(report, c):
    for field in REQUIRED_FIELDS:
        c.check(field in report, f"required field '{field}' present")
    for field in STRING_FIELDS:
        if field in report:
            c.check(
                isinstance(report[field], str),
                f"field '{field}' is a string",
            )
    for field in LIST_FIELDS:
        if field in report:
            ok = isinstance(report[field], list) and all(
                isinstance(item, str) for item in report[field]
            )
            c.check(ok, f"field '{field}' is a list of strings")
    status = report.get("status")
    if isinstance(status, str):
        c.check(
            status in STATUS_VALUES,
            f"status '{status}' is one of {'|'.join(STATUS_VALUES)}",
        )


def check_paths(report, base, c):
    for field in ("artifacts", "evidence"):
        values = report.get(field)
        if not isinstance(values, list):
            continue
        for raw in values:
            if not isinstance(raw, str):
                continue
            path = Path(raw)
            if not path.is_absolute():
                path = base / path
            if not c.check(path.exists(), f"{field} path exists: {raw}"):
                continue
            if path.is_file():
                c.check(
                    path.stat().st_size > 0,
                    f"{field} path is non-empty: {raw}",
                )
            elif path.is_dir():
                c.check(
                    any(path.iterdir()),
                    f"{field} path is non-empty: {raw}",
                )


def main(argv):
    parser = argparse.ArgumentParser(
        prog="check_contract.py",
        description="Validate a handoff report.json sidecar. Relative "
        "artifacts/evidence paths resolve against the report.json's own "
        "directory (not the CWD) unless --base is given.",
    )
    parser.add_argument("report", help="path to the report.json sidecar")
    parser.add_argument(
        "--base",
        help="base directory for relative artifact/evidence paths "
        "(default: the report's directory)",
    )
    args = parser.parse_args(argv[1:])

    report_path = Path(args.report)
    if not report_path.is_file():
        print(f"error: no such file: {report_path}", file=sys.stderr)
        return 2
    base = Path(args.base) if args.base else report_path.resolve().parent
    if not base.is_dir():
        print(f"error: --base is not a directory: {base}", file=sys.stderr)
        return 2

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: {report_path} is not readable JSON ({e})")
        return 1
    c = Checker()
    if not c.check(isinstance(report, dict), "sidecar is a JSON object"):
        print(f"\n{c.failures} contract check(s) failed", file=sys.stderr)
        return 1

    check_fields(report, c)
    check_paths(report, base, c)

    if c.failures:
        print(f"\n{c.failures} contract check(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
