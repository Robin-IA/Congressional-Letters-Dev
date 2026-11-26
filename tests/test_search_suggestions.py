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
const a = src.indexOf('const fold = s =>'), b = src.indexOf('function vocabPanel');
const MEMBERS = [{ id: 'S000033', name: 'Bernard Sanders', letters: 4 },
                 { id: 'W000817', name: 'Elizabeth Warren', letters: 9 }];
const api = new Function('MEMBERS', src.slice(a, b)
  + '\nreturn { didYouMean, filedUnder, membersNamed };')(MEMBERS);
const data = JSON.parse(process.argv[2]);
const out = {};
for (const q of JSON.parse(process.argv[3])) {
  const d = api.didYouMean(data, q), f = api.filedUnder(data, q);
  out[q] = { dym: d && d.text, filed: f && f.tag,
             named: api.membersNamed(data, q.toLowerCase()).map(m => m.id) };
}
console.log(JSON.stringify(out));
"""


@unittest.skipUnless(NODE, "node is not installed")
class PageSuggestions(unittest.TestCase):
    """The page's own functions, lifted out of app.js and run under node."""

    def ask(self, *queries):
        rows = [srow("Medicare payments", "Medicare"), srow("Medicare Advantage", "Medicare"),
                srow("Fentanyl at the border", "Opioids"), srow("Covid relief", "COVID-19"),
                srow("Tariffs on steel", "Tariffs")]
        data = {"members": ["S000033"], "recipients": [], "rows": rows,
                "vocab": build_site.search_vocabulary(rows),
                "aka": {"S000033": ["Bernie Sanders"]}}
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

    def test_nickname_finds_the_member(self):
        got = self.ask("bernie sanders", "bernie sandres")
        self.assertEqual(got["bernie sanders"]["named"], ["S000033"])
        self.assertEqual(got["bernie sandres"]["dym"], "Bernie Sanders")


if __name__ == "__main__":
    unittest.main()
