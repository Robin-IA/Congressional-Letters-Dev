"""Named laws added from the reading notes (#1324)."""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import topics  # noqa: E402


class LawsTest(unittest.TestCase):
    def test_a_law_also_tags_its_parent(self):
        self.assertEqual(topics.tag("Violence Against Women Act reauthorization")[:2],
                         ["Violence Against Women Act", "Domestic violence"])
        self.assertIn("Taxes", topics.tag("Tax Cuts and Jobs Act"))

    def test_a_law_hides_a_word_it_is_not_about(self):
        self.assertNotIn("Jobs", topics.tag("Tax Cuts and Jobs Act"))

    def test_phrases_with_punctuation_still_match(self):
        self.assertIn("Women, Peace, and Security Act", topics.tag("Women, Peace, and Security Act"))
        self.assertIn("Countering America's Adversaries Through Sanctions Act",
                      topics.tag("Countering America’s Adversaries Through Sanctions Act"))

    def test_every_law_parent_is_a_term_and_placed(self):
        broader = {}
        with (ROOT / "vocabulary/hierarchy.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                broader.setdefault(r["term"], set()).add(r["broader"])
        for law, parents in topics.LAW_PARENTS.items():
            self.assertIn(law, topics.SUBJECTS)
            self.assertIn(parents[0], broader.get(law, set()), law)
            for p in parents:
                self.assertTrue(p in topics.SUBJECTS or p in topics.AGENCIES, (law, p))


if __name__ == "__main__":
    unittest.main()
