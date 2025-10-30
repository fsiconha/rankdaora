"""Bayesian smoothing utilities for click popularity signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .bias_correction import PositionBiasCorrector
from .ips import ImpressionEvent, corrected_clicks
from .time_decay import DEFAULT_DECAY_HOURS, decay_weight

EPSILON = 1e-6


def adjusted_impressions(
    events: Iterable[ImpressionEvent],
    bias_corrector: PositionBiasCorrector,
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
    epsilon: float = EPSILON,
) -> float:
    """Return ``Σ(impressions_i / p(pos_i) * w_t)`` for the events."""

    reference = now or datetime.now(timezone.utc)
    total = 0.0
    for event in events:
        raw_impressions = (
            event.impressions if event.impressions is not None else 1.0
        )
        if raw_impressions <= 0:
            continue
        propensity = max(
            epsilon,
            bias_corrector.position_probability(event.position),
        )
        event_ts = (
            event.timestamp if event.timestamp is not None else reference
        )
        weight = decay_weight(event_ts, now=reference, tau_hours=tau_hours)
        total += float(raw_impressions) * weight / propensity
    return total


def corrected_click_rate(
    events: Iterable[ImpressionEvent],
    bias_corrector: PositionBiasCorrector,
    *,
    now: datetime | None = None,
    tau_hours: float = DEFAULT_DECAY_HOURS,
    epsilon: float = EPSILON,
) -> float:
    """Return the corrected click-through rate for the provided events."""

    clicks = corrected_clicks(
        events,
        bias_corrector,
        now=now,
        tau_hours=tau_hours,
        epsilon=epsilon,
    )
    impressions = adjusted_impressions(
        events,
        bias_corrector,
        now=now,
        tau_hours=tau_hours,
        epsilon=epsilon,
    )
    if impressions <= 0:
        return 0.0
    return clicks / impressions


@dataclass
class BayesianSmoother:
    """Compute Bayesian-smoothed popularity scores."""

    prior: float
    pseudocount: float = 10.0
    tau_hours: float = DEFAULT_DECAY_HOURS
    epsilon: float = EPSILON

    def score(
        self,
        events: Iterable[ImpressionEvent],
        bias_corrector: PositionBiasCorrector,
        *,
        now: datetime | None = None,
    ) -> float:
        """Return ``(v * prior + C_corr) / (v + adjusted_impressions)``."""

        clicks = corrected_clicks(
            events,
            bias_corrector,
            now=now,
            tau_hours=self.tau_hours,
            epsilon=self.epsilon,
        )
        impressions = adjusted_impressions(
            events,
            bias_corrector,
            now=now,
            tau_hours=self.tau_hours,
            epsilon=self.epsilon,
        )
        denominator = max(self.epsilon, self.pseudocount + impressions)
        numerator = self.pseudocount * self.prior + clicks
        return numerator / denominator

    def score_from_stats(self, clicks: float, impressions: float) -> float:
        """Return score using precomputed corrected clicks/impressions."""

        denominator = max(self.epsilon, self.pseudocount + impressions)
        numerator = self.pseudocount * self.prior + clicks
        return numerator / denominator
