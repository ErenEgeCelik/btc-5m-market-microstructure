"""Virtual queue scenarios with explicit activation and cancellation timing.

See docs/ for empirical scope and limitations. These reference components
do not establish profitability or guarantee real-world queue bounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field

MAKER_POST_LATENCY_S = 0.050
"""Measured maker order activation: 24-50 ms. The decision cell uses 50 ms."""

MAKER_CANCEL_LATENCY_S = 0.050
"""Measured cancel p50: 23-50 ms. Under load p99 reaches 218 ms."""

TAKER_PATH_LATENCY_S = 0.250
"""Server-delayed taker path. NOT the maker POST latency -- conflating the two
once invalidated an entire campaign of comparisons."""


@dataclass
class RestingOrder:
    """A hypothetical resting order walked through a recorded tape."""

    size: float
    queue_ahead: float
    placed_at: float
    post_latency_s: float = MAKER_POST_LATENCY_S
    cancel_latency_s: float = MAKER_CANCEL_LATENCY_S

    consumed: float = field(default=0.0, init=False)
    filled: float = field(default=0.0, init=False)
    cancel_requested_at: float | None = field(default=None, init=False)

    @property
    def active_from(self) -> float:
        return self.placed_at + self.post_latency_s

    def is_live(self, now: float) -> bool:
        """True when the order can take a fill at ``now``."""
        if now < self.active_from:
            return False
        if self.cancel_requested_at is None:
            return True
        return now < self.cancel_requested_at + self.cancel_latency_s

    def request_cancel(self, now: float) -> None:
        if self.cancel_requested_at is None:
            self.cancel_requested_at = now

    def consume(self, now: float, volume: float) -> float:
        """Apply ``volume`` of market flow at this price level; return the new fill."""
        if volume < 0.0:
            raise ValueError("volume cannot be negative")
        if not self.is_live(now):
            return 0.0
        self.consumed += volume
        reach = max(0.0, self.consumed - self.queue_ahead)
        new_fill = min(self.size, reach) - self.filled
        if new_fill <= 0.0:
            return 0.0
        self.filled = min(self.size, reach)
        return new_fill

    @property
    def is_complete(self) -> bool:
        return self.filled >= self.size - 1e-9


def fill_time_brackets(
    events: list[tuple[float, float, float]],
    queue_ahead: float,
    active_from: float,
) -> tuple[float | None, float | None]:
    """Pessimist and optimist fill times for a level with ``queue_ahead`` in front.

    ``events`` are ``(timestamp, traded_volume, size_drop)`` triples at our price.
    The optimist arm credits the part of a size drop that trades do not explain.

    The constraint "pessimist fills are a subset of optimist fills" is preserved,
    which matters: an adversary allowed to choose per moment inside an
    unconstrained bracket produces a band so wide that it excludes nothing.
    """
    consumed_pes = 0.0
    consumed_opt = 0.0
    t_pes: float | None = None
    t_opt: float | None = None

    for timestamp, traded, size_drop in events:
        if timestamp < active_from:
            continue
        consumed_pes += traded
        consumed_opt += traded + max(0.0, size_drop - traded)
        if t_pes is None and consumed_pes >= queue_ahead - 1e-9:
            t_pes = timestamp
        if t_opt is None and consumed_opt >= queue_ahead - 1e-9:
            t_opt = timestamp
        if t_pes is not None and t_opt is not None:
            break

    return t_pes, t_opt
