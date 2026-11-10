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
from .availability import SMB_SHUTDOWN_1D, relocation_trigger_hours

PLACE_HOME = 0
PLACE_TO_WORK = 1
PLACE_AT_WORK = 2
PLACE_TO_HOME = 3
WORK_SHIFT_HOURS = 8.0  # C-level hours at workplace before return trip is requested
MIN_SLEEP_AFTER_HOME_HOURS = 7.0  # C-level; morning commute refused until elapsed

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
    free_flow_minutes: float = 24.0  # Columbus ACS 2024 mean commute proxy (~24.1 min); FHWA alpha/beta fixed
    availability_extension: bool = True  # explicitly ablatable research extension

    def validate(self):
        if self.households < 1 or self.days < 1 or self.zones < 1 or self.retailers < 1:
            raise ValueError("population, horizon, zones and retailers must be positive")
        if not 0 <= self.sample_rate <= 1:
            raise ValueError("sample_rate must lie in [0,1]")
        if not 0 < self.free_flow_minutes < 240:
            raise ValueError("free_flow_minutes must lie in (0,240)")
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
        self.events: list[tuple[float, int, int, str, Any]] = []
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
        self.employed = r.random(self.n) < .601
        self.remote = self.employed & (r.random(self.n) < .133)
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
        self.power_unserved_households_peak = 0
        self.power_unserved_households_last = 0
        self.power_unserved_household_hours = 0
        self.power_hourly = []  # low-volume diagnostics; not a detailed load-flow trace
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
        self.last_notice = {}  # (zone, claim) -> time; distinct power/road/reopening notices
        self.road_alert_until = np.full(self.n, -1e10)
        self.road_alert_source = np.full(self.n, "", dtype="<U12")
        self.last_road_delay = np.full(self.n, -1e10)
        self.information_review_at = np.full(self.n, -1e10)
        self.peer_relocation_until = np.full(self.n, -1e10)
        self.peer_relocation_route = np.full(self.n, "", dtype="<U12")
        # Transferred observed *closure-response* marginals (Fix I-5, 2008);
        # not an estimated causal effect of message exposure, nor joint distribution.
        self.pref_route_change = r.random(self.n) < .44
        self.pref_time_shift = r.random(self.n) < .48
        self.action_id = 0
        self.actions = {}
        self.actor_pending = defaultdict(set)
        # Operational availability only. No mortality, illness, condemnation, destruction,
        # bankruptcy or unrecorded housing production. Regional absence is NOT death.
        self.household_local = np.ones(self.n, dtype=bool)
        self.hh_outage_hours = np.zeros(self.n, dtype=np.int32)
        self.hh_restored_hours = np.zeros(self.n, dtype=np.int32)
        self.relocation_trigger_h = np.array([relocation_trigger_hours(float(x)) for x in r.uniform(1e-8, 1-1e-8, self.n)])
        self.last_relocation_intention = np.full(self.n, -1e10)
        self.last_relocation_route = np.full(self.n, "main", dtype="<U12")
        self.relocation_pending = np.zeros(self.n, dtype=bool)
        self.return_pending = np.zeros(self.n, dtype=bool)
        self.availability_review_pending = np.zeros(self.n, dtype=bool)
        self.relocation_action_id = np.full(self.n, -1, dtype=np.int64)
        self.return_action_id = np.full(self.n, -1, dtype=np.int64)
        self.rel_location_absence_hours = 0
        # Direct one-day 49% SMB stated shutdown intention, transferred to retailers
        # as a C-level Bernoulli operational *workaround* proxy when site loses grid.
        self.store_workaround = r.random(self.r) >= SMB_SHUTDOWN_1D
        self.store_site_usable = np.ones(self.r, dtype=bool)
        self.store_operational = np.ones(self.r, dtype=bool)
        self.store_cumulative_closed_hours = np.zeros(self.r, dtype=np.int32)
        self.store_rank = r.random(self.r)
        self.store_outage_hours = np.zeros(self.r, dtype=float)
        self.place = np.zeros(self.n, dtype=np.int8)
        self.last_commute_day = np.full(self.n, -1, dtype=np.int32)
        self.last_home_arrival = np.full(self.n, -1e10)
        self.commute_action_id = np.full(self.n, -1, dtype=np.int64)
        self.commute_home_action_id = np.full(self.n, -1, dtype=np.int64)
        self.commute_first_choice_day = np.full(self.n, -1, dtype=np.int32)
        self.commute_informed_seen = np.zeros(self.n, dtype=bool)
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
        heapq.heappush(self.events, (float(when), 0 if kind in ("shock", "restore") else 1, self.seq, kind, payload))

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
        used = self.energy_served_kwh + self.energy_spilled_kwh
        slack = max(1e-6, 1e-10 * abs(self.generation_kwh))
        assert used <= self.generation_kwh + slack, (used, self.generation_kwh)

    def bank_access(self, a: int):
        if a < self.n and not self.household_local[a]:
            return bool(self.internet[a])  # C: outside-region ordinary connectivity boundary
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
        # Intrabank posting is immediate; POS card authorizations settle after one day;
        # other interbank transfers use the NEXT BUSINESS DAY 08:30 proxy.
        if a == b:
            self.call(self.t, "settle", tx)
        elif label in {"retail_sale", "medicine_sale", "wholesale", "utility_bill"}:
            self.call(self.t + 24, "settle", tx)
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

    def road_trip(self, zone: int, units: int, purpose: str, payload: Any, route="main") -> bool:
        if route not in {"main", "alternate"}:
            return False
        hour = int(self.t)
        regional = self.factor_for("road", zone)
        corridor = self.factor_for("road_closure", zone) if route == "main" else 1.
        availability = regional * corridor
        baseline = max(6, int((self.n / self.z) * .42))
        # C-level parallel path proxy, separate capacity/occupancy; a full road
        # shock still affects both routes and zero capacity prevents all movement.
        base_cap = baseline if route == "main" else max(1, int(.35 * baseline))
        cap = max(1, int(base_cap * availability)) if availability > 0 else 0
        if cap == 0:
            self.stats["travel_capacity_rejections"] += units
            self.trace.log(self.t, "mobility", -1, result="blocked", zone=zone,
                           route=route, purpose=purpose, vehicles=units)
            return False
        key = lambda h: (h, zone) if route == "main" else (h, zone, "alternate")
        used = self.road_used[key(hour)]
        if used + units > cap:
            self.stats["travel_capacity_rejections"] += units
            self.trace.log(self.t, "mobility", -1, result="deferred", zone=zone,
                           route=route, purpose=purpose, vehicles=units)
            return False
        ratio = (used + units) / cap
        free_flow = (self.cfg.free_flow_minutes / 60.) * (1.35 if route == "alternate" else 1.)
        travel = free_flow * (1 + .15 * ratio ** 4)
        duration = max(1, math.ceil(travel))
        for h in range(hour, hour + duration):
            if self.road_used[key(h)] + units > cap:
                return False
        for h in range(hour, hour + duration):
            self.road_used[key(h)] += units
        self.stats["vehicle_trips"] += units
        self.stats["travel_minutes_total"] += int(round(units * travel * 60))
        if purpose == "commute_arrival":
            self.stats["morning_commute_minutes_milli"] += int(round(units * travel * 60 * 1000))
            self.stats["morning_commute_trips"] += units
        self.stats["alternate_route_trips" if route == "alternate" else "main_route_trips"] += units
        self.call(self.t + travel, purpose, payload)
        self.trace.log(self.t, "mobility", -1, result="departed", zone=zone,
                       route=route, purpose=purpose, vehicles=units, duration_hours=round(travel, 4))
        return True

    def stock_signal(self, i):
        q = self.query_result.get(i)
        if q and q[1] >= self.t:
            return q[0]
        return None

    def comm_access(self, i):
        return bool(self.internet[i] and (not self.household_local[i] or self.comm_up[int(self.zone[i])]))

    def at_home(self, i: int) -> bool:
        return bool(self.household_local[i] and int(self.place[i]) == PLACE_HOME)

    def at_work(self, i: int) -> bool:
        return bool(self.household_local[i] and int(self.place[i]) == PLACE_AT_WORK)

    def sleep_allows_morning_commute(self, i: int) -> bool:
        last = float(self.last_home_arrival[i])
        if last <= -1e8:
            return True
        return self.t >= last + MIN_SLEEP_AFTER_HOME_HOURS

    def shift_for(self, i: int, day: int) -> bool:
        if self.last_commute_day[i] == day or not self.household_local[i] or not self.employed[i] or self.remote[i]:
            return False
        if day % 7 < 5:
            return True
        job = int(self.job[i])
        return (job < self.r and (i + day) % 3 == 0) or (job in (self.r + 2, self.r + 3) and (i + day) % 4 == 0)

    def obs(self, i):
        zone = int(self.zone[i]); shop = int(self.store_of[i])
        messages = tuple(self.inbox.pop(i, []))
        exposures = {claim: len(src) for claim, src in self.claim_sources.get(i, {}).items()}
        active_ids = set(self.actor_pending.get(i, ()))
        for move_aid, move_pending in ((int(self.relocation_action_id[i]), self.relocation_pending[i]),
                                       (int(self.return_action_id[i]), self.return_pending[i])):
            if move_pending and move_aid in self.actions:
                active_ids.add(move_aid)
        commute_aid = int(self.commute_action_id[i])
        if commute_aid in self.actions:
            active_ids.add(commute_aid)
        commute_home_aid = int(self.commute_home_action_id[i])
        if commute_home_aid in self.actions:
            active_ids.add(commute_home_aid)
        active = tuple(sorted(active_ids))
        relocation_action = self.actions.get(int(self.relocation_action_id[i]))
        return_action = self.actions.get(int(self.return_action_id[i]))
        return Observation(
            participant=i, time=self.t, zone=zone, weekday=int(self.t / 24) % 7,
            locally_present=bool(self.household_local[i]),
            at_home=self.at_home(i),
            at_work=self.at_work(i),
            hours_since_home_arrival=((self.t - self.last_home_arrival[i])
                                      if self.last_home_arrival[i] > -1e8 else None),
            household_size=int(self.hh_size[i]), employed=bool(self.employed[i]), remote_worker=bool(self.remote[i]),
            scheduled_shift=self.shift_for(i, int(self.t // 24)),
            balance_cents=int(self.balance[i]), cash_cents=int(self.cash[i]),
            groceries=float(self.goods[i, 0]), medicines=float(self.goods[i, 1]),
            grocery_need_daily=float(self.need[i]), medical_need_daily=float(self.med_need[i]),
            local_price_cents=int(self.store_price[shop]), medicine_price_cents=self.medicine_price_cents,
            shop_stock_report=self.stock_signal(i),
            power_at_home=(bool(self.power_rank[i] < self.power_ratio[zone]) if self.household_local[i] else None),
            availability_enabled=self.cfg.availability_extension,
            home_outage_hours=int(self.hh_outage_hours[i]),
            home_restored_hours=int(self.hh_restored_hours[i]),
            relocation_preference_threshold_hours=float(self.relocation_trigger_h[i]),
            relocation_pending=bool(self.relocation_pending[i]),
            return_pending=bool(self.return_pending[i]),
            relocation_request_id=(int(self.relocation_action_id[i]) if self.relocation_pending[i] else None),
            return_request_id=(int(self.return_action_id[i]) if self.return_pending[i] else None),
            relocation_request_stage=(relocation_action[2] if relocation_action else ""),
            relocation_request_route=("alternate" if relocation_action and relocation_action[1].target == 1 else "main"),
            return_request_stage=(return_action[2] if return_action else ""),
            return_request_route=("alternate" if return_action and return_action[1].target == 1 else "main"),
            availability_review_pending=bool(self.availability_review_pending[i]),
            comm_access=self.comm_access(i),
            services_report=None, last_stockout_hours_ago=(self.t - self.last_stockout[i]) if self.last_stockout[i] > -1e9 else None,
            last_purchase_hours_ago=(self.t - self.last_purchase[i]) if self.last_purchase[i] > -1e9 else None,
            clinic_pending=i in self.clinic_waiting,
            last_clinic_visit_hours_ago=(self.t - self.last_clinic_visit[i]) if self.last_clinic_visit[i] > -1e9 else None,
            current_claim_exposures=exposures, messages=messages,
            pending_action_ids=active,
            pending_grocery_purchase=any(self.actions[aid][1].kind == "buy" for aid in active if aid in self.actions),
            pending_medicine_purchase=any(self.actions[aid][1].kind == "buy_medicine" for aid in active if aid in self.actions),
            trust=float(self.trust[i]), adoption_threshold=int(self.threshold[i]),
            road_alert=bool(self.road_alert_until[i] >= self.t),
            road_alert_source=(str(self.road_alert_source[i]) if self.road_alert_until[i] >= self.t else ""),
            last_road_delay_hours_ago=(self.t - self.last_road_delay[i] if self.last_road_delay[i] > -1e9 else None),
            commute_route_preference=bool(self.pref_route_change[i]),
            commute_time_preference=bool(self.pref_time_shift[i]),
            pending_commute=any(self.actions[aid][1].kind == "commute" for aid in active if aid in self.actions),
            pending_commute_request_id=(commute_aid if commute_aid in self.actions else None),
            pending_commute_route=(self.actions[commute_aid][1].payload if commute_aid in self.actions else ""),
            pending_commute_home=any(self.actions[aid][1].kind == "commute_home" for aid in active if aid in self.actions),
            pending_commute_home_request_id=(commute_home_aid if commute_home_aid in self.actions else None),
            pending_commute_home_route=(self.actions[commute_home_aid][1].payload
                                        if commute_home_aid in self.actions else ""),
            peer_relocation_route=(str(self.peer_relocation_route[i]) if self.peer_relocation_until[i] >= self.t else ""))

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
            if (action.kind == "relocate" and action.target == 1 and
                    o.peer_relocation_route == "alternate" and not o.commute_route_preference):
                self.stats["peer_coordinated_route_requests"] += 1
            if action.kind == "relocate":
                self.last_relocation_intention[i] = self.t
                self.last_relocation_route[i] = "alternate" if action.target == 1 else "main"
            if action.kind == "commute":
                self.commute_action_id[i] = aid
            if action.kind == "commute_home":
                self.commute_home_action_id[i] = aid
            if action.kind == "commute" and self.commute_first_choice_day[i] != int(self.t // 24):
                self.commute_first_choice_day[i] = int(self.t // 24)
                self.stats["commute_first_choices"] += 1
                if o.road_alert and o.road_alert_source != "firsthand" and not self.commute_informed_seen[i]:
                    self.commute_informed_seen[i] = True
                    self.stats["message_informed_first_commute_choices"] += 1
                    self.stats["message_informed_first_route_choices"] += int(action.payload == "alternate")
                    self.stats["message_informed_first_shift_choices"] += int(action.delay_hours >= 2.5)
            if action.kind == "commute" and o.road_alert:
                self.stats["informed_commute_requests"] += 1
                if action.payload == "alternate": self.stats["informed_route_choices"] += 1
                if action.delay_hours >= 2.5: self.stats["informed_shift_choices"] += 1
            if action.kind == "buy":
                self.last_purchase_intention[i] = self.t
            if action.kind == "review" and self.cfg.availability_extension:
                self.availability_review_pending[i] = True
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
                if not self.at_home(i):
                    valid = False
                else:
                    departed = self.road_trip(zone, 1, "shop_arrival", (aid, i, float(a.amount), good))
                if valid and not departed:
                    deferred = True
                    self.call(self.t + 1, "action_retry", aid)
        elif a.kind == "commute":
            day = int(self.t // 24)
            valid = bool(self.shift_for(i, day) and self.last_commute_day[i] != day
                         and self.at_home(i) and self.sleep_allows_morning_commute(i))
            if valid:
                route = a.payload if a.payload in {"main", "alternate"} else "main"
                departed = self.road_trip(int(self.zone[i]), 1, "commute_arrival", (aid, i, day), route=route)
                if departed:
                    self.place[i] = PLACE_TO_WORK
                    self.last_commute_day[i] = day
                else:
                    self.last_road_delay[i] = self.t  # personal failed departure, not inferred closure
                    self.road_alert_until[i] = max(self.road_alert_until[i], self.t + 4)
                    self.road_alert_source[i] = "firsthand"
                    self.call(self.t + .1, "information_review", i)
                    deferred = True
                    self.call(self.t + 1, "commute_retry", (aid, i, day))
        elif a.kind == "commute_home":
            valid = int(self.place[i]) == PLACE_AT_WORK and self.commute_home_action_id[i] == aid
            if valid:
                route = a.payload if a.payload in {"main", "alternate"} else "main"
                departed = self.road_trip(int(self.zone[i]), 1, "commute_home_arrival", (aid, i), route=route)
                if departed:
                    self.place[i] = PLACE_TO_HOME
                else:
                    self.last_road_delay[i] = self.t
                    self.road_alert_until[i] = max(self.road_alert_until[i], self.t + 4)
                    self.road_alert_source[i] = "firsthand"
                    deferred = True
                    self.call(self.t + 1, "commute_home_retry", (aid, i))
        elif a.kind == "query":
            valid = a.payload == "store_stock" and self.comm_access(i)
            if valid:
                self.call(self.t + self.rng.uniform(.05, .5), "query_result", (aid, i))
        elif a.kind == "send":
            zone = int(self.zone[i]); valid = self.comm_access(i)
            if a.payload == "power_interruption":
                valid &= bool(self.household_local[i]) and self.power_rank[i] >= self.power_ratio[zone]
            elif a.payload == "retail_stockout":
                valid &= self.t - self.last_stockout[i] <= 24
            elif a.payload == "road_delay":
                valid &= self.t - self.last_road_delay[i] <= 4
            else:
                valid = False
            if valid:
                self.send(i, f"road_delay:{zone}" if a.payload == "road_delay" else a.payload, "firsthand", i, 0, "all")
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
                if a.payload == "relocate":
                    valid &= 0 <= self.t - self.last_relocation_intention[i] <= 6
                    route = str(self.last_relocation_route[i])
                    if valid: self.send(i, f"relocation_intent:{int(self.zone[i])}:{route}", "firsthand_intention", i, 0, "all")
                else:
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
        elif a.kind == "relocate":
            valid = bool(self.cfg.availability_extension and self.household_local[i] and
                         not self.relocation_pending[i] and not self.return_pending[i] and
                         a.payload in {"", "while_unpowered"} and
                         (a.payload != "while_unpowered" or self.hh_outage_hours[i] > 0))
            if valid:
                self.relocation_pending[i] = True
                self.relocation_action_id[i] = aid
                self.trace.log(self.t, "availability", i, category="person", transition="relocation_intended",
                               outage_hours=int(self.hh_outage_hours[i]), target="outside_region",
                               requested_by="participant_policy", action_id=aid)
                self.call(self.t + self.rng.uniform(.1, .4), "relocation_depart", i)
        elif a.kind == "return":
            valid = bool(self.cfg.availability_extension and not self.household_local[i] and
                         not self.return_pending[i] and not self.relocation_pending[i])
            if valid:
                self.return_pending[i] = True
                self.return_action_id[i] = aid
                self.call(self.t + self.rng.uniform(.1, .4), "return_depart", i)
        elif a.kind == "review":
            valid = bool(self.cfg.availability_extension and .01 <= a.delay_hours <= 337)
            self.availability_review_pending[i] = False
            if valid:
                self.call(self.t, "availability_review", i)
        elif a.kind == "clinic":
            valid = bool(self.at_home(i)) and i not in self.clinic_waiting and self.t - self.last_clinic_visit[i] > 14 * 24
            if valid:
                self.clinic_queue.append((i, self.t))
                self.clinic_waiting.add(i)
        elif a.kind == "schedule":
            valid = .01 <= a.delay_hours <= 168 and a.payload in {"buy", "buy_medicine", "clinic", "query"}
            if valid:
                self.call(self.t + a.delay_hours, "scheduled_intent", (i, Action(a.payload, amount=a.amount)))
        elif a.kind == "cancel":
            old = self.actions.get(a.reference)
            valid = bool(old and old[0] == i and
                         (old[2] == "requested" or
                          (old[2] in {"accepted", "deferred"} and old[1].kind in {"relocate", "return", "commute", "commute_home"})))
            if valid:
                if old[1].kind == "relocate": self.relocation_pending[i] = False
                if old[1].kind == "return": self.return_pending[i] = False
                if old[1].kind == "commute" and self.commute_action_id[i] == a.reference: self.commute_action_id[i] = -1
                if old[1].kind == "commute_home" and self.commute_home_action_id[i] == a.reference:
                    self.commute_home_action_id[i] = -1
                if old[1].kind == "review": self.availability_review_pending[i] = False
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
        stage = "deferred" if deferred else (("accepted" if a.kind in {"relocate", "return"} else "executed") if valid else "rejected")
        self.actions[aid] = (i, a, stage)
        if valid:
            self.trace.log(self.t, "action", i, id=aid, kind=a.kind, stage="accepted")
        if stage != "accepted":
            self.trace.log(self.t, "action", i, id=aid, kind=a.kind, stage=stage)
        if not valid:
            if a.kind == "commute" and self.commute_action_id[i] == aid:
                self.commute_action_id[i] = -1
            if a.kind == "commute_home" and self.commute_home_action_id[i] == aid:
                self.commute_home_action_id[i] = -1
            self.stats["actions_rejected"] += 1
        elif not deferred and a.kind not in {"buy", "buy_medicine", "commute", "commute_home", "query", "relocate", "return"}:
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
        key = (zone, claim)
        if self.t - self.last_notice.get(key, -1e10) < 24:
            return
        self.last_notice[key] = self.t
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
        channel_available = bool((not self.household_local[i] or self.comm_up[int(self.zone[i])]) and
                                 (self.news_access[i] if layer == "news" else self.internet[i]))
        if not channel_available or self.rng.random() > float(self.attention[i]):
            self.stats["messages_not_received"] += 1
            return
        m = self.messages.get(mid)
        if m is None:
            return
        visible = layer != "online"
        credibility = 1. if layer == "official" else (.8 if layer == "news" else float(self.trust[i]))
        view = MessageView(mid, m["origin"], m["sender"], m["created"], m["claim"], m["evidence"],
                           layer, credibility, visible)
        self.inbox[i].append(view)
        if m["claim"].startswith(("road_closure:", "road_disruption:", "road_delay:")):
            try: relevant = int(m["claim"].split(":", 1)[1]) == int(self.zone[i])
            except (ValueError, IndexError): relevant = False
            if relevant and m["evidence"] in {"firsthand", "institutional_announcement"}:
                still_official = self.road_alert_source[i] == "official" and self.road_alert_until[i] >= self.t
                self.road_alert_until[i] = max(self.road_alert_until[i], self.t + 24)
                self.road_alert_source[i] = "official" if m["evidence"] == "institutional_announcement" or still_official else "peer"
                self.stats["road_alerts_received"] += 1
                self.trace.log(self.t, "information", i, road_alert=m["claim"], provenance=m["evidence"])
                # The message merely offers a review opportunity. Only the
                # participant policy can choose travel or relocation actions.
                commute_relevant = self.shift_for(i, int(self.t // 24)) and 3 <= self.t % 24 < 10
                move_relevant = self.relocation_pending[i] or self.return_pending[i]
                if (commute_relevant or move_relevant) and self.information_review_at[i] < self.t - .01:
                    at = self.t + (max(.1, 5.6 - self.t % 24) if commute_relevant and self.t % 24 < 5.5 else .1)
                    self.information_review_at[i] = at
                    self.call(at, "information_review", i)
        elif m["claim"].startswith("road_reopened:") and m["evidence"] == "institutional_announcement":
            try: relevant = int(m["claim"].split(":", 1)[1]) == int(self.zone[i])
            except (ValueError, IndexError): relevant = False
            if relevant:
                self.road_alert_until[i] = -1e10
                self.road_alert_source[i] = ""
        if (m["claim"].startswith("relocation_intent:") and
                m["evidence"] == "firsthand_intention" and m["sender"] == m["origin"] and
                layer in {"close", "workplace"}):
            parts = m["claim"].split(":")
            if len(parts) == 3 and parts[1].isdigit() and int(parts[1]) == int(self.zone[i]) and parts[2] in {"main", "alternate"}:
                self.peer_relocation_until[i] = self.t + 6
                self.peer_relocation_route[i] = parts[2]
                self.stats["peer_relocation_plans_received"] += 1
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
            if a.kind == "commute" and self.commute_action_id[i] == aid:
                self.commute_action_id[i] = -1
            if a.kind == "commute_home" and self.commute_home_action_id[i] == aid:
                self.commute_home_action_id[i] = -1
            self.trace.log(self.t, "action", i, id=aid, kind=a.kind, stage="completed")

    def shop_arrival(self, payload):
        aid, i, demand, good = payload
        store = int(self.store_of[i]); account = self.n + store; zone = int(self.store_zone[store])
        if not self.at_home(i):
            self.trace.log(self.t, "action", i, id=aid, stage="failed", reason="not_at_home")
            self.complete(aid)
            return
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
            ("power_to_retail" not in self.disabled and not (self.store_rank[store] < self.power_ratio[zone] or (self.cfg.availability_extension and self.store_workaround[store])))):
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
        purchase = self.actions.get(aid)
        electronic_only = bool(purchase and purchase[1].payload == "electronic_only")
        tx = self.transfer(i, account, bill, "retail_sale" if good == 0 else "medicine_sale")
        if tx is None and not electronic_only and self.cash[i] >= bill:
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
        if not self.household_local[i]:
            self.complete(aid)
            return
        employer = int(self.job[i])
        account = self.n + employer if employer < self.r else [self.wh, self.supplier, self.utility, self.clinic][employer - self.r]
        self.place[i] = PLACE_AT_WORK
        self.attended[account] += 1
        self.stats["completed_commutes"] += 1
        self.complete(aid)

    def commute_home_arrival(self, payload):
        aid, i = payload
        if not self.household_local[i]:
            self.complete(aid)
            return
        self.place[i] = PLACE_HOME
        self.last_home_arrival[i] = self.t
        self.stats["completed_commute_home"] += 1
        self.complete(aid)
        self.call(self.t + .01, "decide", i)

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
        served = min(float(critical_served.sum() + available_noncritical.sum()), supply)
        self.home_demand_kwh += float(homes.sum())
        self.home_served_kwh += float((available_noncritical * homes / (homes + commercial)).sum())
        # Fixed household power ranks provide a transparent account-level outage proxy.
        # These are NOT geographic feeder assignments; use only with a separately
        # documented population/utility-account expansion assumption.
        unserved_households = int(np.count_nonzero(self.power_rank >= self.power_ratio[self.zone]))
        self.power_unserved_households_last = unserved_households
        self.power_unserved_households_peak = max(self.power_unserved_households_peak, unserved_households)
        self.power_unserved_household_hours += unserved_households
        self.power_hourly.append((round(float(self.t), 5), unserved_households, round(float(self.power_ratio.mean()), 6)))
        self.generation_kwh += supply
        self.energy_served_kwh += served
        self.energy_spilled_kwh = max(0., self.generation_kwh - self.energy_served_kwh)
        self.energy_unserved_kwh += max(0., float(demand.sum() - served))
        if self.cfg.availability_extension:
            self.availability_power_tick()
        # Refrigeration continuity: tiny explicitly accounted-for loss after sustained
        # store power failure. Rate and four-hour duration are C assumptions.
        if "power_to_retail" not in self.disabled:
            for store in range(self.r):
                z = int(self.store_zone[store])
                powered = self.store_rank[store] < self.power_ratio[z]
                self.store_outage_hours[store] = 0. if powered else self.store_outage_hours[store] + 1
                if self.store_outage_hours[store] > 4:
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

    def availability_power_tick(self):
        # The engine observes service changes and provides decision opportunities;
        # only a participant policy may REQUEST a move or return. Other policies
        # may ignore these observations entirely or choose alternative actions.
        powered = self.power_rank < self.power_ratio[self.zone]
        newly_interrupted = self.household_local & ~powered & (self.hh_outage_hours == 0)
        restored_away = ~self.household_local & powered & (self.hh_restored_hours == 0)
        six_hour_restoration = ~self.household_local & powered & (self.hh_restored_hours == 5)
        self.hh_outage_hours[:] = np.where(powered, 0, self.hh_outage_hours + 1)
        self.hh_restored_hours[:] = np.where(powered, self.hh_restored_hours + 1, 0)
        for i in np.flatnonzero(newly_interrupted | restored_away | six_hour_restoration):
            self.call(self.t + .01 + self.rng.uniform(0, .03), "decide", int(i))
        for store in range(self.r):
            z = int(self.store_zone[store])
            site = bool(self.store_rank[store] < self.power_ratio[z])
            operating = site or bool(self.store_workaround[store])
            if site != self.store_site_usable[store] or operating != self.store_operational[store]:
                self.trace.log(self.t, "availability", -1, category="business_site", store=store,
                               zone=z, grid_service=site, firm_operational=operating,
                               workaround=bool(self.store_workaround[store]))
            self.store_site_usable[store] = site
            self.store_operational[store] = operating
            self.store_cumulative_closed_hours[store] += int(not operating)

    def relocation_depart(self, i):
        aid = int(self.relocation_action_id[i])
        if not self.household_local[i] or not self.relocation_pending[i]:
            return
        # Participant may make its intention conditional on continuing outage.
        # Alternative policies may submit unconditional relocation requests.
        action = self.actions.get(aid)
        if action is None or action[2] in {"cancelled", "expired", "rejected"}:
            self.relocation_pending[i] = False
            return
        if action[1].payload == "while_unpowered" and self.hh_outage_hours[i] == 0:
            self.relocation_pending[i] = False
            self.actions[aid] = (i, action[1], "expired")
            self.trace.log(self.t, "action", i, id=aid, kind="relocate", stage="expired", reason="condition_no_longer_holds")
            return
        # Actual physical road capacity gates the requested departure. A policy
        # may cancel a deferred attempt before it starts moving.
        move = self.actions.get(aid)
        route = "alternate" if move and move[1].target == 1 else "main"
        if not self.road_trip(int(self.zone[i]), 1, "relocation_arrival", i, route=route):
            self.stats["relocation_transport_deferred"] += 1
            if aid in self.actions:
                self.actions[aid] = (i, self.actions[aid][1], "deferred")
                self.trace.log(self.t, "action", i, id=aid, kind="relocate", stage="deferred")
            self.call(self.t + 1, "relocation_depart", i)
        elif aid in self.actions:
            self.actions[aid] = (i, self.actions[aid][1], "executed")
            self.trace.log(self.t, "action", i, id=aid, kind="relocate", stage="executed")

    def relocation_arrival(self, i):
        if self.household_local[i] and self.relocation_pending[i]:
            self.household_local[i] = False
            self.relocation_pending[i] = False
            self.stats["relocation_completed"] += 1
            self.trace.log(self.t, "availability", i, category="person", transition="outside_region",
                           interpretation="temporarily absent from local modeled roles; no health outcome")
            self.complete(int(self.relocation_action_id[i]))

    def return_depart(self, i):
        aid = int(self.return_action_id[i])
        if self.household_local[i] or not self.return_pending[i]:
            return
        action = self.actions.get(aid)
        if action is None or action[2] in {"cancelled", "expired", "rejected"}:
            self.return_pending[i] = False
            return
        move = self.actions.get(aid)
        route = "alternate" if move and move[1].target == 1 else "main"
        if not self.road_trip(int(self.zone[i]), 1, "return_arrival", i, route=route):
            self.stats["return_transport_deferred"] += 1
            if aid in self.actions:
                self.actions[aid] = (i, self.actions[aid][1], "deferred")
                self.trace.log(self.t, "action", i, id=aid, kind="return", stage="deferred")
            self.call(self.t + 1, "return_depart", i)
        elif aid in self.actions:
            self.actions[aid] = (i, self.actions[aid][1], "executed")
            self.trace.log(self.t, "action", i, id=aid, kind="return", stage="executed")

    def return_arrival(self, i):
        if not self.household_local[i] and self.return_pending[i]:
            self.household_local[i] = True
            self.place[i] = PLACE_HOME
            self.return_pending[i] = False
            self.hh_outage_hours[i] = 0
            self.stats["relocation_returned"] += 1
            self.trace.log(self.t, "availability", i, category="person", transition="returned_local")
            self.complete(int(self.return_action_id[i]))

    def services(self):
        # Only continuity/capacity; no individual clinical outcomes are inferred.
        if "power_to_services" in self.disabled:
            clinic_factor = 1.
        else:
            clinic_factor = float(self.critical_ratio[0])
        workforce = max(.5, min(1., self.attended[self.clinic] / max(1, int(self.n * .001))))
        clinic_factor *= workforce * min(1., self.factor_for("services", 0))
        water_need = self.n * .61 / 24  # ~64.6 gpcd indoor × ~2.5 persons, EPA planning benchmark
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
                if not self.household_local[i]:
                    self.clinic_queue.append((i, requested_at))
                    continue
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
        if self.cfg.availability_extension:
            self.stats["outside_region_grocery_need_milli"] += int(round(float(needs[~self.household_local].sum()) * 1000))
            needs[~self.household_local] = 0.  # outside-region requirements not claimed supplied
            self.rel_location_absence_hours += int((~self.household_local).sum()) * 24
        used = np.minimum(self.goods[:self.n, 0], needs)
        self.goods[:self.n, 0] -= used
        self.consumed[0] += used.sum()
        self.stats["unmet_grocery_milli"] += int(round(float((needs - used).sum()) * 1000))
        med = self.med_need.astype(np.float64)
        if self.cfg.availability_extension:
            self.stats["outside_region_medicine_need_milli"] += int(round(float(med[~self.household_local].sum()) * 1000))
            med[~self.household_local] = 0.
        meds_used = np.minimum(self.goods[:self.n, 1], med)
        self.goods[:self.n, 1] -= meds_used
        self.consumed[1] += meds_used.sum()
        self.stats["unmet_medicine_milli"] += int(round(float((med - meds_used).sum()) * 1000))
        # Daily electricity bill and utility salaries/municipal service transfers are real debits.
        for i in range(self.n):
            if self.balance[i] >= 460:  # ~$4.60/day order-of-magnitude residential electric bill proxy
                self.transfer(i, self.utility, 460, "utility_bill")
        if self.balance[self.utility] >= self.n * 100:
            self.transfer(self.utility, self.gov, self.n * 100, "utility_contract")
        self.attended[:] = 0
        self.actions = {aid: item for aid, item in self.actions.items() if item[2] in {"requested", "accepted", "deferred", "executed"} and (item[1].kind in {"buy", "buy_medicine", "commute", "commute_home", "query", "schedule", "relocate", "return"} or item[2] == "requested")}
        # Drop delivered traffic after the forward/receipt window. Unbounded
        # message dicts (each with a recipient set) grow linearly in n × days.
        cutoff = self.t - 48
        self.messages = {mid: m for mid, m in self.messages.items() if m["created"] >= cutoff}
        expired = [i for i, q in self.query_result.items() if q[1] < self.t]
        for i in expired:
            self.query_result.pop(i, None)
        if self.cfg.invariant_every_day:
            self.invariants()
        row = self.snapshot()
        self.metrics.append(row)
        self.trace.log(self.t, "state", -1, **row)
        self.road_used = defaultdict(int, {key: count for key, count in self.road_used.items() if key[0] >= int(self.t) - 2})
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
                    commute_first_choices=int(self.stats["commute_first_choices"]),
                    message_informed_first_commute_choices=int(self.stats["message_informed_first_commute_choices"]),
                    message_informed_first_route_choices=int(self.stats["message_informed_first_route_choices"]),
                    message_informed_first_shift_choices=int(self.stats["message_informed_first_shift_choices"]),
                    informed_commute_requests=int(self.stats["informed_commute_requests"]),
                    informed_route_choices=int(self.stats["informed_route_choices"]),
                    informed_shift_choices=int(self.stats["informed_shift_choices"]),
                    road_alerts_received=int(self.stats["road_alerts_received"]),
                    alternate_route_trips=int(self.stats["alternate_route_trips"]),
                    peer_relocation_plans_received=int(self.stats["peer_relocation_plans_received"]),
                    peer_coordinated_route_requests=int(self.stats["peer_coordinated_route_requests"]),
                    sales_units=float(self.stats["grocery_sales_units_milli"] / 1000),
                    mean_power_service=float(self.power_ratio.mean()),
                    energy_served_kwh=round(self.energy_served_kwh, 3),
                    energy_unserved_kwh=round(self.energy_unserved_kwh, 3),
                    residential_kwh_per_household_day=round(self.home_demand_kwh / self.n / max(1e-6, self.t/24), 3),
                    residential_served_kwh_per_household_day=round(self.home_served_kwh / self.n / max(1e-6, self.t/24), 3),
                    mean_travel_minutes=round(self.stats["travel_minutes_total"] / max(1, self.stats["vehicle_trips"]), 3),
                    mean_morning_commute_minutes=round(
                        self.stats["morning_commute_minutes_milli"] / max(1, self.stats["morning_commute_trips"]) / 1000, 3),
                    completed_commute_home=int(self.stats["completed_commute_home"]),
                    interrupted_feeder_hours=int(self.stats["interrupted_feeder_hours"]),
                    power_unserved_households_peak=int(self.power_unserved_households_peak),
                    power_unserved_households_last=int(self.power_unserved_households_last),
                    power_unserved_household_hours=int(self.power_unserved_household_hours),
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
                    people_locally_present=int(self.household_local.sum()),
                    people_temporarily_away=int((~self.household_local).sum()),
                    relocation_completed=int(self.stats["relocation_completed"]),
                    relocation_returned=int(self.stats["relocation_returned"]),
                    relocation_transport_deferred=int(self.stats["relocation_transport_deferred"]),
                    outside_region_grocery_requirement_units=float(self.stats["outside_region_grocery_need_milli"] / 1000),
                    outside_region_medicine_requirement_units=float(self.stats["outside_region_medicine_need_milli"] / 1000),
                    normal_grid_site_access=int(self.store_site_usable.sum()),
                    firms_power_operable=int(self.store_operational.sum()),
                    firm_power_closed_hours=int(self.store_cumulative_closed_hours.sum()),
                    shop_power_closures=int(self.stats["shop_power_closed"]),
                    shop_understaffed=int(self.stats["shop_understaffed"]),
                    unpaid_payroll=int(self.stats["unpaid_payroll"]))

    def shock(self, s: Shock):
        self.factor_seq += 1
        sid = self.factor_seq
        self.factor[(s.domain, s.zone, sid)] = s.multiplier
        self.call(self.t + s.duration_hours, "restore", (s.domain, s.zone, sid))
        if s.domain in {"road_closure", "road"}:
            for z in (range(self.z) if s.zone == -1 else [s.zone]):
                self.announce(z, f"{'road_closure' if s.domain == 'road_closure' and s.multiplier == 0 else 'road_disruption'}:{z}")
        self.trace.log(self.t, "shock", -1, **asdict(s), stage="introduced", id=sid)

    def run(self):
        horizon = self.cfg.days * 24
        try:
            while self.events and self.events[0][0] <= horizon:
                t, _, _, kind, payload = heapq.heappop(self.events)
                self.t = t
                if kind == "decide": self.decide(payload)
                elif kind == "availability_review":
                    self.availability_review_pending[payload] = False
                    self.decide(payload)
                elif kind == "information_review":
                    self.information_review_at[payload] = -1e10
                    self.decide(payload)
                elif kind == "action": self.action(payload)
                elif kind == "action_retry":
                    if payload in self.actions:
                        i, a, stage = self.actions[payload]
                        if stage == "deferred" and a.kind in {"buy", "buy_medicine"} and self.at_home(i):
                            if not self.road_trip(int(self.zone[i]), 1, "shop_arrival", (payload, i, float(a.amount), 0 if a.kind == "buy" else 1)):
                                self.call(self.t + 1, "action_retry", payload)
                            else:
                                self.actions[payload] = (i, a, "executed")
                elif kind == "commute_retry":
                    aid, i, day = payload
                    if (aid in self.actions and self.actions[aid][2] == "deferred" and int(self.t // 24) == day
                            and self.household_local[i] and self.at_home(i) and self.sleep_allows_morning_commute(i)):
                        route = (self.actions[aid][1].payload if self.actions[aid][1].payload in {"main", "alternate"}
                                 else "main")
                        if self.road_trip(int(self.zone[i]), 1, "commute_arrival", (aid, i, day), route=route):
                            self.place[i] = PLACE_TO_WORK
                            self.actions[aid] = (i, self.actions[aid][1], "executed")
                            self.last_commute_day[i] = day
                        else:
                            self.last_road_delay[i] = self.t
                            self.call(self.t + 1, "commute_retry", payload)
                elif kind == "commute_home_retry":
                    aid, i = payload
                    if (aid in self.actions and self.actions[aid][2] == "deferred"
                            and int(self.place[i]) in {PLACE_AT_WORK, PLACE_TO_HOME} and self.household_local[i]):
                        route = (self.actions[aid][1].payload if self.actions[aid][1].payload in {"main", "alternate"}
                                 else "main")
                        if self.road_trip(int(self.zone[i]), 1, "commute_home_arrival", (aid, i), route=route):
                            self.place[i] = PLACE_TO_HOME
                            self.actions[aid] = (i, self.actions[aid][1], "executed")
                        else:
                            self.last_road_delay[i] = self.t
                            self.call(self.t + 1, "commute_home_retry", payload)
                elif kind == "shop_arrival": self.shop_arrival(payload)
                elif kind == "commute_arrival": self.commute_arrival(payload)
                elif kind == "commute_home_arrival": self.commute_home_arrival(payload)
                elif kind == "relocation_depart": self.relocation_depart(payload)
                elif kind == "relocation_arrival": self.relocation_arrival(payload)
                elif kind == "return_depart": self.return_depart(payload)
                elif kind == "return_arrival": self.return_arrival(payload)
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
                    if payload[0] in {"road_closure", "road"}:
                        for z in (range(self.z) if payload[1] == -1 else [payload[1]]):
                            if (self.factor_for("road", z) >= 1 and self.factor_for("road_closure", z) >= 1):
                                self.announce(z, f"road_reopened:{z}")
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
