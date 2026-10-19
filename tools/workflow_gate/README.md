# Workflow gate prototype — NOT INSTALLED

A prototype of the coded gates decided in
[ENG-004](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6275587422)
([owning issue #19](https://github.com/bardphysicslab/engineering-standards/issues/19)).
Nothing here is registered as a hook, in any settings file or in any session.
It demonstrates code behavior only. It does not prove that an agent understood
the requirements, and it does not control every way a file can change.

Runtime targets: Claude Code 2.1.284 and Codex 0.163.0-alpha.10.2. The adapters
and fixtures were written from the published hook documentation, not captured
from a live session, so live compatibility is unverified.

## Files

| File | Role |
| --- | --- |
| `gate.py` | Shared read-only validator (`decide`) and CLI: `digest`, `record-review`, `check-review`, `check-handoff` |
| `adapters/claude_code.py`, `adapters/codex.py` | Thin PreToolUse adapters: JSON on stdin; allow = exit 0 with no output; deny = exit 2 with a reason on stderr and a `permissionDecision: deny` object on stdout |
| `demo.py` | Synthetic demonstration in a throwaway repository |
| `../../tests/test_workflow_gate.py` | Validator, adapter-subprocess and review tests; fixtures in `tests/fixtures/workflow_gate/` |

## Run

```bash
python3 tools/workflow_gate/demo.py
python3 -m unittest discover -s tests -p test_workflow_gate.py
```

The demo shows a denied edit (missing evidence), an allowed edit inside an
independently approved scope, a denied edit outside it, and a review receipt
invalidated by an uncommitted source change.

## Write evidence

An edit is allowed only when `WORKFLOW_GATE_ROLE=writer` and the evidence file
(`WORKFLOW_GATE_EVIDENCE`, default `<git common dir>/workflow-gate/evidence.json`)
passes every check against the checkout the tool is actually in:

- `schema` is `workflow-gate-evidence/1`; `repository` equals the observed
  top-level path, Git common directory and `origin` URL.
- `baseline` is a full commit SHA and an ancestor of `HEAD`.
- each `governing` entry names a repository, commit and SHA-256 digests of the
  governing files; digests are recomputed with `git show`.
- `mapping` lists every requirement as `covered`, `missing` or `conflicting`.
  A covered item needs `disposition: "accepted"`, nonblank string
  owner/interface/invariant/guidance `refs`, a nonblank `plan` and `files`
  patterns for the files it changes. Any missing or conflicting item denies
  coding and returns its `question` for Codex and Kornelis. These checks are
  structural only; they do not show the requirements were understood.
- `scope` lists repository-relative `fnmatch` patterns (`*` also matches `/`).
  Each target must match the scope and the `files` of a covered item.
- `approval` names an `approver` other than the `writer`, a `source` (for
  example the accepted issue entry), `approved_at`, `expires_at` and a `digest`
  (`gate.py digest <file>`) over the whole approved premise. Any later change
  to the mapping, scope, baseline, governing digests, writer or approval
  makes it stale.

Every target is resolved against the checkout. Any `..` component in the
target or the working directory is denied before resolution; so are paths
outside the checkout, any symlink on the path, an existing hard-linked file, and guard targets are denied even if the scope matches:
`.git/`, `.claude/`, `.codex/` at any depth, `hooks.json`, `settings*.json`,
`tools/workflow_gate/`, the gate's own directory and the evidence store.

The approval is a recorded premise, not a proof: the prototype cannot tell who
wrote the evidence file, does not verify the `source` on GitHub, and takes the
role from an unauthenticated environment variable.

## Review receipts

`record-review` binds a receipt (written outside the checkout) to the observed
repository, `HEAD`, tree, the diff from the baseline, and a digest of dirty
tracked and untracked source. `check-review` fails when any of these changed,
when the reviewer is missing or is the writer, or when the verdict is not
`approved`. Ignored files are not part of the digest. `check-handoff` runs the
repository's existing `scripts/check_workflow_docs.py` when present, then
reports `reviewed` (with a matching receipt) or `awaiting-review` (clean
source only; no review is claimed).

## Coverage

Fixture evidence means the adapter subprocess handled a doc-derived payload in
a test. No path has live runtime evidence.

| Path | Prototype behavior | Evidence |
| --- | --- | --- |
| Claude Code Write, Edit, NotebookEdit | Evidence, path and scope checks | Fixtures; live unverified |
| Claude Code MultiEdit | Same checks on `file_path` | Code only, no fixture; live unverified |
| Codex apply_patch | Every Add, Update, Delete and Move-to path checked | Fixtures; live unverified |
| Claude Code Read, Glob, Grep | Allowed | Read fixture; live unverified |
| Shell: Claude Code Bash (including `run_in_background`), Codex Bash, exec_command, shell | Denied without classifying the command | Fixtures; live unverified |
| MCP tools (`mcp__…`) | Denied | Fixtures; live unverified |
| Any other tool | Denied as unknown | Fixtures (WebFetch, web_search); live unverified |
| Hook input that is malformed, or a gate error or missing gate module | Denied (exit 2) | Tests |

Not controlled by the prototype:

- processes already running before or outside the hooked call: background
  shells, servers, watchers, editors, other terminals and other agents;
- Codex `write_stdin` into an existing process, which does not re-run
  PreToolUse, and hosted tools that do not reach local hooks;
- tools a hook matcher does not select, and the runtime's handling of a hook
  timeout or kill;
- disabled hooks, untrusted hook configuration, and settings or evidence
  edited from outside the session;
- Git operations, ignored files and anything outside the checkout;
- races: a symlink, hard link or file created or changed between the check and
  the write, by the tool itself or any other process, is not caught.

Denying shell makes the prototype impractical for real work by design.

## Before any installation

Installation is not authorized. It would need a protected policy, scripts and
approval store that the writer cannot change; managed hook configuration for
each runtime; negative live tests against the exact runtime versions; and a
separate accepted decision.
