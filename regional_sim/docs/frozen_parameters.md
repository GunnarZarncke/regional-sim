# Frozen world parameters (0.6.0)

**Date:** 2026-11-10  
**Record:** [`../configs/frozen_world_parameters.json`](../configs/frozen_world_parameters.json)  
**Source commit:** `9eed8e9cb978f845e2b71715a7dc53320f1c345b` (pre-0.6.0 implementation base; regen commit when tagged)

## What this freeze is

This release **locks the current world-model parameter set** so policy-replacement experiments can cite a fixed numeric baseline. Verification: `python -m unittest tests.test_frozen_parameters -v`.

It is **not** a claim that the full **world freeze bar** in [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md) is satisfied. Coupling magnitudes, Fix I-5 transfer validation, and most per-domain held-out benchmarks remain open; see [`limitations.md`](limitations.md). The later **scoped software freeze** (0.5.2) is [`scoped_world_freeze.md`](scoped_world_freeze.md).

## Locked engine defaults

| Parameter | Value | Notes |
|-----------|-------|--------|
| Employment probability | 0.601 | BLS 2024 employment–population ratio as household proxy |
| Remote work \| employed | 0.133 | ACS-style WFH share (see provenance) |
| Card-style settlement delay | 24 h | Labels: retail, medicine, wholesale, utility |
| Refrigeration spoilage | after 4 h unpowered @ 0.0006/h | C assumption |
| Water need | 0.61 m³/HH/day | EPA indoor-use order of magnitude |
| Daily utility debit | 460 cents | ~EIA kWh × tariff proxy |
| Default `free_flow_minutes` | 24.0 | Columbus ACS commute proxy |

## Locked packaged fits (not re-fit without version bump)

| Artifact | Key field | Value |
|----------|-----------|-------|
| `configs/calibrated_2024.json` | `free_flow_minutes` | 24.07125 (morning `commute_arrival` mean) |
| Engine | `WORK_SHIFT_HOURS` | 8.0 |
| Engine | `MIN_SLEEP_AFTER_HOME_HOURS` | 7.0 |
| `configs/aep_2022_proxy_shocks.json` | multipliers | as at freeze commit |
| `calibration/*.json` | — | regenerated outputs for the locked engine |

## Changing parameters

1. Edit only with a documented reason and new version string (`VERSION.json`, `__init__.py`, `pyproject.toml`).
2. Regenerate calibration artifacts and update `frozen_world_parameters.json`.
3. Do not silently change frozen values after preregistered experiment scoring has started.
