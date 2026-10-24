# Evidence-bounded calibration — RegionalSim 0.2.0-dev (2026-10-24)

**Decision: partial, conditional, NOT independently validated.** Reproduce with `python scripts/calibrate.py`. The machine-readable source register is `benchmarks/observations.json`; fitted parameter trials, independent RNG-seed checks of the **same** event, complete-world verification, and negative results appear in `calibration/results.json`.

## Method and source separation

- Ordinary mobility: Census Reporter / U.S. Census Bureau, 2024 ACS 1-year for Columbus, OH CBSA 18140: 24.1 ± 0.4 minutes mean commute. Fit ONLY the BPR free-flow parameter `Config.free_flow_minutes`; alpha 0.15 and beta 4 remain unchanged. Caveat: modeled `mean_travel_minutes` covers all completed vehicle/freight trips, while ACS covers commutes. This is a proxy, not identical measurement.
- Case event: AEP Ohio, June 15, 2022, 2 p.m. update (https://www.aepohio.com/company/news/view?releaseID=8562): roughly 170,000 central Ohio customers without power at Tuesday 8 p.m. peak; 87,000 Columbus customers reported in the Wednesday 2 p.m. update. **Source-quality warning:** that AEP bulletin also prints a statewide figure (49,000) lower than its Columbus figure (87,000), which is internally inconsistent. WOSU independently reported 87,560 Franklin County accounts at 1:11 p.m. Wednesday (https://www.wosu.org/news/2022-06-14/storms-bring-down-power-lines-across-ohio-columbus-opens-five-cooling-centers); it corroborates the order of magnitude, not the identical place or time. The 87,000 target is therefore provisional. AEP's earlier June 14 9:30 p.m. release reports approximately 169,000 Columbus-area customers at its reporting time (https://www.aepohio.com/company/news/view?releaseID=8560). Counts are approximate, encompass storm damage plus controlled shedding, and include residential **and** other customer accounts.
- Expansion proxy: 2024 ACS **880,121 ± 6,287 CBSA households** (https://censusreporter.org/profiles/31000US18140-columbus-oh-metro-area/). AEP's central/Columbus outage reporting boundaries are not identical to this CBSA; neither is the year nor all-customer vs residential composition. Dividing the AEP counts by this total is a **deliberately weak transfer assumption**, not an empirical outage rate or a measured 2022 utility market share.
- The `power_rank` model exposes fixed household-level service as `power_rank[i] < power_ratio[zone]`. This is a fractional scalar-energy **proxy**; households are NOT connected to real circuits and the household observation is NOT a documented actual physical feeder-level switch. No change was made to reserve, critical-load priority, transport constraints, settlement or conservation safeguards.
- PUCO (2023), *Summer 2022 electric outages*, describes distinct forced-shed actions, circuit selection, actual utility coordination and repairs (https://dam.assets.ohio.gov/image/upload/puco.ohio.gov/empliibrary/files/Power%20outage%20review/outage%20report%20010323.pdf). NERC (2023), *AEP Summer 2022 Storm Event Observations*, reports 500 MW firm shed on June 14 and 450 MW on June 15 (https://www.nerc.com/globalassets/our-work/reports/event-reports/aep_summer_2022_event.pdf). These are **NOT interchangeable** with numbers of customers out, and are not fitted using the synthetic household proxy. PUCO also reports Event 3's load-shed restoration by Thursday 04:51; the model takes this as a prescribed external end time, not an independently predicted repair time.

The 2022 event is replayed in a **relative synthetic four-day window**, not on the simulator's ordinary April 2024 calendar. Relative hour 20 stands for Tuesday 8 p.m.; relative hour 38 for Wednesday 2 p.m. Two pieces of externally imposed power-supply capacity are fitted separately to their respective AEP observations. The final restore at hour 52.85 is externally set from PUCO and does not validate the model's recovery capability.

The ordinary clock and generic stochastic scenario presets remain as before. The calibrated incident file is opt-in; the random severe-shock generator is **still uncalibrated**.

## Numerical fitting and observations

Three fitting random seeds: 42–44. Two other random seeds: 46–47. Different seeds for the *same fitted event* are a software generalization check, NOT independent historical validation. Two observations determine two distinct external multipliers: this is inverse forcing, not independent identification of engineering parameters.

| Quantity | Documented target | Fitted input | Fitting seeds mean | Other seeds mean | Status |
|---|---:|---:|---:|---:|---|
| Mean model trip duration (ACS commute proxy) | 24.1 ± 0.4 min | `free_flow_minutes=23.769318` | 24.1 min by scaling construction | 24.185 min | Inside published ACS MOE, metric mismatch unresolved |
| Tuesday 20:00 outage-count **proxy** | ~170,000 AEP customer accounts | `power multiplier=0.65775390625` | 169,423 customer equivalents | 170,127 customer equivalents | Fits this selected point conditionally; boundary mismatch |
| Wednesday 14:00 outage-count **proxy** | ~87,000 AEP customer accounts | `power multiplier=0.73123046875` | 86,487 customer equivalents | 87,704 customer equivalents | Fits this selected point conditionally; boundary mismatch |

Fitting-seed outage fractions: 0.19250 and 0.098267; other-seed fractions: 0.19330 and 0.09965. Expansion is `simulated fraction × 880121`, with NO invented statistical confidence interval on the AEP count. The inconsistent AEP bulletin prevents assigning a trustworthy measurement CI to the second point. The ACS denominator MOE alone changes the first proxy target between about 0.1918 and 0.1945; this is much smaller than unquantified area/account mismatch. Bisection trials are retained in `calibration/results.json`. Rounding and weather-shape/stochastic changes explain small differences between one-hour probes and complete DES trajectories.

An actual integrated four-day run on the two other seeds records **1,919 and 1,947 unserved households at hour 20**, and **985 and 1,008 at hour 38**. At its final hourly tick, the modeled unserved-household count is zero, because external restoration has already been applied. This is NOT a fit to the actual storm repair pathway. All 19 automated tests pass, including shock-before-hourly-power tick and conservation tests.

## Cross-domain effects, not external calibrations

Paired full-world disrupted minus same-seed routine outcomes (seeds 46, 47; n=10,000; 4 days):

| Model output | Seed 46 | Seed 47 | External measurement status |
|---|---:|---:|---|
| Unserved electricity (kWh; 10k synthetic accounts) | +65,833 | +65,625 | No geographically and load-comparable observation in register |
| Grocery spoilage (abstract bundles) | +177.38 | +62.87 | No observed grocery-loss distribution |
| Unmet groceries (abstract bundles) | +53.135 | +20.093 | No observed need and shortage distribution |
| Additional message exposures | +6,862 | +6,838 | No Columbus individual-recipient benchmark |
| Additional unique message recipients | +4,064 | +3,998 | Cannot compare against social-platform impressions |
| Grocery retail sales (abstract bundles) | −5.68 | +118.30 | **Direction changes by seed**; no finding |
| Clinic completions | −16 | +3 | **Direction changes by seed**; no finding |
| Water unmet (m³) | 0 | 0 | Critical-load buffer is active; not a real water-utility validation |
| Payment failures | 0 | 0 | No payment-network historical target; buffering active |
| Shop power closure attempts | +1,156 | +449 | No event-level shop trading data |

These values are scenario-generated internal outcomes, NOT reproduced historical impacts. The two-seed spread is not a confidence interval. In particular, do not fit spoilage, behavioral adoption, water interruption or medical outcomes simply to force a desired effect size.

## Gaps and negative controls

| Domain | Calibration status | What is needed before scientific use |
|---|---|---|
| Regional electricity | TWO outage-count proxy points fitted; physically deficient | AEP 2022 account denominator by geography/class, customer interruption hourly trajectory, real zonal/circuit topology, transmission load, field restoration and 2022 weather; MW-vs-count joint validation |
| Mobility | ONE ordinary mean-fit proxy, no shock fit | Local origin-destination and classified trips, link counts and known road incident demand/capacity/time response; use commute-only output |
| Payments/banks | Conservation/software tests only | Incident-specific authorization success/latency, reserve data and actual settlement and legal constraints; no evidence supports the synthetic 0.1 shock factor |
| Retail/wholesale | Conservation/software tests only | Retailer/SKU inventories, stockouts, deliveries, post-outage food losses, uncertainty and time series; abstract bundles prevent direct matching |
| Communication/diffusion | Mechanism only | Account-level notification timestamps, independently identifiable recipients, communication availability, firsthand relay and behavior; PUCO cites 57 posts / 3.51m impressions service-territory-wide, NOT equivalent to unique simulation household exposures |
| Essential services | Continuity mechanism only | Local water process capacities, backup-power restoration, healthcare staffing, visits and queues from an actual incident |
| Household response | Synthetic policies only | Panel-based repeated observations and estimates of delayed precaution, price and stockout responses with measured uncertainty |
| Joint shock distributions | Not calibrated | Historical event catalog with denominators, temporal overlaps, geographic footprints, return periods and correlated hazards |

**Independent negative-control opportunity unavailable in this version:** PUCO reports a later June 21–22 high-heat period without directed shedding; this simulator has no temperature-dependent transmission loading/fault model and therefore cannot honestly claim to reproduce the storm-plus-heat causal distinction. Independent per-domain heldout response benchmarks have **not** been passed. The package is **not** a validated frozen experimental release.

## Commands

```bash
python -m unittest discover -s tests -v
python scripts/calibrate.py
regional-sim --config configs/calibrated_2024.json --shock-json configs/aep_2022_proxy_shocks.json --out output/calibrated_case
regional-sim --config configs/calibrated_2024.json --out output/calibrated_control
```

The last two commands share the configured seed and differ only by the external shock file. Their outputs are synthetic and should not be interpreted as a forecast or a literal reconstruction of June 2022.
