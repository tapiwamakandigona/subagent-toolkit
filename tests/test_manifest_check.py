"""Tests for manifest.py's manifest building, lint rules, and --check flag."""

import json
import subprocess
import sys
from pathlib import Path

import manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PY = REPO_ROOT / "harness" / "scripts" / "manifest.py"

GOOD_SKILL = """---
name: {name}
description: Does a thing. Use when a thing needs doing.
license: MIT
metadata:
  version: "1.1.0"
---

# Skill

Body text.
"""


def make_toolkit(root, skill_name="good-skill", skill_text=None):
    d = root / "skills" / skill_name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        skill_text or GOOD_SKILL.format(name=skill_name), encoding="utf-8"
    )
    return root


def run_manifest(*args):
    return subprocess.run(
        [sys.executable, str(MANIFEST_PY), *args],
        capture_output=True, text=True,
    )


def test_clean_toolkit_check_passes(tmp_path):
    make_toolkit(tmp_path)
    r = run_manifest("--check", str(tmp_path))
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["skills"][0]["name"] == "good-skill"
    assert data["skills"][0]["version"] == "1.1.0"
    assert "warnings" not in data


def test_check_fails_on_warnings(tmp_path):
    bad = "---\nname: Bad_Name\ndescription: x\n---\nbody\n"
    make_toolkit(tmp_path, "bad-skill", bad)
    r = run_manifest("--check", str(tmp_path))
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert any("lowercase-hyphens" in w for w in data["warnings"])


def test_default_mode_exits_zero_despite_warnings(tmp_path):
    bad = "---\nname: Bad_Name\ndescription: x\n---\nbody\n"
    make_toolkit(tmp_path, "bad-skill", bad)
    r = run_manifest(str(tmp_path))
    assert r.returncode == 0


def test_name_dirname_mismatch_warned(tmp_path):
    text = GOOD_SKILL.format(name="other-name")
    make_toolkit(tmp_path, "my-skill", text)
    r = run_manifest(str(tmp_path))
    data = json.loads(r.stdout)
    assert any("does not match directory" in w for w in data["warnings"])


def test_hyphen_edge_cases_warned(tmp_path):
    for bad_name in ("-leading", "trailing-", "double--hyphen"):
        warnings, info = [], []
        text = GOOD_SKILL.format(name=bad_name)
        manifest._lint_common("x", manifest.parse_frontmatter(text), text,
                              warnings, info, [])
        assert any("lowercase-hyphens" in w for w in warnings), bad_name


def test_empty_vs_missing_description(tmp_path):
    warnings, info = [], []
    text = "---\nname: a-skill\ndescription:\n---\nbody\n"
    manifest._lint_common("x", manifest.parse_frontmatter(text), text,
                          warnings, info, [])
    assert any("present but empty" in w for w in warnings)

    warnings2, info2 = [], []
    text2 = "---\nname: a-skill\n---\nbody\n"
    manifest._lint_common("x", manifest.parse_frontmatter(text2), text2,
                          warnings2, info2, [])
    assert any("missing 'description'" in w for w in warnings2)


def test_missing_license_and_version_are_info_not_warning(tmp_path):
    text = "---\nname: a-skill\ndescription: Fine description here.\n---\nbody\n"
    make_toolkit(tmp_path, "a-skill", text)
    r = run_manifest("--check", str(tmp_path))
    assert r.returncode == 0  # info notes must not fail --check
    data = json.loads(r.stdout)
    assert any("license" in i for i in data["info"])
    assert any("metadata.version" in i for i in data["info"])


def test_body_token_budget_warning(tmp_path):
    text = GOOD_SKILL.format(name="big-skill") + ("word " * 4000)
    make_toolkit(tmp_path, "big-skill", text)
    r = run_manifest(str(tmp_path))
    data = json.loads(r.stdout)
    assert any("tokens" in w for w in data["warnings"])


def test_leftover_placeholder_warned_in_skills_not_prompts(tmp_path):
    text = GOOD_SKILL.format(name="ph-skill") + "\nFill {{this_in}} please.\n"
    make_toolkit(tmp_path, "ph-skill", text)
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "template.md").write_text(
        "# Template\n\nA template.\n\nUse {{placeholder}} here.\n", encoding="utf-8"
    )
    r = run_manifest(str(tmp_path))
    data = json.loads(r.stdout)
    ph_warnings = [w for w in data["warnings"] if "placeholder" in w]
    assert ph_warnings and all("ph-skill" in w for w in ph_warnings)


def test_pycache_excluded_from_resources(tmp_path):
    make_toolkit(tmp_path)
    junk = tmp_path / "skills" / "good-skill" / "__pycache__"
    junk.mkdir()
    (junk / "mod.cpython-313.pyc").write_bytes(b"\x00")
    scripts = tmp_path / "skills" / "good-skill" / "scripts"
    scripts.mkdir()
    (scripts / "helper.py").write_text("x = 1\n", encoding="utf-8")
    r = run_manifest(str(tmp_path))
    data = json.loads(r.stdout)
    res = data["skills"][0]["resources"]
    assert any("helper.py" in x for x in res)
    assert not any("__pycache__" in x for x in res)


def test_evals_json_accepted_without_warning(tmp_path):
    make_toolkit(tmp_path)
    evals = tmp_path / "skills" / "good-skill" / "evals"
    evals.mkdir()
    (evals / "evals.json").write_text(
        json.dumps({"skill": "good-skill", "cases": []}), encoding="utf-8"
    )
    r = run_manifest("--check", str(tmp_path))
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert any("evals.json" in x for x in data["skills"][0]["resources"])


def test_empty_root_warns_but_default_exit_zero(tmp_path):
    r = run_manifest(str(tmp_path))
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert any("toolkit root" in w for w in data["warnings"])


def test_real_repo_check_passes():
    r = run_manifest("--check", str(REPO_ROOT))
    assert r.returncode == 0, f"repo lint failed:\n{r.stdout}\n{r.stderr}"
