# Operational availability extension (0.3.0-dev source evidence; 0.3.1-dev policy interface)

**Current implementation update:** The 0.3.0-dev version moved participants automatically from the world engine. In 0.3.1-dev, relocation and return are now explicit participant-policy actions; engine power ticks only provide private observation opportunities and enforce travel/feasibility. See `docs/participant_communication.md` for new results and interface. The historical 0.3.0-dev checks retained below are legacy, not this version.

**Scope:** no mortality, illness, physiological deprivation, building destruction, or automatic bankruptcy. “Unavailable” is always tied to a named, reversible *modeled purpose*: locally resident/able to participate on-site, building/site has normal grid service, retailer can continue operating under grid loss. Absence is not disappearance. The extension is on by default and can be ablated with `--no-availability`.

## Empirical observations and identification

Sue Wing et al. (2025), *Nature Communications* 16:3335, https://doi.org/10.1038/s41467-025-58537-4, report a ComEd service territory survey fielded in Illinois in 2022, with 829 residential and 200 SMB responses. In **hypothetical** outage scenarios, 33% of respondents reported that they would temporarily relocate under a one-day interruption and 83% under a 14-day interruption. The share saying they would close SMB operations in the one-day scenario was 49%, declining to 39% in the 14-day scenario (adaptation, not an increasing destruction probability). Residential backup generator access was 12%; SMB access 22%. These are measured **stated preferences**, not the observed outcomes of an actual outage. A simple unweighted binomial approximation gives 95% margins ±3.2 pp, ±2.6 pp, and ±6.9 pp for the first three proportions, respectively. These **are not** author-published uncertainty intervals and omit survey design effects and geographic/behavioral transfer uncertainty.

The actual 2003 US Northeast blackout provides a historical benchmark: Cavanagh (2005), The Conference Board report 05-01-SR, p.38, reports closure by 38% of surveyed firms in the Northeast Metro sample and 16% nationally. URL: https://www.neweraassociates.com/downloads/conference_board.pdf. Denominator mixes directly exposed and unexposed companies and sectors, so it **cannot** identify power-disconnected retailers' closure probability.

Observed Hurricane Matthew business recovery in Lumberton, NC is 45%, 71%, 85% and 91% reopened by 1, 2, 4 and 6 weeks, respectively (Watson, Xiao, & Helgeson, published online 2023, *Natural Hazards Review*, DOI 10.1061/NHREFO.NHENG-1807; https://www.nist.gov/publications/using-disaster-surveys-model-business-interruption). That paper finds outage duration, access and customer losses relevant to business interruption. Direct flooding and asset damage are mixed with service disruptions. Do **not** transfer its unconditional recovery curve to an outage-only scenario.

The Downtown Alliance (2013) records 20% of Lower Manhattan residential units initially inaccessible after Sandy; office square footage open was 80% at 3 weeks and 99% at 16 weeks: https://downtownny.com/press-releases/fact-sheet-lower-manhattan-update-one-year-after-hurricane-sandy/. This is a mixture of flood damage, accessibility, and utilities. No independent universal building-habitability cutoff is identifiable.

## Fitted operational rule — explicitly provisional

For **households actually disconnected at their own simulated home** for consecutive hours `h`, the extension uses a cumulative *propensity to seek temporary relocation*, with exact stated-response scenario anchors at 24h and 336h:

```
P(h)=0,                            h<=0
P(h)=0.33*h/24,                  0<h<=24
P(h)=1-0.67*exp(-lambda*(h-24)), 24<h<336
P(h)=0.83,                      h>=336
lambda = ln(0.67/0.17)/312 = approximately 0.004397 per hour
```

The within-day linear interpolation, mapping of **planned interruption duration** to **elapsed observed outage time**, and the cap beyond 14 days are *C-level assumptions*, not calibrated observations. Every household receives an individual fixed quantile/trigger from its independent RNG. The participant policy observes local power and its private preference threshold and may REQUEST relocation; the world then enforces a real local road trip (queued/retried if at capacity), then household `locally_present=False`. The participant remains in the simulation and can receive information through an assumed outside-region communication boundary. Local shopping, commutes and appointments are disabled while absent. Its *outside-region requirements* are logged separately without claiming external resources were delivered, paid for, or consumed; household stocks at home are conserved and left untouched. The default participant policy can REQUEST a return after six restored hours (C-level timing); the world enforces a trip and must obtain road capacity. No role status change entails death, serious illness or structural damage.

**Temporary company availability:** individual stores have two separate state variables: `store_site_usable` (connected to normal grid, not a physical building-habitability or structural assessment) and `store_operational` (normal grid connected or an abstract manual operating workaround). Exactly 49% of affected stores are *intended* to lose power-dependent operating ability in the large-sample Bernoulli limit, transferring the Illinois one-day all-sector SMB **stated** shutdown percentage to synthetic retailers (C-level extrapolation). This does not create backup electricity or consumable fuel. Full trade remains subject to existing staffing, inventory, opening hours, payment, and transport constraints. Retail operation returns with restored power; this version does **not** reproduce the source's 39% 14-day shutdown propensity because it does not physically model adaptation, rented generation, alternative worksites or their costs. No forced 14-day refit or fabricated permanent closure occurs.

**Building availability:** residential grid-service access and retail site grid-service are measurable; presence/occupation and company trading capability are separate. Permanent damage/condemnation is NOT inferred from lack of electricity or aggregate water supply. The geographic region has no cadastral building stock, inspection or repair record. A generic calibrated physical-building-unavailability threshold is **not identifiable from these sources**.

## Measured three-seed software checks, not independent validation

`python -m scripts.validate_availability` runs 2,400 households, 120 stores, seeds 41–43, full regional power interruptions of 24 or 336h. `calibration/availability_results.json` records per-seed outcomes. Under a *complete* blackout:

- Day-one locally absent fraction: mean **32.875%** (range 31.833–33.542%), versus fitted survey intention anchor 33%.
- Day-fourteen locally absent fraction: mean **82.986%** (range 81.917–83.625%), versus fitted intention anchor 83%.
- Day-one store power-operability loss: mean **45.833%** across 120-store samples, versus 49% source stated response; binomial sampling uncertainty is large for 120 stores and this does not test independent validity.
- Grid-dependent site access: 0/120 in full blackout, by definition of *normal grid service*, not building damage.
- All relocated participants return after externally scheduled power restoration in this stress test; money and goods invariants pass.

These targets are calibrated from the **same source**, not a historical held-out confirmation. The held-out historical outcomes above remain deliberately **not matched**, because their denominators and causal exposures are incompatible. A separate incident-level residential relocation/return panel, directly power-exposed company panel, and utility-only building function records would be needed to calibrate and validate those components.

## Known gaps and meaningful ranges

- The 0–24h response curve and 24–336h interpolation are assumptions; only survey scenario endpoints are anchored. Beyond 336h probability is held at 0.83, **not** a prediction for prolonged real blackouts. No calibrated substitute for shelter and family-host capacity, accommodation costs, outside food supply, population migration, information delays or return decision-making.
- **Resolved in 0.3.1-dev:** Relocation and return belong to the replaceable participant policy, not to a world-selected movement rule. `--no-availability` ablates the available movement functionality. Return timing and actual action frequencies still lack independent field validation.
- Local workforce attendance depends on local presence, but payroll is not yet a time-worked wage model. No permanent firm insolvency is inferred from zero balances. The established minimum clinic workforce and external supplier-production assumptions still limit interpretation of prolonged general collapse.
- The 49% one-day firm response is not a building threshold and does not remain calibrated at 14 days; sector and jurisdiction transfer are uncertain. Real physical backup energy and its supply are omitted.
- No observed population-level effect size establishes a deterministic person, building or business cutoff across shock types. Need contextual conditional probabilities with independent data and alternatives; do not treat hypothetical choices as certain actions.
