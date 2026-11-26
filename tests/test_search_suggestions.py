"""Did-you-mean and vocabulary suggestions on the search page (#1449)."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import build_site  # noqa: E402


def srow(subject, topics="", recipient=-1):
    return [0, recipient, 2025, 0, subject, 1, topics]


class SearchVocabulary(unittest.TestCase):
    def setUp(self):
        self.rows = [srow("Covid relief", "COVID-19"), srow("Vaccine supply", "Vaccines"),
                     srow("Water rule", "EPA"), srow("Masks", "COVID-19,Public health")]
        self.vocab = {e[0]: e for e in build_site.search_vocabulary(self.rows)}

    def test_only_tags_the_rows_carry(self):
        self.assertEqual(set(self.vocab), {"COVID-19", "Vaccines", "EPA", "Public health"})

    def test_forms_come_from_the_tables_that_tagged_the_letters(self):
        self.assertIn("coronavirus", self.vocab["COVID-19"][2])
        self.assertIn("environmental protection agency", self.vocab["EPA"][2])

    def test_a_form_never_repeats_the_tag(self):
        for tag, _, forms, _ in self.vocab.values():
            self.assertNotIn(tag.lower(), [f.lower() for f in forms])

    def test_abbreviation_carries_the_full_name(self):
        self.assertEqual(self.vocab["EPA"][1], "Environmental Protection Agency")

    def test_broader_is_kept_only_when_it_is_a_tag_here(self):
        self.assertEqual(self.vocab["COVID-19"][3], "Public health")
        rows = [srow("Covid relief", "COVID-19")]
        self.assertEqual(build_site.search_vocabulary(rows)[0][3], "")

    def test_office_holders_are_not_names_for_the_agency(self):
        # "regan" is a person first; a search for him is not a search for EPA.
        self.assertNotIn("regan", self.vocab["EPA"][2])


class MemberNames(unittest.TestCase):
    def test_nickname_from_congress_legislators(self):
        self.assertIn("Bernie Sanders", build_site.member_names(["S000033"]).get("S000033", []))

    def test_only_the_members_asked_for(self):
        self.assertEqual(set(build_site.member_names(["S000033"])), {"S000033"})


NODE = shutil.which("node")
HARNESS = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const a = src.indexOf('const fold = s =>'), b = src.indexOf('async function viewSearch');
const MEMBERS = [{ id: 'S000033', name: 'Bernard Sanders', letters: 4 },
                 { id: 'W000817', name: 'Elizabeth Warren', letters: 9 }];
const api = new Function('MEMBERS', src.slice(a, b)
  + '\nreturn { didYouMean, filedUnder, membersNamed, acronymOf };')(MEMBERS);
const data = JSON.parse(process.argv[2]);
const out = {};
for (const q of JSON.parse(process.argv[3])) {
  const d = api.didYouMean(data, q), f = api.filedUnder(data, q);
  const acro = api.acronymOf(data, q);
  out[q] = { dym: d && d.text, filed: f && f.tag,
             named: api.membersNamed(data, q.toLowerCase()).map(m => m.id),
             means: acro && acro.list.map(m => m.meaning),
             ranks: acro && data.rows.map(r => acro.rank(r[4], '', r[6] || '')) };
}
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(NODE, "node is not installed")
class PageSuggestions(unittest.TestCase):
    """The page's own functions, lifted out of app.js and run under node."""

    def ask(self, *queries):
        rows = [srow("Medicare payments", "Medicare"), srow("Medicare Advantage", "Medicare"),
                srow("Fentanyl at the border", "Opioids"), srow("Covid relief", "COVID-19"),
                srow("Tariffs on steel", "Tariffs"),
                # 5-9: the acronym cases (#1448)
                srow("Justice for detainees", "ICE"), srow("Postal service delays"),
                srow("Immigration and Customs Enforcement raids"),
                srow("AI in hiring"), srow("Said the senator about aid")]
        data = {"members": ["S000033"], "recipients": [], "rows": rows,
                "vocab": build_site.search_vocabulary(rows),
                "aka": {"S000033": ["Bernie Sanders"]},
                "acronyms": build_site.search_acronyms(rows, [])}
        res = subprocess.run(
            [NODE, "-e", HARNESS, str(ROOT / "app.js"), json.dumps(data), json.dumps(queries)],
            capture_output=True, text=True, check=True)
        return json.loads(res.stdout)

    def test_typos(self):
        got = self.ask("medicaire", "fentynal", "tarrifs", "elizebeth warren")
        self.assertEqual(got["medicaire"]["dym"], "Medicare")
        self.assertEqual(got["fentynal"]["dym"].lower(), "fentanyl")
        self.assertEqual(got["tarrifs"]["dym"], "Tariffs")
        self.assertEqual(got["elizebeth warren"]["dym"], "Elizabeth Warren")

    def test_no_suggestion_for_what_is_already_right_or_hopeless(self):
        got = self.ask("medicare", "qwertyuiop", "ice")
        self.assertIsNone(got["medicare"]["dym"])
        self.assertIsNone(got["qwertyuiop"]["dym"])
        self.assertIsNone(got["ice"]["dym"])   # too short to guess at

    def test_a_variant_names_its_tag(self):
        got = self.ask("coronavirus", "pandemic", "fentanyl")
        self.assertEqual(got["coronavirus"]["filed"], "COVID-19")
        self.assertEqual(got["pandemic"]["filed"], "COVID-19")
        self.assertEqual(got["fentanyl"]["filed"], "Opioids")

    def test_an_acronym_says_what_it_stands_for(self):
        got = self.ask("ice", "ICE", "ai", "medicare")
        self.assertEqual(got["ice"]["means"], ["Immigration and Customs Enforcement"])
        self.assertEqual(got["ICE"]["means"], got["ice"]["means"])
        self.assertEqual(got["ai"]["means"], ["artificial intelligence"])
        self.assertIsNone(got["medicare"]["means"])   # not an acronym

    def test_letters_using_the_acronym_rank_before_letters_containing_it(self):
        ice = self.ask("ice")["ice"]["ranks"]
        self.assertEqual(ice[5], 0)   # tagged ICE (and "justice" does not matter)
        self.assertEqual(ice[7], 1)   # spelled out
        self.assertEqual(ice[6], 2)   # "service" only contains it
        ai = self.ask("ai")["ai"]["ranks"]
        self.assertEqual(ai[8], 1)    # "AI in hiring"
        self.assertEqual(ai[9], 2)    # "said", "aid"

    def test_nickname_finds_the_member(self):
        got = self.ask("bernie sanders", "bernie sandres")
        self.assertEqual(got["bernie sanders"]["named"], ["S000033"])
        self.assertEqual(got["bernie sandres"]["dym"], "Bernie Sanders")


class SearchAcronyms(unittest.TestCase):
    def setUp(self):
        self.rows = [srow("AI in hiring"), srow("Super intelligence risks, SI"),
                     srow("Detention", "ICE"), srow("Postal service")]
        self.acr = build_site.search_acronyms(self.rows, [])

    def test_hand_kept_ai_and_si(self):
        # Robin, #1448: AI is artificial intelligence, SI superintelligence.
        self.assertEqual(self.acr["AI"][0][0], "artificial intelligence")
        self.assertEqual(self.acr["SI"][0][0], "superintelligence")
        self.assertIn("super intelligence", self.acr["SI"][0][2])

    def test_agency_acronym_carries_its_tag(self):
        meaning, tag, forms = self.acr["ICE"][0]
        self.assertEqual((meaning, tag), ("Immigration and Customs Enforcement", "ICE"))
        self.assertIn("immigration and customs enforcement", forms)

    def test_one_meaning_per_tag(self):
        acr = build_site.search_acronyms([srow("x", "DHS")], [])
        self.assertEqual(len(acr["DHS"]), 1)

    def test_only_acronyms_this_congress_uses(self):
        self.assertNotIn("FEMA", self.acr)

    def test_hand_file_tags_must_be_topics(self):
        with open(build_site.VOCABULARY / "acronyms.csv", newline="", encoding="utf-8") as fh:
            import csv
            for r in csv.DictReader(fh):
                if r["tag"]:
                    self.assertTrue(r["tag"] in build_site.SUBJECTS or r["tag"] in build_site.AGENCIES,
                                    r["tag"])
if __name__ == "__main__":
    unittest.main()
