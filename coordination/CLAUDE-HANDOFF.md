# Claude handoff: restart-guidance correction and Reference adoption preparation

- **Milestone:** `WGP-ADOPT-PREP-1`, [authorized scope](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6277110447).
- **Status:** PREPARED; awaiting Codex exact-revision review. Nothing installed,
  nothing enrolled, no application code, nothing merged.
- **Parts:**
  1. Shared correction on PR [#20](https://github.com/bardphysicslab/engineering-standards/pull/20),
     branch `codex/workflow-gate-prototype`. The exact head is recorded in the PR.
  2. Reference adoption drafts on BardBox-Reference branch `codex/first-freezer-reference`
     at `a3142b36d30689263b9b00618358ebd56fb632d3` (parent `2feff97`, the head of
     closed PR #2, which is unchanged), owned by [Reference#1](https://github.com/bardphysicslab/BardBox-Reference/issues/1).
- **Shared guidance:** bardphysicslab/engineering-standards@aa8454649fc2e8bb5ad50a5829f8d0cbda736442
- **BardBox standards:** bardphysicslab/bardbox@34b8ae6e7a9ee3340093b6091df7acfd97578b83
- **Roles:** Claude sole writer; Codex reviews; Kornelis approves and runs any system step.
- **Previous:** [setup handoff](archive/CLAUDE-HANDOFF-WGP-SETUP-1.md), [prototype handoff](archive/CLAUDE-HANDOFF-WGP-PROTOTYPE.md).

## Part 1: restart guidance (engineering-standards)

| Requirement | Change | Evidence |
| --- | --- | --- |
| Replace the unconditional immediate-reload claim | `install/README.md`: on a new install, fully restart the Claude desktop app and resume the same conversation; C1 must be denied first, or stop | [Live results](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6277040341): first C1 not denied; denied in the same embedded 2.1.284 session after a full Desktop restart |
| State the cause carefully | Likely explanation cited from vendor docs (a file created mid-session loads only if its folder existed at session start); not a proven sole cause | Documentation quote in the runbook |
| Rollback does not claim unloading | After rollback: restart both apps, record it, and check that a harmless read works; a hook still pointing at the removed entry exits 2 and blocks every call | `/usr/bin/python3 -I` on a missing script exits 2 (checked locally). [Rollback record](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6277080061): disk removal confirmed; app restart not yet confirmed |

Observation, not confirmation: in this Claude session, tool calls after the
rollback ran normally (Read, Bash, Git). With the hook still loaded they would
have been blocked, so this session is not running the removed entry. A Desktop
restart after rollback and the Codex side remain unconfirmed.

## Part 2: Reference adoption (BardBox-Reference, preparation only)

- `docs/workflow-gate-adoption.md` covers:
  - the current facts and the real workflow (decide, approve, code, review, merge);
  - the human enrollment, test and rollback changes to the shared runbook;
  - the shell/MCP blocker, with choices A–C.
- `coordination/workflow-gate/registry-evidence.draft.json` is the Registry
  requirements draft in the gate's format:
  - covered: R1 ownership, R2 layout, R3 identity layers;
  - missing: R4 entity ID and binding, R5 Registry contract, R6 Controls in
    slice, R7 validation limits, R8 permission and timing, R9 baseline and
    scaffold, R10 formats;
  - conflicting: R11 task-tracking policy.

  It has no approval block and private placeholders, and it reuses no fixture
  identity or approval.

## Checks (behavior separate from architecture)

**Behavior.** The draft ran through the reviewed Claude adapter against the
real Reference checkout, with placeholders filled only in a scratch copy and
`HEAD` as a check-only baseline stand-in:
- all eight governing digests verified;
- the write to `software/app/registry/` was denied with the eight questions;
- a tampered digest was denied as stale governing evidence.

The proposed Reference policy command produced a policy that
`verify_install.py policy` accepts. In engineering-standards, the full suite
passes: 56 tests, now with runbook assertions for the restart correction. The
scaffold checker passes in both repositories.

**Architecture.**
- The gate, adapters and runbook are reused unchanged; no new framework.
- Shared guidance stays in engineering-standards; application facts and drafts
  stay in Reference.
- The decision indexes are not duplicated; the ENG-004 row now records "fixture
  only, removed".

## Questions for Kornelis (material)

1. R4–R11 in the draft. R5 (the Registry contract) and R9 (baseline and
   scaffold) come first.
2. Which route for tests and Git once enrolled: A (Kornelis runs them in
   Terminal), B (a separately reviewed restricted-shell decision) or C
   (unenrolled shell, which weakens the guard)?
3. Confirm the app restarts after rollback.

## Gaps

These remain as accepted:
- crash or timeout fails open;
- unenrolled shell;
- persistent and other unhooked routes;
- check-to-write races;
- label-only identities;
- administrator or cached-`sudo` access.

Shell/MCP denial makes enrolled coding impractical without a choice from
question 2. Registry stays paused.

## Next action

Kornelis brings this handoff to Codex for review of the exact PR #20 head and
Reference `a3142b3`, then answers the questions on Reference#1.
