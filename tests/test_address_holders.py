"""Tests for step 3: who held each address, and when.

Built from the real rosters and step 2 lookups, not fixtures: the cases are
the addresses METHODOLOGY.md names, and what matters is that the committed
data gives them the right holders.

    python3 -m unittest discover -s tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

from address_holders import (  # noqa: E402
    address_key,
    attribute,
    build,
    index,
    lookup_rows,
    overlaps,
    roster_rows,
)

HOLDINGS = build(roster_rows(), lookup_rows())
IDX = index(HOLDINGS)

TIM_MURPHY, STEPHANIE_MURPHY, GREG_MURPHY = "M001151", "M001202", "M001210"
ROGERS_MI, ROGERS_AL = "R000572", "R000575"
MENENDEZ, ROB_MENENDEZ = "M000639", "M001226"
PAYNE, PAYNE_JR = "P000149", "P000604"
ROBERT_MATSUI, DORIS_MATSUI = "M000249", "M001163"
JOHN_DINGELL, DEBBIE_DINGELL = "D000355", "D000624"


def who(url, date="", first_capture=""):
    a = attribute(IDX, url, date, first_capture)
    return a.bioguide_id, a.attribution


class AddressKey(unittest.TestCase):
    def test_host_without_www(self):
        self.assertEqual(address_key("https://www.kennedy.senate.gov/public"), "kennedy.senate.gov")
        self.assertEqual(address_key("http://kennedy.senate.gov:80/"), "kennedy.senate.gov")

    def test_shared_hosts_keep_the_members_path(self):
        self.assertEqual(address_key("https://www.house.gov/matsui"), "house.gov/matsui")
        self.assertEqual(address_key("https://wwwc.house.gov/regula"), "wwwc.house.gov/regula")
        self.assertEqual(address_key("https://www.senate.gov/~chafee"), "senate.gov/~chafee")

    def test_senate_holding_pages_keep_the_filename(self):
        self.assertEqual(address_key("https://www.senate.gov/senators/carper.html"),
                         "senate.gov/senators/carper.html")

    def test_a_letters_url_keys_to_its_site(self):
        self.assertEqual(address_key("https://www.house.gov/matsui/pr/letter.pdf"), "house.gov/matsui")
        self.assertEqual(address_key("https://murphy.house.gov/uploadedfiles/x.pdf"), "murphy.house.gov")


class Table(unittest.TestCase):
    def test_no_two_members_hold_an_address_at_once(self):
        self.assertEqual(overlaps(HOLDINGS), [])

    def test_murphy_has_three_holders_in_order(self):
        hs = IDX["murphy.house.gov"]
        self.assertEqual([h.bioguide_id for h in hs], [TIM_MURPHY, STEPHANIE_MURPHY, GREG_MURPHY])
        self.assertEqual({h.holders for h in hs}, {3})
        self.assertEqual((hs[1].before, hs[1].after), (TIM_MURPHY, GREG_MURPHY))

    def test_greg_murphy_holds_only_from_2023(self):
        # serving since 2019, but at gregmurphy.house.gov until 2023
        greg = [h for h in IDX["murphy.house.gov"] if h.bioguide_id == GREG_MURPHY]
        self.assertEqual(greg[0].held_from, "2023-01-03")

    def test_a_chamber_switch_cuts_both_spans(self):
        house = [h for h in IDX["menendez.house.gov"] if h.bioguide_id == MENENDEZ][0]
        senate = IDX["menendez.senate.gov"][0]
        self.assertEqual(house.held_to, "2006-01-18")
        self.assertEqual(house.chamber, "House")
        self.assertEqual(senate.held_from, "2006-01-18")


class Attribute(unittest.TestCase):
    def test_murphy(self):
        self.assertEqual(who("https://murphy.house.gov/a.pdf", "2010-05-01"), (TIM_MURPHY, "holder"))
        self.assertEqual(who("https://murphy.house.gov/a.pdf", "2020-05-01"), (STEPHANIE_MURPHY, "holder"))
        self.assertEqual(who("https://murphy.house.gov/a.pdf", "2024-05-01"), (GREG_MURPHY, "holder"))
        # Tim Murphy resigned 2017-10-21; Stephanie Murphy arrived 2019-01-03
        self.assertEqual(who("https://murphy.house.gov/a.pdf", "2018-05-01"), (TIM_MURPHY, "after_service"))

    def test_mikerogers_same_name_two_people(self):
        self.assertEqual(who("https://mikerogers.house.gov/x.pdf", "2013-06-01"), (ROGERS_MI, "holder"))
        self.assertEqual(who("https://mikerogers.house.gov/x.pdf", "2016-06-01"), (ROGERS_AL, "holder"))

    def test_menendez_father_and_son(self):
        self.assertEqual(who("https://menendez.house.gov/x.pdf", "2004-06-01"), (MENENDEZ, "holder"))
        self.assertEqual(who("https://menendez.house.gov/x.pdf", "2024-06-01"), (ROB_MENENDEZ, "holder"))
        # after he moved to the Senate, the House site is in the gap
        self.assertEqual(who("https://menendez.house.gov/x.pdf", "2006-06-01"), (MENENDEZ, "after_service"))

    def test_payne_same_seat_with_a_gap(self):
        # Donald Payne died 2012-03-06; Payne Jr. sworn in 2012-11-15
        self.assertEqual(who("https://payne.house.gov/x.pdf", "2011-06-01"), (PAYNE, "holder"))
        self.assertEqual(who("https://payne.house.gov/x.pdf", "2012-06-01"), (PAYNE, "after_service"))
        self.assertEqual(who("https://payne.house.gov/x.pdf", "2013-06-01"), (PAYNE_JR, "holder"))

    def test_matsui_same_seat_with_a_gap(self):
        url = "https://www.house.gov/matsui/x.pdf"
        self.assertEqual(who(url, "2004-06-01"), (ROBERT_MATSUI, "holder"))
        self.assertEqual(who(url, "2005-02-01"), (ROBERT_MATSUI, "after_service"))
        self.assertEqual(who(url, "2005-04-01"), (DORIS_MATSUI, "holder"))

    def test_a_redirect_is_not_followed(self):
        # dingell.house.gov redirects to debbiedingell.house.gov, another member's site
        self.assertEqual(who("https://dingell.house.gov/x.pdf", "2014-06-01"), (JOHN_DINGELL, "holder"))
        self.assertEqual(who("https://dingell.house.gov/x.pdf", "2016-06-01"), ("", "none"))
        self.assertEqual(who("https://debbiedingell.house.gov/x.pdf", "2016-06-01"),
                         (DEBBIE_DINGELL, "holder"))

    def test_before_the_first_holder_is_none(self):
        # Tim Murphy was not yet in Congress in 2001
        self.assertEqual(who("https://murphy.house.gov/a.pdf", "2001-05-01"), ("", "none"))

    def test_a_letter_from_the_holders_earlier_office(self):
        # Tammy Baldwin was in the House until 2013; baldwin.senate.gov is hers from 2013
        self.assertEqual(who("https://www.baldwin.senate.gov/a.pdf", "2010-06-06"),
                         ("B001230", "earlier_office"))
        # Tom Cole served from 2003; the rosters give him cole.house.gov from 2011
        self.assertEqual(who("https://cole.house.gov/a.pdf", "2007-11-01"), ("C001053", "earlier_office"))

    def test_unknown_address_or_no_date_is_none(self):
        self.assertEqual(who("https://nobody.house.gov/a.pdf", "2010-05-01"), ("", "none"))
        self.assertEqual(who("https://murphy.house.gov/a.pdf"), ("", "none"))

    def test_dated_by_capture_is_flagged_only_where_shared(self):
        a = attribute(IDX, "https://murphy.house.gov/a.pdf", first_capture="20200115083000")
        self.assertEqual((a.bioguide_id, a.by_capture), (STEPHANIE_MURPHY, True))
        b = attribute(IDX, "https://debbiedingell.house.gov/a.pdf", first_capture="20200115083000")
        self.assertEqual((b.bioguide_id, b.by_capture), (DEBBIE_DINGELL, False))
        c = attribute(IDX, "https://murphy.house.gov/a.pdf", "2020-05-01", "20200115083000")
        self.assertFalse(c.by_capture)

    def test_a_gap_while_still_in_office_is_not_after_service(self):
        # Ed Pastor served 1991-2015; the source gives pastor.house.gov only in
        # the 110th and 113th, www.house.gov/pastor in between
        self.assertEqual(who("https://pastor.house.gov/x.pdf", "2010-06-01"), ("P000099", "holder"))
        # Carol Shea-Porter really was out of office 2011-2013
        self.assertEqual(who("https://shea-porter.house.gov/x.pdf", "2012-06-01"),
                         ("S001170", "after_service"))

    def test_the_day_a_seat_changes_hands_goes_to_the_incoming_holder(self):
        self.assertEqual(who("https://murphy.house.gov/a.pdf", "2023-01-03"), (GREG_MURPHY, "holder"))


if __name__ == "__main__":
    unittest.main()
