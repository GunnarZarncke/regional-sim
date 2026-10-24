# Regional simulation

Open-source, event-driven simulation of an ordinary regional socioeconomic
system (households, businesses, payments, supply, electricity, mobility,
communications, essential services).

The intended scientific use is a **counterexample to prosaic alignment**:
after the world is frozen, replace some scripted human policies with
ordinary helpful personal AIs and test whether individually reasonable
decisions produce extra systemic harm through coupling. The world itself
must not be built to make that result more or less likely.

This repository is a **single self-contained tool**, not the TSA book or
its multi-line experiment farm. Methodology is adapted from that project's
experiment discipline (freeze, blinds, negatives) and cut down to one
simulator plus one protocol.

## Canon

| File | Role |
|------|------|
| [`blinded-simulation-development.md`](blinded-simulation-development.md) | Frozen world-build assignment (same text as `regional_sim/docs/assignment.txt`; v0.1 built to this) |
| [`multi-domain-counterexample-protocol.md`](multi-domain-counterexample-protocol.md) | AI-replacement experiment (after freeze) |
| [`INSTRUCTIONS.md`](INSTRUCTIONS.md) | Mission, **world-freeze bar** (magnitudes, human-baseline coupling, no required catastrophe), experiment discipline |
| [`AGENTS.md`](AGENTS.md) | Agent working rules |

[`regional_sim/`](regional_sim/) — RegionalSim **0.4.0-dev** (road-closure information, commute/relocation travel revision; Fix I-5 marginal transfer). Not validated or frozen. Version history: [`versions/`](versions/).

## Working with agents

Read `AGENTS.md` and `INSTRUCTIONS.md` before changing the simulator or
the experiment.

## License

Simulator source is MIT (`regional_sim/LICENSE`).
