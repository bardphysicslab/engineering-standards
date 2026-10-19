# Claude handoff: workflow gate setup package

- **Milestone:** `WGP-SETUP-1`, ENG-004 installation/test package.
- **Status:** PREPARED; awaiting Codex exact-revision review. Not installed, not
  live-tested, not merged.
- **Owner:** [#19](https://github.com/bardphysicslab/engineering-standards/issues/19):
  [setup/test authorization](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6275981244),
  [acceptance change](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6276212711)
  (useful scoped guard with known gaps). PR [#20](https://github.com/bardphysicslab/engineering-standards/pull/20).
- **Branch:** `codex/workflow-gate-prototype`; reviewed prototype baseline
  `4831c6f3b3f0f8865402d205f4b5a73361af1e37`. The exact head is recorded in the PR.
- **Shared guidance:** bardphysicslab/engineering-standards@aa8454649fc2e8bb5ad50a5829f8d0cbda736442
- **BardBox standards:** bardphysicslab/bardbox@34b8ae6e7a9ee3340093b6091df7acfd97578b83
- **Roles:** Claude sole writer; Codex reviews; Kornelis applies any system change.
- **Review round 1:** [Codex review of `7bd85c2`](https://github.com/bardphysicslab/engineering-standards/pull/20#issuecomment-6276383806)
  requested three runbook/live-plan corrections; addressed below. No code defect was found in the entry.
- **Review round 2:** [Codex review of `f602cd9`](https://github.com/bardphysicslab/engineering-standards/pull/20#issuecomment-6276525245)
  found two preflight/rollback issues; addressed below. Round-1 fixes are unchanged.
- **Previous milestone:** [prototype handoff](archive/CLAUDE-HANDOFF-WGP-PROTOTYPE.md).

## Refusal recorded

Writing an installer script was refused by Claude's session safety check as
self-modification. That was respected: no installer exists, and no other tool
or agent was asked to write one. The runbook gives Kornelis manual `sudo` steps
instead. Nothing on this machine was installed or changed.

## Review corrections (round 1)

| Finding | Correction | Evidence |
| --- | --- | --- |
| Policy command wrote literal `ENROLL` | `live_fixture.py` writes `policy.json` enrolling the fixture's real path; new read-only `verify_install.py policy` checks it before copying | Documented commands run at a scratch path: policy names the real fixture path, check passes; the old command's output is rejected (`policy.json is malformed`); tests for placeholder, non-top-level and wrong-role policies |
| Existing-policy merge and rollback could lose settings | Runbook is new-install only and stops if any destination exists; each rollback removal of a policy file is guarded by `cmp -s` against the installed fragment, and folders are removed only when empty | Runbook test checks every policy-file `sudo rm` line starts with `cmp -s`; probe shows all three destinations absent today |
| Live plan could use another session or clone | Tests use the existing Desktop-embedded session (records entrypoint and version first; `/cd` into the fixture, or stop) and the existing Codex chat after a ChatGPT app restart; hook origin is shown by the installed-entry deny text; C2–C5 check from the agent that policy, gate code and store refuse writes, and that `sudo` needs a password. `verify_install.py installed` checks protected, byte-identical copies before any hook is registered | Verifier tests: identical protected copy passes, changed `gate.py` and non-root owner fail; against the real system path it fails today because nothing is installed |

## Review corrections (round 2)

| Finding | Correction | Evidence |
| --- | --- | --- |
| Verifier accepted any `.git` entry | `verify_install.py` asks Git (fixed hook environment, `/usr/bin/git`) for the top level and requires it to equal the enrolled real path and to have a commit | New tests: `.git` file with `not a gitdir`, empty `.git` folder, a nested `.git` inside another checkout and a repository without commits all fail; an ordinary checkout and a linked worktree pass. They fail against `f602cd9` |
| Rollback compared against mutable checkout files | Installation keeps root-owned reference copies in `/Library/BardWorkflowGate/installed/`; activation installs from them; rollback compares against them, runs from any directory and removes gate files only after both policy files are gone | Tests run the runbook's own rollback lines (sudo removed, paths redirected to a disposable prefix) from a folder whose source copies were edited: an unchanged install is fully removed. With the installed Claude settings edited, that file is kept, Codex is removed and the gate files stay. Both fail against `f602cd9` |

SHA-256 of the configuration files at this revision. If a reference copy is
missing, compare with `shasum -a 256`; the runbook still refuses removal without it:
`claude-managed-settings.fragment.json` `3cd4f27379f294013361289ad31836ae4edd4b9bbaa63030df710b1def84c2f1`,
`codex-requirements.toml` `9ad9e5cbd526ca091c24bb147ea11a44916714b2d4116309d6ae52ca2929ac67`.

## Runtime and policy facts (read-only probes, 2026-10-19)

- Active Claude session: Desktop-embedded Claude Code 2.1.284 (Desktop 2.16120.0).
  The separate Homebrew CLI is 2.1.267.
- Codex: the CLI bundled in the ChatGPT app reports `codex-cli 0.163.0-alpha.10.2`
  and `hooks` stable/on. That does not show hooks active in the running chat.
- No MDM enrollment. No Claude Code managed settings, no `/etc/codex`, no user
  Claude settings file, no Codex hooks. The account is a local administrator.
- Vendor docs: Claude Code file-based managed settings reload in running
  sessions; Codex requirements load at startup (restart). `onFailure: "block"`
  needs Claude Code 2.1.295 or later, and Codex continues on failed hooks.

## Behavior checked (synthetic tests, no live runtime)

| Requirement | Evidence | Result |
| --- | --- | --- |
| Missing evidence denies; approved scoped edit allowed | Entry subprocess with disposable install dir | Pass |
| Writer cannot choose role, evidence file or clock | Env overrides of role, store and time ignored | Pass |
| Stale, malformed, missing or conflicting coverage, and self-approval deny | Entry tests and live-fixture drafts | Pass |
| Guard tamper, shell, background, MCP and unknown deny in enrolled checkout | Entry tests | Pass |
| Unprotected install denies | Not root-owned; writable policy or store; symlinked store; malformed policy | Pass |
| Unenrolled session passes through; enrolled write target still checked | Entry tests | Pass, with the Bash gap shown |
| Config proposals call `python3 -I` entry and add no other keys | Fragment tests | Pass |
| Policy and installed copy verifiable before activation; runbook new-install only with guarded rollback | Verifier and runbook tests | Pass |

`python3 -m unittest discover -s tests -p 'test_*.py'`: 56 tests OK (36 prototype, 2 scaffold,
18 package); the scaffold checker passed; CI runs both gate suites.

## Architecture compliance

- The reviewed `gate.py` and adapters are unchanged; `install/entry.py` wraps them.
- Proposed config adds only one PreToolUse hook per runtime; no permission,
  sandbox, `allowManagedHooksOnly` or other policy change.
- One rule owner: decision index row updated, no duplicate rulebook; the prototype
  handoff was archived, not rewritten.

## Gaps (accepted for a practical guard)

Crash or timeout fails open in both runtimes; unenrolled shell can change
enrolled files; prior and persistent processes, Codex `write_stdin`, hosted or
specialized tools are unhooked; check-to-write races; approver and writer are
labels, so independence rests on Kornelis's protected copy; any administrator or
cached `sudo` credential can change the store or policy. Details:
[install/README.md](../tools/workflow_gate/install/README.md#known-gaps-accepted-for-a-practical-guard).

## Next action

1. Codex reviews the exact PR head.
2. Kornelis then runs the [install steps](../tools/workflow_gate/install/README.md#install-kornelis-after-review-of-commit-c)
   for that commit, then the live tests in the existing sessions (C1–C10, X1), and records the outcomes in #19.
   Rollback is in the same runbook.
