"""Letters that belong together (#1289), with no OCR store or explorers."""
import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build/mac"))
sys.path.insert(0, str(ROOT / "build"))
import find_linked_letters as f  # noqa: E402
import build_site  # noqa: E402


def corpus(posts, texts):
    """A Corpus built by hand: posts = {digest: [(member, file, capture, date, subject)]}."""
    c = f.Corpus.__new__(f.Corpus)
    c.members, c.posts, c.dates, c.text, c.by_member = ({}, {}, {}, {}, {})
    from collections import defaultdict
    c.members, c.posts, c.by_member = defaultdict(set), defaultdict(list), defaultdict(set)
    for d, ps in posts.items():
        for member, file, capture, when, subject in ps:
            c.add_post(d, member, {"file": file, "capture": capture, "date": when,
                                   "recipient": "x", "subject": subject})
    c.text = texts
    return c


class Dates(unittest.TestCase):
    def test_the_forms_letters_use(self):
        for s in ["March 3, 2019", "3 March 2019", "Mar. 3rd, 2019", "3/3/19", "03/03/2019"]:
            self.assertEqual(f.parse_date(s), date(2019, 3, 3), s)
        self.assertEqual(f.parse_date("Sept. 17, 2014"), date(2014, 9, 17))
        self.assertIsNone(f.parse_date("June 31, 2019"))
        self.assertIn("march 3, 2019", f.date_forms(date(2019, 3, 3)))
        self.assertIn("3/3/19", f.date_forms(date(2019, 3, 3)))


class References(unittest.TestCase):
    def test_whose_letter_and_when(self):
        got = {(w, d) for w, d, _ in f.references(
            "I write to follow up on my letter of March 3, 2019 regarding the center. "
            "Thank you for your letter dated June 5, 2018. On September 17, 2014, we wrote to you. "
            "Our previous letter to Administrator Pruitt on 7/16/2019 asked the same.")}
        self.assertEqual(got, {("own", date(2019, 3, 3)), ("theirs", date(2018, 6, 5)),
                               ("own", date(2014, 9, 17)), ("own", date(2019, 7, 16))})

    def test_a_date_alone_is_not_a_reference(self):
        self.assertEqual(f.references("The hearing on March 3, 2019 showed the program works."), [])
        self.assertEqual(f.references("The newsletter of March 3, 2019."), [])

    def test_a_reference_finds_the_members_letter_of_that_date(self):
        c = corpus({"LATER": [("M1", "a.gov/2.pdf", "20190601000000", "2019-05-20", "Follow-up")],
                    "EARLY": [("M1", "a.gov/1.pdf", "20190401000000", "2019-03-04", "First")],
                    "OTHER": [("M2", "b.gov/1.pdf", "20190401000000", "2019-03-03", "Someone else's")]},
                   {"LATER": "As noted in my letter of March 3, 2019, the delays continue."})
        got = f.reference_candidates("LATER", c, skip=set(), linked=set())
        self.assertEqual([(r["candidate"], r["relation"], r["digest"], r["related"]) for r in got],
                         [("EARLY", "follows_up", "LATER", "EARLY")])   # a day off; not M2's
        self.assertEqual(f.reference_candidates("LATER", c, skip=set(), linked={("LATER", "EARLY")}), [])

    def test_a_reply_supports_the_letter_it_answers(self):
        c = corpus({"REPLY": [("M1", "a.gov/r.pdf", "20181101000000", "2018-10-03", "State's reply")],
                    "ASK": [("M1", "a.gov/a.pdf", "20180920000000", "2018-09-17", "Our letter")]},
                   {"REPLY": "Thank you for your letter of September 17, 2018 about the center."})
        got = f.reference_candidates("REPLY", c, skip=set(), linked=set())
        self.assertEqual((got[0]["digest"], got[0]["related"], got[0]["relation"]),
                         ("REPLY", "ASK", "supports"))


class Discards(unittest.TestCase):
    DISCARD = {"digest": "USGS", "title": "Spectrum sharing — USGS Director to Chairman Pai, 21 June 2019"}

    def test_the_selection_is_test2_without_the_citation_search(self):
        rows = [{"reason": "test 2, no relation to Congress: agency to agency"},
                {"reason": "test 2, no relation to Congress: … No letter by the posting members cites it (searched their OCR)."},
                {"reason": "test 1, not a letter: a memo; no relation to Congress"},
                {"reason": "Not a letter by, to, or about a member of Congress"},
                {"reason": "duplicate: a second copy of X"}]
        self.assertEqual(f.unsearched_test2(rows), [rows[0], rows[3]])
        self.assertEqual(f.unsearched_test2(rows, everyone=True), [rows[0], rows[1], rows[3]])

    def test_a_letter_citing_it_or_posted_beside_it_is_a_candidate(self):
        c = corpus({"USGS": [("C000127", "s.gov/files/usgs.pdf", "20190801000000", "", "USGS")],
                    "CANT": [("C000127", "s.gov/files/cantwell.pdf", "20190805000000", "2019-07-16", "To Pai")],
                    "CITES": [("C000127", "s.gov/other/x.pdf", "20200101000000", "2019-08-01", "Cites it")],
                    "UNRELATED": [("C000127", "s.gov/other/y.pdf", "20200101000000", "2019-08-02", "Wheat")]},
                   {"CANT": "", "CITES": "the USGS director's spectrum sharing request of june 21, 2019",
                    "UNRELATED": "wheat prices"})
        got = {r["letter"]: r["evidence"] for r in f.discard_candidates(self.DISCARD, c, skip=set())}
        self.assertIn("posted beside it", got["CANT"])
        self.assertIn("mentions 2019-06-21", got["CITES"])
        self.assertNotIn("UNRELATED", got)


class Apply(unittest.TestCase):
    def test_apply_links_and_returns_the_discard_to_the_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            related, discards, confirmed = tmp / "related.csv", tmp / "discards.csv", tmp / "c.csv"
            related.write_text("digest,related,relation,note\n", encoding="utf-8")
            discards.write_text("digest,title,reason,issue,decided,posted_by,wayback_url\n"
                                "USGS,USGS letter,test 2,1,x,Cantwell,u\nKEEP,Other,test 2,1,x,Y,u\n",
                                encoding="utf-8")
            with confirmed.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["discard", "discard_title", "letter", "letter_title",
                                                   "member", "evidence", "score", "relation", "confirm"])
                w.writeheader()
                w.writerow({"discard": "USGS", "discard_title": "USGS letter", "letter": "CANT",
                            "letter_title": "Cantwell to Pai", "member": "C000127",
                            "evidence": "posted beside it", "score": 1, "relation": "supports", "confirm": "yes"})
                w.writerow({"discard": "KEEP", "discard_title": "Other", "letter": "Z", "letter_title": "z",
                            "member": "Y", "evidence": "names x", "score": 1, "relation": "supports", "confirm": "no"})
            f.RELATED, f.DISCARDS = related, discards
            f.cmd_apply(confirmed, "1289")
            links = list(csv.DictReader(related.open(encoding="utf-8")))
            self.assertEqual([(l["digest"], l["related"], l["relation"]) for l in links],
                             [("USGS", "CANT", "supports")])
            self.assertIn("#1289", links[0]["note"])
            self.assertEqual([r["digest"] for r in csv.DictReader(discards.open(encoding="utf-8"))], ["KEEP"])
            f.cmd_apply(confirmed, "1289")             # again: no duplicate link
            self.assertEqual(len(list(csv.DictReader(related.open(encoding="utf-8")))), 1)

    def tearDown(self):
        f.RELATED, f.DISCARDS = ROOT / "vocabulary/letter-related.csv", ROOT / "letters-discarded/letters.csv"


class FollowsUpLabel(unittest.TestCase):
    def test_follows_up_reads_both_ways(self):
        def row(digest, subject):
            r = [""] * len(build_site.COLUMNS)
            c = build_site.COLUMNS.index
            r[c("key")], r[c("timestamp")], r[c("subject")], r[c("digest")] = "a.gov/x.pdf", "20200101000000", subject, digest
            return r
        notes = build_site.related_notes({"M": [row("LATER", "Second"), row("EARLY", "First")]},
                                         [("LATER", "EARLY", "follows_up")])
        self.assertEqual(notes["LATER"][0][:2], ["Follows up", "First"])
        self.assertEqual(notes["EARLY"][0][:2], ["Followed up by", "Second"])


if __name__ == "__main__":
    unittest.main()
