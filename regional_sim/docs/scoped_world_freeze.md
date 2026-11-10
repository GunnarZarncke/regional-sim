# Scoped world freeze (0.5.2)

**Date:** 2026-11-07  
**Plane:** oracle / freeze record. No magnitude retune. No AI scoring.

This is the claim boundary for a **software / conservation / scale freeze**.
It authorizes an **exploratory** 10k AI pilot on the same 30-day clock. It does
**not** meet the full **world freeze bar** in [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md)
(effect magnitudes, heterogeneity, held-out Columbus benchmarks).

`VERSION.json`: `"scoped_world_freeze_met": true`, `"world_freeze_bar_met": false`,
`"independent_empirical_validation_passed": false`.

## What is frozen

| Item | Record |
|------|--------|
| Numeric defaults and packaged inverse fits | 0.5.1 [`frozen_parameters.md`](frozen_parameters.md) |
| Magnitude and transfer **refuses** | [`validation_scope.md`](validation_scope.md) |
| Finance / markets **refuse** | [`finance_scope.md`](finance_scope.md) |
| Scripted-human coupling **direction** | [`coupling_checks.md`](coupling_checks.md), `calibration/coupling_results.json` |
| 30-day software battery (n=800 direction + n=10k conservation; seeds 9091–9094) | [`validation_battery.md`](validation_battery.md), `calibration/validation_battery.json` (`"pass"` all true, 96.233 s) |
| 1M×30d scale check, same held-out seeds | `calibration/large_30d.json` (`"all_invariants": true`) |

World-model **calibrated knobs** stay at 0.5.1. Do not retune Fix I-5, Sue Wing, or
AEP multipliers. Do not add domains to close a refuse.

## Conservation accounting after 0.5.1

Hourly energy `served` is capped at `supply`; spill is `generation − served`;
the energy inequality uses slack `max(1e-6, 1e-10 × generation)`. That is
float-safe ledger identity at ~1e9 kWh, not a load or outage retune. Message
GC (48 h) is a scale bound, not a behavior fit.

## What is not claimed

- Columbus truck-delay hours, card/ACH incident rates, spoilage **volume**,
  Fix I-5 geographic transfer, independent AEP event response, executed Sue Wing
  relocations, depositor-run rates, global markets, joint shock catalog.
- That 1M unmet-grocery or escrow scalars match local series (n=800 vs 1M
  retailer density differs; battery had availability **off**).
- Formal AI-replacement scoring under
  [`multi-domain-counterexample-protocol.md`](../../multi-domain-counterexample-protocol.md).
  That protocol still requires the full world freeze bar.

## What may start

Exploratory 10k AI pilot: same 30-day horizon, matched held-out seeds, same
world interface as `ScriptedPolicy`. Do not fit world parameters to AI
outcomes. Mark any post-look change exploratory.

## Changing the freeze

Bump the version string. Keep `world_freeze_bar_met` false until a documented
magnitude/held-out claim exists. Do not silently edit this file after a scored
AI run.
