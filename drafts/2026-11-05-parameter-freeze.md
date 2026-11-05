# Session: parameter freeze 0.5.1

**Date:** 2026-11-05

## Done

- Locked engine defaults and `calibrated_2024.json` t0 in `configs/frozen_world_parameters.json` (source commit `0cceb2a`).
- Added `docs/frozen_parameters.md`, `tests/test_frozen_parameters.py`, version bump to **0.5.1**.
- Synced `make_provenance.py` / regenerated `provenance.json`; INSTRUCTIONS parameter-freeze note (explicitly not world freeze bar).

## Verify

```bash
cd regional_sim && python make_provenance.py && python -m unittest discover -s tests -v
```
