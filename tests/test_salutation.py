"""#97: a letter's recipient read from its salutation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

from letter_text import salutation_recipient as who  # noqa: E402

PAD = "x " * 120


class Salutation(unittest.TestCase):
    def test_names(self):
        self.assertEqual(who(PAD + "Dear Secretary Noem, On August 9th"), "Secretary Noem")
        self.assertEqual(who(PAD + "Dear Chairman Cole and Ranking Member DeLauro: We"),
                         "Chairman Cole and Ranking Member DeLauro")
        self.assertEqual(who(PAD + "Dear Honorable Smith: We"), "Smith")
        self.assertEqual(who(PAD + "Dear Mr. President: We"), "Mr. President")

    def test_greetings_name_no_one(self):
        for g in ("Dear Colleague:", "Dear Sirs,", "Dear Mr. Secretary:", "Dear Sir or Madam:",
                  "Dear Senator:", "Dear Members of Congress,"):
            self.assertEqual(who(PAD + g + " We write"), "", g)

    def test_no_salutation(self):
        self.assertEqual(who(PAD + "We write to urge"), "")
        self.assertEqual(who(PAD + "Dear 2021 budget:"), "")

    def test_only_the_opening_is_read(self):
        self.assertEqual(who("y " * 2000 + "Dear Secretary Noem,"), "")


if __name__ == "__main__":
    unittest.main()
