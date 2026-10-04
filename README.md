# Engineering standards

This repository is the single maintained copy of the engineering guidance
shared by Bard Physics Lab repositories. Other repositories reference it from
their root `AGENTS.md`; they do not copy it.

This repository is public. Do not add private hostnames, paths, account names,
credentials or personal contact details here.

## Human overview

A short map for people. It describes where guidance lives and the order to
read it in. The rules themselves are in the files listed.

```text
bardphysicslab/engineering-standards    shared engineering guidance (this repository)
├── README.md                    what to read, which commit governs, precedence, changes
├── development-workflow.md      preflight, project compliance, execution, human checkpoint, recovery
├── agent-practice.md            decisions, change discipline, verification, architectural self-check
├── checkouts-and-worktrees.md   checkouts, worktrees, preservation, checkpoints, daily closeout
├── agent-coordination.md        roles, manual relay, independent review, authorization boundaries
├── AGENTS.md                    instructions for editing this repository itself
└── CLAUDE.md                    compatibility pointer to AGENTS.md

bardphysicslab/bardbox                  BardBox platform guidance (BardBox projects)
├── AGENTS.md                    BardBox-specific change rules
├── ARCHITECTURE.md              BardBox architecture and an index of technical standards
└── docs/                        the technical standards, read when a task touches them

<project repository>
├── AGENTS.md                    entry point: local facts and rules, pointer to shared guidance
├── ARCHITECTURE.md              the project's architecture, when present
├── README.md                    purpose, setup and usage
├── docs/ and other references   documents that AGENTS.md or ARCHITECTURE.md require
├── source and tests             the implementation
└── CLAUDE.md                    compatibility pointer to AGENTS.md
```

Reading order for a task:

1. The project's `AGENTS.md`.
2. The five shared files above, at one resolved commit of this repository.
3. For a BardBox project, bardbox's `AGENTS.md`, `ARCHITECTURE.md` and the
   task-relevant technical standards, at one resolved bardbox commit.
4. The project's `ARCHITECTURE.md`, when present, and the references it
   requires.
5. The source and tests.

This is a reading order, not an override hierarchy. When rules conflict,
[Precedence](#precedence) decides. In brief: the maintainer's task
instructions set the scope, and authorization covers only the actions it
names. For safety, data integrity, approvals, environment isolation and
sources of truth, the most restrictive rule wins. Otherwise a topic-specific
standard governs its topic, and a repository's own files govern its local
facts. A repository may deviate from a shared rule only by naming it and
giving the reason; any other conflict means stop and ask.

A link or a file listing loads nothing; each file has to be opened and
read. A task keeps the governing commits it recorded when it started.

## Scope

This repository holds the reusable requirements: development workflow,
verification, agent practice and coordination, checkouts and worktrees,
preservation, checkpoints, and daily closeout. Project-specific architecture,
technical contracts and local rules stay in the repository that owns them.
BardBox device and platform standards stay in `bardphysicslab/bardbox`.

## What to read

Read all five shared files before planning, proposing, reviewing, delegating
or implementing changes:

1. `README.md` (this file)
2. `development-workflow.md`
3. `agent-practice.md`
4. `checkouts-and-worktrees.md`
5. `agent-coordination.md`

Each repository's root `AGENTS.md` repeats this list and the read commands,
because these files are not loaded automatically. A Markdown link loads
nothing; open each file. Then read the repository's own root `AGENTS.md` and
`ARCHITECTURE.md`, and the documents they require. BardBox device and
platform projects also read the root `AGENTS.md` and `ARCHITECTURE.md` of
`bardphysicslab/bardbox`, at one resolved `main` commit of that repository.

## Which version governs: one SHA per task

At the start of each task, resolve `main` of
`bardphysicslab/engineering-standards` to one commit SHA. Read every shared
file at that SHA. Do not read them from a working tree, which may hold
unpublished edits.

- **Local clone:** run `git -C <clone> fetch origin main`, then
  `git -C <clone> rev-parse origin/main`. Read files with
  `git -C <clone> show <sha>:<file>`.
- **No local clone:** get the SHA with
  `gh api repos/bardphysicslab/engineering-standards/commits/main --jq .sha`.
  Read files with
  `gh api "repos/bardphysicslab/engineering-standards/contents/<file>?ref=<sha>" -H "Accept: application/vnd.github.raw"`.

The guidance at that SHA governs the whole task, including a task that changes
this guidance. Edits on a branch, including this repository's root
`AGENTS.md` that your tool loaded from the working tree, are proposals. They
are not policy until merged to `main`. Review them as a diff against the
governing SHA, for example `git diff <sha> -- .`.

Record `Shared guidance: bardphysicslab/engineering-standards@<sha>` once, in
the task's durable evidence: the handoff, pull request, commit message or the
repository's dated evidence record. If a review or proposal produces no
such artifact, state it once in your response. Keep using that SHA for the
rest of the task.

Copies are not authoritative and do not substitute for the governing SHA.
That includes desktop files, chat project sources, agent memory and earlier
conversations.

## If the guidance cannot be read

- **The fetch fails but a local `origin/main` exists:** resolve the SHA from
  it. Record that SHA and say it may be stale.
- **A required file cannot be read at the resolved SHA:** read-only
  investigation and reporting may continue. Do not implement, commit, push,
  deploy or end checkouts until the guidance has been read, or until the
  maintainer explicitly says to proceed without it. Report which file could
  not be read.

## Precedence

Both supported agent tools combine instruction files into one context. They do
not resolve conflicts themselves, so these rules decide:

1. The maintainer's explicit instructions for the current task set its scope.
   Authorization covers only the actions it names.
2. For safety, data integrity, approvals, environment isolation and sources
   of truth, the most restrictive applicable rule wins, wherever it is written.
3. Otherwise, a topic-specific standard governs its topic over a general
   summary. A repository's root files govern its local facts: paths, commands,
   owners and architecture.
4. A repository may deviate from a shared rule only by naming that rule and
   giving the reason. Any other conflict means stop and ask.

## Changing this guidance

Change it here, by pull request. A proposed change takes effect only when it
is merged to `main`; until then the governing SHA applies, even to the task
proposing the change. In the pull request, list the repositories affected and
any effect on how the tools load instructions. Keep an unchanged
move of existing text separate from a change in what the text requires. When
moving a file or section, leave a pointer at the old location.

## History and cutover

These files moved here from `docs/engineering/` in `bardphysicslab/bardbox`
at commit `dfdb75768b593db49461f1417bb9923f3dc605ac`. `agent-coordination.md`
collects coordination requirements that were already stated elsewhere; it
names its sources.

This repository governs a consuming repository once that repository's root
`AGENTS.md` points here. Until then, the guidance its `AGENTS.md` names still
governs it. A task that already recorded
`Shared guidance: bardphysicslab/bardbox@<sha>` keeps that governing commit
until it ends. The old `bardbox` paths remain as pointers to these files.
