# Agent coordination

How the maintainer and agents divide work, review and approval. This page
collects requirements that were already stated in other files and in the
maintainer's standing instructions. It adds no new obligations. Each section
names its source. Where a source states the rule more strictly, the stricter
rule wins (`README.md`, "Precedence", rule 2).

## Roles

- **The maintainer** sets each task's scope and makes product, architecture,
  access, deployment and other consequential decisions. Authorization covers
  only the actions it names. Sources: `README.md`, "Precedence", rule 1;
  `development-workflow.md`, "Core Principle" ("Humans control scope and
  architectural decisions").
- **An implementing agent** does the bounded work and reports evidence:
  what changed, how it was verified, and the remaining limits. Source:
  `agent-practice.md`, "Verification and documentation".
- **A reviewing agent** reviews independently. Neither an agent's own
  summary nor green tests are sufficient evidence of work it did not verify.
  Source: `agent-practice.md`, "Verification and documentation".

## Manual relay between agents

By default, agents do not message, start, wake or drive one another, operate
each other's desktop applications, or approve one another's permissions. Prompts
and reports pass through the maintainer: the reviewing agent prepares a
prompt, the maintainer sends it to the implementing agent, and the
maintainer returns the report for review. Sources: the maintainer's standing
instruction for Codex and Claude coordination (2026-10-03); the daily
housekeeping handoff in `bardphysicslab/bardbox-tools`, `docs/housekeeping.md`.

The maintainer may explicitly authorize direct coordination for a named task or
session. Record its scope, destination and end condition in the owning issue or
handoff. Verify the destination and preserve drafts; do not create duplicate
workers. Sending a prompt is not proof work started or completion will be reported.
State whether completion is checked manually or through a verified notification
path. Direct coordination grants no implementation, merge, deployment, credential
or permission authority beyond the maintainer's actual authorization. Skills and
local tooling must follow this shared boundary; their defaults do not grant it.

## Independent review and merging

Work is reviewed by someone other than its author before it merges. A review
records its governing commit and its findings, and does not by itself
authorize a merge. Merge, deployment, discarding unique work and exceptional
checkout retirement require authorization covering the action. Routine deletion of confirmed merged
task branches and returning an unowned clean canonical checkout to synchronized
`main` are task closeout under `checkouts-and-worktrees.md`, rule 10; do not ask a
second time for that routine cleanup. Protect other writers and recovery needs.
Record any maintainer-authorized review exception against the specific revision
and risk; do not turn a single waiver into a standing exemption.
Sources: `agent-practice.md`,
"Verification and documentation"; `checkouts-and-worktrees.md`, rules 9
and 10.

The sequence is one active feature branch at a time: the implementing agent
implements and tests, the reviewing agent reviews the exact head, and
reviewed passing work lands in `main` before the next feature starts. Agents
work one writer at a time in the canonical checkout and do not start
concurrent agents or new worktrees. Sources: `development-workflow.md`,
section 6; `checkouts-and-worktrees.md`, rules 1 to 4.

## Authorization, environment isolation and deployment

- Keep development, test and production data, credentials, targets and state
  separate. Do not test against live systems, change authoritative external
  data, deploy, restart services or perform destructive actions without
  explicit authorization covering that action. Documentation changes grant
  none. Source: `bardphysicslab/bardbox` root `AGENTS.md`, "Operational
  boundaries", where the BardBox-specific requirements also remain.
- Passing tests is not deployment approval. Source: the same section.
- No secrets or live state in task checkouts. Source:
  `checkouts-and-worktrees.md`, rule 6.

## Handoffs, records and ownership

- A handoff, pull request, commit message or dated evidence record is the
  durable evidence of a task. It records the governing commit once. Source:
  `README.md`, "Which version governs".
- Checkpoint and closeout records, dispositions and daily closure follow
  `checkouts-and-worktrees.md`, rule 10.
- One writer at a time in the canonical checkout; hand off a clean, known
  commit. A repository's root files name its coordination files and their
  owners. Sources: `checkouts-and-worktrees.md`, rule 4; `README.md`,
  "Precedence", rule 3.
