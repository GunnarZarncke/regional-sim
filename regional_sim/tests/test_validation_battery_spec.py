"""Protocol file must stay aligned with held-out seeds (do not run the battery here)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "configs/validation_battery.json").read_text())
HELDOUT = json.loads((ROOT / "configs/heldout_seeds.json").read_text())


class ValidationBatterySpec(unittest.TestCase):
    def test_seeds_are_held_out(self):
        self.assertEqual(SPEC["held_out_seeds"], HELDOUT["seeds"])
        self.assertTrue(set(SPEC["held_out_seeds"]).isdisjoint({42, 43, 44, 46, 47, 48, 49}))

    def test_horizon_and_no_commit_traces(self):
        self.assertEqual(SPEC["horizon_days"], 30)
        self.assertFalse(SPEC["trace"]["commit"])
        self.assertTrue(SPEC["trace"]["discard_after_extracting_counts"])
        self.assertTrue(SPEC["status"].startswith("run"))
        results = json.loads((ROOT / "calibration/validation_battery.json").read_text())
        self.assertEqual(results["seeds"], SPEC["held_out_seeds"])
        self.assertTrue(all(results["pass"].values()))

    def test_cells(self):
        ids = [c["id"] for c in SPEC["cells"]]
        self.assertEqual(ids, ["routine", "road_closure", "payments", "power", "power_ablation"])


if __name__ == "__main__":
    unittest.main()
