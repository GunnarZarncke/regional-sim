# 2026-11-10 — Porter phases vs protocol

Plane: experiment plan.

Each kept Porter round is a version `V_k` (prompt hash, that round’s menu,
model id, adapter). Discarded rounds are not evaluated and not rolled out.

`V*` is the last kept version whose menu is the full ordinary action
interface. Protocol §5 runs only on `V*`. The adoption sweep deploys those
same bytes. A grocery-only or mid-ladder 100-in-10k run is an exploratory
check of that `V_k`, not §5.

Candidate primary outcomes, not yet frozen: unmet grocery units, unserved
household-hours, payment failures, logistics delays, spoiled groceries.
