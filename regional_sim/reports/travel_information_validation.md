# RegionalSim 0.4.0-dev: commute and relocation information validation

**Status:** software validation and transferred survey-moment calibration, not independent historical validation. No medical outcomes were estimated or included in the fit.

## Evidence targets

- Fix I-5 Sacramento 2008 intermittent freeway closure (Ye, Mokhtarian, & Circella, 2012): 48% of survey respondents avoided rush hour; 44% changed routes. These choices can overlap; uncertainty intervals and denominators are not available in the accessible abstract. Applying the marginals to first-message-informed synthetic Columbus commuters is a declared C-level transfer.
- Sue Wing et al. (2025), Illinois hypothetical power outage survey: 33% stated relocation under one-day interruption, 83% under 14-day interruption. These fit intended preferences, not observed completed departure.
- Other studies motivate accuracy/timeliness of travel advisories and peers' potential role without identifying a numeric communication effect transferable to the current region.

## Implemented mechanism

Announcements are generated for introduced and restored targeted road restrictions; road-delay reports require a simulated failed departure. Delivery is delayed, filtered by access and attention and tracked by source. A participant chooses alternative route and/or postponed departure. Parallel paths consume actual zonal capacity. Pending commute, relocation and return travel can be revised while operationally cancellable. Direct contact's authentic intended relocation route may influence the route of a participant already choosing to leave; it cannot automatically initiate a move. General road-capacity loss blocks both paths when zero.

## Tests and calibration

- **44/44 tests passing**, including 12 in the new travel-information suite.
- Three seeds, 3,000 households, 3 days, one synthetic regional 36-hour main-corridor closure from hour 2; commute response isolated using `availability_extension=False`.
- Observed survey targets: **44%** route choice change and **48%** avoid rush hour. Sampled preference means: **43.733%** and **47.333%**, respectively.
- First message-informed unique commuter requests across seeds 47–49 total **2,565**: mean per-seed **45.396%** alternate route (range 44.713%–46.579%) and **48.848%** shifted departure (range 47.241%–51.044%). Fitted-check residuals are +1.396 and +0.848 percentage points. These are not out-of-sample events or effects of randomly assigned messaging.
- Completed commutes across three closure seeds: 1,429, 1,334, 1,414 with channels; 1,217, 1,210, 1,240 with all outside communication channels disabled. Firsthand failed-trip learning remains permitted in the ablation. This comparison is not a field causal estimate and consumes different event random sequences.
- A separate 10,000-household executable closure stress case (seed 47, 3 days) produced 2,851 first message-informed commuters: 1,278 alternate choices (44.827%) and 1,361 delayed departure choices (47.738%). Actual alternate-route trips: 2,754. Completed commutes: 4,726. Goods accounting discrepancy: ~2.18e-11 abstract units.
- The previous operational availability fitted-point script rerun after the new communications flow reports one-day absence **31.75%** against stated 33% (−1.25 percentage points), and 14-day absence **82.694%** against stated 83% (−0.306 percentage points). We did not retune parameters to erase the regression. These are not observed relocations.

## Gaps and interpretation

1. The Fix I-5 survey is not a randomized message-exposure intervention; cannot identify a causal communication effect. It is Sacramento during a planned 2008 closure, not Columbus at the synthetic 2024 reference point.
2. The route/departure joint probability, respondent count and CIs were unavailable in the abstracts consulted. Independent Bernoulli marginals have no evidential claim to joint realism.
3. Parallel corridor spare capacity (35%), alternate free-flow factor (1.35), shifted departure (2.5h), message access and retention windows, and latency are C-level assumptions. Actual network GIS, commute job flexibility and capacity observations are missing.
4. Only a qualitative social-intention route-coordination mechanism has been implemented; its frequency, benefits, external accommodation and counterfactual relocation probability remain **uncalibrated**. In a partial regional electricity-shock smoke test, few people relocated and received direct plans; no meaningful peer coordination magnitude was established.
5. A full road closure in this model is **main corridor only**; a general road shock multiplier of 0 means both main and alternate are unavailable. This is a synthetic tractable network, not engineering closure routing.
6. Road capacity rejections count repeated deferred attempts, not unique affected people. Existing medical variables are irrelevant to, and excluded from, this calibration. No medical outcomes or thresholds were introduced.

**Reproduce:** `python -m scripts.calibrate_travel_information && python -m scripts.validate_availability && python -m unittest discover -s tests -v`. Data in `calibration/travel_information_results.json`, `calibration/availability_results.json`, `benchmarks/travel_information_observations.json`; 10k event trace and summary in `reports/road_closure_10000_3d/`.
