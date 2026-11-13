"""The member's website as the harvests key it, and its Wayback record (#79)."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import build_congress as bc  # noqa: E402


class SiteAddresses(unittest.TestCase):
    def test_host(self):
        self.assertEqual(bc.site_addresses("https://www.pelosi.house.gov/"),
                         ["pelosi.house.gov"])

    def test_host_with_a_path_is_the_host(self):
        # A domain search covers every path on the host.
        self.assertEqual(bc.site_addresses("https://www.flake.senate.gov/public"),
                         ["flake.senate.gov"])

    def test_shared_hosts_keep_the_first_path_segment(self):
        self.assertEqual(bc.site_addresses("https://www.house.gov/Waxman/index.htm"),
                         ["house.gov/waxman"])
        self.assertEqual(bc.site_addresses("https://www.senate.gov/~stevens/"),
                         ["senate.gov/~stevens"])

    def test_two_sites(self):
        self.assertEqual(
            bc.site_addresses("https://shelby.senate.gov | https://www.senate.gov/~shelby"),
            ["shelby.senate.gov", "senate.gov/~shelby"])

    def test_empty(self):
        self.assertEqual(bc.site_addresses(""), [])


class WaybackRecord(unittest.TestCase):
    def test_reads_days_and_keeps_only_wayback_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "congress106-wayback.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                w = csv.DictWriter(handle, fieldnames=[
                    "bioguide_id", "days_captured", "wayback_first",
                    "wayback_last", "lookup"])
                w.writeheader()
                w.writerow({"bioguide_id": "A", "days_captured": "16", "lookup": "found",
                            "wayback_first": "https://web.archive.org/web/19990127/x/",
                            "wayback_last": "javascript:alert(1)"})
                w.writerow({"bioguide_id": "B", "days_captured": "", "lookup": "none in window",
                            "wayback_first": "", "wayback_last": ""})
                w.writerow({"bioguide_id": "C", "days_captured": "", "lookup": "no URL in roster",
                            "wayback_first": "", "wayback_last": ""})
            saved = bc.WAYBACK_LOOKUPS
            bc.WAYBACK_LOOKUPS = Path(tmp)
            try:
                got = bc.wayback_record(106)
            finally:
                bc.WAYBACK_LOOKUPS = saved
        self.assertEqual(got["A"], {"days": 16,
                                    "first": "https://web.archive.org/web/19990127/x/"})
        self.assertEqual(got["B"], {"days": 0})
        self.assertNotIn("C", got)


if __name__ == "__main__":
    unittest.main()
