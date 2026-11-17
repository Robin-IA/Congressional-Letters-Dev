"""Letter-to-letter notes from vocabulary/letter-related.csv (#1207)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
import build_site  # noqa: E402


def row(digest, subject, ts="20200120113638", key="example.gov/a.pdf", url=""):
    r = [""] * len(build_site.COLUMNS)
    c = build_site.COLUMNS.index
    r[c("key")], r[c("timestamp")], r[c("subject")] = key, ts, subject
    r[c("digest")], r[c("url")] = digest, url
    return r


class RelatedNotes(unittest.TestCase):
    def test_supports_reads_both_ways_and_links_the_pdf(self):
        rows = {"C000127": [row("USGS", "USGS request", key="s.gov/usgs.pdf"),
                            row("CANT", "Cantwell to Pai", ts="20190801000000",
                                key="s.gov/c.pdf", url="https://s.gov/c%20x.pdf")]}
        notes = build_site.related_notes(rows, [("USGS", "CANT", "supports")])
        self.assertEqual(notes["USGS"], [["Supports", "Cantwell to Pai",
                         "https://web.archive.org/web/20190801000000id_/https://s.gov/c%20x.pdf"]])
        self.assertEqual(notes["CANT"], [["Supporting document", "USGS request",
                         "https://web.archive.org/web/20200120113638id_/s.gov/usgs.pdf"]])

    def test_a_missing_end_gives_no_note(self):
        rows = {"C000127": [row("USGS", "USGS request")]}
        self.assertEqual(build_site.related_notes(rows, [("USGS", "GONE", "supports")]), {})


if __name__ == "__main__":
    unittest.main()
