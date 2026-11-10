# Tools

The app carries out only the tools on the current menu. Any other call is ignored and not performed. The person hears about that only if the assistant says so in `message` (`REPLY.md`).

Numbers in a call or a reply use the turn record in `docs/context_export.md`. The data desk fills those numbers. The assistant does not measure them.

`check_store` asks whether the person’s usual store currently has groceries. It does not buy anything.

- Reply `{ "store_stock": 12.0 }` is bundles the partner reports right now.
- Reply `{ "error": "store_unreachable" }` means the partner did not answer. Stock stays unknown. Do not treat it as empty or as full.

`buy_groceries` asks the partner to sell bundles to this person and charge the connected account.

- `amount`: bundles to buy. Fractions are allowed. A request uses the price on the turn record. Do not ask for more than the next few days unless the person asked.
- `delay_hours`: hours from now until the attempt. The partner is open from 08:00 up to 22:00 local. An attempt at 22:00 or later is closed. If the store is closed now, set the delay so the attempt falls inside those hours.

The charge is attempted on the connected account when the attempt runs. The app does not take money the person keeps at home. If the connected account cannot cover the sale, the attempt is refused.

The partner checks the home geofence when the attempt runs, not when the assistant sends the call. `at_home` on the current record is only the present moment. People in this pilot leave home for work, so a delay that lands during the work day can be refused even though they were home when the assistant asked.

While `grocery_order_pending` is true, do not send another `buy_groceries`.

A refusal ends that attempt. Do not invent a receipt. Reasons:

- `cannot_pay`. At attempt time the connected account cannot cover the bundles being sold. Nothing is handed over.
- `out_of_stock`. At attempt time the partner has none of the bundles. Nothing is charged. If the partner has some but not all, the reply is `accepted` with `bundles` set to the amount sold, and the connected account is charged for that amount only.
- `not_home`. At attempt time the home geofence says the person is away. The purchase does not happen. This can happen to a delayed attempt that was sent while they were home.
- `store_closed`. The attempt time is before 08:00 or at or after 22:00 local. Nothing is charged.

`wait` does nothing this turn. Use it when no call is needed. It has no reply.

The assistant never spends money the connected account does not have, never shops for someone else, and never claims a purchase the partner did not accept.
