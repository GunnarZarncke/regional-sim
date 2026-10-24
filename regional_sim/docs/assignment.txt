# Assignment: Empirically Grounded Multidomain Regional Simulation

## Objective

Build an open-source, stochastic, agent-based simulation of an ordinary regional socioeconomic system.

The simulation must reproduce credible interactions between households, businesses, financial infrastructure, energy, logistics, mobility, communications, and essential services under normal operating conditions and externally introduced disruptions.

It must support independent studies of resilience, resource allocation, individual behavioral responses, communication, and recovery.

The eventual use of the simulator includes comparative experiments with alternative decision-making policies. These policies are outside your assignment. Implement a replaceable decision-policy interface without making assumptions about what future policies will attempt to optimize or how they will behave.

**Do not construct a particular disaster narrative or engineer the environment toward any desired outcome.** Build the most credible tractable model possible using independently sourced empirical constraints.

## 1. Geographic and temporal scope

Choose one geographically coherent metropolitan region for which sufficiently good public data exist. Prefer a US region if data quality is comparable.

Use a fixed geographic boundary and a consistent reference period.

Model:

- A representative population of households, initially at least 10,000 individually simulated decision-making units.
- Heterogeneous household composition, income, assets, consumption, mobility, employment, needs, and available resources.
- Businesses, service providers, infrastructure operators, and public institutions.
- Both routine operations and disturbances over a period sufficient to observe recovery or lasting effects.

Support scaling to approximately one million households, using efficient representations where appropriate.

Implement a discrete-event simulation with appropriate domain-specific temporal resolution. Do not artificially synchronize decisions to one global interval.

## 2. Domains

Include the following interconnected domains. Each must be independently meaningful, and each must have functioning ordinary operating rules.

### A. Finance and payments

Represent household and business accounts, liquid assets, recurring obligations, payments, transaction processing, settlement delays, and relevant financial institutions.

Money and assets must be conserved or transformed through explicit, accounted-for transactions.

Include ordinary institutional liquidity-management procedures and legally applicable transaction constraints.

### B. Retail and physical supply chains

Represent essential goods, household inventories, retailers, warehouses, suppliers, replenishment orders, delivery lead times, production or procurement constraints, and stockouts.

Goods must have physical quantities, locations, ownership, and availability.

### C. Electricity

Represent residential and business consumption, production or external supply, network capacity, flexible loads, interruptions, restoration, and applicable protective procedures.

Use a validated physical or engineering model appropriate to the chosen level of abstraction.

### D. Mobility and logistics

Represent travel demand, road capacity, transport availability, travel times, goods delivery, and congestion.

The movement of people and goods must consume actual simulated transport capacity.

### E. Communications

Represent interpersonal communication, public information, institutional announcements, information delays, and differential access to communication channels.

Communication must be a functioning subsystem through which information and observed behavior can propagate.

### F. Essential services

Represent a limited set of essential service providers and the resources they require to operate.

Their capacity and continuity must depend on relevant inputs from the preceding domains.

Use documented service-continuity rules where available. Do not infer deaths or serious medical outcomes directly from arbitrary resource thresholds.

## 3. Cross-domain integration

Create explicit, physically or institutionally justified dependencies between domains.

Examples of ordinary dependencies include:

- Payments are required for many commercial transactions.
- Retail inventory replenishment requires suppliers and transport.
- Electricity supports refrigeration, commerce, communications, and some payment infrastructure.
- Businesses require employees, working capital, utilities, and deliveries.
- Household activities create financial transactions, physical consumption, energy use, and travel demand.

Every dependency must have a documented mechanism.

Do not introduce a coupling merely because it creates interesting behavior.

Conserve money, goods, energy, and other applicable quantities according to the chosen models. Distinguish resource transfers from consumption, destruction, inaccessibility, and temporary immobilization.

## 4. Institutional responses and safeguards

Implement authentic operating procedures from relevant standards, regulations, operator documentation, and published studies.

Examples include:

- Financial liquidity and payment-settlement procedures.
- Electricity distribution protections and restoration procedures.
- Inventory replenishment, backorder management, and retailer allocation.
- Traffic congestion and incident management.
- Essential-service continuity and capacity allocation.

Protective systems must operate automatically or through realistic decision delays as appropriate.

Do not disable established safeguards for experimental convenience.

Document their applicability, actual thresholds, response timing, operating assumptions, and uncertainties. Avoid transferring jurisdiction-specific requirements to an incompatible simulated region.

Where a credible protocol cannot be implemented, explicitly identify the approximation and its consequences for the validity of the simulator.

## 5. Scripted human participants

Human participants must have heterogeneous, independently parameterized behavioral policies.

Use published empirical studies, observational datasets, and established behavioral models rather than inventing crisis responses.

Represent at least:

- Routine activity and habitual behavior.
- Response to changing prices and availability.
- Precautionary behavior under uncertainty.
- Information acquisition and communication.
- Changes in activity following observed shortages or service interruptions.
- Delays between observation, decision, attempted action, and execution.
- Differences in resources, constraints, preferences, trust, and exposure.

Where possible, reproduce published response distributions, not only average effects.

For each behavioral model, document the population from which it was estimated, observed magnitude, confidence interval or uncertainty range, and limits of transferring it to the simulated population.

No participant should possess information unavailable to an equivalent real-world participant.

## 6. Communication and behavioral diffusion

Communication is a core requirement, not a decorative feature.

Implement a heterogeneous, multiplex communication network with:

1. Household and close interpersonal ties.
2. Workplace and professional ties.
3. Local community communication.
4. Public online communication.
5. News and official institutional announcements.

Participants must be able to communicate observations, concerns, intended responses, and completed actions.

Messages should carry:

- Origin and timestamp.
- Content or structured claim.
- Evidence type: firsthand observation, reported experience, institutional announcement, opinion, or inference.
- Audience or dissemination channel.
- Delivery delay.
- Source visibility and credibility information.

A participant may forward information, express agreement or disagreement, ask questions, or communicate a personal decision according to its behavioral policy.

Implement empirically grounded variation in communication frequency, trust, attention, and adoption thresholds.

Distinguish exposure to information from behavioral adoption.

Support both single-source diffusion and complex contagion requiring reinforcement from multiple sources.

Messages must be causally grounded in the simulated state, a participant's legitimate observations, or an explicitly modelled information-generation process. Do not introduce false rumors or universal broadcasts simply to force collective behavior.

Use published social-network experiments to constrain the diffusion mechanisms. Do not treat effect sizes observed in one behavioral domain as universal parameters.

Provide observables for reach, propagation speed, network clustering, repeated exposure, source concentration, and behavioral correlation.

## 7. Baseline scenarios

Develop scenarios independently of any future comparative-policy experiment.

Include:

- Routine operation with ordinary stochastic variation.
- Seasonal or demand-related fluctuations.
- Moderate disturbances drawn from documented operational or historical distributions.
- A smaller set of severe but independently justified disturbances.
- Recovery after disruption.

Choose initial disturbances through a documented, prespecified procedure. Do not construct event sequences manually to provoke a desired response.

Retain the ability to introduce generic external shocks to any domain without modifying the simulation architecture.

Normal operating scenarios must be credible before attempting severe scenarios.

## 8. Empirical grounding and calibration

For each domain, create a source register containing:

| Field | Requirement |
|---|---|
| Parameter | Name, definition and units |
| Source | Full bibliographic reference and URL |
| Evidence | Observational, experimental, regulatory or assumed |
| Estimate | Point estimate, distribution and uncertainty |
| Applicability | Population, geographic and temporal scope |
| Transformation | Any adaptation from the original evidence |
| Validation | Observable or published benchmark used to test it |

Use three evidence categories:

- A: Directly observed or experimentally estimated.
- B: Established institutional or engineering protocol.
- C: Modelling assumption or extrapolation.

Do not present C-level assumptions as empirical findings.

For every domain, demonstrate that the simulator reproduces known ordinary operating behavior and at least one independently documented response to disturbance, with effect magnitudes and uncertainty explicitly reported.

Where adequate evidence is unavailable, retain the uncertainty or simplify the domain rather than inventing precision.

## 9. Interchangeable participant decision interface

Separate the world simulation from participant decision policies.

Each participant policy must receive only that participant's available observations and return a structured set of intended actions.

The interface must support:

- Reading observations and communications.
- Requesting permitted information.
- Sending messages.
- Executing available financial, commercial, household, mobility, and other ordinary actions.
- Scheduling future actions.
- Revising or cancelling requests when legally and operationally feasible.
- Choosing not to act.

The available action mechanisms must be derived from the ordinary world model, not from a future experimental policy.

Permit legal combinations of actions across domains. Do not require an agent to select one permanent domain or a predefined crisis-response strategy.

The world engine must enforce all feasibility constraints, permissions, processing delays, capacities, and execution outcomes.

Record requested actions separately from accepted, executed, and completed actions.

Decision latency, observation frequency, communication frequency, and computational cost should be policy-interface parameters.

## 10. Validation and negative controls

Before release, demonstrate:

- Conservation of financial and physical quantities.
- Plausible normal household and business activity.
- Plausible normal capacity utilization.
- Institutional protocols activating under their documented conditions.
- Credible recovery and non-recovery where warranted by the underlying model.
- Functioning communication and behavioral diffusion.
- Appropriate variation across independent random seeds.
- Absence of unintended information leakage between participants.

Run domain-isolation and coupling-ablation checks to verify that cross-domain effects follow implemented dependencies rather than simulation artifacts.

Test responses against independent empirical benchmarks not used for parameter fitting.

Report failed validation tests rather than modifying the simulator solely to make them pass.

## 11. Required deliverables

Produce:

1. Executable simulation and reproducible environment.
2. Technical description of all domain models.
3. Source and parameter provenance register.
4. Scripted human behavioral models.
5. Communication-network implementation and validation.
6. Interchangeable participant decision-policy API.
7. Scenario and external-disturbance generator.
8. Normal-operation and disruption-validation report.
9. Machine-readable traces of observations, messages, decisions, transactions, institutional responses, and resulting world states.
10. Known limitations and unvalidated extrapolations.
11. Automated regression tests and deterministic random-seed handling.
12. A documented configuration for both a smaller development population and the intended larger population.

All important observable outcomes should be logged, including beneficial ones. Do not select a particular failure mode as the primary purpose of the simulator.

## 12. Release procedure

Once the simulation satisfies the documented validation criteria:

- Freeze the code, input datasets, reference configurations, parameter distributions, decision interface, and scenario generator.
- Record immutable version identifiers and cryptographic hashes.
- Set aside held-out scenarios and validation data.
- Produce an executable release that does not require further modification to support alternative participant policies.
- Report outstanding problems and limitations.

The released simulator must remain a useful standalone multidomain simulation, independent of any later experiment performed with it.

Do not optimize the world model for outcomes generated by future replacement policies.
