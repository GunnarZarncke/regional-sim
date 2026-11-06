# HANDOFF

## Open work

- **Step 2b:** Run `python -m scripts.run_validation_battery` from `regional_sim/` and commit **only** `calibration/validation_battery.json` (plus HANDOFF). Do not retune on fails that are listed as refuses.
- **Step 3:** Million-household 30-day run (`configs/large.json` + `days=30`), traces off; then freeze declaration.
- **Step 4:** Scoped world freeze (`world_freeze_bar_met` for that claim boundary).
- **Step 5:** Exploratory 10k AI pilot on the same 30-day clock; do not retune world from it.

## Recently shipped

- Validation **protocol** (`docs/validation_battery.md`, `configs/validation_battery.json`): 30 days, seeds 9091–9094, n=800 + 10k smoke.
- Provenance + magnitude refuses; 0.5.1 parameter freeze.
