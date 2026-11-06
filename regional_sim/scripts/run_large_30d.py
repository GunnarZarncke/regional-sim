"""Million-household 30-day scale check. Traces off. Not a magnitude calibration."""
from __future__ import annotations

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
SEED = 9091


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


def main():
    large = json.loads((ROOT / "configs" / "large.json").read_text())
    cfg = Config(
        households=int(large["households"]),
        days=DAYS,
        zones=int(large["zones"]),
        retailers=int(large["retailers"]),
        seed=SEED,
        scenario=str(large.get("scenario", "routine")),
        trace="",
        sample_rate=0.0,
        availability_extension=True,
    )
    print(
        f"[0/{DAYS}] init n={cfg.households} zones={cfg.zones} retailers={cfg.retailers} seed={SEED}",
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
            f"[{day}/{DAYS}] t={self.t:.1f}h rss_mb={rss_mb():.1f} "
            f"messages={len(self.messages)} pending_tx={len(self.pending)} actions={len(self.actions)}",
            flush=True,
        )

    World.daily = daily
    try:
        summary = w.run()
    finally:
        World.daily = orig_daily
    elapsed = time.perf_counter() - t0
    w.invariants()
    extract = {
        "status": "million-household 30-day scale check; traces off; not a magnitude calibration",
        "n": cfg.households,
        "days": DAYS,
        "zones": cfg.zones,
        "retailers": cfg.retailers,
        "seed": SEED,
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
    OUT.write_text(json.dumps(extract, indent=2) + "\n")
    print(json.dumps(extract, indent=2), flush=True)


if __name__ == "__main__":
    main()
