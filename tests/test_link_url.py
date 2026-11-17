"""#107: a letter links from the address the archive holds, not from its key."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import build_site  # noqa: E402
from harvest import canonical  # noqa: E402


class LinkUrl(unittest.TestCase):
    def rec(self, url):
        return {"url": url, "key": canonical(url)}

    def test_hex_prefix_keeps_the_observed_url(self):
        url = ("https://smith.house.gov/uploads/0201da8dde9c1cd828dde0ee17facd26."
               "east-waterway-letter-to-epa-january-18-2022.pdf")
        self.assertEqual(build_site.link_url(self.rec(url)), url[len("https://"):])

    def test_forgiven_differences_write_nothing(self):
        # scheme, www, case and percent-encoding the Wayback Machine forgives
        url = "http://www.Cantwell.senate.gov/042310%20Letter_to_Reid.pdf"
        self.assertEqual(build_site.link_url(self.rec(url)), "")

    def test_columns_read_by_position_keep_their_place(self):
        # Scripts read rows by position (row[9] digest, row[10] url, row[11]
        # direction, #175); new columns go at the end.
        self.assertEqual(build_site.COLUMNS[9], "digest")
        self.assertEqual(build_site.COLUMNS[10], "url")
        self.assertEqual(build_site.COLUMNS[11], "direction")


if __name__ == "__main__":
    unittest.main()
