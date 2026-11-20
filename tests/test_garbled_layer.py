"""A text layer that is a glyph stream is not text (#252)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
import export_text  # noqa: E402


class GarbledLayer(unittest.TestCase):
    def test_glyph_stream_is_garbled(self):
        self.assertTrue(export_text.garbled("/0/1/2/3/i255/5/6/7/8/9/10/11/12/13/14/15 " * 40))

    def test_control_characters_are_garbled(self):
        self.assertTrue(export_text.garbled("\x01\x02\x03 amp \x04\x05\x06 B? \x07\x08 " * 50))

    def test_a_letter_is_not_garbled(self):
        letter = ("Dear Secretary Austin: We write to urge the Department to deliver additional "
                  "air defense systems to Ukraine without delay. Sincerely, Members of Congress. ") * 10
        self.assertFalse(export_text.garbled(letter))

    def test_a_signers_list_is_not_garbled(self):
        signers = "Dina Titus Member of Congress Mike Doyle Member of Congress " * 20
        self.assertFalse(export_text.garbled(signers))


if __name__ == "__main__":
    unittest.main()
