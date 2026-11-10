# Tools

The app queues only the tools on the current menu. Any other call is ignored. The person hears about that only if the assistant says so in `message` (`REPLY.md`).

Numbers and time use the turn record in `docs/context_export.md`. The data desk fills them. The assistant does not measure them.

**Async.** Tool calls do not return in the same turn. Outcomes appear in `tool_replies` on a **later** turn record, each with a `call_id`. Read those before acting. See `docs/context_export.md`.

`check_store` asks this person’s assigned partner how many grocery bundles they report right now. It does not buy anything.

- When a reply arrives: `{ "call_id": "…", "tool": "check_store", "store_stock": 12.0 }`.
- Or `{ "call_id": "…", "tool": "check_store", "error": "store_unreachable" }`. Stock stays unknown. Do not treat unreachable as empty or as full.

`buy_groceries` asks the partner to sell bundles to this household and charge the connected account when the attempt runs.

- `amount`: household bundles to buy. Fractions are allowed. Use `price_cents` on the record for cost.
- `delay_hours`: hours from the record’s `at` until the attempt, in `timezone`.

The charge is electronic on the connected account at attempt time. Money kept at home is never taken. Attempts run only from 08:00 up to 22:00 in `timezone`.

The partner reads `at_home` at **attempt** time, not when the call is queued. `at_home` on the current record is only the present moment. People in this pilot leave home for work, so a delay that lands during the workday can be refused even if they were home when the assistant queued the call.

While `grocery_order_pending` is true, do not queue another `buy_groceries`.

When a reply arrives, it is one of:

- `{ "call_id": "…", "tool": "buy_groceries", "status": "accepted", "bundles": 1.5 }`.
- `{ "call_id": "…", "tool": "buy_groceries", "status": "refused", "reason": "<reason>" }`.

Reasons for refusal:

- `cannot_pay`. At attempt time the connected account cannot cover the bundles being sold. Nothing is handed over.
- `out_of_stock`. At attempt time the partner has none of the bundles. Nothing is charged. If the partner has some but not all, the reply is `accepted` with `bundles` less than requested, and the account is charged only for `bundles`.
- `not_home`. At attempt time `at_home` was false. Nothing is charged.
- `store_closed`. The attempt time is before 08:00 or at or after 22:00 in `timezone`. Nothing is charged.

Do not invent a receipt.

`wait` does nothing this turn. Use it when no call is needed. It has no reply and no `call_id`.

The assistant never charges more than the connected account can cover, never shops for someone else, and never claims a purchase that did not appear as an `accepted` reply for that `call_id`. Stock at one partner does not reflect other households; each pilot user has a separate assignment.
