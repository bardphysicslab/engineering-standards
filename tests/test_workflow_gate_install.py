"""Installation package: protected entry behavior in a disposable install directory, and config proposals.

The entry runs as a real subprocess with JSON on stdin. Tests pass the current
user as the protected owner because they cannot create root-owned files; the
installed entry requires root (uid 0).
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
GATE = SOURCE / "tools" / "workflow_gate"
INSTALL = GATE / "install"
FIXTURES = SOURCE / "tests" / "fixtures" / "workflow_gate"
sys.path.insert(0, str(GATE))
import demo  # noqa: E402
import gate  # noqa: E402

HARNESS = "import sys; sys.path.insert(0, sys.argv[1]); import entry; sys.exit(entry.main([sys.argv[2]], owner_uid=int(sys.argv[3]), install_dir=sys.argv[1]))"


def real_time_approval(hours_from=-1, hours_to=8):
    now = dt.datetime.now(dt.timezone.utc)
    return {"approver": "codex", "source": "https://example.invalid/issues/1#accepted-plan",
            "approved_at": (now + dt.timedelta(hours=hours_from)).isoformat(),
            "expires_at": (now + dt.timedelta(hours=hours_to)).isoformat()}


class EntryCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name).resolve()
        self.root, self.baseline = demo.make_repo(self.tmp)
        self.install = self.tmp / "BardWorkflowGate"
        (self.install / "adapters").mkdir(parents=True)
        (self.install / "approvals").mkdir()
        shutil.copyfile(INSTALL / "entry.py", self.install / "entry.py")
        shutil.copyfile(GATE / "gate.py", self.install / "gate.py")
        for name in ["claude_code.py", "codex.py"]:
            shutil.copyfile(GATE / "adapters" / name, self.install / "adapters" / name)
        self.policy({"schema": "workflow-gate-policy/1", "enrolled": [str(self.root)],
                     "roles": {"claude-code": "writer", "codex": "reviewer"}})
        self.store = self.install / "approvals" / "evidence.json"
        for path in [self.install, self.install / "adapters", self.install / "approvals", *self.install.rglob("*.py")]:
            os.chmod(path, 0o755 if path.is_dir() else 0o644)

    def policy(self, value):
        demo.write_json(self.install / "policy.json", value)
        os.chmod(self.install / "policy.json", 0o644)

    def approve(self, **overrides):
        overrides.setdefault("approval", real_time_approval())
        demo.write_json(self.store, demo.make_evidence(self.root, self.baseline, **overrides))
        os.chmod(self.store, 0o644)

    def payload(self, name, cwd=None, **tool_input):
        payload = json.loads((FIXTURES / name).read_text().replace("{REPO}", str(self.root)))
        if cwd:
            payload["cwd"] = str(cwd)
        payload["tool_input"].update(tool_input)
        return payload

    def entry(self, runtime, payload, owner=None, env=None):
        command = [sys.executable, "-I", "-c", HARNESS, str(self.install), runtime, str(os.getuid() if owner is None else owner)]
        base = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", "/")}
        data = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(command, input=data, capture_output=True, text=True, env={**base, **(env or {})})

    def assertAllowed(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def assertDenied(self, result, text):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn(text, result.stderr)


class EntryTests(EntryCase):
    def test_missing_evidence_denies_and_approved_scoped_edit_is_allowed(self):
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json")), "no write evidence")
        self.approve()
        self.assertAllowed(self.entry("claude-code", self.payload("claude-code/write.json")))
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json", file_path=str(self.root / "docs" / "guide.md"))),
                          "outside the approved scope")

    def test_codex_is_reviewer_by_policy(self):
        self.approve()
        self.assertDenied(self.entry("codex", self.payload("codex/apply_patch_update.json")), "reviewer role")

    def test_writer_environment_cannot_choose_role_store_or_clock(self):
        writer_store = self.tmp / "writer" / "evidence.json"
        demo.write_json(writer_store, demo.make_evidence(self.root, self.baseline, approval=real_time_approval()))
        env = {"WORKFLOW_GATE_ROLE": "writer", "WORKFLOW_GATE_EVIDENCE": str(writer_store), "WORKFLOW_GATE_NOW": dt.datetime.now(dt.timezone.utc).isoformat()}
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json"), env=env), "no write evidence")
        self.approve()
        self.assertDenied(self.entry("codex", self.payload("codex/apply_patch_update.json"), env=env), "reviewer role")
        self.approve(approval=real_time_approval(-48, -24))
        env["WORKFLOW_GATE_NOW"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=36)).isoformat()
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json"), env=env), "stale approval")

    def test_bad_evidence_denies(self):
        cases = {
            "conflicting": ({"mapping": [{"requirement": "Owner", "status": "conflicting", "question": "Which owner?"}]}, "questions for Codex and Kornelis"),
            "missing coverage": ({"mapping": []}, "requirements mapping is missing"),
            "self-approval": ({"approval": {**real_time_approval(), "approver": "claude"}}, "approver is the writer"),
            "expired": ({"approval": real_time_approval(-48, -24)}, "stale approval"),
        }
        for name, (overrides, reason) in cases.items():
            with self.subTest(name):
                self.approve(**overrides)
                self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json")), reason)
        demo.write_json(self.store, "{broken")
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json")), "malformed write evidence")

    def test_guard_targets_and_unsupported_tools_deny_in_enrolled_checkout(self):
        self.approve(scope=["*"])
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json", file_path=str(self.root / ".claude" / "settings.json"))), ".claude/")
        for name, reason in {"claude-code/bash.json": "shell", "claude-code/bash_background.json": "shell", "claude-code/mcp.json": "MCP",
                             "claude-code/unknown.json": "unknown tool", "codex/exec_command.json": "shell", "codex/mcp.json": "MCP"}.items():
            with self.subTest(name):
                self.assertDenied(self.entry(name.split("/")[0], self.payload(name)), reason)
        self.assertAllowed(self.entry("claude-code", self.payload("claude-code/read.json")))

    def test_unenrolled_sessions_pass_through_but_enrolled_targets_are_checked(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        self.assertAllowed(self.entry("claude-code", self.payload("claude-code/bash.json", cwd=elsewhere)))  # known gap: unenrolled shell
        result = self.entry("claude-code", self.payload("claude-code/write.json", cwd=elsewhere))
        self.assertDenied(result, "denied")
        patch = self.payload("codex/apply_patch_update.json", cwd=elsewhere, command="not a patch")
        self.assertDenied(self.entry("codex", patch), "not a complete patch")


class ProtectionTests(EntryCase):
    def test_user_owned_install_is_not_trusted_as_root(self):
        self.approve()
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json"), owner=0), "not owned by the protected owner")

    def test_writable_symlinked_or_malformed_install_denies(self):
        self.approve()
        os.chmod(self.install / "policy.json", 0o664)
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/read.json")), "writable by group or others")
        os.chmod(self.install / "policy.json", 0o644)
        os.chmod(self.store, 0o666)
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json")), "writable by group or others")
        os.chmod(self.store, 0o644)
        self.store.unlink()
        self.store.symlink_to(self.tmp / "writer.json")
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/write.json")), "is a symlink")
        self.store.unlink()
        self.policy({"schema": "workflow-gate-policy/1", "enrolled": ["relative/path"], "roles": {}})
        self.assertDenied(self.entry("claude-code", self.payload("claude-code/read.json")), "policy.json is malformed")

    def test_bad_runtime_argument_and_input_deny(self):
        self.assertDenied(self.entry("other", self.payload("claude-code/read.json")), "exactly one runtime argument")
        self.assertDenied(self.entry("claude-code", "not json"), "denied")


class LiveFixtureTests(EntryCase):
    def test_generated_drafts_behave_as_labelled(self):
        folder = self.tmp / "live"
        made = subprocess.run([sys.executable, str(INSTALL / "live_fixture.py"), str(folder)], capture_output=True, text=True, env=demo.GIT_ENV)
        self.assertEqual(made.returncode, 0, made.stderr)
        repo = Path(json.loads(made.stdout)["enroll"])
        self.root = repo
        self.assertEqual(json.loads((folder / "policy.json").read_text())["enrolled"], [str(repo)])
        shutil.copyfile(folder / "policy.json", self.install / "policy.json")  # the runbook's copy step, minus sudo
        os.chmod(self.install / "policy.json", 0o644)
        expected = {"valid.json": None, "self-approved.json": "approver is the writer", "expired.json": "stale approval",
                    "conflicting.json": "questions for Codex and Kornelis", "malformed.json": "malformed write evidence"}
        for draft, reason in expected.items():
            with self.subTest(draft):
                shutil.copyfile(folder / "drafts" / draft, self.store)
                os.chmod(self.store, 0o644)
                result = self.entry("claude-code", self.payload("claude-code/write.json"))
                self.assertAllowed(result) if reason is None else self.assertDenied(result, reason)


class VerifyInstallTests(EntryCase):
    def verify(self, *args):
        return subprocess.run([sys.executable, "-I", str(INSTALL / "verify_install.py"), *args], capture_output=True, text=True)

    def test_policy_check_accepts_fixture_policy_and_rejects_placeholders(self):
        folder = self.tmp / "live"
        subprocess.run([sys.executable, str(INSTALL / "live_fixture.py"), str(folder)], check=True, capture_output=True, env=demo.GIT_ENV)
        good = self.verify("policy", str(folder / "policy.json"))
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn(str(folder.resolve() / "repo"), good.stdout)
        cases = {"ENROLL": "malformed", "/absolute/path/to/disposable/fixture/repo": "not a Git top level", str(self.tmp / "repo" / "src"): "not a Git top level"}
        for enrolled, reason in cases.items():
            with self.subTest(enrolled):
                demo.write_json(self.tmp / "bad.json", {"schema": "workflow-gate-policy/1", "enrolled": [enrolled], "roles": {"claude-code": "writer", "codex": "reviewer"}})
                result = self.verify("policy", str(self.tmp / "bad.json"))
                self.assertEqual(result.returncode, 1)
                self.assertIn(reason, result.stderr)
        self.assertEqual(self.verify("policy", str(self.policy_for(self.root))).returncode, 0)

    def policy_for(self, path):
        demo.write_json(self.tmp / "policy-check.json", {"schema": "workflow-gate-policy/1", "enrolled": [str(path)],
                                                         "roles": {"claude-code": "writer", "codex": "reviewer"}})
        return self.tmp / "policy-check.json"

    def test_policy_check_asks_git_not_the_dot_git_entry(self):
        cases = {}
        bad_file = self.tmp / "bad-file"
        bad_file.mkdir()
        (bad_file / ".git").write_text("not a gitdir\n")
        cases[bad_file] = "not a Git top level"
        bad_dir = self.tmp / "bad-dir"
        (bad_dir / ".git").mkdir(parents=True)
        cases[bad_dir] = "not a Git top level"
        nested = self.root / "src" / "nested"
        (nested / ".git").mkdir(parents=True)
        cases[nested] = "not a Git top level"  # Git reports the enclosing checkout
        empty = self.tmp / "empty"
        empty.mkdir()
        demo.run_git(empty, "init", "-q")
        cases[empty] = "has no commit"
        for path, reason in cases.items():
            with self.subTest(path.name):
                result = self.verify("policy", str(self.policy_for(path)))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(reason, result.stderr)
        worktree = self.tmp / "linked"
        demo.run_git(self.root, "worktree", "add", "-q", "-b", "linked", str(worktree))
        self.assertTrue((worktree / ".git").is_file())
        result = self.verify("policy", str(self.policy_for(worktree.resolve())))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_roles_policy(self):
        demo.write_json(self.tmp / "roles.json", {"schema": "workflow-gate-policy/1", "enrolled": [str(self.root)], "roles": {"claude-code": "writer", "codex": "writer"}})
        self.assertIn("roles must be", self.verify("policy", str(self.tmp / "roles.json")).stderr)

    def test_installed_check_requires_identical_protected_copies(self):
        (self.install / "installed").mkdir()
        for name in ["claude-managed-settings.fragment.json", "codex-requirements.toml"]:
            shutil.copyfile(INSTALL / name, self.install / "installed" / name)
            os.chmod(self.install / "installed" / name, 0o644)
        os.chmod(self.install / "installed", 0o755)
        args = ["installed", "--install-dir", str(self.install), "--test-owner-uid", str(os.getuid())]
        ok = self.verify(*args)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("not owned by the protected owner", self.verify("installed", "--install-dir", str(self.install)).stderr)
        with open(self.install / "gate.py", "a") as handle:
            handle.write("\n# changed\n")
        self.assertIn("gate.py differs", self.verify(*args).stderr)


class RollbackTests(unittest.TestCase):
    """Runs the runbook's rollback commands against a disposable prefix (sudo removed, paths redirected)."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name).resolve()
        self.prefix = self.tmp / "system"
        gate_dir = self.prefix / "Library" / "BardWorkflowGate"
        for relative, source in {"entry.py": INSTALL / "entry.py", "gate.py": GATE / "gate.py",
                                 "adapters/claude_code.py": GATE / "adapters" / "claude_code.py", "adapters/codex.py": GATE / "adapters" / "codex.py",
                                 "installed/claude-managed-settings.fragment.json": INSTALL / "claude-managed-settings.fragment.json",
                                 "installed/codex-requirements.toml": INSTALL / "codex-requirements.toml",
                                 "policy.json": INSTALL / "policy.example.json"}.items():
            (gate_dir / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, gate_dir / relative)
        (gate_dir / "approvals").mkdir()
        self.claude = self.prefix / "Library" / "Application Support" / "ClaudeCode" / "managed-settings.json"
        self.codex = self.prefix / "etc" / "codex" / "requirements.toml"
        for target, name in [(self.claude, "claude-managed-settings.fragment.json"), (self.codex, "codex-requirements.toml")]:
            target.parent.mkdir(parents=True)
            shutil.copyfile(gate_dir / "installed" / name, target)  # activation installs from the reference copy
        # A later, unrelated edit to the development sources: rollback must not depend on them.
        self.work = self.tmp / "checkout"
        for name in ["claude-managed-settings.fragment.json", "codex-requirements.toml"]:
            changed = self.work / "tools" / "workflow_gate" / "install" / name
            changed.parent.mkdir(parents=True, exist_ok=True)
            changed.write_text((INSTALL / name).read_text() + "\n# later edit\n")

    def commands(self):
        section = (INSTALL / "README.md").read_text().split("## Rollback", 1)[1].split("\n## ", 1)[0]
        blocks = [block.split("```", 1)[0].strip() for block in section.split("```bash\n")[1:]]
        lines = [line for line in blocks if line != "sudo -k"]
        self.assertEqual(len(lines), 3)
        return [line.replace("sudo ", "").replace("/Library/", f"{self.prefix}/Library/").replace("/etc/codex", f"{self.prefix}/etc/codex")
                for line in lines]

    def run_line(self, line):
        return subprocess.run(["/bin/bash", "-c", line], cwd=self.work, capture_output=True, text=True)

    def test_rollback_removes_unchanged_install_even_after_source_edits(self):
        for line in self.commands():
            self.assertEqual(self.run_line(line).returncode, 0, line)
        self.assertEqual(sorted(str(p.relative_to(self.prefix)) for p in self.prefix.rglob("*")),
                         ["Library", "Library/Application Support", "etc"])

    def test_rollback_refuses_settings_changed_after_installation(self):
        self.claude.write_text(self.claude.read_text().replace('"timeout": 30', '"timeout": 30, "note": "added later"'))
        claude_line, codex_line, gate_line = self.commands()
        self.assertNotEqual(self.run_line(claude_line).returncode, 0)
        self.assertIn("added later", self.claude.read_text())
        self.assertEqual(self.run_line(codex_line).returncode, 0)
        self.assertNotEqual(self.run_line(gate_line).returncode, 0)  # gate files stay while a policy file remains
        self.assertTrue((self.prefix / "Library" / "BardWorkflowGate" / "installed" / "claude-managed-settings.fragment.json").exists())


class RunbookTests(unittest.TestCase):
    def test_runbook_is_new_install_only_with_guarded_rollback(self):
        text = (INSTALL / "README.md").read_text()
        self.assertNotIn("merge the one hook", text)
        self.assertNotIn("ENROLL#", text)
        self.assertIn("verify_install.py installed", text)
        self.assertNotIn("picks it up when the file appears", text)  # observed: needed a full Desktop restart
        self.assertIn("If C1 is not denied, stop", text)
        removals = [line for line in text.splitlines()
                    if any(part.strip().startswith("sudo rm ") and ("ClaudeCode/managed-settings.json" in part or "/etc/codex/requirements.toml" in part) for part in line.split("&&"))]
        self.assertTrue(removals)
        for line in removals:
            self.assertTrue(line.lstrip().startswith("cmp -s /Library/BardWorkflowGate/installed/"), line)


class ConfigProposalTests(unittest.TestCase):
    def test_both_runtimes_call_the_isolated_protected_entry(self):
        claude = json.loads((INSTALL / "claude-managed-settings.fragment.json").read_text())
        hook = claude["hooks"]["PreToolUse"][0]
        self.assertEqual(hook["matcher"], "*")
        self.assertEqual(hook["hooks"][0]["command"], "/usr/bin/python3 -I /Library/BardWorkflowGate/entry.py claude-code")
        self.assertEqual(set(claude), {"hooks"})  # no permission, sandbox or other policy keys
        codex = (INSTALL / "codex-requirements.toml").read_text()
        self.assertIn('command = "/usr/bin/python3 -I /Library/BardWorkflowGate/entry.py codex"', codex)
        self.assertIn('managed_dir = "/Library/BardWorkflowGate"', codex)
        self.assertNotIn("allow_managed_hooks_only", codex)
        example = json.loads((INSTALL / "policy.example.json").read_text())
        self.assertEqual(example["roles"], {"claude-code": "writer", "codex": "reviewer"})


if __name__ == "__main__":
    unittest.main()
