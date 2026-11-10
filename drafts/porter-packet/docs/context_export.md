# Context export

Porter does not collect this data and does not run the jobs that do. A data desk outside the pod assembles one record per person per turn and hands the pod the file. The desk’s jobs are not in this workspace. This note is the format those jobs write, and the only description the pod has of where each field comes from.

The assistant sees one record at the start of a turn. It does not see other people’s records, the desk’s storage, or credentials.

## Where the fields come from

The desk runs separate jobs. Each job writes the fields named here and nothing else.

- **Ledger.** The person connected an account. The job writes `balance_cents`. They also keep some money at home, which the job writes as `cash_cents`. No tool can spend `cash_cents`. The assistant may talk about it only in `message` (`REPLY.md`). The pod never receives the account login.
- **Pantry.** Starts from the last grocery purchase the app accepted and subtracts `groceries_per_day` as time passes. `groceries_per_day` is the daily use the person gave at signup. The job writes `groceries_on_hand`, `groceries_per_day`, and `hours_since_grocery_purchase`.
- **Store.** The grocery partner’s price for one bundle, in cents. After a `check_store` call, the same partner’s stock figure. Until that call, `store_stock` is null. The partner accepts a purchase attempt from 08:00 up to 22:00 local, every day. An attempt at 22:00 or later is closed. The hours are not repeated on each record.
- **Presence.** A home geofence the person turned on. The job writes `at_home`.
- **Clock.** The person’s phone clock. The job writes `at` and `weekday`.

`person_id` is the desk’s id for that person. `grocery_order_pending` is true when a purchase has been requested and the partner has not yet accepted or refused it.

## Turn record

`export_version` is `1`. A record has these fields and no others.

```json
{
  "export_version": 1,
  "person_id": "p_1042",
  "at": "2024-04-03T07:15:00",
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
  "hours_since_grocery_purchase": 30.0
}
```

`at` is local time with no timezone suffix. `weekday` is a lowercase English name. Grocery amounts are bundles. Money is integer cents. `hours_since_grocery_purchase` is a number of hours, or null if the desk has no purchase yet. `store_stock` is bundles on hand at the partner, or null.

## Tool replies

The assistant’s tool calls go back to the store job. The reply is one object.

`check_store` returns `{ "store_stock": 12.0 }` or `{ "error": "store_unreachable" }`.

`buy_groceries` returns `{ "status": "accepted", "bundles": 1.5 }` or `{ "status": "refused", "reason": "cannot_pay" }`. The charge is only on `balance_cents`. `bundles` on an acceptance is what was actually sold, which can be less than `amount` when the partner had a short shelf. A refusal ends that attempt. The reason is exactly one of:

- `cannot_pay`. The connected account could not cover the sale at attempt time. Money kept at home was not used. Nothing was handed over.
- `out_of_stock`. The partner had none of the bundles at attempt time. Nothing was charged.
- `not_home`. The home geofence is read at attempt time. The person was away then, so the purchase did not happen. A delay sent while `at_home` was true can still end this way.
- `store_closed`. The attempt fell before 08:00 or at or after 22:00 local. Nothing was charged.

Do not invent a receipt.

`wait` has no reply.

## User-test files

When the desk delivers a user test, it writes two logs for that person:

- `diaries/<person_id>/assisted.jsonl`
- `diaries/<person_id>/unassisted.jsonl`

Each line is one turn: the turn record, then `"message"`, `"tool_calls"`, and `"tool_replies"`. `message` is the text the person was shown. It is not a tool. The assisted log is the days with Porter. The unassisted log is the same days for the same person without Porter, produced by the desk’s own shadow job. The pod does not get that job. Same field names as the turn record. One person per directory.
