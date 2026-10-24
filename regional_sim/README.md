# RegionalSim 0.1.0 — synthetic Columbus metropolitan prototype

An open-source, event-driven, six-domain regional socioeconomic simulation. **Research prototype, not a calibrated, validated, operationally certified release.** It does not infer death, illness severity, or any policy's desired outcome.

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

`--config` loads JSON defaults; explicit CLI flags override them. Options: `--households`, `--days`, `--seed`, `--zones`, `--retailers`, `--scenario routine|seasonal|moderate|severe`, `--shock-json`, `--full-trace`, `--sample-rate`, `--disable-coupling`, `--out`. The fixed target is Columbus, OH CBSA 18140; zoning is synthetic and can be refined at higher population scale. Synthetic clock starts on **Monday, April 1, 2024** at 00:00 Eastern local time; there is no daylight-saving transition engine, bank-holiday calendar or other historical event playback.

Example generic external disturbance file:

```json
[{"at_hour":25,"domain":"power","zone":-1,"multiplier":0.35,"duration_hours":24}]
```

Domains: `power`, `road`, `communication`, `supply`, `payments`, `retail`, `services`, `demand`. A zone of -1 selects the full region. Existing factors multiply for overlapping events and each is removed by a distinct restoration event. No response sequence is hand-coded. Routine and seasonal scenarios use no artificial severe shocks. The stochastic moderate/severe distributions are marked **C-level assumptions, not fitted historical hazard distributions**.

## Outputs

Each run writes `daily.csv` (cumulative and daily-state metrics), `summary.json` (configuration, result, event counts, a network-clustering sample), and `traces.ndjson`. The NDJSON contains observations, requested/accepted/executed/completed actions, purchases, goods and payment transfers, deliveries, messages, individual behavioral adoption, protection/other institutional events, shocks and daily state snapshots. Personal records are **sampled deterministically by agent ID** unless `--full-trace` is supplied; all aggregate and institutional records are kept. `--sample-rate 0` suppresses personal traces, not their aggregate event counts. Never treat a sampled NDJSON as a full individual event census.

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

Policy code receives only frozen participant observations (with personal balances/inventory, on-site observations, access-gated requested data, received messages and pending request IDs) and an RNG. The engine owns all account balances, inventory, transport reservations, message routing and the event queue. Policies may emit **lists of ordinary actions**, including `buy`, `buy_medicine`, `commute`, `pay_bill`, `clinic`, `query`, `send`, `forward`, `ask`, `agree`, `disagree`, `intended_message`, `completed_message`, `schedule`, `cancel`, or `none`. The world validates claims, eligibility, capacity, ownership, information access and transaction feasibility. Future comparison-policy objectives do not exist in the model.

See `docs/technical.md` for all action semantics, conservation equations and domain couplings; `provenance.json` for 49 parameter/source records; `docs/limitations.md` for failures and gaps; `reports/validation.md` for actual measurements. Run `python scripts/validate.py` to generate paired-seed comparison outputs and domain shock smoke checks.

## Status

All automated unit/integration tests must pass before using the generated output as a software example. This build is **not the validated frozen release specified in the assignment**. Independent empirical disturbance benchmarks, local calibration, legal banking implementation, electrical topology / protective relays, GIS road network, service continuity protocols, and million-unit run profiling are still outstanding. `MANIFEST.sha256` identifies the artifact contents, not scientific validation.

License: MIT (`LICENSE`).
