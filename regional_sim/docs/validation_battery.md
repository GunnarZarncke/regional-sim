# Preregistered validation battery (software / scoped freeze)

**Date:** 2026-11-06  
**Status:** Protocol plus extract. Runner: `python -m scripts.run_validation_battery`. Extract: `calibration/validation_battery.json`.

**Plane:** oracle / experiment checks. No engine retune. Held-out seeds are **not** used to fit.

This battery is the software gate for a **scoped world freeze** ([`validation_scope.md`](validation_scope.md)). It does **not** claim independent Columbus empirical validation.

## Horizon and matching

| Field | Value |
|-------|--------|
| `days` | **30** |
| Seeds | **9091, 9092, 9093, 9094** ([`../configs/heldout_seeds.json`](../configs/heldout_seeds.json)) |
| Shock start | hour **2** |
| Policy | default `ScriptedPolicy` |
| Availability extension | **off** on all cells (relocation must not mix with freight/shop) |

Later AI pilots that compare to this baseline use the **same 30-day clock**, matched seeds, and the same shock JSON. Grid capacity still restores at `duration_hours` (exogenous). Thirty days is for settlement tails, restock, payroll (weekly), and attendance—not endogenous feeder repair.

Machine-readable copy: [`../configs/validation_battery.json`](../configs/validation_battery.json).

## Cells

Coupling book: **n = 800**, 12 zones, 24 retailers, `trace` under `output/validation_battery/` then **deleted**; commit **event-count extracts only**.

| id | Shock | Ablation |
|----|--------|----------|
| `routine` | none | — |
| `road_closure` | `road_closure` multiplier 0, 36 h | — |
| `payments` | `payments` multiplier 0, 24 h | — |
| `power` | `power` multiplier 0, 24 h | — |
| `power_ablation` | same power shock | `power_to_retail` |

Conservation smoke: **n = 10_000**, same 30 days and four seeds, routine only.

## Pass rules (software)

Recorded **before** looking at held-out outputs:

1. `World.invariants()` succeeds after every run (money, reserves, goods, energy inequalities).
2. For every seed: `road_closure.logistics_delays > routine.logistics_delays`.
3. For every seed: `payments.payment_network_declined >= routine.payment_network_declined`.
4. For every seed: `power.shop_power_closures > power_ablation.shop_power_closures`.
5. Existing `tests/test_frozen_parameters.py` still passes (literals vs `frozen_world_parameters.json`).

Containment (delay without collapse) is a **pass**, not a fail. Collapse is not required ([`INSTRUCTIONS.md`](../../INSTRUCTIONS.md) world freeze bar §3).

## Recorded diagnostics (not pass/fail)

End-of-horizon scalars vs routine, same seed: `escrow_cents`, `logistics_delays`, `grocery_spoiled_units`, `unmet_grocery_units`, `people_temporarily_away`, `goods_error_max`, `trace.counts`. These describe software recovery tails. They are **not** Columbus magnitude tests.

## Scope refuses (not scored)

Do not fail the battery, retune Fix I-5 / Sue Wing / AEP, or add domains to “pass” these: Columbus truck-delay hours, card/ACH incident rates, spoilage **volume**, Fix I-5 geographic transfer, independent AEP event response, executed Sue Wing relocations, depositor-run rates, global markets, joint shock catalog. See [`validation_scope.md`](validation_scope.md).

## Traces

Write NDJSON under `output/` (gitignored). After extracting `trace.counts`, delete the file. `sample_rate` 0 (institutional events only while the file exists). Do not commit traces.

## What this commit does not do

Does not change engine parameters. Does not start the million-household step (`configs/large.json`, same 30-day clock, traces off—later).

## Results (quoted)

`python -m scripts.run_validation_battery` (2026-11-06), **96.233 s**, traces discarded:

- `"transport_freight_direction": true` — routine `logistics_delays` 0 vs closure 1897 / 1899 / 1899 / 1901.
- `"payments_settlement_direction": true` — routine declines 0 vs 1486 / 1498 / 1469 / 1487.
- `"power_retail_direction": true` — closures 114 / 117 / 115 / 107 vs ablation 0.
- `"invariants": true`

These counts are software responses, not Columbus benchmarks.
