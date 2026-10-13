# Checkouts and worktrees

These rules cover where agents write, how work is preserved and how a
checkout is ended. Work is sequential: one canonical checkout per repository,
one active feature branch, one writer at a time. The branch and review
sequence is in `development-workflow.md`, section 6. The tool behavior
described here was checked on 2026-10-01 against the Claude Code and Codex
documentation and the current Codex app. Recheck it when either tool changes.

## Terms

- **Canonical checkout:** the one ordinary clone named in a repository's root
  `AGENTS.md`. All routine development and review happens in it.
- **Task checkout:** where a task writes. Normally this is the canonical
  checkout; a worktree is one only under rule 3.
- **Managed worktree:** one that a tool creates and removes. The Codex app
  keeps them in `$CODEX_HOME/worktrees` by default. Claude Code keeps them in
  `.claude/worktrees/`, along with its subagent and background-session
  worktrees.
- **Ordinary worktree:** one created with `git worktree add`.
- **Legacy checkout:** any further clone or worktree that already exists. It
  is retired under rules 7 and 8 once its unique work is preserved; it is not
  reused for new work.

## Rules

1. **One canonical checkout per repository.** Do not create further clones or
   worktrees for routine development or review. Start agent sessions in the
   canonical checkout, not in a tool-created worktree. Do not keep checkouts
   in folders that a tool synchronizes or the system empties, such as chat
   project mirrors or `/tmp`.
2. **Record the task checkout before writing:** repository, path, branch (or
   base commit if detached), purpose and owner (agent and session). Put it in
   the task's durable evidence.
3. **No new worktrees by default.** No agent creates a worktree or starts a
   concurrent agent automatically. If a task genuinely cannot follow this
   workflow in the canonical checkout, stop and name the concrete conflict to
   the maintainer, for example another writer's unpreservable uncommitted
   work. Only the maintainer can approve a worktree for that one task; record
   its reason, owner and end condition, and end it under rules 7 and 8. Do
   not turn one approval into a standing exception. If a tool creates a
   worktree anyway, treat it as a legacy checkout.
4. **One writer at a time.** The implementing agent writes on the active
   feature branch, then hands off a clean, known commit. The reviewer reads
   that exact commit without writing, for example with `git show` and
   `git diff`. Before switching branches, preserve incomplete, uncommitted
   and ignored unique work (rules 5 and 11). Never force a reset, overwrite
   a stash, or switch branches underneath another active writer. Recheck
   `git status` immediately before writing.
5. **Preserve unique work.** Tool-managed worktrees may start detached.
   Before switching branches or ending a checkout, any unique work must be
   durably recoverable. Unique
   work means commits not on any remote branch, plus uncommitted changes worth
   keeping. It is recoverable when it is:
   - pushed to a named remote branch;
   - saved as a bundle or patch somewhere durable, outside the checkout and
     outside `/tmp`; or
   - held in the tool's recoverable snapshot.

   A bundle preserves committed content, including tracked binaries. A
   patch preserves tracked changes, and binary changes only when made with
   `git diff --binary`. Neither preserves untracked or ignored files, such
   as private build outputs; those need their own copy (rule 11).
6. **No secrets or live state in task checkouts.** Do not copy credentials,
   `.env` files, live state, backups or production logs into a task checkout.
   That includes `.worktreeinclude`: both tools copy matching ignored files
   into new worktrees. Tests use synthetic data, or a read-only snapshot kept
   outside the checkout.
7. **Before ending a checkout, check and record:**
   - uncommitted and untracked files;
   - commits not on a remote branch, after a fresh fetch;
   - ignored files that hold unique data;
   - processes or sessions using the checkout;
   - its owner.

   If anything is unresolved, keep the checkout and ask.
8. **Ending a checkout, by kind.** This applies to legacy checkouts and to
   any worktree approved under rule 3. Retire them one repository at a time,
   only within authorized cleanup scope, after rule 7.
   - **Codex-managed:** the Codex app provides an `archive_worktree` tool. It
     archives a managed worktree and keeps a recoverable snapshot while the
     chat stays open.
     - **If it is available,** meaning `archive_worktree` is in your current
       tool list, apply rule 7, then use it.
     - **If it is not available,** for example in the Codex CLI, a cloud task
       or another tool, do not delete the directory or run
       `git worktree remove` on it. Leave it in place, record the rule 7
       results, and ask the maintainer to archive it from the Codex app.

     Codex also removes older managed worktrees automatically, except those
     of pinned or active chats and permanent worktrees. So rule 5 applies
     before work is left in one.
   - **Claude Code `--worktree`:** at exit, choose Keep unless all unique work
     is recoverable. Choosing Remove deletes the worktree and its local
     branch. Claude Code sweeps subagent and background-session worktrees only
     when they hold no work.
   - **Claude desktop sessions using a worktree:** what archiving the session
     does to its worktree is not yet verified. Apply rule 7 before archiving
     one.
   - **Ordinary:** run `git worktree remove <path>`. It refuses a dirty tree;
     do not force it. Run `git worktree prune` for entries whose directory is
     already gone.
9. **Separate decisions.** Ending a checkout, deleting a branch, and deploying
   are different actions with different approvals. Delete a local or remote
   branch only after its merge is confirmed on GitHub, or after the
   maintainer approves discarding it. Historical branches and tags may
   remain as recovery references; they are not active tasks. Do not delete
   branches or artifacts merely to reduce their number.
10. **Checkpoints, closeout and daily closure.** Daily closure means zero
    unexplained loose ends. It does not require finishing or deleting
    unfinished work. A loose end is any work or state a task leaves behind:
    a kept checkout, uncommitted or unpushed work, an open branch or PR, or
    a pending decision.
    - **Dispositions:** every loose end needs a disposition: retained,
      expected or in progress, with an owner, a reason and the date of the
      next decision. Documented expected state, such as a repository's
      known local edits, is a disposition too. It does not become overdue
      merely because it is still present.
    - **Attention:** new unexplained work and missing closeouts need
      attention immediately. A disposed loose end needs attention again
      when its decision date arrives, when it materially changes, or when
      its preservation becomes uncertain.
    - **Commit and preserve:** at each meaningful checkpoint, commit
      coherent, verified work to the task branch. Before handing work back
      or closing a session, make all unique work durably recoverable as in
      rule 5: push it to a named remote branch, or save a bundle or patch
      outside the checkout and outside `/tmp`. This applies whether or not
      the checkout is kept and whether or not HEAD is detached. Unfinished
      or unverified work is preserved the same way and labelled as such,
      for example in a draft PR or the commit message. It does not have to
      be finished first. Never commit secrets, credentials or live state to
      do this (rule 6). A disposition records a decision; it preserves
      nothing.
    - **Records:** write one activity record at each checkpoint handed back
      for review and one at closeout. Each record gives the repository,
      task checkout, agent and session, stage, any pull request, and these
      checkpoint fields:
      - **Baseline:** the `main` head SHA the work started from.
      - **Feature:** the active feature branch and its head SHA, or "none".
      - **Evidence:** tests run at that head and their level (local,
        simulated, hardware or deployed), and the review status of that
        exact head.
      - **Preservation:** where unique work and artifacts are recoverable
        (rules 5 and 11), and whether each copy is same-machine or
        off-machine.
      - **Next action:** one concrete step and who takes it.

      It also lists every unresolved item and dispositions for the loose
      ends being kept. A checkpoint record also gives the date of the next
      checkpoint or closeout; a closeout is missing once that date passes.
    - **Closeout** means rule 7 has been checked and recorded, unique work
      is durably recoverable, and every loose end is named and disposed. Reporting completion does not
      dispose of anything: observed state that contradicts a closeout
      still needs attention.
    - **Where to write:** use `bardbox housekeeping-activity` from
      `bardbox-tools` where it is installed. It writes each record as a
      separate file in a private store outside every repository. Never
      append to a shared file. Otherwise, give the same fields in the
      handoff.
    - **Records don't replace the inventory:** activity records supplement
      the housekeeping inventory and never replace it. A missing record
      does not show that nothing changed.

    A disposition is not approval, and neither is committing or pushing a
    task branch. Disposal, merging, ending a checkout and deployment keep
    their separate approvals (rule 9).
11. **Build artifacts and private recovery data.** Firmware binaries, their
    manifests and build inputs, and private recovery data such as device
    backups are kept in a durable store that does not depend on any checkout,
    branch or app session. Record a SHA-256 checksum for each file, and keep
    a recovery copy verified by recomputing those checksums. State whether
    each copy is on the same machine or off-machine: a same-machine copy
    survives deleting a checkout but not losing the disk. A Git bundle
    preserves tracked files, including tracked binaries, but not untracked
    or ignored build outputs. Name stores by role in public
    repositories, not by private path. Never commit secrets or private data
    to preserve them (rule 6).
