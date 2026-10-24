import argparse, csv, json
from pathlib import Path
from .engine import Config, World
from .scenarios import Shock

def main(argv=None):
    bootstrap = argparse.ArgumentParser(add_help=False)
    bootstrap.add_argument("--config", help="JSON parameter defaults; explicit CLI flags override them")
    prelim, _ = bootstrap.parse_known_args(argv)
    defaults = {}
    if prelim.config:
        with open(prelim.config, encoding="utf8") as f:
            defaults = json.load(f)
    p = argparse.ArgumentParser(description="Event-driven synthetic Columbus MSA prototype", parents=[bootstrap])
    p.add_argument("--households", type=int, default=10000)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--zones", type=int, default=12)
    p.add_argument("--retailers", type=int, default=24)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--scenario", choices=("routine", "seasonal", "moderate", "severe"), default="routine")
    p.add_argument("--out", default="output")
    p.add_argument("--full-trace", action="store_true")
    p.add_argument("--sample-rate", type=float, default=.02)
    p.add_argument("--free-flow-minutes", type=float, default=24.0)
    p.add_argument("--no-availability", action="store_true", help="Ablate the provisional operational availability extension")
    p.add_argument("--shock-json", help="JSON file containing an array of shock objects")
    p.add_argument("--disable-coupling", action="append", default=[])
    p.set_defaults(**defaults)
    args = p.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    shocks = ()
    if args.shock_json:
        with open(args.shock_json, encoding="utf8") as f:
            shocks = tuple(Shock(**s) for s in json.load(f))
    cfg = Config(households=args.households, days=args.days, seed=args.seed, scenario=args.scenario,
                 zones=args.zones, retailers=args.retailers,
                 trace=str(out / "traces.ndjson"), full_trace=args.full_trace, sample_rate=args.sample_rate,
                 disable_coupling=tuple(args.disable_coupling), extra_shocks=shocks,
                 free_flow_minutes=args.free_flow_minutes, availability_extension=not args.no_availability)
    sim = World(cfg)
    result = sim.run()
    sim.write_metrics(out / "daily.csv")
    summary = {"configuration": {**vars(args), "shocks": [vars(s) for s in shocks]},
               "final": result, "trace_counts": dict(sim.trace.counts),
               "network_clustering_sample": sim.network.clustering_sample(),
               "source_categories": "see provenance.json; C parameters remain uncalibrated",
               "validation_status": "prototype, NOT validated against independent response benchmarks"}
    with open(out / "summary.json", "w", encoding="utf8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
