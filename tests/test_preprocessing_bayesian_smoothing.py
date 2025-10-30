from datetime import datetime, timezone

import pytest

from preprocessing.bayesian_smoothing import (
    BayesianSmoother,
    adjusted_impressions,
    corrected_click_rate,
)
from preprocessing.bias_correction import PositionBiasCorrector
from preprocessing.ips import ImpressionEvent, corrected_clicks


def _build_corrector() -> PositionBiasCorrector:
    corrector = PositionBiasCorrector()
    corrector.ingest([(0, 20, 10), (1, 20, 5)])
    return corrector


def test_adjusted_impressions_scales_by_propensity() -> None:
    corrector = _build_corrector()
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    events = [
        ImpressionEvent(position=0, clicks=10, impressions=20, timestamp=now),
    ]
    total = adjusted_impressions(events, corrector, now=now)
    assert total > 20


def test_corrected_click_rate_matches_ratio() -> None:
    corrector = _build_corrector()
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    events = [
        ImpressionEvent(position=0, clicks=10, impressions=20, timestamp=now),
    ]
    rate = corrected_click_rate(events, corrector, now=now)
    total_clicks = corrected_clicks(events, corrector, now=now)
    total_impressions = adjusted_impressions(events, corrector, now=now)
    expected = total_clicks / total_impressions
    assert rate == pytest.approx(expected)


def test_bayesian_smoother_returns_smoothed_score() -> None:
    corrector = _build_corrector()
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    events = [
        ImpressionEvent(position=0, clicks=10, impressions=20, timestamp=now),
    ]
    smoother = BayesianSmoother(prior=0.5, pseudocount=10)
    score = smoother.score(events, corrector, now=now)
    assert 0 < score < 1
