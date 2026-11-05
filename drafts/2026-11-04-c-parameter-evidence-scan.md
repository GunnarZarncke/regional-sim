# Web scan: substantiating category C parameters (non-Columbus OK)

**Date:** 2026-11-04  
**Scope:** `regional_sim/provenance.json` rows with `evidence_category: C` (excluding already-documented scope refuses: withdrawal probability, global markets).  
**Goal:** Find **A/B-level sources** that support a parameter’s **magnitude, mechanism, or plausibility band**, even when geography or unit differs. Does **not** imply Columbus calibration or freeze.

**Legend**

| Tag | Meaning |
|-----|---------|
| **A-nat** | National (or multi-site) observed statistic; could re-label provenance as A with explicit transfer note |
| **B** | Protocol / engineering / institutional rule |
| **C+** | Evidence supports mechanism or order-of-magnitude; numeric value in sim should stay C until matched |
| **C−** | Little or no external anchor; keep C |
| **⚠** | Evidence suggests current number is misfit |

---

## Households & demographics

| Parameter (provenance) | Model | Scan | Tag |
|------------------------|-------|------|-----|
| Household size mix (1–5) | 0.29, 0.34, 0.16, 0.14, 0.07 | CPS/ACS 2024: **~29%** one-person households; two-person share **~34%** (Census [families release](https://www.census.gov/newsroom/press-releases/2024/families-and-living-arrangements.html), table [C11016](https://data.census.gov/table/ACSDT1Y2024.C11016)) | **A-nat** — sizes 3–5 need B11016 cells; current vector is rough national match for 1–2 |
| Income log-scale SD 0.62 | Lognormal σ | Standard income-modeling identity: σ = √(2 ln(mean/median)); **σ≈0.62 ↔ mean/median≈1.6** ([Schield AMS](https://ww2.amstat.org/meetings/proceedings/2018/data/assets/pdf/867071.pdf), [CMU notes](https://www.stat.cmu.edu/~cshalizi/ineq/21/lectures/03/lecture-03.pdf)) | **C+** — justify σ if ACS mean/median for target year is ~1.6; not verified for Columbus 2024 in this scan |
| Employment probability 0.73 | Household proxy | BLS 2024 **employment–population ratio 60.1%** (16+) ([Table 2](https://www.bls.gov/news.release/srgune.t02.htm)); not same as P(employed \| household) | **⚠ C+** — 0.73 is high vs epop; needs ACS B23025 / person-level employment |
| Remote work given employment 0.17 | Conditional | ACS 2024 **13.3%** of workers worked from home ([Commuting at a Glance](https://www.census.gov/topics/employment/commuting/guidance/acs-1yr.html)); BLS **22.8%** teleworked at work in reference week ([2024 table](https://www.bls.gov/lau/state-telework-table-2024.htm)) | **C+** — 0.17 is between “usual WFH” and “any telework week”; define denominator before upgrading |
| Grocery need (bundles/day) | 0.5 + 0.35×size | USDA ERS 2023 **$3,187/person/year** food-at-home ≈ **$8.73/person/day** ([Amber Waves](https://www.ers.usda.gov/amber-waves/2024/october/u-s-consumers-increased-spending-on-food-away-from-home-in-2023-driving-overall-food-spending-growth)); abstract “bundle” ≠ dollars | **C+** — scale bundle definition to FAH spend or USDA TFP portions |
| Medical consumption 0.1 × 16% HH | Abstract units | No clinical rate matched in scan; primary-care **~1.5 visits/person/year** (see clinics) is separate from “medicine units” | **C−** |

---

## Finance (synthetic institutions)

| Parameter | Model | Scan | Tag |
|-----------|-------|------|-----|
| Same-bank posting 0 h | Instant internal | Real-time internal transfers exist; not a universal A rate | **C−** |
| Retail card-style escrow 1 h | Hold before post | Card **pre-auth holds: 5–7 days** typical retail ([Visa/MC rules via Stripe](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method), [NAB](https://www.nab.com.au/business/payments-and-merchants/merchant-support-centre/preauthorisation)) | **⚠ C+** — 1 h is deliberate compression, not industry timing |
| Collateral facility cap, business endowments | Fictional | No real institution | **C−** |
| Utility obligation $3.10/day | Per HH | Order-of-magnitude check: EIA **861 kWh/mo** national × ~$0.16/kWh ≈ **$4.60/day** (tariff not fixed in scan) | **C+** — ballpark utility outlay; metered tariff would be B/A |

---

## Retail, supply, spoilage

| Parameter | Model | Scan | Tag |
|-----------|-------|------|-----|
| Store/warehouse stock rules | 5N/R, 8N thresholds | Grocery **~23–30 days** on hand blended ([industry turnover summaries](https://aislestock.com/inventory-turnover-grocery), [BBC supply chain](https://www.bbc.com/worklife/article/20200401-covid-19-why-we-wont-run-out-of-food-during-coronavirus)); category spread 3–36 days | **C+** — supports multi-day buffer, not exact 65% reorder rule |
| Boundary production scalars | 1.45N etc. | Mass-balance closure, not empirical throughput | **C−** |
| Opening hours 08:00–22:00 | All stores | Extended grocery hours common; no national survey cited | **C+** weak |
| Staffing minimum ~2% N/R | Onsite | No direct benchmark | **C−** |
| Spoilage 0.0006/h after **6 h** unpowered | Perishable share | **FDA/USDA/CDC: ~4 h** refrigerator safety if unopened ([FDA](https://www.fda.gov/food/food-safety-during-emergencies/power-outages-key-tips-consumers-about-food-safety), [FoodSafety.gov](https://www.foodsafety.gov/food-safety-charts/food-safety-during-power-outage)) | **B/C+** — **6 h delay is ⚠ vs 4 h guidance**; hourly loss rate still unobserved |
| Weekend retail shifts 1/3 | Rotating ID | No employer schedule A source | **C−** |

---

## Electricity

| Parameter | Model | Scan | Tag |
|-----------|-------|------|-----|
| Hourly noncritical shape amplitude 0.18 | Sine | EIA: residential load **low ~5 a.m.**, peak afternoon/evening ([Today in Energy](https://www.eia.gov/TODAYINENERGY/detail.php?id=42915)); regional peak-to-average **~1.78** all-sector New England ([EIA](https://www.eia.gov/todayinenergy/detail.php?id=15051)); smart-meter papers show **~28%** summer vs shoulder daily kWh | **C+** — 0.18 amplitude is plausible diurnal swing; not fitted to Columbus |
| Feeder capacity multiplier 1.65 | Scalar headroom | Distribution engineering headroom; no feeder A data | **C−** |

---

## Mobility & travel (C rows beyond Fix I-5 transfer)

| Parameter | Model | Scan | Tag |
|-----------|-------|------|-----|
| Free-flow trip 24 min (0.4 h) | Corridor | ACS 2024 US mean commute **27.2 min** one-way ([GCT0801](https://www2.census.gov/programs-surveys/acs/data/2024/1_year_geographic_comparison_tables/GCT0801.csv)); Columbus target in provenance ~24.1 | **A-nat / C+** — national mean slightly above 24; Columbus ACS would be A |
| Road hourly capacity formula | 0.42 N/zones | No O-D capacity A source | **C−** |
| Route/departure Bernoulli 0.44 / 0.48 | Advisory | Fix I-5 survey already cited elsewhere; remains **transfer C** | (already documented) |
| Alternate corridor, peer route, deferred commute | Mechanisms | ATIS / Fix I-5 qualitative; no Columbus coefficients | **C+** mechanism |

---

## Communications & policy behavior

| Parameter | Model | Scan | Tag |
|-----------|-------|------|-----|
| Social edges 1×4 layers | Sparse graph | Dunbar layers **~5 / 15 / 50 / 150** cumulative ([PNAS 2018](https://www.pnas.org/doi/10.1073/pnas.1719233115), [mobile-call layers ~4/11/30/129](https://www.technologyreview.com/2016/04/29/160438/your-brain-limits-you-to-just-five-bffs/)) | **C+** — model is **much sparser** than empirical layers; mechanism only |
| Reinforcement thresholds P(1/2/3) | 0.25/0.55/0.20 | Centola **complex contagion** already A in provenance; these probabilities **not** from Centola | **C−** (mechanism A elsewhere) |
| Attention Uniform(0.35, 0.97) | Exposure | No diary / reach study matched | **C−** |
| Backup comms battery **4 h** | Critical nodes | Industry **4–8 h** macro-site batteries common; FCC **proposed 8 h** (never effective federally) ([FCC 07-177](https://www.fcc.gov/eb/Orders/2007/FCC-07-139A1.html), [industry summaries](https://backuppower.ai/critical-buildings/telecom-backup-power/)); CA **72 h** mandate | **B/C+** — **4 h is low-end plausible**, not universal |
| Routine messaging rates | 0.008 / 0.08 | No household communication diary | **C−** |
| Precautionary grocery target | 2.5 d → 4 d | German civil defense **10 d** food ([BBK](https://www.bbk.bund.de/EN/Prepare-for-disasters/Personal-Preparedness/Stockpiling/stockpiling.html)); surveys **16–35%** reach 10 d ([Winkler 2023 PDF](https://www.dghev.de/fileadmin/user_upload/HUW_13_2023_Winkler_Notvorrat.pdf)); Sadus COVID stockpiling predictors ([PMC9326167](https://pmc.ncbi.nlm.nih.gov/articles/PMC9326167/)) already in repo | **C+** — **2.5–4 d is below official 10 d guidance**; behavioral study supports stockpiling heterogeneity, not these exact days |
| Observation/action latency | 0.02–0.35 h | No event-study | **C−** |
| Purchase timing jitter | Hours after open | No shopping diary | **C−** |

---

## Essential services & scenarios

| Parameter | Model | Scan | Tag |
|-----------|-------|------|-----|
| Water need **0.35 m³/HH/day** | Scalar | EPA **~82 gal/person/day** total home ([WaterSense](https://www.epa.gov/watersense/statistics-and-facts)); **~64.6 gpcd indoor** benchmark ([EPA Appendix B](https://www.epa.gov/sites/default/files/2017-03/documents/appendix-b-benchmarks-used-in-conservation-planning.pdf)); ×2.5 persons ≈ **0.61 m³/day** indoor | **⚠ C+** — **0.35 m³ may be low** unless outdoor excluded and HH size < 2.5 |
| Clinic capacity / visit hazard | 0.006N, 0.002+ | **~1.2–1.6 primary-care visits/person/year** ([MEPS/NAMCS summaries](https://pmc.ncbi.nlm.nih.gov/articles/PMC3495923/), [FastStats](https://www.cdc.gov/nchs/fastats/physician-visits.htm)) | **C+** — convert hazard to visits/year vs 0.006N scale |
| Moderate/severe shock Uniform ranges | Scenario generator | No historical joint distribution | **C−** (by design) |
| Retail/services shock multipliers | 0–0.3 | Domain isolation only | **C−** |

---

## Availability & relocation (C interpolation rows)

| Parameter | Scan | Tag |
|-----------|------|-----|
| Relocation threshold interpolation | Sue Wing **stated intent** already A elsewhere; interpolation between anchors | **C+** (hypothetical intent, not moves) |
| Retail power workaround 49% | Illinois SMB **stated** shutdown % — already noted in operational_availability doc | **C+** transfer |
| Return timing, outside-region boundary | No panel A source in scan | **C−** |

---

## Summary counts (qualitative)

| Outcome | ~Count of C rows scanned | Action |
|---------|--------------------------|--------|
| **Strong A-nat upgrade candidates** | 2–3 | Household size (partial), commute mean (national), possibly remote work after definitional fix |
| **C+ with useful bibliography** | ~20 | Add `bibliographic_source` + “national transfer, not fitted” without changing numbers |
| **⚠ numeric tension** | 4 | Employment 0.73, card escrow 1 h, spoilage delay 6 h vs 4 h, water 0.35 m³ |
| **C− / fictional / scenario** | remainder | Keep C; collateral, capacity formula, shock priors, messaging rates |

---

## Suggested next step (provenance plane, not world)

1. **Batch provenance pass:** For each **A-nat** and **C+** row, add optional fields `contextual_source` / `limitation` (or upgrade to A with transformation text) — **do not refit engine constants** in the same pass unless user asks.
2. **Resolve ⚠ rows** with a one-line policy each: accept as deliberate simplification, or nudge toward evidence (e.g. spoilage delay 4 h, water gpcd from EPA).
3. **Leave refuse rows** (finance run, markets) unchanged.

No changes to `blinded-simulation-development.md`. This scan is **`drafts/` only** until you want it merged into `docs/limitations.md` or `make_provenance.py`.
