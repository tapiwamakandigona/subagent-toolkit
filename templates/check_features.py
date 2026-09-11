#!/usr/bin/env python3
"""Fail-closed feature/evidence gate, check-integrity guard, and run-ledger tools.

Standard library only. Does not execute feature commands. The reviewed verify.sh
is the authoritative executable gate; evidence values are project-relative files.
Subcommands:
  snapshot     freeze feature criteria + check files to a baseline outside the project
  integrity    fail if the frozen baseline no longer matches the project
  complete     fail unless every feature passes with nonempty evidence
               (--run-id: evidence must also contain the current run id)
  fingerprint  content/mode digest of the project (progress/report/ledger excluded)
  report       validate the agent's structured iteration report (report.json)
  evaluation   validate an evaluator verdict file (evaluation.json)
  hooks        print trusted hook paths (hooks.lock sha256 must match the file)
  event        append a hash-chained JSON event to a run ledger
  chain        verify a run ledger's hash chain
This detects accidental check/spec changes, not a hostile same-user process.
"""

import argparse
import hashlib
import json
import os
import stat
import sys
import time
from pathlib import Path, PurePosixPath


FROZEN = ("id", "title", "acceptance", "verify")
CHECK_FILES = ("loop.sh", "verify.sh", "check_features.py", "sandbox.sh", "init.sh", "hooks.lock", "policy.json")
CHECK_DIRS = ("tests", "hooks", ".github/workflows")
EXCLUDE_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".harness"}
TRANSIENT_FILES = {"progress.md", "report.json", "evaluation.json", "STEER.md", "APPROVAL_REQUESTED.md"}
LABELS = {"VERIFIED", "ASSUMED"}
REPORT_STATUS = {"progress", "blocked", "complete"}
VERDICTS = {"PASS", "NEEDS_WORK"}
MAX_TEXT = 2000
MAX_ITEMS = 50


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
    paths = set()
    for name in CHECK_FILES:
        if (root / name).is_symlink() or (root / name).is_file():
            paths.add(name)
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
    for name in ("loop.sh", "verify.sh", "check_features.py"):
        if name not in paths:
            raise Invalid("A required check file is missing.")
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


def complete(root, run_id=None):
    rows = features(root)
    if any(not row["passes"] for row in rows):
        raise Invalid("Features remain incomplete.")
    for row in rows:
        artifact = regular(root, row["evidence"])
        data = artifact.read_bytes()
        if not data:
            raise Invalid("Completed features require nonempty evidence files.")
        if run_id and run_id.encode() not in data:
            raise Invalid("Evidence is not bound to this run; the reviewed checks must regenerate it.")


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
            if rel in TRANSIENT_FILES or name.endswith((".log", ".pyc")):
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


def text(value, what, allow_empty=False):
    if not isinstance(value, str) or len(value) > MAX_TEXT or (not allow_empty and not value.strip()):
        raise Invalid(what + " must be a nonempty string of at most 2000 characters.")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise Invalid(what + " contains control characters.")
    return value


def string_list(value, what):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise Invalid(what + " must be a list of at most 50 items.")
    return [text(item, what + " item") for item in value]


def report(root, path):
    """Structured iteration report: every claim carries an explicit evidence label."""
    data = load_json(regular(root, path))
    if not isinstance(data, dict) or set(data) - {"task", "status", "claims", "approval_requests", "next"}:
        raise Invalid("report.json must be an object with only the documented fields.")
    text(data.get("task"), "report task")
    if data.get("status") not in REPORT_STATUS:
        raise Invalid("report status must be progress, blocked, or complete.")
    claims = data.get("claims")
    if not isinstance(claims, list) or not claims or len(claims) > MAX_ITEMS:
        raise Invalid("report claims must be a nonempty list of at most 50 items.")
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) - {"text", "label", "evidence"}:
            raise Invalid("Each claim must have text, label, and evidence only.")
        text(claim.get("text"), "claim text")
        if claim.get("label") not in LABELS:
            raise Invalid("Each claim must be labeled VERIFIED or ASSUMED.")
        evidence = claim.get("evidence")
        if claim["label"] == "VERIFIED":
            if not isinstance(evidence, str) or not evidence.strip():
                raise Invalid("VERIFIED claims require an evidence reference.")
            regular(root, evidence)
        elif evidence not in (None, ""):
            raise Invalid("ASSUMED claims carry no evidence reference.")
    requests = string_list(data.get("approval_requests", []), "approval_requests")
    text(data.get("next", "none"), "report next")
    return {"status": data["status"], "approval_requests": requests}


def evaluation(root, path):
    data = load_json(regular(root, path))
    if not isinstance(data, dict) or set(data) - {"verdict", "findings"}:
        raise Invalid("evaluation.json must contain only verdict and findings.")
    if data.get("verdict") not in VERDICTS:
        raise Invalid("Evaluator verdict must be PASS or NEEDS_WORK.")
    findings = string_list(data.get("findings", []), "findings")
    if data["verdict"] == "NEEDS_WORK" and not findings:
        raise Invalid("NEEDS_WORK requires at least one finding.")
    return {"verdict": data["verdict"], "findings": findings}


def trusted_hooks(root):
    """Codex-style trust-by-hash: a hook runs only if hooks.lock pins its exact content."""
    lock = root / "hooks.lock"
    if not lock.is_file():
        return []
    trusted = []
    for line in lock.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise Invalid("hooks.lock lines must be '<sha256> <relative path>'.")
        digest, rel = parts
        if not rel.startswith("hooks/"):
            raise Invalid("Only files under hooks/ may be trusted hooks.")
        path = regular(root, rel)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest.lower():
            raise Invalid("A hook changed since it was trusted; re-review and update hooks.lock.")
        if not os.access(path, os.X_OK):
            raise Invalid("Trusted hooks must be executable.")
        trusted.append(rel)
    return trusted


def write_lines(root, relative, header, lines):
    target = root / relative
    if "/" in relative or relative.startswith(".") or target.is_symlink():
        raise Invalid("Approval file must be a plain top-level project file.")
    target.write_text(header + "".join("- " + line.replace("\n", " ") + "\n" for line in lines), encoding="utf-8")


def last_event(log):
    prev = "0" * 64
    seq = 0
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                prev = row["hash"]
                seq = row["seq"]
    return prev, seq


def event_hash(row):
    body = {key: row[key] for key in ("seq", "ts", "type", "data", "prev")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def append_event(log, kind, fields):
    data = {}
    for item in fields:
        key, sep, value = item.partition("=")
        if not sep or not key or not key.replace("_", "").isalnum():
            raise Invalid("event fields must be key=value.")
        data[key] = text(value, "event field", allow_empty=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    prev, seq = last_event(log)
    row = {"seq": seq + 1, "ts": int(time.time()), "type": text(kind, "event type"), "data": data, "prev": prev}
    row["hash"] = event_hash(row)
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def verify_chain(log):
    prev = "0" * 64
    seq = 0
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
    except OSError:
        raise Invalid("Run ledger is missing.") from None
    for line in lines:
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("prev") != prev or row.get("seq") != seq + 1 or event_hash(row) != row.get("hash"):
            raise Invalid("Run ledger hash chain is broken at event %d." % (seq + 1))
        prev, seq = row["hash"], row["seq"]
    if seq == 0:
        raise Invalid("Run ledger is empty.")
    return seq


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=(
        "snapshot", "integrity", "complete", "fingerprint", "report", "evaluation", "hooks", "event", "chain"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--path", default=None)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--type", dest="kind")
    parser.add_argument("--approval-file", default=None)
    parser.add_argument("--findings-file", default=None)
    parser.add_argument("fields", nargs="*", help="key=value pairs for event")
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
        elif args.command == "report":
            result = report(root, args.path or "report.json")
            if result["approval_requests"] and args.approval_file:
                write_lines(root, args.approval_file, "# Approval requested by the agent\n",
                            result["approval_requests"])
            print("status=" + result["status"])
            print("approvals=%d" % len(result["approval_requests"]))
        elif args.command == "evaluation":
            result = evaluation(root, args.path or "evaluation.json")
            if args.findings_file:
                Path(args.findings_file).write_text(
                    "".join("- " + line.replace("\n", " ") + "\n" for line in result["findings"]),
                    encoding="utf-8")
            print("verdict=" + result["verdict"])
            print("findings=%d" % len(result["findings"]))
        elif args.command == "hooks":
            for rel in trusted_hooks(root):
                print(rel)
        elif args.command == "event":
            if args.log is None or not args.kind:
                raise Invalid("event requires --log and --type.")
            append_event(args.log, args.kind, args.fields)
        elif args.command == "chain":
            if args.log is None:
                raise Invalid("chain requires --log.")
            print(verify_chain(args.log))
        else:
            if args.baseline:
                integrity(root, args.baseline)
            elif args.command == "integrity":
                raise Invalid("integrity requires --baseline.")
            if args.command == "complete":
                complete(root, args.run_id)
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError) as error:
        # No feature values, file contents, credentials, or external paths.
        message = str(error) if isinstance(error, Invalid) else "Required file operation failed."
        print("CHECK FAILED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
