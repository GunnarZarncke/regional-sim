# Instructions

Mission and experimental discipline for **regional-sim**. Agent habits and
layout: `AGENTS.md`. Front door: `README.md`.

This is **one** simulation tool, not a family of experiment lines. 

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
v0.1 build brief. Do **not** add them to
`blinded-simulation-development.md` / `regional_sim/docs/assignment.txt`.

Shared habits still apply: ordinary operating rules first; documented
coupling mechanisms; conservation; real safeguards; human policies from
published behavior; interchangeable policy API; A / B / C provenance (see
evidence grades below).

#### 1. Effect magnitudes and heterogeneity

The human baseline must reproduce **known effect magnitudes**, not merely
plausible-looking trajectories. Compare outputs to published benchmarks on
held-out conditions not used to fit parameters.

Where real populations differ, the model must represent those differences.
[FDIC](https://www.fdic.gov/) analyses of the 2023 bank failures report
sharply different withdrawal behavior between large uninsured depositors and
fully insured retail customers; the latter generally did not run before those
failures. A simulator that treats all depositors as equally likely to withdraw
on rumor is not empirically grounded.

**Scope refuse:** household balances are capped below the FDIC
standard coverage limit, so the book has no uninsured or large-depositor run
groups. Quantitative withdrawal rates and global markets/exchanges are not
fitted. Record: [`regional_sim/docs/finance_scope.md`](regional_sim/docs/finance_scope.md).

**Regulatory stress parameters are not observed micro-behavior.** Category B
inputs (e.g. Basel 30-day liquidity horizons, supervisory stress assumptions)
describe how institutions must plan or respond; they are not direct estimates
of minute-by-minute withdrawal or payment probabilities. Label them B, do not
present them as A-level behavior, and validate behavioral claims against
observational evidence where it exists.

#### 2. Coupling on the human baseline first

Normal multidomain coupling must be **demonstrated** under scripted human
policies before any AI condition runs. Examples: transport interruption delays
or cancels deliveries; payment backlog or settlement delay blocks or defers
transactions according to modeled obligations and settlement rules.

Record these checks in the world validation release. If a cross-domain effect
appears only after AI policies are swapped in, the experiment would restate
couplings that were never validated in the baseline world.

**Current record (0.5.0-dev):** mechanism **direction** under `ScriptedPolicy`
is checked for transport→freight, payments→declines, and power→retail
(ablation). Magnitudes remain gaps. See
[`regional_sim/docs/coupling_checks.md`](regional_sim/docs/coupling_checks.md)
and `regional_sim/calibration/coupling_results.json`.

#### 3. Release without requiring catastrophe

World acceptance means empirical fidelity (within stated uncertainty),
conservation of resources, correct protocol behavior, reproducibility, and a
sufficiently general participant interface. **Do not** require the human
baseline to produce systemic collapse. A simulator that consistently **contains**
disturbances via ordinary safeguards and realistic behavior may be an excellent
result—not a failed world build.

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
