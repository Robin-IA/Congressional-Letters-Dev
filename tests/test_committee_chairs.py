"""#364: data/committee-chairs.csv is well formed."""
import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Chairs(unittest.TestCase):
    def test_rows(self):
        rows = list(csv.DictReader((ROOT / "data" / "committee-chairs.csv").open(encoding="utf-8")))
        self.assertTrue(rows)
        labels = {r["label"] for r in csv.DictReader((ROOT / "vocabulary" / "terms.csv").open(encoding="utf-8"))}
        for r in rows:
            self.assertIn(r["chamber"], ("Senate", "House"))
            self.assertRegex(r["bioguide"], r"^[A-Z]\d{6}$", r)
            self.assertTrue(106 <= int(r["congress"]) <= 119)
            self.assertTrue(r["committee"].startswith(r["chamber"] + " Committee on")
                            or r["committee"] == "Committee on House Administration", r["committee"])

    def test_murkowski_chaired_energy(self):
        rows = list(csv.DictReader((ROOT / "data" / "committee-chairs.csv").open(encoding="utf-8")))
        got = {r["congress"] for r in rows if r["bioguide"] == "M001153"
               and r["committee"] == "Senate Committee on Energy and Natural Resources"}
        self.assertEqual(got, {"114", "115", "116"})

    def test_house_ways_and_means(self):
        rows = list(csv.DictReader((ROOT / "data" / "committee-chairs.csv").open(encoding="utf-8")))
        got = {r["congress"]: r["bioguide"] for r in rows
               if r["committee"] == "House Committee on Ways and Means"}
        self.assertEqual(got["115"], "B000755")   # Kevin Brady
        self.assertEqual(got["117"], "N000015")   # Richard E. Neal


if __name__ == "__main__":
    unittest.main()
