"""Tests for harness/scripts/check_placeholders.py."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "harness" / "scripts" / "check_placeholders.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True, text=True,
    )


def test_clean_file_passes(tmp_path):
    f = tmp_path / "clean.md"
    f.write_text("All filled in.\n", encoding="utf-8")
    assert run(f).returncode == 0


def test_placeholder_fails_with_location(tmp_path):
    f = tmp_path / "dirty.md"
    f.write_text("line one\nfill {{objective}} here\n", encoding="utf-8")
    r = run(f)
    assert r.returncode == 1
    assert "dirty.md:2" in r.stdout
    assert "{{objective}}" in r.stdout


def test_directory_scan(tmp_path):
    (tmp_path / "a.md").write_text("ok\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.md").write_text("{{leftover}}\n", encoding="utf-8")
    r = run(tmp_path)
    assert r.returncode == 1
    assert "b.md:1" in r.stdout


def test_missing_path_usage_error(tmp_path):
    assert run(tmp_path / "nope.md").returncode == 2


def test_no_args_usage_error():
    assert run().returncode == 2


def test_code_spans_and_fences_ignored(tmp_path):
    f = tmp_path / "skill.md"
    f.write_text(
        "Look for `{{title}}` markers.\n"
        "```\ntemplate: {{example}}\n```\n"
        "clean prose\n",
        encoding="utf-8",
    )
    assert run(f).returncode == 0
