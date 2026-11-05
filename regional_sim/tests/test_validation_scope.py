"""Refuse rows must exist in the generated provenance register."""
import json
import unittest
from pathlib import Path

ROWS = json.loads((Path(__file__).resolve().parents[1] / "provenance.json").read_text())
PARAMS = {r["parameter"] for r in ROWS}


class ValidationScope(unittest.TestCase):
    def test_magnitude_refuse_rows_present(self):
        for name in (
            "Columbus truck-delay magnitude under corridor closure",
            "card or ACH incident decline rate under payment shock",
            "Columbus grocery spoilage volume after outage",
            "Fix I-5 Sacramento → Columbus independent transfer",
            "AEP 2022 independent event-response validation",
            "Sue Wing stated-intent → Columbus executed relocation",
            "synthetic Columbus household withdrawal probability",
            "global markets and exchanges",
        ):
            self.assertIn(name, PARAMS)

    def test_refuse_rows_are_category_c(self):
        named = {r["parameter"]: r for r in ROWS}
        self.assertEqual(named["Columbus truck-delay magnitude under corridor closure"]["evidence_category"], "C")
        self.assertEqual(named["Columbus truck-delay magnitude under corridor closure"]["estimate"], None)


if __name__ == "__main__":
    unittest.main()
