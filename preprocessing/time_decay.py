"""Time-decay weighting helpers for click-based signals."""

from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from typing import Iterable, Sequence

DEFAULT_DECAY_HOURS = 24 * 7
MIN_TAU = 1e-6


def _ensure_datetime(value: str | datetime) -> datetime:
    """Return a timezone-aware datetime in UTC."""

    if isinstance(value, datetime):
        dt = value
    else:
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def decay_weight(
    timestamp: str | datetime,
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
) -> float:
    """Return ``exp(-Δt/τ)`` for the provided timestamp."""

    reference = now or datetime.now(timezone.utc)
    event_time = _ensure_datetime(timestamp)
    delta_hours = max(
        0.0,
        (reference - event_time).total_seconds() / 3600.0,
    )
    tau = max(MIN_TAU, tau_hours)
    return float(exp(-delta_hours / tau))


def apply_time_decay(
    click_count: float,
    timestamp: str | datetime,
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
) -> float:
    """Apply exponential decay to a single aggregated click count."""

    weight = decay_weight(timestamp, now=now, tau_hours=tau_hours)
    return max(0.0, float(click_count)) * weight


def aggregate_time_decay(
    events: Iterable[tuple[str | datetime, float]],
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
) -> float:
    """Aggregate time-decayed counts for multiple events."""

    total = 0.0
    for timestamp, count in events:
        weight = decay_weight(timestamp, now=now, tau_hours=tau_hours)
        total += max(0.0, float(count)) * weight
    return total


def decay_curve(
    timestamps: Sequence[str | datetime],
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
) -> list[float]:
    """Return the decay weights for a sequence of timestamps."""

    return [
        decay_weight(timestamp, now=now, tau_hours=tau_hours)
        for timestamp in timestamps
    ]
