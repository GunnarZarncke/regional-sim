"""The sole information/action interface supplied to participant policies."""
from dataclasses import dataclass, field
from typing import Protocol, Tuple, Mapping, Any
import random
import math

@dataclass(frozen=True)
class MessageView:
    id: int
    origin: int
    sender: int
    created: float
    claim: str
    evidence: str
    channel: str
    credibility: float
    source_visible: bool

@dataclass(frozen=True)
class Observation:
    participant: int
    time: float
    zone: int
    weekday: int
    household_size: int
    locally_present: bool
    employed: bool
    remote_worker: bool
    scheduled_shift: bool
    balance_cents: int
    cash_cents: int
    groceries: float
    medicines: float
    grocery_need_daily: float
    medical_need_daily: float
    local_price_cents: int
    medicine_price_cents: int
    shop_stock_report: float | None
    power_at_home: bool | None
    availability_enabled: bool
    home_outage_hours: int
    home_restored_hours: int
    relocation_preference_threshold_hours: float
    relocation_pending: bool
    return_pending: bool
    relocation_request_id: int | None
    return_request_id: int | None
    availability_review_pending: bool
    comm_access: bool
    services_report: str | None
    last_stockout_hours_ago: float | None
    last_purchase_hours_ago: float | None
    clinic_pending: bool
    last_clinic_visit_hours_ago: float | None
    current_claim_exposures: Mapping[str, int]
    messages: Tuple[MessageView, ...]
    pending_action_ids: Tuple[int, ...]
    pending_grocery_purchase: bool
    pending_medicine_purchase: bool
    trust: float
    adoption_threshold: int

@dataclass(frozen=True)
class Action:
    kind: str
    amount: float = 0.0
    target: int = -1
    payload: str = ""
    delay_hours: float = 0.0
    reference: int = -1

class Policy(Protocol):
    def decide(self, observation: Observation, rng: random.Random) -> list[Action]: ...

class ScriptedPolicy:
    """Illustrative, explicitly C-level household heuristic; no privileged world access."""
    def decide(self, o: Observation, rng: random.Random) -> list[Action]:
        actions: list[Action] = []
        # Relocation is a policy choice, not an automatic world-state transition.
        # This *individual* synthetic threshold is drawn from the two survey
        # stated-response anchors. The policy sees only its own outage history.
        # No unsupported causal effect of other people's messages on relocation
        # is assumed. Other policies may use received messages differently.
        if o.availability_enabled:
            if (o.locally_present and not o.relocation_pending and
                    o.home_outage_hours > 0 and
                    o.home_outage_hours >= o.relocation_preference_threshold_hours):
                actions.append(Action("relocate", payload="while_unpowered"))
            elif (o.locally_present and not o.relocation_pending and
                  o.home_outage_hours > 0 and not o.availability_review_pending and
                  math.isfinite(o.relocation_preference_threshold_hours) and
                  o.home_outage_hours < o.relocation_preference_threshold_hours):
                # Request a future observation at the next power tick that will
                # pass the participant's threshold; no global hourly decision loop.
                future = math.ceil(o.relocation_preference_threshold_hours) - o.home_outage_hours
                if future > 0:
                    actions.append(Action("review", delay_hours=float(future) + .05))
            if (not o.locally_present and not o.return_pending and
                    o.home_restored_hours >= 6):
                actions.append(Action("return"))  # Six hours is a C-level heuristic.
        reinforced = o.current_claim_exposures.get("retail_stockout", 0) >= o.adoption_threshold
        desired = o.grocery_need_daily * (4.0 if reinforced else 2.5)
        opening_delay = (rng.uniform(.1, .65) if 8 <= o.time % 24 <= 20.5
                         else (8 - o.time % 24) % 24 + rng.uniform(.05, .45))
        if o.locally_present and not o.pending_grocery_purchase and o.groceries < desired and o.balance_cents + o.cash_cents >= o.local_price_cents:
            affordable = (o.balance_cents + o.cash_cents) // max(1, o.local_price_cents)
            amount = min(max(0, desired - o.groceries), 6.0, affordable)
            if amount >= .25:
                actions.append(Action("buy", amount=round(amount, 2), delay_hours=opening_delay))
        if o.locally_present and not o.pending_medicine_purchase and o.medical_need_daily and o.medicines < o.medical_need_daily * 3 and o.balance_cents + o.cash_cents >= o.medicine_price_cents:
            med_quantity = min(max(0., o.medical_need_daily * 7 - o.medicines), .8,
                               (o.balance_cents + o.cash_cents) / o.medicine_price_cents)
            if med_quantity >= .05:
                actions.append(Action("buy_medicine", amount=round(med_quantity, 3), delay_hours=opening_delay))
        if o.scheduled_shift and 5.5 <= o.time % 24 <= 10.5:
            actions.append(Action("commute", delay_hours=rng.uniform(.05, .65)))
        if rng.random() < .05 and o.comm_access:
            actions.append(Action("query", payload="store_stock"))
        if o.locally_present and not o.power_at_home and o.comm_access and rng.random() < .16:
            actions.append(Action("send", payload="power_interruption"))
        if o.last_stockout_hours_ago is not None and o.last_stockout_hours_ago < 24 and o.comm_access and rng.random() < .32:
            actions.append(Action("send", payload="retail_stockout"))
        for m in o.messages[:3]:
            if o.comm_access and rng.random() < .05 * o.trust and m.evidence != "opinion":
                actions.append(Action("forward", reference=m.id))
        if o.comm_access and o.last_purchase_hours_ago is not None and o.last_purchase_hours_ago < 24 and rng.random() < .08:
            actions.append(Action("completed_message", payload="buy"))
        if o.comm_access and rng.random() < .008:
            actions.append(Action("ask", payload="retail_stockout"))
        visit_hazard = .002 + (.005 if o.medical_need_daily else 0.)
        if o.locally_present and not o.clinic_pending and (o.last_clinic_visit_hours_ago is None or o.last_clinic_visit_hours_ago > 14 * 24) and rng.random() < visit_hazard:
            actions.append(Action("clinic"))
        if not actions:
            actions.append(Action("none"))
        return actions
