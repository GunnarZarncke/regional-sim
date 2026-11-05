"""Regression guard for configs/frozen_world_parameters.json."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = json.loads((ROOT / "configs/frozen_world_parameters.json").read_text())
ENGINE = (ROOT / "regional_sim/engine.py").read_text()
CALIBRATED = json.loads((ROOT / "configs/calibrated_2024.json").read_text())


class FrozenParameters(unittest.TestCase):
    def test_calibrated_free_flow(self):
        want = FREEZE["configs"]["calibrated_2024.json"]["free_flow_minutes"]
        self.assertEqual(CALIBRATED["free_flow_minutes"], want)

    def test_engine_literals(self):
        e = FREEZE["engine"]
        emp = format(e["employment_probability"], ".3f").lstrip("0")  # .601
        remote = format(e["remote_work_probability_given_employment"], ".3f").lstrip("0")
        checks = [
            (f"random(self.n) < {emp}", "employment"),
            (f"random(self.n) < {remote}", "remote"),
            (f"self.t + {int(e['card_style_settlement_delay_hours'])}, \"settle\"", "card settlement delay"),
            (f"store_outage_hours[store] > {int(e['refrigeration_spoilage_after_outage_hours'])}", "spoilage delay"),
            ("* .0006", "spoilage rate"),
            ("self.n * .61 / 24", "water need"),
            (f"transfer(i, self.utility, {int(e['utility_obligation_cents_per_day'])}", "utility cents"),
            (f"free_flow_minutes: float = {e['config_default_free_flow_minutes']}", "default free flow"),
        ]
        for needle, label in checks:
            self.assertIn(needle, ENGINE, msg=f"missing frozen {label}: {needle}")

    def test_settlement_labels(self):
        for label in FREEZE["engine"]["card_style_settlement_labels"]:
            self.assertIn(label, ENGINE)


if __name__ == "__main__":
    unittest.main()
