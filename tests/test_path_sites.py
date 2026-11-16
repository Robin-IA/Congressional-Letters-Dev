"""A path site's rows must be under its own path (#13): Wayback's index drops
the trailing slash, so house.gov/jackson/* also returns house.gov/jacksonlee."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import harvest_paths  # noqa: E402


class OwnPath(unittest.TestCase):
    def test_own_path(self):
        self.assertTrue(harvest_paths.own("house.gov/jackson", {"url": "http://www.house.gov/jackson/a/letter.pdf"}))
        self.assertTrue(harvest_paths.own("house.gov/jackson", {"url": "http://www.house.gov:80/Jackson/letter.htm"}))
        self.assertTrue(harvest_paths.own("senate.gov/~schumer", {"url": "http://www.senate.gov/~schumer/letter.pdf"}))
        self.assertTrue(harvest_paths.own("senate.gov/~schumer", {"url": "http://www.senate.gov/%7Eschumer/letter.pdf"}))

    def test_neighbour_path(self):
        self.assertFalse(harvest_paths.own("house.gov/jackson", {"url": "http://www.house.gov:80/jacksonlee/letters.htm"}))
        self.assertFalse(harvest_paths.own("house.gov/jackson", {"url": "http://www.house.gov:80/jackson_lee/x"}))
        self.assertFalse(harvest_paths.own("house.gov/john", {"url": "http://www.house.gov/johnlewis/pdf/DOJLetteronGA.PDF"}))


if __name__ == "__main__":
    unittest.main()
