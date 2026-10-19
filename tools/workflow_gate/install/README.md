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
| `live_fixture.py` | Creates a disposable checkout and evidence drafts for live tests |

Tests: `python3 -m unittest discover -s tests -p 'test_workflow_gate*.py'`.

## Supported installation path

This Mac has no MDM enrollment and no existing managed Claude Code or Codex
policy. The vendor-supported route without MDM is the system file for each
runtime, written by an administrator:

- Claude Code reads `/Library/Application Support/ClaudeCode/managed-settings.json`
  at startup and reloads it when it changes, so running sessions are affected.
  `/status` should list `Enterprise managed settings (file)`.
- Codex reads `/etc/codex/requirements.toml` at startup. Managed hooks are trusted
  by policy, so no per-hook trust review is needed; restart the ChatGPT app.

An installer script was refused as self-modification, so these are manual steps.

## Install (Kornelis, after review of commit `C`)

Run from the canonical engineering-standards checkout, clean at `C`. Stop if any
check differs.

```bash
git status --porcelain && git rev-parse HEAD
```

The first command must print nothing; the second must print `C`.

```bash
ls -ld "/Library/Application Support/ClaudeCode" /etc/codex /Library/BardWorkflowGate
```

All three must be absent. If either policy file exists, merge the one hook
group by hand instead.

```bash
python3 tools/workflow_gate/install/live_fixture.py /tmp/wgp-live
```

The output's `enroll` path is `ENROLL`.

```bash
sed "s#/absolute/path/to/disposable/fixture/repo#ENROLL#" tools/workflow_gate/install/policy.example.json > /tmp/wgp-policy.json
```

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
sudo /usr/bin/install -o root -g wheel -m 0644 /tmp/wgp-policy.json /Library/BardWorkflowGate/policy.json
```

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 /etc/codex
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 tools/workflow_gate/install/codex-requirements.toml /etc/codex/requirements.toml
```

Claude Code last, because running sessions pick it up at once:

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 "/Library/Application Support/ClaudeCode"
```

```bash
sudo /usr/bin/install -o root -g wheel -m 0644 tools/workflow_gate/install/claude-managed-settings.fragment.json "/Library/Application Support/ClaudeCode/managed-settings.json"
```

```bash
sudo -k
```

Verify that the installed copies match the reviewed files and the policy names
only `ENROLL`:

```bash
for f in gate.py adapters/claude_code.py adapters/codex.py; do cmp tools/workflow_gate/$f /Library/BardWorkflowGate/$f; done; cmp tools/workflow_gate/install/entry.py /Library/BardWorkflowGate/entry.py; cat /Library/BardWorkflowGate/policy.json
```

## Live tests

Start a new Claude Code session in `ENROLL` and check `/status`; restart the
ChatGPT app and open `ENROLL` in Codex. Record each runtime version and setting
source with the outcomes. Keep private paths and session IDs in private notes.

| # | Action | Expected |
| --- | --- | --- |
| L1 | Claude edits `src/app.txt` | Denied: no write evidence |
| L2 | Kornelis: `sudo /usr/bin/install -o root -g wheel -m 0644 /tmp/wgp-live/drafts/valid.json /Library/BardWorkflowGate/approvals/evidence.json && sudo -k`; Claude edits `src/app.txt`, then `docs/guide.md` | Allowed; then denied: outside the approved scope |
| L3 | Claude writes `.claude/settings.json`; runs a Bash command; calls an MCP tool | Each denied |
| L4 | Install `self-approved`, `expired`, `conflicting`, `malformed` drafts in turn; Claude edits `src/app.txt` | Each denied with its reason |
| L5 | Codex `apply_patch` and a shell command in `ENROLL` | Denied: reviewer role; shell |
| L6 | Claude session outside `ENROLL`: Bash command; Write to a file in `ENROLL` | Bash allowed (known gap); Write denied |

Codex cannot read through its shell in an enrolled checkout, so it reviews from
GitHub or an unenrolled clone.

## Rollback (any time, in a terminal)

These remove only what the steps above created; they assume the policy files
were absent before. Claude Code first, which deactivates it in running sessions:

```bash
sudo rm "/Library/Application Support/ClaudeCode/managed-settings.json" && sudo rmdir "/Library/Application Support/ClaudeCode"
```

```bash
sudo rm /etc/codex/requirements.toml && sudo rmdir /etc/codex
```

```bash
sudo rm -f /Library/BardWorkflowGate/approvals/evidence.json && sudo rm /Library/BardWorkflowGate/entry.py /Library/BardWorkflowGate/gate.py /Library/BardWorkflowGate/policy.json /Library/BardWorkflowGate/adapters/claude_code.py /Library/BardWorkflowGate/adapters/codex.py && sudo rmdir /Library/BardWorkflowGate/adapters /Library/BardWorkflowGate/approvals /Library/BardWorkflowGate
```

```bash
sudo -k
```

Then restart the ChatGPT app. If an installed entry denies every Claude tool
call (for example, a protection check fails), this rollback is the fix; it does
not depend on Claude.

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
