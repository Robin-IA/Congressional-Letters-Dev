"""The hand-kept vocabulary files: every row loads, and every value is one
the build accepts.

These files grow in hourly batches from the PC's reading of the letters
(#128). A row the build rejects -- a topic that does not exist, a date that
is not a date, two titles for one letter -- stops the whole publish, as one
did on 14 November 2026. Checked here, it fails a test instead.

    python3 -m unittest discover -s tests
"""

import csv
import datetime
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))

import build_site  # noqa: E402
import letter_text  # noqa: E402

VOCAB = ROOT / "vocabulary"
DIGEST = re.compile(r"^[A-Z2-7]{32}$")   # base-32 SHA-1, as the CDX gives it
PRECISIONS = {"day", "month", "year"}


def rows(name):
    path = VOCAB / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class ByHand(unittest.TestCase):
    def check_rows(self, name, columns):
        got = rows(name)
        for i, r in enumerate(got, start=2):
            self.assertNotIn(None, r, f"{name} line {i}: more fields than columns (an unquoted comma?)")
            for c in columns:
                self.assertIn(c, r, f"{name}: no column {c!r}")
            self.assertRegex(r["digest"], DIGEST, f"{name} line {i}: not a digest")
        dupes = [d for d, n in Counter(r["digest"] for r in got).items() if n > 1]
        self.assertEqual(dupes, [], f"{name}: a digest listed twice")
        return got

    def test_titles(self):
        for r in self.check_rows("letter-titles.csv", ["digest", "title"]):
            self.assertTrue(r["title"].strip(), f"letter-titles.csv: empty title for {r['digest']}")

    def test_dates(self):
        for r in self.check_rows("letter-dates.csv", ["digest", "date", "precision"]):
            datetime.date.fromisoformat(r["date"])
            self.assertIn(r["precision"] or "day", PRECISIONS, r["digest"])
            # Older letters posted later are kept at their own date (#239,
            # #1284): Coretta Scott King's 1986 letter, re-posted in 2017.
            self.assertTrue(1980 <= int(r["date"][:4]) <= datetime.date.today().year,
                            f"letter-dates.csv: {r['digest']} dated {r['date']}")
        self.assertEqual(len(letter_text.dates_by_hand()), len(rows("letter-dates.csv")))

    def test_topics_are_topics(self):
        self.check_rows("letter-topics.csv", ["digest", "topics"])
        members = letter_text.members_to_file_under()
        for digest, labels in letter_text.topics_by_hand().items():
            unknown = [t for t in labels if t not in build_site.SUBJECTS
                       and t not in letter_text.organizations_to_file_under()
                       and t not in members]
            self.assertEqual(unknown, [], f"letter-topics.csv: {digest}: not a topic")

    def test_recipient_topics_are_topics(self):
        build_site._RECIPIENT_TOPICS = None
        build_site.recipient_topics()      # raises SystemExit on a bad row


if __name__ == "__main__":
    unittest.main()
