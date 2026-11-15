"""Tests for the date audit: what counts as a date, and where a letterhead sits.

The audit exists because the first pass over the letters took the first date
in each one as its letterhead. That is right most of the time. The cases below
are the ones it was wrong about, taken from real letters in the corpus, and
each is here so the audit does not quietly lose them again.

    python3 -m unittest discover -s tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import audit_dates as ad  # noqa: E402


class TestDatesFound(unittest.TestCase):
    def isos(self, text):
        return [iso for _, iso, _ in ad.found(text)]

    def test_ordinary_forms(self):
        self.assertEqual(self.isos("June 25, 2020"), ["2020-06-25"])
        self.assertEqual(self.isos("Jan. 12, 2023"), ["2023-01-12"])
        self.assertEqual(self.isos("12 January 2023"), ["2023-01-12"])
        self.assertEqual(self.isos("11/26/2024"), ["2024-11-26"])

    def test_ordinals(self):
        self.assertEqual(self.isos("March 30th, 2022"), ["2022-03-30"])
        self.assertEqual(self.isos("January 2nd 2023"), ["2023-01-02"])

    def test_ocr_runs_the_words_together(self):
        """Tesseract drops the spaces on some scans, and the date is still a date.

        "July17,2020" is the letterhead of the missing and murdered Indigenous
        women letter; a pattern requiring whitespace reported that letter as
        carrying no date at all.
        """
        self.assertEqual(self.isos("July17,2020"), ["2020-07-17"])
        self.assertEqual(self.isos("TheHonorableNancyPelosi July17,2020 Dear"),
                         ["2020-07-17"])

    def test_ocr_reads_a_one_as_an_l(self):
        """"Aprill5,2019" is April 15 2019 with the 1 read as an l.

        The month pattern's trailing letters absorb the stray l, which leaves
        "5" as the day -- so the audit sees April 5 where the letter says April
        15. That is a parse the audit cannot win, and the point of the test is
        that it still finds *a* date there rather than reporting none, so the
        letter is flagged for a reader instead of passing silently.
        """
        self.assertTrue(self.isos("Aprill5,2019"))

    def test_junk_is_not_a_date(self):
        self.assertEqual(self.isos("H.R. 6201 and S. 4008"), [])
        self.assertEqual(self.isos("Washington, DC 20510"), [])
        self.assertEqual(self.isos("13/45/2020"), [])

    def test_position_is_reported(self):
        pos, iso, _ = ad.found("xxxxx June 25, 2020")[0]
        self.assertEqual((pos, iso), (6, "2020-06-25"))


class TestSalutation(unittest.TestCase):
    def cut(self, text):
        m = ad.SALUTE.search(text)
        return m.start() if m else None

    def test_dear(self):
        self.assertIsNotNone(self.cut("June 25, 2020 ... Dear Speaker Pelosi,"))

    def test_letters_that_do_not_say_dear(self):
        """Three real openings that a /Dear/ test misses.

        Missing the salutation puts the whole body in front of the cut, and
        every date the letter cites then looks like a competing letterhead.
        """
        self.assertIsNotNone(self.cut("January 12, 2023 Senator Chuck Schumer "
                                      "Majority Leader Leader Schumer: I urge you"))
        self.assertIsNotNone(self.cut("April 15, 2021 Honorable Nancy Pelosi "
                                      "Speaker Pelosi, Nearly eight months"))
        self.assertIsNotNone(self.cut("Re: My Reason To Whom It May Concern: I pen"))

    def test_an_address_block_is_not_a_salutation(self):
        block = ("The Honorable Roy Blunt Chairman, Subcommittee on Labor, "
                 "Health and Human Services United States Senate Washington, "
                 "D.C. 20510 Dear Chairman Blunt:")
        self.assertEqual(self.cut(block), block.index("Dear"))


class TestWeekdayCrossCheck(unittest.TestCase):
    def test_the_weekday_dates_the_letter(self):
        """7 January was a Tuesday in 2025 and a Sunday in 2024.

        The Eaton fire letter is headed 12 January 2024 and says the fires
        began "Tuesday, January 7th", which settles the year without anyone
        needing to know when the fires were.
        """
        self.assertEqual(ad.weekdays("on Tuesday, January 7th, a series of fires"),
                         [("Tuesday", 1, 7, "Tuesday, January 7th")])

    def test_no_weekday(self):
        self.assertEqual(ad.weekdays("on January 7th a series of fires"), [])


if __name__ == "__main__":
    unittest.main()
