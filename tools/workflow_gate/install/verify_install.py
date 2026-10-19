"""Read-only checks for the manual installation; changes nothing.

    /usr/bin/python3 -I tools/workflow_gate/install/verify_install.py policy FILE
    /usr/bin/python3 -I tools/workflow_gate/install/verify_install.py installed

`policy` checks a policy file before it is copied: valid shape, the expected
roles, and every enrolled path given by its real path and reported by Git as a
checkout top level with a commit (ordinary checkouts and linked worktrees).
`installed` checks /Library/BardWorkflowGate before any hook is registered: the
copies, including the reference copies of both hook configurations kept for
rollback in `installed/`, are byte-identical to this reviewed checkout, the policy is valid, and
every trusted file and parent is root-owned, not a symlink and not writable by
group or others. Exit 0 means every check passed.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry  # noqa: E402

INSTALL_DIR = "/Library/BardWorkflowGate"
SOURCES = {"entry.py": HERE / "entry.py", "gate.py": HERE.parent / "gate.py",
           "adapters/claude_code.py": HERE.parent / "adapters" / "claude_code.py",
           "adapters/codex.py": HERE.parent / "adapters" / "codex.py",
           "installed/claude-managed-settings.fragment.json": HERE / "claude-managed-settings.fragment.json",
           "installed/codex-requirements.toml": HERE / "codex-requirements.toml"}
ROLES = {"claude-code": "writer", "codex": "reviewer"}


def check_policy(path):
    roots, roles = entry.load_policy(path)
    if roles != ROLES:
        raise entry.Unprotected(f"roles must be {ROLES}")
    raw = json.loads(Path(path).read_text())["enrolled"]
    if not raw:
        raise entry.Unprotected("policy enrolls no checkout")
    for given, real in zip(raw, roots):
        if given != str(real):
            raise entry.Unprotected(f"enrolled path {given} is not its real path {real}")
        check_checkout(real)
    return raw


def check_checkout(path):
    """Git itself (fixed environment, as the hook entry runs it) must report `path` as a top level with a commit."""
    env = {**entry.STABLE_ENV, "HOME": os.environ.get("HOME", "/")}
    def git(*args):
        return subprocess.run(["/usr/bin/git", "-C", str(path), *args], capture_output=True, text=True, env=env)
    top = git("rev-parse", "--show-toplevel")
    if top.returncode or os.path.realpath(top.stdout.strip()) != str(path):
        raise entry.Unprotected(f"enrolled path {path} is not a Git top level")
    if git("rev-parse", "--verify", "--quiet", "HEAD^{commit}").returncode:
        raise entry.Unprotected(f"enrolled checkout {path} has no commit")


def check_installed(install_dir, owner_uid):
    install_dir = Path(install_dir)
    for relative, source in SOURCES.items():
        if (install_dir / relative).read_bytes() != source.read_bytes():
            raise entry.Unprotected(f"installed {relative} differs from the reviewed checkout")
    enrolled = check_policy(install_dir / "policy.json")
    for path in entry.trusted_files(install_dir) + [install_dir / relative for relative in SOURCES if relative.startswith("installed/")]:
        entry.verify_protected(path, owner_uid)
    evidence = install_dir / "approvals" / "evidence.json"
    if evidence.exists():
        json.loads(evidence.read_text())
    return enrolled


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only workflow gate installation checks.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("policy").add_argument("file")
    installed = sub.add_parser("installed")
    installed.add_argument("--install-dir", default=INSTALL_DIR)
    installed.add_argument("--test-owner-uid", type=int, default=entry.PROTECTED_UID, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.command == "policy":
            print("policy OK; enrolls " + ", ".join(check_policy(args.file)))
        else:
            enrolled = check_installed(args.install_dir, args.test_owner_uid)
            print(f"installed copy OK: matches this checkout, protected, enrolls {', '.join(enrolled)}")
        return 0
    except (OSError, ValueError, entry.Unprotected) as error:
        print(f"verify failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
