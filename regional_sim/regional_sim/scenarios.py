"""Prespecified illustrative scenario sampling, without an engineered event narrative."""
from dataclasses import dataclass, asdict
import random

DOMAINS = ("power", "road", "communication", "supply", "payments", "demand", "retail", "services")

@dataclass(frozen=True)
class Shock:
    at_hour: float
    domain: str
    zone: int  # -1 means region-wide
    multiplier: float
    duration_hours: float

    def validate(self, zones: int):
        if self.domain not in DOMAINS or not (-1 <= self.zone < zones):
            raise ValueError("invalid shock target")
        if self.at_hour < 0 or self.duration_hours <= 0 or not 0 <= self.multiplier <= 3:
            raise ValueError("invalid shock time/severity")


def generate(kind: str, days: int, zones: int, seed: int) -> list[Shock]:
    if kind not in {"routine", "seasonal", "moderate", "severe"}:
        raise ValueError(kind)
    rng = random.Random(seed + 10543)
    if kind in ("routine", "seasonal") or days < 2:
        return []
    # Ranges and event probabilities are C-level placeholders: not empirical hazard distributions.
    domain = rng.choice(DOMAINS)
    zone = rng.randrange(zones) if rng.random() < .7 else -1
    at = rng.uniform(12, max(13, 24 * days * .6))
    if kind == "moderate":
        factor, duration = rng.uniform(.65, .9), rng.uniform(4, 24)
    else:
        factor, duration = rng.uniform(.25, .6), rng.uniform(24, 96)
    return [Shock(at, domain, zone, factor, duration)]
