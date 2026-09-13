"""Dropout masking for offline analysis.

The venue order-book socket can freeze silently while external feeds continue.
Historical gap percentages describe elapsed stream time, not a fraction of gap
counts. See docs/data-engineering.md for the specific archived B05 measurement.

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
from math import isfinite

DEFAULT_GAP_THRESHOLD_S = 2.0
"""Gaps at or above this length are treated as outages, not quiet markets."""


@dataclass(frozen=True)
class Outage:
    start: float
    end: float

    def __post_init__(self) -> None:
        if not isfinite(self.start) or not isfinite(self.end):
            raise ValueError("outage endpoints must be finite")
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
    if not isfinite(gap_threshold_s) or gap_threshold_s <= 0.0:
        raise ValueError("gap threshold must be positive")
    if any(not isfinite(t) for t in event_times):
        raise ValueError("event times must be finite")
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

    def covers_window(self, start: float, end: float) -> bool:
        """Whether a positive-length interval avoids every outage interior."""
        return self.coverage(start, end) == 1.0


def slot_health(
    slot_start: float,
    tape_start: float,
    tape_end: float,
    gaps: list[Outage],
    anchor_start: bool,
    anchor_end: bool,
) -> dict[str, object] | None:
    """D0 health classification from stored gaps, not raw message reconstruction.

    Gap length comparisons are strictly >1.5 and >8 seconds. Tape-edge missing
    time is included. A window less than half observed is excluded (None).
    """
    if not all(isfinite(x) for x in (slot_start, tape_start, tape_end)):
        raise ValueError("timestamps must be finite")
    if tape_end <= tape_start:
        raise ValueError("tape span must be positive")
    CleanIndex(gaps)  # reject overlaps before they can double-count lost time
    start, end = slot_start + 10.0, slot_start + 290.0
    observed_start, observed_end = max(start, tape_start), min(end, tape_end)
    observed = observed_end - observed_start
    if observed < 140.0:
        return None
    coverage = {}
    for threshold in (1.5, 8.0):
        lost = sum(
            max(0.0, min(g.end, observed_end) - max(g.start, observed_start))
            for g in gaps if g.duration_s > threshold
        )
        coverage[threshold] = max(0.0, (observed - lost) / 280.0)
    if coverage[1.5] >= 0.95 and anchor_start and anchor_end:
        category = "FULL"
    elif coverage[8.0] >= 0.95 and anchor_start and anchor_end:
        category = "OK8"
    elif coverage[8.0] >= 0.95:
        category = "NOANC"
    else:
        category = "BAD"
    return {"cov15": round(coverage[1.5], 4), "cov80": round(coverage[8.0], 4),
            "a0": anchor_start, "a1": anchor_end, "cls": category}
