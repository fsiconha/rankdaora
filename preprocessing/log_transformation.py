"""Log scaling and percentile ranking for popularity signals."""

from __future__ import annotations

from math import log1p
from typing import Iterable, Sequence


def log_transform(values: Iterable[float]) -> list[float]:
    """Return ``log1p`` for each value after clamping to ``[-1, inf)``."""

    transformed: list[float] = []
    for value in values:
        clipped = max(0.0, float(value))
        transformed.append(log1p(clipped))
    return transformed


def percentile_rank(values: Sequence[float]) -> list[float]:
    """Return percentile ranks in ``[0, 1]`` using average ranks for ties."""

    if not values:
        return []

    indexed = sorted((value, index) for index, value in enumerate(values))
    n = len(indexed) - 1
    ranks = [0.0] * len(indexed)
    i = 0
    while i < len(indexed):
        j = i + 1
        current_value = indexed[i][0]
        while j < len(indexed) and indexed[j][0] == current_value:
            j += 1
        avg_rank = (i + j - 1) / 2.0
        percentile = 0.0 if n <= 0 else avg_rank / n
        for k in range(i, j):
            _, original_index = indexed[k]
            ranks[original_index] = percentile
        i = j
    return ranks


def log_percentile_transform(values: Iterable[float]) -> list[float]:
    """Apply ``log1p`` followed by percentile ranking."""

    logged = log_transform(values)
    return percentile_rank(logged)
