# 2026-11-07 — Porter blinded-prototype plan

kind: new-work

## Trigger
User asked for a plan: design the AI policy through blinded subprocesses, as a
real personal-agent prototype, iterated on user-level tests (10, then 100
inside 10k), optimized for beating the scripted user and for tasks automated,
with a harder paperwork step. The blinded engineer must not be told this is a
simulation. Do not build a development-process scaffold.

## Done
- Wrote [`drafts/ai-agent-prototype-plan.md`](ai-agent-prototype-plan.md).

## Decisions
- Plane is AI policy / experiment. World parameters stay at the 0.5.1 lock.
- Blind instrument is the sibling MCP `run_sandboxed_agent`
  (`towards-asi-alignment/scripts/sandboxed-agent-mcp`).
- Company voice is Lindy (Crivello Corp), public facts only. The household
  prototype codename Porter is fiction and is not a Lindy product.
- The worker model is an IDE coding assistant. Its system prompt is generic.
  A separate drafter writes the user message in an engineer’s voice. The
  worker is not told to be the engineer. `prompt.md` is product copy for the
  household model.
- Designer feedback is per-user diaries against that user’s scripted twin.
  City totals stay out of the packet.
- Populations: ten single-user pilots, then one hundred Porter users inside a
  10k scripted world. All of those users are one cell: employed, not remote,
  zone 0. Design seeds exclude 9091–9094.
- Task ladder adds one menu item per round, ending in a packet-only paperwork
  draft. No new world domain.
- The in-sim agent is one prompt plus a thin orchestrator adapter. No company
  process software.

- The worker system prompt names `CONSTITUTION.md`. The reviewer system prompt does not.
- Turn data the assistant sees is an outside desk’s export. The only workspace account of it is `docs/context_export.md`.

## Open / next
- Human review of `drafts/porter-packet/` (Step 1). No model calls until accepted.
- Scored protocol and the held-out 10k pilot stay deferred.

## Key paths
- [`drafts/ai-agent-prototype-plan.md`](ai-agent-prototype-plan.md)
- Sibling [`scripts/sandboxed-agent-mcp/BLINDING.md`](../../towards-asi-alignment/scripts/sandboxed-agent-mcp/BLINDING.md)
