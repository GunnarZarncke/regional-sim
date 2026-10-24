"""Evidence-anchored availability proxies; never morbidity, death or structural damage.

An Illinois customer stated-response survey (Sue Wing et al., Nature Communications,
2025) reports 33%/83% temporary relocation intent for 1-/14-day blackouts and
49% shutdown intent for SMBs facing a 1-day outage. Treat transfer to Columbus,
conversion of intended action to executed action, within-window interpolation,
and retail-sector transfer as C-level extrapolations. Not historical observed
closure or evacuation frequencies, and not a universal threshold.
"""
import math

RELOCATION_1D = .33
RELOCATION_14D = .83
SMB_SHUTDOWN_1D = .49

# Only the 24 h and 336 h *survey scenario* proportions are observed. Linear
# interpolation before 24 h and a conditional exponential between anchors are
# C-level modelling choices. Beyond day 14 no preference data: cap at 83% instead
# of assuming everyone inevitably leaves. This is NOT a health or safety cutoff.
BETWEEN_ANCHORS_HAZARD = math.log((1 - RELOCATION_1D) / (1 - RELOCATION_14D)) / (13 * 24)


def relocation_probability(hours: float) -> float:
    if hours <= 0:
        return 0.
    if hours <= 24:
        return RELOCATION_1D * hours / 24.
    if hours >= 14 * 24:
        return RELOCATION_14D
    return 1 - (1 - RELOCATION_1D) * math.exp(-BETWEEN_ANCHORS_HAZARD * (hours - 24))


def relocation_trigger_hours(quantile: float) -> float:
    if not 0 < quantile < 1:
        raise ValueError("quantile must be strictly between zero and one")
    if quantile >= RELOCATION_14D:
        return math.inf  # no supported departure threshold beyond observation horizon
    if quantile <= RELOCATION_1D:
        return 24 * quantile / RELOCATION_1D
    return 24 + math.log((1 - RELOCATION_1D) / (1 - quantile)) / BETWEEN_ANCHORS_HAZARD
