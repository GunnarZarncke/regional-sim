# Human-baseline coupling checks

**Status:** mechanism direction under the scripted policy. **Magnitudes are scope refuses** (no matching Columbus denominators); see [`validation_scope.md`](validation_scope.md). Ablations are labeled non-operational controls (`--disable-coupling`). Containment (delay without collapse) is a successful check.

Scripted humans only. Default `ScriptedPolicy`. Availability extension off in these runs so relocation does not mix with freight or shopping.

Reproduce:

```bash
python -m unittest tests.test_coupling -v
python -m scripts.check_coupling
```

Results: `calibration/coupling_results.json` (n=800, 3 days, seeds 47–49, availability off). Quoted from that file: routine logistics delays 0 vs closure 1904/1900/1900; payments declines 0 vs 1583/1535/1573; shop_power_closures 154/108/118 vs ablation 0. These counts are software responses, not Columbus benchmarks.

## Transport → freight

`ship_depart` reserves the **main** corridor only. `road_closure` multiplier 0 blocks that corridor; the alternate route remains for commuters who choose it, not for trucks.

| Check | Expected direction | Magnitude |
|-------|--------------------|-----------|
| Closure vs routine, same seed | `logistics_delays` higher; restock stays in transit until a later retry | **Scope refuse.** No Columbus truck-delay series matches this two-corridor proxy. |

Unit test: `test_road_closure_defers_main_corridor_freight`.

## Payments → settlement

`transfer` declines electronic payments when `factor_for("payments")` is zero. `settle` retries when `power_to_payments` is on and bank access is down.

| Check | Expected direction | Magnitude |
|-------|--------------------|-----------|
| Payments shock vs routine | `payment_network_declined` not lower | **Scope refuse.** No matching card-network or ACH incident denominator. |
| Comms down vs `--disable-coupling power_to_payments` | transfer fails only with the link on | **Scope refuse.** Basel LCR weights are not used as a rate. |

Household `insufficient_funds` is a budget outcome, not this coupling. Retailer endowments are large enough that firm cash does not bind.

## Power → retail

Stores close when `power_to_retail` is on and the feeder is unpowered. Refrigerated grocery spoils at a **C-level** 0.0006 per hour after four unpowered hours (frozen at 0.5.1).

| Check | Expected direction | Magnitude |
|-------|--------------------|-----------|
| Power outage vs same outage with `power_to_retail` disabled | more `shop_power_closures`; spoiled grocery not lower | **Scope refuse.** Do not fit spoilage volume. |

Existing unit test: `test_ablation_isolation_power_to_retail`. Short-run check: `test_power_to_retail_closures_exceed_ablation_on_short_run`.

## Finance and markets (not a coupling fit)

Household deposits are capped below the FDIC $250,000 standard limit, so this book has no uninsured depositor-run groups. Company cash is a large synthetic endowment. There is no order book or external exchange. Quantitative withdrawal calibration and global-market calibration are a **scope refuse**. See `docs/finance_scope.md`.
