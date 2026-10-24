# Commute and relocation information — RegionalSim 0.4.0-dev

## Scope and interpretation

This is an **event-driven, purpose-specific informational response model**. No medical or mortality outcomes are calibrated or asserted. The background simulator retains its other resource-accounting domains, but the experiments below fit only travel decisions. No alternative participant policy is hardcoded into world physics.

A new external `road_closure` shock restricts the synthetic **primary zonal corridor**; a parallel alternate corridor retains capacity unless a concurrent general `road` shock restricts it. `road_closure` is opt-in and excluded from routine randomly drawn shocks. Real transport reservations consume separate per-hour capacity. Official restrictions are generated when shock state changes, not freely invented. `road_reopened` follows restoration. A blocked or over-capacity attempted trip can generate a firsthand `road_delay` report, but it cannot substantiate a claim of a physical closure. Announcements are zone-local, channel/attention-gated, delayed, and can be missed.

Observations contain only delivered advisories or a participant's own failed departure, never raw `factor_for('road', zone)` or neighbors' private state. Participants also receive direct close/workplace contacts' genuine relocation intention, with intended route and six-hour expiry; forwarded claims do not masquerade as a direct contact. Uninformed commuters can take their conventional route. Informed commuters choose on their own whether to request an alternate or delayed trip. A deferred main-route commute, relocation, or return may be *cancelled by the participant* and replaced before travel execution. The engine validates stages and capacity; no automatic policy-free rerouting occurs. Relocation choice remains driven by the separate stated blackout-response anchors (33%/83%). Peer planning can change a selected route, **never the probability of deciding to relocate**. The outside-region destination remains unresolved.

## Published behavioral anchors (no invented confidence intervals)

- Ye, L., Mokhtarian, P. L., & Circella, G. (2012). *Commuter impacts and behavior changes during a temporary freeway closure: The Fix I-5 project in Sacramento, California*. Transportation Planning and Technology, 35(3), 341–371. DOI: [10.1080/03081060.2012.673270](https://doi.org/10.1080/03081060.2012.673270). Observed **48% avoided rush hour**, **44% changed route**, and roughly **5–6% increased transit/telecommuting** during the intermittent 2008 closure. These adaptations are not exclusive. The accessible abstract does not provide a denominator or CI for the two focal estimates. We apply the marginals to a synthetic informed commuter cohort, not as a causally identified messaging effect or a universal population statistic.
- Khattak, A. J., Schofer, J. L., & Koppelman, F. S. (1995). *Effect of traffic information on commuters' propensity to change route and departure time*. Journal of Advanced Transportation, 29(2), 193–212. DOI: [10.1002/atr.5670290205](https://doi.org/10.1002/atr.5670290205). Chicago AM commuters reported greater changes when reports were accurate/timely/relevant; the **coefficients were not transferred**.
- Milch, K., Broad, K., Orlove, B., & Meyer, R. (2018). *Decision science perspectives on hurricane vulnerability*. Atmosphere, 9(1), 32. DOI: [10.3390/atmos9010032](https://doi.org/10.3390/atmos9010032). In their Sandy survey, 23% of people *planning to evacuate* cited family/friend advice as their principal reason; this is only qualitative support that interpersonal information can matter. Hurricane-evacuation choice must **not** be used as a blackout peer-coordination coefficient.
- Sue Wing et al. (2025), DOI: [10.1038/s41467-025-58537-4](https://doi.org/10.1038/s41467-025-58537-4), underpins prior temporary relocation intentions: 33% at a hypothetical 1-day power interruption and 83% at 14 days. It does not report observed relocations, road-route coordination, or social causal effects.

## Model-specific assumptions, category C

1. Each commuter receives fixed binary propensities `P(route_change)=0.44` and `P(avoid_peak)=0.48`, sampled independently. Applying those marginal percentages **conditional on delivered awareness** changes the original survey denominator and is explicitly extrapolative. Correlation between route/time changes is not fitted.
2. A time-shifter delays the intended trip 2.5 hours, not an empirically measured mean shift. No employer consent/tardiness cost is represented.
3. Alternate corridor capacity is 35% of main baseline, alternate free-flow trip time is 1.35 times main, and no local GIS graph or origin-destination reassignment is available. The BPR capacity-response equation is retained. Normal `road` shocks affect both corridors; `road_closure` affects main only.
4. News / online/close/workplace delivery availability and delays, personal failed-trip review timing, 24-hour advisory expiration, and a six-hour expiry for direct relocation plans are assumptions. Repeated and forwarded exposure preserve original provenance; direct plans require `sender == origin`.
5. A recent direct peer's alternate relocation plan may influence route **only if the participant already intended to relocate**. Its incidence and practical coordination gain have **not** been fitted. No social coefficient changes the decision to leave or return.
6. Restoration notices may fail to arrive. A stale belief can persist temporarily. Information is not equal to adoption; a notice neither reserves transport nor guarantees travel.

## Reproducible transferred calibration and controls

`python -m scripts.calibrate_travel_information` runs three independently seeded, 3,000-household, three-day tests (seeds 47–49) with one synthetic regional main-road closure at hour 2 lasting 36 hours, a control with official/peer channels disabled but firsthand experience still available, and routine operation. Availability relocation is disabled for commute isolation. Medical outcomes are outside scope.

The reported first-informed denominator counts **unique participants' first message-informed commute request**, not multiple days, repeated requests, failed attempts or completed trips. The direct assigned-propensity sample means are 47.33% shift and 43.73% route. Conditional first-informed requests average 48.85% shift (three-seed range 47.24–51.04%) and 45.40% route (range 44.71–46.58%). The source values are 48% and 44%. These are in-sample transferred survey-moment checks, not independent validation of the awareness effect. Selection, transportation constraints and model stochasticity produce small departures from the input marginal shares.

Three-seed mean completed commutes with notices is 1,392, compared with 1,222 when outside communications are disabled under the *same external main-road closure*. However, the no-communications case still permits firsthand adaptation and the cases consume random sequences differently; this is an internal ablation, not an observed causal effect. Road-capacity rejection counts include repeated retry attempts and must not be interpreted as unique stranded people. Alternate travel and vehicle capacity are genuine engine state, not descriptive labels.

A 10,000-household, three-day regional closure run (seed 47) recorded 2,851 first message-informed commuter choices, 1,278 route changes (44.83%), 1,361 shifts (47.74%), 2,754 alternate-route trips and 4,726 completed commutes. Goods-accounting error was 2.2e-11 abstract units. It is a software stress test, not a validation against Sacramento or Columbus observed traffic counts.

`tests/test_travel_communications.py` checks no omniscient notices, authentic firsthand claims, source-local delivery, true separate road capacities, common-region capacity loss, actual policy revisions, no forced relocation, peer route choice without induced relocation and refusal to treat a forwarded plan as direct. The full regression suite has 44 tests.

## Outstanding empirical gaps

- **No identified communication treatment effect** for commuting or relocation. Survey respondents' action rates cannot be interpreted as the counterfactual difference between receiving/not receiving information. Need observed traveler panel or randomized information intervention with verified delivery.
- **No conditional calibration** on commute flexibility, income, job, car access, network ties, origin/destination, region or outage expectations.
- **No joint route/time-response distribution** or confidence intervals available from the accessible Fix I-5 abstract; direct independently sampled Bernoulli preferences are only provisional.
- **No observed peer relocation coordination effect** transferable from storm evacuation to utility-induced absence. Social plans are genuine in-model messages, but the behavioral route-following rule is C-level.
- Alternate corridor topology, capacity, diversion time and intersections are synthetic, as are response latency, message arrival and news subscription. A general `road` shock with multiplier zero correctly blocks both routes.
- No realistic employer-approved late arrival, telework/substitute modes or route-specific exposure for nonresidential suppliers and other employment sites.
- A two-link zone is inappropriate for place-specific transport predictions. The model should remain outside policy evaluation until route flows and first-informed responses are measured against independent real incidents.

See `benchmarks/travel_information_observations.json`, `calibration/travel_information_results.json`, `configs/road_closure_information.json`, and `provenance.json` for machine-readable evidence, scenario and outputs.

## Rechecked earlier relocation fitted points after 0.4 changes

`python -m scripts.validate_availability` now gives mean last-affected-day temporary absence of **31.75%** at 24h versus 33% target (−1.25 percentage points) and **82.694%** at 336h versus 83% target (−0.306 percentage points), each over seeds 41–43. In both checks all participants return after the externally scheduled restoration and event horizon. The previous 0.3.1 figures must not be reused. The difference is an in-sample regression from changed message scheduling and RNG consumption; the parameters were **not** retuned. Neither target represents observed historical relocation.
