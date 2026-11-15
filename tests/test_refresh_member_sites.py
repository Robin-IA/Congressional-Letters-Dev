"""in_explorer in data/member-sites.tsv follows what is published, not only the first roster."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import refresh_member_sites as rms  # noqa: E402

TSV = ("host\tchamber\tbioguide\tfirst_year\tlast_year\tyears_listed\tin_explorer\n"
       "abraham.house.gov\thouse\t\t2016\t2021\t6\tno\n"
       "www.house.gov/akin\thouse\t\t2001\t2007\t7\tno\n"
       "pelosi.house.gov\thouse\t\t2000\t2024\t25\tyes\n"
       "cao.house.gov\thouse\t\t2010\t2020\t11\tno\n")


class Refresh(unittest.TestCase):
    def test_published_sites_use_member_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "A000374.json"
            p.write_text(json.dumps([["abraham.house.gov/uploads/letter.pdf"] + [""] * 9,
                                     ["www.house.gov/akin/pdf/x.pdf"] + [""] * 9]))
            self.assertEqual(rms.published_sites(str(Path(d) / "*.json")),
                             {"abraham.house.gov", "house.gov/akin"})

    def test_refresh_marks_published_and_roster_sites(self):
        lines = TSV.splitlines(keepends=True)
        out, changed = rms.refresh(lines, {"abraham.house.gov", "house.gov/akin", "pelosi.house.gov"})
        cols = [line.rstrip("\n").split("\t")[-1] for line in out[1:]]
        self.assertEqual(cols, ["yes", "yes", "yes", "no"])
        self.assertEqual(changed, 2)
        self.assertEqual(out[0], lines[0])
        # every other column is untouched
        self.assertEqual([l.split("\t")[:6] for l in out[1:]], [l.split("\t")[:6] for l in lines[1:]])


if __name__ == "__main__":
    unittest.main()
