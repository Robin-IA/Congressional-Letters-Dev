"""Companies are topics, not recipients (filed_orgs.py; Robin, 15 November 2026)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import filed_orgs  # noqa: E402


class FiledOrgs(unittest.TestCase):
    def test_a_ceo_resolves_to_the_company_and_is_not_shown(self):
        self.assertEqual(filed_orgs.companies_for("Mr. Bastian", 2020), (["Delta Air Lines"], True))

    def test_several_companies_at_once(self):
        orgs, only = filed_orgs.companies_for("Apple And Google", 2019)
        self.assertEqual(sorted(orgs), ["Apple", "Google"])
        self.assertTrue(only)

    def test_a_split_applies_only_in_its_years(self):
        self.assertEqual(filed_orgs.companies_for("Musk", 2023), (["Twitter (X)"], True))
        self.assertEqual(filed_orgs.companies_for("Musk", 2022), ([], False))

    def test_government_recipients_stay(self):
        self.assertEqual(filed_orgs.companies_for("Chairman Crapo", 2019), ([], False))
        self.assertEqual(filed_orgs.companies_for(None, 2019), ([], False))

    def test_no_government_body_is_a_company(self):
        names = filed_orgs.nongov_labels()
        for gov in ("Department of Defense", "Senate Committee on Finance", "The Administration"):
            self.assertNotIn(gov, names)

    def test_tag_has_no_comma(self):
        self.assertEqual(filed_orgs.tag_of("American Academy of Allergy, Asthma & Immunology"),
                         "American Academy of Allergy Asthma & Immunology")


if __name__ == "__main__":
    unittest.main()
