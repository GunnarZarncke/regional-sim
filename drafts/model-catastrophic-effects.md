# Catastrophic failure capability of RegionalSim 0.2.0-dev

The current simulator can represent the development of resource shortages and certain cascading service failures, but it cannot yet represent a full socioeconomic catastrophe.

It can simulate a household running out of groceries and medication, prolonged interruption of electricity and water services, blocked deliveries, financial depletion, and inventory destruction through refrigeration failure.

However, it does not currently model individuals becoming ill or dying, buildings becoming uninhabitable, businesses entering bankruptcy, or physical infrastructure progressively deteriorating because other systems have failed.

This creates an important distinction:

\\[ \boxed{\text{Numerical execution}\neq\text{physical validity}} \\]

The simulator can continue executing far beyond the point at which its representation of the real-world system remains credible.

## 1. Which catastrophic outcomes can emerge?

I checked the actual state transitions in `engine.py`, rather than just the architecture documentation.

| Potential systemic consequence                         | Current implementation                         |
| ------------------------------------------------------ | ---------------------------------------------- |
| Progressive household food shortages                   | Yes; unmet consumption accumulates             |
| Exhaustion of household medication                     | Yes; unmet consumption accumulates             |
| Persistent inability to purchase resources             | Yes; subject to payment and retail constraints |
| Electricity-dependent commercial closures              | Yes                                            |
| Physical destruction of refrigerated inventory         | Yes                                            |
| Water-service interruption                             | Yes; aggregate unmet volume                    |
| Deteriorating individual health                        | Not implemented                                |
| Death from prolonged resource deprivation              | Not implemented                                |
| Destruction of buildings or equipment                  | Not implemented                                |
| Firm insolvency and permanent closure                  | Not implemented                                |
| Infrastructure degradation caused by prolonged outages | Not implemented                                |
| Endogenous infrastructure repair and reconstruction    | Not implemented                                |
| Permanent economic or population restructuring         | Not implemented                                |

The most important missing feature is accumulated damage to people and capital.

Consider a dependency chain such as:

Electricity interruption

Water-service capacity decreases

Implemented

Water demand remains unmet

Implemented

Individual deprivation accumulates

Missing

Health deterioration, possible mortality and reduced workforce availability

Missing

Further deterioration of essential services\
Not currently generated through this mechanism.

This last feedback loop is precisely the kind of mechanism needed to model an endogenous systemic catastrophe.

The original assignment explicitly prohibits deriving deaths or serious medical outcomes directly from arbitrary resource thresholds. Accordingly, simply adding a rule such as three days without water causes death would not be an acceptable scientific solution.

## 2. I tested an extreme scenario

To illustrate the model's present limits, I ran an additional stress test using the packaged implementation.

The experiment used 1,000 households over eight days, comparing routine operation against a seven-day regional electricity interruption.

For the disrupted run:

\\[ m\_{\mathrm{electricity}}(t)= \begin{cases} 0 & 0\leq t<168\text{ hours}\\\ 1 & t\geq168\text{ hours} \end{cases} \\]

This is an intentionally extreme computational test, not a calibrated historical scenario.

### Results

| Outcome over eight days                       | Routine | Seven-day blackout |
| --------------------------------------------- | ------- | ------------------ |
| Unserved household-electricity hours          | 0       | 168,000            |
| Unmet grocery consumption (abstract units)    | 80.79   | 4,850.34           |
| Unmet medication consumption (abstract units) | 0       | 40.02              |
| Unmet water demand                            | 0       | 2,450 m³           |
| Completed clinic appointments                 | 35      | 6                  |
| Destroyed refrigerated grocery inventory      | 0       | 463.26 units       |

The financial and physical conservation checks still passed.

But the striking result is what did not happen.

Despite seven days of zero modeled water-service delivery, all 1,000 households continued to exist as active units. They remained eligible for ordinary scheduled activities. The simulator has no variable describing physiological deprivation, health deterioration, death or resulting removal from the workforce.

That is not a prediction of zero fatalities. It is an absent outcome mechanism.

Likewise, suppliers continued creating goods through the externally specified production process even during the prolonged regional blackout. Local infrastructure conditions do not currently constrain that external production boundary.

This confirms that the engine is numerically robust under at least this extreme input, but also demonstrates why its output cannot be interpreted as a complete account of catastrophic consequences.

## 3. At what point do the value ranges stop being meaningful?

There are three different boundaries: accepted software inputs, meaningful internal model behavior, and empirically defensible predictions.

### A. Software input limits

The shock interface accepts:

| Parameter                   | Permitted range                            |
| --------------------------- | ------------------------------------------ |
| Individual shock multiplier | 0–3                                        |
| Shock duration              | Any positive number of hours               |
| Geographic scope            | One synthetic zone or the entire region    |
| Concurrent disturbances     | Multiple overlapping events                |
| Standard severe scenario    | Multiplier 0.25–0.60, duration 24–96 hours |

These are software limits, not calibrated limits of physical plausibility.

Moreover, overlapping multipliers are multiplied together. Three concurrent 0.3 multipliers acting on the same capacity would produce:

\\[ m\_{\mathrm{effective}}=0.3^3=0.027 \\]

Likewise, repeated demand amplifications can exceed the individual multiplier limit. Some output quantities saturate at 100%, while others do not.

There is no global plausibility constraint applied to these combinations.

### B. Internal thresholds where behavior changes

Several implemented thresholds are especially relevant under extreme conditions.

| Condition                                         | Implemented behavior                                   | Validity limitation                                |
| ------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------- |
| Communications backup exhausted                   | Communications can become unavailable                  | Four-hour backup is assumed                        |
| Communications multiplier below 0.5               | Channel becomes unavailable                            | Binary approximation; no gradual degradation       |
| Retail refrigeration unpowered for over six hours | Spoilage starts at 0.06% of remaining stock per hour   | Uncalibrated rate; no temperature dynamics         |
| Road capacity multiplier exactly zero             | Corridor has no capacity                               | Valid computationally                              |
| Road multiplier very small but positive           | Corridor retains at least six vehicle-equivalents/hour | Artificial capacity floor                          |
| Water capacity falls below demand                 | Unmet water demand accumulates                         | No household water stocks or health effects        |
| Clinic attendance falls to zero                   | Workforce factor retains a 0.5 minimum                 | Unrealistic during a true staffing collapse        |
| Household inventory reaches zero                  | Unmet consumption accumulates                          | No cumulative individual deprivation state         |
| Household money reaches zero                      | Purchases requiring unavailable funds cannot proceed   | No full debt, insolvency or welfare-response model |

These are not all empirically established tipping points.

For example, the road-capacity floor means that tiny positive road multipliers eventually become indistinguishable: capacity stops decreasing until the multiplier reaches exactly zero.

The water model has nominal capacity equal to 125% of demand. With electricity fully available, its service multiplier can therefore fall to 0.8 before modeled unmet demand begins.

That 0.8 threshold arises from the chosen spare-capacity assumption, not from a measured regional infrastructure limit.

### C. Where scientific validity ends

This is the more consequential issue.

Ordinary operation

Partially grounded

Some externally sourced consumption and income anchors exist, but independent normal-operation validation is incomplete.

Documented moderate electricity disruption

Two Columbus outage-count proxies have been fitted to published observations. These reproduce selected observations, not the underlying physical incident.

Severe or prolonged multidomain disruption

The numerical mechanisms remain executable, but input distributions and downstream effect magnitudes are unvalidated.

Catastrophic human and infrastructure consequences

Not represented by the current state space. These cannot be estimated merely by increasing shock severity.

There is therefore no defensible universal statement such as predictions remain meaningful down to 20% electricity availability.

In fact, meaningful ranges are output-specific.

The aggregate electricity accounting remains interpretable under a zero-supply experiment, even though the corresponding household disconnection pattern is only a proxy.

Grocery inventory can also remain correctly conserved while simulated human survival becomes meaningless.

In mathematical terms, the present model may retain accounting validity for \\(t>T\\), even while losing predictive validity for its behavioral and socioeconomic outcomes.

## 4. The larger structural problem: missing endogenous destruction

The current model primarily represents changes to flows:

\\[ \text{Resource production} \rightarrow \text{Transport} \rightarrow \text{Availability} \rightarrow \text{Consumption} \\]

To represent catastrophic systemic failures, it must additionally model accumulated changes to underlying stocks of functional capacity.

For example, a generic capital-stock model might be expressed as:

\\[ \frac{dK_j}{dt} = I_j(t)-D_j(t)-\delta_jK_j(t) \\]

where \\(K_j\\) is operational capital, \\(I_j\\) is investment or restoration, \\(D_j\\) is endogenous destruction, and \\(\delta_j\\) is ordinary depreciation.

An infrastructure system would then have capacity determined by the surviving and functioning capital stock, rather than only by an externally imposed multiplier.

The essential distinction is:

\\[ \text{Shock ends}\\;\not\Rightarrow\\;\text{System recovers} \\]

The present simulator achieves this distinction partially for depleted inventory, delayed deliveries and exhausted financial resources, but not for damaged infrastructure or individual human health.

### What should be added?

I would extend the existing world model rather than construct a separate catastrophic-disaster simulator.

| Extension               | Required new state                                                  | What it enables                                           |
| ----------------------- | ------------------------------------------------------------------- | --------------------------------------------------------- |
| Individual deprivation  | Accumulated unmet needs, exposure duration, access to substitutes   | Persistent consequences of shortages                      |
| Health progression      | Individual health states, care requirements and outcome transitions | Evidence-based morbidity and mortality, where data permit |
| Physical capital        | Functional, degraded, damaged and destroyed assets                  | Endogenous property destruction                           |
| Repair and recovery     | Personnel, spare parts, finance and actual restoration tasks        | Recovery dependent on other subsystems                    |
| Business continuity     | Operating costs, liabilities, solvency, staffing and closure states | Endogenous economic failure                               |
| Production dependencies | Energy, water, transport, labor and intermediate goods              | Propagation of failures into productive capacity          |
| Adaptation              | Substitution, relocation, evacuation, support and changing needs    | More credible prolonged-disruption behavior               |

These changes would make a substantial difference.

For example, an electricity shortage might prevent a water provider from operating, which could subsequently affect the provider's labor availability, maintenance activity or operating condition. The resulting reduction in capacity could persist even after electricity returns.

Such an outcome would be caused by the evolution of the simulated system, not imposed as another external shock.

## 5. How should catastrophic ranges be calibrated?

The correct procedure would be to calibrate normal service operation first, then individual subsystem disruption and recovery, and finally compound effects using independent observations.

In particular, observed catastrophic outcomes should not be used to invent arbitrary failure thresholds.

A health-outcome module, for example, would need exposure-specific evidence, relevant population heterogeneity, competing risks and confidence intervals. Where adequate evidence does not exist, it should report unmet needs and unresolved health risk rather than fabricate fatalities.

Likewise, physical property destruction requires documented mechanisms. An inventory-spoilage model cannot simply be extended into a building-destruction model by increasing its loss coefficient.

The model should also explicitly report when an experiment leaves the calibrated domain. Such a validity report could distinguish:

- Interpolated: operating conditions and outputs supported by calibration observations.
- Extrapolated: the modeled mechanism applies, but its effect magnitude has not been validated.
- Structurally unsupported: necessary state variables or mechanisms are absent.

This would avoid presenting numerical precision as predictive certainty.

## Conclusion

The present architecture has a useful foundation for catastrophic-failure modeling, particularly its explicit dependencies, conservation constraints, event scheduler and replaceable participant policies.

But there is a major gap between representing resource scarcity and representing its eventual consequences.

RegionalSim currently models a socioeconomic system that can become severely resource-constrained, but whose underlying population and much of its infrastructure remain artificially persistent.

There is no single shock-magnitude threshold at which this becomes a problem. The predictive boundary is reached whenever missing mechanisms—such as cumulative deprivation, asset deterioration, institutional collapse or endogenous recovery—become important to the outcome being studied.

For studies of truly systemic catastrophic failure, I would treat adding persistent health, capital and recovery states as a prerequisite, not as an optional enhancement.