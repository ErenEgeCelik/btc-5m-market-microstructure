"""Dropout masking for offline analysis.

The venue order-book socket freezes silently. Measured: 8.9% of observed gaps
exceed 2 seconds, with the longest over 30 seconds, while the external price feeds
keep flowing normally.

This is not ordinary missing data, and the reason matters. A frozen book looks
exactly like a *stable* book -- and a stability-gated quoting policy treats a stable
book as its entry condition. So the corruption is correlated with the strategy: it
fires the engine precisely when the engine is blind. Analysis on unmasked data is
invalid by construction rather than merely noisy.

Every canonical measurement in the study consumes a mask built by an independent
health pass. This module is the reference implementation of the mask semantics.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

DEFAULT_GAP_THRESHOLD_S = 2.0
"""Gaps at or above this length are treated as outages, not quiet markets."""


@dataclass(frozen=True)
class Outage:
    start: float
    end: float

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("outage end precedes its start")

    @property
    def duration_s(self) -> float:
        return self.end - self.start


def detect_outages(
    event_times: list[float],
    gap_threshold_s: float = DEFAULT_GAP_THRESHOLD_S,
) -> list[Outage]:
    """Find inter-event gaps at or above the threshold."""
    if gap_threshold_s <= 0.0:
        raise ValueError("gap threshold must be positive")
    outages: list[Outage] = []
    for earlier, later in zip(event_times, event_times[1:]):
        if later < earlier:
            raise ValueError("event times must be non-decreasing")
        if later - earlier >= gap_threshold_s:
            outages.append(Outage(earlier, later))
    return outages


class CleanIndex:
    """Membership test for timestamps that fall outside any recorded outage."""

    def __init__(self, outages: list[Outage]) -> None:
        ordered = sorted(outages, key=lambda outage: outage.start)
        for first, second in zip(ordered, ordered[1:]):
            if second.start < first.end:
                raise ValueError("outages must not overlap")
        self._starts = [outage.start for outage in ordered]
        self._outages = ordered

    def is_clean(self, timestamp: float) -> bool:
        """False when ``timestamp`` lies strictly inside an outage."""
        if not self._outages:
            return True
        index = bisect_right(self._starts, timestamp) - 1
        if index < 0:
            return True
        outage = self._outages[index]
        return not (outage.start < timestamp < outage.end)

    def filter(self, timestamps: list[float]) -> list[float]:
        return [t for t in timestamps if self.is_clean(t)]

    def coverage(self, window_start: float, window_end: float) -> float:
        """Fraction of the window not covered by an outage."""
        if window_end <= window_start:
            raise ValueError("window must have positive length")
        total = window_end - window_start
        lost = 0.0
        for outage in self._outages:
            low = max(window_start, outage.start)
            high = min(window_end, outage.end)
            if high > low:
                lost += high - low
        return max(0.0, (total - lost) / total)
