# Explicit limitations and outstanding validation (0.1.0)

This is executable **prototype software**, not the validated scientific release required by the uploaded assignment. Its important unvalidated extrapolations are maintained in `provenance.json` as category C; the register has 49 entries but does not yet cover every implied independent variable.

- Synthetic Columbus CBSA population is **not** an ACS PUMS microsimulation. Median income is anchored; household size/income/employment/access correlations and poverty/inventory distributions are not locally estimated. Its one-million scenario is an enlarged synthetic sampling of the same named metropolitan area, not a geographical estimate of actual one-million household CBSA counts.
- Payroll, firm assets, outside-region trade and liquidity buffers are explicit and balanced but lack regional balance-sheet, FDIC, NACHA and Reg CC calibrations. No check deposit logic, bank holidays, repayment schedule for collateral facility, credit risk or card-network legal compliance. NERC EOP-011-4 postdates the 2024 simulated clock: protective priority is conceptual, not claimed to be that standard implemented in 2024.
- The scalar feeder supply model has neither distribution power-flow validation nor actual Columbus operator feeder data, no phase/voltage/frequency/relay settings, and no modeled fault diagnosis, repair crews or automatic protective relays beyond priority capacity allocation and deterministic factor-restoration events. `duration_hours` restores capacity exogenously by design.
- Aggregate corridor transport lacks a spatial O-D network, transit, delivery time-window contracts, return trips and actual regional capacities. One completed road reservation represents a one-way vehicle-equivalent. BPR *form* is documented; local capacity coefficients are not calibrated.
- Grocery `bundle` and medicine `unit` are abstract quantities. Upstream production is accounted as explicit boundary input but fuel, industrial production, packaging and raw materials are excluded. Spoilage delay/rate and institutional stock buffers are C assumptions. Warehouse and delivery agreements are simplified.
- Communication multiplex degree, attention, trust, routine messaging and reinforcement thresholds are C assumptions. News is a delayed relay of genuine operator messages, not a fitted media ecosystem. Evidence of simple/complex diffusion justifies mechanism selection, not actual effect size for grocery purchasing. A shared Python policy instance is not an adversarial sandbox.
- Clinic visits have synthetic hazard, FIFO rules and medicine consumption; no detailed health statuses, clinical urgency, facility staffing rosters, ambulances or health outcomes. Water service uses scalar flow only. No deaths/serious outcomes are asserted.
- Routine/seasonal/severe shock multipliers and durations are transparent **synthetic priors**; no severe-shock frequency, covariance or historical joint distribution has been estimated. A targeted `power_shock.json` is a software test input, not a constructed disaster scenario used to fit desirable response.
- `traces.ndjson` is sampled by household by default. Aggregated and institutional records are always preserved; some private state transformations (e.g., biological consumption) appear as state totals rather than per-person messages. Daily metrics are cumulative unless named as an instantaneous state.
- One-million-household initialization completed in ~3.88 s with ~418 MB peak RSS under the test environment. A **full one-day one-million-household run did not finish within 200 s**, and its final performance/memory needs are unverified. A 100k one-day run completed in ~6.04 s/~187 MB. The large configuration is a documented intended target, not certified throughput.
- At least one independently sourced normal-operating and disturbance-response benchmark **per domain has not been passed**. Existing conservation, paired runs and negative controls test the implementation's internal consistency, not external validity. Unperformed or failed tests are not relabeled successes. Full preregistered freeze, independently held-out response trials and validation-based final release remain outstanding.

## 0.2.0-dev partial calibration supplement

See `docs/calibration.md`. Only ACS travel duration (metric-incompatible commuter vs all-trip proxy) and a June 2022 AEP two-point outage-count (all-account vs 2024 CBSA household-denominator proxy) have been numerically fitted. Fitted exogenous capacity factors cannot identify actual damaged transmission capacity, controlled circuit switching, spatial outage allocation, restoration effort, or cross-domain damage. Simulated post-outage food losses and messaging are **unvalidated**, not reported historical effect-size matches. No independent per-domain heldout disturbance response is demonstrated. Preset random severe-shock distributions, all legacy C-level behavioral parameters and financial/health/retail mechanisms remain uncalibrated.

## 0.3.0-dev availability extension
See `docs/operational_availability.md`. Actual historical responses are not equated with survey choices, property functionality with structural safety, or temporary absence with death. C-level assumptions include elapsed-time interpolation, outside-region resource boundary, return timing, SMB-to-retail transfer and unmodeled adaptation after day one. Do not interpret long-run firm closure or residence habitability using this extension.

## 0.3.1-dev participant policy and communications

Relocation is now policy-owned with an individual survey-proxy preference threshold; no policy request means no move. Simulated messages can change the baseline grocery target following independent stockout reports, but **there is no calibrated communication effect on relocation**. Both the 2.5-to-4-day response and most network contact/trust/attention/propagation rates are C-level assumptions. Stated blackout response scenarios also communicate an expected restoration horizon, unlike the script which acts on elapsed observed outage; this is a transfer limitation. Outside-region resources and realistic return decisions remain outside the modeled boundary.

## 0.4.0-dev travel-information calibration limits

The new Fix I-5 48% departure-adjustment / 44% route-change marginals are respondent-level observed *closure behaviors*, not a randomized effect of a particular message. Applying them to first informed Columbus-synthetic commuters is a geographic/denominator transfer. Peer relocation plan routing is C-level; no quantified peer-induced decision to relocate. Road topology, parallel capacity, employer flexibility, alert reach and latency remain C-level. After additional communication events, the previous availability fit now differs by −1.25 percentage points at 24h and −0.31 at 336h (three seeds); see the regenerated `calibration/availability_results.json`. No medical outcomes have been added or evaluated.

## 0.5.0-dev coupling checks and finance refuse

Scripted-human coupling **direction** holds for transport→freight, payments→electronic declines, and power→retail closures (ablation). Magnitudes are **scope refuses**; see `docs/coupling_checks.md`, `docs/validation_scope.md`, and `calibration/coupling_results.json`. Quantitative depositor-run rates and global markets are a **scope refuse** (`docs/finance_scope.md`), not a missing metadata patch. Fix I-5, Sue Wing, and AEP parameters were not retuned.

## 0.5.1 parameter freeze

World-model defaults and packaged inverse-fit configs are **locked** at [`docs/frozen_parameters.md`](frozen_parameters.md) / [`configs/frozen_world_parameters.json`](../configs/frozen_world_parameters.json). `tests/test_frozen_parameters.py` guards against silent drift. This is **not** the full world freeze bar in [`INSTRUCTIONS.md`](../../INSTRUCTIONS.md): independent magnitude validation and held-out benchmarks remain outstanding.

## 0.5.1 provenance and validation scope

Contextual sources from the 2026-11-04 C-parameter scan are recorded in `provenance.json` without upgrading C to A. Magnitude claims without a matching denominator are **scope refuses** ([`docs/validation_scope.md`](validation_scope.md)): Columbus truck delays, card/ACH incident rates, spoilage volume, Fix I-5 geographic transfer, independent AEP event response, executed Sue Wing relocations, joint shock catalogs. Do not retune Fix I-5, Sue Wing, or AEP multipliers to close those refuses.

## 0.5.1 validation battery (protocol)

Preregistered 30-day software battery: [`docs/validation_battery.md`](validation_battery.md). Held-out seeds 9091–9094. Direction and conservation **passed** (`calibration/validation_battery.json`, 96.233 s). Magnitudes remain scope refuses. Traces discarded.
