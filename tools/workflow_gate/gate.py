"""Workflow gate PROTOTYPE: shared read-only validator for the hook adapters. NOT INSTALLED.

`decide` answers one question: may this tool request proceed, given locally
recorded evidence and the observed Git state? It never writes repository files;
only `record-review` writes, and only to a receipt path outside the checkout.
Every error denies. The evidence store is not protected in this prototype, so an
approval record states the independently controlled premise; it does not prove it.
"""
import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

EVIDENCE_SCHEMA = "workflow-gate-evidence/1"
RECEIPT_SCHEMA = "workflow-gate-review/1"
GATE_DIR = Path(__file__).resolve().parent
READ_ONLY_TOOLS = {"Read", "Glob", "Grep"}
GUARD_DIRS = {".git", ".claude", ".codex"}
STATUSES = {"covered", "missing", "conflicting"}
SHA = re.compile(r"^[0-9a-f]{40}$")
QUESTION_TO = "Codex and Kornelis"


class Denied(Exception):
    """A request, evidence record or review receipt fails a gate rule."""


def git(root, *args, binary=False):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        message = result.stderr.decode(errors="replace").strip()[:200]
        raise Denied(f"git {' '.join(args)} failed: {message}")
    return result.stdout if binary else result.stdout.decode().strip()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def now(env):
    return parse_time(env["WORKFLOW_GATE_NOW"], "WORKFLOW_GATE_NOW") if env.get("WORKFLOW_GATE_NOW") else dt.datetime.now(dt.timezone.utc)


def parse_time(value, field):
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise Denied(f"{field} is not an ISO 8601 time")
    if parsed.tzinfo is None:
        raise Denied(f"{field} has no time zone")
    return parsed


def observe(cwd):
    """Identity of the checkout actually containing `cwd`, computed from Git."""
    top = Path(git(cwd, "rev-parse", "--show-toplevel")).resolve()
    common = Path(git(top, "rev-parse", "--path-format=absolute", "--git-common-dir")).resolve()
    remote = subprocess.run(["git", "-C", str(top), "remote", "get-url", "origin"], capture_output=True, text=True)
    return {"toplevel": str(top), "git_common_dir": str(common), "remote": remote.stdout.strip()}


def evidence_path(repo, env):
    configured = env.get("WORKFLOW_GATE_EVIDENCE")
    return Path(configured) if configured else Path(repo["git_common_dir"]) / "workflow-gate" / "evidence.json"


def load_json(path, what):
    try:
        with open(path) as handle:
            value = json.load(handle)
    except FileNotFoundError:
        raise Denied(f"no {what} at {path}")
    except (OSError, ValueError) as error:
        raise Denied(f"malformed {what} at {path}: {error}")
    if not isinstance(value, dict):
        raise Denied(f"malformed {what}: top level is not an object")
    return value


def approval_digest(evidence):
    """Digest an approver records; any later change to the approved premise makes it stale."""
    bound = {key: evidence.get(key) for key in ("schema", "repository", "baseline", "governing", "mapping", "scope", "writer")}
    bound["approval"] = {k: v for k, v in (evidence.get("approval") or {}).items() if k != "digest"}
    return sha256(json.dumps(bound, sort_keys=True, separators=(",", ":")).encode())


def text_field(container, key, where):
    value = container.get(key) if isinstance(container, dict) else None
    if not isinstance(value, str) or not value.strip():
        raise Denied(f"{where}.{key} is missing")
    return value


def check_evidence(evidence, repo, at):
    if evidence.get("schema") != EVIDENCE_SCHEMA:
        raise Denied(f"evidence schema is not {EVIDENCE_SCHEMA}")
    if evidence.get("repository") != repo:
        raise Denied(f"evidence is bound to another checkout or remote; observed {json.dumps(repo, sort_keys=True)}")
    top = repo["toplevel"]

    baseline = text_field(evidence, "baseline", "evidence")
    if not SHA.match(baseline) or subprocess.run(["git", "-C", top, "cat-file", "-e", baseline + "^{commit}"], capture_output=True).returncode:
        raise Denied(f"baseline {baseline} is not a commit in this checkout")
    if subprocess.run(["git", "-C", top, "merge-base", "--is-ancestor", baseline, "HEAD"], capture_output=True).returncode:
        raise Denied(f"stale baseline: {baseline} is not an ancestor of HEAD")

    governing = evidence.get("governing")
    if not isinstance(governing, list) or not governing:
        raise Denied("evidence.governing is missing")
    for source in governing:
        name = text_field(source, "name", "governing")
        commit = text_field(source, "sha", f"governing[{name}]")
        files = source.get("files")
        if not SHA.match(commit) or not isinstance(files, dict) or not files:
            raise Denied(f"governing[{name}] needs a full commit SHA and file digests")
        for relative, digest in files.items():
            content = git(text_field(source, "repo", f"governing[{name}]"), "show", f"{commit}:{relative}", binary=True)
            if sha256(content) != digest:
                raise Denied(f"stale governing evidence: {name}@{commit[:12]}:{relative} digest differs")

    mapping = evidence.get("mapping")
    if not isinstance(mapping, list) or not mapping:
        raise Denied("requirements mapping is missing; coding is blocked until it is recorded and accepted")
    questions, covered = [], []
    for index, item in enumerate(mapping):
        requirement = text_field(item, "requirement", f"mapping[{index}]")
        status = item.get("status")
        if status not in STATUSES:
            raise Denied(f"mapping[{index}] status must be covered, missing or conflicting")
        if status == "covered":
            if item.get("disposition") != "accepted":
                raise Denied(f"mapping[{index}] is covered but its disposition is not accepted")
            refs = item.get("refs")
            if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref.strip() for ref in refs):
                raise Denied(f"mapping[{index}] is covered but cites no owner/interface/invariant/guidance reference")
            text_field(item, "plan", f"mapping[{index}]")
            if not patterns(item.get("files")):
                raise Denied(f"mapping[{index}].files must list the repository-relative files this requirement changes")
            covered.append(item)
        else:
            questions.append(f"[{status}] {requirement}: {text_field(item, 'question', f'mapping[{index}]')}")
    if questions:
        raise Denied(f"coding is blocked; questions for {QUESTION_TO}: " + " | ".join(questions))

    scope = evidence.get("scope")
    if not patterns(scope):
        raise Denied("evidence.scope must list repository-relative patterns")

    writer = text_field(evidence, "writer", "evidence")
    approval = evidence.get("approval")
    approver = text_field(approval, "approver", "approval")
    text_field(approval, "source", "approval")
    if approver.strip().casefold() == writer.strip().casefold():
        raise Denied("approval is not independent: approver is the writer")
    if approval.get("digest") != approval_digest(evidence):
        raise Denied("stale approval: the recorded premise changed after approval")
    approved_at = parse_time(approval.get("approved_at"), "approval.approved_at")
    expires_at = parse_time(approval.get("expires_at"), "approval.expires_at")
    if not approved_at <= at < expires_at:
        raise Denied(f"stale approval: valid {approved_at.isoformat()} to {expires_at.isoformat()}, now {at.isoformat()}")
    return scope, covered


def patterns(value):
    """True for a non-empty list of repository-relative fnmatch patterns."""
    return isinstance(value, list) and bool(value) and all(
        isinstance(p, str) and p.strip() and not p.startswith("/") and ".." not in p.split("/") for p in value)


def relative_target(target, cwd, repo):
    """Repository-relative path for `target`; denies traversal and symlink aliases."""
    if not isinstance(target, str) or not target:
        raise Denied("write target path is missing")
    if ".." in Path(target).parts or ".." in Path(cwd).parts:
        raise Denied(f"{target} uses parent traversal (..), which is denied before path resolution")
    top = Path(repo["toplevel"])
    path = Path(os.path.normpath(Path(cwd) / target))
    roots = [top]
    cwd_real = Path(cwd).resolve()
    if cwd_real == top or top in cwd_real.parents:  # the lexical spelling of the checkout seen by the tool
        depth = len(cwd_real.relative_to(top).parts)
        lexical = Path(os.path.normpath(cwd))
        roots.append(lexical.parents[depth - 1] if depth else lexical)
    for root in roots:
        try:
            rel = path.relative_to(root)
            break
        except ValueError:
            continue
    else:
        raise Denied(f"{target} is outside the checkout")
    if not rel.parts:
        raise Denied(f"{target} is the checkout itself")
    current = top
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise Denied(f"{target} passes through symlink {current.relative_to(top).as_posix()}")
    real = (top / rel).resolve()
    if real == top or top not in real.parents:
        raise Denied(f"{target} resolves outside the checkout")
    return rel


def guard_reason(rel, top, evidence_file):
    real = (top / rel).resolve()
    name = rel.parts[-1]
    guarded = [part for part in rel.parts if part in GUARD_DIRS]
    if guarded:
        return f"{guarded[0]}/ is guard or settings state"
    if name == "hooks.json" or fnmatch.fnmatchcase(name, "settings*.json"):
        return f"{name} is hook or settings configuration"
    if rel.as_posix().startswith("tools/workflow_gate/") or real == GATE_DIR or GATE_DIR in real.parents:
        return "the workflow gate itself is protected"
    store = evidence_file.resolve()
    if real == store or real == store.parent or store.parent in real.parents:
        return "the evidence store is protected"
    return None


def decide(kind, targets, cwd, env):
    """Return None to allow, or raise Denied. `kind` is read, write, shell, mcp or unknown."""
    if kind == "read":
        return None
    if kind == "shell":
        raise Denied("shell and background-process requests are denied; the gate does not classify shell strings")
    if kind == "mcp":
        raise Denied("MCP tools are denied by the prototype")
    if kind != "write":
        raise Denied("unknown tool; only known file-edit tools can be scope-checked")
    role = env.get("WORKFLOW_GATE_ROLE")
    if role == "reviewer":
        raise Denied("reviewer role does not write")
    if role != "writer":
        raise Denied("WORKFLOW_GATE_ROLE must be writer for edits")
    repo = observe(cwd)
    store = evidence_path(repo, env)
    scope, covered = check_evidence(load_json(store, "write evidence"), repo, now(env))
    if not targets:
        raise Denied("edit names no target path")
    top = Path(repo["toplevel"])
    for target in targets:
        rel = relative_target(target, cwd, repo)
        reason = guard_reason(rel, top, store)
        if reason:
            raise Denied(f"{rel.as_posix()}: {reason}")
        if not any(fnmatch.fnmatchcase(rel.as_posix(), pattern) for pattern in scope):
            raise Denied(f"{rel.as_posix()} is outside the approved scope")
        if not any(fnmatch.fnmatchcase(rel.as_posix(), pattern) for item in covered for pattern in item["files"]):
            raise Denied(f"{rel.as_posix()} is not mapped to any covered requirement")
    return None


def run_hook(classify, runtime, env=None):
    """Shared adapter body: JSON on stdin; allow is exit 0 with no output; deny is exit 2."""
    env = os.environ if env is None else env
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict) or payload.get("hook_event_name") != "PreToolUse":
            raise Denied("input is not a PreToolUse hook payload")
        if not isinstance(payload.get("cwd"), str) or not isinstance(payload.get("tool_name"), str) or not isinstance(payload.get("tool_input"), dict):
            raise Denied("hook payload lacks cwd, tool_name or tool_input")
        kind, targets = classify(payload["tool_name"], payload["tool_input"])
        decide(kind, targets, payload["cwd"], env)
        return 0
    except Exception as error:  # fail closed on every error, not only rule violations
        reason = str(error) if isinstance(error, Denied) else f"gate error ({type(error).__name__}: {error})"
        deny(f"workflow gate prototype ({runtime}) denied: {reason}")
        return 2


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    print(reason, file=sys.stderr)


def review_state(cwd, baseline):
    """Exact review subject: HEAD, tree, diff from baseline, and dirty tracked and untracked source."""
    repo = observe(cwd)
    top = repo["toplevel"]
    status = git(top, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True)
    dirty = hashlib.sha256(status)
    dirty.update(git(top, "diff", "--binary", "HEAD", binary=True))
    entries = status.split(b"\0")
    for entry in entries:
        if entry.startswith(b"?? "):
            path = Path(top) / entry[3:].decode()
            dirty.update(entry[3:] + b"\0")
            dirty.update(os.readlink(path).encode() if path.is_symlink() else path.read_bytes())
    return {
        "repository": repo,
        "baseline": baseline,
        "head": git(top, "rev-parse", "HEAD"),
        "tree": git(top, "rev-parse", "HEAD^{tree}"),
        "diff_sha256": sha256(git(top, "diff", "--binary", f"{baseline}..HEAD", binary=True)),
        "worktree_sha256": dirty.hexdigest(),
        "clean": not status,
    }


def check_review(receipt, cwd):
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise Denied(f"review receipt schema is not {RECEIPT_SCHEMA}")
    reviewer = receipt.get("reviewer")
    writer = text_field(receipt, "writer", "receipt")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise Denied("review receipt names no reviewer")
    if reviewer.strip().casefold() == writer.strip().casefold():
        raise Denied("self-review: reviewer is the writer")
    current = review_state(cwd, text_field(receipt, "baseline", "receipt"))
    for key in ("repository", "head", "tree", "diff_sha256", "worktree_sha256"):
        if receipt.get(key) != current[key]:
            raise Denied(f"stale review: {key} changed since review")
    if receipt.get("verdict") != "approved":
        raise Denied(f"review verdict is {receipt.get('verdict')!r}, not approved")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Workflow gate prototype CLI (NOT INSTALLED).")
    sub = parser.add_subparsers(dest="command", required=True)
    digest = sub.add_parser("digest", help="print the approval digest of an evidence file")
    digest.add_argument("evidence")
    record = sub.add_parser("record-review", help="record a review receipt for the exact current state")
    record.add_argument("--cwd", default=".")
    record.add_argument("--baseline", required=True)
    record.add_argument("--reviewer", required=True)
    record.add_argument("--writer", required=True)
    record.add_argument("--verdict", choices=["approved", "changes-requested"], required=True)
    record.add_argument("--out", required=True)
    check = sub.add_parser("check-review", help="verify a receipt still matches the current state")
    check.add_argument("--cwd", default=".")
    check.add_argument("receipt")
    handoff = sub.add_parser("check-handoff", help="scaffold checker plus awaiting-review or reviewed status")
    handoff.add_argument("--cwd", default=".")
    handoff.add_argument("--baseline")
    handoff.add_argument("--receipt")
    args = parser.parse_args(argv)
    try:
        if args.command == "digest":
            print(approval_digest(load_json(args.evidence, "evidence")))
        elif args.command == "record-review":
            state = review_state(args.cwd, args.baseline)
            out = Path(args.out).resolve()
            top = Path(state["repository"]["toplevel"])
            if out == top or top in out.parents:
                raise Denied("write the receipt outside the checkout; inside it would change the reviewed source")
            if args.reviewer.strip().casefold() == args.writer.strip().casefold():
                raise Denied("self-review: reviewer is the writer")
            state.pop("clean")
            receipt = {"schema": RECEIPT_SCHEMA, **state, "reviewer": args.reviewer, "writer": args.writer,
                       "verdict": args.verdict, "reviewed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
            out.write_text(json.dumps(receipt, indent=2) + "\n")
            print(f"review receipt recorded for {state['head'][:12]}")
        elif args.command == "check-review":
            check_review(load_json(args.receipt, "review receipt"), args.cwd)
            print("review receipt matches the exact current state")
        else:
            top = Path(observe(args.cwd)["toplevel"])
            checker = top / "scripts" / "check_workflow_docs.py"
            if checker.is_file():
                result = subprocess.run([sys.executable, str(checker)], capture_output=True, text=True)
                if result.returncode:
                    raise Denied("scaffold checker failed: " + (result.stdout + result.stderr).strip())
                print(result.stdout.strip())
            else:
                print("scaffold checker: not present in this repository")
            if args.receipt:
                check_review(load_json(args.receipt, "review receipt"), args.cwd)
                print("status: reviewed (exact state matches receipt)")
            else:
                if not review_state(args.cwd, git(top, "rev-parse", "HEAD"))["clean"]:
                    raise Denied("handoff source is dirty; commit or remove changes before awaiting review")
                print("status: awaiting-review (clean; no review is claimed)")
        return 0
    except Denied as error:
        print(f"workflow gate: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
