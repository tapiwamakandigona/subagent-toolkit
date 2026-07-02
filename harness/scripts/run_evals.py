#!/usr/bin/env python3
"""Validate and (optionally) run per-skill evals.

Each skill MAY ship an eval set at skills/<name>/evals/evals.json:

    {
      "skill": "<name>",                     # must match the skill directory
      "cases": [
        {
          "id": "<slug>",
          "prompt": "<task prompt exercising the skill>",
          "checks": [
            {"type": "contains" | "regex" | "not_contains", "value": "<string/pattern>"}
          ]
        }
      ]
    }

Usage:
    python3 run_evals.py --validate [ROOT]     # schema-check all eval sets (the CI gate)
    python3 run_evals.py --list [ROOT]         # table of skills and case counts
    python3 run_evals.py --runner 'CMD {{prompt}}' [ROOT]
                                               # OPTIONAL run mode, see below

ROOT defaults to the repo root above this script.

Run mode is harness-dependent and clearly optional: you supply a shell command
template whose stdout is the agent's answer for a prompt (`{{prompt}}` is
replaced with the case prompt, shell-quoted). Checks are applied to that
output and a benchmark.json (pass rate per skill) is written next to this
repo's root (or --output). CI only runs --validate.

Stdlib only. Exit 0 on success; 1 on any validation failure.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CHECK_TYPES = ("contains", "regex", "not_contains")
SLUG_RE = re.compile(r"^[a-z0-9]+([-_][a-z0-9]+)*$")


def find_eval_files(root):
    """Return sorted list of skills/*/evals/evals.json paths under root."""
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(skills_dir.glob("*/evals/evals.json"))


def validate_eval_file(path, root):
    """Validate one evals.json against the contract. Returns list of error strings."""
    rel = path.relative_to(root)
    errors = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{rel}: not valid JSON ({exc})"]

    if not isinstance(data, dict):
        return [f"{rel}: top level must be an object"]

    skill_dirname = path.parent.parent.name
    skill = data.get("skill")
    if not isinstance(skill, str) or not skill:
        errors.append(f"{rel}: missing or non-string 'skill' field")
    elif skill != skill_dirname:
        errors.append(
            f"{rel}: 'skill' is {skill!r} but the skill directory is {skill_dirname!r}"
        )

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{rel}: 'cases' must be a non-empty array")
        return errors

    seen_ids = set()
    for i, case in enumerate(cases):
        where = f"{rel}: cases[{i}]"
        if not isinstance(case, dict):
            errors.append(f"{where}: must be an object")
            continue

        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{where}: missing or non-string 'id'")
        else:
            where = f"{rel}: cases[{i}] ({case_id})"
            if not SLUG_RE.match(case_id):
                errors.append(f"{where}: id is not a slug (lowercase alnum with - or _)")
            if case_id in seen_ids:
                errors.append(f"{where}: duplicate case id")
            seen_ids.add(case_id)

        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{where}: missing or empty 'prompt'")

        checks = case.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append(f"{where}: 'checks' must be a non-empty array")
            continue

        for j, check in enumerate(checks):
            cwhere = f"{where}: checks[{j}]"
            if not isinstance(check, dict):
                errors.append(f"{cwhere}: must be an object")
                continue
            ctype = check.get("type")
            if ctype not in CHECK_TYPES:
                errors.append(
                    f"{cwhere}: type {ctype!r} not one of {'|'.join(CHECK_TYPES)}"
                )
            value = check.get("value")
            if not isinstance(value, str) or not value:
                errors.append(f"{cwhere}: missing or non-string 'value'")
            elif ctype == "regex":
                try:
                    re.compile(value)
                except re.error as exc:
                    errors.append(f"{cwhere}: regex does not compile ({exc})")

    return errors


def cmd_validate(root):
    files = find_eval_files(root)
    if not files:
        print(f"No eval sets found under {root}/skills/*/evals/ (nothing to validate).")
        return 0
    all_errors = []
    for path in files:
        all_errors.extend(validate_eval_file(path, root))
    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        print(f"\n{len(all_errors)} problem(s) in {len(files)} eval file(s).", file=sys.stderr)
        return 1
    total = sum(len(json.loads(p.read_text(encoding="utf-8"))["cases"]) for p in files)
    print(f"OK: {len(files)} eval file(s), {total} case(s), all valid.")
    return 0


def cmd_list(root):
    files = find_eval_files(root)
    if not files:
        print(f"No eval sets found under {root}/skills/*/evals/.")
        return 0
    print(f"{'SKILL':<32} {'CASES':>5}  STATUS")
    for path in files:
        skill = path.parent.parent.name
        errors = validate_eval_file(path, root)
        try:
            n = len(json.loads(path.read_text(encoding="utf-8")).get("cases", []))
        except (json.JSONDecodeError, UnicodeDecodeError):
            n = 0
        status = "ok" if not errors else f"{len(errors)} problem(s)"
        print(f"{skill:<32} {n:>5}  {status}")
    return 0


def apply_check(check, output):
    ctype, value = check["type"], check["value"]
    if ctype == "contains":
        return value in output
    if ctype == "not_contains":
        return value not in output
    if ctype == "regex":
        return re.search(value, output) is not None
    return False


def cmd_run(root, runner, output_path, timeout):
    """Optional run mode: execute each case's prompt through a runner command."""
    files = find_eval_files(root)
    if not files:
        print("No eval sets found; nothing to run.")
        return 0
    if "{{prompt}}" not in runner:
        print("ERROR: --runner template must contain {{prompt}}", file=sys.stderr)
        return 1

    # Refuse to run invalid sets.
    problems = [e for p in files for e in validate_eval_file(p, root)]
    if problems:
        for err in problems:
            print(f"ERROR: {err}", file=sys.stderr)
        print("Fix validation errors before running (see --validate).", file=sys.stderr)
        return 1

    results = {}
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        skill = data["skill"]
        cases = []
        for case in data["cases"]:
            # POSIX shell single-quote the prompt.
            quoted = "'" + case["prompt"].replace("'", "'\\''") + "'"
            cmd = runner.replace("{{prompt}}", quoted)
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=timeout
                )
                out = proc.stdout
                error = None if proc.returncode == 0 else f"runner exit {proc.returncode}"
            except subprocess.TimeoutExpired:
                out, error = "", f"runner timed out after {timeout}s"
            checks = [
                {"type": c["type"], "value": c["value"], "passed": apply_check(c, out)}
                for c in case["checks"]
            ]
            passed = error is None and all(c["passed"] for c in checks)
            cases.append(
                {"id": case["id"], "passed": passed, "error": error, "checks": checks}
            )
            print(f"  [{'PASS' if passed else 'FAIL'}] {skill}/{case['id']}"
                  + (f" ({error})" if error else ""))
        n_pass = sum(1 for c in cases if c["passed"])
        results[skill] = {
            "cases": cases,
            "total": len(cases),
            "passed": n_pass,
            "pass_rate": round(n_pass / len(cases), 3) if cases else 0.0,
        }

    benchmark = {
        "root": str(root),
        "skills": results,
        "overall_pass_rate": round(
            sum(r["passed"] for r in results.values())
            / max(1, sum(r["total"] for r in results.values())),
            3,
        ),
    }
    output_path.write_text(json.dumps(benchmark, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {output_path} (overall pass rate: {benchmark['overall_pass_rate']})")
    return 0 if benchmark["overall_pass_rate"] == 1.0 else 1


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=None,
                        help="toolkit root (default: repo root above this script)")
    parser.add_argument("--validate", action="store_true",
                        help="validate all skills/*/evals/evals.json (CI gate)")
    parser.add_argument("--list", action="store_true", dest="list_",
                        help="list skills with eval case counts")
    parser.add_argument("--runner", metavar="'CMD {{prompt}}'",
                        help="optional: shell command template that prints the "
                             "agent answer for a prompt; enables run mode")
    parser.add_argument("--output", default="benchmark.json",
                        help="run mode: where to write results (default benchmark.json)")
    parser.add_argument("--timeout", type=int, default=600,
                        help="run mode: per-case runner timeout in seconds")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 1

    if args.validate:
        return cmd_validate(root)
    if args.list_:
        return cmd_list(root)
    if args.runner:
        return cmd_run(root, args.runner, Path(args.output), args.timeout)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
