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


if __name__ == "__main__":
    unittest.main()
