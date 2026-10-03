from __future__ import annotations

import ast
import asyncio
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
RUNNER = TEMPLATES / "autonomous_loop.py"
STORE_SCRIPT = TEMPLATES / "credential_store.py"
sys.path.insert(0, str(TEMPLATES))
import credential_store as credentials
import browser_credentials as browser_credentials


COMPLETE = """
Path("artifact.txt").write_text("real fixture artifact")
data["features"][0]["passes"] = True
data["features"][0]["evidence"] = "agent claim, must be checked"
Path("features.json").write_text(json.dumps(data))
print("DONE_ALL")
"""


class LoopFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "PROMPT.md").write_text("Do one feature, verify, continue safely.")
        self.write_features()
        self.agent = self.root / "agent.py"
        self.write_agent('print("Progress report only")')

    def write_features(self, count=1, **overrides):
        payload = {
            "features": [
                {
                    "id": f"F{index + 1}", "title": f"Fixture {index + 1}",
                    "acceptance": "A real fixture artifact exists",
                    "verify": "test -f artifact.txt",
                    "passes": False, "evidence": "", **overrides,
                }
                for index in range(count)
            ]
        }
        (self.root / "features.json").write_text(json.dumps(payload))
        return payload

    def read_features(self):
        return json.loads((self.root / "features.json").read_text())

    def write_agent(self, body):
        self.agent.write_text(
            "import json, sys\nfrom pathlib import Path\n"
            "prompt = sys.stdin.read()\n"
            'counter = Path(".harness/counter")\n'
            "n = int(counter.read_text()) + 1 if counter.exists() else 1\n"
            "counter.write_text(str(n))\n"
            'data = json.loads(Path("features.json").read_text())\n'
            + textwrap.dedent(body)
        )

    def run_loop(self, *options, gate="true", agent=True):
        environment = os.environ.copy()
        if gate is None:
            environment.pop("VERIFY_CMD", None)
        else:
            environment["VERIFY_CMD"] = gate
        if agent:
            environment["AGENT_CMD"] = shlex.join([sys.executable, str(self.agent)])
        else:
            environment.pop("AGENT_CMD", None)
        result = subprocess.run(
            [
                sys.executable, str(RUNNER), "--root", str(self.root),
                "--max-iterations", "5", "--step-timeout", "2",
                "--max-seconds", "15", *options,
            ],
            cwd=self.root, env=environment, capture_output=True, text=True,
            timeout=20, check=False,
        )
        self.output = result.stdout + result.stderr
        return result

    def turns(self):
        counter = self.root / ".harness/counter"
        return int(counter.read_text()) if counter.exists() else 0


class PolicyTests(unittest.TestCase):
    def test_credentials_are_explicitly_usable(self):
        policy = (TEMPLATES / "AUTONOMY.md").read_text()
        self.assertIn("Do not refuse merely because", policy)
        self.assertIn("reuse that credential", policy)
        self.assertIn("browser workflow", policy)

    def test_actual_boundaries_remain(self):
        policy = (TEMPLATES / "AUTONOMY.md").read_text()
        for required in ("MFA/CAPTCHA", "unapproved", "700", "600",
                         "platform approval", "security controls"):
            with self.subTest(required=required):
                self.assertIn(required, policy)

    def test_single_writer_and_recovery_are_explicit(self):
        policy = (TEMPLATES / "AUTONOMY.md").read_text()
        for required in ("One writer", "no worker swarms", "One optional read-only",
                         "Two iterations", "one informed retry", "hard"):
            with self.subTest(required=required):
                self.assertIn(required, policy)

    def test_fresh_agent_and_browser_handoff(self):
        standing = (ROOT / "STANDING_SETUP.md").read_text()
        self.assertIn("AGENT_SECRET_DIR", standing)
        self.assertIn("Browser login is", standing)
        self.assertIn("not through model-visible", standing)
        self.assertIn("provider policies", standing)

    def test_verification_is_conditional_not_an_automatic_refusal(self):
        policy = (TEMPLATES / "AUTONOMY.md").read_text()
        self.assertIn("verification page is not an automatic stop", policy)
        self.assertIn("site and tool permit automated completion", policy)
        self.assertIn("human action is required or automation is prohibited", policy)
        self.assertIn("not permission to bypass", policy)


class ConfigAndCompletionTests(LoopFixture):
    def test_missing_features_rejected(self):
        (self.root / "features.json").unlink()
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_invalid_json_rejected(self):
        (self.root / "features.json").write_text("{")
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_empty_contract_rejected(self):
        (self.root / "features.json").write_text('{"features":[]}')
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_duplicate_ids_rejected(self):
        data = self.write_features(count=2)
        data["features"][1]["id"] = "F1"
        (self.root / "features.json").write_text(json.dumps(data))
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_non_boolean_passes_rejected(self):
        self.write_features(passes="false")
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_unfilled_verify_command_rejected(self):
        self.write_features(verify="{{command}}")
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_missing_gate_rejected(self):
        self.assertEqual(self.run_loop(gate=None).returncode, 4, self.output)
        self.assertEqual(self.turns(), 0)

    def test_missing_agent_rejected(self):
        self.assertEqual(self.run_loop(agent=False).returncode, 4, self.output)

    def test_missing_prompt_rejected(self):
        (self.root / "PROMPT.md").unlink()
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_false_done_is_not_completion(self):
        self.write_agent('print("DONE_ALL")')
        self.assertEqual(self.run_loop("--max-iterations", "1").returncode, 1, self.output)
        self.assertFalse(self.read_features()["features"][0]["passes"])

    def test_claimed_pass_needs_a_real_artifact(self):
        self.write_agent(COMPLETE.replace(
            'Path("artifact.txt").write_text("real fixture artifact")', ""
        ))
        self.assertEqual(self.run_loop().returncode, 5, self.output)
        self.assertFalse(self.read_features()["features"][0]["passes"])

    def test_full_gate_must_also_pass(self):
        self.write_agent(COMPLETE)
        self.assertEqual(
            self.run_loop(gate="test -f gate-ok.txt").returncode, 5, self.output
        )
        self.assertFalse(self.read_features()["features"][0]["passes"])

    def test_completion_does_not_require_a_marker(self):
        self.write_agent(COMPLETE.replace('print("DONE_ALL")', 'print("Work completed")'))
        self.assertEqual(self.run_loop().returncode, 0, self.output)
        feature = self.read_features()["features"][0]
        self.assertTrue(feature["passes"])
        self.assertIn("VERIFIED", feature["evidence"])
        receipts = json.loads((self.root / ".harness/evidence.json").read_text())
        self.assertTrue(any(r["label"] == "F1" and r["exit_code"] == 0 for r in receipts))
        self.assertTrue(any(r["label"] == "full verification gate" and r["exit_code"] == 0
                            for r in receipts))

    def test_existing_green_claim_is_rechecked(self):
        self.write_features(passes=True, evidence="old unverified claim")
        self.assertEqual(self.run_loop().returncode, 1, self.output)
        self.assertEqual(self.turns(), 0)
        self.assertFalse(self.read_features()["features"][0]["passes"])


class ContinuationTests(LoopFixture):
    def test_early_marker_continues_to_open_feature(self):
        self.write_agent(
            'if n == 1:\n    print("DONE_ALL")\n'
            "else:\n"
            '    assert "Still open in features.json: F1" in prompt\n'
            + textwrap.indent(textwrap.dedent(COMPLETE), "    ")
        )
        self.assertEqual(self.run_loop().returncode, 0, self.output)
        self.assertEqual(self.turns(), 2)

    def test_task_file_progress_without_commits(self):
        self.write_agent(
            'if n < 3:\n    Path(f"step-{n}.txt").write_text("useful fixture artifact")\n'
            '    print("Progress without a Git commit")\n'
            "else:\n" + textwrap.indent(textwrap.dedent(COMPLETE), "    ")
        )
        self.assertEqual(self.run_loop().returncode, 0, self.output)
        self.assertEqual(self.turns(), 3)
        self.assertFalse((self.root / ".git").exists())

    def test_feature_blocker_does_not_block_ready_work(self):
        data = self.write_features(count=2)
        data["features"][0]["blocked_reason"] = "Operator must provide a scope"
        (self.root / "features.json").write_text(json.dumps(data))
        self.write_agent(COMPLETE.replace('["features"][0]', '["features"][1]'))
        self.assertEqual(self.run_loop().returncode, 3, self.output)
        data = self.read_features()
        self.assertFalse(data["features"][0]["passes"])
        self.assertTrue(data["features"][1]["passes"])
        self.assertEqual(self.turns(), 1)

    def test_only_blocked_features_need_no_agent_call(self):
        self.write_features(blocked_reason="Operator decision needed")
        self.assertEqual(self.run_loop().returncode, 3, self.output)
        self.assertEqual(self.turns(), 0)

    def test_global_blocker_is_respected(self):
        self.write_agent('print("BLOCKED: no authorized access for any remaining work")')
        self.assertEqual(self.run_loop().returncode, 3, self.output)
        self.assertEqual(self.turns(), 1)

    def test_mid_line_blocked_word_does_not_stop(self):
        self.write_agent(
            'print("I would print BLOCKED: only if nothing could move")\n' + COMPLETE
        )
        self.assertEqual(self.run_loop().returncode, 0, self.output)


class GuardTests(LoopFixture):
    def test_two_no_progress_turns_stall(self):
        self.assertEqual(self.run_loop().returncode, 2, self.output)
        self.assertEqual(self.turns(), 2)

    def test_status_log_only_is_not_progress(self):
        self.write_agent(
            'with Path("progress.md").open("a") as stream:\n'
            '    stream.write("\\nAnother unverified status note\\n")\n'
            'print("Status only")'
        )
        self.assertEqual(self.run_loop().returncode, 2, self.output)
        self.assertEqual(self.turns(), 2)

    def test_iteration_cap_even_with_file_diffs(self):
        self.write_agent('Path(f"step-{n}.txt").write_text("fixture progress")')
        self.assertEqual(self.run_loop("--max-iterations", "3").returncode, 1, self.output)
        self.assertEqual(self.turns(), 3)

    def test_nonpositive_caps_rejected(self):
        for option, value in (("--max-iterations", "0"), ("--max-seconds", "-1"),
                              ("--step-timeout", "0")):
            with self.subTest(option=option):
                self.assertEqual(self.run_loop(option, value).returncode, 4, self.output)
        self.assertEqual(self.turns(), 0)

    def test_nonfinite_time_caps_rejected(self):
        for option, value in (("--max-seconds", "nan"), ("--max-seconds", "inf"),
                              ("--step-timeout", "inf")):
            with self.subTest(option=option, value=value):
                self.assertEqual(self.run_loop(option, value).returncode, 4, self.output)

    def test_agent_failure_gets_one_informed_retry(self):
        self.write_agent(
            'if n == 2:\n'
            '    assert "deliberate-fixture-error" in prompt\n'
            '    assert "<failure_output_data>" in prompt\n'
            '    Path(".harness/retry-saw-error").write_text("yes")\n'
            'print("deliberate-fixture-error")\nsys.exit(7)\n'
        )
        self.assertEqual(self.run_loop().returncode, 5, self.output)
        self.assertEqual(self.turns(), 2)
        self.assertTrue((self.root / ".harness/retry-saw-error").exists())

    def test_nonzero_agent_cannot_claim_done(self):
        self.write_agent(COMPLETE + "\nsys.exit(7)\n")
        self.assertEqual(self.run_loop().returncode, 5, self.output)
        self.assertFalse(self.read_features()["features"][0]["passes"])

    @unittest.skipUnless(os.name == "posix", "POSIX signal fixture")
    def test_step_timeout_stops_process(self):
        self.write_agent("import signal\nsignal.pause()\n")
        self.assertEqual(self.run_loop("--step-timeout", "0.15").returncode, 6, self.output)

    @unittest.skipUnless(os.name == "posix", "POSIX signal fixture")
    def test_total_deadline_stops_process(self):
        self.write_agent("import signal\nsignal.pause()\n")
        self.assertEqual(self.run_loop("--max-seconds", "0.15").returncode, 6, self.output)


class IntegrityAndStateTests(LoopFixture):
    def test_acceptance_cannot_be_changed(self):
        self.write_agent(
            'data["features"][0]["acceptance"] = "weakened acceptance"\n'
            'Path("features.json").write_text(json.dumps(data))'
        )
        self.assertEqual(self.run_loop().returncode, 4, self.output)
        self.assertIn("CHECK-INTEGRITY", self.output)

    def test_verify_command_cannot_be_changed(self):
        self.write_agent(
            'data["features"][0]["verify"] = "true"\n'
            'Path("features.json").write_text(json.dumps(data))'
        )
        self.assertEqual(self.run_loop().returncode, 4, self.output)

    def test_protected_gate_cannot_be_changed(self):
        gate = self.root / "verify.sh"
        gate.write_text("#!/bin/sh\nexit 0\n")
        gate.chmod(0o755)
        self.write_agent('Path("verify.sh").write_text("#!/bin/sh\\n# weakened\\nexit 0\\n")')
        self.assertEqual(self.run_loop(gate=None).returncode, 4, self.output)

    def test_protected_directory_includes_named_fixture_files(self):
        checks = self.root / "checks"
        checks.mkdir()
        (checks / "features.json").write_text('{"real_check":true}')
        self.write_agent(
            'Path("checks/features.json").write_text(\'{"real_check":false}\')'
        )
        self.assertEqual(self.run_loop("--protect", "checks").returncode, 4, self.output)

    def test_check_cannot_modify_feature_state(self):
        self.write_agent(COMPLETE)
        gate = (
            f"{shlex.quote(sys.executable)} -c "
            + shlex.quote(
                'import json; from pathlib import Path; p=Path("features.json"); '
                'd=json.loads(p.read_text()); d["features"][0]["evidence"]="tampered"; '
                'p.write_text(json.dumps(d))'
            )
        )
        self.assertEqual(self.run_loop(gate=gate).returncode, 4, self.output)

    def test_progress_rotates_verbatim_with_sha256(self):
        contents = b"verbatim-fixture-segment\n" * 3000
        (self.root / "progress.md").write_bytes(contents)
        self.write_agent(COMPLETE)
        self.assertEqual(self.run_loop().returncode, 0, self.output)
        segments = list((self.root / "archive").glob("progress-*.md"))
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].read_bytes(), contents)
        current = (self.root / "progress.md").read_text()
        self.assertIn(hashlib.sha256(contents).hexdigest(), current)

    def test_protected_path_cannot_escape_project(self):
        self.assertEqual(
            self.run_loop("--protect", str(self.root.parent / "outside-check")).returncode,
            4, self.output,
        )


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = self.root / "private-store"
        self.secret = ("fixture-only-" + self.root.name + "!").encode()

    def run_store(self, *arguments, input_value=None):
        result = subprocess.run(
            [sys.executable, str(STORE_SCRIPT), "--store", str(self.store), *arguments],
            input=input_value, capture_output=True, timeout=10, check=False,
        )
        self.output = result.stdout + result.stderr
        return result

    def test_roundtrip_and_private_modes(self):
        path = credentials.write_secret("portal_password", self.secret, self.store)
        self.assertEqual(stat.S_IMODE(self.store.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(credentials.read_secret("portal_password", self.store), self.secret)

    def test_put_check_and_list_never_print_the_value(self):
        self.assertEqual(
            self.run_store("put", "portal_password", "--stdin", input_value=self.secret).returncode,
            0, self.output,
        )
        self.assertNotIn(self.secret, self.output)
        self.assertEqual(self.run_store("check", "portal_password").returncode, 0)
        self.assertNotIn(self.secret, self.output)
        self.assertEqual(self.run_store("list").returncode, 0)
        self.assertIn(b"portal_password", self.output)
        self.assertNotIn(self.secret, self.output)

    def test_reject_store_inside_repository(self):
        (self.root / ".git").mkdir()
        with self.assertRaises(credentials.CredentialError):
            credentials.write_secret("portal_password", self.secret, self.store)

    def test_reject_store_inside_worktree(self):
        (self.root / ".git").write_text("gitdir: fixture-only")
        with self.assertRaises(credentials.CredentialError):
            credentials.write_secret("portal_password", self.secret, self.store)

    def test_loose_file_permissions_block_read(self):
        path = credentials.write_secret("portal_password", self.secret, self.store)
        path.chmod(0o644)
        with self.assertRaises(credentials.CredentialError):
            credentials.read_secret("portal_password", self.store)

    def test_loose_directory_permissions_block_read(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        self.store.chmod(0o755)
        with self.assertRaises(credentials.CredentialError):
            credentials.read_secret("portal_password", self.store)

    def test_symlinks_and_hardlinks_block_read(self):
        path = credentials.write_secret("portal_password", self.secret, self.store)
        link = self.store / "linked_password"
        link.symlink_to(path)
        with self.assertRaises(credentials.CredentialError):
            credentials.read_secret("linked_password", self.store)
        link.unlink()
        os.link(path, link)
        with self.assertRaises(credentials.CredentialError):
            credentials.read_secret("portal_password", self.store)

    def test_existing_alias_requires_explicit_rotation(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        with self.assertRaises(credentials.CredentialError):
            credentials.write_secret("portal_password", b"another-fixture", self.store)
        self.assertEqual(credentials.read_secret("portal_password", self.store), self.secret)
        credentials.write_secret(
            "portal_password", b"replacement-fixture", self.store, replace=True,
        )
        self.assertEqual(
            credentials.read_secret("portal_password", self.store), b"replacement-fixture",
        )

    def test_exec_injects_environment_and_redacts_both_streams(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        child = (
            'import os,sys; v=os.environ["FIXTURE_SECRET"]; '
            'assert all(v not in a for a in sys.argv); print(v); print(v,file=sys.stderr)'
        )
        result = self.run_store(
            "exec", "--map", "portal_password=FIXTURE_SECRET", "--",
            sys.executable, "-c", child,
        )
        self.assertEqual(result.returncode, 0, self.output)
        self.assertNotIn(self.secret, self.output)
        self.assertEqual(self.output.count(b"[REDACTED]"), 2)

    def test_encoded_outputs_are_redacted(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        child = (
            'import os,base64,urllib.parse; v=os.environ["FIXTURE_SECRET"]; '
            'print(base64.b64encode(v.encode()).decode()); '
            'print(urllib.parse.quote(v,safe=""))'
        )
        self.assertEqual(
            self.run_store(
                "exec", "--map", "portal_password=FIXTURE_SECRET", "--",
                sys.executable, "-c", child,
            ).returncode,
            0, self.output,
        )
        self.assertNotIn(self.secret, self.output)
        self.assertNotIn(base64.b64encode(self.secret), self.output)
        self.assertEqual(self.output.count(b"[REDACTED]"), 2)

    def test_invalid_names_empty_values_and_missing_credentials(self):
        for name in ("../password", "/absolute", "UPPERCASE", ""):
            with self.subTest(name=name), self.assertRaises(credentials.CredentialError):
                credentials.write_secret(name, self.secret, self.store)
        with self.assertRaises(credentials.CredentialError):
            credentials.write_secret("portal_password", b"", self.store)
        with self.assertRaises(credentials.CredentialError):
            credentials.read_secret("missing_password", self.store)

    def test_duplicate_environment_destinations_rejected(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        result = self.run_store(
            "exec", "--map", "portal_password=FIXTURE_SECRET",
            "--map", "portal_password=FIXTURE_SECRET", "--", sys.executable, "-c", "pass",
        )
        self.assertEqual(result.returncode, 2, self.output)
        self.assertNotIn(self.secret, self.output)

    def test_values_in_argv_rejected(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        result = self.run_store(
            "exec", "--map", "portal_password=FIXTURE_SECRET", "--",
            sys.executable, "-c", "pass", self.secret.decode(),
        )
        self.assertEqual(result.returncode, 2, self.output)
        self.assertNotIn(self.secret, self.output)

    def test_symlink_store_rejected(self):
        real_store = self.root / "real-store"
        real_store.mkdir(mode=0o700)
        self.store.symlink_to(real_store, target_is_directory=True)
        with self.assertRaises(credentials.CredentialError):
            credentials.write_secret("portal_password", self.secret, self.store)

    @unittest.skipUnless(os.name == "posix", "POSIX signal fixture")
    def test_exec_timeout_redacts_partial_output(self):
        credentials.write_secret("portal_password", self.secret, self.store)
        child = (
            'import os,signal; print(os.environ["FIXTURE_SECRET"],flush=True); '
            'signal.pause()'
        )
        result = self.run_store(
            "exec", "--timeout", "0.15", "--map", "portal_password=FIXTURE_SECRET",
            "--", sys.executable, "-c", child,
        )
        self.assertEqual(result.returncode, 2, self.output)
        self.assertNotIn(self.secret, self.output)
        self.assertIn(b"[REDACTED]", self.output)


class FakeField:
    def __init__(self, page, name):
        self.page = page
        self.name = name
        self.filled = None

    async def get_attribute(self, name):
        return self.page.password_type if name == "type" else None

    async def fill(self, value):
        if self.page.fail_fill and self.name == "#password":
            raise RuntimeError(f"fixture fill failure with {value}")
        self.filled = value
        if self.name == "#username" and self.page.redirect_on_username:
            self.page.url = "https://unapproved.example.test/login"

    async def is_visible(self):
        return self.page.signed_in


class FakePage:
    def __init__(self):
        self.url = "https://portal.example.test/login"
        self.password_type = "password"
        self.fail_fill = False
        self.redirect_on_username = False
        self.signed_in = False
        self.fields = {}

    def locator(self, selector):
        if selector not in self.fields:
            self.fields[selector] = FakeField(self, selector)
        return self.fields[selector]


class BrowserCredentialTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.store = Path(self.temporary.name) / "private-store"
        self.username = "fixture-account@example.test"
        self.password = "fixture-password-not-an-operator-secret!"
        credentials.write_secret("portal_username", self.username.encode(), self.store)
        credentials.write_secret("portal_password", self.password.encode(), self.store)
        self.page = FakePage()

    def fill(self, **overrides):
        arguments = {
            "authorized_origin": "https://portal.example.test",
            "username_alias": "portal_username", "password_alias": "portal_password",
            "username_selector": "#username", "password_selector": "#password",
            "store": self.store, **overrides,
        }
        return asyncio.run(browser_credentials.fill_saved_login(self.page, **arguments))

    def test_password_loaded_and_filled_only_inside_runtime(self):
        self.fill()
        self.assertEqual(self.page.fields["#username"].filled, self.username)
        self.assertEqual(self.page.fields["#password"].filled, self.password)

    def test_wrong_origin_does_not_even_read_credentials(self):
        self.page.url = "https://unapproved.example.test/login"
        with patch.object(browser_credentials, "read_secret") as read:
            with self.assertRaises(browser_credentials.BrowserCredentialError):
                self.fill()
            read.assert_not_called()

    def test_plain_http_rejected(self):
        self.page.url = "http://portal.example.test/login"
        with self.assertRaises(browser_credentials.BrowserCredentialError):
            self.fill()

    def test_non_password_input_rejected(self):
        self.page.password_type = "text"
        with self.assertRaises(browser_credentials.BrowserCredentialError):
            self.fill()
        self.assertIsNone(self.page.fields["#password"].filled)
        self.assertNotIn("#username", self.page.fields)

    def test_redirect_before_password_fill_rejected(self):
        self.page.redirect_on_username = True
        with self.assertRaises(browser_credentials.BrowserCredentialError):
            self.fill()
        self.assertIsNone(self.page.fields["#password"].filled)

    def test_fill_error_does_not_expose_password(self):
        self.page.fail_fill = True
        with self.assertRaises(browser_credentials.BrowserCredentialError) as caught:
            self.fill()
        self.assertNotIn(self.password, str(caught.exception))
        self.assertNotIn(self.username, str(caught.exception))
        self.assertIn("[REDACTED]", str(caught.exception))

    def test_encoded_password_in_error_is_redacted(self):
        error = RuntimeError(base64.b64encode(self.password.encode()).decode())
        result = browser_credentials.safe_error(error, [self.username, self.password])
        self.assertNotIn(base64.b64encode(self.password.encode()).decode(), result)
        self.assertIn("[REDACTED]", result)

    def test_login_claim_needs_positive_signed_in_evidence(self):
        self.assertFalse(asyncio.run(browser_credentials.confirm_signed_in(
            self.page, authorized_origin="https://portal.example.test", selector="#account",
        )))
        self.page.signed_in = True
        self.assertTrue(asyncio.run(browser_credentials.confirm_signed_in(
            self.page, authorized_origin="https://portal.example.test", selector="#account",
        )))
        with self.assertRaises(browser_credentials.BrowserCredentialError):
            asyncio.run(browser_credentials.confirm_signed_in(
                self.page, authorized_origin="https://portal.example.test", selector="",
            ))

    def test_missing_selector_is_not_guessed(self):
        with self.assertRaises(browser_credentials.BrowserCredentialError):
            self.fill(password_selector="")


class PackagingTests(unittest.TestCase):
    def test_pinned_provenance_and_license_present(self):
        source = json.loads((ROOT / "SOURCE.json").read_text())
        self.assertEqual(source["revision"], "3a4d707bdc7f72d622c5e4ea1976bee76be10d50")
        self.assertIn("not a git clone", source["source_method"])
        self.assertIn("MIT License", (ROOT / "LICENSE").read_text())

    def test_legacy_runner_and_upstream_tests_unchanged(self):
        manifest = json.loads((ROOT / "UPSTREAM_FILES.sha256.json").read_text())
        for name in ("templates/loop.sh", "tests/loop_selftest.sh",
                     "tests/harness_budget.sh", "LICENSE"):
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), manifest[name],
                )

    def test_lean_rules_and_stdlib_syntax(self):
        self.assertLessEqual(len((TEMPLATES / "AGENTS.md").read_text().splitlines()), 100)
        boot = sum((TEMPLATES / name).stat().st_size for name in (
            "AGENTS.md", "AUTONOMY.md", "PROMPT.md", "PROJECT.md", "features.json",
        ))
        self.assertLessEqual(boot, 32000)
        for name in ("autonomous_loop.py", "credential_store.py", "browser_credentials.py"):
            with self.subTest(name=name):
                ast.parse((TEMPLATES / name).read_text())

    def test_installation_and_simulation_scope_are_explicit(self):
        documentation = (ROOT / "docs/high-autonomy.md").read_text()
        for required in ("without overwriting", "not an encrypted vault",
                         "scripted fake agents", "remote CI", "mode 600",
                         "Browser login is explicitly supported"):
            with self.subTest(required=required):
                self.assertIn(required, documentation)

    def run_budget(self, large_file):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("AGENTS.md", "PROJECT.md", "features.json"):
                (root / name).write_text("small\n")
            (root / large_file).write_text("x" * 33000 + "\n")
            return subprocess.run(
                ["sh", str(TEMPLATES / "check_budget.sh")], cwd=root,
                capture_output=True, text=True, timeout=5, check=False,
            )

    def test_budget_counts_optional_autonomy_profile(self):
        result = self.run_budget("AUTONOMY.md")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_budget_counts_progress_tail(self):
        result = self.run_budget("progress.md")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
