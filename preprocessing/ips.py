"""Inverse propensity scoring helpers for click-based signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .bias_correction import PositionBiasCorrector
from .time_decay import DEFAULT_DECAY_HOURS, decay_weight

EPSILON = 1e-6


@dataclass(frozen=True)
class ImpressionEvent:
    """Single impression log with position, clicks, and optional extra data."""

    position: int
    clicks: float
    impressions: float | None = None
    timestamp: str | datetime | None = None


def corrected_clicks(
    events: Iterable[ImpressionEvent],
    bias_corrector: PositionBiasCorrector,
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
    epsilon: float = EPSILON,
) -> float:
    """Return ``Σ(click_i / p(pos_i) * w_t)`` for the provided events."""

    reference = now or datetime.now(timezone.utc)
    total = 0.0
    for event in events:
        if event.clicks <= 0:
            continue
        propensity = max(
            epsilon,
            bias_corrector.position_probability(event.position),
        )
        event_ts = (
            event.timestamp if event.timestamp is not None else reference
        )
        weight = decay_weight(event_ts, now=reference, tau_hours=tau_hours)
        total += float(event.clicks) * weight / propensity
    return total
