# Workflow gate installation package — PREPARED, NOT INSTALLED

A practical, scoped guard with known gaps
([acceptance change](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6276212711)),
not a non-bypassable security boundary. Apply nothing here before Codex has
reviewed the exact commit. The agents never run the `sudo` steps; Kornelis
runs them in a terminal.

## Contents

| File | Role |
| --- | --- |
| `entry.py` | Protected hook entry: policy-chosen role, system clock, protected evidence store, installed code only, root ownership checks, `python3 -I`, fixed Git environment; denies on any error |
| `claude-managed-settings.fragment.json` | Proposed Claude Code managed settings: one PreToolUse hook, nothing else |
| `codex-requirements.toml` | Proposed Codex managed requirements: one PreToolUse hook |
| `policy.example.json` | Policy shape: enrolled checkouts and per-runtime role |
| `live_fixture.py` | Creates a disposable checkout, its `policy.json` and evidence drafts for live tests |
| `verify_install.py` | Read-only checks of the policy and of the installed copies before any hook is registered |

Tests: `python3 -m unittest discover -s tests -p 'test_workflow_gate*.py'`.

## Supported installation path

This Mac has no MDM enrollment and no existing managed Claude Code or Codex
policy (read-only probe, 2026-10-19). The vendor-supported route without MDM is
a system file for each runtime, written by an administrator:

- Claude Code reads `/Library/Application Support/ClaudeCode/managed-settings.json`.
  The vendor documentation says changed settings files reload in running
  sessions, but also that a file created mid-session is loaded only if its
  folder existed when the session started. On a new installation that folder
  does not exist yet, so **fully quit and restart the Claude desktop app** and
  resume the same conversation before testing. Observed on 2026-10-19
  ([live results](https://github.com/bardphysicslab/engineering-standards/issues/19#issuecomment-6277040341)):
  the first C1 write in the running Desktop-embedded 2.1.284 session was not
  denied; after a full Desktop restart the same session denied it. Startup
  discovery of the new folder is the likely explanation, not a proven sole cause.
- Codex reads `/etc/codex/requirements.toml` at startup, so the ChatGPT app must
  be restarted. Managed hooks are trusted by policy; there is no per-hook trust review.

An installer script was refused as self-modification, so these are manual steps.
**This runbook is for a new installation only.** If any destination already
exists, stop: merging into an existing policy is not covered, and rollback
here would not preserve other settings.

## Install (Kornelis, after review of commit `C`)

Run each command from the canonical engineering-standards checkout, clean at
`C`. Stop at the first check that differs.

```bash
git status --porcelain && git rev-parse HEAD
```

Prints nothing, then `C`.

```bash
ls -ld "/Library/Application Support/ClaudeCode" /etc/codex /Library/BardWorkflowGate
```

All three report "No such file or directory". Otherwise stop.

```bash
/usr/bin/python3 tools/workflow_gate/install/live_fixture.py /tmp/wgp-live
```

Creates the disposable checkout `/private/tmp/wgp-live/repo`, its policy
`/tmp/wgp-live/policy.json` and the drafts. Check the policy before copying it:

```bash
/usr/bin/python3 -I tools/workflow_gate/install/verify_install.py policy /tmp/wgp-live/policy.json
```

Must print `policy OK; enrolls /private/tmp/wgp-live/repo`.

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 /Library/BardWorkflowGate /Library/BardWorkflowGate/adapters /Library/BardWorkflowGate/approvals
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 tools/workflow_gate/install/entry.py tools/workflow_gate/gate.py /Library/BardWorkflowGate/
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 tools/workflow_gate/adapters/claude_code.py tools/workflow_gate/adapters/codex.py /Library/BardWorkflowGate/adapters/
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 /tmp/wgp-live/policy.json /Library/BardWorkflowGate/policy.json
```

Keep root-owned reference copies of both hook configurations. Activation
installs from these copies, and rollback compares against them, so rollback
does not depend on this checkout staying unchanged:

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 /Library/BardWorkflowGate/installed
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 tools/workflow_gate/install/claude-managed-settings.fragment.json tools/workflow_gate/install/codex-requirements.toml /Library/BardWorkflowGate/installed/
```

Before registering any hook, check the installed copy:

```bash
/usr/bin/python3 -I tools/workflow_gate/install/verify_install.py installed
```

Must print `installed copy OK: matches this checkout, protected, enrolls /private/tmp/wgp-live/repo`.
Otherwise stop and run the gate-file rollback below.

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 /etc/codex
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 /Library/BardWorkflowGate/installed/codex-requirements.toml /etc/codex/requirements.toml
```

Claude Code last. Do not rely on a running session picking it up; restart as
described below before C1:

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 "/Library/Application Support/ClaudeCode"
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 /Library/BardWorkflowGate/installed/claude-managed-settings.fragment.json "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo -k
```

## Live tests in the existing sessions

Use the existing Desktop-embedded Claude Code session (the coding session that
receives this handoff) and the existing Codex chat. Do not start another Claude
runtime, CLI session or worker. Record each outcome with the exact deny text,
keeping private paths and session IDs in private notes; post a summary on #19.
A deny reason that starts with `workflow gate prototype (Claude Code 2.1.284, installed entry)`
or `(Codex 0.163.0-alpha.10.2, installed entry)` shows that the installed managed
hook ran, because no other hooks are configured.

**Claude Code, before the Claude step above:** Claude reports its runtime from
`CLAUDE_CODE_ENTRYPOINT` (expected `claude-desktop`) and the version in
`CLAUDE_CODE_EXECPATH` (expected `2.1.284`).

**Activation:** after the Claude step, fully quit and reopen the Claude desktop
app and resume the same conversation. C1 must be denied by the installed entry
before any other test. If C1 is not denied, stop: record the activation failure
and do not continue to C2–C10.

**Claude Code, after activation, from the session's own unenrolled folder:**

| # | Action | Expected |
| --- | --- | --- |
| C1 | Write tool to `/private/tmp/wgp-live/repo/src/app.txt` | Denied by the installed entry: no write evidence |
| C2 | Bash: `for f in policy.json gate.py entry.py adapters/codex.py approvals; do test -w /Library/BardWorkflowGate/$f && echo "WRITABLE $f" \|\| echo "not writable $f"; done` | Every line `not writable` |
| C3 | Bash: `touch /Library/BardWorkflowGate/agent-probe /Library/BardWorkflowGate/approvals/agent-probe` | `Permission denied` twice; nothing created |
| C4 | Write tool to new file `/Library/BardWorkflowGate/approvals/evidence.json` (store still empty) | Refused by the operating system (permission) |
| C5 | Bash: `sudo -n true` | `a password is required` (no cached credential) |

C2–C5 run from an unenrolled folder, where the hook lets Bash and the Write call
through, so the refusals come from the root-owned files themselves. They create
or change nothing when the protection holds.

**Claude Code, in the fixture:** Kornelis types `/cd /private/tmp/wgp-live/repo`
in the same session (supported from Claude Code 2.1.246). If the Desktop app
does not accept it, stop and record that as the blocker; do not open a new session.

| # | Action | Expected |
| --- | --- | --- |
| C6 | Edit `src/app.txt` | Denied: no write evidence |
| C7 | Kornelis: `sudo /usr/bin/install -o root -g wheel -m 0644 /tmp/wgp-live/drafts/valid.json /Library/BardWorkflowGate/approvals/evidence.json && sudo -k`; Claude edits `src/app.txt`, then `docs/guide.md` | Allowed; then denied: outside the approved scope |
| C8 | Write `.claude/settings.json`; run any Bash command; call an MCP tool | Each denied |
| C9 | Kornelis installs `self-approved`, `expired`, `conflicting`, `malformed` drafts in turn the same way; Claude edits `src/app.txt` | Each denied with its reason |
| C10 | Kornelis types `/cd` back to the original folder | Bash allowed again (unenrolled pass-through, a known gap) |

**Codex:** quit and reopen the ChatGPT app (requirements load at startup), then
open the same Codex chat. Record the app version and the bundled
`codex-cli --version`.

| # | Action | Expected |
| --- | --- | --- |
| X1 | Codex applies a patch to the absolute path `/private/tmp/wgp-live/repo/src/app.txt` | Denied by the installed entry: reviewer role does not write |

If X1 shows no installed-entry deny, record "Codex hook not observed active" as
the blocker; do not start another Codex session. Codex reviews from GitHub; its
shell in its own unenrolled workspace is not gated.

## Rollback (any time, in a terminal)

New installation only. Run from any directory; rollback does not use the
development checkout. Each policy-file removal first compares the file with the
root-owned reference copy made at installation; if `cmp` reports a difference
(or the reference is missing), nothing is removed. Stop and inspect by hand,
because the installed file was changed after installation. `rmdir` only removes
empty folders. Remove in this order, Claude Code first; the gate files, including
the references, go last. Removing the file does not prove a running session has
unloaded the hook:

```bash
cmp -s /Library/BardWorkflowGate/installed/claude-managed-settings.fragment.json "/Library/Application Support/ClaudeCode/managed-settings.json" && sudo rm "/Library/Application Support/ClaudeCode/managed-settings.json" && sudo rmdir "/Library/Application Support/ClaudeCode"
```

```bash
cmp -s /Library/BardWorkflowGate/installed/codex-requirements.toml /etc/codex/requirements.toml && sudo rm /etc/codex/requirements.toml && sudo rmdir /etc/codex
```

Gate files, only after both policy files are gone (they hold no one else's settings):

```bash
test ! -e "/Library/Application Support/ClaudeCode/managed-settings.json" && test ! -e /etc/codex/requirements.toml && sudo rm -f /Library/BardWorkflowGate/approvals/evidence.json && sudo rm /Library/BardWorkflowGate/entry.py /Library/BardWorkflowGate/gate.py /Library/BardWorkflowGate/policy.json /Library/BardWorkflowGate/adapters/claude_code.py /Library/BardWorkflowGate/adapters/codex.py /Library/BardWorkflowGate/installed/claude-managed-settings.fragment.json /Library/BardWorkflowGate/installed/codex-requirements.toml && sudo rmdir /Library/BardWorkflowGate/adapters /Library/BardWorkflowGate/approvals /Library/BardWorkflowGate/installed /Library/BardWorkflowGate
```

```bash
sudo -k
```

Then confirm the three `ls -ld` destinations are absent again, fully quit and
reopen both the Claude desktop app and the ChatGPT app, and record that you did.
In each resumed conversation, a harmless read (Claude Read; a Codex file view)
must work: a hook still pointing at the removed entry would exit 2 and block
every call. That shows the removed entry is no longer run; it is not a
vendor-confirmed unload. If an installed entry denies every Claude tool call
(for example, a protection check fails), this rollback is the fix; it does not
depend on Claude.
The disposable `/tmp/wgp-live` folder can be removed afterwards.

## Known gaps (accepted for a practical guard)

- **Crash or timeout fails open.** Claude Code 2.1.284 has no `onFailure: "block"`
  (needs 2.1.295 or later), and Codex continues on a failed hook.
- **Unenrolled shell.** A session started outside an enrolled checkout can change
  enrolled files through its shell; only file-edit tools are checked there.
- **Unhooked routes.** Processes already running or started outside hooked
  calls, Codex `write_stdin`, hosted or specialized tools, tools the runtime
  exempts, and edits made by people or other programs.
- **Check-to-write races.** Links or files changed between check and write.
- **Reviewer identity and approval store.** Approver and writer are labels.
  Independence rests on Kornelis copying a reviewed draft into the root-owned
  store; the gate cannot verify who reviewed it or the `source` link.
- **Administrator rights.** Any administrator, or any process using a cached
  `sudo` credential, can change the store, policy or managed files. Run
  `sudo -k` after each step. MDM would add redeployment, not prevention.
- **Semantics.** Coverage checks are structural; they do not show understanding.
