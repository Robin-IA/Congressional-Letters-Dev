"""Tests for dating one posting of a letter from another posting of it.

The digest is a hash of the PDF, so two records sharing one are the same
document at two addresses. One member may have put the date in the file name
while the others did not, and the others are then dated by their capture --
an upper bound, not a date.

What matters here is mostly what the rule *refuses* to do. Promoting a date
is cheap and silent, and a wrong one would be indistinguishable from a right
one in the finished site.

    python3 -m unittest discover -s tests
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

from build_site import dates_from_siblings  # noqa: E402


def lines(*records):
    return [json.dumps(r) for r in records]


def posting(digest, date, precision, host="example.senate.gov"):
    return {"digest": digest, "date_best": date, "date_precision": precision,
            "host": host}


class TestPromotes(unittest.TestCase):
    def test_a_capture_takes_a_siblings_file_name_date(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2020-02-14", "day"),
            posting("AAA", "2020-04-18", "captured-by"),
        ))
        self.assertEqual(out["AAA"], ("2020-02-14", "day"))

    def test_a_month_takes_a_siblings_day(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2026-02-06", "day"),
            posting("AAA", "2026-02-01", "month"),
        ))
        self.assertEqual(out["AAA"], ("2026-02-06", "day"))

    def test_several_captures_agree_with_one_good_date(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2020-03-21", "day"),
            posting("AAA", "2020-05-23", "captured-by"),
            posting("AAA", "2024-07-01", "captured-by"),
        ))
        self.assertEqual(out["AAA"], ("2020-03-21", "day"))

    def test_repeated_good_postings_that_agree(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2018-01-25", "day"),
            posting("AAA", "2018-01-25", "day"),
            posting("AAA", "2018-09-19", "captured-by"),
        ))
        self.assertEqual(out["AAA"], ("2018-01-25", "day"))


class TestRefuses(unittest.TestCase):
    def test_good_postings_that_disagree_are_left_alone(self):
        """6,913 letters in the corpus are in this state.

        Two file names claiming different days for one document is a question
        for a reader. Picking one would bury it.
        """
        out = dates_from_siblings(lines(
            posting("AAA", "2018-01-25", "day"),
            posting("AAA", "2018-03-02", "day"),
            posting("AAA", "2018-09-19", "captured-by"),
        ))
        self.assertNotIn("AAA", out)

    def test_nothing_better_than_a_capture(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2020-04-18", "captured-by"),
            posting("AAA", "2021-01-02", "captured-by"),
        ))
        self.assertNotIn("AAA", out)

    def test_a_lone_posting_has_no_sibling(self):
        out = dates_from_siblings(lines(posting("AAA", "2020-02-14", "day")))
        self.assertNotIn("AAA", out)

    def test_nothing_to_promote_when_all_agree_in_precision(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2020-02-14", "day"),
            posting("AAA", "2020-02-14", "day"),
        ))
        self.assertNotIn("AAA", out)

    def test_a_record_with_no_date_is_ignored_not_counted(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2020-02-14", "day"),
            posting("AAA", "", "captured-by"),
        ))
        self.assertNotIn("AAA", out)

    def test_an_unknown_precision_never_wins(self):
        out = dates_from_siblings(lines(
            posting("AAA", "2020-02-14", "something-new"),
            posting("AAA", "2020-04-18", "captured-by"),
        ))
        self.assertNotIn("AAA", out)

    def test_malformed_lines_do_not_stop_the_pass(self):
        out = dates_from_siblings(
            ["{not json", *lines(posting("AAA", "2020-02-14", "day"),
                                 posting("AAA", "2020-04-18", "captured-by"))])
        self.assertEqual(out["AAA"], ("2020-02-14", "day"))


if __name__ == "__main__":
    unittest.main()
