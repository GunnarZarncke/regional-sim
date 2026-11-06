# Session: preregister 30-day validation battery

**Date:** 2026-11-06  
**Plane:** oracle / docs. No engine retune. Battery **not run**.

## Done

- `docs/validation_battery.md`, `configs/validation_battery.json`, `scripts/run_validation_battery.py`.
- Held-out seeds 9091–9094 reserved; traces write then delete; pass = direction + invariants only.

## Next

```bash
cd regional_sim && python -m scripts.run_validation_battery
```
