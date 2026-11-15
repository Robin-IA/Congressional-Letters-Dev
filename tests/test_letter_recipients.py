"""#357: recipients read by hand from a letter's address block, one letter at a time."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))

import letter_text  # noqa: E402
import topics  # noqa: E402


class LetterRecipients(unittest.TestCase):
    def test_reads_digest_to_recipient(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "letter-recipients.csv"
            p.write_text("digest,recipient,source\nAAA,Equifax,x\nBBB,JPMorgan Chase,y\nCCC, ,z\n", encoding="utf-8")
            real = letter_text.RECIPIENTS_BY_HAND
            letter_text.RECIPIENTS_BY_HAND = p
            try:
                self.assertEqual(letter_text.recipients_by_hand(), {"AAA": "Equifax", "BBB": "JPMorgan Chase"})
            finally:
                letter_text.RECIPIENTS_BY_HAND = real

    def test_file_is_well_formed(self):
        rows = list(csv.DictReader((ROOT / "vocabulary" / "letter-recipients.csv").open(encoding="utf-8")))
        digests = [r["digest"] for r in rows]
        self.assertEqual(len(digests), len(set(digests)), "one row per letter")
        for r in rows:
            self.assertRegex(r["digest"], r"^[A-Z2-7]{32}$")
            self.assertTrue(r["recipient"].strip())

    def test_recipient_topics_are_subjects(self):
        for r in csv.DictReader((ROOT / "vocabulary" / "recipient-topics.csv").open(encoding="utf-8")):
            for t in r["topics"].split(";"):
                self.assertIn(t.strip(), topics.SUBJECTS, r["recipient"])


if __name__ == "__main__":
    unittest.main()
