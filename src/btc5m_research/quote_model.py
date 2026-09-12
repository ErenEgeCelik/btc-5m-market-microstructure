"""Reproducing the incumbent maker quote schedule.

The dominant maker on these contracts prices from an external spot reference rather
than from the contract order book, and its quotes are well described by the same
Brownian-probit map the fair-value module implements. Two structural facts were
identified from public data:

* the reference is a **composite of two major spot venues**, followed with a lag of
  roughly a few hundred milliseconds;
* the implied volatility term scales with trailing realized volatility rather than
  being constant.

Fitted per slot, the transformed regression reached a median within-slot R-squared
of about 0.92. With the specification frozen on earlier logs it reproduced later
held-out market mids to roughly six ticks of RMSE.

**This is understanding, not edge.** Where the reproduction and the market
disagreed, the market retained the better realized-outcome calibration. That result
is what moved the research from treating fair value as an alpha target to treating
market fair as an empirical axiom; the quote model became a timing and scenario tool
rather than a pricing one.

A deliberate trap is recorded here too. Merging the two spot references into a
single last-value series produces a saw-tooth artefact: a persistent level offset
between venues makes the merged series jump whenever the reporting venue alternates,
and a spike detector reads those jumps as real events. Signals must be built from a
single venue -- see ``single_feed_series``.
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
    """Map a quoted mid into the space the incumbent schedule is linear in.

    ``Phi^-1(mid) * sqrt(tau)`` is linear in the displacement of the reference price
    from the strike, so a per-slot regression in this space recovers the schedule.
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
