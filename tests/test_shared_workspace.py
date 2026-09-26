'''Tests for the shared workspace.'''

import unittest

from src.shared_workspace import ConflictError, SharedWorkspace


class SharedWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.ws = SharedWorkspace()
        self.ws.create_section("plan", "step one\nstep two")

    def test_read(self):
        text, version = self.ws.read("plan")
        self.assertEqual(text, "step one\nstep two")
        self.assertEqual(version, 0)

    def test_clean_edit(self):
        v = self.ws.edit("a", "plan", "step one\nstep 2!", 0)
        self.assertEqual(v, 1)
        self.assertEqual(self.ws.read("plan")[0], "step one\nstep 2!")

    def test_rebase_disjoint_lines(self):
        # a edits line 1, b edits line 2 from the same base: mergeable
        self.ws.edit("a", "plan", "STEP ONE\nstep two", 0)
        v = self.ws.edit("b", "plan", "step one\nSTEP TWO", 0)
        self.assertEqual(v, 2)
        self.assertEqual(self.ws.read("plan")[0], "STEP ONE\nSTEP TWO")

    def test_conflict_same_line(self):
        self.ws.edit("a", "plan", "aaa\nstep two", 0)
        with self.assertRaises(ConflictError):
            self.ws.edit("b", "plan", "bbb\nstep two", 0)

    def test_stale_base_only_one_side_changed(self):
        self.ws.edit("a", "plan", "step one\nstep two\nstep three", 0)
        # b's text equals base: keep current
        v = self.ws.edit("b", "plan", "step one\nstep two", 0)
        self.assertEqual(self.ws.read("plan")[0],
                         "step one\nstep two\nstep three")

    def test_presence(self):
        self.ws.enter("a", "plan")
        self.ws.enter("b", "plan")
        self.assertEqual(self.ws.viewers("plan"), ["a", "b"])
        self.ws.leave("a", "plan")
        self.assertEqual(self.ws.viewers("plan"), ["b"])

    def test_undo(self):
        self.ws.edit("a", "plan", "changed", 0)
        self.ws.undo("plan")
        self.assertEqual(self.ws.read("plan")[0], "step one\nstep two")

    def test_undo_no_edits(self):
        self.ws.create_section("empty")
        with self.assertRaises(KeyError):
            self.ws.undo("empty")

    def test_duplicate_section_rejected(self):
        with self.assertRaises(ValueError):
            self.ws.create_section("plan")

    def test_unknown_base_version(self):
        with self.assertRaises(ConflictError):
            self.ws.edit("a", "plan", "x", 99)


if __name__ == "__main__":
    unittest.main()
