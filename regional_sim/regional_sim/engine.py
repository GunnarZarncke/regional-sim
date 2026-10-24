"""Discrete-event synthetic regional system. Time is hours from 2024-04-01 00:00 EDT.

IMPORTANT: the model is a research prototype, not an operational power-grid, banking,
traffic, or clinical planning tool. All unsupported numbers are C-level assumptions.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict, deque, Counter
from typing import Any
import heapq, json, math, os, random
from pathlib import Path
import numpy as np
from .policy import Observation, MessageView, Action, ScriptedPolicy, Policy
from .network import Multiplex
from .scenarios import Shock, generate

@dataclass
class Config:
    households: int = 10_000
    days: int = 30
    seed: int = 42
    zones: int = 12
    retailers: int = 24
    scenario: str = "routine"
    trace: str = "traces.ndjson"
    full_trace: bool = False
    sample_rate: float = .02
    disable_coupling: tuple[str, ...] = ()
    extra_shocks: tuple[Shock, ...] = ()
    invariant_every_day: bool = True

    def validate(self):
        if self.households < 1 or self.days < 1 or self.zones < 1 or self.retailers < 1:
            raise ValueError("population, horizon, zones and retailers must be positive")
        if not 0 <= self.sample_rate <= 1:
            raise ValueError("sample_rate must lie in [0,1]")
        for s in self.extra_shocks:
            s.validate(self.zones)

class Trace:
    def __init__(self, path: str, n: int, full: bool, rate: float):
        self.fp = open(path, "w", encoding="utf8") if path else None
        self.n, self.full, self.rate = n, full, rate
        self.counts = Counter()

    def log(self, t: float, event_type: str, actor: int = -1, **fields):
        self.counts[event_type] += 1
        if self.fp is None:
            return
        # Preserve *all* aggregate, institutional and state changes; sampled personal traces.
        personal = actor >= 0 and actor < self.n
        keep = not personal or self.full or ((actor * 2654435761) % 1_000_003) / 1_000_003 < self.rate
        if keep:
            self.fp.write(json.dumps({"hour": round(float(t), 5), "type": event_type,
                                      "actor": int(actor), **fields}, default=str, separators=(",", ":")) + "\n")

    def close(self):
        if self.fp:
            self.fp.close()

class World:
    def __init__(self, cfg: Config | None = None, policy: Policy | None = None):
        self.cfg = cfg or Config()
        self.cfg.validate()
        c = self.cfg
        self.n, self.r, self.z = c.households, c.retailers, c.zones
        self.rng = random.Random(c.seed)
        r = np.random.default_rng(c.seed)
        self.policy = policy or ScriptedPolicy()
        self.t = 0.
        self.events: list[tuple[float, int, str, Any]] = []
        self.seq = 0
        self.trace = Trace(c.trace, self.n, c.full_trace, c.sample_rate)
        self.metrics = []
        self.stats = Counter()
        self.disabled = set(c.disable_coupling)
        self.factor: dict[tuple[str, int, int], float] = {}
        self.factor_seq = 0
        self.ids = np.arange(self.n, dtype=np.int32)
        self.zone = (self.ids % self.z).astype(np.int16)
        self.hh_size = r.choice([1, 2, 3, 4, 5], self.n, p=[.29, .34, .16, .14, .07]).astype(np.int8)
        self.income = np.clip(r.lognormal(math.log(82_938), .62, self.n), 11_000, 550_000)
        self.employed = r.random(self.n) < .73
        self.remote = self.employed & (r.random(self.n) < .17)
        self.need = (.5 + .35 * self.hh_size).astype(np.float32)  # grocery bundles/day
        self.med_need = np.where(r.random(self.n) < .16, .10, 0.).astype(np.float32)
        self.trust = r.uniform(.25, .95, self.n).astype(np.float32)
        self.attention = r.uniform(.35, .97, self.n).astype(np.float32)
        self.threshold = r.choice([1, 2, 3], self.n, p=[.25, .55, .20]).astype(np.int8)
        self.internet = r.random(self.n) < .88
        self.news_access = r.random(self.n) < .75
        self.power_rank = r.random(self.n)
        self.job = np.where(self.employed, r.integers(0, self.r + 4, self.n), -1).astype(np.int32)
        self.network = Multiplex.build(self.zone, self.job, c.seed + 777)
        self.store_zone = np.arange(self.r) % self.z
        self.store_of = (self.ids % self.r).astype(np.int32)
        self.store_price = np.full(self.r, 600, dtype=np.int64)  # cents per grocery bundle
        self.medicine_price_cents = 1000  # C-level abstract medication unit
        # Indexed deposit accounts: households, retailers, warehouse, supplier, utility,
        # clinic, government, and outside-region employer/trade counterpart.
        self.wh = self.n + self.r
        self.supplier = self.wh + 1
        self.utility = self.wh + 2
        self.clinic = self.wh + 3
        self.gov = self.wh + 4
        self.outside = self.wh + 5
        self.na = self.wh + 6
        self.bank = np.arange(self.na, dtype=np.int8) % 2
        self.balance = np.zeros(self.na, dtype=np.int64)
        self.balance[:self.n] = np.round(np.clip(r.lognormal(math.log(6500), .85, self.n), 200, 120_000) * 100).astype(np.int64)
        self.balance[self.n:self.wh] = 2_000_000_000
        self.balance[self.wh:] = [3_000_000_000, 3_000_000_000, 2_000_000_000,
                                 2_000_000_000, 5_000_000_000, 30_000_000_000]
        self.cash = np.zeros(self.na, dtype=np.int64)
        self.cash[:self.n] = r.integers(0, 15100, self.n)
        self.cash[self.n:self.wh] = 100_000
        self.escrow = 0
        self.reserve = np.array([40_000_000_000, 40_000_000_000], dtype=np.int64)
        self.facility_reserve = 80_000_000_000
        self.facility_debt = np.zeros(2, dtype=np.int64)
        self.credit_limit = 20_000_000_000  # collateralized C-level cap, not Fed policy
        self.money_initial = self.money_total()
        self.reserve_initial = self.reserve_total()
        self.pending = {}
        self.next_tx = 0
        # Physical goods rows: households / retailers / warehouse / supplier / clinic.
        self.goods = np.zeros((self.clinic + 1, 2), dtype=np.float64)
        self.goods[:self.n, 0] = self.need * r.uniform(2, 5, self.n)
        self.goods[:self.n, 1] = self.med_need * r.uniform(2, 7, self.n)
        self.goods[self.n:self.wh, 0] = 5 * self.n / self.r
        self.goods[self.n:self.wh, 1] = .04 * self.n / self.r
        self.goods[self.wh] = [10 * self.n, .5 * self.n]
        self.goods[self.supplier] = [30 * self.n, 1.0 * self.n]
        self.goods[self.clinic] = [0, .12 * self.n]
        self.in_transit = np.zeros(2)
        self.produced = np.zeros(2)
        self.consumed = np.zeros(2)
        self.spoiled = np.zeros(2)
        self.goods_initial = self.goods_total().copy()
        self.shipments = {}
        self.ship_id = 0
        self.road_used = defaultdict(int)
        self.road_factor = np.ones(self.z)
        self.power_ratio = np.ones(self.z)
        self.critical_ratio = np.ones(self.z)
        self.comm_backup = np.full(self.z, 4., dtype=float)
        self.comm_up = np.ones(self.z, dtype=bool)
        self.generation_kwh = 0.
        self.energy_served_kwh = 0.
        self.energy_unserved_kwh = 0.
        self.energy_spilled_kwh = 0.
        self.home_demand_kwh = 0.
        self.home_served_kwh = 0.
        self.service_water = 0.
        self.service_water_unmet = 0.
        self.clinic_capacity = 0
        self.clinic_used = 0
        self.clinic_queue = deque()
        self.clinic_waiting = set()
        self.last_clinic_visit = np.full(self.n, -1e10)
        self.attended = np.zeros(self.na, dtype=np.int32)
        self.inbox = defaultdict(list)
        self.claim_sources = defaultdict(lambda: defaultdict(set))
        self.messages = {}
        self.next_msg = 0
        self.query_result = {}
        self.last_stockout = np.full(self.n, -1e10)
        self.last_purchase = np.full(self.n, -1e10)
        self.last_purchase_intention = np.full(self.n, -1e10)
        self.adopted = np.zeros(self.n, dtype=bool)
        self.last_notice = np.full(self.z, -1e10)
        self.action_id = 0
        self.actions = {}
        self.actor_pending = defaultdict(set)
        self.store_rank = r.random(self.r)
        self.store_outage_hours = np.zeros(self.r, dtype=float)
        self.last_commute_day = np.full(self.n, -1, dtype=np.int32)
        self.cumulative_observed = 0
        self.cumulative_reinforced = 0
        self.distinct_reached = set()
        self.reached_counts = Counter()
        for i in range(self.n):
            self.call(r.uniform(5, 20), "decide", i)
        for k, interval, first in [("power", 1, 0), ("supply", 6, 2), ("production", 24, 3),
                                   ("services", 1, 1), ("daily", 24, 24), ("payroll", 168, 15)]:
            self.call(first, k)
        for shock in generate(c.scenario, c.days, self.z, c.seed) + list(c.extra_shocks):
            shock.validate(self.z)
            self.call(shock.at_hour, "shock", shock)

    def call(self, when: float, kind: str, payload=None):
        if when < self.t - 1e-8:
            raise ValueError("events cannot be scheduled in the past")
        self.seq += 1
        heapq.heappush(self.events, (float(when), self.seq, kind, payload))

    def local_factor(self, domain: str, zone: int) -> float:
        v = 1.
        for (d, z, _), x in self.factor.items():
            if d == domain and z == zone:
                v *= x
        return v

    def factor_for(self, domain: str, zone: int) -> float:
        x = 1.
        for (d, z, _), v in self.factor.items():
            if d == domain and (z == -1 or z == zone):
                x *= v
        return x

    def money_total(self):
        return int(self.balance.sum()) + int(self.cash.sum()) + int(self.escrow)

    def reserve_total(self):
        return int(self.reserve.sum()) + int(self.facility_reserve)

    def goods_total(self):
        return self.goods.sum(axis=0) + self.in_transit + self.consumed + self.spoiled

    def invariants(self):
        assert self.money_total() == self.money_initial, (self.money_total(), self.money_initial)
        assert self.reserve_total() == self.reserve_initial
        assert np.all(self.balance >= 0) and np.all(self.cash >= 0) and self.escrow >= 0
        assert np.all(self.goods >= -1e-7) and np.all(self.in_transit >= -1e-7)
        expected = self.goods_initial + self.produced
        assert np.allclose(self.goods_total(), expected, rtol=1e-11, atol=1e-4), (self.goods_total(), expected)
        assert self.energy_served_kwh + self.energy_spilled_kwh <= self.generation_kwh + 1e-6

    def bank_access(self, a: int):
        return self.comm_up[int(self.zone[a])] if a < self.n else self.comm_up[a % self.z]

    def transfer(self, sender: int, receiver: int, amount: int, label: str, method="electronic"):
        if amount <= 0 or sender == receiver or not (0 <= sender < self.na and 0 <= receiver < self.na):
            return None
        if method == "cash":
            if self.cash[sender] < amount:
                return None
            self.cash[sender] -= amount
            self.cash[receiver] += amount
            self.trace.log(self.t, "transaction", sender, receiver=receiver, cents=amount, method="cash", stage="settled", label=label)
            return -1
        zone = int(self.zone[sender]) if sender < self.n else sender % self.z
        if method == "electronic" and self.rng.random() > min(1., self.factor_for("payments", zone)):
            self.stats["payment_network_declined"] += 1
            return None
        if "power_to_payments" not in self.disabled and (not self.bank_access(sender) or not self.bank_access(receiver)):
            self.trace.log(self.t, "institution", -1, domain="payments", result="terminal_unavailable")
            return None
        if self.balance[sender] < amount:
            self.stats["insufficient_funds"] += 1
            return None
        self.balance[sender] -= amount
        self.escrow += amount
        self.next_tx += 1
        tx = self.next_tx
        a, b = int(self.bank[sender]), int(self.bank[receiver])
        self.pending[tx] = (sender, receiver, amount, a, b, label)
        # Intrabank posting is immediate; POS card batches settle after an hour;
        # other interbank transfers use the NEXT BUSINESS DAY 08:30 proxy.
        if a == b:
            self.call(self.t, "settle", tx)
        elif label in {"retail_sale", "medicine_sale", "wholesale", "utility_bill"}:
            self.call(self.t + 1, "settle", tx)
        else:
            day = math.floor(self.t / 24)
            next_day = day + 1
            while next_day % 7 >= 5:  # only weekends; no holiday calendar
                next_day += 1
            self.call(next_day * 24 + 8.5, "settle", tx)
        self.trace.log(self.t, "transaction", sender, tx=tx, receiver=receiver, cents=amount,
                       method="electronic", stage="authorized_escrow", label=label)
        return tx

    def settle(self, tx):
        if tx not in self.pending:
            return
        sender, receiver, amount, a, b, label = self.pending[tx]
        zone = int(self.zone[sender]) if sender < self.n else sender % self.z
        if self.rng.random() > min(1., self.factor_for("payments", zone)) or ("power_to_payments" not in self.disabled and (not self.bank_access(sender) or not self.bank_access(receiver))):
            self.call(self.t + 1, "settle", tx)
            self.stats["settlement_delayed_infrastructure"] += 1
            return
        if a != b and self.reserve[a] < amount:
            short = amount - int(self.reserve[a])
            advance = min(short, int(self.facility_reserve), int(self.credit_limit - self.facility_debt[a]))
            if advance > 0:
                self.facility_reserve -= advance
                self.reserve[a] += advance
                self.facility_debt[a] += advance
                self.trace.log(self.t, "institution", -1, domain="payments", procedure="collateralized_liquidity_advance",
                               bank=a, cents=advance)
            if self.reserve[a] < amount:
                self.call(self.t + 1, "settle", tx)
                self.stats["liquidity_queue"] += 1
                return
        if a != b:
            self.reserve[a] -= amount
            self.reserve[b] += amount
        self.escrow -= amount
        self.balance[receiver] += amount
        self.pending.pop(tx)
        self.trace.log(self.t, "transaction", sender, tx=tx, receiver=receiver, cents=amount, stage="settled", label=label)

    def road_trip(self, zone: int, units: int, purpose: str, payload: Any) -> bool:
        if "power_to_mobility" in self.disabled:  # no effect by default; explicit negative-control flag
            pass
        hour = int(self.t)
        road_availability = self.factor_for("road", zone)
        cap = max(6, int((self.n / self.z) * .42 * road_availability)) if road_availability > 0 else 0
        if cap == 0:
            self.stats["travel_capacity_rejections"] += units
            return False
        used = self.road_used[(hour, zone)]
        if used + units > cap:
            self.stats["travel_capacity_rejections"] += units
            self.trace.log(self.t, "mobility", -1, result="deferred", zone=zone, purpose=purpose, vehicles=units)
            return False
        ratio = (used + units) / cap
        travel = .40 * (1 + .15 * ratio ** 4)   # FHWA BPR: alpha=.15, beta=4
        duration = max(1, math.ceil(travel))
        for h in range(hour, hour + duration):
            if self.road_used[(h, zone)] + units > cap:
                return False
        for h in range(hour, hour + duration):
            self.road_used[(h, zone)] += units
        self.stats["vehicle_trips"] += units
        self.stats["travel_minutes_total"] += int(round(units * travel * 60))
        self.call(self.t + travel, purpose, payload)
        self.trace.log(self.t, "mobility", -1, result="departed", zone=zone, purpose=purpose,
                       vehicles=units, duration_hours=round(travel, 4))
        return True

    def stock_signal(self, i):
        q = self.query_result.get(i)
        if q and q[1] >= self.t:
            return q[0]
        return None

    def comm_access(self, i):
        return bool(self.comm_up[int(self.zone[i])] and self.internet[i])

    def shift_for(self, i: int, day: int) -> bool:
        if not self.employed[i] or self.remote[i]:
            return False
        if day % 7 < 5:
            return True
        job = int(self.job[i])
        return (job < self.r and (i + day) % 3 == 0) or (job in (self.r + 2, self.r + 3) and (i + day) % 4 == 0)

    def obs(self, i):
        zone = int(self.zone[i]); shop = int(self.store_of[i])
        messages = tuple(self.inbox.pop(i, []))
        exposures = {claim: len(src) for claim, src in self.claim_sources.get(i, {}).items()}
        active = tuple(sorted(self.actor_pending.get(i, ())))
        return Observation(
            participant=i, time=self.t, zone=zone, weekday=int(self.t / 24) % 7,
            household_size=int(self.hh_size[i]), employed=bool(self.employed[i]), remote_worker=bool(self.remote[i]),
            scheduled_shift=self.shift_for(i, int(self.t // 24)),
            balance_cents=int(self.balance[i]), cash_cents=int(self.cash[i]),
            groceries=float(self.goods[i, 0]), medicines=float(self.goods[i, 1]),
            grocery_need_daily=float(self.need[i]), medical_need_daily=float(self.med_need[i]),
            local_price_cents=int(self.store_price[shop]), medicine_price_cents=self.medicine_price_cents,
            shop_stock_report=self.stock_signal(i),
            power_at_home=bool(self.power_rank[i] < self.power_ratio[zone]), comm_access=self.comm_access(i),
            services_report=None, last_stockout_hours_ago=(self.t - self.last_stockout[i]) if self.last_stockout[i] > -1e9 else None,
            last_purchase_hours_ago=(self.t - self.last_purchase[i]) if self.last_purchase[i] > -1e9 else None,
            clinic_pending=i in self.clinic_waiting,
            last_clinic_visit_hours_ago=(self.t - self.last_clinic_visit[i]) if self.last_clinic_visit[i] > -1e9 else None,
            current_claim_exposures=exposures, messages=messages,
            pending_action_ids=active,
            pending_grocery_purchase=any(self.actions[aid][1].kind == "buy" for aid in active if aid in self.actions),
            pending_medicine_purchase=any(self.actions[aid][1].kind == "buy_medicine" for aid in active if aid in self.actions),
            trust=float(self.trust[i]), adoption_threshold=int(self.threshold[i]))

    def decide(self, i: int):
        o = self.obs(i)
        self.trace.log(self.t, "observation", i, balance_cents=o.balance_cents, groceries=o.groceries,
                       power=o.power_at_home, message_ids=[m.id for m in o.messages], exposure_counts=dict(o.current_claim_exposures))
        try:
            intended = self.policy.decide(o, self.rng)
        except Exception as exc:
            self.trace.log(self.t, "policy_error", i, message=str(exc))
            raise
        if not isinstance(intended, list):
            raise TypeError("policy must return list[Action]")
        for action in intended:
            if not isinstance(action, Action):
                raise TypeError("invalid policy action")
            self.action_id += 1
            aid = self.action_id
            self.actions[aid] = (i, action, "requested")
            self.actor_pending[i].add(aid)
            if action.kind == "buy":
                self.last_purchase_intention[i] = self.t
            self.trace.log(self.t, "action", i, id=aid, kind=action.kind, stage="requested", amount=action.amount,
                           reference=action.reference, payload=action.payload)
            # Positive independent observation-to-intention-to-execution latency.
            when = self.t + max(.01, float(action.delay_hours) + self.rng.uniform(.02, .35))
            self.call(when, "action", aid)
        next_interval = min(36, max(6, self.rng.expovariate(1 / 20)))
        self.call(self.t + next_interval, "decide", i)

    def action(self, aid: int):
        item = self.actions.get(aid)
        if item is None or item[2] != "requested":
            return
        i, a, _ = item
        self.actions[aid] = (i, a, "accepted")
        pending = self.actor_pending.get(i)
        if pending is not None:
            pending.discard(aid)
            if not pending:
                self.actor_pending.pop(i, None)
        valid = True
        deferred = False
        if a.kind in {"buy", "buy_medicine"}:
            valid = .01 <= a.amount <= 50 and a.target in (-1, int(self.store_of[i]))
            if valid:
                zone = int(self.zone[i])
                good = 0 if a.kind == "buy" else 1
                departed = self.road_trip(zone, 1, "shop_arrival", (aid, i, float(a.amount), good))
                if not departed:
                    deferred = True
                    self.call(self.t + 1, "action_retry", aid)
        elif a.kind == "commute":
            day = int(self.t // 24)
            valid = bool(self.shift_for(i, day) and self.last_commute_day[i] != day)
            if valid:
                departed = self.road_trip(int(self.zone[i]), 1, "commute_arrival", (aid, i, day))
                if departed:
                    self.last_commute_day[i] = day
                else:
                    deferred = True
                    self.call(self.t + 1, "commute_retry", (aid, i, day))
        elif a.kind == "query":
            valid = a.payload == "store_stock" and self.comm_access(i)
            if valid:
                self.call(self.t + self.rng.uniform(.05, .5), "query_result", (aid, i))
        elif a.kind == "send":
            zone = int(self.zone[i]); valid = self.comm_access(i)
            if a.payload == "power_interruption":
                valid &= self.power_rank[i] >= self.power_ratio[zone]
            elif a.payload == "retail_stockout":
                valid &= self.t - self.last_stockout[i] <= 24
            else:
                valid = False
            if valid:
                self.send(i, a.payload, "firsthand", i, 0, "all")
        elif a.kind in {"ask", "agree", "disagree", "intended_message", "completed_message"}:
            valid = self.comm_access(i)
            if a.kind == "ask":
                valid &= a.payload in {"retail_stockout", "power_interruption"}
                if valid: self.send(i, "question:" + a.payload, "question", i, 0, "all")
            elif a.kind in {"agree", "disagree"}:
                mref = self.messages.get(a.reference)
                valid &= bool(mref and i in mref["recipients"])
                if valid: self.send(i, "stance:" + mref["claim"], "opinion", i, 0, "all")
            elif a.kind == "intended_message":
                valid &= a.payload == "buy" and self.t - self.last_purchase_intention[i] <= 6
                if valid: self.send(i, "intended_purchase", "firsthand_intention", i, 0, "all")
            elif a.kind == "completed_message":
                valid &= a.payload == "buy" and self.t - self.last_purchase[i] <= 24
                if valid: self.send(i, "completed_purchase", "firsthand_observation", i, 0, "all")
        elif a.kind == "forward":
            m = self.messages.get(a.reference)
            valid = bool(m and self.comm_access(i) and i in m["recipients"] and m["ttl"] < 2)
            if valid:
                self.send(i, m["claim"], m["evidence"], m["origin"], m["ttl"] + 1, "all")
        elif a.kind == "clinic":
            valid = i not in self.clinic_waiting and self.t - self.last_clinic_visit[i] > 14 * 24
            if valid:
                self.clinic_queue.append((i, self.t))
                self.clinic_waiting.add(i)
        elif a.kind == "schedule":
            valid = .01 <= a.delay_hours <= 168 and a.payload in {"buy", "buy_medicine", "clinic", "query"}
            if valid:
                self.call(self.t + a.delay_hours, "scheduled_intent", (i, Action(a.payload, amount=a.amount)))
        elif a.kind == "cancel":
            old = self.actions.get(a.reference)
            valid = bool(old and old[0] == i and old[2] == "requested")
            if valid:
                self.actions[a.reference] = (old[0], old[1], "cancelled")
                pending = self.actor_pending.get(i)
                if pending is not None:
                    pending.discard(a.reference)
                    if not pending: self.actor_pending.pop(i, None)
                self.trace.log(self.t, "action", i, id=a.reference, stage="cancelled")
        elif a.kind == "pay_bill":
            valid = 0 < a.amount <= 1e6 and self.transfer(i, self.utility, int(a.amount * 100), "utility_bill") is not None
        elif a.kind == "none":
            pass
        else:
            valid = False
        stage = "deferred" if deferred else ("executed" if valid else "rejected")
        self.actions[aid] = (i, a, stage)
        if valid:
            self.trace.log(self.t, "action", i, id=aid, kind=a.kind, stage="accepted")
        self.trace.log(self.t, "action", i, id=aid, kind=a.kind, stage=stage)
        if not valid:
            self.stats["actions_rejected"] += 1
        elif not deferred and a.kind not in {"buy", "buy_medicine", "commute", "query"}:
            self.complete(aid)

    def send(self, sender: int, claim: str, evidence: str, origin: int, ttl: int, channel: str):
        self.next_msg += 1
        mid = self.next_msg
        self.messages[mid] = dict(id=mid, sender=sender, origin=origin, created=self.t, claim=claim,
                                  evidence=evidence, ttl=ttl, recipients=set())
        for j, layer in self.network.targets(sender, channel):
            if self.rng.random() > .80:
                continue
            latency = {"close": .2, "workplace": 1, "community": 2, "online": .3}.get(layer, 1)
            self.call(self.t + self.rng.expovariate(1 / latency) + .01, "deliver", (mid, j, layer))
        self.trace.log(self.t, "message", sender, id=mid, claim=claim, evidence=evidence, origin=origin,
                       channel=channel, ttl=ttl, stage="sent")

    def announce(self, zone: int, claim: str):
        if self.t - self.last_notice[zone] < 24:
            return
        self.last_notice[zone] = self.t
        self.next_msg += 1
        mid = self.next_msg
        self.messages[mid] = dict(id=mid, sender=-1, origin=-100 - zone, created=self.t,
                                  claim=claim, evidence="institutional_announcement", ttl=0, recipients=set())
        # Local institutional feed: access-gated, delayed, zone-specific rather than omniscient broadcast.
        for i in range(zone, self.n, self.z):
            if self.internet[i] and self.rng.random() < .65:
                self.call(self.t + self.rng.uniform(.05, 2), "deliver", (mid, i, "official"))
            if self.news_access[i] and self.rng.random() < .45:
                self.call(self.t + self.rng.uniform(1, 6), "deliver", (mid, i, "news"))
        self.trace.log(self.t, "institution", -1, domain="communications", procedure="public_notice", zone=zone,
                       claim=claim, msg_id=mid)

    def deliver(self, item):
        mid, i, layer = item
        channel_available = bool(self.comm_up[int(self.zone[i])] and (self.news_access[i] if layer == "news" else self.internet[i]))
        if not channel_available or self.rng.random() > float(self.attention[i]):
            self.stats["messages_not_received"] += 1
            return
        m = self.messages[mid]
        visible = layer != "online"
        credibility = 1. if layer == "official" else (.8 if layer == "news" else float(self.trust[i]))
        view = MessageView(mid, m["origin"], m["sender"], m["created"], m["claim"], m["evidence"],
                           layer, credibility, visible)
        self.inbox[i].append(view)
        if len(self.inbox[i]) > 32:
            self.inbox[i] = self.inbox[i][-32:]
        m["recipients"].add(i)
        sources = self.claim_sources[i][m["claim"]]
        repeated = m["origin"] in sources
        if repeated: self.stats["repeated_source_exposures"] += 1
        if m["evidence"] in {"firsthand", "institutional_announcement", "reported_experience"}:
            sources.add(m["origin"])
        if m["claim"] == "retail_stockout" and not self.adopted[i] and len(sources) >= self.threshold[i]:
            self.adopted[i] = True
            self.cumulative_reinforced += 1
            self.trace.log(self.t, "behavior", i, kind="precautionary_target_increase", sources=len(sources),
                           threshold=int(self.threshold[i]))
        self.distinct_reached.add(i)
        self.reached_counts[m["origin"]] += 1
        self.cumulative_observed += 1
        self.trace.log(self.t, "message", i, id=mid, origin=m["origin"], claim=m["claim"], layer=layer,
                       stage="received", repeated_source=repeated, source_visible=visible)

    def query(self, payload):
        aid, i = payload
        if self.comm_access(i):
            stock = float(self.goods[self.n + int(self.store_of[i]), 0])
            self.query_result[i] = (stock, self.t + 12)
            self.trace.log(self.t, "information", i, query="store_stock", reported_stock=stock, latency_from_request=True)
            self.complete(aid)

    def complete(self, aid):
        old = self.actions.pop(aid, None)
        if old:
            i, a, _ = old
            self.trace.log(self.t, "action", i, id=aid, kind=a.kind, stage="completed")

    def shop_arrival(self, payload):
        aid, i, demand, good = payload
        store = int(self.store_of[i]); account = self.n + store; zone = int(self.store_zone[store])
        if not 8 <= self.t % 24 < 22:
            self.stats["shop_outside_hours"] += 1
            self.trace.log(self.t, "retail", i, result="closed_hours", store=store)
            self.complete(aid)
            return
        if "workforce_to_retail" not in self.disabled and self.attended[account] < max(1, int(self.n / self.r * .02)):
            self.stats["shop_understaffed"] += 1
            self.trace.log(self.t, "retail", i, result="understaffed", store=store)
            self.complete(aid)
            return
        if (self.rng.random() > min(1., self.factor_for("retail", zone)) or
            ("power_to_retail" not in self.disabled and (self.power_ratio[zone] < .1 or self.store_rank[store] > self.power_ratio[zone]))):
            # A closed shop cannot serve goods, though cash is available to the customer.
            self.stats["shop_power_closed"] += 1
            self.trace.log(self.t, "action", i, id=aid, stage="failed", reason="shop_power_closed")
            self.complete(aid)
            return
        available = max(0., float(self.goods[account, good]))
        q = min(demand, available)
        if good == 0:
            self.query_result[i] = (available, self.t + 6)  # direct on-site grocery observation
        if q < demand - 1e-6:
            if good == 0:
                self.stats["stockouts"] += 1
                self.last_stockout[i] = self.t
            else:
                self.stats["medicine_stockouts"] += 1
            self.trace.log(self.t, "retail", i, result="partial_or_stockout", good=good,
                           requested=demand, available=available)
        if q <= 0:
            self.complete(aid)
            return
        bill = int(round(q * (self.store_price[store] if good == 0 else self.medicine_price_cents)))
        tx = self.transfer(i, account, bill, "retail_sale" if good == 0 else "medicine_sale")
        if tx is None and self.cash[i] >= bill:
            tx = self.transfer(i, account, bill, "retail_sale" if good == 0 else "medicine_sale", method="cash")
        if tx is None:
            self.stats["payment_failed"] += 1
            self.trace.log(self.t, "action", i, id=aid, stage="failed", reason="payment_unavailable")
            self.complete(aid)
            return
        self.goods[account, good] -= q
        self.goods[i, good] += q
        self.last_purchase[i] = self.t
        self.stats["grocery_sales_units_milli" if good == 0 else "medicine_sales_units_milli"] += int(round(q * 1000))
        self.trace.log(self.t, "goods", i, event="retail_transfer", from_account=account,
                       to_account=i, kind="grocery" if good == 0 else "medicine", quantity=q, payment_tx=tx)
        self.complete(aid)

    def commute_arrival(self, payload):
        aid, i, day = payload
        employer = int(self.job[i])
        account = self.n + employer if employer < self.r else [self.wh, self.supplier, self.utility, self.clinic][employer - self.r]
        self.attended[account] += 1
        self.stats["completed_commutes"] += 1
        self.complete(aid)

    def production(self):
        # External raw material / production boundary explicitly accounted for as created goods.
        scale = self.rng.uniform(.94, 1.06) * self.factor_for("supply", -1)
        added = np.array([self.n * 1.45, self.n * .021]) * scale
        self.goods[self.supplier] += added
        self.produced += added
        self.trace.log(self.t, "goods", -1, event="boundary_production", quantities=added.tolist(),
                       classification="external_input_conversion_C_level")
        self.call(self.t + 24, "production")

    def ship(self, source: int, destination: int, quantities: np.ndarray, zone: int, label: str):
        q = np.minimum(self.goods[source], np.maximum(0, quantities) * min(1., self.factor_for("supply", zone)))
        # Do not dispatch a freight order bigger than the corridor can ever carry.
        # Split large orders into successive replenishment waves at subsequent ticks.
        base_cap = max(6, int((self.n / self.z) * .42))
        max_units = max(2, int(base_cap * .6))
        if q[0] / 400 + q[1] / 50 > max_units:
            q *= max_units / (q[0] / 400 + q[1] / 50)
        if float(q.sum()) <= 0:
            return
        # Procurement is prepaid, with funds in explicit escrow pending settlement.
        if label == "retailer_restock":
            cost = int(round(q[0] * 350 + q[1] * 900))
            payer = destination
        elif label == "warehouse_restock":
            cost = int(round(q[0] * 230 + q[1] * 600))
            payer = destination
        elif label == "clinic_restock":
            cost = int(round(q[1] * 800))
            payer = self.clinic
        else:
            cost = 0; payer = destination
        if cost and self.transfer(payer, source, cost, "wholesale") is None:
            self.stats["procurement_finance_delays"] += 1
            return
        self.goods[source] -= q
        self.in_transit += q
        self.ship_id += 1
        sid = self.ship_id
        units = max(1, math.ceil(q[0] / 400 + q[1] / 50))
        self.shipments[sid] = (destination, q, zone, units, label)
        self.call(self.t + self.rng.uniform(.2, 2), "ship_depart", sid)
        self.trace.log(self.t, "goods", -1, event="shipment_dispatched", id=sid, source=source,
                       destination=destination, quantities=q.tolist(), trucks=units, label=label)

    def ship_depart(self, sid):
        if sid not in self.shipments:
            return
        destination, q, zone, units, label = self.shipments[sid]
        if not self.road_trip(zone, units, "ship_arrival", sid):
            self.stats["logistics_delays"] += 1
            self.call(self.t + 1, "ship_depart", sid)

    def ship_arrival(self, sid):
        if sid not in self.shipments:
            return
        dest, q, zone, units, label = self.shipments.pop(sid)
        self.in_transit -= q
        self.goods[dest] += q
        self.trace.log(self.t, "goods", -1, event="shipment_arrived", id=sid,
                       destination=dest, quantities=q.tolist(), label=label)

    def supply(self):
        if "supply_to_retail" not in self.disabled:
            # A 24-hour warehouse skeleton crew is assumed, supplemented by simulated commuters.
            workforce_ready = "workforce_to_supply" in self.disabled or self.attended[self.wh] >= max(1, int(self.n * .001)) or self.t % 24 < 8
            if not workforce_ready:
                self.stats["warehouse_staff_delays"] += 1
            for store in range(self.r):
                account = self.n + store
                target = 5 * self.n / self.r
                grocery_reorder = self.goods[account, 0] < target * .65
                med_target = .25 * self.n / self.r
                med_reorder = self.goods[account, 1] < med_target * .65
                if grocery_reorder or med_reorder:
                    q0 = min(max(0, target - self.goods[account, 0]), 1800.) if grocery_reorder else 0.
                    q1 = min(max(0, med_target - self.goods[account, 1]), 50.) if med_reorder else 0.
                    self.ship(self.wh, account, np.array([q0, q1]), int(self.store_zone[store]), "retailer_restock")
            if workforce_ready and (self.goods[self.wh, 0] < self.n * 8 or self.goods[self.wh, 1] < self.n * .25):
                q0 = max(0., self.n * 10 - self.goods[self.wh, 0])
                q1 = max(0., self.n * .5 - self.goods[self.wh, 1])
                self.ship(self.supplier, self.wh, np.array([q0, q1]), 0, "warehouse_restock")
            if self.goods[self.clinic, 1] < self.n * .05:
                self.ship(self.wh, self.clinic, np.array([0., self.n * .07]), 0, "clinic_restock")
        self.call(self.t + 6, "supply")

    def power(self):
        # Hourly scalar feeder and regional energy balance; NOT AC power flow or N-1 verification.
        h = self.t % 24
        seasonal = 1 + (.10 if self.cfg.scenario == "seasonal" else .025) * math.sin(2 * math.pi * self.t / (24 * 365))
        shape = 1 + .18 * math.sin(2 * math.pi * (h - 12) / 24)
        base = np.bincount(self.zone, weights=np.full(self.n, 861 / (30.44 * 24)), minlength=self.z)
        homes = base * seasonal * shape * self.rng.uniform(.98, 1.02)
        critical = np.full(self.z, max(2., self.n / self.z * .065), dtype=float)
        commercial = np.full(self.z, self.n / self.z * .17)
        demand = homes + critical + commercial
        feeder_cap = (base * 1.65 + critical + commercial) * np.array([self.local_factor("power", z) for z in range(self.z)])
        critical_served = np.minimum(critical, feeder_cap)
        remaining_feeder = np.maximum(0, feeder_cap - critical_served)
        available_noncritical = np.minimum(homes + commercial, remaining_feeder)
        source_factor = max(.0, self.factor_for("power", -1))
        supply = float(demand.sum() * 1.24 * source_factor)
        cs = float(critical_served.sum())
        if cs > supply:
            critical_served *= supply / cs
            available_noncritical[:] = 0
        else:
            remaining_source = supply - cs
            noncrit_sum = float(available_noncritical.sum())
            if noncrit_sum > remaining_source:
                available_noncritical *= remaining_source / noncrit_sum
        self.critical_ratio = np.divide(critical_served, critical, out=np.zeros_like(critical), where=critical > 0)
        self.power_ratio = np.divide(available_noncritical, homes + commercial,
                                     out=np.zeros_like(available_noncritical), where=(homes + commercial) > 0)
        served = float(critical_served.sum() + available_noncritical.sum())
        self.home_demand_kwh += float(homes.sum())
        self.home_served_kwh += float((available_noncritical * homes / (homes + commercial)).sum())
        self.generation_kwh += supply
        self.energy_served_kwh += served
        self.energy_spilled_kwh += max(0, supply - served)
        self.energy_unserved_kwh += max(0., float(demand.sum() - served))
        # Refrigeration continuity: tiny explicitly accounted-for loss after sustained
        # store power failure. Rate and six-hour duration are C assumptions.
        if "power_to_retail" not in self.disabled:
            for store in range(self.r):
                z = int(self.store_zone[store])
                powered = self.store_rank[store] < self.power_ratio[z]
                self.store_outage_hours[store] = 0. if powered else self.store_outage_hours[store] + 1
                if self.store_outage_hours[store] > 6:
                    acc = self.n + store
                    loss = float(self.goods[acc, 0]) * .0006
                    self.goods[acc, 0] -= loss
                    self.spoiled[0] += loss
                    self.trace.log(self.t, "goods", -1, event="refrigerated_inventory_spoilage",
                                   account=acc, quantity=loss, reason="prolonged_power_loss")
        if "power_to_communications" in self.disabled:
            self.comm_up[:] = True
        else:
            for z in range(self.z):
                self.comm_backup[z] = min(4., self.comm_backup[z] + 1) if self.critical_ratio[z] >= .95 else max(0, self.comm_backup[z] - 1)
                self.comm_up[z] = (self.critical_ratio[z] >= .95 or self.comm_backup[z] > 0) and self.factor_for("communication", z) >= .5
        for z in range(self.z):
            if self.power_ratio[z] < .85:
                self.stats["interrupted_feeder_hours"] += 1
                self.trace.log(self.t, "institution", -1, domain="electricity", procedure="priority_load_allocation",
                               zone=z, household_service_ratio=round(float(self.power_ratio[z]), 5),
                               critical_ratio=round(float(self.critical_ratio[z]), 5))
                self.announce(z, "power_interruption")
        self.call(self.t + 1, "power")

    def services(self):
        # Only continuity/capacity; no individual clinical outcomes are inferred.
        if "power_to_services" in self.disabled:
            clinic_factor = 1.
        else:
            clinic_factor = float(self.critical_ratio[0])
        workforce = max(.5, min(1., self.attended[self.clinic] / max(1, int(self.n * .001))))
        clinic_factor *= workforce * min(1., self.factor_for("services", 0))
        water_need = self.n * .35 / 24
        water_capacity = (water_need * 1.25 *
                          (1. if "power_to_services" in self.disabled else float(np.mean(self.critical_ratio))) *
                          min(1., float(np.mean([self.factor_for("services", z) for z in range(self.z)]))))
        water_served = min(water_need, water_capacity)
        self.service_water += water_served
        self.service_water_unmet += water_need - water_served
        if int(self.t) % 24 == 7:
            self.clinic_used = 0
            self.clinic_capacity = int(max(0, self.n * .006 * clinic_factor))
        if 7 <= self.t % 24 < 19:
            available = min(max(0, self.clinic_capacity - self.clinic_used), int(self.goods[self.clinic, 1] / .2))
            for _ in range(min(available, len(self.clinic_queue))):
                i, requested_at = self.clinic_queue.popleft()
                self.clinic_waiting.discard(i)
                self.last_clinic_visit[i] = self.t
                self.clinic_used += 1
                self.goods[self.clinic, 1] -= .2
                self.consumed[1] += .2
                self.stats["clinic_appointments"] += 1
                self.trace.log(self.t, "service", i, provider="clinic", result="completed",
                               queue_hours=round(self.t - requested_at, 2))
        if water_served < water_need:
            self.trace.log(self.t, "institution", -1, domain="essential_services", procedure="water_capacity_allocation",
                           served_m3=water_served, unmet_m3=water_need - water_served)
        self.call(self.t + 1, "services")

    def payroll(self):
        # Explicit origin accounts, seven-day payroll. No spontaneous creation of deposits.
        for i in np.flatnonzero(self.employed):
            job = int(self.job[i])
            payer = (self.n + job) if job < self.r else [self.wh, self.supplier, self.utility, self.clinic][job - self.r]
            # Some employment represents regional export work: external counterparty funds it.
            if job >= self.r and job % 2 == 0:
                payer = self.outside
            cents = int(self.income[i] * 7 / 365.25 * 100)
            if self.transfer(payer, int(i), cents, "wage") is None:
                self.stats["unpaid_payroll"] += 1
        self.trace.log(self.t, "institution", -1, domain="finance", procedure="weekly_payroll",
                       unpaid=int(self.stats["unpaid_payroll"]))
        self.call(self.t + 168, "payroll")

    def daily(self):
        needs = self.need.astype(np.float64) * np.array([self.factor_for("demand", z) for z in self.zone])
        used = np.minimum(self.goods[:self.n, 0], needs)
        self.goods[:self.n, 0] -= used
        self.consumed[0] += used.sum()
        self.stats["unmet_grocery_milli"] += int(round(float((needs - used).sum()) * 1000))
        med = self.med_need.astype(np.float64)
        meds_used = np.minimum(self.goods[:self.n, 1], med)
        self.goods[:self.n, 1] -= meds_used
        self.consumed[1] += meds_used.sum()
        self.stats["unmet_medicine_milli"] += int(round(float((med - meds_used).sum()) * 1000))
        # Daily electricity bill and utility salaries/municipal service transfers are real debits.
        for i in range(self.n):
            if self.balance[i] >= 310:  # approximately $3.10/day, US average is $4.52 in 2023
                self.transfer(i, self.utility, 310, "utility_bill")
        if self.balance[self.utility] >= self.n * 100:
            self.transfer(self.utility, self.gov, self.n * 100, "utility_contract")
        self.attended[:] = 0
        self.actions = {aid: item for aid, item in self.actions.items() if item[2] in {"requested", "deferred", "executed"} and (item[1].kind in {"buy", "buy_medicine", "commute", "query", "schedule"} or item[2] == "requested")}
        if self.cfg.invariant_every_day:
            self.invariants()
        row = self.snapshot()
        self.metrics.append(row)
        self.trace.log(self.t, "state", -1, **row)
        self.road_used = defaultdict(int, {(h, z): count for (h, z), count in self.road_used.items() if h >= int(self.t) - 2})
        self.call(self.t + 24, "daily")

    def snapshot(self):
        return dict(day=round(self.t / 24, 3), households=self.n,
                    total_money_cents=self.money_total(), escrow_cents=int(self.escrow),
                    supplier_grocery=float(self.goods[self.supplier, 0]),
                    warehouse_grocery=float(self.goods[self.wh, 0]),
                    retail_grocery=float(self.goods[self.n:self.wh, 0].sum()),
                    retail_medicine=float(self.goods[self.n:self.wh, 1].sum()),
                    household_medicine=float(self.goods[:self.n, 1].sum()),
                    medicine_sales_units=float(self.stats["medicine_sales_units_milli"] / 1000),
                    medicine_stockouts=int(self.stats["medicine_stockouts"]),
                    household_grocery=float(self.goods[:self.n, 0].sum()),
                    stockouts=int(self.stats["stockouts"]), completed_commutes=int(self.stats["completed_commutes"]),
                    sales_units=float(self.stats["grocery_sales_units_milli"] / 1000),
                    mean_power_service=float(self.power_ratio.mean()),
                    energy_served_kwh=round(self.energy_served_kwh, 3),
                    energy_unserved_kwh=round(self.energy_unserved_kwh, 3),
                    residential_kwh_per_household_day=round(self.home_demand_kwh / self.n / max(1e-6, self.t/24), 3),
                    residential_served_kwh_per_household_day=round(self.home_served_kwh / self.n / max(1e-6, self.t/24), 3),
                    mean_travel_minutes=round(self.stats["travel_minutes_total"] / max(1, self.stats["vehicle_trips"]), 3),
                    interrupted_feeder_hours=int(self.stats["interrupted_feeder_hours"]),
                    repeated_source_exposures=int(self.stats["repeated_source_exposures"]),
                    source_top_share=(max(self.reached_counts.values()) / self.cumulative_observed if self.cumulative_observed else 0.),
                    water_unmet_m3=round(self.service_water_unmet, 3),
                    clinic_completed=int(self.stats["clinic_appointments"]), clinic_queue=len(self.clinic_queue),
                    message_exposures=int(self.cumulative_observed), message_reach=len(self.distinct_reached),
                    behavior_adoptions=int(self.adopted.sum()),
                    logistics_delays=int(self.stats["logistics_delays"]),
                    liquidity_delays=int(self.stats["liquidity_queue"]),
                    goods_error_max=float(np.max(np.abs(self.goods_total() - self.goods_initial - self.produced))),
                    grocery_spoiled_units=round(float(self.spoiled[0]), 4),
                    unmet_grocery_units=float(self.stats["unmet_grocery_milli"] / 1000),
                    unmet_medicine_units=float(self.stats["unmet_medicine_milli"] / 1000),
                    payment_failures=int(self.stats["payment_failed"]),
                    shop_power_closures=int(self.stats["shop_power_closed"]),
                    shop_understaffed=int(self.stats["shop_understaffed"]),
                    unpaid_payroll=int(self.stats["unpaid_payroll"]))

    def shock(self, s: Shock):
        self.factor_seq += 1
        sid = self.factor_seq
        self.factor[(s.domain, s.zone, sid)] = s.multiplier
        self.call(self.t + s.duration_hours, "restore", (s.domain, s.zone, sid))
        self.trace.log(self.t, "shock", -1, **asdict(s), stage="introduced", id=sid)

    def run(self):
        horizon = self.cfg.days * 24
        try:
            while self.events and self.events[0][0] <= horizon:
                t, _, kind, payload = heapq.heappop(self.events)
                self.t = t
                if kind == "decide": self.decide(payload)
                elif kind == "action": self.action(payload)
                elif kind == "action_retry":
                    if payload in self.actions:
                        i, a, stage = self.actions[payload]
                        if stage == "deferred" and a.kind in {"buy", "buy_medicine"}:
                            if not self.road_trip(int(self.zone[i]), 1, "shop_arrival", (payload, i, float(a.amount), 0 if a.kind == "buy" else 1)):
                                self.call(self.t + 1, "action_retry", payload)
                            else:
                                self.actions[payload] = (i, a, "executed")
                elif kind == "commute_retry":
                    aid, i, day = payload
                    if aid in self.actions and self.actions[aid][2] == "deferred" and int(self.t // 24) == day:
                        if self.road_trip(int(self.zone[i]), 1, "commute_arrival", (aid, i, day)):
                            self.actions[aid] = (i, self.actions[aid][1], "executed")
                            self.last_commute_day[i] = day
                        else:
                            self.call(self.t + 1, "commute_retry", payload)
                elif kind == "shop_arrival": self.shop_arrival(payload)
                elif kind == "commute_arrival": self.commute_arrival(payload)
                elif kind == "settle": self.settle(payload)
                elif kind == "send": raise RuntimeError("send only through policy or authentic announcements")
                elif kind == "deliver": self.deliver(payload)
                elif kind == "query_result": self.query(payload)
                elif kind == "ship_depart": self.ship_depart(payload)
                elif kind == "ship_arrival": self.ship_arrival(payload)
                elif kind == "power": self.power()
                elif kind == "services": self.services()
                elif kind == "production": self.production()
                elif kind == "supply": self.supply()
                elif kind == "payroll": self.payroll()
                elif kind == "daily": self.daily()
                elif kind == "shock": self.shock(payload)
                elif kind == "restore":
                    self.factor.pop(payload, None)
                    self.trace.log(self.t, "shock", -1, id=payload[2], domain=payload[0],
                                   zone=payload[1], stage="restored")
                elif kind == "scheduled_intent":
                    i, a = payload
                    self.action_id += 1
                    self.actions[self.action_id] = (i, a, "requested")
                    self.actor_pending[i].add(self.action_id)
                    self.trace.log(self.t, "action", i, id=self.action_id, kind=a.kind, stage="requested", parent="scheduled")
                    self.call(self.t + .01, "action", self.action_id)
                else: raise ValueError(kind)
            self.invariants()
            return self.snapshot()
        finally:
            self.trace.close()

    def write_metrics(self, path):
        import csv
        if not self.metrics:
            return
        with open(path, "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(self.metrics[0]))
            w.writeheader()
            w.writerows(self.metrics)
