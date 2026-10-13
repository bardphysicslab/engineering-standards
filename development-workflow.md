# Development Workflow Constitution

This document governs how development work is formulated and delegated.

Its purpose is speed with control: make agent tasks clear, bounded,
verifiable, and consistent with the project's established architecture.

## 1. Prompt Preflight

Before giving a coding task to an agent, check the request.

### Intent
- What exactly are we trying to accomplish?
- Is the requested behavior clear?
- Are important assumptions still unresolved?

If the intent is unclear, clarify it before implementation.

### Boundaries
- Is this one reasonably scoped task?
- What should change?
- What must NOT change?
- Is the likely blast radius small enough to review and recover from?

If the task is too broad, decompose it.

### Verification
Define "done" before implementation.

Ask:
- What observable behavior proves success?
- What test, command, measurement, or inspection will verify it?
- What normal case should work?
- What important edge case should work?
- What failure/error case should behave safely?

If we cannot cheaply determine whether the task succeeded,
the task is not ready to delegate.

## 2. Project Compliance

Before implementation, read:

1. `AGENTS.md`
2. `ARCHITECTURE.md`
3. Any relevant documents referenced by them

For BardBox and Bard Physics Lab web applications, hosting, email, messaging,
SMS, authentication or monitoring, also read
[Bard applicability and service guidance](docs/bard-it/README.md) and the
[original institutional requirements](docs/bard-it/web-application-and-hosting-requirements.pdf).
Apply the policy to current and future projects wherever applicable; preserve
its conditional language and keep meeting suggestions distinct from mandates.
Assess existing-project gaps in the owning GitHub tracker. Resolve uncertain
applicability with Bard IT/PR rather than assuming compliance or exemptions.

Check the proposed task against those documents.

Specifically ask:
- Does this preserve existing architectural decisions?
- Does it cross an established interface or ownership boundary?
- Does it duplicate something that already exists?
- Does it violate a project rule or convention?
- Does completing it require an architectural decision that has not
  yet been made?

If there is a conflict or ambiguity, stop and resolve it before coding.

## 3. Execution

Work from a known-good state: the current `main` (section 6).

For each task:

Define done → Design → Decompose → Implement → Verify → Commit →
Review → Integrate

Each implementation step should be small enough to:
- understand,
- verify,
- review,
- and revert cheaply.

Do not build new work on top of an unverified change.

## 4. Human Checkpoint

Before implementation begins, present the proposed task back to the maintainer
in plain language:

**Goal:** What are we changing?

**Boundaries:** What are we deliberately not changing?

**Verification:** How will we know it worked?

**Project compliance:** Does it comply with `AGENTS.md`,
`ARCHITECTURE.md`, and relevant project documentation?

**Open questions:** What, if anything, must be decided first?

Do not begin implementation until unresolved questions that materially
affect the design or verification have been resolved.

Presenting the checkpoint is not a request for new authorization. If the
maintainer has already authorized the task and no question that materially
affects the design or verification is open, present the checkpoint and
proceed. Do not ask again for authorization already given. Authorization
covers only the actions it names.

## 5. Recovery Rule

If either the maintainer or the agent can no longer clearly explain:

- what is being changed,
- why it is being changed,
- what state the implementation is in,
- or how it will be verified,

stop adding functionality.

Summarize → Verify → Return to a known-good state → Re-scope →
Continue with the smallest verifiable step.

## 6. Delivery Sequence

Work is delivered one feature at a time, in the repository's one canonical
checkout (`checkouts-and-worktrees.md`, rules 1 to 4).

- **`main` is the baseline.** It holds the last tested and independently
  reviewed working version. Nobody pushes unreviewed work to `main`.
- **One active feature branch.** Start it from the current `main`. The
  implementing agent implements and tests on it, then hands off a clean,
  known commit with its evidence. The reviewing agent reviews that exact
  head. Findings are fixed on the same branch and the new head is reviewed.
- **Integrate before the next feature.** Reviewed, passing work is merged
  into `main` and pushed before the next feature branch starts. Do not
  accumulate completed but unmerged branches.
- **Distinct steps.** Implementation, review, merge and deployment are
  separate steps with separate approvals. A passing review does not by
  itself authorize a merge; passing tests do not show deployment.
- **Exceptions are named.** If a task genuinely cannot follow this sequence,
  name the concrete conflict to the maintainer instead of bypassing it.

### Reusing hardware evidence

Completed hardware acceptance evidence stays valid for behavior that has not
changed. Repeat a hardware acceptance check only for a concrete changed
behavior: name the changed invariant and why the existing evidence cannot
cover it. Record which existing evidence was reused and at which commit.

## Core Principle

Important state lives in files, not conversation history.

Work proceeds only from verified checkpoints.

Humans control scope and architectural decisions; mechanical
guardrails should enforce critical objective rules where practical.
