"""Shield phrases in build/topics.py: a phrase containing a topic's word that
is not that topic matches, and tags nothing (14 November 2026)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import topics  # noqa: E402


class Shields(unittest.TestCase):
    def test_new_mexico_is_not_mexico(self):
        self.assertNotIn("Mexico", topics.tag("Texas v. New Mexico water compact"))
        self.assertNotIn("Mexico", topics.tag("New Mexico digital equity act"))
        self.assertIn("Water", topics.tag("New Mexico water rights"))   # other words still tag

    def test_mexican_american_is_not_mexico(self):
        self.assertNotIn("Mexico", topics.tag("Mexican American studies ban"))

    def test_mexico_still_tags_mexico(self):
        self.assertIn("Mexico", topics.tag("US Mexico border travel restrictions"))
        self.assertIn("Mexico", topics.tag("Mexico biotech corn"))

    def test_shields_are_not_topics(self):
        for phrase in topics.SHIELDS:
            self.assertEqual(topics.tag(phrase), [], phrase)


if __name__ == "__main__":
    unittest.main()
