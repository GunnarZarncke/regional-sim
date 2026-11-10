"""Scoped freeze flags must not be confused with the full world freeze bar."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "VERSION.json").read_text())
DOC = (ROOT / "docs/scoped_world_freeze.md").read_text()


class ScopedWorldFreeze(unittest.TestCase):
    def test_claim_boundary_flags(self):
        self.assertTrue(VERSION["scoped_world_freeze_met"])
        self.assertFalse(VERSION["world_freeze_bar_met"])
        self.assertFalse(VERSION["independent_empirical_validation_passed"])
        self.assertTrue(VERSION["parameters_frozen"])
        self.assertEqual(VERSION["scoped_world_freeze_record"], "docs/scoped_world_freeze.md")

    def test_declaration_exists_and_refuses_full_bar(self):
        self.assertIn("world_freeze_bar_met", DOC)
        self.assertIn("false", DOC)
        self.assertIn("Do not retune Fix I-5", DOC)
