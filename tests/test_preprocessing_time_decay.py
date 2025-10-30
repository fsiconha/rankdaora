from datetime import datetime, timedelta, timezone

import pytest

from preprocessing.time_decay import (
    apply_time_decay,
    decay_curve,
    decay_weight,
)


def test_decay_weight_recent_event_is_close_to_one() -> None:
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    weight = decay_weight(now - timedelta(hours=1), now=now, tau_hours=24)
    assert 0.9 < weight <= 1.0


def test_decay_weight_future_event_clipped_at_one() -> None:
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    weight = decay_weight(now + timedelta(hours=1), now=now, tau_hours=24)
    assert weight == pytest.approx(1.0)


def test_apply_time_decay_scales_click_count() -> None:
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    adjusted = apply_time_decay(
        10,
        now - timedelta(hours=24),
        now=now,
        tau_hours=24,
    )
    expected = decay_weight(
        now - timedelta(hours=24),
        now=now,
        tau_hours=24,
    )
    assert adjusted == pytest.approx(10 * expected)


def test_decay_curve_returns_weights_for_sequence() -> None:
    now = datetime(2025, 10, 30, tzinfo=timezone.utc)
    timestamps = [now - timedelta(hours=offset) for offset in (0, 12, 24)]
    curve = decay_curve(timestamps, now=now, tau_hours=24)
    assert curve[0] == pytest.approx(1.0)
    assert curve[1] > curve[2] > 0
