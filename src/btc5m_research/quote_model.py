"""Market-mid pricing structure and single-feed reference helpers.

See docs/ for empirical scope and limitations. These reference components
do not establish profitability or guarantee real-world queue bounds.
"""

from __future__ import annotations

import math
from statistics import NormalDist

_N = NormalDist()


def single_feed_series(
    ticks: list[tuple[float, str, float]],
    venue: str,
) -> list[tuple[float, float]]:
    """Project a multi-venue tick stream onto one venue.

    ``ticks`` are ``(timestamp, venue, price)``. Signal construction must run on the
    output of this function, never on a merged last-value series.
    """
    return [(timestamp, price) for timestamp, tick_venue, price in ticks if tick_venue == venue]


def merged_last_value_series(
    ticks: list[tuple[float, str, float]],
) -> list[tuple[float, float]]:
    """The artefact, implemented so that a test can demonstrate it.

    Takes the most recent price regardless of venue. With a persistent inter-venue
    level offset this manufactures alternating jumps that look like spikes.
    """
    return [(timestamp, price) for timestamp, _venue, price in ticks]


def transformed_quote_target(mid: float, tau_s: float) -> float:
    """Transform a market mid into the linear Brownian-probit model space.

    ``Phi^-1(mid) * sqrt(tau)`` is linear in the displacement of the reference price
    from the strike, so a per-slot regression describes this market-price relationship.
    """
    if not 0.0 < mid < 1.0:
        raise ValueError("mid must be a probability in (0, 1)")
    if tau_s <= 0.0:
        raise ValueError("tau must be positive")
    return _N.inv_cdf(mid) * math.sqrt(tau_s)


def predicted_mid(reference_displacement: float, sigma: float, tau_s: float) -> float:
    """Invert the schedule back into a price."""
    if sigma <= 0.0:
        raise ValueError("sigma must be positive")
    if tau_s <= 0.0:
        raise ValueError("tau must be positive")
    return _N.cdf(reference_displacement / (sigma * math.sqrt(tau_s)))


def lagged_reference(
    series: list[tuple[float, float]],
    now: float,
    lag_s: float,
) -> float | None:
    """As-of lookup of the reference price ``lag_s`` before ``now``.

    Strictly causal: it never reads a tick stamped later than ``now - lag_s``, which
    is what the no-lookahead test pins down.
    """
    if lag_s < 0.0:
        raise ValueError("lag cannot be negative")
    cutoff = now - lag_s
    value: float | None = None
    for timestamp, price in series:
        if timestamp <= cutoff:
            value = price
        else:
            break
    return value
