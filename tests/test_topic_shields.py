"""Shield phrases in build/topics.py: a phrase containing a topic's word that
is not that topic matches, and tags nothing (14 November 2026)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import topics  # noqa: E402


class Shields(unittest.TestCase):
    def test_new_mexico_is_not_mexico(self):
        self.assertNotIn("Mexico", topics.tag("Texas v. New Mexico water compact"))
        self.assertNotIn("Mexico", topics.tag("New Mexico digital equity act"))
        self.assertIn("Water", topics.tag("New Mexico water rights"))   # other words still tag

    def test_mexican_american_is_not_mexico(self):
        self.assertNotIn("Mexico", topics.tag("Mexican American studies ban"))

    def test_mexico_still_tags_mexico(self):
        self.assertIn("Mexico", topics.tag("US Mexico border travel restrictions"))
        self.assertIn("Mexico", topics.tag("Mexico biotech corn"))

    def test_chips_is_not_the_childrens_health_program(self):
        # Medicaid's "chip" is CHIP, the Children's Health Insurance Program.
        self.assertNotIn("Medicaid", topics.tag("CHIPS funding guidance to Secretary Raimondo"))
        self.assertIn("CHIPS and Science Act", topics.tag("CHIPS Act funding"))
        self.assertNotIn("Medicaid", topics.tag("Semiconductor chip manufacturing"))
        self.assertNotIn("Medicaid", topics.tag("Chip Roy PPP flexibility"))
        self.assertIn("Medicaid", topics.tag("CHIP reauthorization to Speaker Ryan"))
        self.assertIn("Medicaid", topics.tag("Medicaid and CHIP"))

    def test_shields_are_not_topics(self):
        for phrase in topics.SHIELDS:
            self.assertEqual(topics.tag(phrase), [], phrase)


if __name__ == "__main__":
    unittest.main()


class TestShieldsFromTheOtherSeventeenTerms(unittest.TestCase):
    """The same check #189 ran on Mexico, applied to the rest of #188.

    Of the seventeen other terms, four matched a phrase that is not the
    subject. The rest were left alone: "national park service" really is
    National parks, "transmission line" really is the Electric grid,
    "pension benefit guaranty" really is Retirement, and "drone strike" is
    still a drone.
    """

    def test_solarwinds_is_not_solar_power(self):
        self.assertNotIn("Solar power",
                         topics.tag("the SolarWinds breach, SolarWinds Orion, SolarWinds"))

    def test_the_solar_system_is_not_solar_power(self):
        self.assertNotIn("Solar power",
                         topics.tag("the solar system, the solar system, our solar system"))

    def test_solar_power_still_tags(self):
        self.assertIn("Solar power",
                      topics.tag("rooftop solar and solar panels and solar generation"))

    def test_hydrogen_sulfide_is_not_hydrogen_fuel(self):
        self.assertNotIn("Hydrogen",
                         topics.tag("hydrogen sulfide emissions, hydrogen sulfide, "
                                    "hydrogen sulfide monitoring"))

    def test_hydrogen_still_tags(self):
        self.assertIn("Hydrogen",
                      topics.tag("clean hydrogen hubs, hydrogen production, hydrogen fuel"))

    def test_cuban_american_is_a_community_not_a_country(self):
        self.assertNotIn("Cuba",
                         topics.tag("Cuban American voters, the Cuban American community, "
                                    "Cuban American leaders"))

    def test_cuba_still_tags(self):
        self.assertIn("Cuba", topics.tag("the Cuba embargo and Cuba policy and travel to Cuba"))
