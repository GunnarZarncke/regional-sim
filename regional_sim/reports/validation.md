> Historical earlier-version validation report only. For v0.5.0-dev coupling, read `docs/coupling_checks.md` and `calibration/coupling_results.json`. For travel information, read `reports/travel_information_validation.md`. Rerun the tests.

**Archive notice:** This document reports 0.1.0 results. They were NOT regenerated under 0.3.1-dev. Current participant-relocation tests and calibration checks are in `docs/participant_communication.md` and `calibration/availability_results.json`.

# Internal validation and measured results — RegionalSim 0.1.0

**Status:** executable research prototype, **not an externally calibrated or scientifically validated release**. All figures below are simulator outputs, not forecasts or observed Columbus estimates. Geography is a synthetic zone representation of Columbus, OH CBSA 18140 with a 2024 nominal reference period. Reproduction: `python -m unittest discover -s tests -v`, `python scripts/validate.py`, and the commands in `README.md`.

## Baseline normal-operation run

The checked-in `reports/routine_10000_30d/` was produced with 10,000 individually simulated households, 12 aggregate zones, 24 retailers, 30 synthetic days and seed 42. It recorded:

| Indicator | Synthetic outcome |
|---|---:|
| Household grocery retail sales | 365,953.690 abstract grocery bundles |
| Household medicine retail sales | 4,705.326 abstract medication units |
| Completed commutes | 42,093 |
| Mean completed trip time | 24.274 minutes |
| Residential demand / delivered energy | 28.509 / 28.509 kWh per household-day |
| Unserved energy; interrupted feeder-zone hours | 0 kWh; 0 |
| Retail stockout attempts; medicine stockout attempts | 0; 0 |
| Recorded unmet household groceries / medication | 1,165.629 bundles; 0 medication units |
| Store attempts rejected due to unavailable staff | 8,761 over 30 days |
| Completed clinic visits / outstanding queue at end | 1,102 / 29 |
| Unique recipients / total message exposures | 8,331 / 36,661 |
| Maximum goods-balance numerical error | 1.72e-10 units |

**Interpretation:** grocery demand is not entirely fulfilled; retail staffing is an active constraint even when inventory is available. The initial baseline identified incorrect weekend staffing and missing ordinary medication purchases. Those were treated as implementation defects, corrected via independent weekend shifts, medication retail/replenishment and store-opening-aware delayed shopping; older failed-baseline runs are excluded from the canonical packaged results. This baseline does **not** prove plausible Columbus-wide staffing or medication-demand estimates. Financial totals were exact in integer cents under the modeled closed account boundary; production/consumption/spoilage are explicit goods ledger entries.

## Paired software response experiment

Four matched independent RNG seeds (42–45); 10,000 households, five days each, ordinary operation compared with a synthetic **24-hour 0.35 regional electric supply multiplier beginning at simulated hour 25**. These are intervention-vs-baseline *within-simulator differences*, mean ± sample standard deviation across seeds, **not statistical confidence intervals or empirical effect estimates**. Full runs and machine-readable results are in `reports/internal_validation.json`. Seed-42 NDJSON traces for the five-day paired runs are **not** stored in git; regenerate with `docs/report_artifacts.md`.

| Accumulated metric | Disrupted minus baseline, mean ± sample SD (n=4) |
|---|---:|
| Unserved electric energy | +191,763.58 ± 476.31 kWh |
| Interrupted feeder-zone hours | +288 ± 0 |
| Unique reached communication participants | +3,734.75 ± 38.71 |
| Message exposures | +7,918.50 ± 97.82 |
| Grocery spoilage | +316.01 ± 45.68 abstract units |
| Unmet grocery demand | +152.37 ± 33.65 abstract units |
| Grocery sales | −119.46 ± 91.45 abstract units |
| Completed clinic visits | +1.00 ± 18.17; **no directional finding** |
| Clinic queue at end | +2.25 ± 18.52; **no directional finding** |
| Recorded retail stockouts; payment failures | +0 and +0; inventory/payment buffering may mask effects |

The supply multiplier is restored explicitly at simulated hour 49. The final `mean_power_service` is therefore 1.0 in both branches; it is **not** a measure of cumulative disruption. Paired differences demonstrate that implemented energy, communications, purchasing and spoilage dependencies are exercised; they cannot validate their real-world magnitudes. In this experiment `behavior_adoptions` remained zero: a functioning delivery network and message reach **must not** be misrepresented as measured reinforced behavioral adoption.

## Negative controls and coverage

The 16 automated tests include deterministic seeds and between-seed variation, exact monetary/escrow/reserve conservation, physical goods bookkeeping, reserve advances, capacity-constrained freight/commutes, frozen observations and no direct inter-household state access, restriction of fabricated firsthand claims, forwarding without counting repeated copies as independent sources, power protection and restoration, power/communication coupling, road saturation, a coupling ablation, weekend staffing, medication physical retail, and next-open store scheduling. Note that frozen observations do not sandbox malicious arbitrary Python policies sharing mutable state.

Eight synthetic single-domain smoke interventions were compared to same-seed ordinary controls at 1,200 households / three days: power, road, communication, supply, payments, retail, services and demand. Measured examples: road factor generated **663** additional travel-capacity rejections; payment infrastructure factor generated **1,413** network declines; supply reduction cut upstream supplier stock by approximately **1,555** bundles; a communication factor reduced unique message reach by **59**; and a service factor created approximately **367.5 m³** additional unmet water demand. Other secondary changes and no-effect cases remain in `internal_validation.json`. Cross-domain transport and payment effects occur through reservations/authorizations rather than data-independent scripted events. These are **software responses to assumed multipliers**, not held-out historical benchmarks.

## Empirical validation still failing or outstanding

The 49-entry `provenance.json` labels A directly reported evidence, B published methods/institutional context, and C explicit synthetic assumptions. EIA's US 2023 861 kWh/account/month, Census 2024 Columbus median income, FHWA BPR functional form, FedACH timing context and Centola's online-health diffusion experiment are anchor/context sources, **not** multi-domain local calibration. Assumed behavior distributions, network rates and infrastructure capacity require external fitting. In particular, no independently published normal-operation **and** disruption-response benchmark has been reproduced for *every* domain; there is no validated Columbus feeder load-flow, road GIS network, real bank liquidity protocol, medically verified clinic/water continuity, independently estimated local activity schedules or independent diffusion effect size. `docs/limitations.md` lists omitted operational safeguards, domain simplifications and transferability issues. Held-out scenarios/data have not been consumed or passed.

The 1,000,000-household / 120-zone / 2,400-retailer world **initialized and passed initial invariants** (~3.88 seconds and ~418 MB peak RSS in one local trial, with ~3.73 million directed graph edges and 1,000,006 queued events). A complete one-day run at that scale **did not finish within a 200-second test bound**. A 100,000-household one-day run completed (~6.04 s/~187 MB in a local trial). Large-config initialization is not demonstrated large-scale throughput.

## Release decision

**Do not designate 0.1.0 as the final frozen research environment** requested by the assignment. A reproducible source snapshot and SHA-256 manifest are provided, but credible empirical parameter calibration, independent per-domain validation, institutional protocol verification, severe-scenario empirical distribution fitting and complete million-unit performance proof are outstanding. This report retains failures and ambiguous effects instead of modifying data to pass them.

## 0.2.0-dev calibration supplement (2026-10-24)

The historical 0.1.0 16-test / 49-entry counts above are retained as a snapshot, not current release counts. The source-linked `docs/calibration.md` gives results from **19 currently passing regression tests and 56 current provenance records**. Its two AEP points are fitted inverse external shocks using a known **mismatched denominator**. No independent empirical validation across all domains has been passed, and the original release decision remains **do not freeze**. See `calibration/results.json` for reproducible actual full-engine outputs, including both no-effect and direction-changing downstream metrics.

## 0.3.0-dev operational availability supplement (2026-10-24)

The historical reports above refer to their respective version snapshots and have not been silently reused as new-version experiment results. The new 25-test suite passes. `docs/operational_availability.md` and `calibration/availability_results.json` document a separately ablatable extension, 66 current provenance records, three-seed fit checks against *hypothetical* 2022 ComEd respondent choices, actual historical comparisons not fitted due to incompatible exposure/denominator, and unsupported long-run building and firm outcomes. There is no death/illness modeling or independent empirical validation of local behavior. Routine 10,000-household / four-day smoke run had zero unintended relocation and preserved accounting; a separate one-day complete blackout beginning at hour 24 generated 3,243 relocated and 3,243 returned units by end of day four, not a historical prediction.

## 0.5.0-dev coupling supplement (2026-10-24)

`python -m unittest discover -s tests -v` reported **Ran 48 tests in 1.764s** / **OK**. `python -m scripts.check_coupling` wrote `calibration/coupling_results.json` with `"transport_freight": true`, `"payments_settlement": true`, `"power_retail": true`, `"finance_and_markets": "scope_refuse"`. Magnitudes not calibrated. Regenerated `provenance.json` has **84** records. Do not freeze.
