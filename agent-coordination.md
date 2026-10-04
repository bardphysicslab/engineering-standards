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

Agents do not message, start, wake or drive one another, operate each
other's desktop applications, or approve one another's permissions. Prompts
and reports pass through the maintainer: the reviewing agent prepares a
prompt, the maintainer sends it to the implementing agent, and the
maintainer returns the report for review. Sources: the maintainer's standing
instruction for Codex and Claude coordination (2026-10-03); the daily
housekeeping handoff in `bardphysicslab/bardbox-tools`, `docs/housekeeping.md`.

## Independent review and merging

Work is reviewed by someone other than its author before it merges. A review
records its governing commit and its findings, and does not by itself
authorize a merge. Merges, branch deletion, ending checkouts and deployment
each need their own explicit authorization. Sources: `agent-practice.md`,
"Verification and documentation"; `checkouts-and-worktrees.md`, rules 9
and 10.

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
- In a shared checkout, edit only files your role owns. A repository's root
  files name its coordination files and their owners. Sources:
  `checkouts-and-worktrees.md`, rule 4; `README.md`, "Precedence", rule 3.
