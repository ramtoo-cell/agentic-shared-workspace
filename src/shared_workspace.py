'''Shared document workspace for collaborating agents.

Agents co-edit a document split into named sections.  Concurrency is
handled with per-section versioning: an edit carries the base version
the agent saw; if the section moved on, the edit is rebased when it
touches different lines (line-level three-way merge) or rejected as a
conflict.

Presence tracks which agents are viewing/editing which sections, and
history keeps every applied edit for audit and undo.
'''

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Edit:
    agent: str
    section: str
    base_version: int
    new_text: str
    applied_version: int = 0


class ConflictError(Exception):
    '''Raised when an edit cannot be rebased cleanly.'''


class SharedWorkspace:
    '''Sectioned document with versioned concurrent edits.'''

    def __init__(self):
        self.sections = {}  # name -> {"text": str, "version": int}
        self.history = []
        self.presence = {}  # agent -> set of sections
        self.initial_text = {}  # section -> text at creation

    def create_section(self, name, text=""):
        if name in self.sections:
            raise ValueError(f"section exists: {name}")
        self.sections[name] = {"text": text, "version": 0}
        self.initial_text[name] = text

    def read(self, section):
        entry = self.sections[section]
        return entry["text"], entry["version"]

    def enter(self, agent, section):
        self.presence.setdefault(agent, set()).add(section)

    def leave(self, agent, section):
        self.presence.get(agent, set()).discard(section)

    def viewers(self, section):
        return sorted(a for a, s in self.presence.items() if section in s)

    def edit(self, agent, section, new_text, base_version):
        '''Apply an edit; rebase or raise ConflictError.'''
        entry = self.sections[section]
        if base_version == entry["version"]:
            return self._apply(agent, section, new_text)
        merged = self._rebase(entry["text"], new_text, agent, section,
                              base_version)
        return self._apply(agent, section, merged)

    def _apply(self, agent, section, new_text):
        entry = self.sections[section]
        entry["text"] = new_text
        entry["version"] += 1
        edit = Edit(agent, section, entry["version"] - 1, new_text,
                    entry["version"])
        self.history.append(edit)
        return entry["version"]

    def _rebase(self, current, new_text, agent, section, base_version):
        # find the base text from history
        base = None
        for edit in self.history:
            if edit.section == section and edit.applied_version == base_version:
                base = edit.new_text
                break
        if base is None and base_version == 0:
            base = self.initial_text.get(section, "")
        if base is None:
            raise ConflictError(f"{agent}: unknown base version")
        base_lines, cur_lines, new_lines = (base.splitlines(),
                                            current.splitlines(),
                                            new_text.splitlines())
        # line-level three-way merge: lines changed on both sides conflict
        if len(base_lines) != len(cur_lines) or len(base_lines) != len(
                new_lines):
            # different line counts: accept when only one side changed
            if cur_lines == base_lines:
                return new_text
            if new_lines == base_lines:
                return current
            raise ConflictError(f"{agent}: concurrent edits conflict")
        merged = []
        for b, c, n in zip(base_lines, cur_lines, new_lines):
            if c == n:
                merged.append(c)
            elif b == c:
                merged.append(n)
            elif b == n:
                merged.append(c)
            else:
                raise ConflictError(f"{agent}: line conflict: {c!r} vs {n!r}")
        return "\n".join(merged)

    def undo(self, section):
        '''Revert the last edit to a section.'''
        for edit in reversed(self.history):
            if edit.section == section:
                entry = self.sections[section]
                prev = self.initial_text.get(section, "")
                for e in reversed(self.history):
                    if (e.section == section
                            and e.applied_version < edit.applied_version):
                        prev = e.new_text
                        break
                entry["text"] = prev
                entry["version"] += 1
                return entry["version"]
        raise KeyError(f"no edits for section: {section}")
