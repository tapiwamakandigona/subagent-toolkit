"""Behavioral regression tests; Git and agent invocations are offline fixtures."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.project = self.base / "project"
        self.project.mkdir()
        self.state = self.base / "fixture-state"
        self.state.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for name in ("loop.sh", "check_features.py"):
            shutil.copy2(TEMPLATES / name, self.project / name)
        for name in ("PROMPT.md", "PROJECT.md", "AGENTS.md"):
            (self.project / name).write_text("Fixture project: perform one task.\n")
        (self.project / "progress.md").write_text("# Progress\n")
        (self.project / "app.txt").write_text("baseline\n")
        (self.project / "tests").mkdir()
        (self.project / "tests/test_app.py").write_text("# Frozen test fixture\n")
        self.feature = {
            "id": "F1", "title": "Fixture feature", "acceptance": "Check a fixture artifact",
            "verify": "./verify.sh", "passes": False, "evidence": ""
        }
        self.write_features([self.feature])
        self.executable(
            self.project / "verify.sh",
            '#!/bin/sh\nprintf "verify\\n" >> "$FIXTURE_STATE/verify-calls"\n'
            'exit "${VERIFY_EXIT:-0}"\n'
        )
        self.executable(
            self.bin / "git",
            "#!/bin/sh\n"
            "# Test fixture; never calls a real Git binary.\n"
            'if [ "${GIT_FIXTURE_FAIL:-0}" = 1 ]; then exit 1; fi\n'
            'case "$*" in\n'
            '  "rev-parse --is-inside-work-tree") echo true ;;\n'
            '  "rev-parse --verify HEAD") echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;\n'
            '  *) exit 99 ;;\n'
            'esac\n'
        )
        agent = self.bin / "fixture_agent.py"
        agent.write_text(
            "import json,os,sys\n"
            "from pathlib import Path\n"
            "state=Path(os.environ['FIXTURE_STATE'])\n"
            "calls=int((state/'calls').read_text()) if (state/'calls').exists() else 0\n"
            "calls+=1; (state/'calls').write_text(str(calls))\n"
            "brief=sys.stdin.read(); (state/('prompt-'+str(calls))).write_text(brief)\n"
            "behavior=os.environ.get('BEHAVIOR','noop')\n"
            "if behavior=='nonzero' or (behavior=='fail_then_complete' and calls==1):\n"
            "    print('fixture failure output'); sys.exit(7)\n"
            "if behavior in ('complete','fail_then_complete','failed_marker'):\n"
            "    p=Path('features.json'); data=json.loads(p.read_text())\n"
            "    Path('artifacts').mkdir(exist_ok=True)\n"
            "    Path('artifacts/check.txt').write_text('synthetic verification evidence\\n')\n"
            "    for f in data['features']:\n"
            "        f['passes']=True; f['evidence']='artifacts/check.txt'\n"
            "    p.write_text(json.dumps(data)); print('DONE_ALL')\n"
            "    if behavior=='failed_marker': sys.exit(7)\n"
            "elif behavior=='substring': print('NOT_DONE_ALL')\n"
            "elif behavior=='marker_only': print('DONE_ALL')\n"
            "elif behavior=='change_worktree':\n"
            "    with Path('app.txt').open('a') as f: f.write('change '+str(calls)+'\\n')\n"
            "elif behavior=='log_only':\n"
            "    with Path('progress.md').open('a') as f: f.write('log '+str(calls)+'\\n')\n"
            "elif behavior=='edit_check':\n"
            "    with Path('verify.sh').open('a') as f: f.write('# weakened\\n')\n"
            "elif behavior=='edit_guard':\n"
            "    Path('check_features.py').write_text('raise SystemExit(0)\\n')\n"
            "elif behavior=='delete_test': Path('tests/test_app.py').unlink()\n"
            "elif behavior=='add_test': Path('tests/new.py').write_text('# unapproved check\\n')\n"
            "elif behavior=='edit_criterion':\n"
            "    p=Path('features.json'); data=json.loads(p.read_text())\n"
            "    data['features'][0]['acceptance']='weakened criterion'; p.write_text(json.dumps(data))\n"
            "elif behavior=='false_evidence':\n"
            "    p=Path('features.json'); data=json.loads(p.read_text())\n"
            "    data['features'][0]['passes']=True; p.write_text(json.dumps(data)); print('DONE_ALL')\n"
        )
        self.env = {
            "PATH": str(self.bin) + ":/usr/bin:/bin",
            "HOME": str(self.base),
            "LC_ALL": "C",
            "AGENT_CMD": sys.executable + " " + str(agent),
            "PYTHON": sys.executable,
            "FIXTURE_STATE": str(self.state),
        }

    def executable(self, path, text):
        path.write_text(text)
        path.chmod(0o700)

    def write_features(self, features):
        (self.project / "features.json").write_text(json.dumps({"features": features}))

    def run_loop(self, cap="5", behavior="noop", **env):
        return subprocess.run(
            ["/bin/sh", "./loop.sh", str(cap)], cwd=self.project,
            env={**self.env, "BEHAVIOR": behavior, **env},
            text=True, capture_output=True, timeout=10
        )

    def calls(self):
        return int((self.state / "calls").read_text()) if (self.state / "calls").exists() else 0

    def guard(self, command, *args):
        return subprocess.run(
            [sys.executable, "./check_features.py", command, *args], cwd=self.project,
            env=self.env, text=True, capture_output=True, timeout=5
        )

    def complete_feature(self):
        (self.project / "artifacts").mkdir(exist_ok=True)
        (self.project / "artifacts/check.txt").write_text("fixture evidence\n")
        self.feature.update(passes=True, evidence="artifacts/check.txt")
        self.write_features([self.feature])

    def test_happy_path_checks_and_features_are_required(self):
        result = self.run_loop(behavior="complete")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("VERIFIED green", result.stdout)
        self.assertEqual(self.calls(), 1)

    def test_already_complete_runs_checks_without_invoking_agent(self):
        self.complete_feature()
        result = self.run_loop()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.calls(), 0)
        self.assertTrue((self.state / "verify-calls").is_file())

    def test_missing_verifier_is_configuration_failure(self):
        (self.project / "verify.sh").unlink()
        self.assertEqual(self.run_loop(behavior="complete").returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_nonexecutable_verifier_is_configuration_failure(self):
        (self.project / "verify.sh").chmod(0o600)
        self.assertEqual(self.run_loop(behavior="complete").returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_missing_prompt_is_configuration_failure(self):
        (self.project / "PROMPT.md").unlink()
        self.assertEqual(self.run_loop(1).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_missing_features_is_configuration_failure(self):
        (self.project / "features.json").unlink()
        self.assertEqual(self.run_loop(1).returncode, 3)

    def test_zero_negative_nonnumeric_and_oversized_caps_rejected(self):
        for cap in ("0", "-1", "abc", "1.5", "1001", "999999999999999999999999"):
            with self.subTest(cap=cap):
                self.assertEqual(self.run_loop(cap).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_nonrepo_or_missing_initial_commit_rejected(self):
        self.assertEqual(self.run_loop(GIT_FIXTURE_FAIL="1").returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_false_features_do_not_pass_on_marker(self):
        result = self.run_loop(1, "marker_only")
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_empty_evidence_cannot_pass(self):
        result = self.run_loop(1, "false_evidence")
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_agent_failure_with_marker_cannot_succeed(self):
        result = self.run_loop(5, "failed_marker")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_one_failure_informed_retry_then_halt(self):
        result = self.run_loop(5, "nonzero")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)
        prompt = (self.state / "prompt-2").read_text()
        self.assertIn("agent command exited with status 7", prompt)

    def test_retry_can_complete(self):
        result = self.run_loop(5, "fail_then_complete")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.calls(), 2)
        self.assertIn("agent command exited with status 7", (self.state / "prompt-2").read_text())

    def test_verifier_failure_gets_only_one_retry(self):
        result = self.run_loop(5, "complete", VERIFY_EXIT="8")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)
        self.assertIn("verification command exited with status 8", (self.state / "prompt-2").read_text())

    def test_marker_substring_not_recognized(self):
        result = self.run_loop(1, "substring")
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("completion marker seen", result.stdout)

    def test_two_no_progress_iterations_stall(self):
        result = self.run_loop(5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), 2)

    def test_progress_log_only_does_not_evade_stall(self):
        result = self.run_loop(5, "log_only")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.calls(), 2)

    def test_worktree_changes_do_not_false_stall(self):
        result = self.run_loop(3, "change_worktree")
        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.calls(), 3)

    def test_hard_cap_never_overrun_even_for_retry(self):
        result = self.run_loop(1, "nonzero")
        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.calls(), 1)

    def test_check_changes_fail_integrity_immediately(self):
        result = self.run_loop(5, "edit_check")
        self.assertEqual(result.returncode, 6)
        self.assertEqual(self.calls(), 1)

    def test_python_test_caches_do_not_count_as_check_tampering(self):
        baseline = self.base / "baseline.json"
        self.assertEqual(self.guard("snapshot", "--output", str(baseline)).returncode, 0)
        cache = self.project / "tests/__pycache__"
        cache.mkdir()
        (cache / "test_app.cpython-313.pyc").write_bytes(b"synthetic-cache")
        self.assertEqual(self.guard("integrity", "--baseline", str(baseline)).returncode, 0)

    def test_guard_changes_cannot_disable_trusted_checker(self):
        result = self.run_loop(5, "edit_guard")
        self.assertEqual(result.returncode, 6)
        self.assertEqual(self.calls(), 1)

    def test_deleted_or_added_check_is_rejected(self):
        for behavior in ("delete_test", "add_test"):
            with self.subTest(behavior=behavior):
                result = self.run_loop(5, behavior)
                self.assertEqual(result.returncode, 6)
                # Restore between independently snapshotted runs.
                (self.project / "tests/test_app.py").write_text("# Frozen test fixture\n")
                (self.project / "tests/new.py").unlink(missing_ok=True)

    def test_acceptance_criteria_are_frozen(self):
        self.assertEqual(self.run_loop(5, "edit_criterion").returncode, 6)

    def test_empty_feature_set_rejected(self):
        self.write_features([])
        self.assertEqual(self.run_loop().returncode, 3)

    def test_duplicate_feature_ids_rejected(self):
        self.write_features([self.feature, self.feature.copy()])
        self.assertEqual(self.run_loop().returncode, 3)

    def test_nonboolean_flag_rejected(self):
        self.feature["passes"] = "true"
        self.write_features([self.feature])
        self.assertEqual(self.run_loop().returncode, 3)

    def test_placeholder_definition_rejected(self):
        self.feature["verify"] = "{{test_cmd}}"
        self.write_features([self.feature])
        self.assertEqual(self.run_loop().returncode, 3)

    def test_evidence_must_exist_and_be_nonempty(self):
        self.complete_feature()
        (self.project / "artifacts/check.txt").write_text("")
        self.assertNotEqual(self.guard("complete").returncode, 0)
        (self.project / "artifacts/check.txt").unlink()
        self.assertNotEqual(self.guard("complete").returncode, 0)

    def test_evidence_cannot_escape_or_use_symlinks(self):
        self.complete_feature()
        self.feature["evidence"] = "../outside.txt"
        (self.base / "outside.txt").write_text("fixture")
        self.write_features([self.feature])
        self.assertNotEqual(self.guard("complete").returncode, 0)
        (self.project / "artifacts/check.txt").unlink()
        (self.project / "artifacts/check.txt").symlink_to(self.base / "outside.txt")
        self.feature["evidence"] = "artifacts/check.txt"
        self.write_features([self.feature])
        self.assertNotEqual(self.guard("complete").returncode, 0)

    def test_progress_ignores_commit_metadata_but_sees_code(self):
        first = self.guard("fingerprint").stdout
        (self.project / ".git").mkdir()
        (self.project / ".git/HEAD").write_text("irrelevant-commit\n")
        self.assertEqual(self.guard("fingerprint").stdout, first)
        (self.project / "app.txt").write_text("real-change\n")
        self.assertNotEqual(self.guard("fingerprint").stdout, first)

    def test_outputs_do_not_echo_agent_transcript(self):
        result = self.run_loop(5, "nonzero")
        self.assertNotIn("fixture failure output", result.stdout + result.stderr)
        self.assertNotIn("fixture failure output", (self.state / "prompt-2").read_text())


if __name__ == "__main__":
    unittest.main()
