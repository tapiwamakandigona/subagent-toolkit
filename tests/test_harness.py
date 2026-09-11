"""Behavioral regression tests; Git, agent, and evaluator invocations are offline fixtures."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"

FIXTURE_AGENT = r'''
import json, os, sys, time
from pathlib import Path
state = Path(os.environ['FIXTURE_STATE'])
calls = int((state / 'calls').read_text()) if (state / 'calls').exists() else 0
calls += 1
(state / 'calls').write_text(str(calls))
brief = sys.stdin.read()
(state / ('prompt-' + str(calls))).write_text(brief)
(state / ('env-' + str(calls))).write_text(json.dumps(dict(os.environ)))
behavior = os.environ.get('BEHAVIOR', 'noop')
status = 'progress'
requests = []
claims = [{"text": "fixture claim", "label": "ASSUMED", "evidence": None}]

def flip_all():
    p = Path('features.json'); data = json.loads(p.read_text())
    for f in data['features']:
        f['passes'] = True; f['evidence'] = 'artifacts/check.txt'
    p.write_text(json.dumps(data))

if behavior == 'nonzero' or (behavior == 'fail_then_complete' and calls == 1):
    print('fixture failure output'); sys.exit(7)
if behavior == 'sleep':
    time.sleep(5)
if behavior == 'big_output':
    sys.stdout.write('x' * 2000)
if behavior in ('complete', 'fail_then_complete', 'failed_report'):
    flip_all(); status = 'complete'
    if behavior == 'failed_report':
        sys.exit(7)
elif behavior == 'fake_evidence':
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/check.txt').write_text('agent-written evidence without run id\n')
    flip_all(); status = 'complete'
elif behavior == 'status_only':
    status = 'complete'
elif behavior == 'change_worktree':
    with Path('app.txt').open('a') as f: f.write('change ' + str(calls) + '\n')
elif behavior == 'log_only':
    with Path('progress.md').open('a') as f: f.write('log ' + str(calls) + '\n')
elif behavior == 'edit_check':
    with Path('verify.sh').open('a') as f: f.write('# weakened\n')
elif behavior == 'edit_guard':
    Path('check_features.py').write_text('raise SystemExit(0)\n')
elif behavior == 'edit_hook':
    with Path('hooks/pre_iteration').open('a') as f: f.write('# changed\n')
elif behavior == 'delete_test':
    Path('tests/test_app.py').unlink()
elif behavior == 'add_test':
    Path('tests/new.py').write_text('# unapproved check\n')
elif behavior == 'edit_criterion':
    p = Path('features.json'); data = json.loads(p.read_text())
    data['features'][0]['acceptance'] = 'weakened criterion'; p.write_text(json.dumps(data))
elif behavior == 'false_evidence':
    p = Path('features.json'); data = json.loads(p.read_text())
    data['features'][0]['passes'] = True; p.write_text(json.dumps(data)); status = 'complete'
elif behavior == 'no_report':
    sys.exit(0)
elif behavior == 'bad_report':
    Path('report.json').write_text('{"task": "x"}'); sys.exit(0)
elif behavior == 'unlabeled_claim':
    claims = [{"text": "it works", "label": "TRUE", "evidence": None}]
elif behavior == 'verified_without_evidence':
    claims = [{"text": "tests pass", "label": "VERIFIED", "evidence": ""}]
elif behavior == 'ask_approval':
    requests = ["Delete the production database table `users` (irreversible)"]
    status = 'blocked'
elif behavior == 'stop_after_first' and calls == 1:
    Path('AGENT_STOP').write_text('')
report = {"task": "fixture task", "status": status, "claims": claims,
          "approval_requests": requests, "next": "fixture next"}
Path('report.json').write_text(json.dumps(report))
'''

FIXTURE_EVALUATOR = r'''
import json, os, sys
from pathlib import Path
state = Path(os.environ['FIXTURE_STATE'])
n = int((state / 'eval-calls').read_text()) if (state / 'eval-calls').exists() else 0
n += 1
(state / 'eval-calls').write_text(str(n))
(state / ('eval-prompt-' + str(n))).write_text(sys.stdin.read())
mode = os.environ.get('EVAL_BEHAVIOR', 'pass')
if mode == 'writes_code':
    Path('app.txt').write_text('evaluator tampered\n')
    Path('evaluation.json').write_text(json.dumps({"verdict": "PASS", "findings": []}))
elif mode == 'needs_work':
    Path('evaluation.json').write_text(json.dumps(
        {"verdict": "NEEDS_WORK", "findings": ["artifacts/check.txt does not show the feature end-to-end"]}))
elif mode == 'needs_work_then_pass':
    verdict = 'NEEDS_WORK' if n == 1 else 'PASS'
    findings = ["finding one"] if n == 1 else []
    Path('evaluation.json').write_text(json.dumps({"verdict": verdict, "findings": findings}))
elif mode == 'invalid':
    Path('evaluation.json').write_text('{"verdict": "MAYBE"}')
elif mode == 'silent':
    pass
else:
    Path('evaluation.json').write_text(json.dumps({"verdict": "PASS", "findings": []}))
'''

FIXTURE_VERIFY = (
    '#!/bin/sh\n'
    'printf "verify\\n" >> "$FIXTURE_STATE/verify-calls"\n'
    'if [ "${VERIFY_WRITES_EVIDENCE:-1}" = 1 ]; then\n'
    '  mkdir -p artifacts\n'
    '  printf "checks ran for %s\\n" "$HARNESS_RUN_ID" > artifacts/check.txt\n'
    'fi\n'
    'exit "${VERIFY_EXIT:-0}"\n'
)

FIXTURE_GIT = (
    "#!/bin/sh\n"
    "# Test fixture; never calls a real Git binary.\n"
    'if [ "${GIT_FIXTURE_FAIL:-0}" = 1 ]; then exit 1; fi\n'
    'case "$*" in\n'
    '  "rev-parse --is-inside-work-tree") echo true ;;\n'
    '  "rev-parse --verify HEAD") echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;\n'
    '  *) exit 99 ;;\n'
    'esac\n'
)


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
        for name in ("PROMPT.md", "PROJECT.md", "AGENTS.md", "EVALUATOR.md"):
            (self.project / name).write_text("Fixture %s: perform one task.\n" % name)
        (self.project / "progress.md").write_text("# Progress\n")
        (self.project / "app.txt").write_text("baseline\n")
        (self.project / "tests").mkdir()
        (self.project / "tests/test_app.py").write_text("# Frozen test fixture\n")
        self.feature = {
            "id": "F1", "title": "Fixture feature", "acceptance": "Check a fixture artifact",
            "verify": "./verify.sh", "passes": False, "evidence": ""
        }
        self.write_features([self.feature])
        self.executable(self.project / "verify.sh", FIXTURE_VERIFY)
        self.executable(self.bin / "git", FIXTURE_GIT)
        agent = self.bin / "fixture_agent.py"
        agent.write_text(FIXTURE_AGENT)
        evaluator = self.bin / "fixture_evaluator.py"
        evaluator.write_text(FIXTURE_EVALUATOR)
        self.evaluator_cmd = sys.executable + " " + str(evaluator)
        self.env = {
            "PATH": str(self.bin) + ":/usr/bin:/bin",
            "HOME": str(self.base),
            "LC_ALL": "C",
            "AGENT_CMD": sys.executable + " " + str(agent),
            "PYTHON": sys.executable,
            "FIXTURE_STATE": str(self.state),
            "ITER_TIMEOUT": "0",
        }

    # helpers -----------------------------------------------------------------
    def executable(self, path, text):
        path.write_text(text)
        path.chmod(0o700)

    def write_features(self, features):
        (self.project / "features.json").write_text(json.dumps({"features": features}))

    def run_loop(self, cap="5", behavior="noop", **env):
        return subprocess.run(
            ["/bin/sh", "./loop.sh", str(cap)], cwd=self.project,
            env={**self.env, "BEHAVIOR": behavior, **env},
            text=True, capture_output=True, timeout=30
        )

    def calls(self):
        return int((self.state / "calls").read_text()) if (self.state / "calls").exists() else 0

    def eval_calls(self):
        return int((self.state / "eval-calls").read_text()) if (self.state / "eval-calls").exists() else 0

    def guard(self, command, *args):
        return subprocess.run(
            [sys.executable, "./check_features.py", command, *args], cwd=self.project,
            env=self.env, text=True, capture_output=True, timeout=5
        )

    def complete_feature(self):
        self.feature.update(passes=True, evidence="artifacts/check.txt")
        self.write_features([self.feature])

    def ledger(self):
        runs = sorted((self.project / ".harness/runs").glob("*.jsonl"))
        self.assertEqual(len(runs), 1, "exactly one ledger expected")
        return [json.loads(line) for line in runs[0].read_text().splitlines() if line.strip()], runs[0]

    def event_types(self):
        return [row["type"] for row in self.ledger()[0]]

    def install_hook(self, name, text, trust=True):
        (self.project / "hooks").mkdir(exist_ok=True)
        self.executable(self.project / "hooks" / name, text)
        if trust:
            digest = sha256((self.project / "hooks" / name).read_bytes()).hexdigest()
            with (self.project / "hooks.lock").open("a") as handle:
                handle.write("%s hooks/%s\n" % (digest, name))

    # completion gate -----------------------------------------------------------
    def test_happy_path_checks_and_features_are_required(self):
        result = self.run_loop(behavior="complete")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("VERIFIED green", result.stdout)
        self.assertEqual(self.calls(), 1)
        self.assertIn("complete", self.event_types())

    def test_already_complete_runs_checks_without_invoking_agent(self):
        self.complete_feature()
        result = self.run_loop()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.calls(), 0)
        self.assertTrue((self.state / "verify-calls").is_file())

    def test_agent_written_evidence_without_run_id_cannot_pass(self):
        result = self.run_loop(1, "fake_evidence", VERIFY_WRITES_EVIDENCE="0")
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_stale_evidence_from_a_previous_run_cannot_pass(self):
        (self.project / "artifacts").mkdir()
        (self.project / "artifacts/check.txt").write_text("checks ran for run-OLD\n")
        self.complete_feature()
        result = self.run_loop(1, VERIFY_WRITES_EVIDENCE="0")
        self.assertEqual(result.returncode, 4)  # agent invoked, cap reached, never green
        self.assertEqual(self.calls(), 1)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_false_features_do_not_pass_on_status(self):
        result = self.run_loop(1, "status_only")
        self.assertEqual(result.returncode, 4)
        self.assertIn("agent reports complete", result.stdout)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_empty_evidence_cannot_pass(self):
        result = self.run_loop(1, "false_evidence")
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_agent_failure_with_complete_report_cannot_succeed(self):
        result = self.run_loop(5, "failed_report")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)
        self.assertNotIn("VERIFIED green", result.stdout)

    # setup validation -----------------------------------------------------------
    def test_missing_verifier_is_configuration_failure(self):
        (self.project / "verify.sh").unlink()
        self.assertEqual(self.run_loop(behavior="complete").returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_nonexecutable_verifier_is_configuration_failure(self):
        (self.project / "verify.sh").chmod(0o600)
        self.assertEqual(self.run_loop(behavior="complete").returncode, 3)

    def test_missing_prompt_or_features_is_configuration_failure(self):
        (self.project / "PROMPT.md").unlink()
        self.assertEqual(self.run_loop(1).returncode, 3)
        (self.project / "PROMPT.md").write_text("x\n")
        (self.project / "features.json").unlink()
        self.assertEqual(self.run_loop(1).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_zero_negative_nonnumeric_and_oversized_caps_rejected(self):
        for cap in ("0", "-1", "abc", "1.5", "1001", "999999999999999999999999"):
            with self.subTest(cap=cap):
                self.assertEqual(self.run_loop(cap).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_bad_timeout_budget_and_cap_values_rejected(self):
        for env in ({"ITER_TIMEOUT": "abc"}, {"MAX_MINUTES": "-1"}, {"OUTPUT_CAP": "1.5"}):
            with self.subTest(env=env):
                self.assertEqual(self.run_loop(1, **env).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_nonrepo_or_missing_initial_commit_rejected(self):
        self.assertEqual(self.run_loop(GIT_FIXTURE_FAIL="1").returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_evaluator_requires_prompt_file(self):
        (self.project / "EVALUATOR.md").unlink()
        self.assertEqual(self.run_loop(1, EVALUATOR_CMD=self.evaluator_cmd).returncode, 3)

    def test_placeholder_or_invalid_feature_definitions_rejected(self):
        for mutate in (
            lambda f: f.update(verify="{{test_cmd}}"),
            lambda f: f.update(passes="true"),
        ):
            feature = dict(self.feature)
            mutate(feature)
            self.write_features([feature])
            self.assertEqual(self.run_loop().returncode, 3)
        self.write_features([])
        self.assertEqual(self.run_loop().returncode, 3)
        self.write_features([self.feature, self.feature.copy()])
        self.assertEqual(self.run_loop().returncode, 3)

    # failure handling ------------------------------------------------------------
    def test_one_failure_informed_retry_then_halt(self):
        result = self.run_loop(5, "nonzero")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)
        self.assertIn("agent command exited with status 7", (self.state / "prompt-2").read_text())

    def test_retry_can_complete(self):
        result = self.run_loop(5, "fail_then_complete")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.calls(), 2)

    def test_verifier_failure_gets_only_one_retry(self):
        result = self.run_loop(5, "complete", VERIFY_EXIT="8")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)
        self.assertIn("verification command exited with status 8", (self.state / "prompt-2").read_text())

    def test_hard_cap_never_overrun_even_for_retry(self):
        result = self.run_loop(1, "nonzero")
        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.calls(), 1)

    def test_outputs_do_not_echo_agent_transcript(self):
        result = self.run_loop(5, "nonzero")
        self.assertNotIn("fixture failure output", result.stdout + result.stderr)
        self.assertNotIn("fixture failure output", (self.state / "prompt-2").read_text())

    # stall detection -------------------------------------------------------------
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

    def test_progress_ignores_commit_metadata_and_transient_files_but_sees_code(self):
        first = self.guard("fingerprint").stdout
        (self.project / ".git").mkdir()
        (self.project / ".git/HEAD").write_text("irrelevant-commit\n")
        (self.project / ".harness").mkdir()
        (self.project / ".harness/x.jsonl").write_text("{}\n")
        (self.project / "report.json").write_text("{}")
        self.assertEqual(self.guard("fingerprint").stdout, first)
        (self.project / "app.txt").write_text("real-change\n")
        self.assertNotEqual(self.guard("fingerprint").stdout, first)

    # check integrity -------------------------------------------------------------
    def test_check_changes_fail_integrity_immediately(self):
        self.assertEqual(self.run_loop(5, "edit_check").returncode, 6)
        self.assertEqual(self.calls(), 1)

    def test_guard_changes_cannot_disable_trusted_checker(self):
        self.assertEqual(self.run_loop(5, "edit_guard").returncode, 6)

    def test_deleted_or_added_check_is_rejected(self):
        for behavior in ("delete_test", "add_test"):
            with self.subTest(behavior=behavior):
                self.assertEqual(self.run_loop(5, behavior).returncode, 6)
                (self.project / "tests/test_app.py").write_text("# Frozen test fixture\n")
                (self.project / "tests/new.py").unlink(missing_ok=True)
                shutil.rmtree(self.project / ".harness")

    def test_acceptance_criteria_are_frozen(self):
        self.assertEqual(self.run_loop(5, "edit_criterion").returncode, 6)

    def test_python_test_caches_do_not_count_as_check_tampering(self):
        baseline = self.base / "baseline.json"
        self.assertEqual(self.guard("snapshot", "--output", str(baseline)).returncode, 0)
        cache = self.project / "tests/__pycache__"
        cache.mkdir()
        (cache / "test_app.cpython-313.pyc").write_bytes(b"synthetic-cache")
        self.assertEqual(self.guard("integrity", "--baseline", str(baseline)).returncode, 0)

    def test_evidence_must_exist_be_nonempty_and_stay_inside_project(self):
        self.complete_feature()
        (self.project / "artifacts").mkdir()
        (self.project / "artifacts/check.txt").write_text("")
        self.assertNotEqual(self.guard("complete").returncode, 0)
        (self.project / "artifacts/check.txt").write_text("evidence for run-1\n")
        self.assertEqual(self.guard("complete", "--run-id", "run-1").returncode, 0)
        self.assertNotEqual(self.guard("complete", "--run-id", "run-2").returncode, 0)
        self.feature["evidence"] = "../outside.txt"
        (self.base / "outside.txt").write_text("fixture")
        self.write_features([self.feature])
        self.assertNotEqual(self.guard("complete").returncode, 0)
        (self.project / "artifacts/check.txt").unlink()
        (self.project / "artifacts/check.txt").symlink_to(self.base / "outside.txt")
        self.feature["evidence"] = "artifacts/check.txt"
        self.write_features([self.feature])
        self.assertNotEqual(self.guard("complete").returncode, 0)

    # structured iteration report ---------------------------------------------------
    def test_missing_report_is_a_failure_not_progress(self):
        result = self.run_loop(5, "no_report")
        self.assertEqual(result.returncode, 1)
        self.assertIn("iteration report missing or invalid", (self.state / "prompt-2").read_text())

    def test_malformed_report_or_unlabeled_claim_rejected(self):
        for behavior in ("bad_report", "unlabeled_claim", "verified_without_evidence"):
            with self.subTest(behavior=behavior):
                result = self.run_loop(5, behavior)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                shutil.rmtree(self.project / ".harness")

    def test_report_is_archived_out_of_the_project(self):
        self.run_loop(1)
        self.assertFalse((self.project / "report.json").exists())

    def test_report_validator_rejects_unknown_fields_and_bad_evidence_paths(self):
        good = {"task": "t", "status": "progress", "claims": [{"text": "x", "label": "ASSUMED", "evidence": None}],
                "approval_requests": [], "next": "n"}
        (self.project / "report.json").write_text(json.dumps(good))
        self.assertEqual(self.guard("report").returncode, 0)
        bad = dict(good, extra=1)
        (self.project / "report.json").write_text(json.dumps(bad))
        self.assertNotEqual(self.guard("report").returncode, 0)
        bad = dict(good, claims=[{"text": "x", "label": "VERIFIED", "evidence": "../etc/passwd"}])
        (self.project / "report.json").write_text(json.dumps(bad))
        self.assertNotEqual(self.guard("report").returncode, 0)

    # approvals ----------------------------------------------------------------------
    def test_approval_request_halts_with_exit_5_before_verification(self):
        result = self.run_loop(5, "ask_approval")
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
        self.assertEqual(self.calls(), 1)
        text = (self.project / "APPROVAL_REQUESTED.md").read_text()
        self.assertIn("production database", text)
        self.assertIn("approval_requested", self.event_types())
        self.assertFalse((self.state / "verify-calls").read_text().count("verify") > 1)

    # operator controls ----------------------------------------------------------------
    def test_agent_stop_file_halts_with_exit_7(self):
        result = self.run_loop(5, "stop_after_first")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(self.calls(), 1)

    def test_steer_file_is_injected_once_then_consumed(self):
        (self.project / "STEER.md").write_text("Operator: focus on the login page only.\n")
        self.run_loop(2, "change_worktree")
        self.assertIn("focus on the login page only", (self.state / "prompt-1").read_text())
        self.assertNotIn("focus on the login page only", (self.state / "prompt-2").read_text())
        self.assertFalse((self.project / "STEER.md").exists())
        self.assertIn("steer_consumed", self.event_types())

    # wall-clock and output caps ---------------------------------------------------------
    @unittest.skipUnless(shutil.which("timeout"), "coreutils timeout not available")
    def test_iteration_timeout_is_a_failure_with_verbatim_status(self):
        result = self.run_loop(5, "sleep", ITER_TIMEOUT="1")
        self.assertEqual(result.returncode, 1)
        self.assertIn("timed out after 1 seconds", (self.state / "prompt-2").read_text())

    def test_timeout_requires_timeout_binary_or_explicit_opt_out(self):
        env = dict(self.env, PATH=str(self.bin))  # no coreutils on PATH → no timeout(1)
        result = subprocess.run(["/bin/sh", "./loop.sh", "1"], cwd=self.project,
                                env={**env, "ITER_TIMEOUT": "10", "BEHAVIOR": "noop"},
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 3)

    def test_wall_clock_budget_stops_with_cap_exit(self):
        result = self.run_loop(5, "change_worktree", MAX_MINUTES="0")
        self.assertEqual(result.returncode, 4)  # no budget → iterations bound
        self.assertEqual(self.calls(), 5)

    def test_output_cap_is_enforced(self):
        result = self.run_loop(5, "big_output", OUTPUT_CAP="100")
        self.assertEqual(result.returncode, 1)
        self.assertIn("exceeded the 100 byte cap", (self.state / "prompt-2").read_text())

    # hooks ---------------------------------------------------------------------------------
    def test_trusted_pre_hook_runs_and_can_block(self):
        self.install_hook("pre_iteration", '#!/bin/sh\nprintf "hook\\n" >> "$FIXTURE_STATE/hook-calls"\nexit "${HOOK_EXIT:-0}"\n')
        result = self.run_loop(2, "change_worktree")
        self.assertEqual(result.returncode, 4)
        self.assertEqual((self.state / "hook-calls").read_text().count("hook"), 2)
        shutil.rmtree(self.project / ".harness")
        result = self.run_loop(5, "change_worktree", HOOK_EXIT="9")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), 2)  # a blocking hook means the agent never ran
        failures = [row["data"]["failure"] for row in self.ledger()[0] if row["type"] == "iteration_failed"]
        self.assertEqual(failures, ["pre_iteration hook exited with status 9"] * 2)

    def test_untrusted_hook_is_skipped_not_run(self):
        self.install_hook("pre_iteration", '#!/bin/sh\nprintf "hook\\n" >> "$FIXTURE_STATE/hook-calls"\n', trust=False)
        self.run_loop(1)
        self.assertFalse((self.state / "hook-calls").exists())
        self.assertIn("hook_skipped", self.event_types())

    def test_hook_changed_after_trust_is_rejected_at_setup(self):
        self.install_hook("pre_iteration", '#!/bin/sh\nexit 0\n')
        with (self.project / "hooks/pre_iteration").open("a") as handle:
            handle.write("# edited after trust\n")
        self.assertEqual(self.run_loop(1).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_hook_edited_mid_run_is_integrity_violation(self):
        self.install_hook("pre_iteration", '#!/bin/sh\nexit 0\n')
        self.assertEqual(self.run_loop(5, "edit_hook").returncode, 6)

    # evaluator (sequential, read-only) ----------------------------------------------------------
    def test_evaluator_runs_after_agent_and_pass_allows_completion(self):
        result = self.run_loop(3, "complete", EVALUATOR_CMD=self.evaluator_cmd)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.eval_calls(), 1)
        self.assertIn("fixture task", (self.state / "eval-prompt-1").read_text())

    def test_evaluator_needs_work_blocks_completion_and_feeds_findings(self):
        result = self.run_loop(3, "complete", EVALUATOR_CMD=self.evaluator_cmd, EVAL_BEHAVIOR="needs_work_then_pass")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.calls(), 2)
        self.assertIn("finding one", (self.state / "prompt-2").read_text())

    def test_evaluator_that_never_passes_ends_in_stall_not_green(self):
        result = self.run_loop(5, "complete", EVALUATOR_CMD=self.evaluator_cmd, EVAL_BEHAVIOR="needs_work")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("VERIFIED green", result.stdout)

    def test_evaluator_writing_to_project_is_integrity_violation(self):
        result = self.run_loop(3, "complete", EVALUATOR_CMD=self.evaluator_cmd, EVAL_BEHAVIOR="writes_code")
        self.assertEqual(result.returncode, 6)

    def test_invalid_or_missing_evaluation_is_a_failure(self):
        for mode in ("invalid", "silent"):
            with self.subTest(mode=mode):
                result = self.run_loop(5, "change_worktree", EVALUATOR_CMD=self.evaluator_cmd, EVAL_BEHAVIOR=mode)
                self.assertEqual(result.returncode, 1)
                shutil.rmtree(self.project / ".harness")

    # durability ---------------------------------------------------------------------------------
    def test_ledger_hash_chain_verifies_and_detects_tampering(self):
        self.run_loop(2, "change_worktree")
        rows, path = self.ledger()
        self.assertEqual(rows[0]["type"], "run_start")
        self.assertEqual(self.guard("chain", "--log", str(path)).returncode, 0)
        lines = path.read_text().splitlines()
        row = json.loads(lines[1])
        row["data"]["status"] = "0"
        lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n")
        self.assertNotEqual(self.guard("chain", "--log", str(path)).returncode, 0)

    def test_second_loop_cannot_start_while_lock_held(self):
        (self.project / ".harness/lock").mkdir(parents=True)
        (self.project / ".harness/lock/pid").write_text(str(os.getpid()))
        self.assertEqual(self.run_loop(1).returncode, 3)
        self.assertEqual(self.calls(), 0)

    def test_stale_lock_is_reclaimed_and_recorded(self):
        (self.project / ".harness/lock").mkdir(parents=True)
        (self.project / ".harness/lock/pid").write_text("999999")
        result = self.run_loop(1)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(self.ledger()[0][0]["data"]["stale_lock_reclaimed"], "1")
        self.assertFalse((self.project / ".harness/lock").exists())

    # two-phase setup ------------------------------------------------------------------------------
    def test_init_runs_once_before_baseline_and_failure_is_setup_error(self):
        self.executable(self.project / "init.sh", '#!/bin/sh\nprintf "init\\n" >> "$FIXTURE_STATE/init-calls"\nexit "${INIT_EXIT:-0}"\n')
        result = self.run_loop(2, "change_worktree")
        self.assertEqual(result.returncode, 4)
        self.assertEqual((self.state / "init-calls").read_text().count("init"), 1)
        shutil.rmtree(self.project / ".harness")
        self.assertEqual(self.run_loop(2, INIT_EXIT="1").returncode, 3)

    def test_sandbox_prefix_wraps_agent_and_strips_secrets(self):
        shutil.copy2(TEMPLATES / "sandbox.sh", self.project / "sandbox.sh")
        (self.project / "sandbox.sh").chmod(0o755)
        result = self.run_loop(1, SANDBOX_CMD="./sandbox.sh", SECRET_TOKEN="do-not-leak",
                               SANDBOX_KEEP="FIXTURE_STATE BEHAVIOR", PATH=self.env["PATH"] + ":/usr/sbin:/sbin")
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        env = json.loads((self.state / "env-1").read_text())
        self.assertNotIn("SECRET_TOKEN", env)
        self.assertIn(env.get("HARNESS_SANDBOX"), {"none", "netns", "bwrap"})
        self.assertTrue(env.get("HARNESS_RUN_ID", "").startswith("run-"))
        agent_exit = [row for row in self.ledger()[0] if row["type"] == "agent_exit"][0]
        self.assertEqual(agent_exit["data"]["sandbox_mode"], env["HARNESS_SANDBOX"])


if __name__ == "__main__":
    unittest.main()
