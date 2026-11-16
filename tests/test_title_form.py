"""Hand titles are published as titles: "On ..." in title case (Robin, 16 November 2026)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

from letter_text import title_form  # noqa: E402


class TitleForm(unittest.TestCase):
    def test_on_and_title_case(self):
        self.assertEqual(title_form("Record-high fertilizer prices — to President Biden, 5 April 2022"),
                         "On Record-High Fertilizer Prices — to President Biden, 5 April 2022")

    def test_article_and_acronyms(self):
        self.assertEqual(title_form("The cost of K-12 and H.R. 2987 — to Speaker Johnson, 4 June 2025"),
                         "On the Cost of K-12 and H.R. 2987 — to Speaker Johnson, 4 June 2025")

    def test_idempotent_and_not_our_form(self):
        t = "On Additional Flights — to airline CEOs, 18 December 2025"
        self.assertEqual(title_form(t), t)
        self.assertEqual(title_form("A file-name subject"), "A file-name subject")


if __name__ == "__main__":
    unittest.main()
