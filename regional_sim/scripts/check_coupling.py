"""Scripted-human coupling direction checks. Magnitudes are not calibrated."""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regional_sim import Config, World
from regional_sim.scenarios import Shock

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "calibration" / "coupling_results.json"
SEEDS = (47, 48, 49)
N = 800
DAYS = 3


def run(seed, extra_shocks=(), disable_coupling=()):
    cfg = Config(
        households=N,
        days=DAYS,
        seed=seed,
        trace="",
        extra_shocks=tuple(extra_shocks),
        disable_coupling=tuple(disable_coupling),
        availability_extension=False,
        scenario="routine",
    )
    w = World(cfg)
    summary = w.run()
    summary["payment_network_declined"] = int(w.stats["payment_network_declined"])
    summary["settlement_delayed_infrastructure"] = int(w.stats["settlement_delayed_infrastructure"])
    return summary


def main():
    closure = Shock(2, "road_closure", -1, 0.0, 36)
    payments = Shock(2, "payments", -1, 0.0, 24)
    power = Shock(2, "power", -1, 0.0, 24)
    routine, closed, pay, pwr, pwr_off = [], [], [], [], []
    steps = (
        ("routine", lambda s: run(s), routine),
        ("road_closure", lambda s: run(s, extra_shocks=(closure,)), closed),
        ("payments", lambda s: run(s, extra_shocks=(payments,)), pay),
        ("power", lambda s: run(s, extra_shocks=(power,)), pwr),
        ("power_ablation", lambda s: run(s, extra_shocks=(power,),
                                         disable_coupling=("power_to_retail",)), pwr_off),
    )
    total = len(SEEDS) * len(steps)
    k = 0
    for label, fn, bucket in steps:
        for seed in SEEDS:
            k += 1
            print(f"[{k}/{total}] {label} seed={seed}", flush=True)
            bucket.append(fn(seed))

    freight_ok = all(c["logistics_delays"] > r["logistics_delays"] for c, r in zip(closed, routine))
    pay_ok = all(p["payment_network_declined"] >= r["payment_network_declined"] for p, r in zip(pay, routine))
    retail_ok = all(a["shop_power_closures"] > b["shop_power_closures"] for a, b in zip(pwr, pwr_off))

    result = {
        "status": "scripted-human mechanism checks; magnitudes not calibrated",
        "n": N,
        "days": DAYS,
        "seeds": list(SEEDS),
        "availability_extension": False,
        "transport_freight": {
            "shock": {"domain": "road_closure", "multiplier": 0, "at_hour": 2, "duration_hours": 36},
            "runs": [
                {"seed": seed, "routine_logistics_delays": r["logistics_delays"],
                 "closure_logistics_delays": c["logistics_delays"]}
                for seed, r, c in zip(SEEDS, routine, closed)
            ],
            "direction_holds": freight_ok,
            "magnitude": "gap",
            "note": "Freight uses the main corridor only; trucks cannot take the alternate route.",
        },
        "payments_settlement": {
            "shock": {"domain": "payments", "multiplier": 0, "at_hour": 2, "duration_hours": 24},
            "runs": [
                {"seed": seed,
                 "routine_declined": r["payment_network_declined"],
                 "shocked_declined": p["payment_network_declined"],
                 "routine_settlement_retries": r["settlement_delayed_infrastructure"],
                 "shocked_settlement_retries": p["settlement_delayed_infrastructure"]}
                for seed, r, p in zip(SEEDS, routine, pay)
            ],
            "direction_holds": pay_ok,
            "magnitude": "gap",
            "note": "Full-run declines can be zero if no electronic payment falls in the shock window; unit tests cover transfer().",
        },
        "power_retail": {
            "shock": {"domain": "power", "multiplier": 0, "at_hour": 2, "duration_hours": 24},
            "ablation": "power_to_retail",
            "runs": [
                {"seed": seed,
                 "closures": a["shop_power_closures"],
                 "ablation_closures": b["shop_power_closures"],
                 "spoiled": a["grocery_spoiled_units"],
                 "ablation_spoiled": b["grocery_spoiled_units"]}
                for seed, a, b in zip(SEEDS, pwr, pwr_off)
            ],
            "direction_holds": retail_ok,
            "magnitude": "gap",
            "spoilage_rate": "C-level 0.0006/hour after four unpowered hours; not fitted",
        },
        "finance_and_markets": {
            "status": "scope_refuse",
            "reason": "Household deposits capped below the FDIC standard coverage limit; no uninsured or large-depositor run groups; no global markets or exchanges.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "transport_freight": freight_ok,
        "payments_settlement": pay_ok,
        "power_retail": retail_ok,
        "finance_and_markets": "scope_refuse",
        "wrote": str(OUT),
    }, indent=2))


if __name__ == "__main__":
    main()
