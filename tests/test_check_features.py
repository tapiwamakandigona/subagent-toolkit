"""Tests for check_features.py: shape, evidence-of-done, gate, tamper check."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_FEATURES_PY = REPO_ROOT / "harness" / "scripts" / "check_features.py"


def make_features(tmp_path, entries=None, name="features.json"):
    """Write a features.json plus one real evidence file; return its path."""
    evidence = tmp_path / "proof.log"
    evidence.write_text("1 passed\n", encoding="utf-8")
    if entries is None:
        entries = [
            {
                "id": "signup-dup-409",
                "title": "Duplicate signup rejected",
                "acceptance": "POST /signup with a duplicate email returns 409",
                "passes": True,
                "evidence": "proof.log",
                "milestone": "m1",
            },
            {
                "id": "login-happy",
                "title": "Login works",
                "acceptance": "POST /login with valid creds returns 200 + token",
                "passes": False,
                "milestone": "m2",
            },
        ]
    path = tmp_path / name
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CHECK_FEATURES_PY), *args],
        capture_output=True, text=True,
    )


def test_valid_file_passes(tmp_path):
    r = run_cli(str(make_features(tmp_path)))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "FAIL" not in r.stdout
    assert "ok: signup-dup-409: evidence path exists: proof.log" in r.stdout


def test_missing_file_is_usage_error(tmp_path):
    r = run_cli(str(tmp_path / "nope.json"))
    assert r.returncode == 2


def test_top_level_object_fails(tmp_path):
    path = tmp_path / "features.json"
    path.write_text(json.dumps({"features": []}), encoding="utf-8")
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "top level must be an array" in r.stdout


def test_missing_required_field_fails(tmp_path):
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    del entries[0]["acceptance"]
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "FAIL: signup-dup-409: required field 'acceptance' present" in r.stdout


def test_duplicate_id_fails(tmp_path):
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    entries[1]["id"] = entries[0]["id"]
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "FAIL: signup-dup-409: id is unique" in r.stdout


def test_pass_without_evidence_fails(tmp_path):
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    del entries[0]["evidence"]
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "FAIL: signup-dup-409: passes:true has evidence attached" in r.stdout


def test_pass_with_missing_evidence_path_fails(tmp_path):
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    entries[0]["evidence"] = "gone.log"
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "FAIL: signup-dup-409: evidence path exists: gone.log" in r.stdout


def test_evidence_list_and_empty_evidence_file(tmp_path):
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    entries[0]["evidence"] = ["proof.log", "empty.log"]
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "ok: signup-dup-409: evidence path is non-empty: proof.log" in r.stdout
    assert "FAIL: signup-dup-409: evidence path is non-empty: empty.log" in r.stdout


def test_empty_string_evidence_fails_shape(tmp_path):
    """evidence: '' (or [''] ) is malformed, matching the schema."""
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    entries[1]["evidence"] = ""
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "evidence is a non-empty string or list of them" in r.stdout
    # whitespace-only paths are equally malformed
    entries[1]["evidence"] = [" "]
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "evidence is a non-empty string or list of them" in r.stdout


def test_special_file_evidence_fails_cleanly(tmp_path):
    """A /dev/null-style evidence path must FAIL, not traceback."""
    path = make_features(tmp_path)
    entries = json.loads(path.read_text())
    entries[0]["evidence"] = "/dev/null"
    path.write_text(json.dumps(entries))
    r = run_cli(str(path))
    assert r.returncode == 1
    assert "Traceback" not in r.stderr
    assert (
        "FAIL: signup-dup-409: evidence path is a regular file or directory: "
        "/dev/null" in r.stdout
    )
    assert "feature check(s) failed" in r.stderr


def test_gate_fails_on_unpassed_feature(tmp_path):
    r = run_cli(str(make_features(tmp_path)), "--gate")
    assert r.returncode == 1
    assert "FAIL: gate: login-happy passes" in r.stdout


def test_gate_scoped_to_milestone_passes(tmp_path):
    r = run_cli(str(make_features(tmp_path)), "--gate", "--milestone", "m1")
    assert r.returncode == 0, r.stdout + r.stderr


def test_gate_unknown_milestone_fails(tmp_path):
    r = run_cli(str(make_features(tmp_path)), "--gate", "--milestone", "m9")
    assert r.returncode == 1
    assert "FAIL: gate: milestone 'm9' has at least one feature" in r.stdout


def test_milestone_without_gate_is_usage_error(tmp_path):
    r = run_cli(str(make_features(tmp_path)), "--milestone", "m1")
    assert r.returncode == 2
    # empty string must not slip past the guard
    r = run_cli(str(make_features(tmp_path)), "--milestone", "")
    assert r.returncode == 2


def test_against_detects_acceptance_edit(tmp_path):
    baseline = make_features(tmp_path, name="baseline.json")
    entries = json.loads(baseline.read_text())
    entries[1]["acceptance"] = "POST /login always returns 200"
    entries[1]["passes"] = True
    entries[1]["evidence"] = "proof.log"
    current = make_features(tmp_path, entries=entries, name="features.json")
    r = run_cli(str(current), "--against", str(baseline))
    assert r.returncode == 1
    assert "FAIL: baseline: login-happy field 'acceptance' unchanged" in r.stdout


def test_against_detects_removed_and_added(tmp_path):
    baseline = make_features(tmp_path, name="baseline.json")
    entries = json.loads(baseline.read_text())
    del entries[1]
    entries.append(
        {
            "id": "bonus-feature",
            "title": "Sneaky addition",
            "acceptance": "true",
            "passes": True,
            "evidence": "proof.log",
        }
    )
    current = make_features(tmp_path, entries=entries, name="features.json")
    r = run_cli(str(current), "--against", str(baseline))
    assert r.returncode == 1
    assert "FAIL: baseline: login-happy still present" in r.stdout
    assert "FAIL: baseline: bonus-feature existed in baseline" in r.stdout


def test_against_allows_flipping_passes(tmp_path):
    baseline = make_features(tmp_path, name="baseline.json")
    entries = json.loads(baseline.read_text())
    entries[1]["passes"] = True
    entries[1]["evidence"] = "proof.log"
    current = make_features(tmp_path, entries=entries, name="features.json")
    r = run_cli(str(current), "--against", str(baseline))
    assert r.returncode == 0, r.stdout + r.stderr
