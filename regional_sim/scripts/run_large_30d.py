"""Million-household 30-day scale check. Traces off. Not a magnitude calibration.

Runs held-out seeds sequentially. Reuses existing extracts in calibration/large_30d.json.
"""
from __future__ import annotations

import gc
import json
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from regional_sim import Config, World

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "calibration" / "large_30d.json"
DAYS = 30


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def load_bundle():
    if not OUT.exists():
        return {"status": "million-household 30-day scale check; traces off; not a magnitude calibration",
                "runs": []}
    data = json.loads(OUT.read_text())
    if "runs" in data:
        return data
    return {
        "status": data.get("status", "million-household 30-day scale check; traces off; not a magnitude calibration"),
        "runs": [data],
    }


def run_seed(seed: int, large: dict, seed_i: int, seed_n: int) -> dict:
    cfg = Config(
        households=int(large["households"]),
        days=DAYS,
        zones=int(large["zones"]),
        retailers=int(large["retailers"]),
        seed=seed,
        scenario=str(large.get("scenario", "routine")),
        trace="",
        sample_rate=0.0,
        availability_extension=True,
    )
    print(
        f"[seed {seed_i}/{seed_n}] init n={cfg.households} seed={seed}",
        flush=True,
    )
    t0 = time.perf_counter()
    w = World(cfg)
    t_init = time.perf_counter()
    print(f"init_seconds={t_init - t0:.3f} rss_mb={rss_mb():.1f}", flush=True)

    orig_daily = World.daily

    def daily(self):
        orig_daily(self)
        day = int(self.t // 24)
        print(
            f"[seed {seed} {day}/{DAYS}] t={self.t:.1f}h rss_mb={rss_mb():.1f} "
            f"messages={len(self.messages)} pending_tx={len(self.pending)} actions={len(self.actions)}",
            flush=True,
        )

    World.daily = daily
    try:
        summary = w.run()
        w.invariants()
    finally:
        World.daily = orig_daily
    elapsed = time.perf_counter() - t0
    extract = {
        "status": "million-household 30-day scale check; traces off; not a magnitude calibration",
        "n": cfg.households,
        "days": DAYS,
        "zones": cfg.zones,
        "retailers": cfg.retailers,
        "seed": seed,
        "availability_extension": True,
        "init_seconds": round(t_init - t0, 3),
        "elapsed_seconds": round(elapsed, 3),
        "rss_mb_peak": round(rss_mb(), 1),
        "invariants": True,
        "goods_error_max": summary["goods_error_max"],
        "escrow_cents": summary["escrow_cents"],
        "unmet_grocery_units": summary["unmet_grocery_units"],
        "people_temporarily_away": summary["people_temporarily_away"],
        "logistics_delays": summary["logistics_delays"],
        "shop_power_closures": summary["shop_power_closures"],
        "payment_failures": summary["payment_failures"],
    }
    del w
    gc.collect()
    return extract


def main():
    held = json.loads((ROOT / "configs" / "heldout_seeds.json").read_text())
    seeds = list(held["seeds"])
    large = json.loads((ROOT / "configs" / "large.json").read_text())
    bundle = load_bundle()
    done = {int(r["seed"]) for r in bundle["runs"]}
    todo = [s for s in seeds if s not in done]
    print(f"already_done={sorted(done)} todo={todo}", flush=True)
    n = len(todo)
    for i, seed in enumerate(todo, 1):
        extract = run_seed(seed, large, i, n)
        bundle["runs"].append(extract)
        bundle["runs"].sort(key=lambda r: r["seed"])
        bundle["n_runs"] = len(bundle["runs"])
        bundle["all_invariants"] = all(r.get("invariants") for r in bundle["runs"])
        OUT.write_text(json.dumps(bundle, indent=2) + "\n")
        print(json.dumps(extract, indent=2), flush=True)
    print(json.dumps({"wrote": str(OUT), "seeds": [r["seed"] for r in bundle["runs"]],
                      "all_invariants": bundle.get("all_invariants")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
