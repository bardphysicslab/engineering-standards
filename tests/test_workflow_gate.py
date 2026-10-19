"""Workflow gate prototype: real adapter subprocesses on doc-derived fixtures, and review receipts."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
FIXTURES = SOURCE / "tests" / "fixtures" / "workflow_gate"
sys.path.insert(0, str(SOURCE / "tools" / "workflow_gate"))
import demo  # noqa: E402
import gate  # noqa: E402


class GateCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.tmp = Path(self.folder.name).resolve()
        self.root, self.baseline = demo.make_repo(self.tmp)
        self.store = self.tmp / "store" / "evidence.json"
        self.env = demo.gate_env(self.store)

    def evidence(self, **overrides):
        demo.write_json(self.store, demo.make_evidence(self.root, self.baseline, **overrides))

    def fixture(self, name):
        return (FIXTURES / name).read_text().replace("{REPO}", str(self.root))

    def run_hook(self, name, payload=None, env=None):
        return demo.hook(name.split("/")[0], payload if payload is not None else self.fixture(name), env or self.env)

    def assertAllowed(self, result):
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def assertDenied(self, result, text):
        self.assertEqual(result.returncode, 2, result.stderr)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(text, decision["permissionDecisionReason"])
        self.assertIn(text, result.stderr)

    def write_payload(self, path):
        payload = json.loads(self.fixture("claude-code/write.json"))
        payload["tool_input"]["file_path"] = str(path)
        return payload


class EvidenceTests(GateCase):
    def test_missing_evidence_denies(self):
        self.assertDenied(self.run_hook("claude-code/write.json"), "no write evidence")

    def test_default_store_is_inside_git_common_dir(self):
        env = {k: v for k, v in self.env.items() if k != "WORKFLOW_GATE_EVIDENCE"}
        self.assertDenied(self.run_hook("claude-code/write.json", env=env), "/.git/workflow-gate/evidence.json")

    def test_malformed_evidence_denies(self):
        demo.write_json(self.store, "{not json")
        self.assertDenied(self.run_hook("claude-code/write.json"), "malformed write evidence")

    def test_wrong_schema_denies(self):
        self.evidence(schema="other/1")
        self.assertDenied(self.run_hook("claude-code/write.json"), "evidence schema")

    def test_other_checkout_denies(self):
        repo = {**gate.observe(self.root), "toplevel": "/elsewhere"}
        self.evidence(repository=repo)
        self.assertDenied(self.run_hook("claude-code/write.json"), "another checkout")

    def test_stale_baseline_denies(self):
        demo.run_git(self.root, "switch", "-q", "-c", "side")
        demo.run_git(self.root, "commit", "-q", "--allow-empty", "-m", "side")
        side = demo.run_git(self.root, "rev-parse", "HEAD")
        demo.run_git(self.root, "switch", "-q", "main")
        self.evidence(baseline=side)
        self.assertDenied(self.run_hook("claude-code/write.json"), "stale baseline")

    def test_unknown_baseline_denies(self):
        self.evidence(baseline="0" * 40)
        self.assertDenied(self.run_hook("claude-code/write.json"), "is not a commit")

    def test_governing_digest_mismatch_denies(self):
        evidence = demo.make_evidence(self.root, self.baseline, sign=False)
        evidence["governing"][0]["files"]["docs/guide.md"] = "0" * 64
        self.evidence(governing=evidence["governing"])
        self.assertDenied(self.run_hook("claude-code/write.json"), "stale governing evidence")

    def test_missing_mapping_denies(self):
        self.evidence(mapping=[])
        self.assertDenied(self.run_hook("claude-code/write.json"), "requirements mapping is missing")

    def test_missing_and_conflicting_items_return_questions(self):
        mapping = [
            {"requirement": "Greeting text", "status": "covered", "disposition": "accepted", "refs": ["docs/guide.md"],
             "plan": "Edit src/app.txt", "files": ["src/app.txt"]},
            {"requirement": "Greeting language", "status": "missing", "question": "Which language is accepted?"},
            {"requirement": "Greeting owner", "status": "conflicting", "question": "Which owner wins?"},
        ]
        self.evidence(mapping=mapping)
        result = self.run_hook("claude-code/write.json")
        self.assertDenied(result, "questions for Codex and Kornelis")
        self.assertIn("[missing] Greeting language: Which language is accepted?", result.stderr)
        self.assertIn("[conflicting] Greeting owner: Which owner wins?", result.stderr)

    def test_missing_baseline_denies(self):
        evidence = demo.make_evidence(self.root, self.baseline, sign=False)
        del evidence["baseline"]
        evidence["approval"]["digest"] = gate.approval_digest(evidence)
        demo.write_json(self.store, evidence)
        self.assertDenied(self.run_hook("claude-code/write.json"), "evidence.baseline is missing")

    def test_incomplete_covered_items_deny(self):
        complete = {"requirement": "Greeting", "status": "covered", "disposition": "accepted",
                    "refs": ["docs/guide.md: accepted rule"], "plan": "Edit src/app.txt", "files": ["src/app.txt"]}
        cases = {
            "disposition rejected": ({"disposition": "rejected"}, "disposition is not accepted"),
            "no disposition": ({"disposition": None}, "disposition is not accepted"),
            "no refs": ({"refs": []}, "cites no owner"),
            "blank ref": ({"refs": [""]}, "cites no owner"),
            "null ref": ({"refs": [None]}, "cites no owner"),
            "no plan": ({"plan": " "}, ".plan is missing"),
            "no files": ({"files": []}, ".files must list"),
            "blank file": ({"files": [""]}, ".files must list"),
            "file traversal": ({"files": ["../src/app.txt"]}, ".files must list"),
        }
        for name, (change, reason) in cases.items():
            with self.subTest(name):
                self.evidence(mapping=[{**complete, **change}])
                for fixture in ["claude-code/write.json", "codex/apply_patch_update.json"]:
                    self.assertDenied(self.run_hook(fixture), reason)

    def test_target_must_map_to_a_covered_requirement(self):
        mapping = [{"requirement": "Greeting", "status": "covered", "disposition": "accepted",
                    "refs": ["docs/guide.md"], "plan": "Edit src/app.txt", "files": ["src/app.txt"]}]
        self.evidence(mapping=mapping)
        self.assertAllowed(self.run_hook("claude-code/write.json"))
        result = self.run_hook("claude-code/write.json", self.write_payload(self.root / "src" / "other.txt"))
        self.assertDenied(result, "src/other.txt is not mapped to any covered requirement")

    def test_mapping_changed_after_approval_denies(self):
        evidence = demo.make_evidence(self.root, self.baseline)
        evidence["scope"] = ["*"]
        demo.write_json(self.store, evidence)
        self.assertDenied(self.run_hook("claude-code/write.json"), "stale approval: the recorded premise changed")

    def test_expired_approval_denies(self):
        approval = {"approver": "codex", "source": "https://example.invalid/a", "approved_at": "2026-10-18T00:00:00Z", "expires_at": "2026-10-19T00:00:00Z"}
        self.evidence(approval=approval)
        self.assertDenied(self.run_hook("claude-code/write.json"), "stale approval: valid")

    def test_self_approval_and_missing_approver_deny(self):
        self.evidence(approval={"approver": "Claude", "source": "x", "approved_at": "2026-10-19T00:00:00Z", "expires_at": "2026-10-20T00:00:00Z"})
        self.assertDenied(self.run_hook("claude-code/write.json"), "approver is the writer")
        self.evidence(approval={"source": "x", "approved_at": "2026-10-19T00:00:00Z", "expires_at": "2026-10-20T00:00:00Z"})
        self.assertDenied(self.run_hook("claude-code/write.json"), "approval.approver is missing")


class PathTests(GateCase):
    def test_scoped_edits_allowed_for_each_write_tool(self):
        self.evidence()
        for name in ["claude-code/write.json", "claude-code/edit.json", "claude-code/notebook_edit.json", "codex/apply_patch_update.json"]:
            with self.subTest(name):
                self.assertAllowed(self.run_hook(name))

    def test_unapproved_scope_denies(self):
        self.evidence()
        self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(self.root / "docs" / "guide.md")), "outside the approved scope")

    def test_every_patch_target_is_checked(self):
        self.evidence()
        self.assertDenied(self.run_hook("codex/apply_patch_add_two.json"), "docs/new.md is outside the approved scope")

    def test_traversal_and_outside_paths_deny(self):
        self.evidence(scope=["*"])
        for target in [f"{self.root}/src/../../escape.txt", "../escape.txt", "src/../src/app.txt"]:
            with self.subTest(target):
                self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(target)), "parent traversal")
        self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(self.tmp / "escape.txt")), "outside the checkout")

    def test_parent_traversal_through_symlink_cannot_escape(self):
        # Review regression: normalizing src/link/../x hid the symlink, while the OS resolves link first.
        self.evidence()
        outside = self.tmp / "outside" / "deep"
        outside.mkdir(parents=True)
        (self.root / "src" / "link").symlink_to(outside, target_is_directory=True)
        patch = json.loads(self.fixture("codex/apply_patch_update.json"))
        patch["tool_input"]["command"] = "*** Begin Patch\n*** Add File: src/link/../escaped.txt\n+escaped\n*** End Patch\n"
        self.assertDenied(self.run_hook("codex/x", patch), "parent traversal")
        self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(f"{self.root}/src/link/../escaped.txt")), "parent traversal")
        self.assertFalse((self.tmp / "outside" / "escaped.txt").exists())

    def test_symlink_aliases_deny(self):
        self.evidence(scope=["*"])
        (self.root / "src" / "settings_link").symlink_to(self.root / ".claude", target_is_directory=True)
        (self.root / "src" / "out").symlink_to(self.tmp)
        for target in [self.root / "src" / "settings_link" / "settings.json", self.root / "src" / "out" / "escape.txt"]:
            with self.subTest(str(target)):
                self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(target)), "passes through symlink")

    def test_hard_linked_target_denies(self):
        # Review regression: an in-scope path hard-linked to guard settings shares its inode.
        self.evidence()
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir()
        settings.write_text("{}\n")
        (self.root / "src" / "app.txt").unlink()
        os.link(settings, self.root / "src" / "app.txt")
        for fixture in ["claude-code/write.json", "claude-code/edit.json", "codex/apply_patch_update.json"]:
            with self.subTest(fixture):
                self.assertDenied(self.run_hook(fixture), "hard-linked file")
        self.assertEqual(settings.read_text(), "{}\n")

    def test_guard_and_settings_targets_deny_even_with_broad_scope(self):
        self.evidence(scope=["*"])
        targets = {".claude/settings.json": ".claude/", ".codex/config.toml": ".codex/", "sub/.claude/hooks.json": ".claude/",
                   "hooks.json": "hook or settings", "app/settings.local.json": "hook or settings", ".git/config": ".git/",
                   "tools/workflow_gate/gate.py": "workflow gate itself"}
        for target, reason in targets.items():
            with self.subTest(target):
                self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(self.root / target)), reason)
        self.assertDenied(self.run_hook("codex/apply_patch_move_to_guard.json"), ".codex/")
        self.assertDenied(self.run_hook("codex/apply_patch_delete_gate.json"), "workflow gate itself")

    def test_evidence_store_inside_checkout_is_protected(self):
        self.store = self.root / "src" / "evidence.json"
        self.env = demo.gate_env(self.store)
        self.evidence()
        self.assertDenied(self.run_hook("claude-code/write.json", self.write_payload(self.store)), "evidence store is protected")


class ToolAndRoleTests(GateCase):
    def test_read_is_allowed_without_evidence(self):
        self.assertAllowed(self.run_hook("claude-code/read.json"))

    def test_shell_mcp_and_unknown_tools_deny_even_with_evidence(self):
        self.evidence(scope=["*"])
        cases = {"claude-code/bash.json": "shell", "claude-code/bash_background.json": "background-process",
                 "claude-code/mcp.json": "MCP", "claude-code/unknown.json": "unknown tool",
                 "codex/exec_command.json": "shell", "codex/bash.json": "shell", "codex/mcp.json": "MCP", "codex/unknown.json": "unknown tool"}
        for name, reason in cases.items():
            with self.subTest(name):
                self.assertDenied(self.run_hook(name), reason)

    def test_reviewer_and_missing_role_deny_writes(self):
        self.evidence()
        self.assertDenied(self.run_hook("claude-code/write.json", env=demo.gate_env(self.store, role="reviewer")), "reviewer role")
        self.assertDenied(self.run_hook("claude-code/write.json", env=demo.gate_env(self.store, role=None)), "must be writer")

    def test_malformed_hook_input_denies(self):
        for payload in ["", "not json", "[]", json.dumps({"hook_event_name": "PreToolUse", "cwd": str(self.root)})]:
            with self.subTest(payload):
                self.assertDenied(self.run_hook("claude-code/write.json", payload), "denied")
        broken = json.loads(self.fixture("codex/apply_patch_update.json"))
        broken["tool_input"]["command"] = "*** Update File: src/app.txt"
        self.assertDenied(self.run_hook("codex/x", broken), "not a complete patch")

    def test_internal_error_fails_closed(self):
        self.store.mkdir(parents=True)  # evidence path is a directory
        self.assertDenied(self.run_hook("claude-code/write.json"), "malformed write evidence")
        self.store.rmdir()
        payload = json.loads(self.fixture("claude-code/write.json"))
        payload["tool_input"]["file_path"] = 7
        self.evidence()
        self.assertDenied(self.run_hook("claude-code/write.json", payload), "denied")

    def test_adapter_without_gate_fails_closed(self):
        copy = self.tmp / "isolated" / "adapters" / "claude_code.py"
        copy.parent.mkdir(parents=True)
        shutil.copyfile(demo.ADAPTERS["claude-code"], copy)
        result = subprocess.run([sys.executable, str(copy)], input=self.fixture("claude-code/write.json"), capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("gate unavailable", result.stderr)


class ReviewTests(GateCase):
    def setUp(self):
        super().setUp()
        (self.root / "src" / "app.txt").write_text("hello, reviewed\n")
        demo.run_git(self.root, "commit", "-q", "-am", "edit")
        self.receipt = self.tmp / "review.json"

    def record(self, reviewer="codex", writer="claude", verdict="approved", out=None):
        return demo.cli("record-review", "--cwd", str(self.root), "--baseline", self.baseline, "--reviewer", reviewer,
                        "--writer", writer, "--verdict", verdict, "--out", str(out or self.receipt))

    def check(self):
        return demo.cli("check-review", "--cwd", str(self.root), str(self.receipt))

    def test_exact_review_matches_then_changes_invalidate(self):
        self.assertEqual(self.record().returncode, 0)
        self.assertEqual(self.check().returncode, 0)
        changes = {
            "worktree_sha256": lambda: (self.root / "src" / "app.txt").write_text("tracked dirty edit\n"),
            "untracked": lambda: (self.root / "src" / "new.txt").write_text("untracked\n"),
            "head": lambda: demo.run_git(self.root, "commit", "-q", "--allow-empty", "-m", "later"),
        }
        for name, change in changes.items():
            with self.subTest(name):
                demo.run_git(self.root, "reset", "-q", "--hard")
                demo.run_git(self.root, "clean", "-qfd", "src")
                self.assertEqual(self.record().returncode, 0)
                change()
                result = self.check()
                self.assertEqual(result.returncode, 1)
                self.assertIn("stale review", result.stderr)

    def test_missing_reviewer_and_self_review_fail(self):
        self.assertEqual(self.record().returncode, 0)
        receipt = json.loads(self.receipt.read_text())
        receipt["reviewer"] = ""
        demo.write_json(self.receipt, receipt)
        self.assertIn("names no reviewer", self.check().stderr)
        receipt["reviewer"] = "claude"
        demo.write_json(self.receipt, receipt)
        self.assertIn("self-review", self.check().stderr)
        self.assertIn("self-review", self.record(reviewer="Claude").stderr)

    def test_changes_requested_and_receipt_inside_checkout_fail(self):
        self.record(verdict="changes-requested")
        self.assertIn("not approved", self.check().stderr)
        self.assertIn("outside the checkout", self.record(out=self.root / "review.json").stderr)

    def test_handoff_awaiting_review_requires_clean_source_and_reuses_checker(self):
        for relative in ["scripts/check_workflow_docs.py", ".github/ISSUE_TEMPLATE/work_item.md", ".github/pull_request_template.md"]:
            demo.write_json(self.root / relative, (SOURCE / relative).read_text())
        demo.write_json(self.root / "docs" / "DECISIONS.md", "# Decisions\nhttps://github.com/example/example\n")
        demo.run_git(self.root, "add", ".")
        demo.run_git(self.root, "commit", "-q", "-m", "scaffold")
        clean = demo.cli("check-handoff", "--cwd", str(self.root))
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertIn("Workflow scaffold and local-link checks passed", clean.stdout)
        self.assertIn("status: awaiting-review", clean.stdout)
        (self.root / "src" / "app.txt").write_text("dirty\n")
        self.assertIn("handoff source is dirty", demo.cli("check-handoff", "--cwd", str(self.root)).stderr)
        (self.root / "src" / "app.txt").write_text("hello, reviewed\n")
        (self.root / ".github" / "pull_request_template.md").unlink()
        self.assertIn("scaffold checker failed", demo.cli("check-handoff", "--cwd", str(self.root)).stderr)


class DemoTest(unittest.TestCase):
    def test_demo_passes(self):
        result = subprocess.run([sys.executable, str(SOURCE / "tools" / "workflow_gate" / "demo.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
