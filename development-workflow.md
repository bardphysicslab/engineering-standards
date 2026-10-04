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

Work from a known-good state.

For each task:

Define done → Design → Decompose → Implement → Verify → Commit

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

## Core Principle

Important state lives in files, not conversation history.

Work proceeds only from verified checkpoints.

Humans control scope and architectural decisions; mechanical
guardrails should enforce critical objective rules where practical.
