"""The reading rule (Robin, 20 November 2026): 1-2 pages whole; longer letters
read to 75%, first and last pages always whole."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from reading_view import pages, reading_view  # noqa: E402


class ReadingView(unittest.TestCase):
    def test_two_pages_whole(self):
        v = reading_view("A" * 3000 + "\f" + "B" * 3000)
        self.assertFalse(v["cut"])
        self.assertEqual(v["read_chars"], 6000)

    def test_long_letter_first_last_whole_and_75_percent(self):
        ps = ["FIRST" * 200, "M2" * 500, "M3" * 500, "M4" * 500, "LAST" * 250]  # 1000 chars each
        v = reading_view("\f".join(ps))
        self.assertTrue(v["cut"])
        self.assertEqual(v["read_chars"], 3750)
        self.assertTrue(v["text"].startswith(ps[0]))
        self.assertTrue(v["text"].endswith(ps[-1]))
        self.assertIn(ps[1], v["text"])
        self.assertIn("M3" * 375, v["text"])
        self.assertNotIn("M4", v["text"])
        self.assertIn("omitted", v["text"])

    def test_big_first_and_last_pages_still_whole(self):
        ps = ["F" * 5000, "m" * 100, "L" * 5000]
        v = reading_view("\f".join(ps))
        self.assertIn("F" * 5000, v["text"])
        self.assertIn("L" * 5000, v["text"])
        self.assertNotIn("m", v["text"].replace("omitted", ""))

    def test_text_layer_pages_by_length(self):
        t = ("word " * 19 + "\n") * 200  # 20,000 characters, no form feeds
        ps = pages(t)
        self.assertEqual(sum(len(p) for p in ps), len(t))
        self.assertTrue(all(len(p) <= 2500 for p in ps))
        v = reading_view(t)
        self.assertTrue(v["cut"])
        self.assertAlmostEqual(v["read_chars"] / len(t), 0.75, delta=0.01)

    def test_short_text_layer_whole(self):
        v = reading_view("Dear Secretary,\n" * 100)
        self.assertFalse(v["cut"])


if __name__ == "__main__":
    unittest.main()
