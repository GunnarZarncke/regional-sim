# Session: provenance scan + validation-scope refuses

**Date:** 2026-11-05  
**Plane:** docs / provenance. No engine retune.

## Done

- Reflected `drafts/2026-11-04-c-parameter-evidence-scan.md` in `make_provenance.py` (contextual sources stay C except existing A/B).
- Added `docs/validation_scope.md` magnitude refuses (truck delay, card/ACH rates, spoilage volume, Fix I-5 transfer, AEP independent response, Sue Wing executed moves, joint shocks).
- Coupling magnitude language: gap → scope refuse.

## Verify

```bash
cd regional_sim && python make_provenance.py && python -m unittest discover -s tests -v
```
