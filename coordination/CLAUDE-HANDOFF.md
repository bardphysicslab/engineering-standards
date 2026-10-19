# Claude handoff: workflow gate prototype

- **Milestone:** ENG-004 workflow gate prototype (WGP). NOT INSTALLED.
- **Owning issue:** [#19](https://github.com/bardphysicslab/engineering-standards/issues/19);
  [dated decision](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6275587422).
- **Branch:** `codex/workflow-gate-prototype` from task baseline `main` `aa84546`
  in the canonical checkout. The exact head is recorded in the pull request;
  this file does not embed its own hash.
- **Shared guidance:** bardphysicslab/engineering-standards@aa8454649fc2e8bb5ad50a5829f8d0cbda736442
- **Runtime targets:** Claude Code 2.1.284; Codex 0.163.0-alpha.10.2. Doc-derived;
  live compatibility unverified.
- **Review round:** Codex requested changes on `6f9207d`
  ([review](https://github.com/bardphysicslab/engineering-standards/pull/20#issuecomment-6275783364)):
  symlink-plus-`..` escape and incomplete covered mappings. Both are corrected
  here; the earlier handoff stays in history at that commit.
- **Roles:** Claude implemented (sole writer). Codex reviews the exact head
  independently; this handoff is not a self-certification. The maintainer decides merge.

## Behavior checked (tests, synthetic)

| Issue #19 criterion | Change | Evidence and outcome |
| --- | --- | --- |
| Demo: missing evidence denies; approved scope permits; changed source invalidates review | `tools/workflow_gate/demo.py` | `python3 tools/workflow_gate/demo.py`: 5/5 PASS (including out-of-scope deny and an uncommitted edit invalidating the receipt) |
| Missing, malformed or stale baseline and mapping | `gate.py` `check_evidence` | Tests: missing/malformed/wrong-schema evidence, missing, unknown and non-ancestor baseline, empty mapping, missing/conflicting items return questions, mapping changed after approval: all deny |
| Covered coverage is structurally complete (review fix) | `check_evidence`, `decide` | Adapter tests (Claude Write and Codex apply_patch): disposition not `accepted`, refs empty/`""`/`null`, blank plan, missing/blank/`..` files deny; an in-scope target not in any covered item's `files` denies. Structural only |
| Stale evidence | `check_evidence` | Tests: governing digest mismatch, expired approval, other checkout: deny |
| Unapproved scope | `decide` | Tests: out-of-scope Write and second apply_patch target deny |
| Traversal, symlinks, guard/settings tampering | `relative_target`, `guard_reason` | Tests: any `..` component denied before resolution, including the review's `src/link/../escaped.txt` via both adapters (no outside file created); absolute outside, symlink to `.claude/` and outside, `.claude/`, `.codex/`, nested `hooks.json`, `settings*.json`, `.git/`, gate files, evidence store, Move-to and Delete targets: deny with broad scope |
| Missing reviewer and self-review | `check_review`, `record-review` | Tests: empty reviewer, reviewer = writer (case-insensitive), changes-requested, receipt inside checkout: fail |
| Exact review includes dirty source | `review_state` | Tests: tracked dirty edit, untracked file, new commit each make the receipt stale |
| Real JSON stdin/stdout/exit adapter tests | `adapters/*.py`, `gate.run_hook` | 16 doc-derived fixtures run as subprocesses; allow = exit 0, no output; deny = exit 2 + JSON + stderr; malformed input, internal error and missing gate module deny |
| Shell, MCP, unknown, background | adapters | Bash, background Bash, exec_command, Codex Bash, MCP, WebFetch, web_search fixtures deny; Read allowed |
| Reuse the scaffold checker | `check-handoff` | Test: runs `scripts/check_workflow_docs.py`; clean = awaiting-review, dirty or failing checker = fail |
| Focused CI | `.github/workflows/workflow-docs.yml` | New step runs `test_workflow_gate.py`; CI result is on the pull request |

Local run at the branch head: `python3 -m unittest discover -s tests -p 'test_*.py'`
37 tests OK; scaffold checker passed (Python 3.9, Git 2.50). The new regressions
fail against the reviewed `gate.py` from `6f9207d` (10 failures) and pass with the fix.

## Architecture compliance (separate from behavior)

- ENG-004 shape: one read-only validator shared by two thin adapters; shell
  strings are not classified; JSON formats are prototype choices for review.
- No global or session hook, settings, permissions or security change; no
  application or Registry code; no merge or deployment.
- Decision index row added to the existing `docs/DECISIONS.md`; README pointer;
  no duplicate rulebook.
- Coverage report and unhooked paths: [guide](../tools/workflow_gate/README.md#coverage).

## Not verified or not covered

- No live hook run in either runtime; fixtures are doc-derived. MultiEdit has no fixture.
- The approval is a recorded premise: the evidence store is unprotected, the
  `source` URL is not checked on GitHub, identities and role are unauthenticated labels.
- Unhooked: already-running or external processes, Codex `write_stdin`, hosted
  tools, unmatched tools, hook timeout or kill handling, disabled hooks,
  outside edits, Git operations, ignored files.
- Semantic understanding of requirements is not checked; coverage checks are
  structural. `fnmatch` patterns let `*` match `/`.

## State

Committed and pushed on the branch; pull request open for review; not merged,
not installed, not deployed.

**Next action:** Codex re-reviews the exact pull-request head against issue #19
and the requested changes.
