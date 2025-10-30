from preprocessing.log_transformation import (
    log_percentile_transform,
    log_transform,
    percentile_rank,
)


def test_log_transform_clamps_negative_values() -> None:
    values = [-100, -1, 0, 1]
    transformed = log_transform(values)
    assert transformed[0] == transformed[1]
    assert transformed[-1] > transformed[-2]


def test_percentile_rank_handles_ties() -> None:
    values = [1.0, 2.0, 2.0, 3.0]
    ranks = percentile_rank(values)
    assert ranks[1] == ranks[2]
    assert ranks[0] < ranks[1] < ranks[3]


def test_log_percentile_transform_outputs_unit_interval() -> None:
    values = [0.0, 1.0, 10.0]
    transformed = log_percentile_transform(values)
    assert all(0.0 <= x <= 1.0 for x in transformed)
    assert transformed[0] == 0.0
    assert transformed[-1] == 1.0
