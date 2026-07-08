"""Tests for check_contract.py's sidecar validation and artifact checks."""

import json
import subprocess
import sys
from pathlib import Path

import check_contract

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_CONTRACT_PY = REPO_ROOT / "harness" / "scripts" / "check_contract.py"


def make_sidecar(tmp_path, overrides=None, artifacts=None, name="report.json"):
    """Write a valid sidecar plus one real artifact file; return its path."""
    artifact = tmp_path / "out.md"
    artifact.write_text("content\n", encoding="utf-8")
    report = {
        "run_id": "run-1",
        "agent": "code-worker",
        "status": "complete",
        "artifacts": artifacts if artifacts is not None else ["out.md"],
        "verified": ["tests pass"],
        "assumed": [],
        "implicit_decisions": ["used tabs"],
        "evidence": [],
        "notes": "",
    }
    report.update(overrides or {})
    path = tmp_path / name
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CHECK_CONTRACT_PY), *args],
        capture_output=True, text=True,
    )


def test_valid_sidecar_passes(tmp_path):
    r = run_cli(str(make_sidecar(tmp_path)))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "FAIL" not in r.stdout
    assert "ok: artifacts path exists: out.md" in r.stdout


def test_missing_required_field_fails(tmp_path):
    path = make_sidecar(tmp_path)
    report = json.loads(path.read_text())
    del report["run_id"]
    path.write_text(json.dumps(report))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "FAIL: required field 'run_id' present" in r.stdout


def test_bad_status_enum_fails(tmp_path):
    r = run_cli(str(make_sidecar(tmp_path, {"status": "done"})))
    assert r.returncode == 1
    assert "FAIL: status 'done'" in r.stdout


def test_missing_artifact_fails(tmp_path):
    r = run_cli(str(make_sidecar(tmp_path, artifacts=["nope.md"])))
    assert r.returncode == 1
    assert "FAIL: artifacts path exists: nope.md" in r.stdout


def test_empty_artifact_fails(tmp_path):
    (tmp_path / "empty.md").write_text("", encoding="utf-8")
    r = run_cli(str(make_sidecar(tmp_path, artifacts=["empty.md"])))
    assert r.returncode == 1
    assert "FAIL: artifacts path is non-empty: empty.md" in r.stdout


def test_base_flag_resolves_relative_paths(tmp_path):
    base = tmp_path / "elsewhere"
    base.mkdir()
    (base / "artifact.txt").write_text("x\n", encoding="utf-8")
    path = make_sidecar(tmp_path, artifacts=["artifact.txt"])
    assert run_cli(str(path)).returncode == 1        # not next to the report
    assert run_cli(str(path), "--base", str(base)).returncode == 0


def test_wrong_types_fail(tmp_path):
    r = run_cli(str(make_sidecar(tmp_path, {"artifacts": "out.md",
                                            "run_id": 7})))
    assert r.returncode == 1
    assert "FAIL: field 'artifacts' is a list of strings" in r.stdout
    assert "FAIL: field 'run_id' is a string" in r.stdout


def test_optional_fields_may_be_absent(tmp_path):
    path = make_sidecar(tmp_path)
    report = json.loads(path.read_text())
    for key in ("verified", "assumed", "implicit_decisions", "evidence",
                "notes"):
        del report[key]
    path.write_text(json.dumps(report))
    assert run_cli(str(path)).returncode == 0


def test_evidence_paths_checked(tmp_path):
    r = run_cli(str(make_sidecar(tmp_path, {"evidence": ["proof.log"]})))
    assert r.returncode == 1
    assert "FAIL: evidence path exists: proof.log" in r.stdout


def test_non_json_and_non_object_fail(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert run_cli(str(bad)).returncode == 1
    arr = tmp_path / "arr.json"
    arr.write_text("[1, 2]", encoding="utf-8")
    r = run_cli(str(arr))
    assert r.returncode == 1
    assert "FAIL: sidecar is a JSON object" in r.stdout


def test_missing_file_is_usage_error(tmp_path):
    assert run_cli(str(tmp_path / "absent.json")).returncode == 2


def test_main_importable(tmp_path):
    path = make_sidecar(tmp_path)
    assert check_contract.main(["check_contract.py", str(path)]) == 0


def test_example_matches_pinned_schema_shape():
    """The schema file itself must parse and pin the agreed field set."""
    schema = json.loads(
        (REPO_ROOT / "harness" / "schemas" / "handoff.schema.json")
        .read_text(encoding="utf-8")
    )
    assert schema["required"] == ["run_id", "agent", "status", "artifacts"]
    assert set(schema["properties"]) == {
        "run_id", "agent", "status", "artifacts", "verified", "assumed",
        "implicit_decisions", "evidence", "notes",
    }
    assert schema["properties"]["status"]["enum"] == [
        "complete", "partial", "blocked", "failed",
    ]


def test_base_flag_resolves_relative_evidence(tmp_path):
    base = tmp_path / "elsewhere"
    base.mkdir()
    (base / "proof.log").write_text("evidence\n", encoding="utf-8")
    (base / "artifact.txt").write_text("x\n", encoding="utf-8")
    path = make_sidecar(
        tmp_path, {"evidence": ["proof.log"]}, artifacts=["artifact.txt"]
    )
    assert run_cli(str(path)).returncode == 1  # not next to the report
    assert run_cli(str(path), "--base", str(base)).returncode == 0


def test_base_not_a_directory_is_usage_error(tmp_path):
    path = make_sidecar(tmp_path)
    r = run_cli(str(path), "--base", str(tmp_path / "absent"))
    assert r.returncode == 2
    assert "--base is not a directory" in r.stderr


def test_help_states_resolution_rule():
    r = run_cli("--help")
    assert r.returncode == 0
    text = r.stdout.replace("\n", " ")
    assert "--base" in text
    assert "report" in text and "director" in text  # rule is stated


def test_docstring_states_resolution_rule():
    assert "own directory" in check_contract.__doc__
