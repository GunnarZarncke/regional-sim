# 2026-10-24 — Pass 2 coupling and finance refuse

kind: new-work

## Trigger

Implement Pass 2 of the additional calibration plan: scripted-human coupling checks; record finance/markets as scope refuse. Do not edit the blinded assignment. Do not commit unless asked. Do not retune Fix I-5 / Sue Wing / AEP.

## Done

- Added `scripts/check_coupling.py`, `tests/test_coupling.py`, `docs/coupling_checks.md`, `docs/finance_scope.md`.
- Regenerated `provenance.json` (84 rows) with FDIC/Basel/market refuse records.
- Ran `python -m unittest discover -s tests -v` → 48 tests OK.
- Ran `python -m scripts.check_coupling` → freight/payments/power_retail direction true; finance_and_markets scope_refuse.
- Bumped live version to 0.5.0-dev; `versions/0.5.0-dev.md`; freeze-bar notes in `INSTRUCTIONS.md`.

## Decisions

- No depositor-run rates. No global markets. Magnitudes labeled gap, not fitted.
- Containment (delay without collapse) is a successful check.

## Open / next

- Commit if requested. Independent Fix I-5 transfer still open.

## Key paths

- `regional_sim/docs/coupling_checks.md`
- `regional_sim/docs/finance_scope.md`
- `regional_sim/calibration/coupling_results.json`
- `versions/0.5.0-dev.md`
