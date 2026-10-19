# Workflow hardening continuation

Authoritative tracker: [workflow hardening](https://github.com/bardphysicslab/engineering-standards/issues/15),
on the existing BardBox Template project board. GitHub owns current status; the
dated checkpoint below is historical, not a claim about the current review or
merge stage. Read the latest linked issue checkpoint before resuming.

## October 18, 2026 — authored checkpoint

- Baseline/shared guidance: `5271f1424165b5bfa25c40e4b41e3161bd0fc6aa`.
- Canonical checkout: engineering-standards, owner Codex in the originating
  workflow discussion; branch `codex/workflow-evidence`. Exact feature revision
  and PR are recorded in the linked issue/PR (this tracked file does not embed its
  own impossible-to-stabilize commit hash).
- Scope: evidence-based architecture/acceptance review, decision indexes and
  stable references, coherent coordination/cleanup, reusable forms, diagram
  lifecycle and proportional cold handover. No runtime/service/access changes.
- Companion owners: BardBox owns platform decision index/links; template consumes
  shared form source and owns implementation-specific decision pointers only.
- Template changes are remote-only from published main: its canonical checkout
  has unrelated unpublished hardware work and is untouched.
- Verification: source diffs, table/link checks and focused template/checker
  validation. Independent review pending; no deployed/physical evidence needed or
  claimed for documentation. Per-head results belong in the PR.
- Preservation: feature branch pushed to GitHub at handoff (off-machine); current
  branch/commit and check results are verified and recorded in the issue comment.
- Next owner/action: independent reviewer checks the exact PR heads and performs
  a read-only cold handover, then maintainer decides merge. No merge authorization
  is inferred from implementation approval.
- Adoption gaps: existing consumers are not mass-migrated; operational successor
  ownership/access is not audited or changed; automated enforcement is a small
  completeness check, not proof of design correctness.

## October 19, 2026 — module organization and checkout synchronization (ENG-003)

- Tracker: [engineering-standards#17](https://github.com/bardphysicslab/engineering-standards/issues/17);
  decision [ENG-003](https://github.com/bardphysicslab/engineering-standards/issues/17#issuecomment-6269649466).
  Platform companion: BardBox milestone OCT19-DOCS-1 in
  [bardbox#31](https://github.com/bardphysicslab/bardbox/issues/31).
- Baseline/shared guidance: `2cb958318b5b603b2b250c351425212e10a64fed`.
- Canonical checkout: engineering-standards, branch `codex/module-checkout-guidance`;
  implementer Claude (sole writer), reviewer Codex. Exact head and PR are recorded
  in the PR and the issue.
- Scope: `checkouts-and-worktrees.md` rule 12 (idle definition, fast-forward
  only, deployments separate, extra clones need a role, mirrors deferred);
  `agent-practice.md` module organization, smallest safe slices and scope-first
  review; ENG-003 index row. Rule numbers 1 to 11 are unchanged.
- Consumer and skill impact: consumers already link these files; no copies to
  update. The BardBox repository-layout standard links ENG-003 for its platform
  module names. Coordination skills that describe checkout cleanup should be
  checked for drift after merge; none are changed here.
- Verification: workflow checker and its unit test; independent review pending.
  No automation, host access, cleanup, merge or deployment.
- Next owner/action: Codex reviews the exact head; maintainer decides merge.
