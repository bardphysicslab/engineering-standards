"""Claude Code PreToolUse adapter for the workflow gate PROTOTYPE. NOT INSTALLED.

Derived from the hooks documentation for Claude Code 2.1.284; live compatibility
is unverified. Write targets come from tool_input.file_path (notebook_path for
NotebookEdit). Read, Glob and Grep are allowed; Bash (including background runs),
MCP and every other tool are denied.
"""
import json
import sys
from pathlib import Path

RUNTIME = "Claude Code 2.1.284, doc-derived"
WRITE_TOOLS = {"Write": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}

try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import gate
except Exception as error:  # an import failure must deny, not fail open
    reason = f"workflow gate prototype denied: gate unavailable ({error})"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    print(reason, file=sys.stderr)
    sys.exit(2)


def classify(tool_name, tool_input):
    if tool_name in gate.READ_ONLY_TOOLS:
        return "read", []
    if tool_name in WRITE_TOOLS:
        return "write", [tool_input.get(WRITE_TOOLS[tool_name])]
    if tool_name == "Bash":
        return "shell", []
    if tool_name.startswith("mcp__"):
        return "mcp", []
    return "unknown", []


if __name__ == "__main__":
    sys.exit(gate.run_hook(classify, RUNTIME))
