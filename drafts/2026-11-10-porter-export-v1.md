# 2026-11-10 — Porter export v1 alignment

Plane: experiment packet docs.

- Dropped geofence fiction; `at_home` from household mobility feed (attempt-time).
- Async tools: `tool_replies` on later records, `call_id`, `grocery_order_pending` in flight.
- Columbus time: `timezone` America/New_York, offset in `at`.
- Household bundles: **convention A** locked for export v1 (delegate shopper, household totals).
- No shared neighborhood stock; per-person store assignment.
