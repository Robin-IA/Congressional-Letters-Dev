"""#122: a text layer holding U+FFFD loses to clean OCR, and is queued for OCR."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import build_search  # noqa: E402
import ocr_letters  # noqa: E402

BAD = "Nydia M. Vel�zquez United States Representative " * 5
GOOD = "Nydia M. Velázquez United States Representative " * 4


class DamagedTextLayer(unittest.TestCase):
    def test_search_prefers_clean_ocr_over_a_longer_damaged_layer(self):
        with tempfile.TemporaryDirectory() as d:
            layer, ocr = Path(d, "t.jsonl"), Path(d, "o.jsonl")
            layer.write_text(json.dumps({"digest": "X", "text": BAD}) + "\n", encoding="utf-8")
            ocr.write_text(json.dumps({"digest": "X", "text": GOOD}) + "\n", encoding="utf-8")
            into: dict = {}
            build_search.load_text(layer, "text", into)
            build_search.load_text(ocr, "ocr", into)
            self.assertEqual(into["X"], (GOOD.strip(), "ocr"))

    def test_a_damaged_layer_is_queued_for_ocr(self):
        with tempfile.TemporaryDirectory() as d:
            layer = Path(d, "t.jsonl")
            layer.write_text(json.dumps({"digest": "X", "chars": len(BAD), "text": BAD}) + "\n"
                             + json.dumps({"digest": "Y", "chars": len(GOOD), "text": GOOD}) + "\n",
                             encoding="utf-8")
            chars = ocr_letters.text_chars(layer)
            self.assertEqual(chars["X"], 0)
            self.assertEqual(chars["Y"], len(GOOD))


class PartialTextLayer(unittest.TestCase):
    """#252: a layer with only the signature page loses to OCR of the whole letter."""

    def test_export_prefers_fuller_ocr(self):
        import export_text
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "data").mkdir()
            layer = "Sincerely, United States Senator " * 5           # 160 chars
            full = "Dear Administrator Martinez: " * 20 + layer      # the whole letter
            (root / "data" / "letter-text.jsonl").write_text(
                json.dumps({"digest": "P", "chars": len(layer), "text": layer}) + "\n"
                + json.dumps({"digest": "Q", "chars": len(full), "text": full}) + "\n", encoding="utf-8")
            (root / "data" / "letter-ocr.jsonl").write_text(
                json.dumps({"digest": "P", "chars": len(full), "text": full}) + "\n"
                + json.dumps({"digest": "Q", "chars": len(full) + 10, "text": full + "x" * 10}) + "\n",
                encoding="utf-8")
            old = export_text.ROOT
            export_text.ROOT = root
            try:
                best, _, _ = export_text.best_texts()
            finally:
                export_text.ROOT = old
            self.assertEqual(best["P"]["source"], "ocr")         # partial layer replaced
            self.assertEqual(best["Q"]["source"], "text-layer")  # a full layer still wins


if __name__ == "__main__":
    unittest.main()
