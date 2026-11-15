"""#349: a salutation naming the posting member by title and surname is a letter to them."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

from build_site import poster_if_named as p  # noqa: E402


class Poster(unittest.TestCase):
    def test_own_surname(self):
        self.assertEqual(p("Congressman Smith", "Christopher H. Smith"), "Christopher H. Smith")
        self.assertEqual(p("Senator Nelson", "Ben Nelson"), "Ben Nelson")
        self.assertEqual(p("Rep. Scott", 'Robert C. "Bobby" Scott'), 'Robert C. "Bobby" Scott')
        self.assertEqual(p("Congressman Payne", "Donald M. Payne, Jr."), "Donald M. Payne, Jr.")

    def test_not_the_poster(self):
        self.assertEqual(p("Congressman Smith", "Carolyn B. Maloney"), "")
        self.assertEqual(p("Secretary Smith", "Adam Smith"), "")          # not a member's title
        self.assertEqual(p("Chairman Cole and Ranking Member DeLauro", "Tom Cole"), "")


if __name__ == "__main__":
    unittest.main()
