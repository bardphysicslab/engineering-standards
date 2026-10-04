# Shared agent practice

General engineering rules for Bard Physics Lab repositories. The sections
"Decisions and proportional workflow", "Verification and documentation",
"Architectural self-check" and "Refactoring with little test coverage" came
from the BardBox root `AGENTS.md`. "Change discipline" and the
focused-test and completion-report rules were promoted from Beaker. See
`README.md` in this directory for when to read it.

## Decisions and proportional workflow

Use **Define done → Design → Decompose → Implement → Verify → Commit** for
meaningful new work. Generating code with an agent is one way to implement,
not a separate step. Keep changes small enough for human review, with durable
notes and verified recovery checkpoints. Course reference:
[CMU Agentic Software Development](https://github.com/CMU-17-214/f2026).
Consult relevant material before attributing a rule to it; the course is a
learning reference, not an additional mandatory rulebook.

Apply the course to proposed updates, rather than citing it decoratively:

- Before an architecture recommendation, map the current data, operations, and
  dependencies; trace a representative request to where its invariant is enforced.
- Locate each proposed correction in actual files and explain a concrete failure
  or costly change. For material boundary decisions, compare two plausible
  decompositions, their costs, and the condition that would change the choice.
- Specify preserved invariants and externally observable behavior before a
  refactor. Distinguish additive contract evolution from breaking changes and
  state the compatibility/deprecation path.
- Keep a concise evidence/decision record so later agents can compare intended
  design with reality, without inventing another general-purpose rulebook.

Sources consulted for this consolidation (2026-09-25): course
[learning goals](https://github.com/CMU-17-214/f2026/blob/main/learninggoals.md)
and [Lab 3: Find the Design Gap](https://github.com/CMU-17-214/f2026/blob/main/labs/lab03.md).
These rules are our application of that material; classroom submission and
transcript-publication requirements do not become BardBox requirements.

For material decisions: flag the issue, explain evidence and consequences,
compare reasonable options and effort, recommend an approach, obtain the
maintainer's decision where needed, and record it. Existing task authorization
covers routine choices; do not ask again for already authorized work.

Existing systems with deadlines improve incrementally. Record deferred
architecture or verification debt and follow-up triggers. Do not make an
unrelated refactor a release prerequisite or waive safety/data-integrity checks
because of a deadline. Repeated failed fixes are a reason to reassess scope and
the recovery checkpoint, not to continue generating ever-larger changes.

## Change discipline

- Do not invent missing facts. A reasonable assumption is allowed when you
  state it.
- Do not silently introduce new schemas, architectural patterns,
  dependencies, or sources of truth.
- Preserve existing architectural decisions unless the task authorizes
  reconsidering them. Re-examining a decision in an assessment is not
  changing it.
- Do not refactor unrelated code while implementing a feature or fix.
- Avoid speculative abstractions. Build a boundary when there is a real
  need for it.
- Keep secrets and credentials out of source control.

## Verification and documentation

- Add or update focused tests when changed behavior warrants them. Avoid
  tests that merely mirror the implementation.

- Run relevant existing tests; identify changed assumptions and credible gaps in
  the tests themselves. Recommend additional checks with their purpose. Verify
  actual behavior and review the diff, including unexpected files and weakened
  tests. Green tests or an agent summary alone are insufficient evidence.
- Cover relevant failures, boundaries, interactions, hardware limits, data
  integrity, timing, offline operation, recovery, permissions, and compatibility.
  Use controlled dependencies for component tests. Distinguish local, simulated,
  hardware, and deployed evidence. Do not claim hooks enforce rules unless such
  checks actually exist.
- Perform a concise blind-spot scan for changes that can break behavior: include
  configuration, security, observability, maintenance, historical data,
  cross-project effects, versioning, migration, rollout, and recovery where
  relevant. Skip a formal scan for genuinely trivial changes.
- Flag expensive, destructive, or unusual tests for a scope/authorization
  decision; do not run them automatically. Broaden tests when a concrete risk
  warrants it, not as an unbounded ritual, and explain the reason in plain
  language.
- Every material change checks documentation impact, including an explicit
  “no documentation change required” result when appropriate. Update affected
  user guidance, architecture/data flow, setup/maintenance instructions,
  derived-metric definitions, decision records, and platform standards.
  These are required topics, not a mandate for a separate file for each topic.
- Explain derived values plainly to users. Document mathematical methods and
  thresholds where relevant: formula, implementation, and tests must agree.
  Record meaningful decisions with their reason, alternatives, and consequences.
- Report completion concisely: what changed, how it was verified, and
  material limitations or remaining risks. Mention what did not change only
  when it clarifies scope.

## Architectural self-check

Scale the check to the change: a sentence or two for a small, local fix; the
full list below for a multi-module refactor, a boundary or source-of-truth
change, or an explicit request to assess a design. When the task is an
assessment, report rather than implement. When implementation is already
authorized, the check informs that work; it is not an additional approval step.

1. Re-examine earlier decisions, including your own; prior authorship or
   approval is not evidence. Cite the files and functions involved.
2. Trace a normal path and a relevant failure path through the behavior being
   changed, including its most recent change.
3. Check against the project's `ARCHITECTURE.md`. Where a project has none,
   use `docs/architecture-principles.md` in `bardphysicslab/bardbox`, read at
   one resolved `main` commit of that repository
   (`git show <bardbox-sha>:docs/architecture-principles.md`). It directs to
   bardbox's root `ARCHITECTURE.md`, read at the same commit:
   - each module has a cohesive responsibility: related operations that change
     for the same reason;
   - each piece of authoritative state has a named owner that performs its
     mutations and enforces its invariants;
   - business rules are separate from UI, storage, network and hardware code;
   - controllability: a test can supply the inputs, initial state, time and
     dependency responses (including failures) the rule needs;
   - observability: a test can see the outcome (return value, state change,
     emitted event or recorded effect), including failures.
4. Name the boundaries worth keeping and, for each weakness, its practical
   consequence.
5. Recommend continue, small repair first, or clarify a requirement, and end
   with one bounded next step and the checks that show it is done.

## Refactoring with little test coverage

- Refactor in small steps that leave the application working. Where practical,
  keep structural changes (extract, move, rename, rewire) in separate commits
  from behavior or business-rule changes; when they must be combined, say so
  and name the behavior that changed.
- Before a structural step, pin the behavior it touches with the smallest useful
  check: a characterization test, or a written manual/bench scenario (setup,
  action, expected observation). A full suite is not a prerequisite.
- A characterization test records current behavior, not intended behavior. If
  current behavior looks wrong or conflicts with a requirement, label it and
  report it rather than changing it inside the refactor.
- Make a dependency explicit (a parameter, or an injected clock, transport or
  store) when a concrete test needs to control it. Do not add interfaces,
  frameworks or layers for flexibility nobody has asked for; a plain function or
  concrete class is often enough.
