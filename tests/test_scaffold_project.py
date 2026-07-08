"""Tests for scaffold_project.py: state-file creation, seeding, refusal."""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAFFOLD_PY = REPO_ROOT / "harness" / "scripts" / "scaffold_project.py"
CHECK_FEATURES_PY = REPO_ROOT / "harness" / "scripts" / "check_features.py"

STATE_FILES = ("PROJECT.md", "features.json", "progress.md", "init.sh")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCAFFOLD_PY), *map(str, args)],
        capture_output=True,
        text=True,
    )


def scaffold(tmp_path, *extra):
    target = tmp_path / "state"
    result = run_cli(target, "--name", "Demo", "--goal", "A demo project.", *extra)
    return target, result


def test_creates_all_state_files(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    for name in STATE_FILES:
        assert (target / name).is_file(), name
    assert (target / "checkpoints").is_dir()
    assert (target / "checkpoints" / "features.baseline.json").is_file()


def test_project_md_contains_name_and_goal(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0
    text = (target / "PROJECT.md").read_text(encoding="utf-8")
    assert "# Demo" in text
    assert "A demo project." in text
    assert "./features.json" in text


def test_placeholder_features_validate_but_fail_gate(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0
    assert "features.json validates" in result.stdout
    entries = json.loads((target / "features.json").read_text(encoding="utf-8"))
    assert entries[0]["passes"] is False
    gate = subprocess.run(
        [sys.executable, str(CHECK_FEATURES_PY), str(target / "features.json"), "--gate"],
        capture_output=True,
        text=True,
    )
    assert gate.returncode == 1  # placeholder must never pass a gate


def test_baseline_snapshot_matches_features(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0
    features = (target / "features.json").read_bytes()
    baseline = (target / "checkpoints" / "features.baseline.json").read_bytes()
    assert features == baseline


def test_init_sh_is_executable_and_fails(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0
    init_sh = target / "init.sh"
    assert os.access(init_sh, os.X_OK)
    proc = subprocess.run([str(init_sh)], capture_output=True, text=True)
    assert proc.returncode != 0  # stub must never be reported green


def test_progress_md_is_seeded_with_dated_line(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0
    lines = (target / "progress.md").read_text(encoding="utf-8").strip().splitlines()
    assert lines[0].startswith("# Progress")
    assert "orchestrator: state files scaffolded" in lines[1]


def test_valid_seed_is_copied_verbatim(tmp_path):
    evidence = tmp_path / "proof.log"
    evidence.write_text("1 passed\n", encoding="utf-8")
    seed = tmp_path / "seed.json"
    seed_entries = [
        {
            "id": "signup-basic",
            "title": "User can sign up",
            "acceptance": "POST /signup returns 201; tests/test_signup.py green",
            "passes": False,
            "evidence": None,
            "milestone": "m1",
        }
    ]
    seed.write_text(json.dumps(seed_entries), encoding="utf-8")
    target, result = scaffold(tmp_path, "--features", seed)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / "features.json").read_text(encoding="utf-8") == seed.read_text(
        encoding="utf-8"
    )


def test_invalid_seed_writes_nothing(tmp_path):
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps([{"id": "bad entry"}]), encoding="utf-8")
    target, result = scaffold(tmp_path, "--features", seed)
    assert result.returncode == 1
    assert "FAIL" in result.stdout
    assert not target.exists()  # nothing partial left behind


def test_missing_seed_file_is_usage_error(tmp_path):
    target, result = scaffold(tmp_path, "--features", tmp_path / "nope.json")
    assert result.returncode == 2
    assert "error: no such seed file" in result.stderr
    assert not target.exists()


def test_target_is_regular_file_is_usage_error(tmp_path):
    target = tmp_path / "state"
    target.write_text("not a directory", encoding="utf-8")
    result = run_cli(target, "--name", "Demo", "--goal", "A demo project.")
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert target.read_text(encoding="utf-8") == "not a directory"


def test_post_write_validation_failure_cleans_up(tmp_path):
    # Seed validates pre-write (evidence relative to the seed's own dir) but
    # fails post-write revalidation from the target dir — must leave nothing.
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    (seed_dir / "proof.log").write_text("evidence", encoding="utf-8")
    seed = seed_dir / "seed.json"
    seed.write_text(
        json.dumps(
            [
                {
                    "id": "feat-a",
                    "title": "Done feature",
                    "acceptance": "It works.",
                    "passes": True,
                    "evidence": "proof.log",
                    "milestone": "m1",
                }
            ]
        ),
        encoding="utf-8",
    )
    target, result = scaffold(tmp_path, "--features", seed)
    assert result.returncode == 1
    assert not target.exists(), "failed run must not leave partial state behind"


def test_valid_seed_with_absolute_evidence_scaffolds(tmp_path):
    proof = tmp_path / "proof.log"
    proof.write_text("evidence", encoding="utf-8")
    seed = tmp_path / "seed.json"
    seed.write_text(
        json.dumps(
            [
                {
                    "id": "feat-a",
                    "title": "Done feature",
                    "acceptance": "It works.",
                    "passes": True,
                    "evidence": str(proof),
                    "milestone": "m1",
                }
            ]
        ),
        encoding="utf-8",
    )
    target, result = scaffold(tmp_path, "--features", seed)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (target / "features.json").is_file()


def test_refuses_existing_state_files(tmp_path):
    target = tmp_path / "state"
    target.mkdir()
    (target / "features.json").write_text("[]", encoding="utf-8")
    _, result = scaffold(tmp_path)
    assert result.returncode == 1
    assert "refusing to overwrite" in result.stdout
    assert not (target / "PROJECT.md").exists()


def test_empty_name_is_usage_error(tmp_path):
    result = run_cli(tmp_path / "state", "--name", "  ", "--goal", "g")
    assert result.returncode == 2


def test_gitignore_created_with_pycache(tmp_path):
    target, result = scaffold(tmp_path)
    assert result.returncode == 0
    gitignore = target / ".gitignore"
    assert gitignore.is_file()
    assert "__pycache__/" in gitignore.read_text(encoding="utf-8")
    assert f"ok: wrote {gitignore}" in result.stdout


def test_existing_gitignore_left_untouched(tmp_path):
    target = tmp_path / "state"
    target.mkdir()
    gitignore = target / ".gitignore"
    gitignore.write_text("custom-rule\n", encoding="utf-8")
    _, result = scaffold(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert gitignore.read_text(encoding="utf-8") == "custom-rule\n"
    assert "left untouched" in result.stdout


def test_failed_run_cleans_up_gitignore(tmp_path):
    # Same failure mode as test_post_write_validation_failure_cleans_up:
    # the .gitignore written by the scaffolder must not survive cleanup.
    seed_dir = tmp_path / "seeds"
    seed_dir.mkdir()
    (seed_dir / "proof.log").write_text("evidence", encoding="utf-8")
    seed = seed_dir / "seed.json"
    seed.write_text(
        json.dumps(
            [
                {
                    "id": "feat-a",
                    "title": "Done feature",
                    "acceptance": "It works.",
                    "passes": True,
                    "evidence": "proof.log",
                    "milestone": "m1",
                }
            ]
        ),
        encoding="utf-8",
    )
    target, result = scaffold(tmp_path, "--features", seed)
    assert result.returncode == 1
    assert not (target / ".gitignore").exists()
    assert not target.exists()
