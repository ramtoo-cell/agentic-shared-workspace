# Shared Workspace for Agent Collaboration

Shared document workspace for agents: operational-transform-style concurrent edits, version history, presence, and conflict-free merge of text sections.

**Stack:** Python 3.12 · stdlib only · unittest

## Problem statement

Agents co-edit a document split into named sections.  Concurrency is handled with per-section versioning: an edit carries the base version the agent saw; if the section moved on, the edit is rebased when it touches different lines (line-level three-way merge) or rejected as a conflict.

## Design decisions

- Agents co-edit a document split into named sections.
- Concurrency is handled with per-section versioning: an edit carries the base version the agent saw; if the section moved on, the edit is rebased when it touches different lines (line-level three-way merge) or rejected as a conflict.
- Presence tracks which agents are viewing/editing which sections, and history keeps every applied edit for audit and undo.

## Usage example

```python
from src.shared_workspace import SharedWorkspace

ws = SharedWorkspace()
ws.create_section("plan", "step one")
ws.edit("planner", "plan", "step one\nstep two", 0)
print(ws.read("plan"))  # ('step one\nstep two', 1)
```

## Layout

- `README.md`
- `src/shared_workspace.py`
- `tests/test_shared_workspace.py`
- `LICENSE`
- `.gitignore`

## Setup

No third-party dependencies — Python 3.11+ standard library only.

```bash
cd agentic-shared-workspace
python -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
