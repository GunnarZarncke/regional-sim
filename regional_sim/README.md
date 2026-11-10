# RegionalSim 0.5.2 — synthetic Columbus metropolitan prototype

An open-source, event-driven, six-domain regional socioeconomic simulation. **Research prototype with partial proxy calibration; not independently validated or operationally certified.** It does not infer death, illness severity, or any policy's desired outcome.

## Install and execute

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
regional-sim --config configs/development.json --out output/routine
regional-sim --config configs/development.json --days 5 --shock-json configs/power_shock.json --out output/power
regional-sim --households 1024 --days 3 --seed 11 --scenario moderate --out output/quick
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`. The runtime depends only on Python >=3.10 and NumPy >=1.24. The simulation has no network access, no runtime downloads, and no optional machine-learning dependency.

The development preset includes **10,000 individual household decision units**, 12 aggregated geographic zones and 24 retailers over 30 days. The large preset (`configs/large.json`) specifies 1,000,000 households, 120 zones and 2,400 retailers. It **initializes** at 1,000,000 households but a complete one-day run did not finish within our 200-second test bound; it is not a performance guarantee. A 100,000-household one-day run completed.

`--config` loads JSON defaults; explicit CLI flags override them. Options: `--households`, `--days`, `--seed`, `--zones`, `--retailers`, `--scenario routine|seasonal|moderate|severe`, `--shock-json`, `--full-trace`, `--sample-rate`, `--free-flow-minutes`, `--disable-coupling`, `--out`. The fixed target is Columbus, OH CBSA 18140; zoning is synthetic and can be refined at higher population scale. Synthetic clock starts on **Monday, April 1, 2024** at 00:00 Eastern local time; there is no daylight-saving transition engine, bank-holiday calendar or other historical event playback.

Example generic external disturbance file:

```json
[{"at_hour":25,"domain":"power","zone":-1,"multiplier":0.35,"duration_hours":24}]
```

Domains: `power`, `road`, `road_closure` (opt-in targeted main corridor), `communication`, `supply`, `payments`, `retail`, `services`, `demand`. A zone of -1 selects the full region. Existing factors multiply for overlapping events and each is removed by a distinct restoration event. No response sequence is hand-coded. Routine and seasonal scenarios use no artificial severe shocks. The stochastic moderate/severe distributions are marked **C-level assumptions, not fitted historical hazard distributions**.

## Outputs

Each run writes `daily.csv` (cumulative and daily-state metrics), `summary.json` (configuration, result, event counts, a network-clustering sample), and `traces.ndjson` (local only; not committed—see `docs/report_artifacts.md`). The NDJSON contains observations, requested/accepted/executed/completed actions, purchases, goods and payment transfers, deliveries, messages, individual behavioral adoption, protection/other institutional events, shocks and daily state snapshots. Personal records are **sampled deterministically by agent ID** unless `--full-trace` is supplied; all aggregate and institutional records are kept. `--sample-rate 0` suppresses personal traces, not their aggregate event counts. Never treat a sampled NDJSON as a full individual event census.

## Replacing participants' policies

```python
from regional_sim import World, Config
from regional_sim.policy import Action

class ExamplePolicy:
    def decide(self, observation, rng):
        if observation.groceries < observation.grocery_need_daily:
            return [Action("buy", amount=1, delay_hours=0.3)]
        return [Action("none")]

w = World(Config(households=10000, days=7, trace="my-trace.ndjson"), policy=ExamplePolicy())
print(w.run())
```

Policy code receives only frozen participant observations (with personal balances/inventory, on-site observations, access-gated requested data, received messages and pending request IDs) and an RNG. The engine owns all account balances, inventory, transport reservations, message routing and the event queue. Policies may emit **lists of ordinary actions**, including `buy`, `buy_medicine`, `commute`, `pay_bill`, `clinic`, `query`, `send`, `forward`, `ask`, `agree`, `disagree`, `intended_message`, `completed_message`, `relocate`, `return`, `review`, `schedule`, `cancel`, or `none`. The world validates claims, eligibility, capacity, ownership, information access and transaction feasibility. Future comparison-policy objectives do not exist in the model.

See `docs/technical.md` for all action semantics, conservation equations and domain couplings; `provenance.json` for 79 parameter/source records; `docs/limitations.md` for failures and gaps; `reports/travel_information_validation.md` for current travel experiments (`reports/validation.md` contains earlier-version tests). Run `python scripts/validate.py` to generate paired-seed comparison outputs and domain shock smoke checks.

## Status

All automated unit/integration tests must pass before using the generated output as a software example. This build is **not the validated frozen release specified in the assignment**. Independent empirical disturbance benchmarks, local calibration, legal banking implementation, electrical topology / protective relays, GIS road network, service continuity protocols, and million-unit run profiling are still outstanding. `MANIFEST.sha256` identifies the artifact contents, not scientific validation.

License: MIT (`LICENSE`).

## Partial source-linked calibration (0.2.0-dev supplement)

The previous 0.1.0 internal-software report and traces remain reproducible legacy baseline artifacts. The new opt-in benchmark/calibration workflow is **partial and explicitly not independently validated**:

```bash
python scripts/calibrate.py
regional-sim --config configs/calibrated_2024.json --shock-json configs/aep_2022_proxy_shocks.json --out output/calibrated_case
regional-sim --config configs/calibrated_2024.json --out output/calibrated_control
```

It fits a configurable BPR free-flow time to a 2024 Columbus ACS commute-time **proxy** and two *external* supply multipliers to approximate June 2022 AEP outage-count **proxies**, not to a physical circuit reconstruction. Source observations and explicit comparability limits are in `benchmarks/observations.json`; trials, seed checks and measured paired outcomes are in `calibration/results.json`; interpretations and missing independent validation are in `docs/calibration.md`. Three new regression tests cover precise shock-tick ordering, outage boundedness and free-flow sensitivity. The provenance generator now produces **56** entries, including observed benchmarks and separately flagged inverse-fitted C-level quantities. The archived 0.1.0 report's statement of 16 tests / 49 parameters describes the older snapshot, not this supplement.

The new `--free-flow-minutes` flag (`Config.free_flow_minutes`) defaults to the legacy 24 minutes; the calibrated configuration sets about 23.7693. The `power_unserved_households_*` counters describe a fixed-rank *scalar service proxy*, **not an engineered feeder/customer outage circuit model**. Externally scheduled restoration remains an input. Never use the two fitted points as evidence of independent shock-response validation.

## Optional reversible operational availability (0.3.0-dev)

Operational absence/closure is not mortality, serious illness, structural damage or automatic bankruptcy. A provisional evidence-linked **stated-response** fit represents households' temporary relocation under actual local grid loss, and store-site normal grid availability separately from synthetic retailer operating workarounds. Temporary relocation consumes road capacity; absent households cannot perform local work, shopping or clinic visits, but are retained in the population and outside-region food/medicine requirements are logged as **unresolved boundary needs**, not assumed fulfilled. The extension is on by default; `--no-availability` disables it.

```bash
python -m scripts.validate_availability
regional-sim --config configs/development.json --no-availability --out output/ablation
```

See [docs/operational_availability.md](docs/operational_availability.md), `benchmarks/availability_observations.json` and `calibration/availability_results.json` for fitted survey endpoints, actual blackout and hurricane comparators *not* fitted, three-seed checks and all gaps. These are **not independently historically validated**; physical buildings have no damage or safety state. Prior example output folders and `calibration/results.json` were generated with the earlier 0.2.0-dev version; re-run them to compare model versions.

## Participant-controlled relocation and communication (0.3.1-dev baseline; superseded by the 0.4.0-dev travel additions below)

**Breaking API extension:** `Observation` now exposes the participant's own consecutive
outage/restoration hours, private survey-proxy preference threshold, relocation/return
request IDs, pending state, and availability-module status. `Action("relocate")` and
`Action("return")` are **requested by the participant policy**, never autonomously
selected by the engine. A baseline scripted relocation has
`Action("relocate", payload="while_unpowered")`, which expires before departure if
home power is restored; alternative policies may issue unconditional actions.
Roads can defer departures/returns and queued requests can be cancelled until
travel actually begins. `Action("review", delay_hours=...)` requests a future
participant decision without synchronizing all households to the grid clock.
Electricity state changes only notify policies; `--no-availability` rejects movement.

Actual delivered stockout reports **can affect** baseline grocery purchasing:
`current_claim_exposures["retail_stockout"] >= adoption_threshold` switches the desired
stock from 2.5 to 4 days. The engine counts **distinct original sources**, not repeats
of the same forwarded message. Participant decisions also affect what gets reported,
asked and forwarded; messages are delayed and access/attention-gated. **There is no
calibrated effect of social messages on whether baseline participants choose relocation**: its survey-proxy
propensity uses only the participant's own observed loss of power. Custom policies
may use personal messages and exposure counts to make relocation decisions, but
such response coefficients would be experimental C-level assumptions.

Evidence: Centola (2010), DOI 10.1126/science.1185231, demonstrates an experimentally
identified complex-contagion mechanism for online health-tool adoption (roughly
54% clustered versus 38% randomized groups), **not** stockout or relocation effects.
Sadus, Göttmann & Schubert (2023), DOI 10.1007/s10389-022-01727-x, observed an
association of descriptive social norms with self-reported stockpiling among 861
German respondents during COVID-19; this is not a causal numerical calibration.
Sue Wing et al. (2025), DOI 10.1038/s41467-025-58537-4, supply *hypothetical*
blackout relocation intention anchors (33% at 1 day; 83% at 14 days), not actual
completed moves or a peer-message effect. Most timing, trust, message-delivery and
consumption-response parameters therefore remain synthetic. See
`docs/participant_communication.md` and regenerated `calibration/availability_results.json`.

Run `python -m unittest discover -s tests -v` and
`python -m scripts.validate_availability` to reproduce version-specific results.

## Version 0.4.0-dev: communication-aware commuting and relocation travel

The `road_closure` shock (main corridor only) now causes authentic, delayed, zone-local official road notices. A generic `road` capacity shock still affects both modeled corridors. Actual transport capacity is reserved separately on the alternate route. A participant's *own* failed departure can be reported as a delay, never automatically elevated to an asserted closure. Participants can change their commute route/departure time after **receiving** information; unexecuted deferred commute, relocation and return requests can be cancelled and revised by their policy. Genuine direct peer relocation plans can influence the route of a participant who already intends to leave, but cannot automatically cause departure. `ScriptedPolicy` remains interchangeable; the engine never chooses participants' travel strategies.

The closure-response **marginal targets** transfer the observed 48% avoidance of rush hour and 44% route change reported in Ye, Mokhtarian & Circella's Fix I-5 Sacramento survey, not a causal effect of message receipt. Source-denominator differences, joint effects and generalization to Columbus remain unvalidated. No medical outcomes were added, calibrated or analyzed. Run `python -m scripts.calibrate_travel_information` and `python -m unittest discover -s tests -v`. The detailed calibration, constraints, ablation and gaps are in `docs/travel_information.md`.

Post-change relocation-proxy regression: `python -m scripts.validate_availability` now reports 31.75% simulated temporary absence at one day versus the original 33% *stated* anchor (−1.25 percentage points) and 82.69% at fourteen days versus 83% (−0.31 percentage points), three seeds. No attempt was made to conceal this residual by changing communication parameters. These are not observed relocation validation results.

To reproduce the new 10,000-household road closure with trace records:

```bash
regional-sim --households 10000 --days 3 --seed 47 --shock-json configs/road_closure_information.json --no-availability --sample-rate 0.002 --out output/road_closure
```

## Version 0.5.2: scoped software freeze

Conservation, scripted coupling direction, and 1M×30d scale are frozen (`docs/scoped_world_freeze.md`). Parameters remain the 0.5.1 lock. This is not the full world freeze bar.

## Version 0.5.1: frozen world parameters

Numeric defaults and packaged calibration configs are locked; see `docs/frozen_parameters.md` and `configs/frozen_world_parameters.json`. This is not the full validated world release.

## Version 0.5.0-dev: scripted-human coupling checks

Mechanism **direction** under the default scripted policy is recorded for freight under `road_closure`, electronic declines under a payments shock, and store closures under power with `power_to_retail` ablated. Magnitudes are gaps. Finance withdrawal rates and global markets are a documented scope refuse (`docs/finance_scope.md`, `docs/coupling_checks.md`). Fix I-5 / Sue Wing / AEP coefficients were not retuned.

```bash
python -m unittest tests.test_coupling -v
python -m scripts.check_coupling
```
