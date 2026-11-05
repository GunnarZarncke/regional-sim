# 2026-11-04 — Apply evidence-scan parameter revisions

kind: new-work

## Trigger

Apply revised C-parameter values from evidence scan one-by-one; run simulation/tests after each; card hold = **1 day** (24 h).

## Changes (cumulative in `engine.py`)

| Step | Parameter | Old → New | Tests (48) |
|------|-----------|-----------|------------|
| 1 | Refrigeration spoilage delay | 6 h → **4 h** unpowered | OK |
| 2 | Water need | 0.35 → **0.61** m³/HH/day | OK |
| 3 | Card-style settlement delay | 1 h → **24 h** (retail/medicine/wholesale/utility labels) | OK |
| 4 | Employment | 0.73 → **0.601** | OK |
| 5 | Remote given employed | 0.17 → **0.133** | OK |
| 6 | Default `free_flow_minutes` | 24.0 → 27.2 → **restored 24.0** (Columbus) | OK |
| 7 | Daily utility debit | 310 → **460** cents | OK |

Post-all: `python -m scripts.check_coupling` direction holds.

## Breakage

**None** — no failing unit tests or conservation asserts.

## Non-breaking drift (treatment)

1. **24 h card/merchant settlement** — After day 1, large **escrow** and **pending** counts (e.g. seed 47, n=800: ~647 pending, ~$470k escrow at hour 24) while `money_total()` conserved. **Treatment:** expected float; document in finance_scope; optionally split `wholesale`/`utility_bill` back to ACH (next-day) while keeping 24 h for `retail_sale`/`medicine_sale` only.
2. **free_flow** — Restored default **24.0**; `python -m scripts.calibrate` with other changes active refits **`23.702395` min** (unchanged). At default 24.0, mean trip **24.27 min** (+0.17 vs ACS 24.1); at calibrated t0, **24.21 min** (+0.11 vs ACS) on check seeds 46–47.
3. **Employment 0.601** — BLS employment–population ratio used as household-unit proxy (estimand mismatch). **Treatment:** provenance limitation; optional ACS employment table later.
4. **Spoilage at 4 h** — More early spoilage under power shocks; coupling direction tests still pass; magnitudes not re-benchmarked.
5. **Higher water demand** — More `water_unmet_m3` under power stress possible; not asserted in CI.

## Not done

- `make_provenance.py` / `calibration/*.json` not regenerated
- Not committed
