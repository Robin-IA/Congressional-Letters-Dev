"""The 105th subdomain check (#1386), without touching the Wayback Machine."""
import sys
import unittest
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import check_105_subdomains as c  # noqa: E402


def row(host, why="guess", early=0, late=0, status="ok", letterish=0):
    return {"host": host, "why": why, "status": status, "captures_1997_98": str(early),
            "letterish_1997_98": str(letterish), "captures_1999": str(late)}


class Names(unittest.TestCase):
    def test_stems(self):
        self.assertEqual(c.stems_of("David Bonior"), ["bonior", "davidbonior"])
        self.assertEqual(c.stems_of("Eshoo"), ["eshoo"])              # one word: no "eshooeshoo"
        self.assertEqual(c.stems_of("Luis V. Gutiérrez"), ["gutierrez", "luisgutierrez"])
        self.assertIn("moseley-braun", c.stems_of("Carol Moseley Braun"))
        self.assertIn("moseleybraun", c.stems_of("Carol Moseley Braun"))
        self.assertIn("roslehtinen", c.stems_of("Ileana Ros-Lehtinen"))
        self.assertEqual(c.name_parts('Robert C. "Bobby" Scott')[1], "scott")
        self.assertEqual(c.name_parts("Frank Pallone, Jr.")[1], "pallone")

    def test_candidates_put_the_directory_first_and_say_when_it_was_seen(self):
        m = {"name": "David Bonior", "chamber": "House"}
        holders = [{"address": "davidbonior.house.gov", "first_capture": "1999-01-25"}]
        got = c.candidates(m, holders, [])
        self.assertEqual(got[0], ("davidbonior.house.gov", "directory, first seen 1999-01"))
        self.assertIn(("www-bonior.house.gov", "guess, as www-eshoo"), got)

    def test_a_directory_path_is_asked_as_a_path(self):
        m = {"name": "W. Weldon", "chamber": "House"}
        holders = [{"address": "house.gov/curtweldon", "first_capture": "1999-02-01"}]
        got = c.candidates(m, holders, ["Curt Weldon"])
        self.assertEqual(got[0][0], "house.gov/curtweldon/")
        self.assertIn("curtweldon.house.gov", [t for t, _ in got])   # from the other name

    def test_senators_get_senate_hosts(self):
        got = [t for t, _ in c.candidates({"name": "Carol Moseley Braun", "chamber": "Senate"}, [], [])]
        self.assertTrue(all(t.endswith(".senate.gov") for t in got))


class Queries(unittest.TestCase):
    def test_host_and_path_queries(self):
        host = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(c.query("bonior.house.gov")).query))
        self.assertEqual(host["matchType"], "host")     # domain timed out in #1330
        self.assertTrue(c.query("x").startswith("https://"))   # http answers 503 (CLAUDE.md)
        path = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(c.query("house.gov/pitts/")).query))
        self.assertEqual((path["matchType"], path["url"]), ("prefix", "house.gov/pitts/"))
        self.assertNotIn("*", path["url"])               # no wildcard with prefix

    def test_summarize_splits_the_years_and_finds_letter_names(self):
        body = "\n".join([
            "http://armey.house.gov/letters/reno.htm 19970610000000 text/html",
            "http://armey.house.gov/index.htm 19981101000000 text/html",
            "http://armey.house.gov/newsletter.htm 19980101000000 text/html",
            "http://armey.house.gov/index.htm 19990301000000 text/html",
        ])
        got = c.summarize(body)
        self.assertEqual((got["captures_1997_98"], got["letterish_1997_98"], got["captures_1999"]), (3, 1, 1))
        self.assertEqual(got["first_capture"], "19970610000000")
        self.assertEqual(c.summarize("")["captures_1997_98"], 0)


class Verdicts(unittest.TestCase):
    """Robin's rule: Wayback first; if nothing passes and the subdomain looks
    used, note it for 20thcenturyweb."""

    def test_wayback_when_1997_98_captures_exist(self):
        v = c.verdict_for([row("armey.house.gov", early=170, letterish=3), row("www-armey.house.gov")])
        self.assertTrue(v.startswith("Wayback: armey.house.gov (170 URLs"), v)

    def test_20thcenturyweb_when_used_by_1999_but_not_captured_earlier(self):
        v = c.verdict_for([row("davidbonior.house.gov", "directory, first seen 1999-01"),
                           row("bonior.house.gov")])
        self.assertTrue(v.startswith("20thcenturyweb: davidbonior.house.gov"), v)
        v = c.verdict_for([row("x.house.gov", late=12)])
        self.assertTrue(v.startswith("20thcenturyweb"), v)

    def test_a_later_directory_address_is_not_evidence(self):
        v = c.verdict_for([row("eshoo.house.gov", "directory, first seen 2005-01")])
        self.assertEqual(v, "no site found in Wayback for 1997-98")

    def test_a_path_in_1999_is_not_a_subdomain(self):
        v = c.verdict_for([row("house.gov/aderholt/", "directory, first seen 1999-03, path", late=40)])
        self.assertEqual(v, "no site found in Wayback for 1997-98")

    def test_a_failed_query_is_retried_not_judged(self):
        v = c.verdict_for([row("x.house.gov", status="error: 503")])
        self.assertEqual(v, "retry: a query failed")


class Plan(unittest.TestCase):
    def test_the_plan_covers_the_members_the_paths_missed_and_the_control(self):
        todo = c.plan(everyone=False)
        ids = {m["bioguide_id"] for m, _, _ in todo}
        self.assertIn(c.CONTROL, ids)
        self.assertIn("B000619", ids)        # Bonior
        self.assertIn("E000215", ids)        # Eshoo
        self.assertEqual(len(ids), 80)       # 79 missed, plus Armey


if __name__ == "__main__":
    unittest.main()
