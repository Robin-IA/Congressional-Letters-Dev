"""State and local government is arranged by state, then by city (#1421).

The vocabulary browser lists each level alphabetically, so a city filed straight
under "State and local government" sits among the fifty states instead of under
its own. These tests keep every place under its state's chain:

    State and local government
      State of X
        X state officials
        X agencies and organizations
          X state government agencies
          X local government and agencies
          X organizations
"""
import csv
import functools
import re
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = "State and local government"

# What may sit directly under the top: bodies of no one state, the territories
# (not yet arranged; see #1421), and two terms that are two places at once.
NOT_ONE_STATE = {
    "National Governors Association", "State attorneys general", "Public facilities",
    "Interstate Commission for Adult Offender Supervision", "Great Lakes Commission",
    "State SNAP Agencies", "District of Columbia", "Commonwealth of the Northern Mariana Islands",
    "Governor of Guam", "Governor of the U.S. Virgin Islands", "Governor of Puerto Rico",
    "Puerto Rico Institute of Statistics", "Puerto Rico Department of Correction and Rehabilitation",
    "President of the Senate of Puerto Rico", "Speaker of the House of Representatives of Puerto Rico",
    # Letters from Oregon and from Maine; Ohio and Washington. One term each,
    # so it cannot go under one state until it is split (#1421).
    "City of Portland", "Adams County Board of Commissioners",
}

LEVEL = re.compile(r"^(?P<st>.+?) (state officials|agencies and organizations|state government "
                   r"agencies|local government and agencies|organizations)$")


@functools.lru_cache(maxsize=None)
def _hierarchy():
    with (ROOT / "vocabulary/hierarchy.csv").open(encoding="utf-8") as fh:
        return tuple(csv.DictReader(fh))


def hierarchy():
    return _hierarchy()


def accepted_reviews():
    with (ROOT / "vocabulary/reviews.csv").open(encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)
                if r["status"] == "accepted" and r["broader"]
                and r["decision"] not in ("hold", "reject")]


@functools.lru_cache(maxsize=None)
def states():
    """The places that have a "State of" node, plus D.C., which has its own chain."""
    found = {r["term"][len("State of "):] for r in hierarchy() if r["term"].startswith("State of ")}
    return found | {"District of Columbia"}


def level(node):
    """The state a level node is for ("Ohio local government and agencies"), or None."""
    m = LEVEL.match(node or "")
    return m["st"] if m and m["st"] in states() else None


class StateAndLocal(unittest.TestCase):
    def test_only_states_and_multi_state_bodies_sit_at_the_top(self):
        loose = sorted(r["term"] for r in hierarchy()
                       if r["broader"] == TOP and not r["term"].startswith("State of ")
                       and r["term"] not in NOT_ONE_STATE)
        self.assertEqual(loose, [], "file these under their state's chain, not under "
                                    f"{TOP!r} (#1421)")

    def test_reviews_do_not_put_a_place_back_at_the_top(self):
        # A review's broader is applied on top of hierarchy.csv, so a city
        # placed under its state there would also show at the top.
        loose = sorted(r["target"] for r in accepted_reviews()
                       if r["broader"] == TOP and not r["target"].startswith("State of ")
                       and r["target"] not in NOT_ONE_STATE)
        self.assertEqual(loose, [])

    def test_reviews_agree_with_hierarchy_under_a_state(self):
        placed = defaultdict(set)
        for r in hierarchy():
            placed[r["term"]].add(r["broader"])
        for r in accepted_reviews():
            if level(r["broader"]) and r["target"] in placed:
                self.assertIn(r["broader"], placed[r["target"]], r["target"])

    def test_every_level_reaches_its_state(self):
        up = {}
        for r in hierarchy():
            up.setdefault(r["term"], r["broader"])
        for node in up:
            st = level(node)
            if not st or st == "District of Columbia":
                continue
            seen, n = [], node
            while n in up and n != TOP and n not in seen:
                seen.append(n)
                n = up[n]
            self.assertIn(f"State of {st}", seen + [n], node)

    def test_the_cases_the_letters_settled(self):
        # Each from the letters, not the name: the names alone mislead.
        placed = {r["term"]: r["broader"] for r in hierarchy()}
        self.assertEqual(placed["Scipio Town"], "Utah local government and agencies")
        self.assertEqual(placed["City of Elkins"], "Arkansas local government and agencies")
        self.assertEqual(placed["City of Birmingham"], "Alabama local government and agencies")
        self.assertEqual(placed["City of Portsmouth"], "Ohio local government and agencies")
        self.assertEqual(placed["Garfield County Commissioners"], "Montana local government and agencies")


if __name__ == "__main__":
    unittest.main()
