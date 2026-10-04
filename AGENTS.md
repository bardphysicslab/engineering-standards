# Agent instructions: engineering-standards

This repository holds the shared engineering guidance itself. See
`README.md` for its scope and history.

## Shared guidance

Before planning, proposing, reviewing, delegating or implementing changes,
read the shared engineering guidance in `bardphysicslab/engineering-standards`
(this repository). Your tool does not load it automatically.

1. Resolve `main` once per task: run `git fetch origin main`, then
   `git rev-parse origin/main`. If the fetch fails, use the existing
   `origin/main` and say it may be stale. Without a clone, run
   `gh api repos/bardphysicslab/engineering-standards/commits/main --jq .sha`.
2. Read these files at that SHA with `git show <sha>:<file>`:
   - `README.md`
   - `development-workflow.md`
   - `agent-practice.md`
   - `checkouts-and-worktrees.md`
   - `agent-coordination.md`
3. Record `Shared guidance: bardphysicslab/engineering-standards@<sha>` once
   in the task's durable evidence. If a review or proposal produces no such
   artifact, state it once in your response.

The files at that SHA govern the task, including a task that changes them.
Your branch's edits, including to this file, are proposals until merged to
`main`. Review them with `git diff <sha> -- .`.

## Changing this repository

- Follow `README.md`, "Changing this guidance". In each pull request, list
  the repositories affected and any effect on how the tools load
  instructions.
- Keep a move of existing text separate from a change in what the text
  requires.
- This repository is public. Do not add private hostnames, paths, account
  names, credentials or personal contact details.
- Keep project-specific architecture, contracts and local rules in their
  owning repositories.
