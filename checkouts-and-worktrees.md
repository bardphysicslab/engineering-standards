# Checkouts and worktrees

These rules cover where agents write and how a checkout is ended. The tool
behavior described here was checked on 2026-10-01 against the Claude Code and
Codex documentation and the current Codex app. Recheck it when either tool
changes.

## Terms

- **Canonical checkout:** the one ordinary clone named in a repository's root
  `AGENTS.md`. It tracks the default branch.
- **Task checkout:** where a task writes, either the canonical checkout or a
  linked worktree of it.
- **Managed worktree:** one that a tool creates and removes. The Codex app
  keeps them in `$CODEX_HOME/worktrees` by default. Claude Code keeps them in
  `.claude/worktrees/`, along with its subagent and background-session
  worktrees.
- **Ordinary worktree:** one created with `git worktree add`.

## Rules

1. **One clone per repository.** Make further checkouts as worktrees of the
   canonical clone, not new clones. Do not keep checkouts in folders that a
   tool synchronizes or the system empties, such as chat project mirrors or
   `/tmp`.
2. **Record the task checkout before writing:** repository, path, branch (or
   base commit if detached), purpose and owner (agent and session). Put it in
   the task's durable evidence.
3. **Reuse before creating.** Run `git worktree list`. Reuse an idle worktree
   for the same purpose if it is clean and no process or session is using it.
4. **One writer per working tree.** Concurrent writers use separate
   worktrees. In a shared canonical checkout, edit only files your role owns,
   and recheck `git status` immediately before writing.
5. **Detached HEAD is allowed.** Codex-managed worktrees start detached by
   design. Before cleanup, any unique work must be durably recoverable. Unique
   work means commits not on any remote branch, plus uncommitted changes worth
   keeping. It is recoverable when it is:
   - pushed to a named remote branch;
   - saved as a bundle or patch somewhere durable, outside the checkout and
     outside `/tmp`; or
   - held in the tool's recoverable snapshot.
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
8. **Ending a checkout, by kind:**
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
   maintainer approves discarding it.
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
      task checkout, branch (or base commit), agent and session, stage, any
      pull request, every unresolved item, and dispositions for the loose
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
