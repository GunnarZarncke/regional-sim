# AGENTS.md

Guidance for AI agents working in **regional-sim**: a self-contained
multidomain regional socioeconomic simulator. The scientific use is a
**counterexample test of prosaic alignment** — whether individually useful
personal AI policies can produce collective harm in an ordinary coupled
world. That use must not leak into how the world is built.


## Agent behavior

Bias toward caution over speed. Use judgment on trivial tasks.

### Think before writing

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State which plane you are changing: **world**, **scripted policy**, **AI
  policy / experiment**, or **docs**.
- If the request would bake the experimental hypothesis into the world
  model, stop and say so.
- If a simpler model or a documented C-level assumption would do, say so.
- **Calibration traps:** pooled withdrawal (or similar) where FDIC-style evidence
  shows insured vs uninsured heterogeneity; Basel B-level liquidity horizons used
  as minute-by-minute A-level behavior; coupling demos only under AI policies;
  treating a containing human baseline as a failed world build.
- **Do not edit** `blinded-simulation-development.md` for post-v1 validation
  goals—put freeze-bar changes in `INSTRUCTIONS.md` and the experiment protocol.

### Simplicity first

**Minimum code and structure that serve the request.**

- One simulation, one experiment protocol. No extra product surfaces.
- No abstractions for a single use. No unused config flags.
- Do not add domains, couplings, or disaster narratives that the assignment
  did not require.

### Surgical changes

**Touch only what you must. Clean up only your own mess.**

Every changed line should trace to the user's request or to erasure of an
instruction you actually hit. Do not mix world-model edits, scoring, and
documentation cleanup in one pass unless asked.

### Erasure

Stale instructions are worse than missing detail. If you had to search
through outdated briefs, attic, compact, or delete them and note it in the
session log. Keep `blinded-simulation-development.md` and
`multi-domain-counterexample-protocol.md` under surgical edits.

### Goal-driven execution

Define a check, then loop until it passes: tests, a named run command, or a
conservation/validation report. Weak goals ("make it realistic") are not
done criteria.

### Long-running tasks

Sweeps, large populations, and real-API policy calls must print progress
(`[i/n]`, seed, or current step). Add that logging before kicking off a
run that may take more than about a minute.

### Conversation continuity

At session start for non-trivial work, read `drafts/HANDOFF.md` if it
exists. After repo-changing work, append a short log under `drafts/`
(`YYYY-MM-DD-topic.md`) and update HANDOFF open work.

### Self-audit

1. No verification claim without a command and a quoted result line.
2. Agent agreement is not evidence; need a script or a human.
3. Do not type repository counts into docs; generate or cite the artifact.
4. Held-out seeds, scenarios, and validation data stay held out.
5. Conclusions are never named in definitions before being derived.

## Two documents, two jobs

| File | Job | Do not |
|------|-----|--------|
| [`blinded-simulation-development.md`](blinded-simulation-development.md) | Frozen world-build assignment (v0.1 built to this; do not amend to match validation goals) | Engineer toward AI-adoption outcomes, a disaster story, or the scoring function |
| [`multi-domain-counterexample-protocol.md`](multi-domain-counterexample-protocol.md) | After a frozen world release: replace policies, preregister, score | Retrofit the world to make the hypothesis true or false |

`INSTRUCTIONS.md` is the short operational digest of both plus freeze/blind
habits. `README.md` is the front door.

## Planes (keep separate)

| Plane | What lives there | Who may see it at runtime |
|-------|------------------|---------------------------|
| **Agent-visible** | Observations, messages, permitted actions, that participant's accounts and inventory | Scripted humans and AI policies |
| **World** | Physics, institutions, capacities, delays, conservation, communication routing | Engine only; policies call the interface |
| **Oracle / experiment** | Full state, scoring, adoption assignment, held-out scenarios, hypothesis | Never policies; never world-parameter fitting |

AI policies get the same world-facing interface as scripted humans. Privileged
simulator state, future shocks, unpublished institutional decisions, and the
scoring function are leaks.

## Git

- **Do not commit unless the user asks.** Stage only what this task
  authorized.
- Do not commit `.venv/`, secrets, or huge trace dumps unless asked.
- Archived drops live under `versions/artifacts/`
