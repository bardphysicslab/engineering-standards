# Engineering standards

This repository is the single maintained copy of the engineering guidance
shared by Bard Physics Lab repositories. Other repositories reference it from
their root `AGENTS.md`; they do not copy it.

This repository is public. Do not add private hostnames, paths, account names,
credentials or personal contact details here.

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
