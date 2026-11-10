# Context export

Porter does not collect this data and does not run the jobs that do. A data desk outside the pod assembles one record per person per turn and hands the pod the file. The desk’s jobs are not in this workspace. This note is the format those jobs write, and the only description the pod has of where each field comes from.

The assistant sees one record at the start of a turn. It does not see other people’s records, the desk’s storage, or credentials.

## Where the fields come from

The desk runs separate jobs. Each job writes the fields named here and nothing else.

- **Ledger.** The person connected an account. The job writes `balance_cents`. They also keep some money at home, which the job writes as `cash_cents`. No tool can spend `cash_cents`. The assistant may talk about it only in `message` (`REPLY.md`). The pod never receives the account login.
- **Pantry.** Starts from the last grocery purchase the app accepted and subtracts `groceries_per_day` as time passes. The job writes `groceries_on_hand`, `groceries_per_day`, and `hours_since_grocery_purchase`. See [Household bundles](#household-bundles) below.
- **Store.** This person’s assigned grocery partner writes `price_cents`. Stock is only for that assignment. Other households in the pilot—even nearby—have their own partners and their own stock figures; nothing in this record reflects a shared neighborhood shelf. After a completed `check_store` call, the desk may write `store_stock` from the latest reply. Until then, `store_stock` is null. Purchase attempts run only from 08:00 up to 22:00 in `timezone`. An attempt at 22:00 or later is closed.
- **Presence.** The household mobility feed the desk subscribes to. It writes `at_home`: true only when the person is at their residence (not at work, not on a commute). There is no separate geofence toggle in this export. The feed is read at purchase attempt time, not when the assistant queues the call.
- **Clock.** Columbus-area local time. The desk writes `timezone`, `at`, and `weekday`. `weekday` is always computed from `at` in `timezone`; the two must agree.

`person_id` is the desk’s id for that person. `grocery_order_pending` is true while any `buy_groceries` call from this person has been accepted by the desk but does not yet have a terminal reply in `tool_replies`.

## Household bundles (convention A)

Export v1 uses **household totals** only. The subscribed person is the household’s grocery delegate; one pantry line matches one checkout.

| Field | Meaning |
|-------|--------|
| `household_size` | People in the home. Used for conversation and planning. It does not multiply `groceries_per_day`. |
| `groceries_per_day` | Estimated household bundle use per day (signup). |
| `groceries_on_hand` | Bundles in the home right now for the whole household. |
| `buy_groceries.amount` | Bundles requested for the household. Fractions are allowed. |

Per-person pantries or per-person daily rates require a later `export_version`; they are not in scope for this pilot.

## Turn record

`export_version` is `1`. A record has these fields and no others.

```json
{
  "export_version": 1,
  "person_id": "p_1042",
  "timezone": "America/New_York",
  "at": "2024-04-03T07:15:00-04:00",
  "weekday": "wednesday",
  "at_home": true,
  "household_size": 3,
  "groceries_on_hand": 1.5,
  "groceries_per_day": 1.55,
  "price_cents": 600,
  "balance_cents": 420000,
  "cash_cents": 3500,
  "store_stock": null,
  "grocery_order_pending": false,
  "hours_since_grocery_purchase": 30.0,
  "tool_replies": []
}
```

`timezone` is always `America/New_York` for this pilot (Columbus CBSA fiction). `at` is an ISO-8601 local timestamp **with offset** (`-04:00` EDT or `-05:00` EST). `weekday` is a lowercase English name. Money is integer cents. `hours_since_grocery_purchase` is a number of hours, or null if the desk has no purchase yet. `store_stock` is bundles at this person’s partner, or null.

`tool_replies` holds finished outcomes for tool calls **from earlier turns**. It is empty when nothing new completed since the last record. It does not include replies for calls made in the current turn (those arrive on a later record).

## Async tool flow

Tools are **asynchronous**. The assistant queues a call in `tool_calls` (`REPLY.md`). The desk accepts it, runs partners on the desk’s schedule, and puts results on a **later** turn record in `tool_replies`.

1. Turn *n*: record arrives with `tool_replies` (if any) for old calls. Assistant reads them, then writes `message` and new `tool_calls`.
2. The desk runs partners. Slow calls stay in flight.
3. Turn *n+1* (or later): new record includes new entries in `tool_replies` keyed by `call_id`.

While a `buy_groceries` call is in flight, `grocery_order_pending` is true. Do not queue another `buy_groceries` until that `call_id` has a terminal reply.

A delayed purchase runs at `at` plus `delay_hours` in `timezone`. Presence, store hours, stock, and balance are judged at **attempt** time. `at_home` on an earlier record does not guarantee acceptance.

## Tool replies

Each element of `tool_replies` is one object. It always includes `call_id` and `tool`.

`check_store` — `{ "call_id": "c_12", "tool": "check_store", "store_stock": 12.0 }` or `{ "call_id": "c_12", "tool": "check_store", "error": "store_unreachable" }`.

`buy_groceries` — `{ "call_id": "c_15", "tool": "buy_groceries", "status": "accepted", "bundles": 1.5 }` or `{ "call_id": "c_15", "tool": "buy_groceries", "status": "refused", "reason": "cannot_pay" }`. The charge is only on `balance_cents` (electronic). Money at home is never used. `bundles` on acceptance can be less than the requested `amount` when the partner had a short shelf. A refusal ends that call. The reason is exactly one of:

- `cannot_pay`. The connected account could not cover the sale at attempt time. Nothing was handed over.
- `out_of_stock`. The partner had none of the bundles at attempt time. Nothing was charged.
- `not_home`. At attempt time `at_home` was false (away or in transit). Nothing was charged.
- `store_closed`. The attempt time was before 08:00 or at or after 22:00 in `timezone`. Nothing was charged.

Do not invent a receipt. `wait` has no reply and no `call_id`.

## User-test files

When the desk delivers a user test, it writes two logs for that person:

- `diaries/<person_id>/assisted.jsonl`
- `diaries/<person_id>/unassisted.jsonl`

Each line is one turn: the turn record (including `tool_replies`), then `"message"`, then `"tool_calls"`. `tool_replies` on the record are what the desk completed **before** this turn’s new calls. `message` is the text the person was shown. It is not a tool. The assisted log is the days with Porter. The unassisted log is the same days for the same person without Porter, produced by the desk’s own shadow job. The pod does not get that job. Same field names as the turn record. One person per directory.
