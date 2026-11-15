"""What counts as done in build/progress.py (Robin, 14 November 2026)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import progress  # noqa: E402

D = "A" * 32


def status(**kw):
    args = {"chars": {D: 500}, "ocr": set(), "reviewed": {D: {"title": "yes", "date": "yes"}},
            "titles": {D: "Industry funding — to American Diabetes Association"},
            "dates": set(), "topics": "Health care"}
    args.update(kw)
    topics = args.pop("topics")
    return progress.status(D, topics, **args)


class TitleForm(unittest.TestCase):
    def test_subject_dash_whom(self):
        self.assertTrue(progress.title_in_form("Industry funding — to American Diabetes Association"))
        self.assertTrue(progress.title_in_form("Blue slips — Dianne Feinstein to Chuck Grassley"))

    def test_not_in_form(self):
        self.assertFalse(progress.title_in_form("Title 32 extension"))
        self.assertFalse(progress.title_in_form("Industry funding - to ADA"))   # a hyphen, not the em dash
        self.assertFalse(progress.title_in_form(" — to the Speaker"))           # no subject
        self.assertFalse(progress.title_in_form(""))


class Done(unittest.TestCase):
    def test_all_steps_is_done(self):
        self.assertTrue(status()["done"])

    def test_each_step_is_needed(self):
        self.assertFalse(status(chars={D: 50})["done"])                       # no usable text
        self.assertFalse(status(reviewed={})["done"])                          # not reviewed
        self.assertFalse(status(reviewed={D: {"title": "", "date": "yes"}})["done"])
        self.assertFalse(status(titles={D: "Title 32 extension"})["done"])     # title not in form
        self.assertFalse(status(reviewed={D: {"title": "yes", "date": ""}})["done"])
        self.assertFalse(status(topics="")["done"])                           # no subjects

    def test_date_settled_by_reading_or_by_review(self):
        self.assertTrue(status(reviewed={D: {"title": "yes", "date": "unchanged"}})["date_settled"])
        self.assertTrue(status(reviewed={D: {"title": "yes", "date": ""}}, dates={D})["date_settled"])
        self.assertFalse(status(reviewed={D: {"title": "yes", "date": ""}})["date_settled"])


class Filed(unittest.TestCase):
    TERMS = {progress.name_key("Department of Justice"): "preferred",
             progress.name_key("Ambassadors"): "candidate"}

    def test_states(self):
        self.assertEqual(progress.filing("Department of Justice", self.TERMS), "filed")
        self.assertEqual(progress.filing("department of justice", self.TERMS), "filed")
        self.assertEqual(progress.filing("Ambassadors", self.TERMS), "not yet reviewed")
        self.assertEqual(progress.filing("Some Rare Name", self.TERMS), "no term")
        self.assertEqual(progress.filing("", self.TERMS), "no recipient")
        self.assertEqual(progress.filing(None, self.TERMS), "no recipient")

    def test_unreviewed_is_not_done(self):
        # Robin: anything in Not yet reviewed is not complete.
        self.assertFalse(status(filed="not yet reviewed")["done"])
        self.assertFalse(status(filed="no recipient")["done"])
        self.assertTrue(status(filed="filed")["done"])


class ReviewedNames(unittest.TestCase):
    """A name decided in reviews.csv as an office holder, a member or a split is filed."""

    def test_officeholder_and_member_names_are_filed(self):
        terms = {"terms.csv": [{"term_id": "O-dod", "label": "Department of Defense", "status": "preferred"},
                               {"term_id": "M-G000386", "label": "Chuck Grassley", "status": "preferred"},
                               {"term_id": "U-x", "label": "Thompson", "status": "candidate"}],
                 "relations.csv": [{"term_id": "O-dod", "relation": "officeHolderName", "value": "Hagel"},
                                   {"term_id": "O-dod", "relation": "officeHolderName", "value": "Wheeler (2018-2021)"},
                                   {"term_id": "M-G000386", "relation": "recipientName", "value": "Grassley"},
                                   {"term_id": "O-dod", "relation": "broader", "value": "Executive"}]}
        real = progress.read_csv
        progress.read_csv = lambda name: terms.get(name, [])
        try:
            t = progress.recipient_terms()
        finally:
            progress.read_csv = real
        self.assertEqual(progress.filing("Hagel", t), "filed")
        self.assertEqual(progress.filing("Wheeler", t), "filed")
        self.assertEqual(progress.filing("Grassley", t), "filed")
        self.assertEqual(progress.filing("Thompson", t), "not yet reviewed")
        self.assertEqual(progress.filing("Executive", t), "no term")


if __name__ == "__main__":
    unittest.main()
