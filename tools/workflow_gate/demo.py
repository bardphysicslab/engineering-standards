"""Synthetic demonstration of the workflow gate PROTOTYPE. NOT INSTALLED.

Builds a throwaway Git repository in a temporary directory and shows, through the
real Claude Code adapter subprocess and the review CLI:
1. an edit is denied while write evidence is missing;
2. an independently approved, in-scope edit is allowed (and an out-of-scope one denied);
3. a review receipt is invalidated when the reviewed source changes, even uncommitted.
The tests reuse the fixture helpers below.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate  # noqa: E402

ADAPTERS = {"claude-code": HERE / "adapters" / "claude_code.py", "codex": HERE / "adapters" / "codex.py"}
NOW = "2026-10-19T12:00:00Z"
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def run_git(root, *args):
    command = ["git", "-C", str(root), "-c", "user.name=Fixture writer", "-c", "user.email=writer@example.invalid", "-c", "commit.gpgsign=false", *args]
    return subprocess.run(command, check=True, capture_output=True, text=True, env=GIT_ENV).stdout.strip()


def make_repo(folder):
    """Synthetic checkout with a committed guidance file and one source file."""
    root = Path(folder).resolve() / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "src").mkdir()
    run_git(root, "init", "-q", "-b", "main")
    run_git(root, "remote", "add", "origin", "https://example.invalid/fixture.git")
    (root / "docs" / "guide.md").write_text("# Guide\n\nAccepted rule: greetings live in src/.\n")
    (root / "src" / "app.txt").write_text("hello\n")
    run_git(root, "add", ".")
    run_git(root, "commit", "-q", "-m", "baseline")
    return root, run_git(root, "rev-parse", "HEAD")


def make_evidence(root, base_commit, sign=True, **overrides):
    """Write evidence an independent approver would record; `sign` adds the approval digest."""
    evidence = {
        "schema": gate.EVIDENCE_SCHEMA,
        "repository": gate.observe(root),
        "baseline": base_commit,
        "governing": [{"name": "fixture-standards", "repo": str(root), "sha": base_commit,
                       "files": {"docs/guide.md": gate.sha256((root / "docs" / "guide.md").read_bytes())}}],
        "mapping": [{"id": "R1", "requirement": "Change the greeting", "status": "covered",
                     "disposition": "accepted as specified", "refs": ["docs/guide.md: accepted rule"]}],
        "scope": ["src/*"],
        "writer": "claude",
        "approval": {"approver": "codex", "source": "https://example.invalid/issues/1#accepted-plan",
                     "approved_at": "2026-10-19T00:00:00Z", "expires_at": "2026-10-20T00:00:00Z"},
    }
    evidence.update(overrides)
    if sign:
        evidence["approval"] = {**evidence["approval"], "digest": gate.approval_digest(evidence)}
    return evidence


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) if not isinstance(value, str) else value)
    return path


def hook(runtime, payload, env):
    """Run an adapter exactly as a hook would: JSON on stdin, decision on stdout/stderr/exit."""
    data = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(ADAPTERS[runtime])], input=data, capture_output=True, text=True, env=env)


def gate_env(store, role="writer"):
    env = {**GIT_ENV, "WORKFLOW_GATE_NOW": NOW, "WORKFLOW_GATE_EVIDENCE": str(store)}
    if role:
        env["WORKFLOW_GATE_ROLE"] = role
    return env


def claude_write(root, path):
    return {"session_id": "demo", "transcript_path": "/demo/transcript.jsonl", "cwd": str(root), "permission_mode": "default",
            "hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": str(path), "content": "hello, reviewed\n"},
            "tool_use_id": "toolu_demo"}


def cli(*args):
    return subprocess.run([sys.executable, str(HERE / "gate.py"), *args], capture_output=True, text=True, env=GIT_ENV)


def main():
    results = []
    with tempfile.TemporaryDirectory() as folder:
        root, baseline = make_repo(folder)
        store = Path(folder).resolve() / "store" / "evidence.json"
        env = gate_env(store)

        denied = hook("claude-code", claude_write(root, root / "src" / "app.txt"), env)
        results.append(("missing evidence denies the edit", denied.returncode == 2, denied.stderr.strip()))

        write_json(store, make_evidence(root, baseline))
        allowed = hook("claude-code", claude_write(root, root / "src" / "app.txt"), env)
        results.append(("approved in-scope edit is allowed", allowed.returncode == 0 and not allowed.stdout, "exit 0, no output"))
        outside = hook("claude-code", claude_write(root, root / "docs" / "guide.md"), env)
        results.append(("out-of-scope edit is denied", outside.returncode == 2, outside.stderr.strip()))

        (root / "src" / "app.txt").write_text("hello, reviewed\n")
        run_git(root, "commit", "-q", "-am", "approved edit")
        receipt = Path(folder).resolve() / "review.json"
        cli("record-review", "--cwd", str(root), "--baseline", baseline, "--reviewer", "codex", "--writer", "claude",
            "--verdict", "approved", "--out", str(receipt))
        fresh = cli("check-review", "--cwd", str(root), str(receipt))
        results.append(("review matches the exact reviewed state", fresh.returncode == 0, fresh.stdout.strip()))
        (root / "src" / "app.txt").write_text("hello, changed after review\n")
        stale = cli("check-review", "--cwd", str(root), str(receipt))
        results.append(("uncommitted source change invalidates the review", stale.returncode == 1, stale.stderr.strip()))

    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}\n      {detail}")
    print("Synthetic prototype demonstration only: NOT INSTALLED; no live hook was exercised.")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
