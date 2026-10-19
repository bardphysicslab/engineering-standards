"""Create a disposable checkout and evidence drafts for live gate tests (changes nothing else).

    python3 tools/workflow_gate/install/live_fixture.py NEW_DIR

Creates NEW_DIR/repo (synthetic Git checkout, example.invalid remote),
NEW_DIR/policy.json enrolling exactly that checkout (by its real path), and
NEW_DIR/drafts/*.json. The drafts are proposals: the approver reviews one and
copies it into the protected store with `sudo install` (see README.md). A draft
written here is not an approval until that protected copy is made.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import demo  # noqa: E402

VALID_HOURS = 8


def approval(start_hours, end_hours, approver="codex"):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return {"approver": approver, "source": "https://example.invalid/disposable-fixture#approval",
            "approved_at": (now + dt.timedelta(hours=start_hours)).isoformat(),
            "expires_at": (now + dt.timedelta(hours=end_hours)).isoformat()}


def main(argv):
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 1
    folder = Path(argv[0]).expanduser()
    if folder.exists():
        print(f"{folder} exists; choose a new directory", file=sys.stderr)
        return 1
    folder.mkdir(parents=True)
    root, baseline = demo.make_repo(folder)
    drafts = {
        "valid": {"approval": approval(-1, VALID_HOURS)},
        "self-approved": {"approval": approval(-1, VALID_HOURS, approver="claude")},
        "expired": {"approval": approval(-48, -24)},
        "conflicting": {"approval": approval(-1, VALID_HOURS),
                        "mapping": [{"requirement": "Greeting owner", "status": "conflicting", "question": "Which module owns the greeting?"}]},
    }
    for name, overrides in drafts.items():
        demo.write_json(folder / "drafts" / f"{name}.json", demo.make_evidence(root, baseline, **overrides))
    demo.write_json(folder / "drafts" / "malformed.json", "{not json")
    policy = {"schema": "workflow-gate-policy/1", "enrolled": [str(root.resolve())],
              "roles": {"claude-code": "writer", "codex": "reviewer"}}
    demo.write_json(folder / "policy.json", json.dumps(policy, indent=2) + "\n")
    print(json.dumps({"enroll": str(root.resolve()), "baseline": baseline, "drafts": sorted(p.name for p in (folder / "drafts").iterdir()),
                      "valid_for_hours": VALID_HOURS}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
