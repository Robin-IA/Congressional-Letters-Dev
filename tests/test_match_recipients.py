"""#97: unreviewed recipient names matched to reviewed ones by rule."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import match_recipients as mr  # noqa: E402

REVIEWS = [
    {"candidate": "Director Redfield", "decision": "officeholder", "target": "Centers for Disease Control",
     "kind": "", "broader": "", "status": "accepted"},
    {"candidate": "Secretary Thompson", "decision": "officeholder", "target": "Department of Health and Human Services",
     "kind": "", "broader": "", "status": "accepted"},
    {"candidate": "Chairwoman Granger and Ranking Member DeLauro", "decision": "merge",
     "target": "House Committee on Appropriations", "kind": "", "broader": "", "status": "accepted"},
    {"candidate": "Secretary Blinken", "decision": "officeholder", "target": "Department of State",
     "kind": "", "broader": "", "status": "accepted"},
]
ROSTER = {("Senate", "boxer"): {"B000711"}, ("House", "smith"): {"S000522", "S000583"},
          ("House", "thompson"): {"T000193"}}
MEMBERS = {"B000711", "S000522", "S000583", "T000193"}


def m(label):
    r = mr.match(label, mr.index(REVIEWS), MEMBERS, ROSTER)
    return r[0][:2] if r else None


class Match(unittest.TestCase):
    def test_same_title_and_surname(self):
        self.assertEqual(m("Acting Director Redfield"), ("officeholder", "Centers for Disease Control"))

    def test_honorific_needs_a_unique_non_member_surname(self):
        self.assertEqual(m("Dr. Redfield"), ("officeholder", "Centers for Disease Control"))
        self.assertIsNone(m("Mr. Thompson"))        # a member's surname too
        self.assertIsNone(m("Redfield"))            # bare surname

    def test_same_people_other_spelling(self):
        self.assertEqual(m("Charwoman Granger And Ranking Member DeLauro"),
                         ("merge", "House Committee on Appropriations"))

    def test_each_part_resolved(self):
        self.assertEqual(m("Secretary Blinken and Director Redfield"),
                         ("joint", "Department of State;Centers for Disease Control"))
        self.assertIsNone(m("Secretary Blinken and Secretary Nobody"))

    def test_member_by_title_only_when_unique(self):
        self.assertEqual(m("Senator Boxer"), ("member", "B000711"))
        self.assertIsNone(m("Congressman Smith"))

    def test_rank_is_part_of_the_office(self):
        self.assertIsNone(m("Assistant Secretary Blinken"))
        self.assertIsNone(m("Under Secretary Thompson"))

    def test_title_alone_is_no_one(self):
        self.assertIsNone(m("Mr. Chairman"))


if __name__ == "__main__":
    unittest.main()
