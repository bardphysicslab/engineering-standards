"""Protected hook entry for the workflow gate (installation package, NOT INSTALLED).

Runs as `/usr/bin/python3 -I <install dir>/entry.py claude-code|codex` from managed
hook configuration. Unlike the bare prototype adapters, the writer cannot choose
the role, clock, evidence file or gate code: the role comes from the protected
policy, the clock is the system clock, the evidence file is the protected store,
and the code is loaded only from the install directory. Every file it trusts and
every parent directory must be owned by the protected owner (root when installed)
and not writable by group or others. Any error denies.

Sessions whose working directory and write targets are all outside the enrolled
checkouts pass through unchanged; enforcement applies only to enrolled checkouts.
"""
import io
import json
import os
import stat
import sys
from pathlib import Path

PROTECTED_UID = 0
RUNTIMES = {"claude-code": ("claude_code", "Claude Code 2.1.284, installed entry"),
            "codex": ("codex", "Codex 0.163.0-alpha.10.2, installed entry")}
POLICY_SCHEMA = "workflow-gate-policy/1"
STABLE_ENV = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "core.fsmonitor",
    "GIT_CONFIG_VALUE_0": "false",
    "GIT_CONFIG_KEY_1": "core.hooksPath",
    "GIT_CONFIG_VALUE_1": "/dev/null",
}


class Unprotected(Exception):
    pass


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    print(reason, file=sys.stderr)
    return 2


def verify_protected(path, owner_uid):
    """`path` and every parent: not a symlink, owned by `owner_uid` or root, not group/other
    writable (a root-owned sticky parent such as /tmp is accepted, as in common secure-path checks)."""
    path = Path(path)
    for current in [path, *path.parents]:
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode):
            raise Unprotected(f"{current} is a symlink")
        if info.st_uid not in (owner_uid, 0):
            raise Unprotected(f"{current} is not owned by the protected owner")
        sticky_root_parent = current != path and info.st_uid == 0 and info.st_mode & stat.S_ISVTX
        if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH) and not sticky_root_parent:
            raise Unprotected(f"{current} is writable by group or others")


def trusted_files(install_dir):
    files = [install_dir / "entry.py", install_dir / "gate.py", install_dir / "policy.json",
             install_dir / "adapters" / "claude_code.py", install_dir / "adapters" / "codex.py",
             install_dir / "approvals"]
    evidence = install_dir / "approvals" / "evidence.json"
    return files + ([evidence] if os.path.lexists(evidence) else [])


def load_policy(policy_file):
    with open(policy_file) as handle:
        policy = json.load(handle)
    enrolled = policy.get("enrolled") if isinstance(policy, dict) else None
    roles = policy.get("roles") if isinstance(policy, dict) else None
    if policy.get("schema") != POLICY_SCHEMA or not isinstance(enrolled, list) or not all(isinstance(p, str) and os.path.isabs(p) for p in enrolled):
        raise Unprotected("policy.json is malformed")
    if not isinstance(roles, dict) or not set(roles.values()) <= {"writer", "reviewer"}:
        raise Unprotected("policy.json roles are malformed")
    return [Path(os.path.realpath(p)) for p in enrolled], roles


def inside(path, roots):
    return any(path == root or root in path.parents for root in roots)


def enrolled_request(payload, kind, targets, roots):
    """True when the session directory or any write target is inside an enrolled checkout."""
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or inside(Path(os.path.realpath(cwd)), roots):
        return True
    for target in targets:
        if not isinstance(target, str):
            return True
        joined = os.path.join(cwd, target)
        if inside(Path(os.path.normpath(joined)), roots) or inside(Path(os.path.realpath(joined)), roots):
            return True
    return False


def main(argv=None, owner_uid=PROTECTED_UID, install_dir=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        install_dir = Path(install_dir or os.path.dirname(os.path.abspath(__file__)))
        if len(argv) != 1 or argv[0] not in RUNTIMES:
            raise Unprotected("entry needs exactly one runtime argument: claude-code or codex")
        module_name, runtime = RUNTIMES[argv[0]]
        for path in trusted_files(install_dir):
            verify_protected(path, owner_uid)
        roots, roles = load_policy(install_dir / "policy.json")
        role = roles.get(argv[0])
        home = os.environ.get("HOME", "/")
        os.environ.clear()
        os.environ.update(STABLE_ENV, HOME=home)
        sys.path[:0] = [str(install_dir), str(install_dir / "adapters")]
        import gate
        adapter = __import__(module_name)
        data = sys.stdin.read()
        payload = json.loads(data)
        if not isinstance(payload, dict) or not isinstance(payload.get("tool_name"), str) or not isinstance(payload.get("tool_input"), dict):
            raise Unprotected("hook payload lacks tool_name or tool_input")
        try:
            kind, targets = adapter.classify(payload["tool_name"], payload["tool_input"])
            enrolled = enrolled_request(payload, kind, targets, roots)
        except gate.Denied:
            enrolled = True  # unparseable edit targets cannot be shown to be outside enrolled checkouts
        if not enrolled:
            return 0
        sys.stdin = io.StringIO(data)
        env = {"WORKFLOW_GATE_EVIDENCE": str(install_dir / "approvals" / "evidence.json")}
        if role:
            env["WORKFLOW_GATE_ROLE"] = role
        return gate.run_hook(adapter.classify, runtime, env=env)
    except Exception as error:  # fail closed, including protection and policy failures
        return deny(f"workflow gate entry denied: {error}")


if __name__ == "__main__":
    sys.exit(main())
