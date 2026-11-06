"""Preregistered 30-day software validation battery. Magnitudes are scope refuses."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regional_sim import Config, World
from regional_sim.scenarios import Shock

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "configs" / "validation_battery.json").read_text())
OUT = ROOT / SPEC["output"]
TRACE_DIR = ROOT / SPEC["trace"]["write_under"]
SEEDS = tuple(SPEC["held_out_seeds"])
DAYS = int(SPEC["horizon_days"])
AT = float(SPEC["shock_at_hour"])


def shocks_from(cell):
    return tuple(
        Shock(AT, s["domain"], -1, s["multiplier"], s["duration_hours"])
        for s in cell["shocks"]
    )


def run_one(n, seed, cell, zones=12, retailers=24):
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    trace_path = TRACE_DIR / f"{cell['id']}_n{n}_seed{seed}.ndjson"
    cfg = Config(
        households=n,
        days=DAYS,
        zones=zones,
        retailers=retailers,
        seed=seed,
        scenario="routine",
        availability_extension=False,
        extra_shocks=shocks_from(cell),
        disable_coupling=tuple(cell.get("disable_coupling") or ()),
        trace=str(trace_path),
        sample_rate=float(SPEC["trace"]["sample_rate"]),
        full_trace=bool(SPEC["trace"]["full_trace"]),
    )
    w = World(cfg)
    summary = w.run()
    w.invariants()
    counts = dict(w.trace.counts)
    summary["payment_network_declined"] = int(w.stats["payment_network_declined"])
    summary["settlement_delayed_infrastructure"] = int(w.stats["settlement_delayed_infrastructure"])
    w.trace.close()
    if SPEC["trace"]["discard_after_extracting_counts"] and trace_path.exists():
        trace_path.unlink()
    extract = {
        k: summary[k]
        for k in (
            "logistics_delays",
            "payment_network_declined",
            "settlement_delayed_infrastructure",
            "shop_power_closures",
            "grocery_spoiled_units",
            "unmet_grocery_units",
            "escrow_cents",
            "people_temporarily_away",
            "goods_error_max",
            "payment_failures",
        )
        if k in summary
    }
    extract["trace_counts"] = {k: int(v) for k, v in counts.items()}
    return extract


def main():
    book = SPEC["coupling_book"]
    smoke = SPEC["conservation_smoke"]
    cells = SPEC["cells"]
    n_book = int(book["households"])
    n_smoke = int(smoke["households"])
    total = len(SEEDS) * (len(cells) + 1)
    k = 0
    t0 = time.perf_counter()
    by_cell = {c["id"]: [] for c in cells}
    conservation = []
    for seed in SEEDS:
        for cell in cells:
            k += 1
            print(f"[{k}/{total}] {cell['id']} n={n_book} seed={seed}", flush=True)
            by_cell[cell["id"]].append({"seed": seed, **run_one(n_book, seed, cell)})
        k += 1
        print(f"[{k}/{total}] conservation_smoke n={n_smoke} seed={seed}", flush=True)
        conservation.append(
            {"seed": seed, **run_one(n_smoke, seed, {"id": "routine", "shocks": [], "disable_coupling": []})}
        )

    def col(cid, key):
        return [row[key] for row in by_cell[cid]]

    freight_ok = all(
        c["logistics_delays"] > r["logistics_delays"]
        for c, r in zip(by_cell["road_closure"], by_cell["routine"])
    )
    pay_ok = all(
        p["payment_network_declined"] >= r["payment_network_declined"]
        for p, r in zip(by_cell["payments"], by_cell["routine"])
    )
    retail_ok = all(
        a["shop_power_closures"] > b["shop_power_closures"]
        for a, b in zip(by_cell["power"], by_cell["power_ablation"])
    )
    result = {
        "status": "software validation battery; magnitudes are scope refuses",
        "protocol": SPEC["protocol"],
        "simulator_version": SPEC["simulator_version"],
        "n_coupling": n_book,
        "n_conservation_smoke": n_smoke,
        "days": DAYS,
        "seeds": list(SEEDS),
        "availability_extension": False,
        "elapsed_seconds": round(time.perf_counter() - t0, 3),
        "pass": {
            "transport_freight_direction": freight_ok,
            "payments_settlement_direction": pay_ok,
            "power_retail_direction": retail_ok,
            "invariants": True,
        },
        "cells": by_cell,
        "conservation_smoke": conservation,
        "finance_and_markets": "scope_refuse",
        "not_scored": SPEC["not_scored"],
        "direction_pairs": {
            "logistics_delays": {"routine": col("routine", "logistics_delays"),
                                 "road_closure": col("road_closure", "logistics_delays")},
            "payment_network_declined": {"routine": col("routine", "payment_network_declined"),
                                         "payments": col("payments", "payment_network_declined")},
            "shop_power_closures": {"power": col("power", "shop_power_closures"),
                                    "power_ablation": col("power_ablation", "shop_power_closures")},
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({**result["pass"], "wrote": str(OUT)}, indent=2), flush=True)
    if not (freight_ok and pay_ok and retail_ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
