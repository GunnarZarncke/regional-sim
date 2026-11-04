# Report artifacts and traces

`daily.csv` and `summary.json` under `reports/` may be checked in when they support validation write-ups. **`traces.ndjson` is never committed** (see repo `.gitignore`); regenerate from the seed and CLI options recorded in `summary.json` or below.

Run from `regional_sim/` after `pip install -e .`.

## `reports/routine_10000_30d/` (0.1.0 baseline narrative)

```bash
regional-sim --config configs/development.json --out reports/routine_10000_30d
```

Uses seed 42, 10,000 households, 30 days, `sample_rate` 0.02 from the config file.

## `reports/routine_10000_5d/` and `reports/power_10000_5d/` (paired shock, seed 42)

Ordinary five-day control and power shock (hour 25, multiplier 0.35, 24 h) with defaults:

```bash
regional-sim --households 10000 --days 5 --seed 42 --out reports/routine_10000_5d
regional-sim --households 10000 --days 5 --seed 42 --shock-json configs/power_shock.json --out reports/power_10000_5d
```

Aggregated paired metrics without traces: `python -m scripts.validate` → `reports/internal_validation.json`.

## `reports/calibrated_example/`

```bash
regional-sim --config configs/calibrated_2024.json --out reports/calibrated_example
```

## `reports/road_closure_10000_3d/` (0.4.0 travel example)

```bash
regional-sim --households 10000 --days 3 --seed 47 \
  --shock-json configs/road_closure_information.json --no-availability \
  --sample-rate 0.002 --out reports/road_closure_10000_3d
```
