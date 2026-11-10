# HANDOFF

## Open work

- **Porter packet:** Adapter maps engine `Observation` to export v1 and uses `electronic_only` on buy. Round 0 when asked. Plan: [`ai-agent-prototype-plan.md`](ai-agent-prototype-plan.md).
- **Later:** exploratory 10k pilot on held-out seeds 9091–9094, only from a prompt that loop has frozen.
- Full **world freeze bar** (magnitudes, heterogeneity, held-out Columbus) remains unmet. Scored protocol waits on it.

## Recently shipped

- **0.6.0 world mobility** (`versions/0.6.0.md`): return `commute_home`, `at_home` / `at_work`, 7 h sleep gate, `electronic_only` buys, morning-commute recalibration (`free_flow_minutes` 24.07125). Tests pass in `regional_sim` venv.
- **0.5.2 scoped software freeze** (`docs/scoped_world_freeze.md`): conservation, coupling direction, 1M×30d. `world_freeze_bar_met` false.
- **1M × 30 d** held-out 9091–9094 (`calibration/large_30d.json`, `all_invariants` true).
- Validation battery; 0.5.1 parameter freeze; provenance refuses.
