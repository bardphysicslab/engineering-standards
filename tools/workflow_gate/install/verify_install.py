"""Read-only checks for the manual installation; changes nothing.

    /usr/bin/python3 -I tools/workflow_gate/install/verify_install.py policy FILE
    /usr/bin/python3 -I tools/workflow_gate/install/verify_install.py installed

`policy` checks a policy file before it is copied: valid shape, the expected
roles, and every enrolled path an existing Git top level given by its real path.
`installed` checks /Library/BardWorkflowGate before any hook is registered: the
copies are byte-identical to this reviewed checkout, the policy is valid, and
every trusted file and parent is root-owned, not a symlink and not writable by
group or others. Exit 0 means every check passed.
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import entry  # noqa: E402

INSTALL_DIR = "/Library/BardWorkflowGate"
SOURCES = {"entry.py": HERE / "entry.py", "gate.py": HERE.parent / "gate.py",
           "adapters/claude_code.py": HERE.parent / "adapters" / "claude_code.py",
           "adapters/codex.py": HERE.parent / "adapters" / "codex.py"}
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
        if not (real / ".git").exists():
            raise entry.Unprotected(f"enrolled path {real} is not a Git top level")
    return raw


def check_installed(install_dir, owner_uid):
    install_dir = Path(install_dir)
    for relative, source in SOURCES.items():
        if (install_dir / relative).read_bytes() != source.read_bytes():
            raise entry.Unprotected(f"installed {relative} differs from the reviewed checkout")
    enrolled = check_policy(install_dir / "policy.json")
    for path in entry.trusted_files(install_dir):
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
