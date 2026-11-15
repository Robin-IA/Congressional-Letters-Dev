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


class TestLetterheadDate(unittest.TestCase):
    """The extractor that makes the letterhead a source, not just a check.

    Scored against the 405 day-precision dates read by hand: a date for 355
    of them, agreeing with 352 (99.2%). The cases below are the shapes it
    must read and, more importantly, the ones it must refuse.
    """

    def test_a_plain_letterhead(self):
        self.assertEqual(
            ad.letterhead_date("June 25, 2020 The Honorable Nancy Pelosi "
                               "Speaker Dear Speaker Pelosi: We write"),
            "2020-06-25")

    def test_the_date_may_follow_the_address_block(self):
        self.assertEqual(
            ad.letterhead_date("The Honorable Tom Vilsack Secretary U.S. "
                               "Department of Agriculture October 25, 2011 "
                               "Dear Secretary Vilsack: I am writing"),
            "2011-10-25")

    def test_a_date_after_the_salutation_is_not_a_letterhead(self):
        """A date the letter cites is not the date of the letter."""
        self.assertIsNone(
            ad.letterhead_date("Dear Secretary Azar: We write about the rule "
                               "you signed on May 29, 2020 and have not published"))

    def test_two_different_dates_before_the_salutation_are_refused(self):
        """A Re: line or a hoisted footnote; which is the letterhead is a reader's call."""
        self.assertIsNone(
            ad.letterhead_date("Re: the inauguration of January 20, 2025 "
                               "May 16, 2025 To Whom It May Concern: I pen this"))

    def test_the_same_date_twice_is_still_one_date(self):
        self.assertEqual(
            ad.letterhead_date("March 5, 2024 March 5, 2024 Dear Mr Moynihan, As members"),
            "2024-03-05")

    def test_no_salutation_means_no_letterhead(self):
        self.assertIsNone(
            ad.letterhead_date("November 29, 2023 We write to express our opposition "
                               "to attaching any short-term reauthorization"))

    def test_an_impossible_year_is_refused(self):
        """The FCC letter on cell phones in flight OCRs its 2013 as 2073."""
        self.assertIsNone(
            ad.letterhead_date("December 12, 2073 The Honorable Tom Wheeler "
                               "Dear Chairman Wheeler, We respectfully ask"))

    def test_a_placeholder_day_is_not_a_date(self):
        """18 letters went out with the day unfilled (#180)."""
        self.assertIsNone(
            ad.letterhead_date("August XX, 2017 The Honorable Chuck Grassley "
                               "Dear Chairman Grassley, One of the most important"))

    def test_no_date_at_all(self):
        self.assertIsNone(ad.letterhead_date("Dear Colleague: We are all shocked"))


class TestCaptureGuard(unittest.TestCase):
    """A letter cannot be dated after the capture that holds it."""

    def test_guard(self):
        from build_site import _after
        self.assertTrue(_after("2024-08-01", "20180612000000"))
        self.assertFalse(_after("2018-05-01", "20180612000000"))
        self.assertFalse(_after("2018-06-12", "20180612000000"))
        self.assertFalse(_after("2024-08-01", None))
        self.assertFalse(_after("2024-08-01", "2018"))
