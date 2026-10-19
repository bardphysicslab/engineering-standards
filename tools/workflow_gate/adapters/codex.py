"""Codex PreToolUse adapter for the workflow gate PROTOTYPE. NOT INSTALLED.

Derived from the hooks documentation for Codex 0.163.0-alpha.10.2; live
compatibility is unverified. apply_patch targets are every Add, Update, Delete
and Move-to path in tool_input.command; all are checked. Shell (Bash,
exec_command), MCP and every other tool are denied.
"""
import json
import re
import sys
from pathlib import Path

RUNTIME = "Codex 0.163.0-alpha.10.2, doc-derived"
SHELL_TOOLS = {"Bash", "exec_command", "shell", "local_shell", "write_stdin"}
PATCH_HEADER = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$")

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import gate
except Exception as error:  # an import failure must deny, not fail open
    reason = f"workflow gate prototype denied: gate unavailable ({error})"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    print(reason, file=sys.stderr)
    sys.exit(2)


def patch_targets(patch):
    lines = patch.strip().splitlines() if isinstance(patch, str) else []
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise gate.Denied("apply_patch input is not a complete patch")
    targets = [match.group(1).strip() for match in map(PATCH_HEADER.match, lines) if match]
    if not targets:
        raise gate.Denied("apply_patch names no file")
    return targets


def classify(tool_name, tool_input):
    if tool_name == "apply_patch":
        return "write", patch_targets(tool_input.get("command"))
    if tool_name in SHELL_TOOLS:
        return "shell", []
    if tool_name.startswith("mcp__"):
        return "mcp", []
    return "unknown", []


if __name__ == "__main__":
    sys.exit(gate.run_hook(classify, RUNTIME))
