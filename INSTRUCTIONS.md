# Instructions

Mission and experimental discipline for **regional-sim**. Agent habits and
layout: `AGENTS.md`. Front door: `README.md`.

This is **one** simulation tool, not a family of experiment lines and not a
book. Shared habits below are a cut-down of TSA `docs/METHODOLOGY.md`.

## Mission

Build and freeze an empirically constrained, stochastic, agent-based
simulation of an ordinary regional system (households, firms, payments,
supply, power, mobility, communications, essential services).

Then, in a **separate** experiment, replace a fraction of scripted human
decision policies with general-purpose personal AI agents and measure
system-level outcomes.

**Hypothesis (experiment only):** individually useful adaptive AI policies
can produce collective consequences not visible in isolated evaluations,
via resource constraints, communication, and cross-domain coupling.

**Null:** AI adoption does not add systemic harm, or improves resilience,
relative to human and non-AI automation baselines.

The world must remain a useful standalone simulator if the hypothesis
fails.

## Claim strength

A strong positive result needs all three: individually defensible agent
behavior, reproducible adverse system outcomes, and evidence that
**interaction** among decisions caused those outcomes.

The hypothesis is weakened if harm vanishes after bug/permission fixes,
equals generic faster humans, does not need cross-domain action, or rides
on weakly calibrated C-level assumptions.

Do not describe a tested LLM as perfectly aligned. Do not infer
catastrophe from a price spike, high utilization, or a safeguard firing.
Do not infer deaths from arbitrary resource thresholds.

## World vs experiment

### Blinded assignment (`blinded-simulation-development.md`)

Frozen text of the world-build brief. **RegionalSim 0.1.0** was produced
against this assignment only; an identical copy ships inside the prototype as
[`regional_sim/docs/assignment.txt`](regional_sim/docs/assignment.txt). Do not
retro-edit the assignment to match later validation goals.

### World freeze bar (before the AI experiment)

These requirements **extend** the blinded assignment for accepting a **frozen
world release** and starting participant replacement. They were not part of the
v0.1 build brief.

- Ordinary operating rules first; severe shocks only from a prespecified
  generator, not a crafted narrative.
- Couplings only with a documented mechanism.
- Conserve money, goods, energy, and other tracked quantities, or account
  for loss explicitly.
- Keep real safeguards; document approximations.
- Human policies from published behavior, not invented crisis scripts.
- Interchangeable policy API: observe → intended actions; the engine
  enforces feasibility.
- Source register with evidence grades A / B / C. Do not sell C as data.
- **Magnitudes, not vibes:** human baseline must match published effect sizes
  and subgroup differences where evidence exists (e.g. insured vs uninsured
  depositors in 2023 bank-run studies). Do not use one pooled withdrawal
  propensity for everyone.
- **B ≠ A:** Basel-style liquidity horizons and other regulatory stress inputs
  are institutional requirements, not observed minute-by-minute behavior; label
  and validate separately.
- **Coupling first:** demonstrate transport→delivery, payments→transactions,
  and other ordinary links on the **scripted human baseline** before any AI
  condition; do not treat the AI experiment as the first coupling test.
- **No catastrophe requirement:** world release = fidelity, conservation,
  protocols, reproducibility, policy API. Baselines that contain shocks are
  fine.

### Experiment (`multi-domain-counterexample-protocol.md`)

- Freeze the world (code, data, configs, interface, scenario generator)
  before scoring AI conditions.
- Preregister adoption levels, models, instructions, outcomes, analysis,
  and stopping rules.
- Matched seeds and initial states across human / mixed / AI runs.
- Primary instructions must not mention the hypothesis.
- No live-world transactions or infrastructure commands.

If a change after seeing results is required, mark it exploratory and
rerun; do not silently edit old numbers.

## Freeze, blinds, negatives

1. **Freeze before you score.** Thresholds, batteries, and detectors get a
   new version string when they genuinely change.
2. **Blind the measurement, not the phenomenon.** World-builders and
   in-sim agents may know how their own system works. They must not see
   the experimental rubric, scoring function, or desired failure mode.
3. **Coarsened feedback is still a leak.** Do not hint which threshold
   failed between blinded rounds.
4. **World fact vs threshold.** Missing domain facts a cold reviewer would
   catch are OK to disclose. Which side of a score you are on is not.
5. **Refuse and null are first-class.** Wrong substrate or weak
   calibration → stop and record; do not fetch a cleaner world to recover
   a pass.
6. **Negatives stay** in `results/FINDINGS.md` (create when the first
   scored run exists). Later fixes get new IDs; old rows remain.

## Evidence grades (world parameters)

| Grade | Meaning |
|-------|---------|
| **A** | Directly observed or experimentally estimated |
| **B** | Established institutional or engineering protocol |
| **C** | Modelling assumption or extrapolation |

Where evidence is thin, keep uncertainty or simplify the domain.

## Session logs

After work that changes the repo or makes a project decision, write
`drafts/YYYY-MM-DD-topic.md` and update `drafts/HANDOFF.md`. Template is
in `drafts/README.md`.
