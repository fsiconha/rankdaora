from datetime import datetime, timezone

from preprocessing.bias_correction import PositionBiasCorrector
from preprocessing.ips import ImpressionEvent, corrected_clicks


def test_corrected_clicks_handles_simple_case() -> None:
    corrector = PositionBiasCorrector()
    corrector.ingest([(0, 10, 5)])
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    events = [
        ImpressionEvent(
            position=0,
            clicks=5,
            impressions=10,
            timestamp=now,
        )
    ]
    result = corrected_clicks(events, corrector, now=now)
    assert result > 5  # propensity < 1 so corrected clicks should inflate


def test_corrected_clicks_skips_zero_click_events() -> None:
    corrector = PositionBiasCorrector()
    corrector.ingest([(1, 10, 5)])
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    events = [
        ImpressionEvent(position=1, clicks=0, impressions=10, timestamp=now),
        ImpressionEvent(position=1, clicks=3, impressions=10, timestamp=now),
    ]
    result = corrected_clicks(events, corrector, now=now)
    assert result > 0
    assert result < 10
