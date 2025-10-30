"""Position-bias correction utilities based on controlled exploration data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass
class PositionStats:
    """Aggregated impression and click statistics for a given position."""

    impressions: int = 0
    clicks: int = 0

    def add(self, impressions: int, clicks: int) -> None:
        """Accumulate raw counts for the position."""

        if impressions < 0 or clicks < 0:
            raise ValueError("Impressions and clicks must be non-negative")
        self.impressions += impressions
        self.clicks += clicks

    def probability(self, epsilon: float = 1e-6) -> float:
        """Return the click probability for the position with smoothing."""

        if self.impressions == 0:
            return 0.0
        return (self.clicks + epsilon) / (self.impressions + epsilon)


class PositionBiasCorrector:
    """Compute position bias using controlled exploration sessions."""

    def __init__(self) -> None:
        self._stats: Dict[int, PositionStats] = {}

    def ingest(self, observations: Iterable[tuple[int, int, int]]) -> None:
        """Update stats from ``(position, impressions, clicks)`` triples."""

        for position, impressions, clicks in observations:
            if position < 0:
                raise ValueError("Position index must be non-negative")
            stats = self._stats.setdefault(position, PositionStats())
            stats.add(impressions, clicks)

    def position_probability(self, position: int) -> float:
        """Return ``P(click | impression at position)``."""

        stats = self._stats.get(position)
        if stats is None:
            return 0.0
        return stats.probability()

    def bias_curve(self) -> Dict[int, float]:
        """Return the learned probability curve for all known positions."""

        return {
            position: stats.probability()
            for position, stats in self._stats.items()
        }
